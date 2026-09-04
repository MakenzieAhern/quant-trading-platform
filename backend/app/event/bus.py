from collections import defaultdict
from collections.abc import Callable
from typing import Any

from app.event.events import Event, EventType

EventHandler = Callable[[Event[Any]], None]


class EventBus:
    """Synchronous event dispatcher preserving subscriber registration order.

    Publishing is fail-fast: handler exceptions propagate immediately and later handlers
    are not called. A publish uses a subscriber snapshot, so subscription changes made by
    a handler affect only subsequent events.
    """

    def __init__(self) -> None:
        self._handlers: dict[EventType, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        handlers = self._handlers[event_type]
        if handler in handlers:
            raise ValueError(f"handler is already subscribed to {event_type}")
        handlers.append(handler)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> bool:
        handlers = self._handlers[event_type]
        if handler not in handlers:
            return False
        handlers.remove(handler)
        return True

    def publish(self, event: Event[Any]) -> None:
        for handler in tuple(self._handlers[event.event_type]):
            handler(event)
