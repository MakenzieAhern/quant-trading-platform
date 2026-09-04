from collections.abc import Sequence
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from itertools import pairwise

INDICATOR_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)
ONE_HUNDRED = Decimal(100)


@dataclass(frozen=True, slots=True)
class MACDResult:
    line: Decimal
    signal: Decimal
    histogram: Decimal


@dataclass(frozen=True, slots=True)
class BollingerBandsResult:
    middle: Decimal
    upper: Decimal
    lower: Decimal


def _validate_period(period: int, name: str = "period") -> None:
    if isinstance(period, bool) or not isinstance(period, int) or period <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_values(values: Sequence[Decimal]) -> None:
    for value in values:
        if not isinstance(value, Decimal):
            raise TypeError("indicator values must be Decimal instances")
        if not value.is_finite():
            raise ValueError("indicator values must be finite")


def sma(values: Sequence[Decimal], period: int) -> Decimal | None:
    """Return the mean of the latest `period` values after a complete warm-up."""
    _validate_period(period)
    _validate_values(values)
    if len(values) < period:
        return None
    with localcontext(INDICATOR_CONTEXT):
        return sum(values[-period:], ZERO) / Decimal(period)


def _ema_series(values: Sequence[Decimal], period: int) -> list[Decimal | None]:
    results: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return results

    with localcontext(INDICATOR_CONTEXT):
        seed = sum(values[:period], ZERO) / Decimal(period)
        results[period - 1] = seed
        alpha = Decimal(2) / Decimal(period + 1)
        previous = seed
        for index in range(period, len(values)):
            previous = values[index] * alpha + previous * (Decimal(1) - alpha)
            results[index] = previous
    return results


def ema(values: Sequence[Decimal], period: int) -> Decimal | None:
    """Return an EMA seeded by the SMA of the first `period` observations."""
    _validate_period(period)
    _validate_values(values)
    if not values:
        return None
    return _ema_series(values, period)[-1]


def _rsi_from_averages(average_gain: Decimal, average_loss: Decimal) -> Decimal:
    if average_loss == ZERO:
        return ONE_HUNDRED if average_gain > ZERO else Decimal(50)
    if average_gain == ZERO:
        return ZERO
    relative_strength = average_gain / average_loss
    return ONE_HUNDRED - ONE_HUNDRED / (Decimal(1) + relative_strength)


def rsi(values: Sequence[Decimal], period: int) -> Decimal | None:
    """Return Wilder RSI, seeded from the first `period` price changes.

    A flat window returns 50, an all-gain window returns 100, and an all-loss
    window returns 0. At least `period + 1` prices are required.
    """
    _validate_period(period)
    _validate_values(values)
    if len(values) <= period:
        return None

    with localcontext(INDICATOR_CONTEXT):
        changes = [current - previous for previous, current in pairwise(values)]
        gains = [max(change, ZERO) for change in changes]
        losses = [max(-change, ZERO) for change in changes]
        average_gain = sum(gains[:period], ZERO) / Decimal(period)
        average_loss = sum(losses[:period], ZERO) / Decimal(period)

        for gain, loss in zip(gains[period:], losses[period:], strict=True):
            average_gain = (average_gain * Decimal(period - 1) + gain) / Decimal(period)
            average_loss = (average_loss * Decimal(period - 1) + loss) / Decimal(period)

        return _rsi_from_averages(average_gain, average_loss)


def macd(
    values: Sequence[Decimal],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> MACDResult | None:
    """Return MACD after both price EMAs and the SMA-seeded signal EMA warm up."""
    _validate_period(fast_period, "fast_period")
    _validate_period(slow_period, "slow_period")
    _validate_period(signal_period, "signal_period")
    if fast_period >= slow_period:
        raise ValueError("fast_period must be less than slow_period")
    _validate_values(values)

    fast_values = _ema_series(values, fast_period)
    slow_values = _ema_series(values, slow_period)
    with localcontext(INDICATOR_CONTEXT):
        macd_values = [
            fast_value - slow_value
            for fast_value, slow_value in zip(fast_values, slow_values, strict=True)
            if fast_value is not None and slow_value is not None
        ]
    signal_value = ema(macd_values, signal_period)
    if signal_value is None:
        return None

    with localcontext(INDICATOR_CONTEXT):
        line = macd_values[-1]
        return MACDResult(line=line, signal=signal_value, histogram=line - signal_value)


def bollinger_bands(
    values: Sequence[Decimal],
    period: int = 20,
    standard_deviations: Decimal = Decimal(2),
) -> BollingerBandsResult | None:
    """Return bands using population standard deviation after full warm-up."""
    _validate_period(period)
    if not isinstance(standard_deviations, Decimal):
        raise TypeError("standard_deviations must be a Decimal instance")
    if not standard_deviations.is_finite() or standard_deviations <= ZERO:
        raise ValueError("standard_deviations must be positive and finite")
    _validate_values(values)
    if len(values) < period:
        return None

    with localcontext(INDICATOR_CONTEXT):
        window = values[-period:]
        middle = sum(window, ZERO) / Decimal(period)
        variance = sum(((value - middle) ** 2 for value in window), ZERO) / Decimal(period)
        width = standard_deviations * variance.sqrt()
        return BollingerBandsResult(
            middle=middle,
            upper=middle + width,
            lower=middle - width,
        )
