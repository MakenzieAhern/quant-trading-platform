from pydantic import Field

from app.domain.common import FiniteDecimal, NonNegativeDecimal, UtcDateTime
from app.domain.trading import DomainModel


class EquityPoint(DomainModel):
    timestamp: UtcDateTime
    equity: FiniteDecimal
    cash: FiniteDecimal
    market_value: FiniteDecimal


class PerformanceMetrics(DomainModel):
    initial_equity: FiniteDecimal
    final_equity: FiniteDecimal
    total_return: FiniteDecimal
    cagr: FiniteDecimal | None
    max_drawdown: FiniteDecimal
    sharpe_ratio: FiniteDecimal | None
    sortino_ratio: FiniteDecimal | None
    total_commission: NonNegativeDecimal
    number_of_fills: int = Field(ge=0)
