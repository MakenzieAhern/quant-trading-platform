from datetime import datetime

from app.data.providers.base import MarketDataProvider, Timeframe
from app.domain.market import Bar
from app.event.bus import EventBus
from app.event.events import Event, EventType


class MarketDataService:
    """Coordinate a provider and publish normalized bars without exposing its source."""

    def __init__(self, provider: MarketDataProvider, event_bus: EventBus) -> None:
        self._provider = provider
        self._event_bus = event_bus

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> tuple[Bar, ...]:
        bars = self._provider.get_historical_bars(symbol, start, end, timeframe)
        for bar in bars:
            self._event_bus.publish(
                Event(event_type=EventType.MARKET_DATA, payload=bar, occurred_at=bar.timestamp)
            )
        return bars
