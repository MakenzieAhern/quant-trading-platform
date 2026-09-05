from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.market import Bar
from app.domain.trading import Fill, OrderSide
from app.event import EventBus
from app.portfolio import PortfolioEngine, PortfolioError

START = datetime(2024, 1, 1, tzinfo=UTC)


def make_fill(
    sequence: int,
    side: OrderSide,
    quantity: str,
    price: str,
    commission: str = "0",
    symbol: str = "AAPL",
) -> Fill:
    return Fill(
        order_id=UUID(int=sequence),
        strategy_id="manual",
        symbol=symbol,
        side=side,
        quantity=Decimal(quantity),
        price=Decimal(price),
        commission=Decimal(commission),
        timestamp=START + timedelta(days=sequence),
    )


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


def test_long_cash_marking_and_realized_pnl_reference() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(1000))

    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "2", "100", "1"))
    open_snapshot = portfolio.mark_to_market(make_bar(1, "110"))

    assert open_snapshot.cash == Decimal(799)
    assert open_snapshot.market_value == Decimal(220)
    assert open_snapshot.equity == Decimal(1019)
    assert open_snapshot.unrealized_pnl == Decimal(20)
    assert open_snapshot.realized_pnl == Decimal(0)
    assert open_snapshot.cumulative_commission == Decimal(1)
    assert open_snapshot.positions[0].quantity == Decimal(2)
    assert open_snapshot.positions[0].average_price == Decimal(100)

    portfolio.apply_fill(make_fill(2, OrderSide.SELL, "2", "120", "1"))
    closed_snapshot = portfolio.mark_to_market(make_bar(2, "120"))

    assert closed_snapshot.cash == Decimal(1038)
    assert closed_snapshot.market_value == Decimal(0)
    assert closed_snapshot.equity == Decimal(1038)
    assert closed_snapshot.realized_pnl == Decimal(40)
    assert closed_snapshot.unrealized_pnl == Decimal(0)
    assert closed_snapshot.cumulative_commission == Decimal(2)


def test_short_cash_market_value_and_covering_reference() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(1000))

    portfolio.apply_fill(make_fill(1, OrderSide.SELL, "10", "100", "1"))
    short_snapshot = portfolio.mark_to_market(make_bar(1, "90"))

    assert short_snapshot.cash == Decimal(1999)
    assert short_snapshot.positions[0].quantity == Decimal(-10)
    assert short_snapshot.market_value == Decimal(-900)
    assert short_snapshot.unrealized_pnl == Decimal(100)
    assert short_snapshot.equity == Decimal(1099)

    portfolio.apply_fill(make_fill(2, OrderSide.BUY, "4", "90", "1"))
    reduced_snapshot = portfolio.mark_to_market(make_bar(2, "90"))
    assert reduced_snapshot.positions[0].quantity == Decimal(-6)
    assert reduced_snapshot.positions[0].average_price == Decimal(100)
    assert reduced_snapshot.realized_pnl == Decimal(40)
    assert reduced_snapshot.equity == Decimal(1098)

    portfolio.apply_fill(make_fill(3, OrderSide.BUY, "6", "80", "1"))
    closed_snapshot = portfolio.mark_to_market(make_bar(3, "80"))
    assert closed_snapshot.cash == Decimal(1157)
    assert closed_snapshot.positions[0].quantity == Decimal(0)
    assert closed_snapshot.realized_pnl == Decimal(160)
    assert closed_snapshot.equity == Decimal(1157)
    assert closed_snapshot.cumulative_commission == Decimal(3)


def test_same_direction_fills_use_weighted_average_cost() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(1000))

    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "10", "100"))
    position = portfolio.apply_fill(make_fill(2, OrderSide.BUY, "10", "120"))

    assert position.quantity == Decimal(20)
    assert position.average_price == Decimal(110)
    assert position.realized_pnl == Decimal(0)
    assert portfolio.cash == Decimal(-1200)


def test_same_direction_short_fills_use_absolute_weighted_average_cost() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(3000))

    portfolio.apply_fill(make_fill(1, OrderSide.SELL, "10", "100"))
    position = portfolio.apply_fill(make_fill(2, OrderSide.SELL, "10", "120"))

    assert position.quantity == Decimal(-20)
    assert position.average_price == Decimal(110)
    assert position.realized_pnl == Decimal(0)
    assert portfolio.cash == Decimal(5200)


def test_long_reduction_preserves_cost_basis_and_realizes_price_pnl() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(2000))
    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "10", "100"))

    position = portfolio.apply_fill(make_fill(2, OrderSide.SELL, "4", "110"))

    assert position.quantity == Decimal(6)
    assert position.average_price == Decimal(100)
    assert position.realized_pnl == Decimal(40)


