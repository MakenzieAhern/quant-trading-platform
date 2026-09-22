from dataclasses import replace
from datetime import date
from decimal import Decimal

from app.data.providers.research import SecurityStatusRecord
from app.domain.markets import Board, Exchange, Market, TradingRuleResolver
from app.domain.markets.cn_a_rules import historical_cn_a_rules
from app.domain.trading import OrderSide, OrderType
from app.execution import FixedCommission
from app.research.engine import ResearchExecutionEngine
from tests.test_research_execution_engine import CALENDAR, OneTargetStrategy, _session


def test_unknown_suspension_is_not_normalized_to_false_and_cannot_fill() -> None:
    first = _session(date(2024, 1, 2), opening="10")
    next_day = _session(date(2024, 1, 3), opening="9.9")
    unknown = next_day.statuses[0].status.model_copy(update={"is_suspended": None})
    # Even a conflicting positive tradeability flag cannot override unknown suspension.
    assert unknown.is_tradeable is True
    rule = TradingRuleResolver(historical_cn_a_rules()).resolve(
        security_id=unknown.security_id,
        market=Market.CN_A,
        exchange=Exchange.SSE,
        board=Board.SSE_MAIN,
        trading_date=unknown.trading_date,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        security_status=unknown,
        listing_age_sessions=999,
    )
    assert rule.suspended is None and rule.executable is False
    next_day = replace(
        next_day, statuses=(SecurityStatusRecord(status=unknown),), trading_rules=(rule,)
    )
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    result = engine.run(iter((first, next_day)))
    assert result.proposals and result.orders
    assert not result.fills and not result.active_reservations
    assert result.execution_checks[0][1] == "NOT_CONFIRMED_TRADEABLE"
    assert result.snapshots[-1].equity == Decimal(10000)
