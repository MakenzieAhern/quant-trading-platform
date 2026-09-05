from datetime import datetime

from app.domain.common import ensure_utc


class SimulationClockError(ValueError):
    """Raised when historical simulation time attempts to move backwards."""


class SimulationClock:
    """A deterministic clock advanced only by historical timestamps."""

    def __init__(self) -> None:
        self._current_time: datetime | None = None

    @property
    def current_time(self) -> datetime | None:
        return self._current_time

    def advance(self, timestamp: datetime) -> datetime:
        normalized = ensure_utc(timestamp)
        if self._current_time is not None and normalized < self._current_time:
            raise SimulationClockError(
                f"simulation time cannot move backwards: "
                f"{self._current_time.isoformat()} -> {normalized.isoformat()}"
            )
        self._current_time = normalized
        return normalized

    def reset(self) -> None:
        self._current_time = None
