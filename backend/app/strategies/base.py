from abc import ABC, abstractmethod
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from types import MappingProxyType

from app.domain.common import normalize_symbol
from app.domain.market import Bar
from app.domain.trading import Signal

StrategyConfiguration = Mapping[str, int | Decimal]


class BarOrderError(ValueError):
    """Raised before strategy state can be corrupted by repeated or older data."""


class BaseStrategy(ABC):
    """Stateful single-symbol strategy consuming completed bars one at a time.

    Implementations can retain only state derived from bars already passed to
    `on_bar`. Duplicate and out-of-order timestamps fail before state changes.
    """

    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        configuration: StrategyConfiguration,
    ) -> None:
        normalized_id = strategy_id.strip()
        if not normalized_id:
            raise ValueError("strategy_id must not be empty")
        self._strategy_id = normalized_id
        self._symbol = normalize_symbol(symbol)
        self._configuration = MappingProxyType(dict(configuration))
        self._last_timestamp: datetime | None = None

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def configuration(self) -> StrategyConfiguration:
        return self._configuration

    def supports(self, symbol: str) -> bool:
        return normalize_symbol(symbol) == self.symbol

    def on_bar(self, bar: Bar) -> tuple[Signal, ...]:
        """Process one completed bar and return only newly generated intent."""
        if bar.symbol != self.symbol:
            raise ValueError(f"strategy {self.strategy_id} does not support {bar.symbol}")
        if self._last_timestamp is not None and bar.timestamp <= self._last_timestamp:
            raise BarOrderError(
                f"bar timestamp for {bar.symbol} must be strictly later than "
                f"{self._last_timestamp.isoformat()}"
            )

        signals = tuple(self._process_bar(bar))
        for signal in signals:
            if (
                signal.strategy_id != self.strategy_id
                or signal.symbol != bar.symbol
                or signal.timestamp != bar.timestamp
            ):
                raise ValueError("strategy emitted a signal inconsistent with its current bar")
        self._last_timestamp = bar.timestamp
        return signals

    def reset(self) -> None:
        """Discard all observed history so an identical replay is reproducible."""
        self._last_timestamp = None
        self._reset_state()

    @abstractmethod
    def _process_bar(self, bar: Bar) -> Sequence[Signal]: ...

    @abstractmethod
    def _reset_state(self) -> None: ...
