from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import NonNegativeDecimal, PositiveDecimal
from app.domain.markets.identifiers import SecurityId


class CorporateActionType(StrEnum):
    CASH_DIVIDEND = "CASH_DIVIDEND"
    STOCK_DIVIDEND = "STOCK_DIVIDEND"
    SPLIT = "SPLIT"
    RIGHTS_ISSUE = "RIGHTS_ISSUE"


class CorporateAction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    action_type: CorporateActionType
    announcement_date: date
    ex_date: date
    record_date: date | None = None
    cash_per_share: NonNegativeDecimal = Decimal(0)
    share_ratio: NonNegativeDecimal = Decimal(0)
    subscription_price: PositiveDecimal | None = None
    source_version: str = Field(min_length=1)

    @model_validator(mode="after")
    def prevent_lookahead(self) -> "CorporateAction":
        if self.announcement_date > self.ex_date:
            raise ValueError("announcement_date must not follow ex_date")
        return self
