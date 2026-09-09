from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import NonNegativeDecimal, PositiveDecimal
from app.domain.markets.identifiers import SecurityId


class CorporateActionType(StrEnum):
    CASH_DIVIDEND = "CASH_DIVIDEND"
    STOCK_DIVIDEND = "STOCK_DIVIDEND"
    BONUS_SHARE = "BONUS_SHARE"
    RIGHTS_RELATED_EVENT = "RIGHTS_RELATED_EVENT"
    SPLIT_OR_SHARE_CHANGE = "SPLIT_OR_SHARE_CHANGE"
    UNKNOWN_UNSUPPORTED = "UNKNOWN_UNSUPPORTED"


class CorporateActionCompleteness(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNSUPPORTED = "UNSUPPORTED"


class CorporateAction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    action_type: CorporateActionType
    announcement_date: date | None = None
    effective_date: date | None = None
    record_date: date | None = None
    ex_date: date | None = None
    payment_date: date | None = None
    listing_date: date | None = None
    cash_per_share: NonNegativeDecimal = Decimal(0)
    share_ratio: NonNegativeDecimal = Decimal(0)
    subscription_price: PositiveDecimal | None = None
    source_provider: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    source_record_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    completeness: CorporateActionCompleteness

    @model_validator(mode="after")
    def prevent_lookahead(self) -> "CorporateAction":
        if (
            self.announcement_date is not None
            and self.ex_date is not None
            and self.announcement_date > self.ex_date
        ):
            raise ValueError("announcement_date must not follow ex_date")
        if self.completeness is CorporateActionCompleteness.COMPLETE and self.ex_date is None:
            raise ValueError("complete corporate actions require an ex-date")
        return self
