from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.data.providers.base import MarketDataProvider
from app.data.providers.csv import (
    CSVDataProvider,
    DuplicateTimestampError,
    MarketDataError,
    MarketDataSchemaError,
    MarketDataValidationError,
)

FIXTURE_DIRECTORY = Path(__file__).resolve().parent / "fixtures" / "market_data"


def test_provider_implements_contract_and_sorts_bars() -> None:
    provider = CSVDataProvider(FIXTURE_DIRECTORY)
    assert isinstance(provider, MarketDataProvider)

    bars = provider.get_historical_bars(" aapl ")

    assert len(bars) == 6
    assert all(bar.symbol == "AAPL" for bar in bars)
    assert [bar.timestamp for bar in bars] == sorted(bar.timestamp for bar in bars)
    assert all(bar.timestamp.tzinfo is UTC for bar in bars)


def test_provider_filters_inclusive_utc_date_range() -> None:
    bars = CSVDataProvider(FIXTURE_DIRECTORY).get_historical_bars(
        "AAPL",
        start=datetime(2024, 1, 3, tzinfo=UTC),
        end=datetime(2024, 1, 5, tzinfo=UTC),
    )
    assert [bar.timestamp.day for bar in bars] == [3, 4, 5]


def test_provider_rejects_reversed_or_naive_filters() -> None:
    provider = CSVDataProvider(FIXTURE_DIRECTORY)
    with pytest.raises(MarketDataError, match="start must"):
        provider.get_historical_bars(
            "AAPL",
            start=datetime(2024, 1, 3, tzinfo=UTC),
            end=datetime(2024, 1, 2, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="timestamp must include a timezone"):
        provider.get_historical_bars("AAPL", start=datetime(2024, 1, 2))


def write_csv(directory: Path, contents: str) -> CSVDataProvider:
    (directory / "AAPL.csv").write_text(contents, encoding="utf-8")
    return CSVDataProvider(directory)


def test_provider_rejects_missing_columns(tmp_path: Path) -> None:
    provider = write_csv(tmp_path, "timestamp,open,high,low,close\n")
    with pytest.raises(MarketDataSchemaError, match="missing columns: volume"):
        provider.get_historical_bars("AAPL")


@pytest.mark.parametrize(
    "row",
    [
        "2024-01-02T00:00:00Z,100,99,98,101,1000",
        "2024-01-02T00:00:00Z,100,101,98,,1000",
        "2024-01-02T00:00:00,100,101,98,100,1000",
        "2024-01-02T00:00:00Z,not-a-number,101,98,100,1000",
        "2024-01-02T00:00:00Z,100,101,98,100,-1",
        "2024-01-02T00:00:00Z,NaN,101,98,100,1000",
    ],
)
def test_provider_rejects_malformed_rows(tmp_path: Path, row: str) -> None:
    provider = write_csv(
        tmp_path,
        "timestamp,open,high,low,close,volume\n" + row + "\n",
    )
    with pytest.raises(MarketDataValidationError, match="row 2"):
        provider.get_historical_bars("AAPL")


def test_provider_rejects_duplicate_utc_timestamps(tmp_path: Path) -> None:
    provider = write_csv(
        tmp_path,
        "timestamp,open,high,low,close,volume\n"
        "2024-01-02T00:00:00Z,100,101,99,100,1000\n"
        "2024-01-02T11:00:00+11:00,100,101,99,100,1100\n",
    )
    with pytest.raises(DuplicateTimestampError, match="duplicate UTC timestamp"):
        provider.get_historical_bars("AAPL")


def test_provider_reports_missing_symbol_file() -> None:
    provider = CSVDataProvider(FIXTURE_DIRECTORY)
    with pytest.raises(FileNotFoundError, match="market data file not found"):
        provider.get_historical_bars("MSFT")


def test_provider_rejects_non_portable_symbol() -> None:
    provider = CSVDataProvider(FIXTURE_DIRECTORY)
    with pytest.raises(ValueError, match="letters, numbers"):
        provider.get_historical_bars("../AAPL")
