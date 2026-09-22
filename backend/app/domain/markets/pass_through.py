"""Net restructuring pass-through facts, never an ordinary retained bonus."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.common import PositiveDecimal
from app.domain.markets.demergers import DemergerSource
from app.domain.markets.identifiers import SecurityId

PASS_THROUGH_POLICY: Final = "CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1"
PASS_THROUGH_BASIS_POLICY: Final = "NET_PASS_THROUGH_NO_BASIS_ALLOCATION"


class RestructuringBonusPassThroughEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    effective_date: date
    event_class: Literal["RESTRUCTURING_BONUS_PASS_THROUGH"] = "RESTRUCTURING_BONUS_PASS_THROUGH"
    original_quantity_preserved: bool
    bonus_ratio: PositiveDecimal
    temporary_registration_date: date
    transfer_date: date
    transfer_recipient: str = Field(min_length=1)
    mandatory_transfer: bool
    holder_compensation: Literal["NONE", "PRESENT", "UNRESOLVED"]
    tradability_during_pass_through: Literal["NONE", "PRESENT", "UNRESOLVED"]
    monetization_during_pass_through: Literal["NONE", "PRESENT", "UNRESOLVED"]
    sources: tuple[DemergerSource, ...] = Field(min_length=1)
    confirmation_sources: tuple[DemergerSource, ...] = Field(min_length=1)
    convention_approval_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy: Literal["CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1"] = PASS_THROUGH_POLICY
    basis_policy: Literal["NET_PASS_THROUGH_NO_BASIS_ALLOCATION"] = PASS_THROUGH_BASIS_POLICY

    @field_validator("bonus_ratio", mode="before")
    @classmethod
    def exact_ratio(cls, value: object) -> object:
        if isinstance(value, (float, bool)):
            raise ValueError("pass-through ratio must not pass through binary float")
        return value

    @model_validator(mode="after")
    def validate_dates(self) -> "RestructuringBonusPassThroughEvent":
        if self.effective_date != self.temporary_registration_date:
            raise ValueError("pass-through metadata begins at legal registration")
        if self.transfer_date < self.temporary_registration_date:
            raise ValueError("pass-through transfer precedes registration")
        if any(s.published_on >= self.effective_date for s in self.sources):
            raise ValueError("PASS_THROUGH_PRE_EFFECTIVE_TERMS_UNAVAILABLE")
        return self

    def require_supported(self) -> None:
        if (
            not self.original_quantity_preserved
            or not self.mandatory_transfer
            or any(
                value != "NONE"
                for value in (
                    self.holder_compensation,
                    self.tradability_during_pass_through,
                    self.monetization_during_pass_through,
                )
            )
        ):
            raise ValueError("PASS_THROUGH_ELIGIBILITY_UNRESOLVED")

    @property
    def event_checksum(self) -> str:
        value = self.model_dump(mode="json")
        # Equivalent Decimal spellings and source order do not change event identity.
        ratio = format(Decimal(value["bonus_ratio"]), "f")
        value["bonus_ratio"] = ratio.rstrip("0").rstrip(".") if "." in ratio else ratio
        for key in ("sources", "confirmation_sources"):
            value[key].sort(key=lambda s: (s["sha256"], s["url"]))
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
