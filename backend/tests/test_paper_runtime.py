from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from app.backtest import BacktestConfig, BacktestEngine
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
from app.strategies import MovingAverageCrossoverStrategy, RSIMeanReversionStrategy

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


def symbol_bar(symbol: str, day: int, price: str) -> Bar:
    return bar(day, price).model_copy(update={"symbol": symbol})


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


async def test_extreme_future_bars_cannot_change_already_produced_results() -> None:
    fixture = CSVDataProvider(FIXTURES).get_historical_bars("AAPL")
    prefix = fixture[:4]
    extreme_future = bar(20, "999999999999999999")

    async def execute(items: tuple[Bar, ...]) -> tuple[object, ...]:
        runtime = PaperTradingRuntime(
            (MovingAverageCrossoverStrategy("future-audit", "AAPL", 2, 3),),
            BacktestConfig(initial_cash=Decimal("100000"), default_order_quantity=Decimal("10")),
        )
        return tuple([await runtime.process_bar(item) for item in items])

    before = await execute(prefix)
    with_future = await execute((*prefix, extreme_future))
    assert with_future[: len(prefix)] == before


async def test_pending_orders_are_cancelled_once_and_release_reservations() -> None:
    runtime = PaperTradingRuntime(
        (MovingAverageCrossoverStrategy("cancel-audit", "AAPL", 2, 3),),
        BacktestConfig(initial_cash=Decimal("100000"), default_order_quantity=Decimal("10")),
    )
    fixture = CSVDataProvider(FIXTURES).get_historical_bars("AAPL")
    next_bar: Bar | None = None
    for index, item in enumerate(fixture):
        await runtime.process_bar(item)
        if runtime.broker.pending_orders:
            next_bar = fixture[index + 1]
            break

    assert runtime.order_manager.active_reservation_count == 1
    cancelled = runtime.cancel_pending_orders()
    assert len(cancelled) == 1
    assert cancelled[0].status is OrderStatus.CANCELLED
    assert runtime.order_manager.active_reservation_count == 0
    assert runtime.cancel_pending_orders() == ()
    assert next_bar is not None
    delta = await runtime.process_bar(next_bar)
    assert delta.fills == ()
    assert runtime.broker.fills == ()


async def test_duplicate_market_event_cannot_duplicate_fill_or_accounting() -> None:
    runtime = PaperTradingRuntime(
        (MovingAverageCrossoverStrategy("exactly-once", "AAPL", 2, 3),),
        BacktestConfig(initial_cash=Decimal("100000"), default_order_quantity=Decimal("10")),
    )
    fixture = CSVDataProvider(FIXTURES).get_historical_bars("AAPL")
    for item in fixture:
        await runtime.process_bar(item)
    cash = runtime.portfolio.cash
    position = runtime.portfolio.positions
    assert len(runtime.broker.fills) == 1

    with pytest.raises(ReplayProviderError, match="chronological"):
        await runtime.process_bar(fixture[-1])
    assert len(runtime.broker.fills) == 1
    assert runtime.portfolio.cash == cash
    assert runtime.portfolio.positions == position


async def test_isolated_symbols_strategies_and_failures_do_not_cross_sessions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = PaperTradingRuntime(
        (MovingAverageCrossoverStrategy("first", "AAPL", 2, 3),),
        BacktestConfig(
            initial_cash=Decimal("1000"),
            default_order_quantity=Decimal("1"),
            risk=RiskConfig(max_order_notional=Decimal("500")),
        ),
    )
    second = PaperTradingRuntime(
        (RSIMeanReversionStrategy("second", "MSFT", 2, Decimal("30"), Decimal("70")),),
        BacktestConfig(initial_cash=Decimal("2000"), default_order_quantity=Decimal("2")),
    )
    await first.process_bar(symbol_bar("AAPL", 0, "100"))
    await second.process_bar(symbol_bar("MSFT", 0, "50"))
    assert first.portfolio.cash == Decimal("1000")
    assert second.portfolio.cash == Decimal("2000")
    assert first.portfolio.marks == {"AAPL": Decimal("100")}
    assert second.portfolio.marks == {"MSFT": Decimal("50")}

    def fail(_item: Bar) -> tuple[()]:
        raise RuntimeError("isolated broker failure")

    monkeypatch.setattr(first.broker, "execute_pending", fail)
    with pytest.raises(RuntimeError, match="isolated broker failure"):
        await first.process_bar(symbol_bar("AAPL", 1, "101"))
    healthy = await second.process_bar(symbol_bar("MSFT", 1, "51"))
    assert healthy.snapshot.cash == Decimal("2000")
    assert second.broker.orders == second.broker.fills == ()


async def test_paper_replay_matches_backtest_financial_and_strategy_contracts() -> None:
    provider = CSVDataProvider(FIXTURES)
    bars = provider.get_historical_bars("AAPL")
    config = BacktestConfig(
        initial_cash=Decimal("100000.052500000000000001"),
        default_order_quantity=Decimal("10"),
        risk=RiskConfig(enforce_buying_power=True),
    )
    backtest = BacktestEngine(
        provider,
        (MovingAverageCrossoverStrategy("parity", "AAPL", 2, 3),),
        config,
    ).run("AAPL")
    paper = PaperTradingRuntime(
        (MovingAverageCrossoverStrategy("parity", "AAPL", 2, 3),),
        config,
    )
    for item in bars:
        await paper.process_bar(item)

    assert tuple(paper.portfolio.snapshots) == backtest.portfolio_snapshots
    assert paper.portfolio.cash == backtest.portfolio_snapshots[-1].cash
    assert [fill.model_dump(exclude={"order_id"}) for fill in paper.broker.fills] == [
        fill.model_dump(exclude={"order_id"}) for fill in backtest.fills
    ]
    assert [order.model_dump(exclude={"id"}) for order in paper.order_manager.orders] == [
        order.model_dump(exclude={"id"}) for order in backtest.orders
    ]


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
