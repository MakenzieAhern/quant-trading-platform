"""Immutable mandatory conversion evidence, separate from portfolio elections."""

import hashlib
import json
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import PositiveDecimal, UtcDateTime
from app.domain.markets.identifiers import SecurityId

DEMERGER_POLICY = "CN_A_MANDATORY_DEMERGER_POLICY_V1"
CASH_ELECTION_POLICY = "NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE"


class BasisAllocationMethod(StrEnum):
    OFFICIAL_REFERENCE_VALUE = "OFFICIAL_REFERENCE_VALUE"
    OFFICIAL_TAX_ALLOCATION = "OFFICIAL_TAX_ALLOCATION"
    OFFICIAL_ASSET_ALLOCATION = "OFFICIAL_ASSET_ALLOCATION"
    FIRST_COMMON_MARKET_VALUE = "FIRST_COMMON_MARKET_VALUE"
    UNRESOLVED = "UNRESOLVED"


class DemergerSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    url: str = Field(pattern=r"^https://\S+$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    published_on: date
    retrieved_at: UtcDateTime
    document: str = Field(min_length=1)


class DemergerSuccessor(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    security_id: SecurityId
    conversion_ratio: PositiveDecimal
    listing_date: date
    reference_value: PositiveDecimal


class DemergerEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    parent_security: SecurityId
    effective_date: date
    completion_date: date
    parent_last_close: PositiveDecimal
    parent_last_trading_date: date
    successors: tuple[DemergerSuccessor, ...] = Field(min_length=2)
    basis_allocation: BasisAllocationMethod
    # Effective conversion and later allocation evidence have different availability.
    conversion_source: DemergerSource
    allocation_sources: tuple[DemergerSource, ...] = Field(min_length=1)
    cash_election_offered: bool

    @model_validator(mode="after")
    def validate_structure(self) -> "DemergerEvent":
        ids = [s.security_id for s in self.successors]
        if len(ids) != len(set(ids)) or self.parent_security in ids:
            raise ValueError("duplicate or self-referential demerger successor")
        if self.parent_last_trading_date >= self.effective_date:
            raise ValueError("parent close must precede conversion")
        if self.conversion_source.published_on > self.effective_date:
            raise ValueError("DEMERGER_CONVERSION_EVIDENCE_NOT_AVAILABLE")
        if self.completion_date < self.effective_date:
            raise ValueError("demerger completion precedes effective date")
        if any(s.listing_date < self.completion_date for s in self.successors):
            raise ValueError("successor listing precedes legal completion")
        return self

    def require_supported(self) -> None:
        if self.basis_allocation is not BasisAllocationMethod.OFFICIAL_REFERENCE_VALUE:
            raise ValueError("DEMERGER_BASIS_ALLOCATION_UNRESOLVED")
        if len({s.listing_date for s in self.successors}) != 1:
            raise ValueError("DEMERGER_ASYNCHRONOUS_ACTIVATION_UNSUPPORTED")
        if max(s.published_on for s in self.allocation_sources) >= self.successors[0].listing_date:
            raise ValueError("DEMERGER_PRELISTING_ALLOCATION_EVIDENCE_UNAVAILABLE")

    @property
    def event_checksum(self) -> str:
        value = self.model_dump(mode="json")
        value["successors"] = sorted(value["successors"], key=lambda s: s["security_id"]["value"])
        value["allocation_sources"] = sorted(value["allocation_sources"], key=lambda s: s["sha256"])
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def accounting_symbol(security_id: SecurityId) -> str:
    _, exchange, code = str(security_id).split(":")
    return f"{code}.{exchange}"
