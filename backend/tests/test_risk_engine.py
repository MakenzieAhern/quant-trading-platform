from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal, localcontext
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.domain.risk import OrderProposal, RiskConfig, RiskDecision, RiskReasonCode
from app.domain.trading import OrderSide, OrderType, PortfolioSnapshot, Position
from app.risk import RiskEngine

START = datetime(2024, 1, 2, tzinfo=UTC)
ZERO = Decimal(0)


def proposal(
    sequence: int = 1,
    side: OrderSide = OrderSide.BUY,
    quantity: str = "1",
    symbol: str = "AAPL",
    order_type: OrderType = OrderType.MARKET,
) -> OrderProposal:
    return OrderProposal(
        proposal_id=UUID(int=sequence),
        strategy_id="manual",
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=Decimal(quantity),
        signal_timestamp=START,
    )


def position(symbol: str, quantity: str, mark: str) -> Position:
    return Position(
        symbol=symbol,
        quantity=Decimal(quantity),
        average_price=Decimal(mark),
        market_price=Decimal(mark),
        unrealized_pnl=ZERO,
        realized_pnl=ZERO,
    )


def snapshot(
    positions: tuple[Position, ...] = (),
    *,
    cash: str = "10000",
    equity: str | None = None,
    drawdown: str = "0",
) -> PortfolioSnapshot:
    market_value = sum((item.quantity * item.market_price for item in positions), ZERO)
    return PortfolioSnapshot(
        timestamp=START,
        cash=Decimal(cash),
        positions=positions,
        market_value=market_value,
        equity=Decimal(equity) if equity is not None else Decimal(cash) + market_value,
        drawdown=Decimal(drawdown),
    )


def test_manual_position_limit_reference_uses_projected_position() -> None:
    state = snapshot((position("AAPL", "20", "100"),), cash="8000")
    engine = RiskEngine(RiskConfig(max_position_quantity=Decimal(25)))

    increase = engine.evaluate(proposal(quantity="10"), state, {"AAPL": Decimal(100)})
    reduction = engine.evaluate(proposal(2, OrderSide.SELL, "5"), state, {"AAPL": Decimal(100)})

    assert increase.reason_code is RiskReasonCode.POSITION_LIMIT
    assert increase.projected_position_quantity == Decimal(30)
    assert reduction.approved
    assert reduction.projected_position_quantity == Decimal(15)
    assert not reduction.risk_increasing


@pytest.mark.parametrize(
    ("current", "side", "quantity", "limit", "approved", "projected"),
    [
        ("5", OrderSide.BUY, "3", "7", False, "8"),
        ("-5", OrderSide.SELL, "3", "7", False, "-8"),
        ("10", OrderSide.SELL, "4", "5", True, "6"),
        ("20", OrderSide.BUY, "5", "25", True, "25"),
        ("10", OrderSide.SELL, "15", "5", True, "-5"),
        ("-10", OrderSide.BUY, "15", "5", True, "5"),
        ("5", OrderSide.SELL, "8", "2", False, "-3"),
        ("-5", OrderSide.BUY, "8", "2", False, "3"),
    ],
)
def test_position_limit_distinguishes_reductions_from_reversals(
    current: str,
    side: OrderSide,
    quantity: str,
    limit: str,
    approved: bool,
    projected: str,
) -> None:
    state = snapshot((position("AAPL", current, "100"),))
    decision = RiskEngine(RiskConfig(max_position_quantity=Decimal(limit))).evaluate(
        proposal(side=side, quantity=quantity), state, {"AAPL": Decimal(100)}
    )

    assert decision.approved is approved
    assert decision.projected_position_quantity == Decimal(projected)


