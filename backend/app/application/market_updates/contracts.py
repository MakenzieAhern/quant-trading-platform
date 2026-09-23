"""Bounded public-source requests and strict raw-only parsing."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated, Any
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.application.backtests.decimal_policy import canonical_decimal, parse_decimal_string
from app.application.experiments.data import ExperimentInputError
from app.data.providers.research import DailyBarRecord
from app.domain.markets import SecurityId

PROVIDER = "BAOSTOCK_PUBLIC_SINGLE_SECURITY_EOD"
SDK_VERSION = "0.9.4"
SDK_WHEEL_SHA256 = "0bf71c6069ab5890ff3596632f9c3f8f1fbc6bfcac582c2f9d6a5c11ab2cfaf8"
PARSER_VERSION = "product-baostock-raw-v2"
FIELDS = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,tradestatus,isST"
TERMINAL = {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}
AUTHORITY = {
    "raw_ohlcv": "CANDIDATE_ONLY",
    "current_security_master": "UNVERIFIED",
    "trading_calendar": "UNVERIFIED",
    "st_history": "UNVERIFIED",
    "market_rules": "UNVERIFIED",
    "corporate_actions": "UNVERIFIED",
    "adjustment_factors": "NOT_REQUESTED",
    "execution_eligible": False,
    "forward_acceptance": False,
}
TERMS = {
    "source_url": "https://www.baostock.com/mainContent?file=stockKData.md",
    "source_snapshot_sha256": "2a6db3b24ab21a199aa17bd949dfbe545d3279007bea1664854f9b7c20542aac",
    "terms_url": "https://www.baostock.com/disclaimer",
    "terms_version": "V1.0.0",
    "terms_snapshot_sha256": "4172ee9f39f0e33f12be4e84d319fa066a5b48655aa1ea572f6ce905159e9d13",
    "terms_retrieved_at_utc": "2026-09-22T07:48:30.347255Z",
    "permitted_scope": "PRIVATE_LOCAL_ANALYSIS_TRIAL",
    "redistribution_commercial_rights": "NOT_ESTABLISHED",
    "software_license": "BSD_SOFTWARE_NOT_DATA_LICENSE",
}


class UpdateError(ExperimentInputError):
    pass


class UpdateConflict(ValueError):
    pass


class UpdateCancelled(Exception):
    pass


class CreateUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    security_ids: list[Annotated[str, Field(pattern=r"^CN-A:(SSE|SZSE):[0-9]{6}$")]] = Field(
        min_length=1, max_length=20
    )
    start_date: date
    end_date: date

    @field_validator("security_ids")
    @classmethod
    def unique_sorted(cls, values: list[str]) -> list[str]:
        if len(set(values)) != len(values):
            raise ValueError("DUPLICATE_SECURITY_IDS")
        return sorted(values)

    @model_validator(mode="after")
    def bounded_dates(self) -> "CreateUpdateRequest":
        if not 1 <= (self.end_date - self.start_date).days + 1 <= 366:
            raise ValueError("UPDATE_DATE_RANGE_MUST_BE_1_TO_366_DAYS")
        return self


def latest_publishable_date(now: datetime) -> date:
    local = now.astimezone(ZoneInfo("Asia/Shanghai"))
    # Publication eligibility is not proof that this is an exchange trading day.
    return local.date() - timedelta(days=int(local.time() < time(17, 30)))


def missing_chunks(start: date, end: date, cached: set[date]) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    day = start
    while day <= end:
        if day in cached:
            day += timedelta(days=1)
            continue
        first = last = day
        while last < end and (last - first).days < 30:
            following = last + timedelta(days=1)
            if following in cached:
                break
            last = following
        chunks.append((first, last))
        day = last + timedelta(days=1)
    return chunks


def request_parameters(security_id: str, start: date, end: date) -> dict[str, str]:
    _, exchange, symbol = security_id.split(":")
    return {
        "code": f"{'sh' if exchange == 'SSE' else 'sz'}.{symbol}",
        "fields": FIELDS,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "frequency": "d",
        "adjustflag": "3",
    }


def parse_response(
    payload: dict[str, Any], security_id: str, start: date, end: date
) -> list[dict[str, Any]]:
    """Keep SDK-decoded strings as evidence; normalize without float or status inference."""
    try:
        fields, rows = payload["fields"], payload["rows"]
        if fields != FIELDS.split(",") or not isinstance(rows, list) or len(rows) > 31:
            raise ValueError("unexpected bounded response shape")
        expected_code = request_parameters(security_id, start, end)["code"]
        result: dict[date, dict[str, Any]] = {}
        for values in rows:
            if not isinstance(values, list) or len(values) != len(fields):
                raise ValueError("invalid row")
            row = dict(zip(fields, values, strict=True))
            if any(not isinstance(v, str) or len(v) > 128 for v in values):
                raise ValueError("non-string or oversized provider field")
            day = date.fromisoformat(row["date"])
            if (
                row["code"] != expected_code
                or not start <= day <= end
                or day in result
                or row["adjustflag"] != "3"
                or row["tradestatus"] not in {"0", "1"}
                or row["isST"] not in {"0", "1"}
            ):
                raise ValueError("invalid identity/date/status/adjustment")
            numeric_row = dict(row)
            if row["tradestatus"] == "0" and row["volume"] == row["amount"] == "":
                numeric_row["volume"] = numeric_row["amount"] = "0"
            numbers = {
                key: parse_decimal_string(numeric_row[key])
                for key in ("open", "high", "low", "close", "preclose", "volume", "amount")
            }
            DailyBarRecord(
                security_id=SecurityId(value=security_id),
                trading_date=day,
                raw_open=numbers["open"],
                raw_high=numbers["high"],
                raw_low=numbers["low"],
                raw_close=numbers["close"],
                pre_close=numbers["preclose"],
                volume=numbers["volume"],
                amount=numbers["amount"],
            )
            if row["tradestatus"] == "0" and (numbers["volume"] or numbers["amount"]):
                raise ValueError("suspended row has transactions")
            result[day] = {
                "security_id": security_id,
                "trading_date": day.isoformat(),
                "raw": {key: canonical_decimal(value) for key, value in numbers.items()},
                "provider_trade_status": row["tradestatus"],
                "provider_is_st": row["isST"],
                "status": "VENDOR_SUSPENDED" if row["tradestatus"] == "0" else "RAW_CANDIDATE",
                "execution_eligible": False,
            }
        return [result[day] for day in sorted(result)]
    except (KeyError, TypeError, ValueError) as exc:
        raise UpdateError("INVALID_PROVIDER_RESPONSE") from exc


def utc_now() -> datetime:
    return datetime.now(UTC)
