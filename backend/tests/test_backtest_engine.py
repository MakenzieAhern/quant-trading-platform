from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest

from app.backtest import (
    BacktestConfig,
    BacktestDataError,
    BacktestEngine,
    BacktestResult,
    DuplicateSignalError,
)
from app.data.providers import Timeframe
from app.domain.market import Bar
from app.domain.risk import RiskConfig, RiskReasonCode
from app.domain.trading import OrderSide, OrderStatus, Signal, SignalType
from app.event import EventBus, EventType
from app.execution import FixedBasisPointSlippage, FixedCommission
from app.strategies import BaseStrategy, MovingAverageCrossoverStrategy

START = datetime(2024, 1, 1, tzinfo=UTC)


def make_bar(day: int, open_price: str, close_price: str, symbol: str = "AAPL") -> Bar:
    open_value = Decimal(open_price)
    close_value = Decimal(close_price)
    return Bar(
        symbol=symbol,
        timestamp=START + timedelta(days=day),
        open=open_value,
        high=max(open_value, close_value) + Decimal(1),
        low=max(min(open_value, close_value) - Decimal(1), Decimal("0.01")),
        close=close_value,
        volume=Decimal(1000),
    )


class StubProvider:
    def __init__(self, bars: Sequence[Bar]) -> None:
        self.bars = list(bars)

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime | None = None,
        end: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> tuple[Bar, ...]:
        return tuple(self.bars)


class CurrentBarStrategy(BaseStrategy):
    """Test strategy whose intent depends only on the close just delivered."""

    def __init__(
        self,
        strategy_id: str,
        symbol: str,
        signals_by_close: Mapping[Decimal, SignalType],
    ) -> None:
        super().__init__(strategy_id, symbol, {})
        self._signals_by_close = dict(signals_by_close)

    def _process_bar(self, bar: Bar) -> tuple[Signal, ...]:
        signal_type = self._signals_by_close.get(bar.close)
        if signal_type is None:
            return ()
        return (
            Signal(
                strategy_id=self.strategy_id,
                symbol=bar.symbol,
                timestamp=bar.timestamp,
                signal_type=signal_type,
            ),
        )

    def _reset_state(self) -> None:
        pass


class DuplicateSignalStrategy(BaseStrategy):
    def __init__(self) -> None:
        super().__init__("duplicate", "AAPL", {})

    def _process_bar(self, bar: Bar) -> tuple[Signal, ...]:
        signal = Signal(
            strategy_id=self.strategy_id,
            symbol=bar.symbol,
            timestamp=bar.timestamp,
            signal_type=SignalType.BUY,
        )
        return (signal, signal)

    def _reset_state(self) -> None:
        pass


def manual_bars() -> list[Bar]:
    return [
        make_bar(0, "99", "100"),
        make_bar(1, "100", "90"),
        make_bar(2, "105", "100"),
        make_bar(3, "108", "110"),
        make_bar(4, "110", "100"),
    ]


def make_engine(
    provider: StubProvider,
    strategies: tuple[BaseStrategy, ...] | None = None,
    event_bus: EventBus | None = None,
    risk_config: RiskConfig | None = None,
) -> BacktestEngine:
    selected = strategies or (
        CurrentBarStrategy(
            "manual",
            "AAPL",
            {Decimal(90): SignalType.BUY, Decimal(110): SignalType.SELL},
        ),
    )
    return BacktestEngine(
        provider,
        selected,
        BacktestConfig(
            initial_cash=Decimal("10000"),
            default_order_quantity=Decimal(2),
            commission_model=FixedCommission(Decimal(1)),
            slippage_model=FixedBasisPointSlippage(Decimal(5)),
            risk=risk_config or RiskConfig(),
        ),
        event_bus,
    )


