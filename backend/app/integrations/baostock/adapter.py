from collections.abc import Iterable, Iterator, Mapping
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Protocol

from app.data.catalog.checksums import canonical_sha256
from app.data.providers.research import (
    AdjustmentFactorRecord,
    BenchmarkBarRecord,
    BenchmarkMembershipRecord,
    DailyBarRecord,
    SecurityRecord,
    SecurityStatusRecord,
    SessionRecord,
)
from app.domain.markets import (
    Board,
    CorporateAction,
    CorporateActionCompleteness,
    CorporateActionType,
    DailySecurityStatus,
    Exchange,
    SecurityId,
)


class BaoStockResult(Protocol):
    error_code: str
    fields: list[str]

    def next(self) -> bool: ...

    def get_row_data(self) -> list[str]: ...


class BaoStockClient(Protocol):
    def query_all_stock(self, day: str) -> BaoStockResult: ...

    def query_stock_basic(self, code: str) -> BaoStockResult: ...

    def query_trade_dates(self, *, start_date: str, end_date: str) -> BaoStockResult: ...

    def query_history_k_data_plus(
        self,
        code: str,
        fields: str,
        *,
        start_date: str,
        end_date: str,
        frequency: str,
        adjustflag: str,
    ) -> BaoStockResult: ...

    def query_hs300_stocks(self, date: str) -> BaoStockResult: ...

    def query_sz50_stocks(self, date: str) -> BaoStockResult: ...

    def query_zz500_stocks(self, date: str) -> BaoStockResult: ...

    def query_adjust_factor(
        self, code: str, *, start_date: str, end_date: str
    ) -> BaoStockResult: ...

    def query_dividend_data(self, code: str, *, year: str, yearType: str) -> BaoStockResult: ...


class BoardHistoryResolver(Protocol):
    def resolve(self, security_id: SecurityId, as_of: date) -> Board: ...


class BaoStockProviderError(RuntimeError):
    pass


