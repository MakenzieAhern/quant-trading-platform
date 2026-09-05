from datetime import UTC, datetime, timedelta
from decimal import ROUND_DOWN, Decimal, localcontext
from typing import Any

import pytest
from pydantic import ValidationError

from app.domain.market import Bar
from app.domain.trading import Fill, Order, OrderSide, OrderStatus, OrderType
from app.event import Event, EventBus, EventType
from app.execution import (
    FixedBasisPointSlippage,
    FixedCommission,
    InvalidOrderTransitionError,
    PercentageCommission,
    SimulatedBroker,
    transition_order,
)

START = datetime(2024, 1, 1, tzinfo=UTC)


def make_order(**overrides: Any) -> Order:
    values: dict[str, Any] = {
        "strategy_id": "strategy",
        "symbol": "AAPL",
        "side": OrderSide.BUY,
        "order_type": OrderType.MARKET,
        "quantity": Decimal("2"),
        "created_at": START,
    }
    values.update(overrides)
    return Order.model_validate(values)


def make_bar(day: int, open_price: str, symbol: str = "AAPL") -> Bar:
    price = Decimal(open_price)
    return Bar(
        symbol=symbol,
        timestamp=START + timedelta(days=day),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal(100),
    )


def test_order_state_machine_allows_only_explicit_transitions() -> None:
    created = make_order()
    submitted = transition_order(created, OrderStatus.SUBMITTED)
    accepted = transition_order(submitted, OrderStatus.ACCEPTED)
    filled = transition_order(accepted, OrderStatus.FILLED)

    assert [created.status, submitted.status, accepted.status, filled.status] == [
        OrderStatus.CREATED,
        OrderStatus.SUBMITTED,
        OrderStatus.ACCEPTED,
        OrderStatus.FILLED,
    ]
    with pytest.raises(InvalidOrderTransitionError, match="CREATED -> FILLED"):
        transition_order(created, OrderStatus.FILLED)
    with pytest.raises(InvalidOrderTransitionError, match="FILLED -> SUBMITTED"):
        transition_order(filled, OrderStatus.SUBMITTED)


def test_order_quantity_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="greater than 0"):
        make_order(quantity=Decimal(0))


def test_commission_models_use_decimal_and_validate_values() -> None:
    assert FixedCommission(Decimal("1.25")).calculate(Decimal(2), Decimal(100)) == Decimal("1.25")
    percentage = PercentageCommission(Decimal("0.001"))
    assert percentage.calculate(Decimal(10), Decimal(100)) == Decimal("1.000")
    assert percentage.calculate(Decimal(-10), Decimal(100)) == Decimal("1.000")

    with pytest.raises(ValueError, match="non-negative"):
        FixedCommission(Decimal("-1"))
    with pytest.raises(ValueError, match="non-negative"):
        PercentageCommission(Decimal("-0.01"))
    with pytest.raises(TypeError, match="Decimal"):
        FixedCommission(1)  # type: ignore[arg-type]


def test_basis_point_slippage_is_always_adverse() -> None:
    slippage = FixedBasisPointSlippage(Decimal(5))

    assert slippage.apply(Decimal(100), OrderSide.BUY) == Decimal("100.0500")
    assert slippage.apply(Decimal(100), OrderSide.SELL) == Decimal("99.9500")

    with pytest.raises(ValueError, match="non-negative"):
        FixedBasisPointSlippage(Decimal("-1"))
    with pytest.raises(ValueError, match="less than 10000"):
        FixedBasisPointSlippage(Decimal(10_000))


def test_transaction_cost_context_is_isolated_and_deterministic() -> None:
    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        slipped = FixedBasisPointSlippage(Decimal(5)).apply(Decimal("123.456789"), OrderSide.BUY)
        commission = PercentageCommission(Decimal("0.001")).calculate(
            Decimal("3.25"), Decimal("123.456789")
        )
        assert context.prec == 6
        assert context.rounding == ROUND_DOWN

    assert slipped == Decimal("123.5185173945")
    assert commission == Decimal("0.40123456425")


def test_simulated_broker_fills_market_order_only_on_later_matching_bar() -> None:
    bus = EventBus()
    events: list[Event[Any]] = []
    for event_type in (
        EventType.ORDER_SUBMITTED,
        EventType.ORDER_ACCEPTED,
        EventType.ORDER_FILLED,
    ):
        bus.subscribe(event_type, events.append)
    broker = SimulatedBroker(
        bus,
        FixedCommission(Decimal(1)),
        FixedBasisPointSlippage(Decimal(5)),
    )
    order = make_order()

    accepted = broker.submit(order)
    assert accepted.status is OrderStatus.ACCEPTED
    assert broker.execute_pending(make_bar(0, "90")) == ()
    assert broker.execute_pending(make_bar(1, "90", symbol="MSFT")) == ()

    fills = broker.execute_pending(make_bar(1, "105"))

    assert len(fills) == 1
    assert fills[0] == Fill(
        order_id=order.id,
        strategy_id="strategy",
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=Decimal(2),
        price=Decimal("105.0525"),
        commission=Decimal(1),
        timestamp=START + timedelta(days=1),
    )
    assert broker.orders[0].status is OrderStatus.FILLED
    assert [event.event_type for event in events] == [
        EventType.ORDER_SUBMITTED,
        EventType.ORDER_ACCEPTED,
        EventType.ORDER_FILLED,
    ]


def test_simulated_broker_rejects_unsupported_limit_order() -> None:
    bus = EventBus()
    events: list[EventType] = []
    bus.subscribe(EventType.ORDER_SUBMITTED, lambda event: events.append(event.event_type))
    bus.subscribe(EventType.ORDER_REJECTED, lambda event: events.append(event.event_type))
    broker = SimulatedBroker(bus, FixedCommission(), FixedBasisPointSlippage())

    rejected = broker.submit(make_order(order_type=OrderType.LIMIT, price=Decimal(100)))

    assert rejected.status is OrderStatus.REJECTED
    assert broker.pending_orders == ()
    assert events == [EventType.ORDER_SUBMITTED, EventType.ORDER_REJECTED]


def test_simulated_broker_rejects_duplicate_submission() -> None:
    broker = SimulatedBroker(EventBus(), FixedCommission(), FixedBasisPointSlippage())
    order = make_order()
    broker.submit(order)
    with pytest.raises(ValueError, match="already known"):
        broker.submit(order)


class NegativeCommission:
    def calculate(self, quantity: Decimal, price: Decimal) -> Decimal:
        return Decimal("-1")


class ImprovingSlippage:
    def apply(self, market_price: Decimal, side: OrderSide) -> Decimal:
        return market_price - Decimal(1)


def test_broker_rejects_invalid_custom_transaction_cost() -> None:
    broker = SimulatedBroker(EventBus(), NegativeCommission(), FixedBasisPointSlippage())
    broker.submit(make_order())

    with pytest.raises(ValueError, match="invalid commission"):
        broker.execute_pending(make_bar(1, "100"))
    assert broker.orders[0].status is OrderStatus.ACCEPTED
    assert broker.pending_orders == (broker.orders[0],)
    assert broker.fills == ()


def test_broker_keeps_order_pending_when_custom_slippage_is_invalid() -> None:
    broker = SimulatedBroker(EventBus(), FixedCommission(), ImprovingSlippage())
    broker.submit(make_order())

    with pytest.raises(ValueError, match="must not improve a BUY"):
        broker.execute_pending(make_bar(1, "100"))
    assert broker.orders[0].status is OrderStatus.ACCEPTED
    assert broker.pending_orders == (broker.orders[0],)
    assert broker.fills == ()
