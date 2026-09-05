from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from app.domain.market import Bar
from app.domain.risk import OrderProposal, RiskConfig, RiskDecision, RiskReasonCode
from app.domain.trading import Fill, Order, OrderSide, OrderStatus, OrderType
from app.event import Event, EventBus, EventType
from app.execution import (
    DuplicateProposalError,
    FixedBasisPointSlippage,
    FixedCommission,
    InvalidOrderTransitionError,
    OrderManagementError,
    OrderManager,
    ReservationError,
    SimulatedBroker,
    transition_order,
)
from app.portfolio import PortfolioEngine
from app.risk import RiskEngine

START = datetime(2024, 1, 1, tzinfo=UTC)


def bar(day: int, price: str = "100", symbol: str = "AAPL") -> Bar:
    value = Decimal(price)
    return Bar(
        symbol=symbol,
        timestamp=START + timedelta(days=day),
        open=value,
        high=value,
        low=value,
        close=value,
        volume=Decimal(100),
    )


def proposal(
    sequence: int,
    *,
    quantity: str = "10",
    side: OrderSide = OrderSide.BUY,
    strategy_id: str = "manual",
    order_type: OrderType = OrderType.MARKET,
    symbol: str = "AAPL",
) -> OrderProposal:
    return OrderProposal(
        proposal_id=UUID(int=sequence),
        strategy_id=strategy_id,
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=Decimal(quantity),
        signal_timestamp=START,
    )


def components(
    risk_config: RiskConfig | None = None,
    *,
    initial_cash: str = "10000",
) -> tuple[EventBus, PortfolioEngine, SimulatedBroker, OrderManager]:
    bus = EventBus()
    portfolio = PortfolioEngine(bus, Decimal(initial_cash))
    broker = SimulatedBroker(bus, FixedCommission(), FixedBasisPointSlippage())
    manager = OrderManager(
        bus,
        broker,
        portfolio,
        RiskEngine(risk_config),
        FixedCommission(),
    )
    portfolio.mark_to_market(bar(0))
    return bus, portfolio, broker, manager


def test_approved_proposal_creates_one_order_and_is_idempotent() -> None:
    _, _, broker, manager = components()
    intent = proposal(1)

    first = manager.process_proposal(intent)
    second = manager.process_proposal(intent)

    assert first == second
    assert first[0].approved
    assert first[1] is not None and first[1].status is OrderStatus.ACCEPTED
    assert manager.proposals == (intent,)
    assert len(manager.decisions) == len(manager.orders) == len(broker.orders) == 1
    assert manager.active_reservation_count == 1

    conflicting = intent.model_copy(update={"quantity": Decimal(11)})
    with pytest.raises(DuplicateProposalError, match="conflicting intent"):
        manager.process_proposal(conflicting)


def test_risk_rejection_stops_before_broker_submission() -> None:
    bus, _, broker, manager = components(RiskConfig(max_position_quantity=Decimal(5)))
    decisions: list[RiskDecision] = []
    broker_rejections: list[Order] = []
    bus.subscribe(EventType.RISK_DECISION, lambda event: decisions.append(event.payload))
    bus.subscribe(EventType.ORDER_REJECTED, lambda event: broker_rejections.append(event.payload))

    bus.publish(Event(EventType.ORDER_PROPOSAL, proposal(1), occurred_at=START))

    assert decisions[0].reason_code is RiskReasonCode.POSITION_LIMIT
    assert manager.orders == broker.orders == ()
    assert manager.active_reservation_count == 0
    assert broker_rejections == []


def test_sequential_reservation_prevents_combined_same_bar_position_breach() -> None:
    _, portfolio, _, manager = components(RiskConfig(max_position_quantity=Decimal(15)))

    first, first_order = manager.process_proposal(proposal(1, quantity="10"))
    second, second_order = manager.process_proposal(proposal(2, quantity="10"))

    assert first.approved and first_order is not None
    assert second.reason_code is RiskReasonCode.POSITION_LIMIT
    assert second.projected_position_quantity == Decimal(20)
    assert second_order is None
    assert portfolio.positions == ()
    assert manager.active_reservation_count == 1


