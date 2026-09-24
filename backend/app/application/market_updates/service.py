"""One local durable queue; receipts survive cancellation, never become trading authority."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker

from app.application.experiments.data import HISTORICAL_ID
from app.application.market_updates.cache import ReceiptCache
from app.application.market_updates.contracts import (
    AUTHORITY,
    PARSER_VERSION,
    PROVIDER,
    SDK_VERSION,
    SDK_WHEEL_SHA256,
    TERMINAL,
    TERMS,
    CreateUpdateRequest,
    UpdateCancelled,
    UpdateConflict,
    UpdateError,
    latest_publishable_date,
    missing_chunks,
    parse_response,
    request_parameters,
    utc_now,
)
from app.application.market_updates.transport import fetch, sdk_available
from app.application.markets import MarketReader
from app.data.catalog.checksums import canonical_sha256
from app.db.models.market_updates import (
    MarketObservationModel,
    MarketReceiptModel,
    MarketUpdateJobModel,
)

logger = logging.getLogger(__name__)
OWNER_LOCK = 12001434
Fetch = Callable[
    [dict[str, str], asyncio.Event], Awaitable[tuple[dict[str, Any], datetime, datetime]]
]


class MarketUpdateManager:
    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
        engine: AsyncEngine,
        reader: MarketReader,
        cache_root: Path,
        *,
        transport: Fetch = fetch,
        request_interval: float = 1.0,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.factory, self.engine, self.reader = factory, engine, reader
        self.cache = ReceiptCache(cache_root, reader.registry.root)
        self.transport, self.request_interval, self.now = transport, request_interval, now
        self._worker: asyncio.Task[None] | None = None
        self._ownership: AsyncConnection | None = None
        self._owner_pid: int | None = None
        self._stopping = False
        self._wake = asyncio.Event()
        self._cancel: asyncio.Event | None = None
        self._active_id: UUID | None = None
        self._last_request = 0.0
        self._pending_terminal: tuple[UUID, str, str | None] | None = None

    async def _release(self) -> None:
        connection, self._ownership = self._ownership, None
        if connection is None:
            return
        try:
            if not connection.invalidated and not connection.closed:
                await connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": OWNER_LOCK}
                )
                await connection.commit()
        except BaseException:
            await connection.invalidate()
            raise
        finally:
            await connection.close()

    async def _verify_owner(self) -> None:
        try:
            connection = self._ownership
            if connection is None or connection.closed or connection.invalidated:
                raise RuntimeError("missing ownership")
            if await connection.scalar(text("SELECT pg_backend_pid()")) != self._owner_pid:
                raise RuntimeError("lost ownership")
            await connection.commit()
        except Exception as exc:
            self._stopping = True
            if self._cancel is not None:
                self._cancel.set()
            raise UpdateError("UPDATE_WORKER_OWNERSHIP_LOST") from exc

    async def start(self) -> None:
        if self._worker is not None:
            return
        connection = await self.engine.connect()
        try:
            if not await connection.scalar(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": OWNER_LOCK}
            ):
                raise UpdateConflict("UPDATE_WORKER_ALREADY_OWNED")
            self._ownership = connection
            self._owner_pid = await connection.scalar(text("SELECT pg_backend_pid()"))
            await connection.commit()
            await self._recover_receipts()
            async with self.factory() as db, db.begin():
                for row in await db.scalars(
                    select(MarketUpdateJobModel)
                    .where(MarketUpdateJobModel.status == "RUNNING")
                    .with_for_update()
                ):
                    row.status = row.phase = "INTERRUPTED"
                    row.completed_at = self.now()
                    if row.error_code != "RECEIPT_PERSISTENCE_BLOCKED":
                        row.error_code = "WORKER_RESTARTED_RETRY_AVAILABLE"
            self._stopping = False
            self._worker = asyncio.create_task(self._work(), name="user-market-update-worker")
            self._wake.set()
        except BaseException:
            if self._ownership is connection:
                with suppress(Exception):
                    await self._release()
            else:
                await connection.close()
            raise

    async def shutdown(self) -> None:
        self._stopping = True
        if self._cancel is not None:
            self._cancel.set()
        self._wake.set()
        try:
            if self._worker is not None:
                await self._worker
                self._worker = None
        finally:
            await self._release()

    async def _denied(self) -> bool:
        if await asyncio.to_thread(self.cache.denied):
            return True
        async with self.factory() as db:
            return bool(
                await db.scalar(
                    select(MarketUpdateJobModel.id)
                    .where(MarketUpdateJobModel.error_code == "SOURCE_ACCESS_DENIED")
                    .limit(1)
                )
            )

    async def _receipt_blocked(self) -> bool:
        async with self.factory() as db:
            return bool(
                await db.scalar(
                    select(MarketUpdateJobModel.id)
                    .where(MarketUpdateJobModel.error_code == "RECEIPT_PERSISTENCE_BLOCKED")
                    .limit(1)
                )
            )

    async def capabilities(self) -> dict[str, Any]:
        denied = await self._denied()
        receipt_blocked = await self._receipt_blocked()
        provider_available = sdk_available() and not denied
        archives = await asyncio.to_thread(self.reader.registry.datasets)
        archive = next((item for item in archives if item["dataset_id"] == HISTORICAL_ID), None)
        archive_available = bool(archive and archive["available"])
        worker_running = self._worker is not None and not self._worker.done() and not self._stopping
        reason = (
            "SOURCE_ACCESS_DENIED"
            if denied
            else "RECEIPT_PERSISTENCE_BLOCKED"
            if receipt_blocked
            else "BAOSTOCK_SDK_NOT_INSTALLED"
            if not provider_available
            else (archive or {}).get("reason_code", "DATASET_NOT_MOUNTED")
            if not archive_available
            else "UPDATE_WORKER_UNAVAILABLE"
            if not worker_running
            else None
        )
        return {
            "provider": PROVIDER,
            "sdk_version": SDK_VERSION,
            "available": provider_available
            and archive_available
            and worker_running
            and not receipt_blocked,
            "provider_available": provider_available,
            "archive_available": archive_available,
            "worker_running": worker_running,
            "reason_code": reason,
            "mode": "raw_only_candidate",
            "authority": AUTHORITY,
            "terms": TERMS,
            "max_securities": 20,
            "max_days": 366,
            "request_chunk_days": 31,
            "latest_publishable_date": latest_publishable_date(self.now()).isoformat(),
            "publication_timezone": "Asia/Shanghai",
            "publication_time": "17:30",
            "maximum_attempts_per_request": 3,
            "request_timeout_seconds": 45,
            "minimum_request_interval_seconds": 1,
            "job_timeout_seconds": 1800,
            "scope": "SELECTED_EXISTING_ARCHIVE_SECURITIES_NOT_FULL_UNIVERSE",
            "archive": archives,
        }

    @staticmethod
    def _same(
        row: MarketUpdateJobModel, digest: str, retry_of: UUID | None
    ) -> MarketUpdateJobModel:
        if row.configuration_sha256 != digest or row.retry_of != retry_of:
            raise UpdateConflict("IDEMPOTENCY_KEY_CONFLICT")
        return row

    async def create(
        self,
        request: CreateUpdateRequest,
        key: str,
        *,
        retry_of: UUID | None = None,
        attempt: int = 1,
    ) -> MarketUpdateJobModel:
        config = request.model_dump(mode="json")
        digest = canonical_sha256(config)
        async with self.factory() as db:
            existing = await db.scalar(
                select(MarketUpdateJobModel).where(MarketUpdateJobModel.request_key == key)
            )
            if existing is not None:
                return self._same(existing, digest, retry_of)
            if retry_of is not None:
                child = await db.scalar(
                    select(MarketUpdateJobModel).where(MarketUpdateJobModel.retry_of == retry_of)
                )
                if child is not None:
                    return self._same(child, digest, retry_of)
        if self._stopping:
            raise UpdateConflict("UPDATE_WORKER_UNAVAILABLE")
        if await self._denied():
            raise UpdateConflict("SOURCE_ACCESS_DENIED")
        if await self._receipt_blocked():
            raise UpdateConflict("RECEIPT_PERSISTENCE_BLOCKED")
        if self.transport is fetch and not sdk_available():
            raise UpdateError("BAOSTOCK_SDK_NOT_INSTALLED")
        dataset = await asyncio.to_thread(self.reader.registry.resolve, HISTORICAL_ID)
        if request.start_date <= date.fromisoformat(dataset["coverage_end"]):
            raise UpdateError("UPDATE_MUST_FOLLOW_FROZEN_COVERAGE")
        if request.end_date > latest_publishable_date(self.now()):
            raise UpdateError("UPDATE_DATE_NOT_YET_PUBLISHABLE")
        securities = []
        for sid in request.security_ids:
            security = await asyncio.to_thread(self.reader.security, HISTORICAL_ID, sid)
            if (
                security["listed_to"] is not None
                and request.end_date > date.fromisoformat(security["listed_to"])
            ) or request.start_date < date.fromisoformat(security["listed_from"]):
                raise UpdateError("UPDATE_OUTSIDE_KNOWN_LISTING_LIFECYCLE")
            securities.append(security)
        row = MarketUpdateJobModel(
            id=uuid4(),
            request_key=key,
            configuration=config,
            configuration_sha256=digest,
            master_snapshot={
                "dataset_id": HISTORICAL_ID,
                "sha256": dataset["sha256"],
                "as_of": dataset["coverage_end"],
                "securities": securities,
                "current_authority": "UNVERIFIED",
            },
            status="QUEUED",
            phase="QUEUED",
            created_at=self.now(),
            cancel_requested=False,
            completed_requests=0,
            retry_of=retry_of,
            attempt=attempt,
        )
        async with self.factory() as db:
            db.add(row)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                existing = await db.scalar(
                    select(MarketUpdateJobModel).where(MarketUpdateJobModel.request_key == key)
                )
                if existing is None and retry_of is not None:
                    existing = await db.scalar(
                        select(MarketUpdateJobModel).where(
                            MarketUpdateJobModel.retry_of == retry_of
                        )
                    )
                if existing is None:
                    raise
                return self._same(existing, digest, retry_of)
        self._wake.set()
        return row

    async def get(self, identifier: UUID) -> MarketUpdateJobModel:
        async with self.factory() as db:
            row = await db.get(MarketUpdateJobModel, identifier)
            if row is None:
                raise LookupError("MARKET_UPDATE_NOT_FOUND")
            return row

    async def list_jobs(self, limit: int, offset: int) -> tuple[list[MarketUpdateJobModel], int]:
        async with self.factory() as db:
            total = await db.scalar(select(func.count()).select_from(MarketUpdateJobModel))
            rows = await db.scalars(
                select(MarketUpdateJobModel)
                .order_by(MarketUpdateJobModel.created_at.desc(), MarketUpdateJobModel.id)
                .limit(limit)
                .offset(offset)
            )
            return list(rows), int(total or 0)

    async def cancel(self, identifier: UUID) -> MarketUpdateJobModel:
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(MarketUpdateJobModel)
                .where(MarketUpdateJobModel.id == identifier)
                .with_for_update()
            )
            if row is None:
                raise LookupError("MARKET_UPDATE_NOT_FOUND")
            if row.status not in TERMINAL:
                row.cancel_requested = True
                if row.status == "QUEUED":
                    row.status = row.phase = "CANCELLED"
                    row.completed_at = self.now()
        if self._active_id == identifier and self._cancel is not None:
            self._cancel.set()
        return row

    async def retry(self, identifier: UUID, key: str) -> MarketUpdateJobModel:
        row = await self.get(identifier)
        if row.status not in {"FAILED", "CANCELLED", "INTERRUPTED"}:
            raise UpdateConflict("RETRY_REQUIRES_UNSUCCESSFUL_TERMINAL_JOB")
        return await self.create(
            CreateUpdateRequest.model_validate(row.configuration),
            key,
            retry_of=row.id,
            attempt=row.attempt + 1,
        )

    async def receipts(
        self, identifier: UUID, limit: int, offset: int
    ) -> tuple[list[dict[str, Any]], int]:
        await self.get(identifier)
        async with self.factory() as db:
            query = select(MarketReceiptModel).where(MarketReceiptModel.job_id == identifier)
            total = await db.scalar(select(func.count()).select_from(query.subquery()))
            rows = list(
                await db.scalars(
                    query.order_by(MarketReceiptModel.received_at, MarketReceiptModel.id)
                    .limit(limit)
                    .offset(offset)
                )
            )
        items = []
        for row in rows:
            await self._verify_receipt(row)
            items.append(
                {"receipt_id": str(row.id), "manifest_sha256": row.manifest_sha256, **row.evidence}
            )
        return items, int(total or 0)

    async def _verify_receipt(self, receipt: MarketReceiptModel) -> None:
        manifest = await asyncio.to_thread(self.cache.verify, receipt.manifest_sha256)
        if manifest["evidence"] != receipt.evidence:
            raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")

    async def observations(self, sid: str, start: date, end: date) -> list[dict[str, Any]]:
        async with self.factory() as db:
            rows = list(
                await db.scalars(
                    select(MarketObservationModel)
                    .where(
                        MarketObservationModel.provider == PROVIDER,
                        MarketObservationModel.security_id == sid,
                        MarketObservationModel.trading_date >= start,
                        MarketObservationModel.trading_date <= end,
                    )
                    .order_by(MarketObservationModel.trading_date)
                )
            )
            receipts = list(
                await db.scalars(
                    select(MarketReceiptModel).where(
                        MarketReceiptModel.id.in_({row.receipt_id for row in rows})
                    )
                )
            )
        for receipt in receipts:
            await self._verify_receipt(receipt)
        return [{**row.payload, "receipt_id": str(row.receipt_id)} for row in rows]

    async def _claim(self) -> MarketUpdateJobModel | None:
        await self._verify_owner()
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(MarketUpdateJobModel)
                .where(MarketUpdateJobModel.status == "QUEUED")
                .order_by(MarketUpdateJobModel.created_at, MarketUpdateJobModel.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if row is not None:
                row.status, row.phase, row.started_at = "RUNNING", "VERIFYING_CACHE", self.now()
            return row

    async def _terminal(self, identifier: UUID, status: str, code: str | None) -> None:
        self._pending_terminal = (identifier, status, code)
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(MarketUpdateJobModel)
                .where(MarketUpdateJobModel.id == identifier)
                .with_for_update()
            )
            if row is not None and row.status == "RUNNING":
                row.status = row.phase = status
                row.completed_at, row.error_code = self.now(), code
        self._pending_terminal = None

    async def _work(self) -> None:
        failures = 0
        while not self._stopping:
            self._wake.clear()
            try:
                if self._pending_terminal is not None:
                    await self._terminal(*self._pending_terminal)
                await self._recover_receipts()
                if job := await self._claim():
                    await self._execute(job)
                    failures = 0
                    continue
                failures = 0
            except Exception:
                failures += 1
                logger.error("Market update queue unavailable; new claims deferred")
            with suppress(TimeoutError):
                await asyncio.wait_for(
                    self._wake.wait(), timeout=30 if failures >= 3 else 2**failures
                )

    async def _checkpoint(
        self, identifier: UUID, total: int, parameters: dict[str, str] | None = None
    ) -> None:
        await self._verify_owner()
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(MarketUpdateJobModel)
                .where(MarketUpdateJobModel.id == identifier)
                .with_for_update()
            )
            assert row is not None
            if row.cancel_requested or self._stopping:
                raise UpdateCancelled
            row.phase, row.total_requests = "FETCHING_RAW_CANDIDATES", total
            row.summary = {"active_request": parameters, "authority": AUTHORITY}

    async def _fetch(
        self, params: dict[str, str], cancelled: asyncio.Event
    ) -> tuple[dict[str, Any], datetime, datetime, int]:
        loop = asyncio.get_running_loop()
        for attempt in range(1, 4):
            delay = max(0.0, self._last_request + self.request_interval - loop.time())
            if delay:
                with suppress(TimeoutError):
                    await asyncio.wait_for(cancelled.wait(), timeout=delay)
            if cancelled.is_set() or self._stopping:
                raise UpdateCancelled
            await self._verify_owner()
            self._last_request = loop.time()
            try:
                envelope, requested, received = await self.transport(params, cancelled)
                return envelope, requested, received, attempt
            except UpdateError as exc:
                if exc.code == "SOURCE_ACCESS_DENIED":
                    # Preserve the circuit even when the subsequent DB write or process fails.
                    marker = asyncio.create_task(
                        asyncio.to_thread(self.cache.record_denial, self.now().isoformat())
                    )
                    try:
                        await asyncio.shield(marker)
                    except asyncio.CancelledError:
                        await marker
                        raise
                    except Exception:
                        self._stopping = True
                        raise exc from None
                if (
                    exc.code not in {"PROVIDER_TIMEOUT", "PROVIDER_TRANSPORT_FAILED"}
                    or attempt == 3
                ):
                    raise
                with suppress(TimeoutError):
                    await asyncio.wait_for(
                        cancelled.wait(), timeout=self.request_interval * 2**attempt
                    )
        raise AssertionError("bounded attempts exhausted")

    async def _save(
        self,
        job: MarketUpdateJobModel,
        sid: str,
        envelope: dict[str, Any],
        requested: datetime,
        received: datetime,
        attempt: int,
        start: date,
        end: date,
        rows: list[dict[str, Any]],
        cancelled: asyncio.Event,
    ) -> None:
        raw = {"fields": envelope["fields"], "rows": envelope["rows"]}
        evidence = {
            "job_id": str(job.id),
            "receipt_id": str(uuid4()),
            "provider": PROVIDER,
            "sdk_version": SDK_VERSION,
            "parser_version": PARSER_VERSION,
            "sdk_release_wheel_sha256": SDK_WHEEL_SHA256,
            "source_endpoint": "public-api.baostock.com:10030",
            "security_id": sid,
            "parameters": request_parameters(sid, start, end),
            "requested_at_utc": requested.isoformat(),
            "received_at_utc": received.isoformat(),
            "response_completed_at_utc": envelope["response_completed_at_utc"],
            "first_received_at_utc": received.isoformat(),
            "attempt": attempt,
            "raw_response_representation": "SDK_DECODED_FIELDS_AND_ROWS_NOT_WIRE_BYTES",
            "raw_response_sha256": canonical_sha256(raw),
            "logical_rows_sha256": canonical_sha256({"rows": rows}),
            "row_count": len(rows),
            "terms": TERMS,
            "authority": AUTHORITY,
        }
        payload = {"raw": raw, "rows": rows, "evidence": evidence}
        writing = asyncio.create_task(asyncio.to_thread(self.cache.journal, payload))
        try:
            try:
                journal = await asyncio.shield(writing)
            except asyncio.CancelledError:
                # A received response must not disappear when a job time budget expires.
                await writing
                raise
        except (OSError, UpdateError) as exc:
            self._stopping = True
            # A full/unavailable cache cannot turn a later reacquisition into the
            # first receipt. Retain the complete fact in the independent DB when
            # available and block acquisition until explicit storage reconciliation.
            try:
                async with self.factory() as db, db.begin():
                    current = await db.scalar(
                        select(MarketUpdateJobModel)
                        .where(MarketUpdateJobModel.id == job.id)
                        .with_for_update()
                    )
                    assert current is not None
                    current.error_code = "RECEIPT_PERSISTENCE_BLOCKED"
                    current.summary = {"unpublished_receipt": payload, "authority": AUTHORITY}
            except Exception:
                logger.critical(
                    "Receipt journal and fallback database unavailable; acquisition stopped"
                )
            raise UpdateError("RECEIPT_PERSISTENCE_BLOCKED") from exc
        await self._link_receipt(journal, payload)
        if cancelled.is_set() or self._stopping:
            raise UpdateCancelled

    async def _recover_receipts(self) -> None:
        for journal, payload in await asyncio.to_thread(self.cache.pending):
            await self._link_receipt(journal, payload)

    async def _link_receipt(self, journal: str, payload: dict[str, Any]) -> None:
        evidence, rows, raw = payload["evidence"], payload["rows"], payload["raw"]
        identifier, receipt_id = UUID(evidence["job_id"]), UUID(evidence["receipt_id"])
        await self._verify_owner()
        async with self.factory() as db:
            existing = await db.get(MarketReceiptModel, receipt_id)
        if existing is not None:
            await self._verify_receipt(existing)
            if existing.evidence != evidence:
                raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")
            await asyncio.to_thread(self.cache.acknowledge, journal)
            return
        digest = await asyncio.to_thread(self.cache.publish, raw, rows, evidence)
        await self._verify_owner()
        async with self.factory() as db, db.begin():
            current = await db.scalar(
                select(MarketUpdateJobModel)
                .where(MarketUpdateJobModel.id == identifier)
                .with_for_update()
            )
            if current is None:
                raise UpdateError("PRODUCT_CACHE_JOB_NOT_FOUND")
            # These are receipt facts, not a success transition. Cancellation or a
            # crash must not discard already received raw evidence or move first-seen.
            params = evidence["parameters"]
            if (
                evidence["security_id"] not in current.configuration["security_ids"]
                or not current.configuration["start_date"]
                <= params["start_date"]
                <= params["end_date"]
                <= current.configuration["end_date"]
                or rows
                != parse_response(
                    raw,
                    evidence["security_id"],
                    date.fromisoformat(params["start_date"]),
                    date.fromisoformat(params["end_date"]),
                )
            ):
                raise UpdateError("PRODUCT_CACHE_INTEGRITY_FAILED")
            receipt = MarketReceiptModel(
                id=receipt_id,
                job_id=identifier,
                security_id=evidence["security_id"],
                received_at=datetime.fromisoformat(evidence["received_at_utc"]),
                manifest_sha256=digest,
                evidence=evidence,
            )
            db.add(receipt)
            await db.flush()
            if rows:
                await db.execute(
                    insert(MarketObservationModel)
                    .values(
                        [
                            dict(
                                provider=PROVIDER,
                                security_id=evidence["security_id"],
                                trading_date=date.fromisoformat(row["trading_date"]),
                                receipt_id=receipt.id,
                                payload=row,
                            )
                            for row in rows
                        ]
                    )
                    .on_conflict_do_nothing()
                )
            current.completed_requests += 1
        await asyncio.to_thread(self.cache.acknowledge, journal)

    async def _execute(self, job: MarketUpdateJobModel) -> None:
        cancelled = asyncio.Event()
        self._cancel, self._active_id = cancelled, job.id
        try:
            if self._stopping:
                raise UpdateCancelled
            if await self._denied():
                raise UpdateError("SOURCE_ACCESS_DENIED")
            if await self._receipt_blocked():
                raise UpdateError("RECEIPT_PERSISTENCE_BLOCKED")
            async with asyncio.timeout(1800):
                request = CreateUpdateRequest.model_validate(job.configuration)
                work: list[tuple[str, date, date]] = []
                skipped = 0
                for sid in request.security_ids:
                    cached = await self.observations(sid, request.start_date, request.end_date)
                    skipped += len(cached)
                    work.extend(
                        (sid, first, last)
                        for first, last in missing_chunks(
                            request.start_date,
                            request.end_date,
                            {date.fromisoformat(row["trading_date"]) for row in cached},
                        )
                    )
                await self._checkpoint(job.id, len(work))
                for sid, start, end in work:
                    await self._checkpoint(job.id, len(work), request_parameters(sid, start, end))
                    envelope, requested, received, attempt = await self._fetch(
                        request_parameters(sid, start, end), cancelled
                    )
                    rows = parse_response(envelope, sid, start, end)
                    await self._save(
                        job,
                        sid,
                        envelope,
                        requested,
                        received,
                        attempt,
                        start,
                        end,
                        rows,
                        cancelled,
                    )
                unresolved = {}
                count = 0
                for sid in request.security_ids:
                    observed = await self.observations(sid, request.start_date, request.end_date)
                    dates = {row["trading_date"] for row in observed}
                    count += len(observed)
                    unresolved[sid] = [
                        (request.start_date + timedelta(days=i)).isoformat()
                        for i in range((request.end_date - request.start_date).days + 1)
                        if (request.start_date + timedelta(days=i)).isoformat() not in dates
                    ]
                await self._verify_owner()
                async with self.factory() as db, db.begin():
                    row = await db.scalar(
                        select(MarketUpdateJobModel)
                        .where(MarketUpdateJobModel.id == job.id)
                        .with_for_update()
                    )
                    assert row is not None
                    if row.cancel_requested or cancelled.is_set() or self._stopping:
                        raise UpdateCancelled
                    if row.status != "RUNNING":
                        raise UpdateConflict("UPDATE_JOB_OWNERSHIP_CHANGED")
                    row.summary = {
                        "authority": AUTHORITY,
                        "cached_observations_skipped": skipped,
                        "observations_available": count,
                        "new_observations": count - skipped,
                        "unresolved_dates": unresolved,
                        "unresolved_date_count": sum(len(days) for days in unresolved.values()),
                        "gap_semantics": "CALENDAR_UNVERIFIED_ABSENCE_NOT_HOLIDAY_OR_SUSPENSION",
                        "completion_semantics": "BOUNDED_RAW_REQUESTS_COMPLETED_NOT_AUTHORITY_PASS",
                    }
                    row.status, row.phase, row.completed_at = "SUCCEEDED", "COMPLETE", self.now()
        except UpdateCancelled:
            await self._terminal(job.id, "INTERRUPTED" if self._stopping else "CANCELLED", None)
        except TimeoutError:
            await self._terminal(job.id, "INTERRUPTED", "UPDATE_JOB_TIME_BUDGET_EXHAUSTED")
        except Exception as exc:
            code = exc.code if isinstance(exc, UpdateError) else "MARKET_UPDATE_FAILED"
            logger.error("Market update %s failed: %s", job.id, type(exc).__name__)
            await self._terminal(job.id, "FAILED", code)
        finally:
            self._cancel, self._active_id = None, None
