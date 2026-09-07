from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.domain.markets import SecurityId
from app.research import AdjustedClosePoint, FactorUnavailableError, calculate_factors
from app.research.standardization import population_z_scores
from app.research.winsorization import robust_winsorize


def _history(count: int = 253) -> tuple[AdjustedClosePoint, ...]:
    start = date(2020, 1, 1)
    return tuple(
        AdjustedClosePoint(start + timedelta(days=index), Decimal(100 + index))
        for index in range(count)
    )


def test_factor_formulas_use_only_completed_history() -> None:
    history = _history()
    result = calculate_factors(
        SecurityId(value="CN-A:SSE:600000"), history[-1].trading_date, history
    )
    assert result.mom_12_1 == Decimal(331) / Decimal(100) - Decimal(1)
    assert result.trend_120 == Decimal(352) / (sum(Decimal(233 + i) for i in range(120)) / 120) - 1
    assert result.vol20 > 0


def test_factor_requires_252_session_lookback_plus_completed_t() -> None:
    history = _history(252)
    with pytest.raises(FactorUnavailableError, match="INSUFFICIENT_HISTORY"):
        calculate_factors(SecurityId(value="CN-A:SSE:600000"), history[-1].trading_date, history)


def test_future_observation_is_rejected() -> None:
    history = _history()
    with pytest.raises(FactorUnavailableError, match="LOOKAHEAD"):
        calculate_factors(SecurityId(value="CN-A:SSE:600000"), history[-2].trading_date, history)


def test_robust_winsorization_caps_outlier_deterministically() -> None:
    values = {
        "a": Decimal(1),
        "b": Decimal(2),
        "c": Decimal(3),
        "d": Decimal(1000),
    }
    winsorized = robust_winsorize(values)
    assert winsorized["d"] < values["d"]
    assert robust_winsorize(values) == winsorized


def test_zero_dispersion_marks_factor_unavailable() -> None:
    assert population_z_scores({"a": Decimal(1), "b": Decimal(1)}) is None
