from decimal import Decimal

from app.domain.market import Bar
from app.domain.trading import Signal, SignalType
from app.indicators import rsi
from app.strategies.base import BaseStrategy


class RSIMeanReversionStrategy(BaseStrategy):
    """Trade only RSI re-entry crossings from oversold or overbought regions."""

    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        rsi_period: int,
        oversold: Decimal,
        overbought: Decimal,
    ) -> None:
        if isinstance(rsi_period, bool) or not isinstance(rsi_period, int) or rsi_period <= 0:
            raise ValueError("rsi_period must be a positive integer")
        if not isinstance(oversold, Decimal) or not isinstance(overbought, Decimal):
            raise TypeError("RSI thresholds must be Decimal instances")
        if not oversold.is_finite() or not overbought.is_finite():
            raise ValueError("RSI thresholds must be finite")
        if not (Decimal(0) < oversold < overbought < Decimal(100)):
            raise ValueError("thresholds must satisfy 0 < oversold < overbought < 100")
        super().__init__(
            strategy_id,
            symbol,
            {
                "rsi_period": rsi_period,
                "oversold": oversold,
                "overbought": overbought,
            },
        )
        self._rsi_period = rsi_period
        self._oversold = oversold
        self._overbought = overbought
        self._closes: list[Decimal] = []
        self._previous_rsi: Decimal | None = None

    def _process_bar(self, bar: Bar) -> tuple[Signal, ...]:
        self._closes.append(bar.close)
        current_rsi = rsi(self._closes, self._rsi_period)
        if current_rsi is None:
            return ()

        signal_type = None
        if self._previous_rsi is not None:
            if self._previous_rsi <= self._oversold and current_rsi > self._oversold:
                signal_type = SignalType.BUY
            elif self._previous_rsi >= self._overbought and current_rsi < self._overbought:
                signal_type = SignalType.SELL
        self._previous_rsi = current_rsi

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
        self._previous_rsi = None