def test_multi_symbol_gross_and_net_exposure_use_independent_marks() -> None:
    long_only = snapshot(
        (position("AAPL", "10", "100"), position("MSFT", "5", "200")),
        cash="8000",
    )
    engine = RiskEngine(RiskConfig(max_gross_exposure=Decimal(2400)))

    decision = engine.evaluate(
        proposal(quantity="5"), long_only, {"AAPL": Decimal(100), "MSFT": Decimal(200)}
    )

    assert decision.reason_code is RiskReasonCode.GROSS_EXPOSURE_LIMIT
    assert decision.projected_symbol_exposure == Decimal(1500)
    assert decision.projected_gross_exposure == Decimal(2500)
    assert decision.projected_net_exposure == Decimal(2500)

    hedged = snapshot((position("AAPL", "10", "100"), position("MSFT", "-5", "200")))
    assert hedged.market_value == Decimal(0)
    assert sum(
        (abs(item.quantity * item.market_price) for item in hedged.positions), ZERO
    ) == Decimal(2000)
    diagnostic = RiskEngine().evaluate(
        proposal(quantity="1"), hedged, {"AAPL": Decimal(100), "MSFT": Decimal(200)}
    )
    assert diagnostic.projected_gross_exposure == Decimal(2100)
    assert diagnostic.projected_net_exposure == Decimal(100)


def test_symbol_exposure_uses_target_mark_and_exact_decimal() -> None:
    state = snapshot((position("MSFT", "5", "200"),), cash="9000")
    decision = RiskEngine(RiskConfig(max_symbol_exposure=Decimal(250))).evaluate(
        proposal(quantity="3"), state, {"AAPL": Decimal(100), "MSFT": Decimal(200)}
    )

    assert decision.reason_code is RiskReasonCode.SYMBOL_EXPOSURE_LIMIT
    assert decision.reference_price == Decimal(100)
    assert decision.projected_symbol_exposure == Decimal(300)
    assert decision.projected_gross_exposure == Decimal(1300)


@pytest.mark.parametrize(
    ("current", "side", "quantity", "expected_quantity", "expected_exposure"),
    [
        ("10", OrderSide.SELL, "4", "6", "600"),
        ("-10", OrderSide.BUY, "4", "-6", "600"),
        ("10", OrderSide.SELL, "15", "-5", "500"),
        ("-10", OrderSide.BUY, "15", "5", "500"),
    ],
)
def test_symbol_exposure_uses_final_long_short_reduction_and_reversal_state(
    current: str,
    side: OrderSide,
    quantity: str,
    expected_quantity: str,
    expected_exposure: str,
) -> None:
    state = snapshot((position("AAPL", current, "100"),))
    decision = RiskEngine().evaluate(
        proposal(side=side, quantity=quantity), state, {"AAPL": Decimal(100)}
    )

    assert decision.projected_position_quantity == Decimal(expected_quantity)
    assert decision.projected_symbol_exposure == Decimal(expected_exposure)


def test_permissive_configuration_supports_short_selling() -> None:
    decision = RiskEngine().evaluate(
        proposal(side=OrderSide.SELL, quantity="10"),
        snapshot(),
        {"AAPL": Decimal(100)},
    )

    assert decision.approved
    assert decision.projected_position_quantity == Decimal(-10)
    assert decision.projected_gross_exposure == Decimal(1000)


def test_order_notional_uses_current_mark_not_future_execution_price() -> None:
    decision = RiskEngine(RiskConfig(max_order_notional=Decimal(1000))).evaluate(
        proposal(quantity="10.01"), snapshot(), {"AAPL": Decimal(100)}
    )

    assert decision.reason_code is RiskReasonCode.ORDER_NOTIONAL_LIMIT
    assert decision.order_notional == Decimal(1001)
    assert decision.reference_price == Decimal(100)


@pytest.mark.parametrize(
    ("side", "quantity", "approved"),
    [
        (OrderSide.BUY, "10", True),
        (OrderSide.SELL, "10", True),
        (OrderSide.BUY, "10.0001", False),
        (OrderSide.SELL, "10.0001", False),
    ],
)
def test_order_notional_limit_has_exact_decimal_boundary_for_both_sides(
    side: OrderSide, quantity: str, approved: bool
) -> None:
    decision = RiskEngine(RiskConfig(max_order_notional=Decimal(1000))).evaluate(
        proposal(side=side, quantity=quantity), snapshot(), {"AAPL": Decimal(100)}
    )

    assert decision.approved is approved
    assert decision.order_notional == Decimal(quantity) * Decimal(100)


def test_order_notional_limit_still_applies_to_a_reduction() -> None:
    state = snapshot((position("AAPL", "10", "100"),), cash="9000")
    decision = RiskEngine(RiskConfig(max_order_notional=Decimal(400))).evaluate(
        proposal(side=OrderSide.SELL, quantity="5"),
        state,
        {"AAPL": Decimal(100)},
    )

    assert not decision.risk_increasing
    assert decision.reason_code is RiskReasonCode.ORDER_NOTIONAL_LIMIT