def test_sequential_reservation_prevents_combined_buying_power_breach() -> None:
    _, _, _, manager = components(RiskConfig(enforce_buying_power=True), initial_cash="1000")

    first, _ = manager.process_proposal(proposal(1, quantity="8"))
    second, _ = manager.process_proposal(proposal(2, quantity="8"))

    assert first.approved
    assert second.reason_code is RiskReasonCode.INSUFFICIENT_BUYING_POWER
    assert second.projected_cash == Decimal(-600)


def test_unfilled_sell_proceeds_do_not_fund_another_symbol_buy() -> None:
    _, portfolio, _, manager = components(
        RiskConfig(enforce_buying_power=True), initial_cash="1000"
    )
    portfolio.mark_to_market(bar(0, symbol="MSFT"))

    sell, _ = manager.process_proposal(
        proposal(1, quantity="8", side=OrderSide.SELL, symbol="AAPL")
    )
    buy, order = manager.process_proposal(proposal(2, quantity="15", symbol="MSFT"))

    assert sell.approved
    assert sell.projected_cash == Decimal(1800)
    assert buy.reason_code is RiskReasonCode.INSUFFICIENT_BUYING_POWER
    assert buy.projected_cash == Decimal(300)
    assert order is None


def test_cross_symbol_reservations_enforce_combined_gross_exposure() -> None:
    _, portfolio, _, manager = components(RiskConfig(max_gross_exposure=Decimal(5000)))
    portfolio.mark_to_market(bar(0, symbol="MSFT"))

    first, _ = manager.process_proposal(proposal(1, quantity="30", symbol="AAPL"))
    second, order = manager.process_proposal(proposal(2, quantity="30", symbol="MSFT"))

    assert first.approved
    assert first.projected_gross_exposure == Decimal(3000)
    assert second.reason_code is RiskReasonCode.GROSS_EXPOSURE_LIMIT
    assert second.projected_gross_exposure == Decimal(6000)
    assert order is None


def test_fill_reconciles_actual_portfolio_and_releases_reservation() -> None:
    _, portfolio, broker, manager = components()
    decision, order = manager.process_proposal(proposal(1, quantity="2"))
    assert decision.approved and order is not None

    fills = broker.execute_pending(bar(1, "105"))

    assert len(fills) == 1
    assert portfolio.positions[0].quantity == Decimal(2)
    assert manager.orders[0].status is OrderStatus.FILLED
    assert manager.active_reservation_count == 0
    assert manager.active_reservations == ()


class RejectingBroker:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._orders: list[Order] = []

    @property
    def orders(self) -> tuple[Order, ...]:
        return tuple(self._orders)

    @property
    def fills(self) -> tuple[Fill, ...]:
        return ()

    def submit(self, order: Order) -> Order:
        submitted = transition_order(order, OrderStatus.SUBMITTED)
        self._event_bus.publish(
            Event(EventType.ORDER_SUBMITTED, submitted, occurred_at=submitted.created_at)
        )
        rejected = transition_order(submitted, OrderStatus.REJECTED)
        self._orders.append(rejected)
        self._event_bus.publish(
            Event(EventType.ORDER_REJECTED, rejected, occurred_at=rejected.created_at)
        )
        return rejected

    def execute_pending(self, bar: Bar) -> tuple[Fill, ...]:
        return ()

    def reset(self) -> None:
        self._orders.clear()


class FailingBroker(RejectingBroker):
    def submit(self, order: Order) -> Order:
        raise RuntimeError("broker unavailable")


class SilentBroker(RejectingBroker):
    def submit(self, order: Order) -> Order:
        self._orders.append(order)
        return order


def test_broker_rejection_is_distinct_and_releases_approved_reservation() -> None:
    bus = EventBus()
    portfolio = PortfolioEngine(bus, Decimal(10000))
    broker = RejectingBroker(bus)
    manager = OrderManager(bus, broker, portfolio, RiskEngine(), FixedCommission())
    portfolio.mark_to_market(bar(0))

    decision, order = manager.process_proposal(proposal(1))

    assert decision.reason_code is RiskReasonCode.APPROVED
    assert order is not None and order.status is OrderStatus.REJECTED
    assert manager.orders[0].status is OrderStatus.REJECTED
    assert manager.active_reservation_count == 0


