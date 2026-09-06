import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID


class PaperEventHub:
    """Fan out without blocking a runtime; slow consumers are told to rehydrate."""

    def __init__(self, queue_size: int = 64) -> None:
        if queue_size < 2:
            raise ValueError("queue_size must be at least two")
        self._queue_size = queue_size
        self._subscribers: dict[UUID, set[asyncio.Queue[dict[str, object]]]] = defaultdict(set)

    @asynccontextmanager
    async def subscribe(self, session_id: UUID) -> AsyncIterator[asyncio.Queue[dict[str, object]]]:
        queue: asyncio.Queue[dict[str, object]] = asyncio.Queue(self._queue_size)
        self._subscribers[session_id].add(queue)
        try:
            yield queue
        finally:
            self._subscribers[session_id].discard(queue)
            if not self._subscribers[session_id]:
                self._subscribers.pop(session_id, None)

    def publish(self, session_id: UUID, event: dict[str, object]) -> None:
        for queue in tuple(self._subscribers.get(session_id, ())):
            if queue.full():
                while not queue.empty():
                    queue.get_nowait()
                queue.put_nowait(
                    {
                        "sequence": None,
                        "type": "stream.resync_required",
                        "occurred_at": event["occurred_at"],
                        "payload": {"reason": "slow consumer; reload authoritative REST snapshot"},
                    }
                )
            queue.put_nowait(event)

    def subscriber_count(self, session_id: UUID) -> int:
        return len(self._subscribers.get(session_id, ()))
