from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta
from decimal import Decimal

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
from app.domain.trading import OrderStatus, Signal, SignalType
from app.event import EventBus, EventType
from app.execution import FixedBasisPointSlippage, FixedCommission
from app.strategies import BaseStrategy

START = datetime(2024, 1, 1, tzinfo=UTC)


def make_bar(day: int, open_price: str, close_price: str, symbol: str = "AAPL") -> Bar:
    open_value = Decimal(open_price)
    close_value = Decimal(close_price)
    return Bar(
        symbol=symbol,
        timestamp=START + timedelta(days=day),
        open=open_value,
        high=max(open_value, close_value) + Decimal(1),
        low=min(open_value, close_value) - Decimal(1),
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
    assert [fill.timestamp for fill in result.fills] == [
        bars[2].timestamp,
        bars[4].timestamp,
    ]
    assert [fill.price for fill in result.fills] == [
        Decimal("105.0525"),
        Decimal("109.9450"),
    ]
    assert [fill.commission for fill in result.fills] == [Decimal(1), Decimal(1)]
    assert all(order.status is OrderStatus.FILLED for order in result.orders)
    assert result.start_time == bars[0].timestamp
    assert result.end_time == bars[-1].timestamp


def test_per_bar_events_execute_old_orders_before_current_market_data() -> None:
    bars = manual_bars()[:3]
    bus = EventBus()
    observed: list[EventType] = []
    for event_type in (
        EventType.MARKET_DATA,
        EventType.SIGNAL,
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
        EventType.ORDER_CREATED,
        EventType.ORDER_SUBMITTED,
        EventType.ORDER_ACCEPTED,
        EventType.ORDER_FILLED,
        EventType.MARKET_DATA,
    ]


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


def test_appending_future_bars_does_not_change_completed_history() -> None:
    provider = StubProvider(manual_bars()[:3])
    engine = make_engine(provider)
    prefix = engine.run("AAPL")

    provider.bars.extend(manual_bars()[3:])
    complete = engine.run("AAPL")

    assert complete.signals[:1] == prefix.signals
    assert complete.orders[:1] == prefix.orders
    assert complete.fills[:1] == prefix.fills


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
    assert result.signals == result.orders == result.fills == ()
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
