from collections.abc import Iterable
from datetime import date
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import NonNegativeDecimal, PositiveDecimal
from app.domain.markets import (
    Board,
    CorporateAction,
    DailySecurityStatus,
    Exchange,
    SecurityId,
)


class ResearchRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class SecurityRecord(ResearchRecord):
    security_id: SecurityId
    provider_code: str = Field(min_length=1)
    symbol: str = Field(pattern=r"^[0-9]{6}$")
    name: str = Field(min_length=1)
    exchange: Exchange
    board: Board
    listing_date: date
    delisting_date: date | None = None


class SessionRecord(ResearchRecord):
    session_date: date
    is_open: bool


class DailyBarRecord(ResearchRecord):
    security_id: SecurityId
    trading_date: date
    raw_open: PositiveDecimal
    raw_high: PositiveDecimal
    raw_low: PositiveDecimal
    raw_close: PositiveDecimal
    pre_close: PositiveDecimal | None = None
    volume: NonNegativeDecimal
    amount: NonNegativeDecimal | None = None
    turnover: NonNegativeDecimal | None = None
    adjustment_factor: PositiveDecimal | None = None
    adjusted_close: PositiveDecimal | None = None

    @model_validator(mode="after")
    def validate_ohlc(self) -> "DailyBarRecord":
        if self.raw_high < max(self.raw_open, self.raw_close, self.raw_low):
            raise ValueError("raw_high must be at least open, close, and low")
        if self.raw_low > min(self.raw_open, self.raw_close):
            raise ValueError("raw_low must be at most open and close")
        return self


class SecurityStatusRecord(ResearchRecord):
    status: DailySecurityStatus


class BenchmarkBarRecord(ResearchRecord):
    benchmark_id: str = Field(min_length=1)
    trading_date: date
    close: PositiveDecimal


class BenchmarkMembershipRecord(ResearchRecord):
    benchmark_id: str = Field(min_length=1)
    security_id: SecurityId
    valid_from: date
    valid_to: date | None = None


class AdjustmentFactorRecord(ResearchRecord):
    security_id: SecurityId
    ex_date: date
    forward_factor: PositiveDecimal
    backward_factor: PositiveDecimal
    adjustment_factor: PositiveDecimal
    source_record_hash: str = Field(pattern=r"^[0-9a-f]{64}$")


class FundamentalRecord(ResearchRecord):
    security_id: SecurityId
    published_on: date
    period_end: date
    fields: tuple[tuple[str, Decimal | str | None], ...]


class ResearchDataProvider(Protocol):
    @property
    def provider_name(self) -> str: ...

    @property
    def provider_version(self) -> str: ...

    def securities(self, as_of: date) -> Iterable[SecurityRecord]: ...

    def trading_calendar(self, start: date, end: date) -> Iterable[SessionRecord]: ...

    def daily_bars(
        self, security_id: SecurityId, start: date, end: date
    ) -> Iterable[DailyBarRecord]: ...

    def daily_status(
        self, security_id: SecurityId, start: date, end: date
    ) -> Iterable[SecurityStatusRecord]: ...

    def corporate_actions(
        self, security_id: SecurityId, start: date, end: date
    ) -> Iterable[CorporateAction]: ...

    def benchmark_bars(
        self, benchmark_id: str, start: date, end: date
    ) -> Iterable[BenchmarkBarRecord]: ...

    def benchmark_membership(
        self, benchmark_id: str, as_of: date
    ) -> Iterable[BenchmarkMembershipRecord]: ...