def test_manual_reference_backtest_uses_next_bar_open() -> None:
    bars = manual_bars()
    result = make_engine(StubProvider(bars)).run("AAPL")

    assert [signal.timestamp for signal in result.signals] == [
        bars[1].timestamp,
        bars[3].timestamp,
    ]
    assert [order.created_at for order in result.orders] == [
        bars[1].timestamp,
        bars[3].timestamp,
    ]
    assert [order.side for order in result.orders] == [OrderSide.BUY, OrderSide.SELL]
    assert [order.id for order in result.orders] == [
        UUID("f356a327-b7d7-568d-a23a-c52738c9bfa9"),
        UUID("5775c3a9-a6a0-551e-b9dd-79037e72aca5"),
    ]
    assert [proposal.proposal_id for proposal in result.order_proposals] == [
        order.id for order in result.orders
    ]
    assert all(decision.approved for decision in result.risk_decisions)
    assert all(order.quantity == Decimal(2) for order in result.orders)
    assert [fill.timestamp for fill in result.fills] == [
        bars[2].timestamp,
        bars[4].timestamp,
    ]
    assert all(
        fill.timestamp > signal.timestamp
        for signal, fill in zip(result.signals, result.fills, strict=True)
    )
    assert [fill.price for fill in result.fills] == [
        Decimal("105.0525"),
        Decimal("109.9450"),
    ]
    assert [fill.commission for fill in result.fills] == [Decimal(1), Decimal(1)]
    assert [fill.side for fill in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert all(order.status is OrderStatus.FILLED for order in result.orders)
    assert result.start_time == bars[0].timestamp
    assert result.end_time == bars[-1].timestamp
    assert [snapshot.equity for snapshot in result.portfolio_snapshots] == [
        Decimal("10000"),
        Decimal("10000"),
        Decimal("9988.8950"),
        Decimal("10008.8950"),
        Decimal("10007.7850"),
    ]
    assert result.portfolio_snapshots[2].cash == Decimal("9788.8950")
    assert result.portfolio_snapshots[2].unrealized_pnl == Decimal("-10.1050")
    assert result.portfolio_snapshots[-1].realized_pnl == Decimal("9.7850")
    assert result.portfolio_snapshots[-1].cumulative_commission == Decimal(2)
    assert result.performance_metrics.final_equity == Decimal("10007.7850")
    assert result.performance_metrics.total_return == Decimal("0.0007785")
    assert result.performance_metrics.total_commission == Decimal(2)
    assert result.performance_metrics.number_of_fills == 2


def test_per_bar_events_execute_old_orders_before_current_market_data() -> None:
    bars = manual_bars()[:3]
    bus = EventBus()
    observed: list[EventType] = []
    for event_type in (
        EventType.MARKET_DATA,
        EventType.SIGNAL,
        EventType.ORDER_PROPOSAL,
        EventType.RISK_DECISION,
        EventType.ORDER_CREATED,
        EventType.ORDER_SUBMITTED,
        EventType.ORDER_ACCEPTED,
        EventType.ORDER_FILLED,
    ):
        bus.subscribe(event_type, lambda event: observed.append(event.event_type))

    make_engine(StubProvider(bars), event_bus=bus).run("AAPL")

    assert observed == [
        EventType.MARKET_DATA,
        EventType.MARKET_DATA,
        EventType.SIGNAL,
        EventType.ORDER_PROPOSAL,
        EventType.RISK_DECISION,
        EventType.ORDER_CREATED,
        EventType.ORDER_SUBMITTED,
        EventType.ORDER_ACCEPTED,
        EventType.ORDER_FILLED,
        EventType.MARKET_DATA,
    ]


def test_portfolio_snapshot_precedes_strategy_signal_for_each_completed_bar() -> None:
    bars = manual_bars()[:3]
    bus = EventBus()
    observed: list[EventType] = []
    for event_type in (EventType.MARKET_DATA, EventType.PORTFOLIO_UPDATED, EventType.SIGNAL):
        bus.subscribe(event_type, lambda event: observed.append(event.event_type))

    make_engine(StubProvider(bars), event_bus=bus).run("AAPL")

    assert observed == [
        EventType.MARKET_DATA,
        EventType.PORTFOLIO_UPDATED,
        EventType.MARKET_DATA,
        EventType.PORTFOLIO_UPDATED,
        EventType.SIGNAL,
        EventType.MARKET_DATA,
        EventType.PORTFOLIO_UPDATED,
    ]


def test_real_crossover_strategy_signal_fills_at_following_open() -> None:
    closes = ["3", "2", "1", "2", "4", "5"]
    bars = [make_bar(day, "50" if day == 5 else close, close) for day, close in enumerate(closes)]
    strategy = MovingAverageCrossoverStrategy("ma", "AAPL", 2, 3)
    engine = BacktestEngine(
        StubProvider(bars),
        (strategy,),
        BacktestConfig(
            commission_model=FixedCommission(),
            slippage_model=FixedBasisPointSlippage(),
        ),
    )

    result = engine.run("AAPL")

    assert len(result.signals) == len(result.orders) == len(result.fills) == 1
    assert result.signals[0].timestamp == bars[4].timestamp
    assert result.orders[0].created_at == bars[4].timestamp
    assert result.fills[0].timestamp == bars[5].timestamp
    assert result.fills[0].price == Decimal(50)


def test_signal_on_final_bar_remains_accepted_without_invented_fill() -> None:
    bars = manual_bars()[:2]

    result = make_engine(StubProvider(bars)).run("AAPL")

    assert len(result.signals) == 1
    assert len(result.orders) == 1
    assert result.orders[0].status is OrderStatus.ACCEPTED
    assert result.fills == ()


def test_multiple_strategies_preserve_registration_order() -> None:
    bars = manual_bars()[:3]
    strategies = tuple(
        CurrentBarStrategy(name, "AAPL", {Decimal(90): SignalType.BUY})
        for name in ("first", "second")
    )

    result = make_engine(StubProvider(bars), strategies).run("AAPL")

    assert [signal.strategy_id for signal in result.signals] == ["first", "second"]
    assert [order.strategy_id for order in result.orders] == ["first", "second"]
    assert [fill.strategy_id for fill in result.fills] == ["first", "second"]
    assert [proposal.strategy_id for proposal in result.order_proposals] == [
        "first",
        "second",
    ]
    assert all(decision.approved for decision in result.risk_decisions)
    assert len({order.id for order in result.orders}) == len(result.orders)


def test_duplicate_signal_fails_instead_of_creating_a_second_order() -> None:
    engine = make_engine(
        StubProvider([make_bar(0, "100", "100")]),
        strategies=(DuplicateSignalStrategy(),),
    )

    with pytest.raises(DuplicateSignalError, match="duplicate signal"):
        engine.run("AAPL")


def test_repeated_run_is_exactly_reproducible() -> None:
    engine = make_engine(StubProvider(manual_bars()))

    first = engine.run("AAPL")
    second = engine.run("AAPL")

    assert second == first
    assert [order.id for order in second.orders] == [order.id for order in first.orders]


def test_appending_future_bars_does_not_change_completed_history() -> None:
    provider = StubProvider(manual_bars()[:3])
    engine = make_engine(provider)
    prefix = engine.run("AAPL")

    provider.bars.extend(manual_bars()[3:])
    complete = engine.run("AAPL")

    assert complete.signals[:1] == prefix.signals
    assert complete.orders[:1] == prefix.orders
    assert complete.fills[:1] == prefix.fills
    assert complete.order_proposals[:1] == prefix.order_proposals
    assert complete.risk_decisions[:1] == prefix.risk_decisions
    assert complete.portfolio_snapshots[:3] == prefix.portfolio_snapshots
    assert complete.equity_curve[:3] == prefix.equity_curve


@pytest.mark.parametrize(
    "bars",
    [
        [make_bar(1, "100", "100"), make_bar(0, "100", "100")],
        [make_bar(0, "100", "100"), make_bar(0, "101", "101")],
    ],
)
def test_backtest_rejects_non_chronological_history_before_running(bars: list[Bar]) -> None:
    engine = make_engine(StubProvider(bars))

    with pytest.raises(BacktestDataError, match="strictly chronological"):
        engine.run("AAPL")

    assert engine.clock.current_time is None


def test_backtest_rejects_provider_symbol_mismatch() -> None:
    engine = make_engine(StubProvider([make_bar(0, "100", "100", symbol="MSFT")]))
    with pytest.raises(BacktestDataError, match="returned MSFT"):
        engine.run("AAPL")


def test_empty_history_returns_typed_empty_result() -> None:
    engine = make_engine(StubProvider([]))

    result = engine.run("AAPL")

    assert isinstance(result, BacktestResult)
    assert result.signals == result.order_proposals == result.risk_decisions == ()
    assert result.orders == result.fills == ()
    assert result.portfolio_snapshots == result.equity_curve == ()
    assert result.performance_metrics.final_equity == Decimal("10000")
    assert result.performance_metrics.total_return == Decimal(0)
    assert result.start_time is result.end_time is None


def test_backtest_config_requires_decimal_positive_values() -> None:
    with pytest.raises(ValueError, match="initial_cash"):
        BacktestConfig(initial_cash=Decimal(0))
    with pytest.raises(ValueError, match="default_order_quantity"):
        BacktestConfig(default_order_quantity=Decimal("-1"))
    with pytest.raises(TypeError, match="Decimal"):
        BacktestConfig(default_order_quantity=1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="CommissionModel"):
        BacktestConfig(commission_model=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="SlippageModel"):
        BacktestConfig(slippage_model=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="periods_per_year"):
        BacktestConfig(periods_per_year=0)
    with pytest.raises(TypeError, match="risk_free_rate_per_period"):
        BacktestConfig(risk_free_rate_per_period=0)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="RiskConfig"):
        BacktestConfig(risk=object())  # type: ignore[arg-type]


