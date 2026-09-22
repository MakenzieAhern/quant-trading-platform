from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from itertools import pairwise

from app.domain.markets import TransactionCostSchedule
from app.domain.trading import OrderSide

COST_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)


@dataclass(frozen=True, slots=True)
class EffectiveDatedAShareCommission:
    schedules: tuple[TransactionCostSchedule, ...]

    def __post_init__(self) -> None:
        if not self.schedules:
            raise ValueError("at least one transaction-cost schedule is required")
        ordered = tuple(sorted(self.schedules, key=lambda item: item.valid_from))
        for previous, current in pairwise(ordered):
            if previous.valid_to is None or current.valid_from <= previous.valid_to:
                raise ValueError("transaction-cost schedules must not overlap")
        object.__setattr__(self, "schedules", ordered)

    def calculate(self, quantity: Decimal, price: Decimal) -> Decimal:
        """Conservative RiskEngine estimate: latest buy-side commission and transfer fee."""

        schedule = self.schedules[-1]
        return self._calculate(quantity, price, OrderSide.BUY, schedule)

    def calculate_for_fill(
        self,
        quantity: Decimal,
        price: Decimal,
        side: OrderSide,
        timestamp: datetime,
    ) -> Decimal:
        schedule = self._resolve(timestamp)
        return self._calculate(quantity, price, side, schedule)

    def _resolve(self, timestamp: datetime) -> TransactionCostSchedule:
        trading_date = timestamp.date()
        matching = tuple(
            schedule
            for schedule in self.schedules
            if schedule.valid_from <= trading_date
            and (schedule.valid_to is None or trading_date <= schedule.valid_to)
        )
        if len(matching) != 1:
            raise ValueError("RULE_VERSION_NOT_FOUND")
        return matching[0]

    @staticmethod
    def _calculate(
        quantity: Decimal,
        price: Decimal,
        side: OrderSide,
        schedule: TransactionCostSchedule,
    ) -> Decimal:
        if quantity <= ZERO or price <= ZERO or not quantity.is_finite() or not price.is_finite():
            raise ValueError("quantity and price must be positive finite Decimals")
        with localcontext(COST_CONTEXT):
            notional = quantity * price
            commission = max(notional * schedule.commission_rate, schedule.minimum_commission)
            transfer = notional * schedule.transfer_fee_rate
            stamp = notional * schedule.sell_stamp_duty_rate if side is OrderSide.SELL else ZERO
            return commission + transfer + stamp
