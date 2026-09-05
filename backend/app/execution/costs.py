from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Protocol, runtime_checkable

from app.domain.trading import OrderSide

EXECUTION_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)
ONE = Decimal(1)
BASIS_POINT_DENOMINATOR = Decimal(10_000)


def _require_decimal(value: Decimal, name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{name} must be a Decimal instance")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")


@runtime_checkable
class CommissionModel(Protocol):
    def calculate(self, quantity: Decimal, price: Decimal) -> Decimal: ...


@runtime_checkable
class SlippageModel(Protocol):
    def apply(self, market_price: Decimal, side: OrderSide) -> Decimal: ...


@dataclass(frozen=True, slots=True)
class FixedCommission:
    amount: Decimal = ZERO

    def __post_init__(self) -> None:
        _require_decimal(self.amount, "amount")
        if self.amount < ZERO:
            raise ValueError("amount must be non-negative")

    def calculate(self, quantity: Decimal, price: Decimal) -> Decimal:
        _require_decimal(quantity, "quantity")
        _require_decimal(price, "price")
        return self.amount


@dataclass(frozen=True, slots=True)
class PercentageCommission:
    """Charge `rate` as a fraction of absolute notional; 0.001 means 0.1%."""

    rate: Decimal

    def __post_init__(self) -> None:
        _require_decimal(self.rate, "rate")
        if self.rate < ZERO:
            raise ValueError("rate must be non-negative")

    def calculate(self, quantity: Decimal, price: Decimal) -> Decimal:
        _require_decimal(quantity, "quantity")
        _require_decimal(price, "price")
        with localcontext(EXECUTION_CONTEXT):
            return abs(quantity * price) * self.rate


@dataclass(frozen=True, slots=True)
class FixedBasisPointSlippage:
    basis_points: Decimal = ZERO

    def __post_init__(self) -> None:
        _require_decimal(self.basis_points, "basis_points")
        if self.basis_points < ZERO:
            raise ValueError("basis_points must be non-negative")
        if self.basis_points >= BASIS_POINT_DENOMINATOR:
            raise ValueError("basis_points must be less than 10000")

    def apply(self, market_price: Decimal, side: OrderSide) -> Decimal:
        _require_decimal(market_price, "market_price")
        if market_price <= ZERO:
            raise ValueError("market_price must be positive")
        with localcontext(EXECUTION_CONTEXT):
            rate = self.basis_points / BASIS_POINT_DENOMINATOR
            multiplier = ONE + rate if side is OrderSide.BUY else ONE - rate
            return market_price * multiplier
