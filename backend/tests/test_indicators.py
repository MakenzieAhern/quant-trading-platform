from decimal import Decimal, localcontext

import pytest

from app.indicators import bollinger_bands, ema, macd, rsi, sma


def decimals(*values: str) -> list[Decimal]:
    return [Decimal(value) for value in values]


def test_sma_uses_only_latest_complete_window() -> None:
    assert sma(decimals("1", "2"), 3) is None
    assert sma(decimals("1", "2", "3", "4"), 3) == Decimal(3)


def test_ema_seeds_with_sma_then_applies_recurrence() -> None:
    values = decimals("1", "2", "3", "4", "5")
    assert ema(values[:2], 3) is None
    assert ema(values[:3], 3) == Decimal(2)
    assert ema(values[:4], 3) == Decimal(3)
    assert ema(values, 3) == Decimal(4)


def test_rsi_handles_rising_falling_and_flat_markets() -> None:
    assert rsi(decimals("1", "2", "3", "4"), 3) == Decimal(100)
    assert rsi(decimals("4", "3", "2", "1"), 3) == Decimal(0)
    assert rsi(decimals("2", "2", "2", "2"), 3) == Decimal(50)


def test_rsi_uses_wilder_smoothing_for_mixed_market() -> None:
    result = rsi(decimals("1", "2", "3", "2", "4"), 3)
    assert result == Decimal("83.33333333333333333333333333")


def test_rsi_warmup_and_bounds() -> None:
    assert rsi(decimals("1", "2", "3"), 3) is None
    result = rsi(decimals("10", "8", "9", "7", "11", "6", "12"), 3)
    assert result is not None
    assert Decimal(0) <= result <= Decimal(100)


def test_macd_has_explicit_signal_warmup_and_consistent_result() -> None:
    assert macd(decimals("1", "2", "3"), 2, 3, 2) is None

    result = macd(decimals("1", "2", "3", "4"), 2, 3, 2)

    assert result is not None
    assert result.line == Decimal("0.5")
    assert result.signal == Decimal("0.5")
    assert result.histogram == result.line - result.signal


def test_bollinger_bands_use_population_standard_deviation() -> None:
    assert bollinger_bands(decimals("1", "1", "3"), 4) is None

    result = bollinger_bands(decimals("1", "1", "3", "3"), 4)

    assert result is not None
    assert result.middle == Decimal(2)
    assert result.upper == Decimal(4)
    assert result.lower == Decimal(0)
    assert result.lower <= result.middle <= result.upper


@pytest.mark.parametrize("period", [0, -1, True])
def test_indicators_reject_invalid_periods(period: int) -> None:
    values = decimals("1", "2", "3")
    with pytest.raises(ValueError, match="positive integer"):
        sma(values, period)
    with pytest.raises(ValueError, match="positive integer"):
        ema(values, period)
    with pytest.raises(ValueError, match="positive integer"):
        rsi(values, period)


def test_macd_and_bollinger_validate_parameters() -> None:
    values = decimals("1", "2", "3")
    with pytest.raises(ValueError, match="fast_period must be less"):
        macd(values, 3, 3, 2)
    with pytest.raises(ValueError, match="signal_period"):
        macd(values, 2, 3, 0)
    with pytest.raises(ValueError, match="positive and finite"):
        bollinger_bands(values, standard_deviations=Decimal(0))


def test_indicators_require_decimal_and_use_a_fixed_decimal_context() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        sma([1.0], 1)  # type: ignore[list-item]
    with pytest.raises(TypeError, match="Decimal"):
        bollinger_bands(decimals("1"), standard_deviations=2)  # type: ignore[arg-type]

    with localcontext() as context:
        context.prec = 6
        result = rsi(decimals("1", "2", "3", "2", "4"), 3)
    assert result == Decimal("83.33333333333333333333333333")
