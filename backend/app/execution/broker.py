from collections.abc import Callable
from decimal import Decimal
from typing import Protocol

from app.domain.market import Bar
from app.domain.trading import Fill, Order, OrderSide, OrderStatus, OrderType
from app.event import Event, EventBus, EventType
from app.execution.costs import CommissionModel, ContextualCommissionModel, SlippageModel
from app.execution.state import transition_order


class BrokerExecutionError(ValueError):
    """Raised when simulated execution would violate its deterministic contract."""


class ExecutionBroker(Protocol):
    @property
    def orders(self) -> tuple[Order, ...]: ...

    @property
    def fills(self) -> tuple[Fill, ...]: ...

    def submit(self, order: Order) -> Order: ...

    def execute_pending(self, bar: Bar) -> tuple[Fill, ...]: ...

    def reset(self) -> None: ...


class SimulatedBroker:
    """All-or-nothing MARKET execution at the next same-symbol Bar open."""

    def __init__(
        self,
        event_bus: EventBus,
        commission_model: CommissionModel,
        slippage_model: SlippageModel,
        *,
        limit_fill_eligible: Callable[[Order, Bar], bool] | None = None,
    ) -> None:
        self._event_bus = event_bus
        self._commission_model = commission_model
        self._slippage_model = slippage_model
        self._limit_fill_eligible = limit_fill_eligible
        self._orders: list[Order] = []
        self._pending: list[Order] = []
        self._fills: list[Fill] = []

    @property
    def orders(self) -> tuple[Order, ...]:
        return tuple(self._orders)

    @property
    def pending_orders(self) -> tuple[Order, ...]:
        return tuple(self._pending)

    @property
    def fills(self) -> tuple[Fill, ...]:
        return tuple(self._fills)

    def submit(self, order: Order) -> Order:
        if any(existing.id == order.id for existing in self._orders):
            raise BrokerExecutionError(f"order is already known: {order.id}")

        try:
            submitted = transition_order(order, OrderStatus.SUBMITTED)
            self._orders.append(submitted)
            self._publish(EventType.ORDER_SUBMITTED, submitted)

            if submitted.order_type is not OrderType.MARKET and not (
                submitted.order_type is OrderType.LIMIT and self._limit_fill_eligible is not None
            ):
                rejected = transition_order(submitted, OrderStatus.REJECTED)
                self._replace_order(rejected)
                self._publish(EventType.ORDER_REJECTED, rejected)
                return rejected

            accepted = transition_order(submitted, OrderStatus.ACCEPTED)
            self._replace_order(accepted)
            self._pending.append(accepted)
            self._publish(EventType.ORDER_ACCEPTED, accepted)
            return accepted
        except Exception:
            self._orders = [existing for existing in self._orders if existing.id != order.id]
            self._pending = [existing for existing in self._pending if existing.id != order.id]
            raise

    def execute_pending(self, bar: Bar) -> tuple[Fill, ...]:
        executable = tuple(
            order
            for order in self._pending
            if order.symbol == bar.symbol
            and order.created_at < bar.timestamp
            and self._eligible(order, bar)
        )
        return tuple(self._fill(order, bar) for order in executable)

    def _eligible(self, order: Order, bar: Bar) -> bool:
        if order.order_type is OrderType.MARKET:
            return True
        if self._limit_fill_eligible is None or not self._limit_fill_eligible(order, bar):
            return False
        assert order.price is not None
        price = self._slippage_model.apply(bar.open, order.side)
        return price <= order.price if order.side is OrderSide.BUY else price >= order.price

    def cancel_pending(self) -> tuple[Order, ...]:
        """Cancel every locally pending order without implying external activity."""
        cancelled: list[Order] = []
        for order in tuple(self._pending):
            updated = transition_order(order, OrderStatus.CANCELLED)
            self._pending.remove(order)
            self._replace_order(updated)
            self._publish(EventType.ORDER_CANCELLED, updated)
            cancelled.append(updated)
        return tuple(cancelled)

    def reset(self) -> None:
        self._orders.clear()
        self._pending.clear()
        self._fills.clear()

    def _fill(self, order: Order, bar: Bar) -> Fill:
        fill_price = self._slippage_model.apply(bar.open, order.side)
        self._validate_fill_price(bar.open, fill_price, order.side)
        if isinstance(self._commission_model, ContextualCommissionModel):
            commission = self._commission_model.calculate_for_fill(
                order.quantity,
                fill_price,
                order.side,
                bar.timestamp,
            )
        else:
            commission = self._commission_model.calculate(order.quantity, fill_price)
        if not isinstance(commission, Decimal):
            raise BrokerExecutionError("commission model must return Decimal")
        if not commission.is_finite() or commission < Decimal(0):
            raise BrokerExecutionError("commission model returned an invalid commission")

        fill = Fill(
            order_id=order.id,
            strategy_id=order.strategy_id,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            commission=commission,
            timestamp=bar.timestamp,
        )
        filled_order = transition_order(order, OrderStatus.FILLED)
        self._pending.remove(order)
        self._replace_order(filled_order)
        self._fills.append(fill)
        self._publish(EventType.ORDER_FILLED, fill)
        return fill

    @staticmethod
    def _validate_fill_price(market_price: Decimal, fill_price: Decimal, side: OrderSide) -> None:
        if not isinstance(fill_price, Decimal):
            raise BrokerExecutionError("slippage model must return Decimal")
        if not fill_price.is_finite() or fill_price <= Decimal(0):
            raise BrokerExecutionError("slippage model returned an invalid fill price")
        if side is OrderSide.BUY and fill_price < market_price:
            raise BrokerExecutionError("slippage must not improve a BUY price")
        if side is OrderSide.SELL and fill_price > market_price:
            raise BrokerExecutionError("slippage must not improve a SELL price")

    def _replace_order(self, updated: Order) -> None:
        for index, order in enumerate(self._orders):
            if order.id == updated.id:
                self._orders[index] = updated
                return
        raise BrokerExecutionError(f"order is not known: {updated.id}")

    def _publish(self, event_type: EventType, payload: Order | Fill) -> None:
        timestamp = payload.created_at if isinstance(payload, Order) else payload.timestamp
        self._event_bus.publish(Event(event_type, payload, occurred_at=timestamp))
