from decimal import Decimal

import pytest

from app.research.analytics import ClosedTrade, analyze_research_period, rolling_compounded_returns


def test_research_analytics_calculates_trade_and_benchmark_metrics() -> None:
    result = analyze_research_period(
        equity=(Decimal("100"), Decimal("110"), Decimal("99"), Decimal("120")),
        benchmark_equity=(Decimal("100"), Decimal("105"), Decimal("104"), Decimal("110")),
        closed_trades=(
            ClosedTrade(Decimal("12"), 10),
            ClosedTrade(Decimal("-4"), 6),
            ClosedTrade(Decimal("0"), 2),
        ),
        turnover=Decimal("1.25"),
        transaction_costs=Decimal("3.50"),
        gross_exposures=(Decimal("0"), Decimal("0.9"), Decimal("0.8"), Decimal("1")),
        net_exposures=(Decimal("0"), Decimal("0.9"), Decimal("0.8"), Decimal("1")),
    )
    assert result.cumulative_return == Decimal("0.2")
    assert result.maximum_drawdown == Decimal("-0.1")
    assert result.win_rate == Decimal(1) / Decimal(3)
    assert result.profit_factor == Decimal("3")
    assert result.average_holding_period == Decimal("6")
    assert result.benchmark_return == Decimal("0.1")
    assert result.excess_return == Decimal("0.1")
    assert result.tracking_error is not None
    assert result.information_ratio is not None


def test_undefined_metrics_are_none_not_infinity_or_zero() -> None:
    result = analyze_research_period(equity=(Decimal("100"), Decimal("100"), Decimal("100")))
    assert result.sharpe_ratio is None
    assert result.sortino_ratio is None
    assert result.calmar_ratio is None
    assert result.win_rate is None
    assert result.profit_factor is None
    assert result.average_holding_period is None
    assert result.benchmark_return is None


def test_rolling_returns_preserve_warmup_as_none() -> None:
    assert rolling_compounded_returns((Decimal("0.1"), Decimal("-0.1"), Decimal("0.2")), 2) == (
        None,
        Decimal("-0.01"),
        Decimal("0.08"),
    )


def test_benchmark_must_be_aligned() -> None:
    with pytest.raises(ValueError, match="align"):
        analyze_research_period(
            equity=(Decimal("100"), Decimal("101")),
            benchmark_equity=(Decimal("100"),),
        )
