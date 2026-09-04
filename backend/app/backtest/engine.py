from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import NAMESPACE_URL, uuid5

from app.backtest.clock import SimulationClock
from app.backtest.config import BacktestConfig
from app.backtest.result import BacktestResult
from app.data.providers import MarketDataProvider, Timeframe
from app.domain.common import normalize_symbol
from app.domain.market import Bar
from app.domain.trading import Order, OrderSide, OrderType, Signal, SignalType
from app.event import Event, EventBus, EventType
from app.execution import SimulatedBroker
from app.strategies import BaseStrategy, StrategyEngine


class BacktestError(ValueError):
    """Base error for deterministic backtest coordination failures."""


class BacktestDataError(BacktestError):
    """Raised when a provider violates the historical Bar contract."""


class DuplicateSignalError(BacktestError):
    """Raised when identical trading intent is delivered more than once."""


class BacktestEngine:
    """Coordinate completed bars, strategies, orders, and next-open fills."""

    def __init__(
        self,
        provider: MarketDataProvider,
        strategies: Sequence[BaseStrategy],
        config: BacktestConfig,
        event_bus: EventBus | None = None,
    ) -> None:
        self._provider = provider
        self._config = config
        self._event_bus = event_bus or EventBus()
        self._clock = SimulationClock()
        self._strategy_engine = StrategyEngine(self._event_bus)
        for strategy in strategies:
            self._strategy_engine.register(strategy)
        self._broker = SimulatedBroker(
            self._event_bus,
            config.commission_model,
            config.slippage_model,
        )
        self._signals: list[Signal] = []
        self._seen_signals: set[tuple[str, str, datetime, SignalType]] = set()
        self._running = False
        self._event_bus.subscribe(EventType.SIGNAL, self._on_signal)

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def clock(self) -> SimulationClock:
        return self._clock

    def run(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> BacktestResult:
        bars = self._provider.get_historical_bars(symbol, start, end, timeframe)
        self._validate_bars(normalize_symbol(symbol), bars)
        self.reset()
        self._running = True
        try:
            for bar in bars:
                self._clock.advance(bar.timestamp)
                self._broker.execute_pending(bar)
                self._event_bus.publish(
                    Event(EventType.MARKET_DATA, bar, occurred_at=bar.timestamp)
                )
        finally:
            self._running = False

        return BacktestResult(
            signals=tuple(self._signals),
            orders=self._broker.orders,
            fills=self._broker.fills,
            start_time=bars[0].timestamp if bars else None,
            end_time=bars[-1].timestamp if bars else None,
            configuration=self._config,
        )

    def reset(self) -> None:
        if self._running:
            raise BacktestError("cannot reset a running backtest")
        self._clock.reset()
        self._strategy_engine.reset()
        self._broker.reset()
        self._signals.clear()
        self._seen_signals.clear()

    def _on_signal(self, event: Event[Any]) -> None:
        if not self._running:
            raise BacktestError("received SIGNAL outside an active backtest")
        if not isinstance(event.payload, Signal):
            raise TypeError("SIGNAL event payload must be a Signal")
        signal = event.payload
        if signal.timestamp != self._clock.current_time:
            raise BacktestError("signal timestamp must equal the current simulation time")

        signal_key = (
            signal.strategy_id,
            signal.symbol,
            signal.timestamp,
            signal.signal_type,
        )
        if signal_key in self._seen_signals:
            raise DuplicateSignalError("duplicate signal received during backtest")
        self._seen_signals.add(signal_key)
        self._signals.append(signal)

        side = self._side_for(signal.signal_type)
        if side is None:
            return
        order = Order(
            id=uuid5(
                NAMESPACE_URL,
                ":".join(
                    (
                        "quant-trading-platform",
                        signal.strategy_id,
                        signal.symbol,
                        signal.timestamp.isoformat(),
                        signal.signal_type.value,
                    )
                ),
            ),
            strategy_id=signal.strategy_id,
            symbol=signal.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=self._config.default_order_quantity,
            created_at=signal.timestamp,
        )
        self._event_bus.publish(Event(EventType.ORDER_CREATED, order, occurred_at=order.created_at))
        self._broker.submit(order)

    @staticmethod
    def _side_for(signal_type: SignalType) -> OrderSide | None:
        if signal_type is SignalType.BUY:
            return OrderSide.BUY
        if signal_type is SignalType.SELL:
            return OrderSide.SELL
        return None

    @staticmethod
    def _validate_bars(symbol: str, bars: tuple[Bar, ...]) -> None:
        previous: Bar | None = None
        for bar in bars:
            if bar.symbol != symbol:
                raise BacktestDataError(
                    f"provider returned {bar.symbol} while backtesting {symbol}"
                )
            if previous is not None and bar.timestamp <= previous.timestamp:
                raise BacktestDataError(
                    f"bars must be strictly chronological: "
                    f"{previous.timestamp.isoformat()} then {bar.timestamp.isoformat()}"
                )
            previous = bar
