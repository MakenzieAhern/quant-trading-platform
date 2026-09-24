"""One local worker, a durable PostgreSQL queue, and session-boundary cancellation."""

import asyncio
import logging
from contextlib import suppress
from datetime import UTC, date, datetime
from threading import Event
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession, async_sessionmaker

from app.application.experiments.data import ExperimentDatasetRegistry, ExperimentInputError
from app.application.experiments.models import CreateExperimentRequest
from app.application.experiments.runner import ExperimentCancelled, json_value, run_experiment
from app.data.catalog.checksums import canonical_sha256
from app.db.models.experiments import ExperimentJobModel, ExperimentResultRowModel

logger = logging.getLogger(__name__)
TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}
OWNER_LOCK = 12001234


class ExperimentConflictError(ValueError):
    pass


class ExperimentManager:
    def __init__(
        self,
        factory: async_sessionmaker[AsyncSession],
        registry: ExperimentDatasetRegistry,
        engine: AsyncEngine,
    ) -> None:
        self.factory = factory
        self.registry = registry
        self.engine = engine
        self._wake = asyncio.Event()
        self._stopping = False
        self._worker: asyncio.Task[None] | None = None
        self._active_cancel: Event | None = None
        self._active_id: UUID | None = None
        self._ownership: AsyncConnection | None = None
        self._pending_terminal: tuple[UUID, str, str | None] | None = None
        self._ownership_failed = False
        self._owner_pid: int | None = None

    async def start(self) -> None:
        if self._worker is not None:
            return
        connection = await self.engine.connect()
        try:
            if not await connection.scalar(
                text("SELECT pg_try_advisory_lock(:key)"), {"key": OWNER_LOCK}
            ):
                raise RuntimeError("another process owns the exploratory job queue")
            self._ownership = connection
            self._owner_pid = await connection.scalar(text("SELECT pg_backend_pid()"))
            await connection.commit()
            async with self.factory() as db, db.begin():
                rows = (
                    await db.scalars(
                        select(ExperimentJobModel)
                        .where(ExperimentJobModel.status == "RUNNING")
                        .with_for_update()
                    )
                ).all()
                for row in rows:
                    row.status = "INTERRUPTED"
                    row.phase = "INTERRUPTED"
                    row.error_code = "WORKER_RESTARTED_RETRY_AVAILABLE"
                    row.completed_at = datetime.now(UTC)
            self._stopping = False
            self._ownership_failed = False
            self._worker = asyncio.create_task(self._work(), name="product-experiment-worker")
            self._wake.set()
        except BaseException:
            if self._ownership is connection:
                self._ownership = None
                with suppress(Exception):
                    await self._release_ownership(connection)
            else:
                await connection.close()
            raise

    async def shutdown(self) -> None:
        self._stopping = True
        if self._active_cancel is not None:
            self._active_cancel.set()
        self._wake.set()
        if self._worker is not None:
            await self._worker
            self._worker = None
        if self._ownership is not None:
            connection = self._ownership
            self._ownership = None
            await self._release_ownership(connection)

    @staticmethod
    async def _release_ownership(connection: AsyncConnection) -> None:
        try:
            if connection.invalidated or connection.closed:
                return
            await connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": OWNER_LOCK})
            await connection.commit()
        except BaseException:
            # A pooled close alone retains a PostgreSQL session lock. Discard a broken
            # physical connection if explicit unlock cannot be confirmed.
            await connection.invalidate()
            raise
        finally:
            await connection.close()

    async def _verify_ownership(self) -> None:
        connection = self._ownership
        try:
            if connection is None or connection.invalidated or connection.closed:
                raise RuntimeError("owner connection is no longer active")
            if await connection.scalar(text("SELECT pg_backend_pid()")) != self._owner_pid:
                raise RuntimeError("owner connection was replaced")
            await connection.commit()
        except Exception as exc:
            self._ownership_failed = self._stopping = True
            if self._active_cancel is not None:
                self._active_cancel.set()
            self._wake.set()
            raise ExperimentInputError("EXPERIMENT_WORKER_OWNERSHIP_LOST") from exc

    async def create(
        self,
        request: CreateExperimentRequest,
        key: str,
        *,
        retry_of: UUID | None = None,
        attempt: int = 1,
    ) -> ExperimentJobModel:
        if self._ownership_failed:
            raise ExperimentConflictError("EXPERIMENT_WORKER_UNAVAILABLE")
        config = json_value(request.model_dump())
        fingerprint = canonical_sha256(config)
        async with self.factory() as db:
            existing = await db.scalar(
                select(ExperimentJobModel).where(ExperimentJobModel.request_key == key)
            )
            if existing is not None:
                return self._same(existing, fingerprint, retry_of)
        dataset = await asyncio.to_thread(self.registry.resolve, request.dataset_id)
        if (
            not date.fromisoformat(dataset["coverage_start"])
            <= request.start_date
            <= request.end_date
            <= date.fromisoformat(dataset["coverage_end"])
        ):
            raise ExperimentInputError("DATES_OUTSIDE_DATASET")
        if request.universe not in dataset["universes"]:
            raise ExperimentInputError("UNIVERSE_NOT_AVAILABLE")
        model = ExperimentJobModel(
            id=uuid4(),
            name=request.name,
            status="QUEUED",
            mode=dataset["mode"],
            dataset_id=request.dataset_id,
            dataset_sha256=dataset["sha256"],
            configuration=config,
            configuration_sha256=fingerprint,
            request_key=key,
            created_at=datetime.now(UTC),
            phase="QUEUED",
            completed_sessions=0,
            total_sessions=None,
            cancel_requested=False,
            retry_of=retry_of,
            attempt=attempt,
        )
        async with self.factory() as db:
            db.add(model)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                existing = await db.scalar(
                    select(ExperimentJobModel).where(ExperimentJobModel.request_key == key)
                )
                if existing is None:
                    raise
                return self._same(existing, fingerprint, retry_of)
        self._wake.set()
        return model

    @staticmethod
    def _same(
        row: ExperimentJobModel, fingerprint: str, retry_of: UUID | None
    ) -> ExperimentJobModel:
        if row.configuration_sha256 != fingerprint or row.retry_of != retry_of:
            raise ExperimentConflictError("IDEMPOTENCY_KEY_CONFLICT")
        return row

    async def get(self, identifier: UUID) -> ExperimentJobModel:
        async with self.factory() as db:
            row = await db.get(ExperimentJobModel, identifier)
            if row is None:
                raise LookupError("EXPERIMENT_NOT_FOUND")
            return row

    async def list_jobs(self, limit: int, offset: int) -> tuple[list[ExperimentJobModel], int]:
        async with self.factory() as db:
            total = await db.scalar(select(func.count()).select_from(ExperimentJobModel))
            rows = list(
                (
                    await db.scalars(
                        select(ExperimentJobModel)
                        .order_by(ExperimentJobModel.created_at.desc(), ExperimentJobModel.id)
                        .limit(limit)
                        .offset(offset)
                    )
                ).all()
            )
            return rows, int(total or 0)

    async def cancel(self, identifier: UUID) -> ExperimentJobModel:
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(ExperimentJobModel)
                .where(ExperimentJobModel.id == identifier)
                .with_for_update()
            )
            if row is None:
                raise LookupError("EXPERIMENT_NOT_FOUND")
            if row.status not in TERMINAL:
                row.cancel_requested = True
                if row.status == "QUEUED":
                    row.status = row.phase = "CANCELLED"
                    row.completed_at = datetime.now(UTC)
        if self._active_id == identifier and self._active_cancel is not None:
            self._active_cancel.set()
        return row

    async def retry(self, identifier: UUID, key: str) -> ExperimentJobModel:
        row = await self.get(identifier)
        if row.status not in {"FAILED", "CANCELLED", "INTERRUPTED"}:
            raise ExperimentConflictError("RETRY_REQUIRES_UNSUCCESSFUL_TERMINAL_JOB")
        return await self.create(
            CreateExperimentRequest.model_validate(row.configuration),
            key,
            retry_of=row.id,
            attempt=row.attempt + 1,
        )

    async def collection(
        self, identifier: UUID, collection: str, limit: int, offset: int
    ) -> tuple[list[dict[str, Any]], int]:
        await self.get(identifier)
        async with self.factory() as db:
            query = select(ExperimentResultRowModel).where(
                ExperimentResultRowModel.job_id == identifier,
                ExperimentResultRowModel.collection == collection,
            )
            total = await db.scalar(select(func.count()).select_from(query.subquery()))
            rows = (
                await db.scalars(
                    query.order_by(ExperimentResultRowModel.sequence).limit(limit).offset(offset)
                )
            ).all()
            return [row.payload for row in rows], int(total or 0)

    async def _claim(self) -> ExperimentJobModel | None:
        await self._verify_ownership()
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(ExperimentJobModel)
                .where(ExperimentJobModel.status == "QUEUED")
                .order_by(ExperimentJobModel.created_at, ExperimentJobModel.id)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if row is not None:
                row.status = "RUNNING"
                row.phase = "VERIFYING_DATA"
                row.started_at = datetime.now(UTC)
            return row

    async def _progress(
        self, identifier: UUID, phase: str, completed: int, total: int | None
    ) -> None:
        await self._verify_ownership()
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(ExperimentJobModel)
                .where(ExperimentJobModel.id == identifier)
                .with_for_update()
            )
            if row is not None and row.status == "RUNNING":
                row.phase, row.completed_sessions, row.total_sessions = phase, completed, total
                if row.cancel_requested and self._active_cancel is not None:
                    self._active_cancel.set()

    async def _work(self) -> None:
        failures = 0
        while not self._stopping:
            self._wake.clear()
            try:
                # Retain terminal intent until its transaction commits. A temporary DB
                # failure must not leave an unowned RUNNING row while new work is claimed.
                if self._pending_terminal is not None:
                    await self._record_terminal(*self._pending_terminal)
                if self._stopping:
                    break
                job = await self._claim()
                if job is not None:
                    await self._execute(job)
                    failures = 0
                    continue
                failures = 0
            except Exception:
                failures += 1
                logger.error("Exploratory queue unavailable; new claims deferred")
            with suppress(TimeoutError):
                # After three failures the queue circuit probes at most once per 30s;
                # an explicit new request can wake it sooner after DB recovery.
                delay = 30 if failures >= 3 else max(2, 2**failures)
                await asyncio.wait_for(self._wake.wait(), timeout=delay)

    async def _execute(self, job: ExperimentJobModel) -> None:
        cancelled = Event()
        self._active_cancel, self._active_id = cancelled, job.id
        loop = asyncio.get_running_loop()

        def progress(phase: str, completed: int, total: int | None) -> None:
            asyncio.run_coroutine_threadsafe(
                self._progress(job.id, phase, completed, total), loop
            ).result()

        try:
            # _claim awaits a transaction: shutdown may begin before this event exists.
            # Registration and this check are synchronous, closing that ownership gap.
            if self._stopping:
                raise ExperimentCancelled
            output = await asyncio.to_thread(
                run_experiment,
                self.registry,
                CreateExperimentRequest.model_validate(job.configuration),
                job.dataset_sha256,
                cancelled,
                progress,
            )
            await self._verify_ownership()
            async with self.factory() as db, db.begin():
                row = await db.scalar(
                    select(ExperimentJobModel)
                    .where(ExperimentJobModel.id == job.id)
                    .with_for_update()
                )
                assert row is not None
                if row.cancel_requested or cancelled.is_set():
                    raise ExperimentCancelled
                if row.status != "RUNNING":
                    raise ExperimentConflictError("JOB_OWNERSHIP_CHANGED")
                for collection, values in output.rows.items():
                    db.add_all(
                        [
                            ExperimentResultRowModel(
                                job_id=job.id, collection=collection, sequence=i, payload=value
                            )
                            for i, value in enumerate(values)
                        ]
                    )
                row.summary = {"job_id": str(job.id), **output.summary}
                row.status, row.phase = "SUCCEEDED", "COMPLETE"
                row.completed_at = datetime.now(UTC)
        except ExperimentCancelled:
            await self._record_terminal(
                job.id,
                "INTERRUPTED" if self._stopping else "CANCELLED",
                "WORKER_STOPPED_RETRY_AVAILABLE" if self._stopping else None,
            )
        except Exception as exc:
            logger.error("Experiment %s failed: %s", job.id, type(exc).__name__)
            code = (
                exc.code if isinstance(exc, ExperimentInputError) else "EXPERIMENT_EXECUTION_FAILED"
            )
            await self._record_terminal(job.id, "FAILED", code)
        finally:
            self._active_cancel = None
            self._active_id = None

    async def _record_terminal(self, identifier: UUID, status: str, code: str | None) -> None:
        self._pending_terminal = (identifier, status, code)
        await self._finish_failure(identifier, status, code)
        self._pending_terminal = None

    async def _finish_failure(self, identifier: UUID, status: str, code: str | None) -> None:
        async with self.factory() as db, db.begin():
            row = await db.scalar(
                select(ExperimentJobModel)
                .where(ExperimentJobModel.id == identifier)
                .with_for_update()
            )
            if row is not None and row.status == "RUNNING":
                row.status = row.phase = status
                row.error_code = code
                row.completed_at = datetime.now(UTC)