class BaoStockAdapter:
    """Normalizes BaoStock cursor rows without exposing SDK objects to core code."""

    provider_name = "BaoStock"
    _DAILY_FIELDS = "date,code,open,high,low,close,preclose,volume,amount,turn,tradestatus,isST"

    def __init__(
        self,
        client: BaoStockClient,
        *,
        provider_version: str,
        boards: BoardHistoryResolver,
    ) -> None:
        self._client = client
        self.provider_version = provider_version
        self._boards = boards

    def securities(self, as_of: date) -> Iterable[SecurityRecord]:
        for row in _rows(self._client.query_all_stock(as_of.isoformat())):
            code = row.get("code", "")
            if not _is_equity_code(code):
                continue
            basic_rows = tuple(_rows(self._client.query_stock_basic(code)))
            if len(basic_rows) != 1:
                raise BaoStockProviderError("BAOSTOCK_SECURITY_BASIC_INVALID")
            basic = basic_rows[0]
            security_id, exchange, symbol = _identity(code)
            listing_date = _date(basic, "ipoDate")
            delisting_date = _optional_date(basic.get("outDate", ""))
            if listing_date > as_of or (delisting_date is not None and delisting_date < as_of):
                continue
            yield SecurityRecord(
                security_id=security_id,
                provider_code=code,
                symbol=symbol,
                name=basic.get("code_name") or row.get("code_name") or symbol,
                exchange=exchange,
                board=self._boards.resolve(security_id, as_of),
                listing_date=listing_date,
                delisting_date=delisting_date,
            )

    def trading_calendar(self, start: date, end: date) -> Iterable[SessionRecord]:
        result = self._client.query_trade_dates(
            start_date=start.isoformat(), end_date=end.isoformat()
        )
        return tuple(
            SessionRecord(
                session_date=_date(row, "calendar_date"),
                is_open=row.get("is_trading_day") == "1",
            )
            for row in _rows(result)
        )

    def daily_bars(
        self, security_id: SecurityId, start: date, end: date
    ) -> Iterable[DailyBarRecord]:
        code = _provider_code(security_id)
        raw = _daily_by_date(
            self._client.query_history_k_data_plus(
                code,
                self._DAILY_FIELDS,
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                frequency="d",
                adjustflag="3",
            )
        )
        adjusted = _daily_by_date(
            self._client.query_history_k_data_plus(
                code,
                "date,code,close",
                start_date=start.isoformat(),
                end_date=end.isoformat(),
                frequency="d",
                adjustflag="2",
            )
        )
        if set(raw) != set(adjusted):
            raise BaoStockProviderError("BAOSTOCK_ADJUSTED_DATE_MISMATCH")
        records = []
        for trading_date, row in sorted(raw.items()):
            adjusted_close = _decimal(adjusted[trading_date], "close")
            raw_close = _decimal(row, "close")
            records.append(
                DailyBarRecord(
                    security_id=security_id,
                    trading_date=trading_date,
                    raw_open=_decimal(row, "open"),
                    raw_high=_decimal(row, "high"),
                    raw_low=_decimal(row, "low"),
                    raw_close=raw_close,
                    pre_close=_optional_decimal(row.get("preclose", "")),
                    volume=_decimal(row, "volume"),
                    amount=_optional_decimal(row.get("amount", "")),
                    turnover=_optional_decimal(row.get("turn", "")),
                    adjustment_factor=adjusted_close / raw_close,
                    adjusted_close=adjusted_close,
                )
            )
        return tuple(records)

    def daily_status(
        self, security_id: SecurityId, start: date, end: date
    ) -> Iterable[SecurityStatusRecord]:
        code = _provider_code(security_id)
        result = self._client.query_history_k_data_plus(
            code,
            "date,code,tradestatus,isST",
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            frequency="d",
            adjustflag="3",
        )
        return tuple(
            SecurityStatusRecord(
                status=DailySecurityStatus(
                    security_id=security_id,
                    trading_date=_date(row, "date"),
                    is_st=row.get("isST") == "1",
                    is_suspended=row.get("tradestatus") != "1",
                    source_version=f"baostock-{self.provider_version}",
                )
            )
            for row in _rows(result)
        )

    def adjustment_factors(
        self, security_id: SecurityId, start: date, end: date
    ) -> tuple[AdjustmentFactorRecord, ...]:
        records = []
        for row in _rows(
            self._client.query_adjust_factor(
                _provider_code(security_id),
                start_date=start.isoformat(),
                end_date=end.isoformat(),
            )
        ):
            records.append(
                AdjustmentFactorRecord(
                    security_id=security_id,
                    ex_date=_date(row, "dividOperateDate"),
                    forward_factor=_decimal(row, "foreAdjustFactor"),
                    backward_factor=_decimal(row, "backAdjustFactor"),
                    adjustment_factor=_decimal(row, "adjustFactor"),
                    source_record_hash=canonical_sha256(dict(row)),
                )
            )
        return tuple(sorted(records, key=lambda item: item.ex_date))

    def corporate_actions(
        self, security_id: SecurityId, start: date, end: date
    ) -> tuple[CorporateAction, ...]:
        records: list[CorporateAction] = []
        for year in range(start.year, end.year + 1):
            result = self._client.query_dividend_data(
                _provider_code(security_id), year=str(year), yearType="operate"
            )
            for row in _rows(result):
                records.extend(self._normalize_dividend_row(security_id, row, start, end))
        return tuple(sorted(records, key=lambda item: (item.ex_date or date.max, item.action_type)))

    def _normalize_dividend_row(
        self,
        security_id: SecurityId,
        row: Mapping[str, str],
        start: date,
        end: date,
    ) -> tuple[CorporateAction, ...]:
        ex_date = _optional_date(row.get("dividOperateDate", ""))
        if ex_date is not None and not start <= ex_date <= end:
            return ()
        common = {
            "security_id": security_id,
            "announcement_date": _first_date(row, "dividPreNoticeDate", "dividPlanAnnounceDate"),
            "effective_date": ex_date,
            "record_date": _optional_date(row.get("dividRegistDate", "")),
            "ex_date": ex_date,
            "payment_date": _optional_date(row.get("dividPayDate", "")),
            "listing_date": _optional_date(row.get("dividStockMarketDate", "")),
            "source_provider": self.provider_name,
            "source_version": self.provider_version,
            "source_record_hash": canonical_sha256(dict(row)),
        }
        actions = []
        for action_type, field in (
            (CorporateActionType.CASH_DIVIDEND, "dividCashPsBeforeTax"),
            (CorporateActionType.STOCK_DIVIDEND, "dividStocksPs"),
            (CorporateActionType.BONUS_SHARE, "dividReserveToStockPs"),
        ):
            value = _optional_decimal(row.get(field, ""))
            if value is None or value <= 0:
                continue
            complete = ex_date is not None
            actions.append(
                CorporateAction.model_validate(
                    {
                        **common,
                        "action_type": action_type,
                        "cash_per_share": (
                            value
                            if action_type is CorporateActionType.CASH_DIVIDEND
                            else Decimal(0)
                        ),
                        "share_ratio": (
                            value
                            if action_type is not CorporateActionType.CASH_DIVIDEND
                            else Decimal(0)
                        ),
                        "completeness": (
                            CorporateActionCompleteness.COMPLETE
                            if complete
                            else CorporateActionCompleteness.PARTIAL
                        ),
                    }
                )
            )
        if actions:
            return tuple(actions)
        return (
            CorporateAction.model_validate(
                {
                    **common,
                    "action_type": CorporateActionType.UNKNOWN_UNSUPPORTED,
                    "completeness": CorporateActionCompleteness.UNSUPPORTED,
                }
            ),
        )

    def benchmark_bars(
        self, benchmark_id: str, start: date, end: date
    ) -> Iterable[BenchmarkBarRecord]:
        code = _benchmark_code(benchmark_id)
        result = self._client.query_history_k_data_plus(
            code,
            "date,code,close",
            start_date=start.isoformat(),
            end_date=end.isoformat(),
            frequency="d",
            adjustflag="3",
        )
        return tuple(
            BenchmarkBarRecord(
                benchmark_id=benchmark_id,
                trading_date=_date(row, "date"),
                close=_decimal(row, "close"),
            )
            for row in _rows(result)
        )

    def benchmark_membership(
        self, benchmark_id: str, as_of: date
    ) -> Iterable[BenchmarkMembershipRecord]:
        query = {
            "CSI300": self._client.query_hs300_stocks,
            "SSE50": self._client.query_sz50_stocks,
            "CSI500": self._client.query_zz500_stocks,
        }.get(benchmark_id)
        if query is None:
            raise BaoStockProviderError("BAOSTOCK_BENCHMARK_NOT_REGISTERED")
        records = []
        for row in _rows(query(as_of.isoformat())):
            security_id, _, _ = _identity(row.get("code", ""))
            records.append(
                BenchmarkMembershipRecord(
                    benchmark_id=benchmark_id,
                    security_id=security_id,
                    valid_from=as_of,
                )
            )
        return tuple(sorted(records, key=lambda item: str(item.security_id)))


