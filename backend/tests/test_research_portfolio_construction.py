from datetime import date
from decimal import Decimal

import pytest

from app.domain.markets import SecurityId
from app.research import (
    FactorValues,
    construct_equal_weight_portfolio,
    score_cross_section,
    select_top_decile,
)


def _security(index: int) -> SecurityId:
    return SecurityId(value=f"CN-A:SSE:{600000 + index:06d}")


def _factor(index: int) -> FactorValues:
    value = Decimal(index)
    return FactorValues(
        security_id=_security(index),
        as_of=date(2024, 1, 2),
        mom_12_1=value,
        trend_120=value * Decimal(2),
        vol20=Decimal(100) - value,
    )


def test_cross_section_scores_and_selects_top_decile_with_cap() -> None:
    result = score_cross_section(tuple(_factor(index) for index in range(100)))
    selected = select_top_decile(result)
    assert len(selected) == 10
    assert selected[0].security_id == _security(99)

    larger = score_cross_section(tuple(_factor(index) for index in range(300)))
    assert len(select_top_decile(larger)) == 20


def test_cross_section_tie_breaks_by_security_id() -> None:
    values = (
        FactorValues(_security(2), date(2024, 1, 2), Decimal(1), Decimal(3), Decimal(2)),
        FactorValues(_security(1), date(2024, 1, 2), Decimal(1), Decimal(3), Decimal(2)),
        FactorValues(_security(3), date(2024, 1, 2), Decimal(2), Decimal(1), Decimal(3)),
    )
    result = score_cross_section(values)
    assert result.scores[0].alpha_score == result.scores[1].alpha_score
    assert str(result.scores[0].security_id) < str(result.scores[1].security_id)


def test_invalid_factor_dispersion_stops_selection() -> None:
    result = score_cross_section(
        (
            FactorValues(_security(1), date(2024, 1, 2), Decimal(1), Decimal(1), Decimal(1)),
            FactorValues(_security(2), date(2024, 1, 2), Decimal(1), Decimal(2), Decimal(2)),
        )
    )
    assert result.scores == ()
    assert result.unavailable_factors == ("MOM_12_1",)


def test_fixed_candidate_uses_only_its_registered_factors() -> None:
    values = (
        FactorValues(_security(1), date(2024, 1, 2), Decimal(1), Decimal(7), Decimal(2)),
        FactorValues(_security(2), date(2024, 1, 2), Decimal(2), Decimal(7), Decimal(2)),
    )
    result = score_cross_section(values, factor_names=("MOM_12_1",))
    assert tuple(item.security_id for item in result.scores) == (_security(2), _security(1))
    assert all(item.trend_120_z == item.low_vol_z == 0 for item in result.scores)


def test_equal_weight_portfolio_rounds_down_to_board_lots_and_keeps_cash() -> None:
    selected = score_cross_section(tuple(_factor(index) for index in range(10))).scores[:2]
    prices = {score.security_id: Decimal("10.01") for score in selected}
    lots = {score.security_id: 100 for score in selected}
    target = construct_equal_weight_portfolio(
        selected,
        capital=Decimal("10000"),
        raw_reference_prices=prices,
        buy_lot_sizes=lots,
    )
    assert tuple(position.quantity for position in target.positions) == (
        Decimal(400),
        Decimal(400),
    )
    assert target.residual_cash == Decimal("1992.00")


def test_portfolio_rejects_adjusted_or_missing_reference_price() -> None:
    selected = score_cross_section(tuple(_factor(index) for index in range(10))).scores[:1]
    with pytest.raises(ValueError, match="raw reference price"):
        construct_equal_weight_portfolio(
            selected,
            capital=Decimal(1000),
            raw_reference_prices={},
            buy_lot_sizes={selected[0].security_id: 100},
        )
