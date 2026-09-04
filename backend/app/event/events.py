from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TypeVar

from app.domain.common import ensure_utc

PayloadT = TypeVar("PayloadT")


class EventType(StrEnum):
    MARKET_DATA = "MARKET_DATA"
    SIGNAL = "SIGNAL"
    ORDER_CREATED = "ORDER_CREATED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_REJECTED = "ORDER_REJECTED"
    ORDER_PARTIALLY_FILLED = "ORDER_PARTIALLY_FILLED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CANCELLED = "ORDER_CANCELLED"
    POSITION_UPDATED = "POSITION_UPDATED"
    PORTFOLIO_UPDATED = "PORTFOLIO_UPDATED"
    RISK_REJECTED = "RISK_REJECTED"
    BACKTEST_STARTED = "BACKTEST_STARTED"
    BACKTEST_FINISHED = "BACKTEST_FINISHED"


@dataclass(frozen=True, slots=True)
class Event[PayloadT]:
    """An immutable domain event with a timezone-aware UTC occurrence time."""

    event_type: EventType
    payload: PayloadT
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        object.__setattr__(self, "occurred_at", ensure_utc(self.occurred_at))