def _rows(result: BaoStockResult) -> Iterator[Mapping[str, str]]:
    if result.error_code != "0":
        raise BaoStockProviderError("BAOSTOCK_QUERY_FAILED")
    fields = tuple(result.fields)
    if not fields or len(fields) != len(set(fields)):
        raise BaoStockProviderError("BAOSTOCK_SCHEMA_INVALID")
    while result.next():
        values = result.get_row_data()
        if len(values) != len(fields):
            raise BaoStockProviderError("BAOSTOCK_ROW_INVALID")
        yield dict(zip(fields, values, strict=True))


def _daily_by_date(result: BaoStockResult) -> dict[date, Mapping[str, str]]:
    indexed: dict[date, Mapping[str, str]] = {}
    for row in _rows(result):
        key = _date(row, "date")
        if key in indexed:
            raise BaoStockProviderError("BAOSTOCK_DUPLICATE_RECORD")
        indexed[key] = row
    return indexed


def _identity(provider_code: str) -> tuple[SecurityId, Exchange, str]:
    try:
        prefix, symbol = provider_code.split(".", maxsplit=1)
    except ValueError as exc:
        raise BaoStockProviderError("BAOSTOCK_SECURITY_CODE_INVALID") from exc
    exchange = {"sh": Exchange.SSE, "sz": Exchange.SZSE}.get(prefix.lower())
    if exchange is None or len(symbol) != 6 or not symbol.isdigit():
        raise BaoStockProviderError("BAOSTOCK_SECURITY_CODE_INVALID")
    return SecurityId(value=f"CN-A:{exchange.value}:{symbol}"), exchange, symbol


def _provider_code(security_id: SecurityId) -> str:
    _, exchange, symbol = security_id.value.split(":")
    prefix = {"SSE": "sh", "SZSE": "sz"}.get(exchange)
    if prefix is None:
        raise BaoStockProviderError("BAOSTOCK_SECURITY_CODE_INVALID")
    return f"{prefix}.{symbol}"


def _is_equity_code(code: str) -> bool:
    try:
        _identity(code)
    except BaoStockProviderError:
        return False
    return True


def _benchmark_code(benchmark_id: str) -> str:
    try:
        return {"CSI300": "sh.000300", "CSI500": "sh.000905", "SSE50": "sh.000016"}[benchmark_id]
    except KeyError as exc:
        raise BaoStockProviderError("BAOSTOCK_BENCHMARK_NOT_REGISTERED") from exc


def _date(row: Mapping[str, str], key: str) -> date:
    try:
        return date.fromisoformat(row[key])
    except (KeyError, ValueError) as exc:
        raise BaoStockProviderError("BAOSTOCK_DATE_INVALID") from exc


def _optional_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise BaoStockProviderError("BAOSTOCK_DATE_INVALID") from exc


def _first_date(row: Mapping[str, str], *keys: str) -> date | None:
    for key in keys:
        value = _optional_date(row.get(key, ""))
        if value is not None:
            return value
    return None


def _decimal(row: Mapping[str, str], key: str) -> Decimal:
    value = _optional_decimal(row.get(key, ""))
    if value is None:
        raise BaoStockProviderError("BAOSTOCK_DECIMAL_MISSING")
    return value


def _optional_decimal(value: str) -> Decimal | None:
    if value == "":
        return None
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise BaoStockProviderError("BAOSTOCK_DECIMAL_INVALID") from exc
    if not parsed.is_finite():
        raise BaoStockProviderError("BAOSTOCK_DECIMAL_INVALID")
    return parsed
