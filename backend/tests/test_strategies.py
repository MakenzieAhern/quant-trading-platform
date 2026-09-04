from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.domain.market import Bar
from app.domain.trading import Signal, SignalType
from app.strategies import (
    BarOrderError,
    MovingAverageCrossoverStrategy,
    RSIMeanReversionStrategy,
)

START = datetime(2024, 1, 1, tzinfo=UTC)


def make_bar(day: int, close: str, symbol: str = "AAPL") -> Bar:
    price = Decimal(close)
    return Bar(
        symbol=symbol,
        timestamp=START + timedelta(days=day),
        open=price,
        high=price,
        low=price,
        close=price,
        volume=Decimal(100),
    )


def run_strategy(
    strategy: MovingAverageCrossoverStrategy | RSIMeanReversionStrategy,
    closes: list[str],
) -> tuple[Signal, ...]:
    return tuple(
        signal
        for day, close in enumerate(closes)
        for signal in strategy.on_bar(make_bar(day, close))
    )


def test_moving_average_strategy_emits_only_true_crossovers() -> None:
    strategy = MovingAverageCrossoverStrategy("ma", "AAPL", 2, 3)

    signals = run_strategy(strategy, ["3", "2", "1", "2", "4", "5", "1"])

    assert [signal.signal_type for signal in signals] == [SignalType.BUY, SignalType.SELL]
    assert [signal.timestamp for signal in signals] == [
        START + timedelta(days=4),
        START + timedelta(days=6),
    ]
    assert all(signal.strategy_id == "ma" and signal.symbol == "AAPL" for signal in signals)


@pytest.mark.parametrize(
    ("closes", "expected"),
    [
        (["1", "1", "1", "2"], SignalType.BUY),
        (["2", "2", "2", "1"], SignalType.SELL),
    ],
)
def test_moving_average_crossover_includes_previous_equality(
    closes: list[str], expected: SignalType
) -> None:
    strategy = MovingAverageCrossoverStrategy("ma", "AAPL", 2, 3)

    signals = run_strategy(strategy, closes)

    assert [signal.signal_type for signal in signals] == [expected]
    assert signals[0].timestamp == START + timedelta(days=3)


def test_rsi_strategy_emits_only_threshold_reentry_crossings() -> None:
    strategy = RSIMeanReversionStrategy(
        "rsi",
        "AAPL",
        rsi_period=2,
        oversold=Decimal(30),
        overbought=Decimal(70),
    )

    signals = run_strategy(strategy, ["4", "3", "2", "1", "2", "3", "4", "3"])

    assert [signal.signal_type for signal in signals] == [SignalType.BUY, SignalType.SELL]
    assert [signal.timestamp for signal in signals] == [
        START + timedelta(days=4),
        START + timedelta(days=7),
    ]


def test_strategy_rejects_duplicate_and_out_of_order_bars_before_mutation() -> None:
    control = MovingAverageCrossoverStrategy("control", "AAPL", 2, 3)
    reviewed = MovingAverageCrossoverStrategy("reviewed", "AAPL", 2, 3)
    first_bar = make_bar(1, "3")
    control.on_bar(first_bar)
    reviewed.on_bar(first_bar)

    with pytest.raises(BarOrderError, match="strictly later"):
        reviewed.on_bar(make_bar(1, "100"))
    with pytest.raises(BarOrderError, match="strictly later"):
        reviewed.on_bar(make_bar(0, "100"))

    remaining_bars = [make_bar(day, close) for day, close in enumerate(["2", "1", "2", "4"], 2)]
    control_signals = tuple(signal for bar in remaining_bars for signal in control.on_bar(bar))
    reviewed_signals = tuple(signal for bar in remaining_bars for signal in reviewed.on_bar(bar))

    assert [signal.signal_type for signal in reviewed_signals] == [SignalType.BUY]
    assert [signal.signal_type for signal in reviewed_signals] == [
        signal.signal_type for signal in control_signals
    ]
    assert [signal.timestamp for signal in reviewed_signals] == [
        signal.timestamp for signal in control_signals
    ]


def test_single_symbol_strategy_rejects_direct_cross_symbol_input() -> None:
    strategy = MovingAverageCrossoverStrategy("ma", "AAPL", 2, 3)
    with pytest.raises(ValueError, match="does not support MSFT"):
        strategy.on_bar(make_bar(0, "3", symbol="MSFT"))


def test_reset_replays_identical_signals() -> None:
    strategy = MovingAverageCrossoverStrategy("ma", "AAPL", 2, 3)
    closes = ["3", "2", "1", "2", "4", "5", "1"]
    first_run = run_strategy(strategy, closes)

    strategy.reset()
    second_run = run_strategy(strategy, closes)

    assert second_run == first_run


def test_future_bars_cannot_change_prior_decisions() -> None:
    strategy = MovingAverageCrossoverStrategy("ma", "AAPL", 2, 3)
    prefix_signals = run_strategy(strategy, ["3", "2", "1", "2", "4"])
    recorded_prefix = tuple(prefix_signals)

    future_signals = tuple(
        signal
        for day, close in enumerate(["5", "1"], start=5)
        for signal in strategy.on_bar(make_bar(day, close))
    )

    assert prefix_signals == recorded_prefix
    assert [signal.signal_type for signal in prefix_signals] == [SignalType.BUY]
    assert prefix_signals[0].timestamp == START + timedelta(days=4)
    assert [signal.signal_type for signal in future_signals] == [SignalType.SELL]


def test_strategy_parameters_are_validated() -> None:
    with pytest.raises(ValueError, match="short_window"):
        MovingAverageCrossoverStrategy("ma", "AAPL", 0, 3)
    with pytest.raises(ValueError, match="less than"):
        MovingAverageCrossoverStrategy("ma", "AAPL", 3, 3)
    with pytest.raises(ValueError, match="rsi_period"):
        RSIMeanReversionStrategy("rsi", "AAPL", 0, Decimal(30), Decimal(70))
    with pytest.raises(ValueError, match="thresholds"):
        RSIMeanReversionStrategy("rsi", "AAPL", 2, Decimal(70), Decimal(30))
    with pytest.raises(TypeError, match="Decimal"):
        RSIMeanReversionStrategy("rsi", "AAPL", 2, 30, 70)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite"):
        RSIMeanReversionStrategy("rsi", "AAPL", 2, Decimal("NaN"), Decimal(70))


def test_strategy_exposes_immutable_parameter_metadata() -> None:
    strategy = MovingAverageCrossoverStrategy("ma", "aapl", 2, 3)

    assert strategy.symbol == "AAPL"
    assert strategy.configuration == {"short_window": 2, "long_window": 3}
    with pytest.raises(TypeError):
        strategy.configuration["short_window"] = 1  # type: ignore[index]
