from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.data.providers.research import DailyBarRecord, SecurityStatusRecord
from app.domain.markets import DailySecurityStatus, SecurityId
from app.research import (
    AdjustedClosePoint,
    FactorUnavailableError,
    FeatureOnlyDailyObservation,
    ResearchSession,
    calculate_factors,
)
from app.research.standardization import population_z_scores
from app.research.strategy import ChinaAMomentumLowVolResearchStrategy
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


def test_feature_only_close_and_amount_bounds_preserve_factor_history() -> None:
    security_id = SecurityId(value="CN-A:SZSE:300001")
    strategy = ChinaAMomentumLowVolResearchStrategy(minimum_average_daily_amount=Decimal(100))
    start = date(2010, 1, 1)
    for index in range(253):
        day = start + timedelta(days=index)
        if index == 250:
            session = ResearchSession(
                trading_date=day,
                bars=(),
                statuses=(),
                buy_lot_sizes=(),
                feature_only_observations=(
                    FeatureOnlyDailyObservation(
                        security_id=security_id,
                        trading_date=day,
                        raw_close=Decimal(100 + index),
                        adjusted_close=Decimal(100 + index),
                        volume_lower=Decimal(10),
                        volume_upper=Decimal(20),
                        amount_lower=Decimal(200),
                        amount_upper=Decimal(300),
                        lineage="OFFICIAL_PARTIAL_FEATURE_ONLY_NON_TRADABLE",
                    ),
                ),
            )
        else:
            close = Decimal(100 + index)
            session = ResearchSession(
                trading_date=day,
                bars=(
                    DailyBarRecord(
                        security_id=security_id,
                        trading_date=day,
                        raw_open=close,
                        raw_high=close,
                        raw_low=close,
                        raw_close=close,
                        volume=Decimal(10),
                        amount=Decimal(200),
                        adjusted_close=close,
                    ),
                ),
                statuses=(
                    SecurityStatusRecord(
                        status=DailySecurityStatus(
                            security_id=security_id,
                            trading_date=day,
                            is_st=False,
                            is_suspended=False,
                            is_tradeable=True,
                            source_version="fixture",
                        )
                    ),
                ),
                buy_lot_sizes=((security_id, 100),),
            )
        strategy.target_for_completed_session(session, Decimal(100000))
    assert tuple(value.security_id for value in strategy.last_factors) == (security_id,)


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