def test_genuine_reduction_can_remain_above_portfolio_risk_limits() -> None:
    state = snapshot(
        (position("AAPL", "20", "100"),),
        cash="8000",
        drawdown="-0.20",
    )
    config = RiskConfig(
        max_position_quantity=Decimal(10),
        max_symbol_exposure=Decimal(1000),
        max_gross_exposure=Decimal(1000),
        max_leverage=Decimal("0.10"),
        enforce_buying_power=True,
        max_drawdown=Decimal("-0.15"),
    )

    decision = RiskEngine(config).evaluate(
        proposal(side=OrderSide.SELL, quantity="5"),
        state,
        {"AAPL": Decimal(100)},
    )

    assert decision.approved
    assert not decision.risk_increasing
    assert decision.projected_position_quantity == Decimal(15)
    assert decision.projected_gross_exposure == Decimal(1500)


def test_leverage_reference_is_gross_exposure_over_current_equity() -> None:
    decision = RiskEngine(RiskConfig(max_leverage=Decimal(2))).evaluate(
        proposal(quantity="25"),
        snapshot(cash="1000", equity="1000"),
        {"AAPL": Decimal(100)},
    )

    assert decision.reason_code is RiskReasonCode.LEVERAGE_LIMIT
    assert decision.projected_gross_exposure == Decimal(2500)
    assert decision.projected_gross_leverage == Decimal("2.5")


def test_leverage_uses_current_equity_not_transaction_cost_adjusted_equity() -> None:
    decision = RiskEngine(RiskConfig(max_leverage=Decimal("2.6"))).evaluate(
        proposal(quantity="25"),
        snapshot(cash="1000", equity="1000"),
        {"AAPL": Decimal(100)},
        estimated_transaction_cost=Decimal(100),
    )

    assert decision.approved
    assert decision.projected_cash == Decimal("-1600")
    assert decision.projected_gross_exposure == Decimal(2500)
    assert decision.projected_gross_leverage == Decimal("2.5")


def test_non_positive_equity_halts_increases_but_allows_genuine_reduction() -> None:
    invalid = snapshot(cash="-100", equity="-100")
    halted = RiskEngine().evaluate(proposal(), invalid, {"AAPL": Decimal(100)})
    assert halted.reason_code is RiskReasonCode.INVALID_PORTFOLIO_STATE
    assert halted.projected_gross_leverage is None

    reducing = snapshot((position("AAPL", "10", "100"),), cash="-1100", equity="-100")
    allowed = RiskEngine().evaluate(
        proposal(side=OrderSide.SELL, quantity="5"),
        reducing,
        {"AAPL": Decimal(100)},
    )
    assert allowed.approved
    assert not allowed.risk_increasing


def test_buying_power_includes_known_transaction_cost() -> None:
    engine = RiskEngine(RiskConfig(enforce_buying_power=True))

    rejected = engine.evaluate(
        proposal(quantity="10"),
        snapshot(cash="1000", equity="1000"),
        {"AAPL": Decimal(100)},
        estimated_transaction_cost=Decimal(1),
    )
    approved = engine.evaluate(
        proposal(2, quantity="9"),
        snapshot(cash="1000", equity="1000"),
        {"AAPL": Decimal(100)},
        estimated_transaction_cost=Decimal(1),
    )

    assert rejected.reason_code is RiskReasonCode.INSUFFICIENT_BUYING_POWER
    assert rejected.projected_cash == Decimal(-1)
    assert approved.approved
    assert approved.projected_cash == Decimal(99)


def test_drawdown_guard_blocks_increase_and_allows_reduction() -> None:
    engine = RiskEngine(RiskConfig(max_drawdown=Decimal("-0.15")))
    empty = snapshot(cash="8000", equity="8000", drawdown="-0.20")
    assert (
        engine.evaluate(proposal(), empty, {"AAPL": Decimal(100)}).reason_code
        is RiskReasonCode.DRAWDOWN_LIMIT
    )

    long_state = snapshot(
        (position("AAPL", "10", "100"),),
        cash="7000",
        equity="8000",
        drawdown="-0.20",
    )
    reduction = engine.evaluate(
        proposal(2, OrderSide.SELL, "5"), long_state, {"AAPL": Decimal(100)}
    )
    assert reduction.approved

    boundary = snapshot(cash="8500", equity="8500", drawdown="-0.15")
    assert engine.evaluate(proposal(3), boundary, {"AAPL": Decimal(100)}).approved


