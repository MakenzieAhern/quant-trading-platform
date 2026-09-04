from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.market import Bar


def make_bar(**overrides: object) -> Bar:
    values: dict[str, object] = {
        "symbol": " aapl ",
        "timestamp": datetime(2024, 1, 2, tzinfo=timezone(timedelta(hours=11))),
        "open": Decimal("100.00"),
        "high": Decimal("105.00"),
        "low": Decimal("99.00"),
        "close": Decimal("103.00"),
        "volume": 1000,
    }
    values.update(overrides)
    return Bar.model_validate(values)


def test_bar_normalizes_symbol_and_timestamp_to_utc() -> None:
    bar = make_bar()

    assert bar.symbol == "AAPL"
    assert bar.timestamp == datetime(2024, 1, 1, 13, tzinfo=UTC)
    assert bar.timestamp.tzinfo is UTC


def test_bar_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError, match="timestamp must include a timezone"):
        make_bar(timestamp=datetime(2024, 1, 2))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"high": Decimal("102"), "close": Decimal("103")}, "high must be"),
        ({"low": Decimal("101")}, "low must be"),
        ({"open": Decimal("0")}, "greater than 0"),
        ({"volume": -1}, "greater than or equal to 0"),
    ],
)
def test_bar_rejects_invalid_market_values(overrides: dict[str, object], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        make_bar(**overrides)


def test_bar_preserves_decimal_prices() -> None:
    bar = make_bar(close="103.1234", high="104")
    assert bar.close == Decimal("103.1234")


def test_bar_preserves_fractional_volume() -> None:
    bar = make_bar(volume="123.456")
    assert bar.volume == Decimal("123.456")
