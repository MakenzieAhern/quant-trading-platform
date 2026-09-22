"""Official mandatory merger facts, separate from account-level research rounding."""

import hashlib
import json
from datetime import date
from decimal import Decimal, localcontext
from enum import StrEnum
from fractions import Fraction
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.common import PositiveDecimal
from app.domain.markets.demergers import DemergerSource
from app.domain.markets.identifiers import SecurityId

MERGER_POLICY = "CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1"
ZERO_WHOLE_SHARE_POLICY = "WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"


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
    conversion_denominator: PositiveDecimal = Decimal(1)
    parent_last_trading_date: date
    record_date: date
    effective_date: date
    successor_listing_date: date
    official_fractional_method: FractionalShareMethod
    research_fractional_method: FractionalShareMethod
    basis_policy: Literal["FULL_PARENT_BASIS_TRANSFERRED_TO_WHOLE_SUCCESSOR_SHARES"] = (
        "FULL_PARENT_BASIS_TRANSFERRED_TO_WHOLE_SUCCESSOR_SHARES"
    )
    # Unknown offer metadata never authorizes an election or changes mandatory conversion.
    cash_election_offered: bool | None
    cash_election_policy: Literal["NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE"] = (
        "NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE"
    )
    sources: tuple[DemergerSource, ...] = Field(min_length=1)
    activation_sources: tuple[DemergerSource, ...] = ()
    successor_shares_tradable_from: date | None = None
    zero_whole_share_policy: (
        Literal["WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"] | None
    ) = None

    @field_validator("conversion_ratio", "conversion_denominator", mode="before")
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
        if any(s.published_on >= self.activation_date for s in self.activation_sources):
            raise ValueError("MERGER_PRE_ACTIVATION_EVIDENCE_UNAVAILABLE")
        return self

    def require_supported(self) -> None:
        if self.research_fractional_method is not (
            FractionalShareMethod.FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION
        ) or self.official_fractional_method not in {
            FractionalShareMethod.GLOBAL_SHAREHOLDER_ALLOCATION_UNREPRODUCIBLE,
            FractionalShareMethod.OFFICIAL_EXACT_INTEGER,
        }:
            raise ValueError("MERGER_VARIANT_UNRESOLVED")

    def theoretical_fraction(self, parent_quantity: Decimal) -> Fraction:
        self.require_supported()
        if not isinstance(parent_quantity, Decimal) or not parent_quantity.is_finite():
            raise ValueError("parent quantity must be finite Decimal")
        if parent_quantity < 0 or parent_quantity != parent_quantity.to_integral_value():
            raise ValueError("merger policy requires whole long shares")
        return (
            Fraction(parent_quantity)
            * Fraction(self.conversion_ratio)
            / Fraction(self.conversion_denominator)
        )

    def quantities(self, parent_quantity: Decimal) -> tuple[Decimal, Decimal, Decimal]:
        exact = self.theoretical_fraction(parent_quantity)
        whole = Decimal(exact.numerator // exact.denominator)
        fractional = exact % 1
        with localcontext() as context:
            context.prec = max(
                28,
                len(str(exact.numerator)) + len(str(exact.denominator)) + 1,
            )
            # Recurring decimals are audit displays only; exact rational arithmetic decides Q.
            theoretical = Decimal(exact.numerator) / Decimal(exact.denominator)
            remainder = Decimal(fractional.numerator) / Decimal(fractional.denominator)
        if (
            self.official_fractional_method is FractionalShareMethod.OFFICIAL_EXACT_INTEGER
            and remainder
        ):
            raise ValueError("OFFICIAL_INTEGER_CONVERSION_CONTRADICTED")
        if parent_quantity and not whole and self.zero_whole_share_policy is None:
            raise ValueError("MERGER_ZERO_WHOLE_SHARES_BASIS_UNRESOLVED")
        return theoretical, whole, remainder

    @property
    def activation_date(self) -> date:
        return max(
            self.effective_date,
            self.successor_listing_date,
            self.successor_shares_tradable_from or self.successor_listing_date,
        )

    @property
    def event_checksum(self) -> str:
        data = self.model_dump(mode="json")
        if self.conversion_denominator == 1:
            data.pop("conversion_denominator")  # Preserve accepted finite-ratio event identities.
        data["sources"].sort(key=lambda s: (s["sha256"], s["url"]))
        # Preserve accepted legacy event identities when the extension is absent.
        if data["activation_sources"]:
            data["activation_sources"].sort(key=lambda s: (s["sha256"], s["url"]))
        else:
            data.pop("activation_sources")
        for key in ("successor_shares_tradable_from", "zero_whole_share_policy"):
            if data[key] is None:
                data.pop(key)
        return hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
