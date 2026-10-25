from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.api.schemas.backtests import (
    DecimalString,
    FillResponse,
    PositiveDecimalString,
    RiskDecisionResponse,
    RiskRequest,
    SignalResponse,
    StrategyRequest,
    StrictModel,
)
from app.application.paper_trading.source_admission import (
    ZONE,
    DailyInput,
    InputCommitObservation,
)
from app.paper.calendar import CalendarObservation
from app.paper.models import PaperSessionStatus


class ReplayPaperSessionRequest(StrictModel):
    provider_type: Literal["replay"] = "replay"
    dataset_id: Literal["AAPL_fixture"] = "AAPL_fixture"
    symbol: Literal["AAPL"] = "AAPL"
    strategy: StrategyRequest
    initial_cash: PositiveDecimalString = Field(default=Decimal("100000"))
    default_order_quantity: PositiveDecimalString = Field(default=Decimal("10"))
    risk: RiskRequest = Field(default_factory=RiskRequest)


class FrozenAShareParameters(StrictModel):
    pass


class FrozenAShareStrategy(StrictModel):
    type: Literal["cn_a_cross_sectional_momentum_low_vol_v1"]
    parameters: FrozenAShareParameters = Field(default_factory=FrozenAShareParameters)


class SimulatedASharePaperSessionRequest(StrictModel):
    provider_type: Literal["simulated_a_share"]
    dataset_id: Literal["CN_A_SIMULATED_PAPER_FIXTURE_V1"]
    symbol: Literal["CN-A"]
    strategy: FrozenAShareStrategy
    initial_cash: PositiveDecimalString = Field(default=Decimal("100000000"))
    default_order_quantity: PositiveDecimalString = Field(default=Decimal(1))
    risk: RiskRequest = Field(default_factory=lambda: RiskRequest(enforce_buying_power=True))


class HistoricalAShareParameters(StrictModel):
    start_date: date
    end_date: date
    rebalance_sessions: int = Field(default=20, ge=1, le=252, strict=True)
    maximum_holdings: int = Field(default=20, ge=1, le=100, strict=True)
    max_position_weight: PositiveDecimalString = Field(default=Decimal("0.1"), le=1)
    universe: Literal["ALL", "SSE", "SZSE"] = "ALL"
    commission_rate: DecimalString = Field(default=Decimal("0.0003"), ge=0, le=Decimal("0.01"))
    minimum_commission: DecimalString = Field(default=Decimal("5"), ge=0, le=Decimal("1000"))

    @model_validator(mode="after")
    def valid_period(self) -> "HistoricalAShareParameters":
        if self.end_date < self.start_date or (self.end_date - self.start_date).days > 92:
            raise ValueError("historical replay requires a range of at most 93 calendar days")
        return self


class HistoricalAShareStrategy(StrictModel):
    type: Literal["cn_a_cross_sectional_momentum_low_vol_v1"]
    parameters: HistoricalAShareParameters


class HistoricalASharePaperSessionRequest(StrictModel):
    provider_type: Literal["historical_a_share"]
    dataset_id: Literal["cn-a-research-20100101-20251231-v1"]
    symbol: Literal["CN-A"]
    strategy: HistoricalAShareStrategy
    initial_cash: PositiveDecimalString = Field(default=Decimal("100000"))
    default_order_quantity: PositiveDecimalString = Field(default=Decimal(1))
    risk: RiskRequest = Field(default_factory=lambda: RiskRequest(enforce_buying_power=True))

    @model_validator(mode="after")
    def safe_risk(self) -> "HistoricalASharePaperSessionRequest":
        if not self.risk.enforce_buying_power:
            raise ValueError("historical A-share paper requires buying-power enforcement")
        if self.risk.max_leverage is not None and self.risk.max_leverage > 1:
            raise ValueError("historical A-share paper cannot use leverage")
        if self.risk.max_drawdown is not None and not (-1 <= self.risk.max_drawdown <= 0):
            raise ValueError("historical A-share paper drawdown must be between -1 and 0")
        self.risk.max_leverage = Decimal(1)
        if self.risk.max_drawdown is None:
            self.risk.max_drawdown = Decimal("-0.2")
        return self


class ForwardASharePaperSessionRequest(StrictModel):
    provider_type: Literal["forward_a_share"]
    dataset_id: str = Field(pattern=r"^[a-z0-9][a-z0-9._-]{2,127}$")
    symbol: Literal["CN-A"]
    strategy: HistoricalAShareStrategy
    initial_cash: PositiveDecimalString = Field(default=Decimal("100000"))
    default_order_quantity: PositiveDecimalString = Field(default=Decimal(1))
    risk: RiskRequest = Field(default_factory=lambda: RiskRequest(enforce_buying_power=True))

    @model_validator(mode="after")
    def safe_risk(self) -> "ForwardASharePaperSessionRequest":
        if not self.risk.enforce_buying_power or (
            self.risk.max_leverage is not None and self.risk.max_leverage > 1
        ):
            raise ValueError("forward A-share paper requires unlevered buying-power enforcement")
        if self.risk.max_drawdown is not None and not (-1 <= self.risk.max_drawdown <= 0):
            raise ValueError("forward paper drawdown must be between -1 and 0")
        self.risk.max_leverage = Decimal(1)
        if self.risk.max_drawdown is None:
            self.risk.max_drawdown = Decimal("-0.2")
        return self


