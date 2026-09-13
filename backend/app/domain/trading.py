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


class ShareConsolidationAudit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    security_id: str
    effective_date: date
    original_quantity: NonNegativeDecimal
    theoretical_quantity: NonNegativeDecimal
    new_quantity: NonNegativeDecimal
    discarded_fraction: NonNegativeDecimal
    original_basis: NonNegativeDecimal
    retained_basis: NonNegativeDecimal
    basis_written_off: NonNegativeDecimal
    policy: Literal["CN_A_SHARE_CONSOLIDATION_POLICY_V1"] = "CN_A_SHARE_CONSOLIDATION_POLICY_V1"
    fractional_treatment: Literal["EXACT", "OFFICIAL_FLOOR", "RESEARCH_FLOOR"]
    zero_whole_policy: Literal["WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"] = (
        "WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"
    )


class RestructuringBonusPassThroughAudit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    security_id: str = Field(pattern=r"^CN-A:(SSE|SZSE):[0-9]{6}$")
    effective_date: date
    temporary_registration_date: date
    transfer_date: date
    transfer_recipient: str
    original_quantity: NonNegativeDecimal
    original_basis: NonNegativeDecimal
    bonus_ratio: PositiveDecimal
    temporary_bonus_quantity: NonNegativeDecimal
    quantity_measure: Literal["THEORETICAL_RATIO_NOT_REGISTRY_ALLOCATION"] = (
        "THEORETICAL_RATIO_NOT_REGISTRY_ALLOCATION"
    )
    temporary_legal_registration: Literal[True] = True
    portfolio_tradable_holding: Literal[False] = False
    portfolio_cost_basis_allocated: Literal[False] = False
    policy: Literal["CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1"] = (
        "CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1"
    )
    basis_policy: Literal["NET_PASS_THROUGH_NO_BASIS_ALLOCATION"] = (
        "NET_PASS_THROUGH_NO_BASIS_ALLOCATION"
    )
    convention_approval_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


class PartialShareSurrenderAudit(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    security_id: str = Field(pattern=r"^CN-A:(SSE|SZSE):[0-9]{6}$")
    effective_date: date
    affected_holder_class: str
    policy: Literal["CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1"] = (
        "CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1"
    )
    classification: Literal["CORPORATE_ACTION_MANDATORY_SHARE_SURRENDER_LOSS"] = (
        "CORPORATE_ACTION_MANDATORY_SHARE_SURRENDER_LOSS"
    )
    original_quantity: PositiveDecimal
    surrendered_quantity: PositiveDecimal
    retained_quantity: NonNegativeDecimal
    original_basis: NonNegativeDecimal
    surrendered_basis: NonNegativeDecimal
    retained_basis: NonNegativeDecimal
    market_value_removed: NonNegativeDecimal
    historical_registry_date: date | None = None
    research_boundary: str | None = None
    official_fraction_rule: str | None = None
    research_fraction_rule: str | None = None
    convention_approval_sha256: str | None = None
    theoretical_surrender: NonNegativeDecimal | None = None
    lower_surrender_bound: NonNegativeDecimal | None = None
    extra_shares_vs_floor: NonNegativeDecimal = Decimal(0)
    estimated_value_difference: NonNegativeDecimal = Decimal(0)


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


class PendingMergerEntitlement(PendingDemergerEntitlement):
    whole_successor_quantity: PositiveDecimal


class MergerRoundingAudit(DomainModel):
    event_checksum: str = Field(pattern=r"^[0-9a-f]{64}$")
    parent_symbol: Symbol
    successor_symbol: Symbol
    parent_quantity: PositiveDecimal
    theoretical_successor_quantity: PositiveDecimal
    whole_successor_quantity: NonNegativeDecimal
    fractional_remainder: Decimal = Field(ge=0, lt=1, allow_inf_nan=False)
    label: Literal["UNREALIZED_HISTORICAL_ROUNDING_REMAINDER"] = (
        "UNREALIZED_HISTORICAL_ROUNDING_REMAINDER"
    )
    first_available_raw_price: PositiveDecimal | None = None
    maximum_observed_raw_price: PositiveDecimal | None = None
    maximum_estimated_discarded_value: NonNegativeDecimal | None = None
    floor_ceil_quantity_difference: NonNegativeDecimal
    maximum_floor_ceil_value_difference: NonNegativeDecimal | None = None
    zero_whole_share_policy: (
        Literal["WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"] | None
    ) = None
    accounting_classification: Literal["CORPORATE_ACTION_FRACTIONAL_FORFEITURE_LOSS"] | None = None
    basis_written_off: NonNegativeDecimal = Decimal(0)
    market_value_removed: NonNegativeDecimal = Decimal(0)


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
    pending_mergers: tuple[PendingMergerEntitlement, ...] = ()
    merger_rounding_audits: tuple[MergerRoundingAudit, ...] = ()
    partial_surrender_audits: tuple[PartialShareSurrenderAudit, ...] = ()
    pass_through_audits: tuple[RestructuringBonusPassThroughAudit, ...] = ()
    consolidation_audits: tuple[ShareConsolidationAudit, ...] = ()
    corporate_action_realized_pnl: FiniteDecimal = Decimal(0)
    total_pnl: FiniteDecimal = Decimal(0)

    def pnl_breakdown(self) -> dict[str, Decimal]:
        """Legacy realized_pnl remains trading-only; total is net of commissions."""
        return {
            "TRADING_REALIZED_PNL": self.realized_pnl,
            "CORPORATE_ACTION_REALIZED_PNL": self.corporate_action_realized_pnl,
            "UNREALIZED_PNL": self.unrealized_pnl,
            "TOTAL_PNL": self.total_pnl,
        }
