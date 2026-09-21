from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.api.schemas.backtests import (
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


CreatePaperSessionRequest = Annotated[
    ReplayPaperSessionRequest | SimulatedASharePaperSessionRequest,
    Field(discriminator="provider_type"),
]


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
    source: Literal["SIMULATED_SCENARIO_NOT_RESEARCH_EVIDENCE_V1"]


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