def test_risk_rejection_creates_no_broker_order() -> None:
    result = make_engine(
        StubProvider(manual_bars()[:2]),
        risk_config=RiskConfig(max_order_notional=Decimal(100)),
    ).run("AAPL")

    assert len(result.signals) == len(result.order_proposals) == 1
    assert result.risk_decisions[0].reason_code is RiskReasonCode.ORDER_NOTIONAL_LIMIT
    assert result.risk_decisions[0].reference_price == Decimal(90)
    assert result.orders == result.fills == ()


def test_risk_uses_completed_signal_bar_close_not_next_bar_open() -> None:
    bars = manual_bars()[:3]
    result = make_engine(StubProvider(bars)).run("AAPL")

    assert result.risk_decisions[0].reference_price == bars[1].close == Decimal(90)
    assert result.fills[0].price == Decimal("105.0525")
    assert result.fills[0].timestamp == bars[2].timestamp


def test_same_bar_strategy_order_uses_sequential_risk_reservations() -> None:
    bars = manual_bars()[:3]
    strategies = tuple(
        CurrentBarStrategy(name, "AAPL", {Decimal(90): SignalType.BUY})
        for name in ("first", "second")
    )
    result = make_engine(
        StubProvider(bars),
        strategies,
        risk_config=RiskConfig(max_position_quantity=Decimal(3)),
    ).run("AAPL")

    assert [proposal.strategy_id for proposal in result.order_proposals] == [
        "first",
        "second",
    ]
    assert [decision.reason_code for decision in result.risk_decisions] == [
        RiskReasonCode.APPROVED,
        RiskReasonCode.POSITION_LIMIT,
    ]
    assert [order.strategy_id for order in result.orders] == ["first"]
    assert [fill.strategy_id for fill in result.fills] == ["first"]
