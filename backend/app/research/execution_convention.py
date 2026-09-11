"""Approved daily-bar proxy, not reconstruction of actual auction executions."""

from decimal import ROUND_HALF_UP, Decimal

from app.data.providers.research import DailyBarRecord
from app.domain.markets.rules import DailySecurityStatus, ResolvedTradingRules
from app.domain.trading import Order, OrderSide, OrderType

VERSION = "CN_A_DAILY_OPENING_LIMIT_V1"
CLASSIFICATION = "SIMULATION_ASSUMPTION"


def rejection_reason(
    order: Order,
    bar: DailyBarRecord,
    status: DailySecurityStatus | None,
    rules: ResolvedTradingRules | None,
    held_quantity: Decimal,
) -> str | None:
    """Future observations can veto an immutable instruction, never reprice it."""
    if order.order_type is not OrderType.LIMIT or order.price is None:
        return "LIMIT_INSTRUCTION_REQUIRED"
    if order.intended_execution_session != bar.trading_date:
        return "EXPIRED_SESSION"
    if status is None or rules is None:
        return "MISSING_STATUS_OR_RULES"
    if any(
        item.security_id != bar.security_id or item.trading_date != bar.trading_date
        for item in (status, rules)
    ):
        return "IDENTITY_MISMATCH"
    if status.is_tradeable is not True or status.is_suspended or rules.suspended:
        return "NOT_CONFIRMED_TRADEABLE"
    if not rules.executable or OrderType.LIMIT not in rules.permitted_order_types:
        return "RULE_NOT_EXECUTABLE"
    if rules.price_limit_rate is None or bar.pre_close is None:
        return "UNSUPPORTED_UNBOUNDED_OR_MISSING_REFERENCE"
    if status.is_one_price_limit or bar.raw_high == bar.raw_low:
        return "SINGLE_PRICE_OR_LOCKED"
    quantity = order.quantity
    if quantity != quantity.to_integral_value() or rules.maximum_limit_quantity is None:
        return "INVALID_OR_UNKNOWN_QUANTITY_RULE"
    if quantity > rules.maximum_limit_quantity:
        return "MAXIMUM_QUANTITY"
    regular = (
        quantity >= rules.minimum_buy_quantity
        and (quantity - rules.minimum_buy_quantity) % rules.buy_quantity_increment == 0
    )
    if order.side is OrderSide.SELL:
        if quantity > held_quantity:
            return "INSUFFICIENT_SETTLED_HOLDING"
        regular = regular or (quantity == held_quantity and quantity < rules.minimum_buy_quantity)
    if not regular:
        return "LOT_SIZE"
    tick = rules.minimum_tick
    if order.price % tick != 0:
        return "TICK_SIZE"
    if any(price % tick != 0 for price in (bar.raw_open, bar.raw_high, bar.raw_low, bar.raw_close)):
        return "OBSERVATION_TICK_SIZE"
    reference = bar.pre_close
    upper = max(
        reference + tick,
        ((reference * (1 + rules.price_limit_rate)) / tick).quantize(
            Decimal(1), rounding=ROUND_HALF_UP
        )
        * tick,
    )
    lower = max(
        tick,
        min(
            reference - tick,
            ((reference * (1 - rules.price_limit_rate)) / tick).quantize(
                Decimal(1), rounding=ROUND_HALF_UP
            )
            * tick,
        ),
    )
    if not lower <= order.price <= upper:
        return "LIMIT_OUTSIDE_LEGAL_BOUNDS"
    if not lower < bar.raw_open < upper or bar.raw_low < lower or bar.raw_high > upper:
        return "BOUNDARY_OR_INVALID_OBSERVATION"
    if (order.side is OrderSide.BUY and bar.raw_open > order.price) or (
        order.side is OrderSide.SELL and bar.raw_open < order.price
    ):
        return "OPEN_OUTSIDE_PRECOMMITTED_LIMIT"
    # ponytail: daily participation is a proxy, not auction queue/liquidity evidence.
    if quantity > bar.volume * Decimal("0.01"):
        return "DAILY_PARTICIPATION_CAP"
    return None
