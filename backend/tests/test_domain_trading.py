from datetime import UTC, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.trading import Order, OrderSide, OrderStatus, OrderType


def test_limit_order_requires_price() -> None:
    with pytest.raises(ValidationError, match="limit orders require a price"):
        Order(
            strategy_id="strategy",
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("10"),
            created_at=datetime(2024, 1, 2, tzinfo=UTC),
        )


def test_order_defaults_to_created() -> None:
    order = Order(
        strategy_id="strategy",
        symbol="aapl",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        created_at=datetime(2024, 1, 2, tzinfo=UTC),
    )
    assert order.symbol == "AAPL"
    assert order.status is OrderStatus.CREATED
