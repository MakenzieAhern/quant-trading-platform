from datetime import UTC, datetime

from app.data.providers.base import MarketDataProvider, Timeframe
from app.data.services.market_data import MarketDataService
from app.domain.market import Bar
from app.event.bus import EventBus
from app.event.events import Event, EventType


class StubProvider:
    def __init__(self, bars: tuple[Bar, ...]) -> None:
        self.bars = bars
        self.calls: list[tuple[str, datetime | None, datetime | None, Timeframe]] = []

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> tuple[Bar, ...]:
        self.calls.append((symbol, start, end, timeframe))
        return self.bars


def test_service_uses_provider_and_publishes_each_market_bar() -> None:
    bars = tuple(
        Bar(
            symbol="AAPL",
            timestamp=datetime(2024, 1, day, tzinfo=UTC),
            open="100",
            high="102",
            low="99",
            close="101",
            volume=100,
        )
        for day in (2, 3)
    )
    provider = StubProvider(bars)
    assert isinstance(provider, MarketDataProvider)
    bus = EventBus()
    received: list[Event[object]] = []
    bus.subscribe(EventType.MARKET_DATA, received.append)
    service = MarketDataService(provider, bus)

    result = service.get_historical_bars("AAPL")

    assert result == bars
    assert provider.calls == [("AAPL", None, None, Timeframe.DAY_1)]
    assert [event.payload for event in received] == list(bars)
    assert [event.occurred_at for event in received] == [bar.timestamp for bar in bars]
