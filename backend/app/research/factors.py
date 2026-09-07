from datetime import date
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from itertools import pairwise

from app.domain.markets import SecurityId
from app.research.models import AdjustedClosePoint, FactorValues

FACTOR_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)
ONE = Decimal(1)


class FactorUnavailableError(ValueError):
    pass


def calculate_factors(
    security_id: SecurityId,
    as_of: date,
    history: tuple[AdjustedClosePoint, ...],
) -> FactorValues:
    _validate_history(as_of, history)
    if len(history) < 253:
        raise FactorUnavailableError("INSUFFICIENT_HISTORY")
    closes = tuple(point.adjusted_close for point in history)
    with localcontext(FACTOR_CONTEXT) as context:
        mom_12_1 = closes[-22] / closes[-253] - ONE
        sma120 = sum(closes[-120:], ZERO) / Decimal(120)
        trend120 = closes[-1] / sma120 - ONE
        returns = tuple(current / previous - ONE for previous, current in pairwise(closes[-21:]))
        mean = sum(returns, ZERO) / Decimal(20)
        variance = sum(((value - mean) ** 2 for value in returns), ZERO) / Decimal(20)
        vol20 = context.sqrt(variance)
    return FactorValues(
        security_id=security_id,
        as_of=as_of,
        mom_12_1=mom_12_1,
        trend_120=trend120,
        vol20=vol20,
    )


def _validate_history(as_of: date, history: tuple[AdjustedClosePoint, ...]) -> None:
    previous_date: date | None = None
    for point in history:
        if point.adjusted_close <= ZERO or not point.adjusted_close.is_finite():
            raise FactorUnavailableError("INVALID_ADJUSTED_CLOSE")
        if point.trading_date > as_of:
            raise FactorUnavailableError("LOOKAHEAD_DATA_REJECTED")
        if previous_date is not None and point.trading_date <= previous_date:
            raise FactorUnavailableError("NON_CHRONOLOGICAL_HISTORY")
        previous_date = point.trading_date
    if history and history[-1].trading_date != as_of:
        raise FactorUnavailableError("AS_OF_SESSION_MISSING")
