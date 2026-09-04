from dataclasses import dataclass
from datetime import datetime

from app.backtest.config import BacktestConfig
from app.domain.trading import Fill, Order, Signal


@dataclass(frozen=True, slots=True)
class BacktestResult:
    signals: tuple[Signal, ...]
    orders: tuple[Order, ...]
    fills: tuple[Fill, ...]
    start_time: datetime | None
    end_time: datetime | None
    configuration: BacktestConfig
