"""Pure downstream analytics over immutable portfolio snapshots."""

from app.analytics.performance import (
    AnalyticsConfig,
    AnalyticsEngine,
    AnalyticsInputError,
    build_equity_curve,
    calculate_cagr,
    calculate_max_drawdown,
    calculate_period_returns,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_total_return,
)

__all__ = [
    "AnalyticsConfig",
    "AnalyticsEngine",
    "AnalyticsInputError",
    "build_equity_curve",
    "calculate_cagr",
    "calculate_max_drawdown",
    "calculate_period_returns",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_total_return",
]
