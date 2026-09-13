"""Mandatory same-security share-unit changes, distinct from surrender losses."""

import hashlib
import json
from datetime import date
from decimal import ROUND_FLOOR, Decimal, localcontext
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.domain.markets.demergers import DemergerSource
from app.domain.markets.identifiers import SecurityId

CONSOLIDATION_POLICY: Final = "CN_A_SHARE_CONSOLIDATION_POLICY_V1"


class ShareConsolidationEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    effective_date: date
    affected_holder_class: str = Field(min_length=1)
    new_shares_per_old_share: Decimal = Field(gt=0, allow_inf_nan=False)
    holder_consideration: Literal["NONE", "PRESENT", "UNRESOLVED"]
    official_fraction_method: Literal["EXACT", "FLOOR", "GLOBAL_ALLOCATION", "UNRESOLVED"]
    sources: tuple[DemergerSource, ...] = Field(min_length=1)
    confirmation_sources: tuple[DemergerSource, ...] = ()
    convention_approval_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    policy: Literal["CN_A_SHARE_CONSOLIDATION_POLICY_V1"] = CONSOLIDATION_POLICY

    @field_validator("new_shares_per_old_share", mode="before")
    @classmethod
    def exact_ratio(cls, value: object) -> object:
        if isinstance(value, (float, bool)):
            raise ValueError("share ratio must not pass through binary float")
        return value

    @model_validator(mode="after")
    def validate_availability(self) -> "ShareConsolidationEvent":
        if any(s.published_on >= self.effective_date for s in self.sources):
            raise ValueError("CONSOLIDATION_PRE_EFFECTIVE_TERMS_UNAVAILABLE")
        return self

    def require_supported(self) -> None:
        if self.holder_consideration != "NONE":
            raise ValueError("CONSOLIDATION_CONSIDERATION_UNRESOLVED")

    def quantities(self, quantity: Decimal) -> tuple[Decimal, Decimal]:
        self.require_supported()
        if not quantity.is_finite() or quantity < 0 or quantity != quantity.to_integral_value():
            raise ValueError("consolidation requires whole long shares")
        with localcontext() as context:
            context.prec = max(
                28,
                len(quantity.as_tuple().digits)
                + len(self.new_shares_per_old_share.as_tuple().digits)
                + 1,
            )
            theoretical = quantity * self.new_shares_per_old_share
            whole = theoretical.to_integral_value(rounding=ROUND_FLOOR)
        if self.official_fraction_method == "EXACT" and theoretical != whole:
            raise ValueError("CONSOLIDATION_OFFICIAL_INTEGER_CONTRADICTED")
        return theoretical, whole

    @property
    def event_checksum(self) -> str:
        value = self.model_dump(mode="json")
        ratio = format(self.new_shares_per_old_share, "f")
        value["new_shares_per_old_share"] = ratio.rstrip("0").rstrip(".") if "." in ratio else ratio
        for key in ("sources", "confirmation_sources"):
            value[key].sort(key=lambda s: (s["sha256"], s["url"]))
        return hashlib.sha256(
            json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
