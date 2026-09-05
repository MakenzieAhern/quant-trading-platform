from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Context, Decimal, localcontext
from typing import Any
from uuid import UUID

from app.domain.risk import OrderProposal, RiskDecision
from app.domain.trading import Fill, Order, OrderSide, OrderStatus, OrderType
from app.event import Event, EventBus, EventType
from app.execution.broker import ExecutionBroker
from app.execution.costs import CommissionModel
from app.execution.state import transition_order
from app.portfolio import PortfolioEngine
from app.risk import RiskEngine

OMS_CONTEXT = Context(prec=28, rounding=ROUND_HALF_EVEN)
ZERO = Decimal(0)


class OrderManagementError(ValueError):
    """Raised when proposal, order, or reservation state is inconsistent."""


class DuplicateProposalError(OrderManagementError):
    """Raised when one proposal ID is reused for different intent."""


class ReservationError(OrderManagementError):
    """Raised when risk capacity cannot be reconciled deterministically."""


@dataclass(frozen=True, slots=True)
class _Reservation:
    proposal_id: UUID
    order_id: UUID
    symbol: str
    signed_quantity: Decimal
    cash_delta: Decimal


class OrderManager:
    """Coordinate proposals, pre-trade decisions, orders, and risk reservations."""

    def __init__(
        self,
        event_bus: EventBus,
        broker: ExecutionBroker,
        portfolio: PortfolioEngine,
        risk_engine: RiskEngine,
        commission_model: CommissionModel,
    ) -> None:
        self._event_bus = event_bus
        self._broker = broker
        self._portfolio = portfolio
        self._risk_engine = risk_engine
        self._commission_model = commission_model
        self._proposals: dict[UUID, OrderProposal] = {}
        self._decisions: dict[UUID, RiskDecision] = {}
        self._orders: dict[UUID, Order] = {}
        self._order_by_proposal: dict[UUID, UUID] = {}
        self._reservations: dict[UUID, _Reservation] = {}
        self._event_bus.subscribe(EventType.ORDER_PROPOSAL, self._on_proposal)
        self._event_bus.subscribe(EventType.ORDER_SUBMITTED, self._on_order_state)
        self._event_bus.subscribe(EventType.ORDER_ACCEPTED, self._on_order_state)
        self._event_bus.subscribe(EventType.ORDER_REJECTED, self._on_order_state)
        self._event_bus.subscribe(EventType.ORDER_FILLED, self._on_fill)

    @property
    def proposals(self) -> tuple[OrderProposal, ...]:
        return tuple(self._proposals.values())

    @property
    def decisions(self) -> tuple[RiskDecision, ...]:
        return tuple(self._decisions.values())

    @property
    def orders(self) -> tuple[Order, ...]:
        return tuple(self._orders.values())

    @property
    def active_reservation_count(self) -> int:
        return len(self._reservations)

    def get_order(self, order_id: UUID) -> Order | None:
        return self._orders.get(order_id)

    def orders_for_strategy(self, strategy_id: str) -> tuple[Order, ...]:
        return tuple(order for order in self._orders.values() if order.strategy_id == strategy_id)

    def orders_for_symbol(self, symbol: str) -> tuple[Order, ...]:
        return tuple(order for order in self._orders.values() if order.symbol == symbol)

    def process_proposal(self, proposal: OrderProposal) -> tuple[RiskDecision, Order | None]:
        existing = self._proposals.get(proposal.proposal_id)
        if existing is not None:
            if existing != proposal:
                raise DuplicateProposalError(
                    f"proposal ID has conflicting intent: {proposal.proposal_id}"
                )
            order_id = self._order_by_proposal.get(proposal.proposal_id)
            return self._decisions[proposal.proposal_id], (
                self._orders[order_id] if order_id is not None else None
            )

        marks = self._portfolio.marks
        reference_price = marks.get(proposal.symbol)
        estimated_cost = ZERO
        if (
            reference_price is not None
            and proposal.quantity > ZERO
            and proposal.order_type is OrderType.MARKET
        ):
            estimated_cost = self._commission_model.calculate(proposal.quantity, reference_price)
        reserved_quantities, reserved_cash_delta = self._reservation_state()
        decision = self._risk_engine.evaluate(
            proposal,
            self._portfolio.latest_snapshot,
            marks,
            reserved_quantities=reserved_quantities,
            reserved_cash_delta=reserved_cash_delta,
            estimated_transaction_cost=estimated_cost,
        )
        self._proposals[proposal.proposal_id] = proposal
        self._decisions[proposal.proposal_id] = decision
        self._event_bus.publish(
            Event(EventType.RISK_DECISION, decision, occurred_at=decision.timestamp)
        )
        if not decision.approved:
            return decision, None

        if decision.reference_price is None or decision.estimated_transaction_cost is None:
            raise OrderManagementError("approved decision is missing reservation diagnostics")
        order = Order(
            id=proposal.proposal_id,
            strategy_id=proposal.strategy_id,
            symbol=proposal.symbol,
            side=proposal.side,
            order_type=proposal.order_type,
            quantity=proposal.quantity,
            created_at=proposal.signal_timestamp,
        )
        with localcontext(OMS_CONTEXT):
            notional = proposal.quantity * decision.reference_price
            cash_delta = (
                -notional if proposal.side is OrderSide.BUY else notional
            ) - decision.estimated_transaction_cost
        reservation = _Reservation(
            proposal_id=proposal.proposal_id,
            order_id=order.id,
            symbol=order.symbol,
            signed_quantity=(order.quantity if order.side is OrderSide.BUY else -order.quantity),
            cash_delta=cash_delta,
        )
        self._orders[order.id] = order
        self._order_by_proposal[proposal.proposal_id] = order.id
        self._reservations[order.id] = reservation
        self._event_bus.publish(Event(EventType.ORDER_CREATED, order, occurred_at=order.created_at))
        try:
            submitted = self._broker.submit(order)
        except Exception:
            if order.id in self._reservations:
                self.release_reservation(order.id)
            raise
        return decision, submitted

    def release_reservation(self, order_id: UUID) -> None:
        if order_id not in self._reservations:
            raise ReservationError(f"no active reservation for order: {order_id}")
        del self._reservations[order_id]

    def reset(self) -> None:
        self._proposals.clear()
        self._decisions.clear()
        self._orders.clear()
        self._order_by_proposal.clear()
        self._reservations.clear()

    def _reservation_state(self) -> tuple[dict[str, Decimal], Decimal]:
        quantities: dict[str, Decimal] = {}
        cash_delta = ZERO
        with localcontext(OMS_CONTEXT):
            for reservation in self._reservations.values():
                quantities[reservation.symbol] = (
                    quantities.get(reservation.symbol, ZERO) + reservation.signed_quantity
                )
                cash_delta += reservation.cash_delta
        return quantities, cash_delta

    def _on_proposal(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, OrderProposal):
            raise TypeError("ORDER_PROPOSAL event payload must be an OrderProposal")
        self.process_proposal(event.payload)

    def _on_order_state(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Order):
            raise TypeError(f"{event.event_type} event payload must be an Order")
        order = event.payload
        current = self._orders.get(order.id)
        if current is None:
            raise OrderManagementError(f"order is not registered with OMS: {order.id}")
        expected = transition_order(current, order.status)
        if expected != order:
            raise OrderManagementError(f"order state event changed immutable intent: {order.id}")
        self._orders[order.id] = order
        if order.status is OrderStatus.REJECTED:
            self.release_reservation(order.id)

    def _on_fill(self, event: Event[Any]) -> None:
        if not isinstance(event.payload, Fill):
            raise TypeError("ORDER_FILLED event payload must be a Fill")
        fill = event.payload
        order = self._orders.get(fill.order_id)
        if order is None:
            raise OrderManagementError(f"fill references an unknown OMS order: {fill.order_id}")
        self._orders[order.id] = transition_order(order, OrderStatus.FILLED)
        self.release_reservation(order.id)
