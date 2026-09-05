from dataclasses import dataclass
from datetime import datetime

from app.backtest.config import BacktestConfig
from app.domain.analytics import EquityPoint, PerformanceMetrics
from app.domain.trading import Fill, Order, PortfolioSnapshot, Signal


@dataclass(frozen=True, slots=True)
class BacktestResult:
    signals: tuple[Signal, ...]
    orders: tuple[Order, ...]
    fills: tuple[Fill, ...]
    portfolio_snapshots: tuple[PortfolioSnapshot, ...]
    equity_curve: tuple[EquityPoint, ...]
    performance_metrics: PerformanceMetrics
    start_time: datetime | None
    end_time: datetime | None
    configuration: BacktestConfig
