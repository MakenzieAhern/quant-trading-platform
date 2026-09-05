from dataclasses import dataclass, field
from decimal import Decimal

from app.execution.costs import (
    CommissionModel,
    FixedBasisPointSlippage,
    FixedCommission,
    SlippageModel,
)
from app.risk import RiskConfig


def _require_positive_decimal(value: Decimal, name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal instance")
    if not value.is_finite() or value <= Decimal(0):
        raise ValueError(f"{name} must be positive and finite")


def _require_finite_decimal(value: Decimal, name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal instance")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_cash: Decimal = Decimal("100000")
    default_order_quantity: Decimal = Decimal(1)
    commission_model: CommissionModel = field(default_factory=FixedCommission)
    slippage_model: SlippageModel = field(default_factory=FixedBasisPointSlippage)
    periods_per_year: int = 252
    risk_free_rate_per_period: Decimal = Decimal(0)
    risk: RiskConfig = field(default_factory=RiskConfig)

    def __post_init__(self) -> None:
        _require_positive_decimal(self.initial_cash, "initial_cash")
        _require_positive_decimal(self.default_order_quantity, "default_order_quantity")
        if not isinstance(self.commission_model, CommissionModel):
            raise TypeError("commission_model must implement CommissionModel")
        if not isinstance(self.slippage_model, SlippageModel):
            raise TypeError("slippage_model must implement SlippageModel")
        if isinstance(self.periods_per_year, bool) or not isinstance(self.periods_per_year, int):
            raise TypeError("periods_per_year must be an integer")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        _require_finite_decimal(self.risk_free_rate_per_period, "risk_free_rate_per_period")
        if not isinstance(self.risk, RiskConfig):
            raise TypeError("risk must be a RiskConfig instance")
