"""Durable calendar knowledge; this record does not grant market-data authority."""

import json
from datetime import date, datetime, timedelta
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.data.catalog.checksums import canonical_sha256
from app.domain.common import UtcDateTime
from app.domain.markets.calendar import TradingCalendar


class CalendarObservation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["PAPER_CALENDAR_V1"]
    kind: Literal["initial", "extension"]
    calendar: TradingCalendar
    before_sha256: str | None = Field(pattern=r"^[0-9a-f]{64}$", min_length=64, max_length=64)
    after_sha256: str = Field(pattern=r"^[0-9a-f]{64}$", min_length=64, max_length=64)
    applied_at: UtcDateTime
    after_completed_sessions: int = Field(ge=0, strict=True)
    after_trading_date: date | None

    @field_validator("after_trading_date", mode="before")
    @classmethod
    def strict_date(cls, value: object) -> date | None:
        if value is None:
            return None
        if isinstance(value, str):
            parsed = date.fromisoformat(value)
            if parsed.isoformat() == value:
                return parsed
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        raise ValueError("calendar checkpoint date must be an ISO trading date")

    @field_validator("calendar", mode="before")
    @classmethod
    def strict_calendar(cls, value: object) -> TradingCalendar:
        if isinstance(value, TradingCalendar):
            return value
        return TradingCalendar.model_validate_json(json.dumps(value), strict=True)

    @field_validator("applied_at", mode="before")
    @classmethod
    def actual_utc(cls, value: object) -> datetime:
        if isinstance(value, str):
            value = datetime.fromisoformat(value)
        if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
            raise ValueError("calendar application time must be UTC")
        return value

    @model_validator(mode="after")
    def validate_record(self) -> Self:
        if self.after_sha256 != canonical_sha256(self.calendar.model_dump(mode="json")):
            raise ValueError("calendar observation checksum mismatch")
        if (self.after_completed_sessions == 0) != (self.after_trading_date is None):
            raise ValueError("calendar checkpoint must identify its last consumed trading date")
        if self.after_trading_date is not None and not self.calendar.is_trading_session(
            self.after_trading_date
        ):
            raise ValueError("calendar checkpoint is outside accepted trading sessions")
        if self.kind == "initial":
            if self.before_sha256 is not None or self.after_completed_sessions != 0:
                raise ValueError("initial calendar must precede session consumption")
        elif self.before_sha256 is None or self.before_sha256 == self.after_sha256:
            raise ValueError("calendar extension must change an identified previous calendar")
        return self

    def validate_current(self, calendar: TradingCalendar) -> None:
        expected = self.after_sha256 if self.kind == "initial" else self.before_sha256
        if canonical_sha256(calendar.model_dump(mode="json")) != expected:
            raise ValueError("calendar observation chain mismatch")
        self.calendar.require_extension_of(calendar)
