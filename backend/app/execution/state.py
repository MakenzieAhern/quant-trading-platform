from app.domain.trading import Order, OrderStatus


class InvalidOrderTransitionError(ValueError):
    """Raised when an order transition is outside the Phase 4 state machine."""


ALLOWED_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset({OrderStatus.SUBMITTED}),
    OrderStatus.SUBMITTED: frozenset({OrderStatus.ACCEPTED, OrderStatus.REJECTED}),
    OrderStatus.ACCEPTED: frozenset({OrderStatus.FILLED}),
}


def transition_order(order: Order, target: OrderStatus) -> Order:
    """Return a new immutable Order after validating its state transition."""
    if target not in ALLOWED_TRANSITIONS.get(order.status, frozenset()):
        raise InvalidOrderTransitionError(
            f"invalid order transition: {order.status.value} -> {target.value}"
        )
    return Order.model_validate({**order.model_dump(), "status": target})
