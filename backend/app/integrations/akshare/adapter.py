from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Protocol

from app.data.providers.research import DailyBarRecord
from app.domain.markets import SecurityId


class AKShareSource(Protocol):
    """SDK-facing source that converts DataFrames to row mappings inside integration code."""

    @property
    def version(self) -> str: ...

    def daily_rows(self, symbol: str, start: date, end: date) -> Iterable[Mapping[str, object]]: ...


class AKShareProviderError(RuntimeError):
    pass


class AKShareValidationAdapter:
    provider_name = "AKShare"

    def __init__(self, source: AKShareSource) -> None:
        self._source = source
        self.provider_version = source.version

    def daily_bars(
        self, security_id: SecurityId, start: date, end: date
    ) -> tuple[DailyBarRecord, ...]:
        symbol = security_id.value.rsplit(":", maxsplit=1)[1]
        seen: set[date] = set()
        records: list[DailyBarRecord] = []
        for row in self._source.daily_rows(symbol, start, end):
            trading_date = _date(row.get("date"))
            if trading_date in seen:
                raise AKShareProviderError("AKSHARE_DUPLICATE_RECORD")
            seen.add(trading_date)
            records.append(
                DailyBarRecord(
                    security_id=security_id,
                    trading_date=trading_date,
                    raw_open=_decimal(row.get("open")),
                    raw_high=_decimal(row.get("high")),
                    raw_low=_decimal(row.get("low")),
                    raw_close=_decimal(row.get("close")),
                    volume=_decimal(row.get("volume")),
                    amount=_optional_decimal(row.get("amount")),
                    turnover=_optional_decimal(row.get("turnover")),
                )
            )
        return tuple(sorted(records, key=lambda item: item.trading_date))


def _date(value: object) -> date:
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise AKShareProviderError("AKSHARE_DATE_INVALID") from exc


def _decimal(value: object) -> Decimal:
    parsed = _optional_decimal(value)
    if parsed is None:
        raise AKShareProviderError("AKSHARE_DECIMAL_MISSING")
    return parsed


def _optional_decimal(value: object) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(str(value))
    except InvalidOperation as exc:
        raise AKShareProviderError("AKSHARE_DECIMAL_INVALID") from exc
    if not parsed.is_finite():
        raise AKShareProviderError("AKSHARE_DECIMAL_INVALID")
    return parsed
