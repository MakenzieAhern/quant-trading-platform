"""Provider- and framework-independent financial domain contracts."""

from app.domain.analytics import EquityPoint, PerformanceMetrics
from app.domain.market import Bar
from app.domain.trading import (
    Fill,
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PortfolioSnapshot,
    Position,
    Signal,
    SignalType,
)

__all__ = [
    "Bar",
    "EquityPoint",
    "Fill",
    "Order",
    "OrderSide",
    "OrderStatus",
    "OrderType",
    "PerformanceMetrics",
    "PortfolioSnapshot",
    "Position",
    "Signal",
    "SignalType",
]