CreatePaperSessionRequest = (
    ReplayPaperSessionRequest
    | SimulatedASharePaperSessionRequest
    | HistoricalASharePaperSessionRequest
    | ForwardASharePaperSessionRequest
)


class PaperProviderCapability(StrictModel):
    provider_type: Literal["replay", "simulated_a_share", "historical_a_share"]
    dataset_id: Literal[
        "AAPL_fixture",
        "CN_A_SIMULATED_PAPER_FIXTURE_V1",
        "cn-a-research-20100101-20251231-v1",
    ]
    symbol: Literal["AAPL", "CN-A"]
    available: bool = Field(strict=True)
    reason_code: (
        Literal[
            "REPLAY_DATA_UNAVAILABLE",
            "REPLAY_DATA_INVALID",
            "DATASET_NOT_REGISTERED",
            "DATASET_NOT_MOUNTED",
            "DATASET_INTEGRITY_FAILED",
            "SOURCE_CONTRACT_INTEGRITY_FAILED",
            "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED",
            "DATASET_EXECUTION_NOT_ACCEPTED",
            "PAPER_CAPABILITY_CHECK_FAILED",
        ]
        | None
    )

    @model_validator(mode="after")
    def consistent_capability(self) -> "PaperProviderCapability":
        identities = {
            "replay": ("AAPL_fixture", "AAPL"),
            "simulated_a_share": ("CN_A_SIMULATED_PAPER_FIXTURE_V1", "CN-A"),
            "historical_a_share": ("cn-a-research-20100101-20251231-v1", "CN-A"),
        }
        if identities[self.provider_type] != (self.dataset_id, self.symbol):
            raise ValueError("paper provider capability identity mismatch")
        if self.available != (self.reason_code is None):
            raise ValueError("paper capability availability and reason disagree")
        return self


class ForwardPaperCapability(StrictModel):
    available: Literal[False]
    reason_code: Literal["FORWARD_NOT_AVAILABLE"]


class PaperCapabilitiesResponse(StrictModel):
    providers: list[PaperProviderCapability] = Field(min_length=3, max_length=3)
    forward: ForwardPaperCapability

    @model_validator(mode="after")
    def supported_providers(self) -> "PaperCapabilitiesResponse":
        if [item.provider_type for item in self.providers] != [
            "replay",
            "simulated_a_share",
            "historical_a_share",
        ]:
            raise ValueError("paper capabilities must identify each supported provider in order")
        return self


class PaperSessionResponse(BaseModel):
    session_id: UUID
    status: PaperSessionStatus
    provider_type: str
    dataset_id: str
    symbol: str
    strategy_type: str
    strategy_parameters: dict[str, object]
    initial_cash: str
    default_order_quantity: str
    risk: dict[str, object]
    created_at: datetime
    started_at: datetime | None
    stopped_at: datetime | None
    error_message: str | None


class PaperSessionPage(BaseModel):
    items: list[PaperSessionResponse]
    limit: int
    offset: int
    total: int


class SessionStatusPayload(BaseModel):
    status: PaperSessionStatus


class MarketBarPayload(BaseModel):
    symbol: str
    timestamp: datetime
    open: str
    high: str
    low: str
    close: str
    volume: str


class MarketSessionPayload(BaseModel):
    trading_date: date
    security_count: int = Field(ge=0)
    source: Literal[
        "SIMULATED_SCENARIO_NOT_RESEARCH_EVIDENCE_V1",
        "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
        "RECEIPT_BOUND_FORWARD_A_SHARE_V1",
    ]
    input_provenance: DailyInput | None = Field(
        default=None, exclude_if=lambda value: value is None
    )

    @model_validator(mode="after")
    def validate_input(self) -> "MarketSessionPayload":
        if self.source == "RECEIPT_BOUND_FORWARD_A_SHARE_V1":
            if (
                self.input_provenance is None
                or self.trading_date != self.input_provenance.trading_date
                or self.security_count != len(self.input_provenance.receipts)
            ):
                raise ValueError("forward market session requires bound input provenance")
        elif self.input_provenance is not None:
            raise ValueError("legacy market source cannot claim forward input provenance")
        return self


