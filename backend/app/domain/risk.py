from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import Field, model_validator

from app.domain.common import FiniteDecimal, PositiveDecimal, Symbol, UtcDateTime
from app.domain.trading import DomainModel, OrderSide, OrderType


class RiskReasonCode(StrEnum):
    APPROVED = "APPROVED"
    INVALID_QUANTITY = "INVALID_QUANTITY"
    UNSUPPORTED_ORDER_TYPE = "UNSUPPORTED_ORDER_TYPE"
    ORDER_NOTIONAL_LIMIT = "ORDER_NOTIONAL_LIMIT"
    POSITION_LIMIT = "POSITION_LIMIT"
    SYMBOL_EXPOSURE_LIMIT = "SYMBOL_EXPOSURE_LIMIT"
    GROSS_EXPOSURE_LIMIT = "GROSS_EXPOSURE_LIMIT"
    LEVERAGE_LIMIT = "LEVERAGE_LIMIT"
    INSUFFICIENT_BUYING_POWER = "INSUFFICIENT_BUYING_POWER"
    DRAWDOWN_LIMIT = "DRAWDOWN_LIMIT"
    INVALID_PORTFOLIO_STATE = "INVALID_PORTFOLIO_STATE"


class OrderProposal(DomainModel):
    proposal_id: UUID
    strategy_id: str = Field(min_length=1)
    symbol: Symbol
    side: OrderSide
    order_type: OrderType
    quantity: FiniteDecimal
    signal_timestamp: UtcDateTime
    limit_price: PositiveDecimal | None = None
    intended_execution_session: date | None = None

    @model_validator(mode="after")
    def validate_market_price(self) -> Self:
        if self.order_type is OrderType.MARKET and self.limit_price is not None:
            raise ValueError("market proposal cannot have a limit price")
        return self


class RiskReservation(DomainModel):
    proposal_id: UUID
    order_id: UUID
    symbol: Symbol
    signed_quantity: FiniteDecimal
    cash_delta: FiniteDecimal
    buying_power_consumed: FiniteDecimal

    @model_validator(mode="after")
    def validate_buying_power_consumed(self) -> Self:
        if self.buying_power_consumed < 0:
            raise ValueError("buying_power_consumed must be non-negative")
        return self


class RiskDecision(DomainModel):
    proposal_id: UUID
    approved: bool
    reason_code: RiskReasonCode
    message: str = Field(min_length=1)
    timestamp: UtcDateTime
    risk_increasing: bool
    reference_price: FiniteDecimal | None = None
    order_notional: FiniteDecimal | None = None
    projected_position_quantity: FiniteDecimal | None = None
    projected_symbol_exposure: FiniteDecimal | None = None
    projected_gross_exposure: FiniteDecimal | None = None
    projected_net_exposure: FiniteDecimal | None = None
    projected_gross_leverage: FiniteDecimal | None = None
    projected_cash: FiniteDecimal | None = None
    estimated_transaction_cost: FiniteDecimal | None = None

    @model_validator(mode="after")
    def validate_approval_reason(self) -> Self:
        if self.approved != (self.reason_code is RiskReasonCode.APPROVED):
            raise ValueError("approved must match the APPROVED reason code")
        if self.estimated_transaction_cost is not None and self.estimated_transaction_cost < 0:
            raise ValueError("estimated_transaction_cost must be non-negative")
        return self


class RiskConfig(DomainModel):
    max_order_notional: FiniteDecimal | None = None
    max_position_quantity: FiniteDecimal | None = None
    max_symbol_exposure: FiniteDecimal | None = None
    max_gross_exposure: FiniteDecimal | None = None
    max_leverage: FiniteDecimal | None = None
    enforce_buying_power: bool = False
    max_drawdown: FiniteDecimal | None = None
    allow_limit_orders: bool = False

    @model_validator(mode="after")
    def validate_limits(self) -> Self:
        for name in (
            "max_order_notional",
            "max_position_quantity",
            "max_symbol_exposure",
            "max_gross_exposure",
            "max_leverage",
        ):
            value = getattr(self, name)
            if value is not None and value <= 0:
                raise ValueError(f"{name} must be positive when configured")
        if self.max_drawdown is not None and not Decimal("-1") <= self.max_drawdown <= 0:
            raise ValueError("max_drawdown must be between -1 and 0")
        return self
