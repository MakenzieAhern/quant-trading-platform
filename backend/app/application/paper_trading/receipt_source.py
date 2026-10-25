"""Canonical product receipts -> admitted dated sessions; never fetches market data."""

import asyncio
from collections.abc import AsyncIterator, Callable
from datetime import date, datetime
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.application.market_updates.contracts import PROVIDER
from app.application.market_updates.service import MarketUpdateManager
from app.application.paper_trading.qualified_context import QualifiedContextReader
from app.application.paper_trading.source_admission import (
    DAILY_INPUT,
    AdmittedSource,
    AuthorityFrame,
    ContextDailyInputProvenance,
    ContextPin,
    DailyInput,
    DynamicAdmissionContract,
    ForwardAdmissionRegistry,
    InputCommitObservation,
    ReceiptPin,
    receipt_bar,
    utc,
)
from app.data.catalog.checksums import canonical_sha256
from app.db.models.market_updates import MarketObservationModel, MarketReceiptModel
from app.domain.markets.calendar import TradingCalendar
from app.paper.models import PaperEventRecord, PaperSession
from app.research.models import ResearchSession


class CanonicalReceiptReader:
    def __init__(self, factory: async_sessionmaker[AsyncSession], updates: MarketUpdateManager):
        self.factory = factory
        self.updates = updates

    async def read(
        self, frame: AuthorityFrame
    ) -> tuple[tuple[dict[str, Any], MarketReceiptModel], ...] | None:
        ids = tuple(str(item.status.security_id) for item in frame.statuses)
        # Bound duplicate reconciliation work, never the admitted security universe.
        receipt_budget = max(1000, 4 * len(ids))
        async with self.factory() as db:
            observations = tuple(
                await db.scalars(
                    select(MarketObservationModel).where(
                        MarketObservationModel.provider == PROVIDER,
                        MarketObservationModel.trading_date == frame.trading_date,
                        MarketObservationModel.security_id.in_(ids),
                    )
                )
            )
            receipts = tuple(
                await db.scalars(
                    select(MarketReceiptModel)
                    .where(
                        or_(
                            MarketReceiptModel.id.in_({item.receipt_id for item in observations}),
                            and_(
                                MarketReceiptModel.security_id.in_(ids),
                                MarketReceiptModel.evidence["parameters"]["start_date"].astext
                                <= frame.trading_date.isoformat(),
                                MarketReceiptModel.evidence["parameters"]["end_date"].astext
                                >= frame.trading_date.isoformat(),
                            ),
                        )
                    )
                    .order_by(MarketReceiptModel.received_at, MarketReceiptModel.id)
                    .limit(receipt_budget + 1)
                )
            )
        if len(receipts) > receipt_budget:
            raise ValueError("FORWARD_RECEIPT_RECONCILIATION_LIMIT_EXCEEDED")
        by_id = {item.id: item for item in receipts}
        by_security = {item.security_id: item for item in observations}
        if len(by_security) != len(observations) or not set(by_security) <= set(ids):
            raise ValueError("FORWARD_CANONICAL_OBSERVATION_IDENTITY_INVALID")
        verified = {}
        for candidate in receipts:
            verified[candidate.id] = await self.updates.verify_receipt(candidate)
        result = []
        for sid in ids:
            if sid not in by_security:
                continue
            observation = by_security[sid]
            receipt = by_id.get(observation.receipt_id)
            if (
                receipt is None
                or receipt.security_id != sid
                or observation.provider != PROVIDER
                or observation.trading_date != frame.trading_date
            ):
                raise ValueError("FORWARD_CANONICAL_RECEIPT_MISSING_OR_MISMATCH")
            matching = [
                row
                for row in verified[receipt.id]
                if row["security_id"] == sid
                and row["trading_date"] == frame.trading_date.isoformat()
            ]
            if len(matching) != 1 or canonical_sha256(matching[0]) != canonical_sha256(
                observation.payload
            ):
                raise ValueError("FORWARD_CANONICAL_OBSERVATION_NOT_IN_RECEIPT")
            for candidate_id, candidate_rows in verified.items():
                for candidate_row in candidate_rows:
                    if (
                        candidate_row["security_id"] == sid
                        and candidate_row["trading_date"] == frame.trading_date.isoformat()
                        and canonical_sha256(candidate_row) != canonical_sha256(matching[0])
                    ):
                        raise ValueError("FORWARD_CONFLICTING_RECEIPT_OBSERVATIONS")
                    if (
                        candidate_row["security_id"] == sid
                        and candidate_row["trading_date"] == frame.trading_date.isoformat()
                        and by_id[candidate_id].received_at < receipt.received_at
                    ):
                        raise ValueError("FORWARD_CANONICAL_FIRST_RECEIPT_CHANGED")
            result.append((matching[0], receipt))
        return tuple(result) if len(result) == len(ids) else None


