from datetime import date
from itertools import pairwise
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import UtcDateTime
from app.domain.markets.identifiers import Board, Exchange, InstrumentType, Market, SecurityId


class ImmutableModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class InstrumentClassification(ImmutableModel):
    """Sourced instrument fact, independent of any research eligibility decision."""

    security_id: SecurityId
    instrument_type: InstrumentType
    effective_from: date
    effective_to: date | None = None
    source_url: str = Field(pattern=r"^https://")
    source_publication_date: date | None
    evidence_basis: Literal["DATED_NOTICE", "ORIGINAL_TYPED_LISTING_REGISTER"] = "DATED_NOTICE"
    source_listing_date: date | None = None
    source_document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    retrieval_timestamp: UtcDateTime

    @model_validator(mode="after")
    def validate_range(self) -> "InstrumentClassification":
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not precede effective_from")
        if self.evidence_basis == "DATED_NOTICE" and self.source_publication_date is None:
            raise ValueError("dated notice requires publication date")
        if self.evidence_basis == "ORIGINAL_TYPED_LISTING_REGISTER" and (
            self.source_publication_date is not None
            or self.source_listing_date != self.effective_from
        ):
            raise ValueError(
                "typed original listing requires its explicit listing date, "
                "not a fabricated publication date"
            )
        return self

    def known_on(self, on_date: date) -> bool:
        return (
            (self.source_publication_date is None or self.source_publication_date <= on_date)
            and self.effective_from <= on_date
            and (self.effective_to is None or on_date <= self.effective_to)
        )


class EffectiveSymbolPeriod(ImmutableModel):
    symbol: str = Field(pattern=r"^[0-9]{6}$")
    exchange: Exchange
    valid_from: date
    valid_to: date | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "EffectiveSymbolPeriod":
        if self.valid_to is not None and self.valid_to < self.valid_from:
            raise ValueError("valid_to must not precede valid_from")
        return self


class SecurityListingPeriod(ImmutableModel):
    board: Board
    listed_from: date
    delisted_on: date | None = None

    @model_validator(mode="after")
    def validate_range(self) -> "SecurityListingPeriod":
        if self.delisted_on is not None and self.delisted_on < self.listed_from:
            raise ValueError("delisted_on must not precede listed_from")
        return self

    def contains(self, on_date: date) -> bool:
        return self.listed_from <= on_date and (
            self.delisted_on is None or on_date <= self.delisted_on
        )


class Security(ImmutableModel):
    security_id: SecurityId
    market: Market = Market.CN_A
    exchange: Exchange
    name: str = Field(min_length=1)
    symbol_periods: tuple[EffectiveSymbolPeriod, ...]
    listing_periods: tuple[SecurityListingPeriod, ...]

    @model_validator(mode="after")
    def validate_periods(self) -> "Security":
        if not self.symbol_periods or not self.listing_periods:
            raise ValueError("security requires symbol and listing history")
        _assert_non_overlapping(
            tuple((p.valid_from, p.valid_to) for p in self.symbol_periods), "symbol"
        )
        _assert_non_overlapping(
            tuple((p.listed_from, p.delisted_on) for p in self.listing_periods), "listing"
        )
        if any(period.exchange is not self.exchange for period in self.symbol_periods):
            raise ValueError("symbol-period exchange must match security exchange")
        return self


def ordinary_a_share_on(
    security: Security, classifications: tuple[InstrumentClassification, ...], on_date: date
) -> bool:
    """Instrument/lifecycle gate only; downstream ST, liquidity and execution gates still apply."""
    facts = [
        fact
        for fact in classifications
        if fact.security_id == security.security_id and fact.known_on(on_date)
    ]
    if len(facts) > 1:
        raise ValueError("overlapping instrument classifications")
    return bool(
        facts
        and facts[0].instrument_type is InstrumentType.COMMON_A_SHARE
        and any(period.contains(on_date) for period in security.listing_periods)
        and any(
            period.valid_from <= on_date and (period.valid_to is None or on_date <= period.valid_to)
            for period in security.symbol_periods
        )
    )


def _assert_non_overlapping(periods: tuple[tuple[date, date | None], ...], label: str) -> None:
    ordered = sorted(periods, key=lambda item: item[0])
    for previous, current in pairwise(ordered):
        if previous[1] is None or current[0] <= previous[1]:
            raise ValueError(f"{label} periods must not overlap")
