from decimal import Decimal

from app.domain.market import Bar
from app.domain.trading import Signal, SignalType
from app.indicators import sma
from app.strategies.base import BaseStrategy


class MovingAverageCrossoverStrategy(BaseStrategy):
    """Emit intent only when the short SMA truly crosses the long SMA."""

    def __init__(self, strategy_id: str, symbol: str, short_window: int, long_window: int) -> None:
        if isinstance(short_window, bool) or not isinstance(short_window, int) or short_window <= 0:
            raise ValueError("short_window must be a positive integer")
        if isinstance(long_window, bool) or not isinstance(long_window, int) or long_window <= 0:
            raise ValueError("long_window must be a positive integer")
        if short_window >= long_window:
            raise ValueError("short_window must be less than long_window")
        super().__init__(
            strategy_id,
            symbol,
            {"short_window": short_window, "long_window": long_window},
        )
        self._short_window = short_window
        self._long_window = long_window
        self._closes: list[Decimal] = []
        self._previous_averages: tuple[Decimal, Decimal] | None = None

    def _process_bar(self, bar: Bar) -> tuple[Signal, ...]:
        self._closes.append(bar.close)
        short_average = sma(self._closes, self._short_window)
        long_average = sma(self._closes, self._long_window)
        if short_average is None or long_average is None:
            return ()

        signal_type = None
        if self._previous_averages is not None:
            previous_short, previous_long = self._previous_averages
            if previous_short <= previous_long and short_average > long_average:
                signal_type = SignalType.BUY
            elif previous_short >= previous_long and short_average < long_average:
                signal_type = SignalType.SELL
        self._previous_averages = (short_average, long_average)

        if signal_type is None:
            return ()
        return (
            Signal(
                strategy_id=self.strategy_id,
                symbol=bar.symbol,
                timestamp=bar.timestamp,
                signal_type=signal_type,
            ),
        )

    def _reset_state(self) -> None:
        self._closes.clear()
        self._previous_averages = None
