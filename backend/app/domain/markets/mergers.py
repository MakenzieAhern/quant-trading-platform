"""Official mandatory merger facts, separate from account-level research rounding."""

import hashlib
import json
from datetime import date
from decimal import ROUND_FLOOR, Decimal, localcontext
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.common import PositiveDecimal
from app.domain.markets.demergers import DemergerSource
from app.domain.markets.identifiers import SecurityId

MERGER_POLICY = "CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1"


class FractionalShareMethod(StrEnum):
    OFFICIAL_EXACT_INTEGER = "OFFICIAL_EXACT_INTEGER"
    OFFICIAL_CASH_IN_LIEU = "OFFICIAL_CASH_IN_LIEU"
    OFFICIAL_DETERMINISTIC_ALLOCATION = "OFFICIAL_DETERMINISTIC_ALLOCATION"
    GLOBAL_SHAREHOLDER_ALLOCATION_UNREPRODUCIBLE = "GLOBAL_SHAREHOLDER_ALLOCATION_UNREPRODUCIBLE"
    FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION = (
        "FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION"
    )
    UNRESOLVED = "UNRESOLVED"


class MergerEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    parent_security: SecurityId
    successor_security: SecurityId
    conversion_ratio: PositiveDecimal
    parent_last_trading_date: date
    record_date: date
    effective_date: date
    successor_listing_date: date
    official_fractional_method: FractionalShareMethod
    research_fractional_method: FractionalShareMethod
    basis_policy: Literal["FULL_PARENT_BASIS_TRANSFERRED_TO_WHOLE_SUCCESSOR_SHARES"] = (
        "FULL_PARENT_BASIS_TRANSFERRED_TO_WHOLE_SUCCESSOR_SHARES"
    )
    cash_election_offered: bool
    cash_election_policy: Literal["NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE"] = (
        "NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE"
    )
    sources: tuple[DemergerSource, ...] = Field(min_length=1)

    @field_validator("conversion_ratio", mode="before")
    @classmethod
    def no_binary_float(cls, value: object) -> object:
        if isinstance(value, (float, bool)):
            raise ValueError("conversion ratio must not pass through binary float")
        return value

    @model_validator(mode="after")
    def validate_lifecycle(self) -> "MergerEvent":
        if self.parent_security == self.successor_security:
            raise ValueError("merger requires distinct identities")
        if not self.parent_last_trading_date <= self.record_date < self.effective_date:
            raise ValueError("invalid merger lifecycle")
        if max(s.published_on for s in self.sources) >= self.effective_date:
            raise ValueError("MERGER_PRE_EFFECTIVE_EVIDENCE_UNAVAILABLE")
        return self

    def require_supported(self) -> None:
        if self.research_fractional_method is not (
            FractionalShareMethod.FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION
        ) or self.official_fractional_method not in {
            FractionalShareMethod.GLOBAL_SHAREHOLDER_ALLOCATION_UNREPRODUCIBLE,
            FractionalShareMethod.OFFICIAL_EXACT_INTEGER,
        }:
            raise ValueError("MERGER_VARIANT_UNRESOLVED")

    def quantities(self, parent_quantity: Decimal) -> tuple[Decimal, Decimal, Decimal]:
        self.require_supported()
        if not isinstance(parent_quantity, Decimal) or not parent_quantity.is_finite():
            raise ValueError("parent quantity must be finite Decimal")
        if parent_quantity < 0:
            raise ValueError("merger policy is long-only")
        with localcontext() as context:
            context.prec = max(
                28,
                len(parent_quantity.as_tuple().digits)
                + len(self.conversion_ratio.as_tuple().digits)
                + 1,
            )
            theoretical = parent_quantity * self.conversion_ratio
            whole = theoretical.to_integral_value(rounding=ROUND_FLOOR)
            remainder = theoretical - whole
        if (
            self.official_fractional_method is FractionalShareMethod.OFFICIAL_EXACT_INTEGER
            and remainder
        ):
            raise ValueError("OFFICIAL_INTEGER_CONVERSION_CONTRADICTED")
        if parent_quantity and not whole:
            raise ValueError("MERGER_ZERO_WHOLE_SHARES_BASIS_UNRESOLVED")
        return theoretical, whole, remainder

    @property
    def activation_date(self) -> date:
        return max(self.effective_date, self.successor_listing_date)

    @property
    def event_checksum(self) -> str:
        data = self.model_dump(mode="json")
        data["sources"].sort(key=lambda s: (s["sha256"], s["url"]))
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