@pytest.mark.parametrize(
    ("opening_side", "reversing_side", "opening_quantity", "reversing_quantity", "expected"),
    [
        (OrderSide.BUY, OrderSide.SELL, "5", "8", (Decimal(-3), Decimal(110), Decimal(50))),
        (OrderSide.SELL, OrderSide.BUY, "5", "8", (Decimal(3), Decimal(90), Decimal(50))),
    ],
)
def test_position_reversal_resets_cost_basis(
    opening_side: OrderSide,
    reversing_side: OrderSide,
    opening_quantity: str,
    reversing_quantity: str,
    expected: tuple[Decimal, Decimal, Decimal],
) -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(1000))
    opening_price = "100"
    reversing_price = "110" if opening_side is OrderSide.BUY else "90"

    portfolio.apply_fill(make_fill(1, opening_side, opening_quantity, opening_price))
    position = portfolio.apply_fill(
        make_fill(2, reversing_side, reversing_quantity, reversing_price)
    )

    assert (position.quantity, position.average_price, position.realized_pnl) == expected


def test_multi_symbol_marks_are_retained_independently() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(5000))
    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "2", "100", symbol="AAPL"))
    portfolio.apply_fill(make_fill(1, OrderSide.SELL, "3", "50", symbol="MSFT"))

    portfolio.mark_to_market(make_bar(1, "110", "AAPL"))
    both_marked = portfolio.mark_to_market(make_bar(1, "40", "MSFT"))
    aapl_updated = portfolio.mark_to_market(make_bar(2, "120", "AAPL"))

    assert [(position.symbol, position.market_price) for position in both_marked.positions] == [
        ("AAPL", Decimal(110)),
        ("MSFT", Decimal(40)),
    ]
    assert [(position.symbol, position.market_price) for position in aapl_updated.positions] == [
        ("AAPL", Decimal(120)),
        ("MSFT", Decimal(40)),
    ]
    assert aapl_updated.market_value == Decimal(120)


@pytest.mark.parametrize(
    ("side", "mark"),
    [(OrderSide.BUY, "90"), (OrderSide.SELL, "110")],
)
def test_unrealized_pnl_is_negative_for_losing_long_and_short(side: OrderSide, mark: str) -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(2000))
    portfolio.apply_fill(make_fill(1, side, "10", "100"))

    snapshot = portfolio.mark_to_market(make_bar(1, mark))

    assert snapshot.unrealized_pnl == Decimal(-100)
    assert snapshot.positions[0].unrealized_pnl == Decimal(-100)


def test_historical_snapshots_are_frozen_and_do_not_reference_live_positions() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(2000))
    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "10", "100"))
    historical = portfolio.mark_to_market(make_bar(1, "110"))
    expected = historical.model_copy(deep=True)

    portfolio.apply_fill(make_fill(2, OrderSide.SELL, "4", "120"))
    portfolio.mark_to_market(make_bar(2, "120"))

    assert historical == expected
    assert historical.positions[0].quantity == Decimal(10)
    with pytest.raises(ValidationError, match="frozen"):
        historical.positions[0].quantity = Decimal(0)  # type: ignore[misc]


def test_negative_cash_is_recorded_and_reset_is_deterministic() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(100))
    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "2", "100"))
    first = portfolio.mark_to_market(make_bar(1, "100"))
    assert first.cash == Decimal(-100)
    assert first.equity == Decimal(100)

    portfolio.reset()
    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "2", "100"))
    second = portfolio.mark_to_market(make_bar(1, "100"))
    assert second == first


def test_fills_and_market_data_share_one_monotonic_portfolio_clock() -> None:
    portfolio = PortfolioEngine(EventBus(), Decimal(1000))
    portfolio.mark_to_market(make_bar(2, "100"))
    with pytest.raises(PortfolioError, match="backwards"):
        portfolio.mark_to_market(make_bar(1, "100"))
    with pytest.raises(PortfolioError, match="fill cannot move"):
        portfolio.apply_fill(make_fill(1, OrderSide.BUY, "1", "100"))

    portfolio.reset()
    portfolio.apply_fill(make_fill(2, OrderSide.BUY, "1", "100"))
    with pytest.raises(PortfolioError, match="market data cannot move"):
        portfolio.mark_to_market(make_bar(1, "100"))
    with pytest.raises(PortfolioError, match="fill cannot move"):
        portfolio.apply_fill(make_fill(1, OrderSide.BUY, "1", "100"))
