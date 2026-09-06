from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.backtest import BacktestConfig
from app.data.providers import CSVDataProvider
from app.domain.market import Bar
from app.domain.risk import RiskConfig, RiskReasonCode
from app.domain.trading import Order, OrderSide, OrderStatus, OrderType
from app.event import EventBus
from app.execution import FixedBasisPointSlippage, FixedCommission
from app.paper.hub import PaperEventHub
from app.paper.models import PaperSessionStatus, require_transition
from app.paper.runtime import (
    PaperBroker,
    PaperTradingRuntime,
    ReplayMarketDataProvider,
    ReplayProviderError,
)
from app.strategies import MovingAverageCrossoverStrategy

FIXTURES = Path(__file__).parents[2] / "data" / "fixtures"
START = datetime(2024, 1, 1, tzinfo=UTC)


def bar(day: int, price: str) -> Bar:
    value = Decimal(price)
    return Bar(
        symbol="AAPL",
        timestamp=START + timedelta(days=day),
        open=value,
        high=value,
        low=value,
        close=value,
        volume=Decimal("100"),
    )


async def test_replay_provider_subscribe_stop_and_future_protection() -> None:
    bars = (bar(0, "100"), bar(1, "101"), bar(2, "102"))
    provider = ReplayMarketDataProvider(bars, 0)
    received: list[Bar] = []
    provider.subscribe("AAPL")
    await provider.start(lambda item: _append(received, item))
    assert received == list(bars)
    assert not provider.running

    provider.unsubscribe("AAPL")
    received.clear()
    await provider.start(lambda item: _append(received, item))
    assert received == []
    with pytest.raises(ReplayProviderError, match="chronological"):
        ReplayMarketDataProvider((bars[1], bars[0]))


async def _append(target: list[Bar], item: Bar) -> None:
    target.append(item)


def test_paper_broker_is_local_next_bar_and_explicitly_rejects_limit_orders() -> None:
    broker = PaperBroker(EventBus(), FixedCommission(), FixedBasisPointSlippage())
    market = Order(
        strategy_id="strategy",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("1.000000000000000001"),
        created_at=START,
    )
    assert broker.submit(market).status is OrderStatus.ACCEPTED
    assert broker.execute_pending(bar(0, "100")) == ()
    fill = broker.execute_pending(bar(1, "101"))[0]
    assert fill.price == Decimal("101")
    assert fill.quantity == Decimal("1.000000000000000001")
    assert fill.timestamp == START + timedelta(days=1)

    limit = Order(
        strategy_id="strategy",
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("1"),
        price=Decimal("99"),
        created_at=START + timedelta(days=2),
    )
    assert broker.submit(limit).status is OrderStatus.REJECTED


async def test_paper_runtime_is_deterministic_and_updates_existing_portfolio() -> None:
    bars = CSVDataProvider(FIXTURES).get_historical_bars("AAPL")

    async def execute() -> tuple[list[dict[str, Any]], Decimal, Decimal]:
        runtime = PaperTradingRuntime(
            (MovingAverageCrossoverStrategy("moving_average_crossover:AAPL", "AAPL", 2, 3),),
            BacktestConfig(
                initial_cash=Decimal("105.052500000000000001"),
                default_order_quantity=Decimal("0.000000000000000001"),
            ),
        )
        records: list[dict[str, Any]] = []
        for item in bars:
            delta = await runtime.process_bar(item)
            records.append(
                {
                    "bar": item.timestamp,
                    "signals": delta.signals,
                    "decisions": delta.decisions,
                    "orders": delta.orders,
                    "fills": delta.fills,
                    "snapshot": delta.snapshot,
                }
            )
        latest = runtime.portfolio.latest_snapshot
        assert latest is not None
        return records, runtime.portfolio.cash, latest.equity

    first = await execute()
    second = await execute()
    assert first == second
    assert sum(len(item["signals"]) for item in first[0]) == 1
    assert sum(len(item["fills"]) for item in first[0]) == 1
    assert first[1] != Decimal("105.052500000000000001")


async def test_risk_rejection_never_reaches_paper_broker_or_portfolio_fill() -> None:
    runtime = PaperTradingRuntime(
        (MovingAverageCrossoverStrategy("moving_average_crossover:AAPL", "AAPL", 2, 3),),
        BacktestConfig(
            initial_cash=Decimal("100000"),
            default_order_quantity=Decimal("10"),
            risk=RiskConfig(max_order_notional=Decimal("1")),
        ),
    )
    bars = CSVDataProvider(FIXTURES).get_historical_bars("AAPL")
    decisions = []
    for item in bars:
        decisions.extend((await runtime.process_bar(item)).decisions)
    assert len(decisions) == 1
    assert decisions[0].reason_code is RiskReasonCode.ORDER_NOTIONAL_LIMIT
    assert runtime.broker.orders == ()
    assert runtime.broker.fills == ()


def test_session_lifecycle_rejects_illegal_transitions() -> None:
    require_transition(PaperSessionStatus.CREATED, PaperSessionStatus.STARTING)
    require_transition(PaperSessionStatus.RUNNING, PaperSessionStatus.STOPPING)
    require_transition(PaperSessionStatus.STOPPING, PaperSessionStatus.STOPPED)
    with pytest.raises(ValueError, match="invalid paper session transition"):
        require_transition(PaperSessionStatus.STOPPED, PaperSessionStatus.RUNNING)


async def test_websocket_hub_bounds_slow_consumers_and_cleans_disconnects() -> None:
    from uuid import uuid4

    session_id = uuid4()
    hub = PaperEventHub(queue_size=2)
    event = {
        "sequence": 1,
        "type": "market.bar",
        "occurred_at": "2024-01-01T00:00:00+00:00",
        "payload": {},
    }
    async with hub.subscribe(session_id) as queue:
        assert hub.subscriber_count(session_id) == 1
        hub.publish(session_id, event)
        hub.publish(session_id, {**event, "sequence": 2})
        hub.publish(session_id, {**event, "sequence": 3})
        assert (await queue.get())["type"] == "stream.resync_required"
        assert (await queue.get())["sequence"] == 3
    assert hub.subscriber_count(session_id) == 0
