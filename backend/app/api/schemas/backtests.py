from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from app.application.backtests.decimal_policy import validate_storage_decimal
from app.application.backtests.models import BacktestRunStatus
from app.domain.common import Symbol, UtcDateTime


def _decimal_string(value: object) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("financial Decimal values must be JSON strings")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("invalid Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError("Decimal value must be finite")
    return validate_storage_decimal(parsed, "Decimal value")


DecimalString = Annotated[Decimal, BeforeValidator(_decimal_string)]
PositiveDecimalString = Annotated[Decimal, BeforeValidator(_decimal_string), Field(gt=0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MovingAverageParameters(StrictModel):
    short_period: int = Field(gt=0, strict=True)
    long_period: int = Field(gt=0, strict=True)


class MovingAverageStrategy(StrictModel):
    type: Literal["moving_average_crossover"]
    parameters: MovingAverageParameters


class RSIParameters(StrictModel):
    rsi_period: int = Field(gt=0, strict=True)
    oversold: DecimalString
    overbought: DecimalString


class RSIStrategy(StrictModel):
    type: Literal["rsi_mean_reversion"]
    parameters: RSIParameters


StrategyRequest = Annotated[MovingAverageStrategy | RSIStrategy, Field(discriminator="type")]


class RiskRequest(StrictModel):
    max_order_notional: DecimalString | None = None
    max_position_quantity: DecimalString | None = None
    max_symbol_exposure: DecimalString | None = None
    max_gross_exposure: DecimalString | None = None
    max_leverage: DecimalString | None = None
    enforce_buying_power: bool = False
    max_drawdown: DecimalString | None = None


class CreateBacktestRequest(StrictModel):
    dataset_id: str = Field(min_length=1, max_length=128)
    symbol: Symbol
    strategy: StrategyRequest
    initial_cash: PositiveDecimalString = Decimal("100000")
    default_order_quantity: PositiveDecimalString = Decimal("1")
    risk: RiskRequest = Field(default_factory=RiskRequest)
    start: UtcDateTime | None = None
    end: UtcDateTime | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> CreateBacktestRequest:
        if self.start is not None and self.end is not None and self.start > self.end:
            raise ValueError("start must be less than or equal to end")
        return self


class LinkSet(BaseModel):
    self: str
    result: str
    signals: str
    risk_decisions: str
    orders: str
    fills: str
    equity: str


class RunResponse(BaseModel):
    run_id: UUID
    status: BacktestRunStatus
    strategy_id: str
    strategy_type: str
    strategy_parameters: dict[str, object]
    symbol: str
    dataset_id: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    initial_cash: str
    default_order_quantity: str
    risk: dict[str, object]
    start: datetime | None
    end: datetime | None
    error_message: str | None
    metrics: MetricsResponse | None = None
    links: LinkSet


class CreateBacktestResponse(BaseModel):
    run_id: UUID
    status: BacktestRunStatus
    links: LinkSet


class MetricsResponse(BaseModel):
    initial_equity: str
    final_equity: str
    total_return: str
    cagr: str | None
    max_drawdown: str
    sharpe_ratio: str | None
    sortino_ratio: str | None
    total_commission: str
    number_of_fills: int


class ResultResponse(BaseModel):
    run_id: UUID
    status: BacktestRunStatus
    metrics: MetricsResponse
    signal_count: int
    proposal_count: int
    risk_decision_count: int
    risk_rejection_count: int
    order_count: int
    fill_count: int
    snapshot_count: int
    reservation_count: int
    start_time: datetime | None
    end_time: datetime | None


class SignalResponse(BaseModel):
    strategy_id: str
    symbol: str
    timestamp: datetime
    signal_type: str


class RiskDecisionResponse(BaseModel):
    proposal_id: UUID
    approved: bool
    reason_code: str
    message: str
    timestamp: datetime
    risk_increasing: bool
    reference_price: str | None
    order_notional: str | None
    projected_position_quantity: str | None
    projected_symbol_exposure: str | None
    projected_gross_exposure: str | None
    projected_net_exposure: str | None
    projected_gross_leverage: str | None
    projected_cash: str | None
    estimated_transaction_cost: str | None


class OrderResponse(BaseModel):
    order_id: UUID
    strategy_id: str
    symbol: str
    side: str
    order_type: str
    quantity: str
    price: str | None
    status: str
    created_at: datetime


class FillResponse(BaseModel):
    order_id: UUID
    strategy_id: str
    symbol: str
    side: str
    quantity: str
    price: str
    commission: str
    timestamp: datetime


class EquityResponse(BaseModel):
    timestamp: datetime
    equity: str
    cash: str
    market_value: str


class PageResponse[PageItemT](BaseModel):
    items: list[PageItemT]
    limit: int
    offset: int
    total: int
