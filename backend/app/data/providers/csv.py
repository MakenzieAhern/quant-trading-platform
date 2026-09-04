import csv
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from pydantic import ValidationError

from app.data.providers.base import Timeframe
from app.domain.common import ensure_utc, normalize_symbol
from app.domain.market import Bar

REQUIRED_COLUMNS = frozenset({"timestamp", "open", "high", "low", "close", "volume"})


class MarketDataError(ValueError):
    """Base error for provider input and source-data failures."""


class MarketDataSchemaError(MarketDataError):
    """Raised when a source does not contain the required structure."""


class MarketDataValidationError(MarketDataError):
    """Raised when a source row cannot become a valid domain bar."""


class DuplicateTimestampError(MarketDataValidationError):
    """Raised when a symbol has more than one bar for the same UTC instant."""


class CSVDataProvider:
    """Load `<SYMBOL>.csv` files and normalize every row into a domain `Bar`."""

    def __init__(self, data_directory: Path) -> None:
        self._data_directory = data_directory.expanduser().resolve()

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> tuple[Bar, ...]:
        normalized_symbol = normalize_symbol(symbol)
        if timeframe is not Timeframe.DAY_1:
            raise MarketDataError(f"unsupported CSV timeframe: {timeframe}")

        normalized_start = ensure_utc(start) if start is not None else None
        normalized_end = ensure_utc(end) if end is not None else None
        if (
            normalized_start is not None
            and normalized_end is not None
            and normalized_start > normalized_end
        ):
            raise MarketDataError("start must be less than or equal to end")

        bars = self._read_file(normalized_symbol)
        return tuple(
            bar
            for bar in bars
            if (normalized_start is None or bar.timestamp >= normalized_start)
            and (normalized_end is None or bar.timestamp <= normalized_end)
        )

    def _read_file(self, symbol: str) -> tuple[Bar, ...]:
        path = self._data_directory / f"{symbol}.csv"
        if not path.is_file():
            raise FileNotFoundError(f"market data file not found for {symbol}: {path}")

        with path.open(encoding="utf-8-sig", newline="") as source:
            reader = csv.DictReader(source)
            columns = set(reader.fieldnames or ())
            missing = REQUIRED_COLUMNS - columns
            if missing:
                missing_list = ", ".join(sorted(missing))
                raise MarketDataSchemaError(f"{path.name} is missing columns: {missing_list}")
            bars = tuple(
                self._parse_row(path, symbol, row_number, row)
                for row_number, row in enumerate(reader, 2)
            )

        timestamps: set[datetime] = set()
        for bar in bars:
            if bar.timestamp in timestamps:
                raise DuplicateTimestampError(
                    f"{path.name} contains duplicate UTC timestamp: {bar.timestamp.isoformat()}"
                )
            timestamps.add(bar.timestamp)
        return tuple(sorted(bars, key=lambda bar: bar.timestamp))

    @staticmethod
    def _parse_row(path: Path, symbol: str, row_number: int, row: dict[str, str | None]) -> Bar:
        try:
            values = {
                column: CSVDataProvider._required_value(row, column) for column in REQUIRED_COLUMNS
            }
            timestamp = datetime.fromisoformat(values["timestamp"].replace("Z", "+00:00"))
            return Bar(
                symbol=symbol,
                timestamp=timestamp,
                open=Decimal(values["open"]),
                high=Decimal(values["high"]),
                low=Decimal(values["low"]),
                close=Decimal(values["close"]),
                volume=int(values["volume"]),
            )
        except (InvalidOperation, ValueError, ValidationError) as exc:
            raise MarketDataValidationError(
                f"invalid market data in {path.name} at row {row_number}: {exc}"
            ) from exc

    @staticmethod
    def _required_value(row: dict[str, str | None], column: str) -> str:
        value = row.get(column)
        if value is None or not value.strip():
            raise MarketDataSchemaError(f"missing value for {column}")
        return value.strip()