class PaperOrderResponse(BaseModel):
    order_id: UUID
    strategy_id: str
    symbol: str
    side: str
    order_type: str
    quantity: str
    price: str | None
    status: str
    created_at: datetime
    cancellation_reason_code: str | None = Field(
        default=None, exclude_if=lambda value: value is None
    )


class PositionPayload(BaseModel):
    symbol: str
    quantity: str
    average_price: str
    market_price: str
    unrealized_pnl: str
    realized_pnl: str


class PortfolioPayload(BaseModel):
    timestamp: datetime
    cash: str
    market_value: str
    equity: str
    realized_pnl: str
    unrealized_pnl: str
    cumulative_commission: str
    drawdown: str
    positions: list[PositionPayload]
    plan: dict[str, Any] | None = None
    input_provenance: DailyInput | None = Field(
        default=None, exclude_if=lambda value: value is None
    )
    accounting_version: Literal["PNL_BREAKDOWN_V1"] | None = None
    corporate_action_realized_pnl: str | None = Field(
        default=None, strict=True, pattern=r"^-?[0-9]+(?:\.[0-9]+)?$"
    )
    total_pnl: str | None = Field(default=None, strict=True, pattern=r"^-?[0-9]+(?:\.[0-9]+)?$")

    @model_validator(mode="after")
    def validate_accounting(self) -> "PortfolioPayload":
        if self.input_provenance is not None:
            if self.timestamp.astimezone(ZONE).date() != self.input_provenance.trading_date:
                raise ValueError("forward portfolio input date mismatch")
            if self.plan is None or self.plan.get(
                "input_provenance"
            ) != self.input_provenance.model_dump(mode="json"):
                raise ValueError("forward portfolio plan input mismatch")
        if self.accounting_version is None:
            if self.corporate_action_realized_pnl is not None or self.total_pnl is not None:
                raise ValueError("paper PnL breakdown requires an accounting version")
        elif self.corporate_action_realized_pnl is None or self.total_pnl is None:
            raise ValueError("versioned paper PnL breakdown requires both amounts")
        return self


PaperPayload = (
    SessionStatusPayload
    | MarketBarPayload
    | MarketSessionPayload
    | SignalResponse
    | RiskDecisionResponse
    | PaperOrderResponse
    | FillResponse
    | PortfolioPayload
    | CalendarObservation
    | InputCommitObservation
)


class PaperEventResponse(BaseModel):
    sequence: int
    type: Literal[
        "session.status",
        "market.bar",
        "market.session",
        "signal.created",
        "risk.decision",
        "order.updated",
        "fill.created",
        "portfolio.snapshot",
        "calendar.observed",
        "input.committed",
    ]
    occurred_at: datetime
    payload: PaperPayload

    @model_validator(mode="after")
    def validate_calendar_event(self) -> "PaperEventResponse":
        expected_payload = {
            "session.status": SessionStatusPayload,
            "market.bar": MarketBarPayload,
            "market.session": MarketSessionPayload,
            "signal.created": SignalResponse,
            "risk.decision": RiskDecisionResponse,
            "order.updated": PaperOrderResponse,
            "fill.created": FillResponse,
            "portfolio.snapshot": PortfolioPayload,
            "calendar.observed": CalendarObservation,
            "input.committed": InputCommitObservation,
        }[self.type]
        if not isinstance(self.payload, expected_payload):
            raise ValueError("paper event payload does not match its event type")
        if self.type == "calendar.observed":
            if not isinstance(self.payload, CalendarObservation):
                raise ValueError("calendar event requires a calendar observation")
            if self.occurred_at != self.payload.applied_at:
                raise ValueError("calendar application timestamp mismatch")
        if isinstance(self.payload, InputCommitObservation) and (
            self.occurred_at != self.payload.commit_observed_at
            or self.sequence <= self.payload.journal_last_sequence
        ):
            raise ValueError("forward commit event timestamp/sequence mismatch")
        return self


class PaperStateResponse(BaseModel):
    session: PaperSessionResponse
    last_sequence: int
    latest_bar: MarketBarPayload | None
    latest_session: MarketSessionPayload | None = None
    latest_portfolio: PortfolioPayload | None
    last_rebalance_plan: dict[str, Any] | None = None
    current_dataset_quality: str | None = None
    current_source_integrity: str | None = None


class PaperSnapshotResponse(PaperStateResponse):
    signals: list[SignalResponse]
    risk_decisions: list[RiskDecisionResponse]
    orders: list[PaperOrderResponse]
    fills: list[FillResponse]


PaperCollectionKind = Literal["signals", "risk_decisions", "orders", "fills"]


class PaperCollectionPage(BaseModel):
    session_id: UUID
    collection: PaperCollectionKind
    as_of_sequence: int
    limit: int
    offset: int
    total: int
    items: list[PaperEventResponse]