class ReceiptSessionSource:
    def __init__(
        self,
        admitted: AdmittedSource,
        reader: CanonicalReceiptReader,
        account: PaperSession,
        clock: Callable[[], datetime],
        cursor: date | None,
        contexts: QualifiedContextReader | None = None,
    ) -> None:
        self.admitted = admitted
        self.reader = reader
        self.account = account
        self.clock = clock
        self.cursor = cursor
        self.started_at = account.started_at
        self.inputs: dict[date, DailyInput] = {}
        self.contexts = contexts
        self.replay_contexts: dict[date, ContextPin] = {}

    def bind_history(self, history: tuple[PaperEventRecord, ...]) -> None:
        for event in history:
            if event.event_type == "market.session":
                provenance = DAILY_INPUT.validate_python(event.payload.get("input_provenance"))
                if isinstance(provenance, ContextDailyInputProvenance):
                    if provenance.trading_date in self.replay_contexts:
                        raise ValueError("FORWARD_DUPLICATE_REPLAY_CONTEXT")
                    self.replay_contexts[provenance.trading_date] = provenance.context

    def bind_start(self, started_at: datetime | None) -> None:
        if started_at is None:
            raise ValueError("FORWARD_ORIGINAL_START_MISSING")
        utc(started_at)
        if self.started_at is not None and self.started_at != started_at:
            raise ValueError("FORWARD_ORIGINAL_START_CHANGED")
        self.started_at = started_at

    async def sessions(self) -> AsyncIterator[ResearchSession | TradingCalendar]:
        yield self.admitted.calendar
        for session in self.admitted.warmup:
            # Inactive strategy warms up; manager journals no pre-range account result.
            yield session
        schedule = self.admitted.schedule
        indices = {item.trading_date: index for index, item in enumerate(schedule)}
        frames = {frame.trading_date: frame for frame in self.admitted.frames}
        dynamic = isinstance(self.admitted.contract, DynamicAdmissionContract)
        for day in self.admitted.forward_dates:
            current = schedule[indices[day]]
            following = schedule[indices[day] + 1]
            replay = self.cursor is not None and day <= self.cursor
            if self.started_at is None or self.started_at >= current.closes_at:
                raise ValueError("FORWARD_SESSION_CLOSED_BEFORE_ACCOUNT_START")
            context_pin = None
            expected = self.replay_contexts.get(day)
            if dynamic and replay and expected is None:
                raise ValueError("FORWARD_REPLAY_CONTEXT_PIN_MISSING")
            while True:
                now = utc(self.clock())
                if not replay and now >= following.opens_at:
                    raise ValueError("FORWARD_INPUT_MISSED_NEXT_OPEN")
                if replay or now >= current.closes_at:
                    if dynamic:
                        if self.contexts is None:
                            raise ValueError("FORWARD_CONTEXT_VERIFIER_NOT_REGISTERED")
                        qualified = await self.contexts.read(self.admitted, day, expected)
                        if qualified is None:
                            if replay:
                                raise ValueError("FORWARD_REPLAY_CONTEXT_DISAPPEARED")
                            await asyncio.sleep(5)
                            continue
                        frame, context_pin = qualified
                    else:
                        frame = frames[day]
                    rows = await self.reader.read(frame)
                    if rows is not None:
                        await asyncio.to_thread(self.admitted.recheck)
                        now = utc(self.clock())
                        if not replay and now >= following.opens_at:
                            raise ValueError("FORWARD_INPUT_MISSED_NEXT_OPEN")
                        if context_pin is not None and (
                            context_pin.registered_at >= following.opens_at
                            or context_pin.registered_at > now
                        ):
                            raise ValueError("FORWARD_CONTEXT_OUTSIDE_CAUSAL_WINDOW")
                        break
                    if replay:
                        raise ValueError("FORWARD_REPLAY_RECEIPT_DISAPPEARED")
                await asyncio.sleep(5)
            pins = []
            for row, receipt in rows:
                evidence = receipt.evidence
                first = utc(datetime.fromisoformat(evidence["first_received_at_utc"]))
                completed = utc(datetime.fromisoformat(evidence["response_completed_at_utc"]))
                if (
                    not current.closes_at <= completed <= first < following.opens_at
                    or first < self.started_at
                    or (not replay and first > now)
                ):
                    raise ValueError("FORWARD_ORIGINAL_RECEIPT_OUTSIDE_CAUSAL_WINDOW")
                if (
                    evidence["terms"].get("terms_snapshot_sha256")
                    != self.admitted.contract.permission.terms_sha256
                ):
                    raise ValueError("FORWARD_RECEIPT_PERMISSION_VERSION_MISMATCH")
                status = next(
                    item.status
                    for item in frame.statuses
                    if str(item.status.security_id) == row["security_id"]
                )
                if status.is_suspended != (row["provider_trade_status"] == "0") or status.is_st != (
                    row["provider_is_st"] == "1"
                ):
                    raise ValueError("FORWARD_VENDOR_AUTHORITY_STATUS_CONFLICT")
                pins.append(
                    ReceiptPin(
                        security_id=receipt.security_id,
                        receipt_id=receipt.id,
                        manifest_sha256=receipt.manifest_sha256,
                        first_received_at=first,
                    )
                )
            session = frame.session(tuple(receipt_bar(row, frame) for row, _ in rows))
            payload: dict[str, Any] = {
                "schema_version": "PAPER_DAILY_INPUT_V1",
                "paper_session_id": str(self.account.id),
                "trading_date": frame.trading_date.isoformat(),
                "admission_sha256": self.admitted.sha256,
                "calendar_sha256": self.admitted.contract.schedule.sha256,
                "authorities_sha256": self.admitted.authorities_sha256,
                "session_sha256": canonical_sha256(
                    TypeAdapter(ResearchSession).dump_python(session, mode="json")
                ),
                "closed_at": current.closes_at.isoformat().replace("+00:00", "Z"),
                "next_open_at": following.opens_at.isoformat().replace("+00:00", "Z"),
                "receipts": [pin.model_dump(mode="json") for pin in pins],
            }
            if context_pin is not None:
                payload["schema_version"] = "PAPER_DAILY_INPUT_V2"
                payload["context"] = context_pin.model_dump(mode="json")
            self.inputs[frame.trading_date] = DAILY_INPUT.validate_python(
                {**payload, "input_sha256": canonical_sha256(payload)}
            )
            yield session


