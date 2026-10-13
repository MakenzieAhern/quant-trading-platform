"""Read-only, deployment-pinned authority contracts, not a data acquisition approval.

No contract ships with the application. A hash passed by an HTTP caller cannot
register one. Synthetic contracts in tests prove plumbing, not source acceptance.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Context, Decimal, localcontext
from pathlib import Path
from typing import Annotated, Any, Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from app.data.catalog.checksums import canonical_sha256, verified_file_bytes
from app.data.providers.research import DailyBarRecord, SecurityStatusRecord
from app.domain.markets import CorporateAction, Market, SecurityId
from app.domain.markets.calendar import TradingCalendar, TradingSession
from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.demergers import DemergerEvent
from app.domain.markets.mergers import MergerEvent
from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.markets.rules import ResolvedTradingRules, TransactionCostSchedule
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent
from app.research.costs import EffectiveDatedAShareCommission
from app.research.models import ResearchSession

SHA = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
FORWARD_SOURCE = "RECEIPT_BOUND_FORWARD_A_SHARE_V1"
AUTHORITY_NAMES = frozenset(
    {
        "SECURITY_MASTER",
        "SSE_ST",
        "SZSE_ST",
        "SUSPENSIONS",
        "ADJUSTMENTS",
        "CORPORATE_ACTIONS",
        "RAW_OHLCV",
        "CALENDAR",
        "MARKET_RULES",
        "TRANSACTION_COSTS",
    }
)
ZONE = ZoneInfo("Asia/Shanghai")


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ForwardSourceError(ValueError):
    """Stable public error; private contract paths/content stay in the cause only."""


def utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError("FORWARD_TIMESTAMP_MUST_BE_UTC")
    return value


class FilePin(ContractModel):
    path: str = Field(min_length=1)
    sha256: SHA

    def read(self, root: Path) -> bytes:
        relative = Path(self.path)
        target = (root / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(root):
            raise ValueError("FORWARD_CONTRACT_PATH_ESCAPE")
        return verified_file_bytes(target, self.sha256)


class AuthorityApproval(ContractModel):
    decision: Literal["ADMITTED_FOR_PRIVATE_LOCAL_PAPER_EOD"]
    valid_from: date
    valid_to: date
    known_at: datetime
    source_version: str = Field(min_length=1)
    evidence: tuple[FilePin, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def dates(self) -> "AuthorityApproval":
        utc(self.known_at)
        if self.valid_to < self.valid_from:
            raise ValueError("FORWARD_AUTHORITY_COVERAGE_INVALID")
        return self


class SourcePermission(ContractModel):
    # The scope may be a lawful public/local trial; no paid licence is presumed.
    decision: Literal["PERMITTED"]
    permitted_scope: Literal["PRIVATE_LOCAL_ANALYSIS_TRIAL"]
    use: Literal["PRIVATE_LOCAL_PAPER_EOD"]
    provider: Literal["BAOSTOCK_PUBLIC_SINGLE_SECURITY_EOD"]
    evidence: tuple[FilePin, ...] = Field(min_length=1)
    terms_sha256: SHA


class ExchangeSession(ContractModel):
    trading_date: date
    opens_at: datetime
    closes_at: datetime

    @model_validator(mode="after")
    def dates(self) -> "ExchangeSession":
        utc(self.opens_at)
        utc(self.closes_at)
        if not (
            self.opens_at < self.closes_at
            and self.opens_at.astimezone(ZONE).date() == self.trading_date
            and self.closes_at.astimezone(ZONE).date() == self.trading_date
        ):
            raise ValueError("FORWARD_EXCHANGE_SESSION_INVALID")
        return self


class AuthorityFrame(ContractModel):
    """Complete admitted PIT context; raw prices come only from canonical receipts."""

    trading_date: date
    authorities_sha256: SHA
    statuses: tuple[SecurityStatusRecord, ...] = Field(min_length=1)
    buy_lot_sizes: tuple[tuple[SecurityId, int], ...]
    adjustment_factors: dict[str, Decimal]
    trading_rules: tuple[ResolvedTradingRules, ...]
    corporate_actions: tuple[CorporateAction, ...] = ()
    demergers: tuple[DemergerEvent, ...] = ()
    mergers: tuple[MergerEvent, ...] = ()
    partial_surrenders: tuple[MandatoryPartialShareSurrenderEvent, ...] = ()
    surrender_holder_class: str | None = None
    surrender_holder_classes: tuple[tuple[SecurityId, str], ...] = ()
    pass_through_events: tuple[RestructuringBonusPassThroughEvent, ...] = ()
    consolidations: tuple[ShareConsolidationEvent, ...] = ()
    consolidation_holder_class: str | None = None

    @model_validator(mode="after")
    def complete(self) -> "AuthorityFrame":
        ids = tuple(str(item.status.security_id) for item in self.statuses)
        if ids != tuple(sorted(set(ids))):
            raise ValueError("FORWARD_UNIVERSE_MUST_BE_SORTED_AND_UNIQUE")
        if (
            {str(key) for key, _ in self.buy_lot_sizes} != set(ids)
            or len(self.buy_lot_sizes) != len(ids)
            or set(self.adjustment_factors) != set(ids)
            or {str(item.security_id) for item in self.trading_rules} != set(ids)
            or len(self.trading_rules) != len(ids)
        ):
            raise ValueError("FORWARD_AUTHORITY_UNIVERSE_NOT_CLOSED")
        statuses = {item.status.security_id: item.status for item in self.statuses}
        for item in self.trading_rules:
            status = statuses[item.security_id]
            if (
                status.trading_date != self.trading_date
                or item.trading_date != self.trading_date
                or status.is_suspended is None
                or status.is_tradeable is None
                or item.suspended is None
                or item.suspended != status.is_suspended
                or (status.is_suspended and item.executable)
                or (not status.is_tradeable and item.executable)
                or dict(self.buy_lot_sizes)[item.security_id] != item.buy_lot_size
                or item.buy_lot_size <= 0
                or not item.cost_schedule.valid_from <= self.trading_date
                or (
                    item.cost_schedule.valid_to is not None
                    and self.trading_date > item.cost_schedule.valid_to
                )
            ):
                raise ValueError("FORWARD_PIT_CONTEXT_INVALID")
        if any(not value.is_finite() or value <= 0 for value in self.adjustment_factors.values()):
            raise ValueError("FORWARD_ADJUSTMENT_INVALID")
        for events in (
            self.corporate_actions,
            self.demergers,
            self.mergers,
            self.partial_surrenders,
            self.pass_through_events,
            self.consolidations,
        ):
            for event in events:
                if getattr(event, "application_date", event.effective_date) != self.trading_date:
                    raise ValueError("FORWARD_ACTION_APPLICATION_DATE_MISMATCH")
        return self

    def session(self, bars: tuple[DailyBarRecord, ...]) -> ResearchSession:
        fields = {
            name: getattr(self, name)
            for name in type(self).model_fields
            if name not in {"authorities_sha256", "adjustment_factors"}
        }
        return ResearchSession(bars=bars, **fields)


class WarmupFrame(AuthorityFrame):
    bars: tuple[DailyBarRecord, ...]

    def session(self, bars: tuple[DailyBarRecord, ...] | None = None) -> ResearchSession:
        fields = self.model_dump(exclude={"bars"})
        return AuthorityFrame.model_validate(fields).session(self.bars)


class AdmissionContract(ContractModel):
    schema_version: Literal["PAPER_FORWARD_ADMISSION_V1"]
    admission_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")
    permission: SourcePermission
    authorities: dict[str, AuthorityApproval]
    first_forward_session: date
    last_forward_session: date
    schedule: FilePin
    daily_context: FilePin
    warmup: FilePin
    transaction_costs: tuple[TransactionCostSchedule, ...] = Field(min_length=1)


class ReceiptPin(ContractModel):
    security_id: str = Field(pattern=r"^CN-A:(SSE|SZSE):[0-9]{6}$")
    receipt_id: UUID
    manifest_sha256: SHA
    first_received_at: datetime

    @model_validator(mode="after")
    def aware(self) -> "ReceiptPin":
        utc(self.first_received_at)
        return self


class DailyInputProvenance(ContractModel):
    schema_version: Literal["PAPER_DAILY_INPUT_V1"] = "PAPER_DAILY_INPUT_V1"
    paper_session_id: UUID
    trading_date: date
    admission_sha256: SHA
    calendar_sha256: SHA
    authorities_sha256: SHA
    session_sha256: SHA
    input_sha256: SHA
    closed_at: datetime
    next_open_at: datetime
    receipts: tuple[ReceiptPin, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def binding(self) -> "DailyInputProvenance":
        utc(self.closed_at)
        utc(self.next_open_at)
        ids = tuple(item.security_id for item in self.receipts)
        if ids != tuple(sorted(set(ids))) or self.closed_at >= self.next_open_at:
            raise ValueError("FORWARD_RECEIPT_IDENTITY_INVALID")
        if any(
            not self.closed_at <= item.first_received_at < self.next_open_at
            for item in self.receipts
        ):
            raise ValueError("FORWARD_RECEIPT_OUTSIDE_SESSION_WINDOW")
        if self.input_sha256 != canonical_sha256(
            self.model_dump(mode="json", exclude={"input_sha256"})
        ):
            raise ValueError("FORWARD_INPUT_DIGEST_MISMATCH")
        return self


class InputCommitObservation(ContractModel):
    schema_version: Literal["PAPER_INPUT_COMMIT_V1"] = "PAPER_INPUT_COMMIT_V1"
    paper_session_id: UUID
    trading_date: date
    input_sha256: SHA
    journal_first_sequence: int = Field(gt=0, strict=True)
    journal_last_sequence: int = Field(gt=0, strict=True)
    commit_observed_at: datetime
    next_open_at: datetime

    @model_validator(mode="after")
    def dates(self) -> "InputCommitObservation":
        utc(self.commit_observed_at)
        utc(self.next_open_at)
        if (
            self.journal_first_sequence > self.journal_last_sequence
            or self.commit_observed_at >= self.next_open_at
        ):
            raise ValueError("FORWARD_COMMIT_AFTER_NEXT_OPEN")
        return self


@dataclass(frozen=True)
class AdmittedSource:
    contract: AdmissionContract
    sha256: str
    calendar: TradingCalendar
    schedule: tuple[ExchangeSession, ...]
    frames: tuple[AuthorityFrame, ...]
    warmup: tuple[ResearchSession, ...]
    authorities_sha256: str
    registry: "ForwardAdmissionRegistry"

    def recheck(self) -> None:
        self.registry.load(self.contract.admission_id, self.sha256)


class ForwardAdmissionRegistry:
    def __init__(self, path: Path | None, expected_sha256: str | None) -> None:
        if (path is None) != (expected_sha256 is None):
            raise ValueError("FORWARD_CONTRACT_REQUIRES_PATH_AND_SHA256")
        self.path = path.resolve() if path is not None else None
        self.expected_sha256 = expected_sha256

    def load(self, admission_id: str, expected_sha256: str | None = None) -> AdmittedSource:
        try:
            return self._load(admission_id, expected_sha256)
        except (ValueError, OSError, KeyError, TypeError) as exc:
            code = str(exc)
            if not code.startswith("FORWARD_") or not code.replace("_", "").isalnum():
                code = "FORWARD_SOURCE_CONTRACT_INVALID"
            raise ForwardSourceError(code) from exc

    def _load(self, admission_id: str, expected_sha256: str | None = None) -> AdmittedSource:
        if self.path is None or self.expected_sha256 is None:
            raise ValueError("FORWARD_SOURCE_NOT_REGISTERED")
        if expected_sha256 is not None and expected_sha256 != self.expected_sha256:
            raise ValueError("FORWARD_SOURCE_CHANGED_SINCE_SUBMISSION")
        contract = AdmissionContract.model_validate_json(
            verified_file_bytes(self.path, self.expected_sha256)
        )
        if contract.admission_id != admission_id or set(contract.authorities) != AUTHORITY_NAMES:
            raise ValueError("FORWARD_SOURCE_AUTHORITY_SET_INVALID")
        root = self.path.parent
        for pin in contract.permission.evidence:
            pin.read(root)
        if contract.permission.terms_sha256 not in {
            pin.sha256 for pin in contract.permission.evidence
        }:
            raise ValueError("FORWARD_PERMISSION_TERMS_NOT_BOUND")
        for authority in contract.authorities.values():
            for pin in authority.evidence:
                pin.read(root)
        digest = canonical_sha256(
            {key: value.model_dump(mode="json") for key, value in contract.authorities.items()}
        )
        schedule = TypeAdapter(tuple[ExchangeSession, ...]).validate_json(
            contract.schedule.read(root)
        )
        frames = TypeAdapter(tuple[AuthorityFrame, ...]).validate_json(
            contract.daily_context.read(root)
        )
        warmup = TypeAdapter(tuple[WarmupFrame, ...]).validate_json(contract.warmup.read(root))
        days = tuple(item.trading_date for item in schedule)
        if not days or days != tuple(sorted(set(days))):
            raise ValueError("FORWARD_CALENDAR_NOT_CLOSED")
        expected = tuple(
            day
            for day in days
            if contract.first_forward_session <= day <= contract.last_forward_session
        )
        if (
            not expected
            or tuple(frame.trading_date for frame in frames) != expected
            or days[-1] <= expected[-1]
        ):
            raise ValueError("FORWARD_DAILY_COVERAGE_OR_NEXT_SESSION_MISSING")
        warm_days = tuple(day for day in days if day < expected[0])
        if tuple(frame.trading_date for frame in warmup) != warm_days:
            raise ValueError("FORWARD_WARMUP_BOUNDARY_INVALID")
        times = {item.trading_date: item for item in schedule}
        costs = EffectiveDatedAShareCommission(contract.transaction_costs)
        for frame in (*warmup, *frames):
            # Compare approved source schedules before the existing user commission overrides.
            applicable = tuple(
                cost
                for cost in costs.schedules
                if cost.valid_from <= frame.trading_date
                and (cost.valid_to is None or frame.trading_date <= cost.valid_to)
            )
            if len(applicable) != 1 or any(
                rule.cost_schedule != applicable[0] for rule in frame.trading_rules
            ):
                raise ValueError("FORWARD_TRANSACTION_COST_SOURCE_MISMATCH")
            if frame.authorities_sha256 != digest:
                raise ValueError("FORWARD_FRAME_AUTHORITY_MISMATCH")
            for authority in contract.authorities.values():
                if (
                    not authority.valid_from <= frame.trading_date <= authority.valid_to
                    or authority.known_at > times[frame.trading_date].closes_at
                ):
                    raise ValueError("FORWARD_AUTHORITY_NOT_EFFECTIVE_OR_NOT_KNOWN")
        sessions = tuple(frame.session() for frame in warmup)
        for frame, session in zip(warmup, sessions, strict=True):
            if {str(bar.security_id) for bar in session.bars} != {
                str(item.status.security_id) for item in frame.statuses
            }:
                raise ValueError("FORWARD_WARMUP_UNIVERSE_NOT_CLOSED")
            for bar in session.bars:
                factor = frame.adjustment_factors[str(bar.security_id)]
                with localcontext(Context(prec=28)):
                    adjusted = bar.raw_close * factor
                if bar.adjustment_factor != factor or bar.adjusted_close != adjusted:
                    raise ValueError("FORWARD_WARMUP_ADJUSTMENT_MISMATCH")
        calendar = TradingCalendar(
            market=Market.CN_A,
            sessions=tuple(
                TradingSession(
                    session_date=day, is_open=True, source_version=contract.schedule.sha256
                )
                for day in days
            ),
        )
        return AdmittedSource(
            contract, self.expected_sha256, calendar, schedule, frames, sessions, digest, self
        )


def receipt_bar(row: dict[str, Any], frame: AuthorityFrame) -> DailyBarRecord:
    raw = row["raw"]
    sid = str(row["security_id"])
    if row["trading_date"] != frame.trading_date.isoformat() or sid not in frame.adjustment_factors:
        raise ValueError("FORWARD_RECEIPT_DATE_OR_SECURITY_MISMATCH")
    factor = frame.adjustment_factors[sid]
    with localcontext(Context(prec=28)):
        adjusted_close = Decimal(raw["close"]) * factor
    return DailyBarRecord(
        security_id=SecurityId(value=sid),
        trading_date=frame.trading_date,
        raw_open=raw["open"],
        raw_high=raw["high"],
        raw_low=raw["low"],
        raw_close=raw["close"],
        pre_close=raw["preclose"],
        volume=raw["volume"],
        amount=raw["amount"],
        adjustment_factor=factor,
        adjusted_close=adjusted_close,
    )
