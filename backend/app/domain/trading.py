from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal, Self
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.domain.common import (
    FiniteDecimal,
    NonNegativeDecimal,
    PositiveDecimal,
    Symbol,
    UtcDateTime,
)


class SignalType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(StrEnum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderStatus(StrEnum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class DomainModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Signal(DomainModel):
    strategy_id: str = Field(min_length=1)
    symbol: Symbol
    timestamp: UtcDateTime
    signal_type: SignalType


class Order(DomainModel):
    id: UUID = Field(default_factory=uuid4)
    strategy_id: str = Field(min_length=1)
    symbol: Symbol
    side: OrderSide
    order_type: OrderType
    quantity: PositiveDecimal
    price: PositiveDecimal | None = None
    status: OrderStatus = OrderStatus.CREATED
    created_at: UtcDateTime
    intended_execution_session: date | None = None

    @model_validator(mode="after")
    def validate_order_price(self) -> Self:
        if self.order_type is OrderType.LIMIT and self.price is None:
            raise ValueError("limit orders require a price")
        if self.order_type is OrderType.MARKET and self.price is not None:
            raise ValueError("market orders must not specify a price")
        return self


class Fill(DomainModel):
    order_id: UUID
    strategy_id: str = Field(min_length=1)
    symbol: Symbol
    side: OrderSide
    quantity: PositiveDecimal
    price: PositiveDecimal
    commission: NonNegativeDecimal
    timestamp: UtcDateTime


class Position(DomainModel):
    symbol: Symbol
    quantity: FiniteDecimal
    average_price: NonNegativeDecimal
    market_price: NonNegativeDecimal
    unrealized_pnl: FiniteDecimal
    realized_pnl: FiniteDecimal
    aggregate_cost_basis: NonNegativeDecimal | None = None


class PendingDemergerEntitlement(DomainModel):
    parent_symbol: Symbol
    successor_symbols: tuple[Symbol, ...]
    event_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    parent_quantity: PositiveDecimal
    aggregate_cost_basis: NonNegativeDecimal
    carrying_value: NonNegativeDecimal
    valuation_label: Literal["CORPORATE_ACTION_PENDING_CARRY_VALUE"] = (
        "CORPORATE_ACTION_PENDING_CARRY_VALUE"
    )
    tradable: Literal[False] = False
    orderable: Literal[False] = False
    executable: Literal[False] = False

    @property
    def unrealized_pnl(self) -> Decimal:
        return self.carrying_value - self.aggregate_cost_basis


class PortfolioSnapshot(DomainModel):
    timestamp: UtcDateTime
    cash: FiniteDecimal
    positions: tuple[Position, ...] = ()
    market_value: FiniteDecimal
    equity: FiniteDecimal
    realized_pnl: FiniteDecimal = Decimal(0)
    unrealized_pnl: FiniteDecimal = Decimal(0)
    cumulative_commission: NonNegativeDecimal = Decimal(0)
    drawdown: FiniteDecimal
    pending_demergers: tuple[PendingDemergerEntitlement, ...] = ()