def test_broker_rejection_restores_buying_power_for_next_proposal() -> None:
    bus = EventBus()
    portfolio = PortfolioEngine(bus, Decimal(1000))
    broker = RejectingBroker(bus)
    manager = OrderManager(
        bus,
        broker,
        portfolio,
        RiskEngine(RiskConfig(enforce_buying_power=True)),
        FixedCommission(),
    )
    portfolio.mark_to_market(bar(0))

    first, _ = manager.process_proposal(proposal(1, quantity="8"))
    second, _ = manager.process_proposal(proposal(2, quantity="10"))

    assert first.approved and second.approved
    assert second.projected_cash == Decimal(0)
    assert manager.active_reservations == ()


def test_broker_failure_releases_reservation_before_propagating() -> None:
    bus = EventBus()
    portfolio = PortfolioEngine(bus, Decimal(10000))
    manager = OrderManager(
        bus,
        FailingBroker(bus),
        portfolio,
        RiskEngine(),
        FixedCommission(),
    )
    portfolio.mark_to_market(bar(0))

    with pytest.raises(RuntimeError, match="broker unavailable"):
        manager.process_proposal(proposal(1))
    assert manager.active_reservation_count == 0
    assert manager.proposals == manager.decisions == manager.orders == ()


def test_broker_must_publish_a_lifecycle_matching_its_returned_order() -> None:
    bus = EventBus()
    portfolio = PortfolioEngine(bus, Decimal(10000))
    manager = OrderManager(
        bus,
        SilentBroker(bus),
        portfolio,
        RiskEngine(),
        FixedCommission(),
    )
    portfolio.mark_to_market(bar(0))

    with pytest.raises(OrderManagementError, match="broker result does not match"):
        manager.process_proposal(proposal(1))

    assert manager.proposals == manager.decisions == manager.orders == ()
    assert manager.active_reservations == ()


@pytest.mark.parametrize(
    "event_type",
    [
        EventType.RISK_DECISION,
        EventType.ORDER_CREATED,
        EventType.ORDER_SUBMITTED,
        EventType.ORDER_ACCEPTED,
    ],
)
def test_event_handler_failure_rolls_back_partial_oms_state(event_type: EventType) -> None:
    bus, _, broker, manager = components()

    def fail(_event: Event[object]) -> None:
        raise RuntimeError("downstream handler failed")

    bus.subscribe(event_type, fail)

    with pytest.raises(RuntimeError, match="downstream handler failed"):
        manager.process_proposal(proposal(1))

    assert manager.proposals == manager.decisions == manager.orders == ()
    assert manager.active_reservations == ()
    assert broker.orders == ()


def test_invalid_release_and_illegal_order_transition_fail_explicitly() -> None:
    bus, _, _, manager = components()
    with pytest.raises(ReservationError, match="no active reservation"):
        manager.release_reservation(UUID(int=99))

    _, order = manager.process_proposal(proposal(1))
    assert order is not None
    with pytest.raises(InvalidOrderTransitionError, match="ACCEPTED -> ACCEPTED"):
        bus.publish(Event(EventType.ORDER_ACCEPTED, order, occurred_at=order.created_at))


def test_queries_and_reset_are_deterministic() -> None:
    _, _, broker, manager = components()
    manager.process_proposal(proposal(1, strategy_id="first"))
    manager.process_proposal(proposal(2, strategy_id="second"))

    assert manager.get_order(UUID(int=1)) == manager.orders[0]
    assert manager.orders_for_strategy("second") == (manager.orders[1],)
    assert manager.orders_for_symbol("AAPL") == manager.orders

    manager.reset()
    broker.reset()
    assert manager.proposals == manager.decisions == manager.orders == ()
    assert manager.active_reservation_count == 0
