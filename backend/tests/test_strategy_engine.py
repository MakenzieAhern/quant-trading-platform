from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.data.providers import Timeframe
from app.data.services import MarketDataService
from app.domain.market import Bar
from app.domain.trading import Signal, SignalType
from app.event import Event, EventBus, EventType
from app.strategies import BaseStrategy, StrategyEngine


def make_bar(symbol: str = "AAPL") -> Bar:
    return Bar(
        symbol=symbol,
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        open=Decimal(100),
        high=Decimal(101),
        low=Decimal(99),
        close=Decimal(100),
        volume=Decimal(1000),
    )


class RecordingStrategy(BaseStrategy):
    def __init__(self, strategy_id: str, symbol: str, calls: list[str]) -> None:
        super().__init__(strategy_id, symbol, {})
        self.calls = calls
        self.seen = 0

    def _process_bar(self, bar: Bar) -> Sequence[Signal]:
        self.calls.append(self.strategy_id)
        self.seen += 1
        return (
            Signal(
                strategy_id=self.strategy_id,
                symbol=bar.symbol,
                timestamp=bar.timestamp,
                signal_type=SignalType.BUY,
            ),
        )

    def _reset_state(self) -> None:
        self.seen = 0


class SingleBarProvider:
    def __init__(self, bar: Bar) -> None:
        self.bar = bar

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> tuple[Bar, ...]:
        return (self.bar,)


def test_engine_processes_strategies_then_publishes_signals_in_registration_order() -> None:
    bus = EventBus()
    engine = StrategyEngine(bus)
    calls: list[str] = []
    published: list[Signal] = []
    engine.register(RecordingStrategy("A", "AAPL", calls))
    engine.register(RecordingStrategy("B", "AAPL", calls))
    bus.subscribe(EventType.SIGNAL, lambda event: published.append(event.payload))

    bar = make_bar()
    bus.publish(Event(EventType.MARKET_DATA, bar, occurred_at=bar.timestamp))

    assert calls == ["A", "B"]
    assert [signal.strategy_id for signal in published] == ["A", "B"]
    assert all(signal.timestamp == bar.timestamp for signal in published)


def test_market_data_service_to_strategy_engine_to_signal_event_flow() -> None:
    bar = make_bar()
    bus = EventBus()
    engine = StrategyEngine(bus)
    engine.register(RecordingStrategy("strategy", "AAPL", []))
    published: list[Signal] = []
    bus.subscribe(EventType.SIGNAL, lambda event: published.append(event.payload))

    returned_bars = MarketDataService(SingleBarProvider(bar), bus).get_historical_bars("AAPL")

    assert returned_bars == (bar,)
    assert len(published) == 1
    assert published[0].timestamp == bar.timestamp


def test_engine_routes_symbols_without_mixing_strategy_state() -> None:
    bus = EventBus()
    engine = StrategyEngine(bus)
    calls: list[str] = []
    aapl = RecordingStrategy("aapl", "AAPL", calls)
    msft = RecordingStrategy("msft", "MSFT", calls)
    engine.register(aapl)
    engine.register(msft)

    engine.process_bar(make_bar("AAPL"))

    assert calls == ["aapl"]
    assert aapl.seen == 1
    assert msft.seen == 0


def test_engine_rejects_duplicate_strategy_identity_and_invalid_event_payload() -> None:
    bus = EventBus()
    engine = StrategyEngine(bus)
    engine.register(RecordingStrategy("same", "AAPL", []))
    with pytest.raises(ValueError, match="already registered"):
        engine.register(RecordingStrategy("same", "MSFT", []))

    with pytest.raises(TypeError, match="payload must be a Bar"):
        bus.publish(Event(EventType.MARKET_DATA, "not-a-bar"))


def test_engine_reset_resets_every_registered_strategy() -> None:
    bus = EventBus()
    engine = StrategyEngine(bus)
    strategy = RecordingStrategy("A", "AAPL", [])
    engine.register(strategy)
    engine.process_bar(make_bar())
    assert strategy.seen == 1

    engine.reset()

    assert strategy.seen == 0
    assert engine.process_bar(make_bar())[0].strategy_id == "A"