class ReceiptSessionFactory:
    def __init__(
        self,
        registry: ForwardAdmissionRegistry,
        reader: CanonicalReceiptReader,
        contexts: QualifiedContextReader | None = None,
    ):
        self.registry = registry
        self.reader = reader
        self.contexts = contexts

    def load(self, admission_id: str, expected_sha256: str | None = None) -> AdmittedSource:
        admitted = self.registry.load(admission_id, expected_sha256)
        if isinstance(admitted.contract, DynamicAdmissionContract):
            if self.contexts is None:
                raise ValueError("FORWARD_CONTEXT_VERIFIER_NOT_REGISTERED")
            self.contexts.require(admitted)
        return admitted

    def build(
        self, account: PaperSession, clock: Callable[[], datetime], cursor: date | None
    ) -> ReceiptSessionSource:
        pinned = account.strategy_parameters.get("dataset_sha256")
        if not isinstance(pinned, str):
            raise ValueError("FORWARD_ACCOUNT_ADMISSION_PIN_MISSING")
        admitted = self.load(account.dataset_id, pinned)
        if (
            str(account.strategy_parameters.get("start_date"))
            != admitted.contract.first_forward_session.isoformat()
            or str(account.strategy_parameters.get("end_date"))
            != admitted.contract.last_forward_session.isoformat()
        ):
            raise ValueError("FORWARD_ACCOUNT_COVERAGE_CHANGED")
        return ReceiptSessionSource(admitted, self.reader, account, clock, cursor, self.contexts)


def validate_commit_history(
    history: tuple[PaperEventRecord, ...], account: PaperSession
) -> set[date]:
    """A resume cannot invent a missing/late commit acknowledgement for an old plan."""
    markets = [item for item in history if item.event_type == "market.session"]
    markers = [item for item in history if item.event_type == "input.committed"]
    commits = {}
    for record in markers:
        marker = InputCommitObservation.model_validate(record.payload)
        if (
            marker.paper_session_id != account.id
            or marker.commit_observed_at != record.occurred_at
            or marker.trading_date in commits
            or marker.journal_last_sequence >= record.sequence
        ):
            raise ValueError("FORWARD_COMMIT_HISTORY_INVALID")
        commits[marker.trading_date] = (marker, record)
    for index, market in enumerate(markets):
        provenance = DAILY_INPUT.validate_python(market.payload.get("input_provenance"))
        pair = commits.get(provenance.trading_date)
        if pair is None:
            raise ValueError("FORWARD_COMMITTED_INPUT_ACKNOWLEDGEMENT_MISSING")
        marker, record = pair
        batch = [
            item
            for item in history
            if marker.journal_first_sequence <= item.sequence <= marker.journal_last_sequence
        ]
        if (
            provenance.paper_session_id != account.id
            or market.payload["trading_date"] != provenance.trading_date.isoformat()
            or marker.input_sha256 != provenance.input_sha256
            or marker.next_open_at != provenance.next_open_at
            or marker.commit_observed_at < provenance.available_at
            or not batch
            or batch[0] != market
            or batch[-1].event_type != "portfolio.snapshot"
            or batch[-1].payload.get("input_provenance") != market.payload["input_provenance"]
            or any(
                item.event_type in {"session.status", "calendar.observed", "input.committed"}
                for item in batch
            )
            or (index + 1 < len(markets) and record.sequence >= markets[index + 1].sequence)
        ):
            raise ValueError("FORWARD_COMMIT_BATCH_BINDING_INVALID")
    if len(commits) != len(markets):
        raise ValueError("FORWARD_ORPHAN_COMMIT_OBSERVATION")
    return set(commits)
