from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from app.domain.market import Bar


class Timeframe(StrEnum):
    DAY_1 = "1d"


@runtime_checkable
class MarketDataProvider(Protocol):
    """Vendor-neutral source of normalized completed market bars."""

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> tuple[Bar, ...]: ...
