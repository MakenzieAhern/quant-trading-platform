from datetime import UTC, datetime
from typing import Any

import pytest

from app.domain.market import Bar
from app.event.bus import EventBus
from app.event.events import Event, EventType


def test_one_subscriber_receives_event_payload() -> None:
    bus = EventBus()
    received: list[object] = []
    bus.subscribe(EventType.SIGNAL, lambda event: received.append(event.payload))

    bus.publish(Event(EventType.SIGNAL, {"side": "BUY"}))

    assert received == [{"side": "BUY"}]


def test_multiple_subscribers_execute_in_registration_order() -> None:
    bus = EventBus()
    calls: list[str] = []
    bus.subscribe(EventType.MARKET_DATA, lambda _: calls.append("first"))
    bus.subscribe(EventType.MARKET_DATA, lambda _: calls.append("second"))

    bus.publish(Event(EventType.MARKET_DATA, "bar"))

    assert calls == ["first", "second"]


def test_unsubscribe_removes_handler() -> None:
    bus = EventBus()
    received: list[Event[Any]] = []

    def handler(event: Event[Any]) -> None:
        received.append(event)

    bus.subscribe(EventType.SIGNAL, handler)
    assert bus.unsubscribe(EventType.SIGNAL, handler)
    assert not bus.unsubscribe(EventType.SIGNAL, handler)
    bus.publish(Event(EventType.SIGNAL, "ignored"))
    assert received == []


def test_duplicate_subscription_is_rejected() -> None:
    bus = EventBus()

    def handler(_: Event[Any]) -> None:
        pass

    bus.subscribe(EventType.SIGNAL, handler)
    with pytest.raises(ValueError, match="already subscribed"):
        bus.subscribe(EventType.SIGNAL, handler)


def test_handler_error_propagates_and_stops_later_handlers() -> None:
    bus = EventBus()
    calls: list[str] = []

    def failing(_: Event[Any]) -> None:
        calls.append("failing")
        raise RuntimeError("subscriber failed")

    bus.subscribe(EventType.SIGNAL, failing)
    bus.subscribe(EventType.SIGNAL, lambda _: calls.append("not-called"))

    with pytest.raises(RuntimeError, match="subscriber failed"):
        bus.publish(Event(EventType.SIGNAL, None))
    assert calls == ["failing"]


def test_market_data_event_contains_bar_and_uses_bar_time() -> None:
    bar = Bar(
        symbol="AAPL",
        timestamp=datetime(2024, 1, 2, tzinfo=UTC),
        open="100",
        high="102",
        low="99",
        close="101",
        volume=100,
    )
    event = Event(EventType.MARKET_DATA, bar, occurred_at=bar.timestamp)
    assert event.payload is bar
    assert event.occurred_at == bar.timestamp