def test_basic_validation_and_missing_mark_are_explicit() -> None:
    engine = RiskEngine()

    assert (
        engine.evaluate(proposal(quantity="0"), snapshot(), {"AAPL": Decimal(100)}).reason_code
        is RiskReasonCode.INVALID_QUANTITY
    )
    assert (
        engine.evaluate(
            proposal(order_type=OrderType.LIMIT), snapshot(), {"AAPL": Decimal(100)}
        ).reason_code
        is RiskReasonCode.UNSUPPORTED_ORDER_TYPE
    )
    assert (
        engine.evaluate(proposal(), snapshot(), {}).reason_code
        is RiskReasonCode.INVALID_PORTFOLIO_STATE
    )
    with pytest.raises(ValidationError, match="symbol"):
        proposal(symbol="bad symbol")


def test_invalid_snapshot_and_decision_contract_fail_explicitly() -> None:
    inconsistent = snapshot().model_copy(update={"equity": Decimal(9999)})
    decision = RiskEngine().evaluate(proposal(), inconsistent, {"AAPL": Decimal(100)})
    assert decision.reason_code is RiskReasonCode.INVALID_PORTFOLIO_STATE

    with pytest.raises(ValidationError, match="approved must match"):
        RiskDecision(
            proposal_id=UUID(int=1),
            approved=False,
            reason_code=RiskReasonCode.APPROVED,
            message="invalid",
            timestamp=START,
            risk_increasing=True,
        )
    with pytest.raises(ValidationError, match="frozen"):
        decision.approved = True  # type: ignore[misc]


def test_reservations_are_included_without_mutating_inputs_or_decimal_context() -> None:
    state = snapshot()
    intent = proposal(quantity="5")
    expected_state = state.model_copy(deep=True)
    expected_intent = intent.model_copy(deep=True)

    with localcontext() as context:
        context.prec = 6
        context.rounding = ROUND_DOWN
        decision = RiskEngine().evaluate(
            intent,
            state,
            {"AAPL": Decimal("123.456789")},
            reserved_quantities={"AAPL": Decimal(2)},
            reserved_cash_delta=Decimal("-247.913578"),
            estimated_transaction_cost=Decimal("1.25"),
        )
        assert context.prec == 6
        assert context.rounding == ROUND_DOWN

    assert decision.projected_position_quantity == Decimal(7)
    assert decision.projected_cash == Decimal("9133.552477")
    assert state == expected_state
    assert intent == expected_intent


def test_risk_evaluation_is_pure_and_reproducible() -> None:
    state = snapshot((position("AAPL", "4", "100"),), cash="9600")
    intent = proposal(side=OrderSide.SELL, quantity="2")
    marks = {"AAPL": Decimal(100)}
    engine = RiskEngine(RiskConfig(max_position_quantity=Decimal(10)))

    first = engine.evaluate(intent, state, marks)
    second = engine.evaluate(intent, state, marks)

    assert second == first
    assert state.positions[0].quantity == Decimal(4)
    assert marks == {"AAPL": Decimal(100)}


def test_invalid_reserved_buying_power_is_rejected_explicitly() -> None:
    decision = RiskEngine().evaluate(
        proposal(),
        snapshot(),
        {"AAPL": Decimal(100)},
        reserved_buying_power=Decimal(-1),
    )

    assert decision.reason_code is RiskReasonCode.INVALID_PORTFOLIO_STATE
    assert "reserved buying power" in decision.message


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"max_order_notional": Decimal(0)}, "max_order_notional"),
        ({"max_leverage": Decimal(-1)}, "max_leverage"),
        ({"max_leverage": Decimal("NaN")}, "finite"),
        ({"max_gross_exposure": Decimal("Infinity")}, "finite"),
        ({"max_drawdown": Decimal("-1.1")}, "max_drawdown"),
        ({"max_drawdown": Decimal("0.1")}, "max_drawdown"),
    ],
)
def test_risk_config_rejects_invalid_limits(values: dict[str, Any], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        RiskConfig.model_validate(values)
