from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.backtest import SimulationClock, SimulationClockError


def test_simulation_clock_uses_historical_time_and_normalizes_utc() -> None:
    clock = SimulationClock()
    timestamp = datetime(2024, 1, 2, 11, tzinfo=timezone(timedelta(hours=11)))

    assert clock.current_time is None
    assert clock.advance(timestamp) == datetime(2024, 1, 2, tzinfo=UTC)
    assert clock.current_time == datetime(2024, 1, 2, tzinfo=UTC)


def test_simulation_clock_is_monotonic_and_resettable() -> None:
    clock = SimulationClock()
    first = datetime(2024, 1, 2, tzinfo=UTC)
    second = datetime(2024, 1, 3, tzinfo=UTC)
    clock.advance(first)
    assert clock.advance(first) == first
    assert clock.advance(second) == second

    with pytest.raises(SimulationClockError, match="cannot move backwards"):
        clock.advance(first)

    clock.reset()
    assert clock.current_time is None
    assert clock.advance(first) == first


def test_simulation_clock_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="timezone"):
        SimulationClock().advance(datetime(2024, 1, 2))
