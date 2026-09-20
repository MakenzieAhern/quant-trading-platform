"""Immutable mandatory conversion evidence, separate from portfolio elections."""

import hashlib
import json
from datetime import date
from enum import StrEnum
from typing import Literal

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
    basis_allocation_weight: PositiveDecimal | None = None


class DemergerEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    parent_security: SecurityId
    effective_date: date
    research_effective_date: date | None = None
    completion_date: date
    parent_last_close: PositiveDecimal
    parent_last_trading_date: date
    successors: tuple[DemergerSuccessor, ...] = Field(min_length=2)
    basis_allocation: BasisAllocationMethod
    # Effective conversion and later allocation evidence have different availability.
    conversion_source: DemergerSource
    allocation_sources: tuple[DemergerSource, ...] = Field(min_length=1)
    confirmation_sources: tuple[DemergerSource, ...] | None = None
    official_fractional_method: Literal["GLOBAL_SHAREHOLDER_ALLOCATION_UNREPRODUCIBLE"] | None = (
        None
    )
    research_fractional_method: Literal["FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION"] | None = (
        None
    )
    cash_election_offered: bool

    @model_validator(mode="after")
    def validate_structure(self) -> "DemergerEvent":
        ids = [s.security_id for s in self.successors]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate demerger successor")
        if self.parent_last_trading_date >= self.effective_date:
            raise ValueError("parent close must precede conversion")
        if self.conversion_source.published_on > self.effective_date:
            raise ValueError("DEMERGER_CONVERSION_EVIDENCE_NOT_AVAILABLE")
        if self.completion_date < self.effective_date:
            raise ValueError("demerger completion precedes effective date")
        if self.research_effective_date is not None and (
            self.research_effective_date < self.completion_date
            or not self.confirmation_sources
            or any(
                source.published_on > self.research_effective_date
                for source in self.confirmation_sources
            )
        ):
            raise ValueError("DEMERGER_RESEARCH_BOUNDARY_PROVENANCE_REQUIRED")
        if any(s.listing_date < self.completion_date for s in self.successors):
            raise ValueError("successor listing precedes legal completion")
        return self

    def require_supported(self) -> None:
        if self.basis_allocation not in {
            BasisAllocationMethod.OFFICIAL_REFERENCE_VALUE,
            BasisAllocationMethod.OFFICIAL_ASSET_ALLOCATION,
        }:
            raise ValueError("DEMERGER_BASIS_ALLOCATION_UNRESOLVED")
        weights = [s.basis_allocation_weight for s in self.successors]
        if self.basis_allocation == BasisAllocationMethod.OFFICIAL_ASSET_ALLOCATION and (
            any(weight is None for weight in weights)
            or sum(weight for weight in weights if weight is not None) != 1
        ):
            raise ValueError("DEMERGER_ASSET_ALLOCATION_UNRESOLVED")
        if (self.official_fractional_method is None) != (self.research_fractional_method is None):
            raise ValueError("DEMERGER_FRACTIONAL_POLICY_UNRESOLVED")
        if len({s.listing_date for s in self.successors}) != 1:
            raise ValueError("DEMERGER_ASYNCHRONOUS_ACTIVATION_UNSUPPORTED")
        if max(s.published_on for s in self.allocation_sources) >= self.successors[0].listing_date:
            raise ValueError("DEMERGER_PRELISTING_ALLOCATION_EVIDENCE_UNAVAILABLE")

    @property
    def application_date(self) -> date:
        return self.research_effective_date or self.effective_date

    @property
    def event_checksum(self) -> str:
        value = self.model_dump(mode="json", exclude_none=True)
        value["successors"] = sorted(value["successors"], key=lambda s: s["security_id"]["value"])
        value["allocation_sources"] = sorted(value["allocation_sources"], key=lambda s: s["sha256"])
        if "confirmation_sources" in value:
            value["confirmation_sources"] = sorted(
                value["confirmation_sources"], key=lambda s: s["sha256"]
            )
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()


def accounting_symbol(security_id: SecurityId) -> str:
    _, exchange, code = str(security_id).split(":")
    return f"{code}.{exchange}"
