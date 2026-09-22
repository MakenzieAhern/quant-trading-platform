from collections.abc import Iterable, Mapping
from datetime import date
from importlib import import_module
from typing import Any


class AKShareSdkSource:
    """Optional AKShare SDK boundary used only by ingestion and validation scripts."""

    def __init__(self) -> None:
        self._sdk: Any = import_module("akshare")
        self.version = str(self._sdk.__version__)

    def daily_rows(self, symbol: str, start: date, end: date) -> Iterable[Mapping[str, object]]:
        frame: Any = self._sdk.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start.strftime("%Y%m%d"),
            end_date=end.strftime("%Y%m%d"),
            adjust="",
        )
        for provider_row in frame.to_dict("records"):
            yield {
                "date": provider_row["日期"],
                "open": provider_row["开盘"],
                "high": provider_row["最高"],
                "low": provider_row["最低"],
                "close": provider_row["收盘"],
                # AKShare's Eastmoney endpoint reports volume in 100-share lots.
                "volume": str(provider_row["成交量"] * 100),
                "amount": provider_row["成交额"],
                "turnover": provider_row["换手率"],
            }
