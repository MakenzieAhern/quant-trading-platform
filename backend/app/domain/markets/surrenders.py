"""Mandatory holder-level surrender facts; issuer issuance is not holder consideration."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.common import NonNegativeDecimal, PositiveDecimal
from app.domain.markets.demergers import DemergerSource
from app.domain.markets.identifiers import SecurityId

PARTIAL_SURRENDER_POLICY: Final = "CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1"
PARTIAL_SURRENDER_FRACTION_POLICY: Final = "CEIL_SURRENDER_FLOOR_RETAINED_V1"
PARTIAL_SURRENDER_BOUNDARY_POLICY: Final = "FIRST_POST_EVENT_TRADING_BOUNDARY_V1"


class SurrenderQuantityBand(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    up_to_quantity: PositiveDecimal | None
    surrender_ratio: Decimal = Field(ge=0, lt=1, allow_inf_nan=False)

    @field_validator("surrender_ratio", mode="before")
    @classmethod
    def no_float(cls, value: object) -> object:
        if isinstance(value, (float, bool)):
            raise ValueError("surrender values must not pass through binary float")
        return value


class MandatoryPartialShareSurrenderEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    affected_holder_class: str = Field(min_length=1)
    record_date: date | None
    effective_date: date | None
    research_effective_date: date | None = None
    nontrading_from: date | None = None
    boundary_sources: tuple[DemergerSource, ...] = ()
    convention_approval_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    surrender_ratio: Decimal | None = Field(default=None, gt=0, lt=1, allow_inf_nan=False)
    quantity_bands: tuple[SurrenderQuantityBand, ...] = ()
    consideration_type: Literal["NONE", "CASH", "SHARES", "DEBT_CLAIM", "OTHER", "UNRESOLVED"]
    consideration_value: NonNegativeDecimal | None
    quantity_rounding_rule: Literal["EXACT_INTEGER_ONLY", "OFFICIAL_FLOOR_SURRENDER", "UNRESOLVED"]
    research_fraction_rule: Literal["CEIL_SURRENDER_FLOOR_RETAINED_V1"] | None = None
    recipient: str = Field(min_length=1)
    disposition: Literal["TRANSFERRED", "CANCELLED"]
    sources: tuple[DemergerSource, ...] = Field(min_length=1)
    confirmation_sources: tuple[DemergerSource, ...] = ()
    policy: Literal["CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1"] = PARTIAL_SURRENDER_POLICY

    @field_validator("surrender_ratio", "consideration_value", mode="before")
    @classmethod
    def no_float(cls, value: object) -> object:
        if isinstance(value, (float, bool)):
            raise ValueError("surrender values must not pass through binary float")
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "MandatoryPartialShareSurrenderEvent":
        if (self.surrender_ratio is None) == (not self.quantity_bands):
            raise ValueError("exactly one flat ratio or quantity-band schedule is required")
        if self.quantity_bands:
            upper = Decimal(0)
            for index, band in enumerate(self.quantity_bands):
                if band.up_to_quantity is None:
                    if index != len(self.quantity_bands) - 1:
                        raise ValueError("open surrender band must be last")
                elif band.up_to_quantity <= upper:
                    raise ValueError("surrender quantity bands must be strictly increasing")
                else:
                    upper = band.up_to_quantity
            if self.quantity_bands[-1].up_to_quantity is not None:
                raise ValueError("surrender quantity bands must cover all quantities")
        if self.effective_date is not None:
            if self.record_date is not None and self.effective_date < self.record_date:
                raise ValueError("surrender precedes record date")
            if any(s.published_on >= self.effective_date for s in self.sources):
                raise ValueError("SURRENDER_PRE_EFFECTIVE_EVIDENCE_UNAVAILABLE")
        if self.research_effective_date is not None:
            if (
                self.effective_date is not None
                or self.nontrading_from is None
                or (
                    self.record_date is not None
                    and self.record_date >= self.research_effective_date
                )
                or self.nontrading_from >= self.research_effective_date
                or not self.boundary_sources
                or self.convention_approval_sha256 is None
            ):
                raise ValueError("SURRENDER_BOUNDARY_PROVENANCE_REQUIRED")
            if any(s.published_on >= self.research_effective_date for s in self.sources) or any(
                s.published_on > self.research_effective_date for s in self.boundary_sources
            ):
                raise ValueError("SURRENDER_BOUNDARY_FUTURE_EVIDENCE")
        if self.research_fraction_rule is not None and self.convention_approval_sha256 is None:
            raise ValueError("SURRENDER_FRACTION_APPROVAL_REQUIRED")
        return self

    def theoretical_surrender(self, quantity: Decimal) -> Decimal:
        if self.surrender_ratio is not None:
            return quantity * self.surrender_ratio
        surrendered = Decimal(0)
        lower = Decimal(0)
        for band in self.quantity_bands:
            upper = quantity if band.up_to_quantity is None else min(quantity, band.up_to_quantity)
            surrendered += max(Decimal(0), upper - lower) * band.surrender_ratio
            lower = upper
            if lower == quantity:
                break
        return surrendered

    @property
    def application_date(self) -> date | None:
        return self.research_effective_date or self.effective_date

    def require_supported(self) -> None:
        if self.consideration_type != "NONE" or self.consideration_value != Decimal(0):
            raise ValueError("PARTIAL_SURRENDER_CONSIDERATION_POLICY_UNRESOLVED")
        if self.application_date is None:
            raise ValueError("PARTIAL_SURRENDER_EFFECTIVE_DATE_UNVERIFIED")

    @property
    def event_checksum(self) -> str:
        value = self.model_dump(mode="json")
        for key in ("sources", "confirmation_sources", "boundary_sources"):
            value[key].sort(key=lambda s: (s["sha256"], s["url"]))
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
