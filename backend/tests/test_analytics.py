from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, Decimal, localcontext

import pytest

from app.analytics import (
    AnalyticsConfig,
    AnalyticsEngine,
    AnalyticsInputError,
    calculate_cagr,
    calculate_max_drawdown,
    calculate_period_returns,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_total_return,
)
from app.domain.analytics import EquityPoint

START = datetime(2024, 1, 1, tzinfo=UTC)


def point(day: int, equity: str) -> EquityPoint:
    value = Decimal(equity)
    return EquityPoint(
        timestamp=START + timedelta(days=day),
        equity=value,
        cash=value,
        market_value=Decimal(0),
    )


def test_total_and_period_returns_are_exact_decimals() -> None:
    curve = (point(0, "100"), point(1, "110"), point(2, "99"))

    assert calculate_total_return(Decimal(100), Decimal(120)) == Decimal("0.2")
    assert calculate_period_returns(curve) == (Decimal("0.1"), Decimal("-0.1"))

    with pytest.raises(AnalyticsInputError, match="initial_equity"):
        calculate_total_return(Decimal(0), Decimal(100))
    with pytest.raises(AnalyticsInputError, match="zero equity"):
        calculate_period_returns((point(0, "0"), point(1, "1")))


def test_max_drawdown_reports_negative_peak_to_trough_return() -> None:
    curve = tuple(point(day, value) for day, value in enumerate(("100", "120", "90", "110")))

    assert calculate_max_drawdown(curve) == Decimal("-0.25")
    with pytest.raises(AnalyticsInputError, match="chronological"):
        calculate_max_drawdown((point(1, "100"), point(0, "90")))


def test_sharpe_and_sortino_use_explicit_population_conventions() -> None:
    config = AnalyticsConfig(periods_per_year=1, risk_free_rate_per_period=Decimal(0))

    assert calculate_sharpe_ratio((Decimal("0.1"), Decimal("0.2")), config) == Decimal(3)
    assert calculate_sortino_ratio((Decimal("0.1"), Decimal("-0.05")), config) == Decimal(
        "0.7071067811865475244008443621"
    )
    assert calculate_sharpe_ratio((Decimal("0.1"),), config) is None
    assert calculate_sharpe_ratio((Decimal("0.1"), Decimal("0.1")), config) is None
    assert calculate_sortino_ratio((Decimal("0.1"), Decimal("0.2")), config) is None


def test_cagr_uses_a_365_2425_day_year_and_isolates_decimal_context() -> None:
    one_year = timedelta(seconds=31_556_952)

    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        result = calculate_cagr(Decimal(100), Decimal(121), START, START + one_year)
        assert context.prec == 6
        assert context.rounding == ROUND_DOWN

    assert result == Decimal("0.21")
    assert calculate_cagr(Decimal(100), Decimal(121), START, START) is None
    assert calculate_cagr(Decimal(100), Decimal(-1), START, START + one_year) is None
    with pytest.raises(AnalyticsInputError, match="timezone"):
        calculate_cagr(
            Decimal(100),
            Decimal(121),
            datetime(2024, 1, 1),
            datetime(2025, 1, 1),
        )


def test_empty_analytics_result_has_explicit_undefined_ratios() -> None:
    curve, metrics = AnalyticsEngine().analyze((), Decimal(1000), Decimal(0), 0, None, None)

    assert curve == ()
    assert metrics.initial_equity == metrics.final_equity == Decimal(1000)
    assert metrics.total_return == metrics.max_drawdown == Decimal(0)
    assert metrics.cagr is metrics.sharpe_ratio is metrics.sortino_ratio is None
    assert metrics.number_of_fills == 0
