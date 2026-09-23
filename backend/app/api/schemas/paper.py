from datetime import date, datetime
from decimal import Decimal
from typing import Literal
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
    rebalance_sessions: int = Field(default=20, ge=1, le=252)
    maximum_holdings: int = Field(default=20, ge=1, le=100)
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


CreatePaperSessionRequest = (
    ReplayPaperSessionRequest
    | SimulatedASharePaperSessionRequest
    | HistoricalASharePaperSessionRequest
)


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
    ]


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


PaperPayload = (
    SessionStatusPayload
    | MarketBarPayload
    | MarketSessionPayload
    | SignalResponse
    | RiskDecisionResponse
    | PaperOrderResponse
    | FillResponse
    | PortfolioPayload
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
    ]
    occurred_at: datetime
    payload: PaperPayload


class PaperSnapshotResponse(BaseModel):
    session: PaperSessionResponse
    last_sequence: int
    latest_bar: MarketBarPayload | None
    latest_session: MarketSessionPayload | None = None
    signals: list[SignalResponse]
    risk_decisions: list[RiskDecisionResponse]
    orders: list[PaperOrderResponse]
    fills: list[FillResponse]
    latest_portfolio: PortfolioPayload | None
