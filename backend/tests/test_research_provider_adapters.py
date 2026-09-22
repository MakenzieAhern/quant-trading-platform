from collections.abc import Iterable, Mapping
from datetime import date
from decimal import Decimal

import pytest

from app.domain.markets import Board, CorporateActionCompleteness, CorporateActionType, SecurityId
from app.integrations.akshare import AKShareProviderError, AKShareValidationAdapter
from app.integrations.baostock import BaoStockAdapter, BaoStockProviderError


class FakeResult:
    def __init__(self, fields: list[str], rows: list[list[str]], error_code: str = "0") -> None:
        self.fields = fields
        self.error_code = error_code
        self._rows = iter(rows)
        self._current: list[str] = []

    def next(self) -> bool:
        try:
            self._current = next(self._rows)
        except StopIteration:
            return False
        return True

    def get_row_data(self) -> list[str]:
        return self._current


class FakeBoards:
    def resolve(self, security_id: SecurityId, as_of: date) -> Board:
        assert as_of == date(2024, 1, 2)
        return Board.SSE_MAIN


class FakeBaoStock:
    def query_all_stock(self, day: str) -> FakeResult:
        return FakeResult(["code", "tradeStatus", "code_name"], [["sh.600000", "1", "浦发银行"]])

    def query_stock_basic(self, code: str) -> FakeResult:
        return FakeResult(
            ["code", "code_name", "ipoDate", "outDate", "type", "status"],
            [[code, "浦发银行", "1999-11-10", "", "1", "1"]],
        )

    def query_trade_dates(self, *, start_date: str, end_date: str) -> FakeResult:
        return FakeResult(
            ["calendar_date", "is_trading_day"],
            [["2024-01-01", "0"], ["2024-01-02", "1"]],
        )

    def query_history_k_data_plus(
        self,
        code: str,
        fields: str,
        *,
        start_date: str,
        end_date: str,
        frequency: str,
        adjustflag: str,
    ) -> FakeResult:
        names = fields.split(",")
        if names == ["date", "code", "close"]:
            return FakeResult(names, [["2024-01-02", code, "9.0"]])
        if names == ["date", "code", "tradestatus", "isST"]:
            return FakeResult(names, [["2024-01-02", code, "1", "0"]])
        values = {
            "date": "2024-01-02",
            "code": code,
            "open": "10.0",
            "high": "10.5",
            "low": "9.8",
            "close": "10.0",
            "preclose": "9.9",
            "volume": "1000",
            "amount": "10000",
            "turn": "0.12",
            "tradestatus": "1",
            "isST": "0",
        }
        return FakeResult(names, [[values[name] for name in names]])

    def query_hs300_stocks(self, date: str) -> FakeResult:
        return FakeResult(["date", "code", "code_name"], [[date, "sh.600000", "浦发银行"]])

    def query_sz50_stocks(self, date: str) -> FakeResult:
        return self.query_hs300_stocks(date)

    def query_zz500_stocks(self, date: str) -> FakeResult:
        return self.query_hs300_stocks(date)

    def query_adjust_factor(self, code: str, *, start_date: str, end_date: str) -> FakeResult:
        return FakeResult(
            ["code", "dividOperateDate", "foreAdjustFactor", "backAdjustFactor", "adjustFactor"],
            [[code, "2024-01-02", "0.9", "1.1", "1.0"]],
        )

    def query_dividend_data(self, code: str, *, year: str, yearType: str) -> FakeResult:
        return FakeResult(
            [
                "code",
                "dividPreNoticeDate",
                "dividRegistDate",
                "dividOperateDate",
                "dividPayDate",
                "dividStockMarketDate",
                "dividCashPsBeforeTax",
                "dividStocksPs",
                "dividReserveToStockPs",
            ],
            [
                [
                    code,
                    "2023-12-01",
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-05",
                    "",
                    "0.10",
                    "0.20",
                    "0",
                ]
            ],
        )


def test_baostock_adapter_normalizes_raw_and_adjusted_data() -> None:
    adapter = BaoStockAdapter(FakeBaoStock(), provider_version="0.8.9", boards=FakeBoards())
    security_id = SecurityId(value="CN-A:SSE:600000")
    security = next(iter(adapter.securities(date(2024, 1, 2))))
    bar = next(iter(adapter.daily_bars(security_id, date(2024, 1, 2), date(2024, 1, 2))))
    status = next(iter(adapter.daily_status(security_id, date(2024, 1, 2), date(2024, 1, 2))))

    assert security.board is Board.SSE_MAIN
    assert bar.raw_close == Decimal("10.0")
    assert bar.adjusted_close == Decimal("9.0")
    assert bar.adjustment_factor == Decimal("0.9")
    assert status.status.is_suspended is False


def test_baostock_normalizes_adjustment_factors_and_economic_actions() -> None:
    adapter = BaoStockAdapter(FakeBaoStock(), provider_version="0.8.9", boards=FakeBoards())
    security_id = SecurityId(value="CN-A:SSE:600000")
    factors = adapter.adjustment_factors(security_id, date(2024, 1, 1), date(2024, 1, 3))
    actions = adapter.corporate_actions(security_id, date(2024, 1, 1), date(2024, 1, 3))

    assert factors[0].forward_factor == Decimal("0.9")
    assert [item.action_type for item in actions] == [
        CorporateActionType.CASH_DIVIDEND,
        CorporateActionType.STOCK_DIVIDEND,
    ]
    assert all(item.completeness is CorporateActionCompleteness.COMPLETE for item in actions)
    assert actions[0].cash_per_share == Decimal("0.10")
    assert actions[1].share_ratio == Decimal("0.20")


def test_baostock_adapter_rejects_malformed_rows() -> None:
    client = FakeBaoStock()
    client.query_trade_dates = lambda **_: FakeResult(["calendar_date"], [[]])  # type: ignore[method-assign]
    adapter = BaoStockAdapter(client, provider_version="0.8.9", boards=FakeBoards())
    with pytest.raises(BaoStockProviderError, match="ROW_INVALID"):
        tuple(adapter.trading_calendar(date(2024, 1, 1), date(2024, 1, 2)))


class FakeAKSource:
    version = "1.17.87"

    def daily_rows(self, symbol: str, start: date, end: date) -> Iterable[Mapping[str, object]]:
        return (
            {
                "date": "2024-01-02",
                "open": "10",
                "high": "11",
                "low": "9",
                "close": "10.5",
                "volume": "1000",
                "amount": "10500",
            },
        )


def test_akshare_adapter_is_validation_only_and_preserves_decimal_text() -> None:
    adapter = AKShareValidationAdapter(FakeAKSource())
    records = adapter.daily_bars(
        SecurityId(value="CN-A:SSE:600000"), date(2024, 1, 2), date(2024, 1, 2)
    )
    assert records[0].raw_close == Decimal("10.5")


def test_akshare_adapter_rejects_duplicate_dates() -> None:
    class Duplicates(FakeAKSource):
        def daily_rows(self, symbol: str, start: date, end: date) -> Iterable[Mapping[str, object]]:
            row = next(iter(super().daily_rows(symbol, start, end)))
            return (row, row)

    with pytest.raises(AKShareProviderError, match="DUPLICATE"):
        AKShareValidationAdapter(Duplicates()).daily_bars(
            SecurityId(value="CN-A:SSE:600000"), date(2024, 1, 2), date(2024, 1, 2)
        )
