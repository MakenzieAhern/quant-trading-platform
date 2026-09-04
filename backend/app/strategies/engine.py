from typing import Any

from app.domain.market import Bar
from app.domain.trading import Signal
from app.event import Event, EventBus, EventType
from app.strategies.base import BaseStrategy


class StrategyEngine:
    """Route market bars to strategies and publish their signals synchronously."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._strategies: list[BaseStrategy] = []
        self._event_bus.subscribe(EventType.MARKET_DATA, self._on_market_data)

    @property
    def strategies(self) -> tuple[BaseStrategy, ...]:
        return tuple(self._strategies)

    def register(self, strategy: BaseStrategy) -> None:
        if any(registered.strategy_id == strategy.strategy_id for registered in self._strategies):
            raise ValueError(f"strategy_id is already registered: {strategy.strategy_id}")
        self._strategies.append(strategy)

    def process_bar(self, bar: Bar) -> tuple[Signal, ...]:
        signals = tuple(
            signal
            for strategy in tuple(self._strategies)
            if strategy.supports(bar.symbol)
            for signal in strategy.on_bar(bar)
        )
        for signal in signals:
            self._event_bus.publish(
                Event(event_type=EventType.SIGNAL, payload=signal, occurred_at=signal.timestamp)
            )
        return signals

    def reset(self) -> None:
        for strategy in self._strategies:
            strategy.reset()

    def _on_market_data(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Bar):
            raise TypeError("MARKET_DATA event payload must be a Bar")
        self.process_bar(event.payload)
