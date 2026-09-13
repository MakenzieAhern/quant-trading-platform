from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from app.domain.markets.surrenders import (
    PARTIAL_SURRENDER_POLICY,
    MandatoryPartialShareSurrenderEvent,
)
from app.domain.trading import OrderSide, PortfolioSnapshot
from app.event import EventBus, EventType
from app.portfolio import PortfolioEngine
from tests.test_demerger_accounting import at
from tests.test_portfolio_engine import make_bar, make_fill


def evidence():
    return MandatoryPartialShareSurrenderEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600462_partial_surrender.json").read_bytes()
    )


def action():
    # Engineering date ONLY. Do not represent this as a verified historical transfer date.
    return evidence().model_copy(update={"effective_date": date(2024, 1, 4)})


def funded(q="100", price="10"):
    bus = EventBus()
    events = []
    for kind in (EventType.ORDER_CREATED, EventType.ORDER_FILLED, EventType.ORDER_PROPOSAL):
        bus.subscribe(kind, events.append)
    p = PortfolioEngine(bus, Decimal(100000))
    p.apply_fill(
        make_fill(1, OrderSide.BUY, q, price, symbol="600462.SSE").model_copy(
            update={"timestamp": at("2024-01-02"), "commission": Decimal("0.5")}
        )
    )
    p.mark_to_market(
        make_bar(1, "15", symbol="600462.SSE").model_copy(update={"timestamp": at("2024-01-03")})
    )
    return p, events


@pytest.mark.parametrize(
    "q,price,basis,lost",
    [
        ("100", "10", "1000", "200"),
        ("1000", "12.34567", "12345.67", "2469.134"),
    ],
)
def test_proportional_surrender_reconciles_and_preserves_average(q, price, basis, lost):
    outputs = []
    for reverse in (False, True):
        event = action()
        if reverse:
            event = event.model_copy(
                update={
                    "sources": tuple(reversed(event.sources)),
                    "confirmation_sources": tuple(reversed(event.confirmation_sources)),
                }
            )
        p, emitted = funded(q, price)
        before = p.latest_snapshot
        with localcontext() as ctx:
            ctx.prec = 6
            p.apply_partial_surrender(
                event, at("2024-01-04"), holder_class=event.affected_holder_class
            )
            after = p.snapshot_at(at("2024-01-04"))
        with localcontext() as ctx:
            ctx.prec = 28
            a = after.partial_surrender_audits[0]
            assert a.surrendered_quantity == Decimal(q) * Decimal("0.2")
            assert a.retained_quantity + a.surrendered_quantity == Decimal(q)
            assert a.surrendered_basis == Decimal(lost)
            assert a.surrendered_basis + a.retained_basis == a.original_basis == Decimal(basis)
            assert a.retained_basis / a.retained_quantity == Decimal(price)
            assert (
                after.positions[0].average_price
                == before.positions[0].average_price
                == Decimal(price)
            )
            assert after.positions[0].aggregate_cost_basis == a.retained_basis
            assert before.equity - after.equity == a.market_value_removed
            assert after.cash == before.cash and not emitted
            assert after.cumulative_commission == before.cumulative_commission == Decimal("0.5")
            assert after.realized_pnl == before.realized_pnl == 0
            assert after.corporate_action_realized_pnl == -Decimal(lost)
            assert after.total_pnl == after.equity - p.initial_cash
            assert after.total_pnl == (
                after.realized_pnl
                + after.corporate_action_realized_pnl
                + after.unrealized_pnl
                - after.cumulative_commission
            )
            assert not after.pending_mergers and not after.pending_demergers
            assert a.policy == PARTIAL_SURRENDER_POLICY
            assert PortfolioSnapshot.model_validate_json(after.model_dump_json()) == after
            assert p.partial_surrender_materiality()["total_basis_written_off"] == Decimal(lost)
        outputs.append(after)
        with pytest.raises(ValueError, match="duplicate"):
            p.apply_partial_surrender(
                event, at("2024-01-04"), holder_class=event.affected_holder_class
            )
        assert p.snapshot_at(at("2024-01-04")) == after
        p.reset()
        assert not p.partial_surrender_audits
        assert p.snapshot_at(at("2024-01-04")).corporate_action_realized_pnl == 0
    assert outputs[0] == outputs[1]


def test_zero_position_and_same_security_remains_orderable():
    p = PortfolioEngine(EventBus(), Decimal(10000))
    e = action()
    p.apply_partial_surrender(e, at("2024-01-04"), holder_class=e.affected_holder_class)
    assert p.cash == 10000 and not p.positions and not p.partial_surrender_audits
    assert p.partial_surrender_materiality()["events_total"] == 1
    assert p.is_orderable("600462.SSE")


def test_fractional_quantity_compensation_unknown_date_and_holder_fail_without_mutation():
    for e, holder, q, error in [
        (action(), action().affected_holder_class, "6", "FRACTIONAL_ALLOCATION_UNRESOLVED"),
        (
            action().model_copy(
                update={"consideration_type": "CASH", "consideration_value": Decimal(1)}
            ),
            action().affected_holder_class,
            "100",
            "CONSIDERATION_POLICY_UNRESOLVED",
        ),
        (evidence(), action().affected_holder_class, "100", "EFFECTIVE_DATE_UNVERIFIED"),
        (action(), "EXEMPT_CREDIT_ACCOUNT", "100", "HOLDER_APPLICABILITY_UNVERIFIED"),
    ]:
        p, emitted = funded(q)
        before = p.latest_snapshot
        with pytest.raises(ValueError, match=error):
            p.apply_partial_surrender(e, at("2024-01-04"), holder_class=holder)
        assert p.snapshot_at(at("2024-01-03")) == before and not emitted


@pytest.mark.parametrize("ratio", ["0", "1", "-0.2", "NaN", "Infinity", 0.2, True])
def test_invalid_ratio_rejected(ratio):
    with pytest.raises(ValueError):
        MandatoryPartialShareSurrenderEvent.model_validate(
            {**evidence().model_dump(), "surrender_ratio": ratio}
        )


def test_no_closed_strategy_trade_is_created_and_following_sale_uses_retained_basis():
    from app.research.analytics import ClosedTrade, analyze_research_period

    p, _ = funded()
    e = action()
    p.apply_partial_surrender(e, at("2024-01-04"), holder_class=e.affected_holder_class)
    snap = p.snapshot_at(at("2024-01-04"))
    trades = (ClosedTrade(Decimal(10), 2), ClosedTrade(Decimal(-5), 1))
    first = analyze_research_period(equity=(Decimal(100000), Decimal(100005)), closed_trades=trades)
    after = analyze_research_period(equity=(Decimal(100000), snap.equity), closed_trades=trades)
    assert after.number_of_trades == first.number_of_trades == 2
    assert (after.win_rate, after.profit_factor) == (first.win_rate, first.profit_factor)
    p.apply_fill(
        make_fill(2, OrderSide.SELL, "40", "12", symbol="600462.SSE").model_copy(
            update={"timestamp": at("2024-01-05")}
        )
    )
    final = p.snapshot_at(at("2024-01-05"))
    assert final.positions[0].aggregate_cost_basis == 400
    assert final.realized_pnl == 80 and final.corporate_action_realized_pnl == -200


def test_research_session_no_bar_accounting_replay_and_source_order():
    from app.domain.markets.calendar import TradingCalendar, TradingSession
    from app.domain.markets.identifiers import Market
    from app.execution import FixedCommission
    from app.research import ResearchExecutionEngine, ResearchSession
    from tests.test_research_execution_engine import SECURITY_ID, OneTargetStrategy, _session

    class Strategy(OneTargetStrategy):
        def target_for_completed_session(self, session, available_equity):
            assert not session.partial_surrenders and session.surrender_holder_class is None
            return super().target_for_completed_session(session, available_equity)

    days = [date(2024, 1, n) for n in (2, 3, 4)]
    engine = ResearchExecutionEngine(
        Strategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=TradingCalendar(
            market=Market.CN_A,
            sessions=tuple(
                TradingSession(session_date=d, is_open=True, source_version="synthetic")
                for d in days
            ),
        ),
    )
    results = []
    for reverse in (False, True):
        e = action().model_copy(update={"security_id": SECURITY_ID})
        if reverse:
            e = e.model_copy(update={"sources": tuple(reversed(e.sources))})
        sessions = [
            _session(days[0], opening="10"),
            _session(days[1], opening="9.9"),
            ResearchSession(
                trading_date=days[2],
                bars=(),
                statuses=(),
                buy_lot_sizes=(),
                partial_surrenders=(e,),
                surrender_holder_class=e.affected_holder_class,
            ),
        ]
        results.append(engine.run(sessions))
    assert results[0] == results[1]
    final = results[0].snapshots[-1]
    assert final.timestamp.date() == days[2]
    assert final.positions[0].quantity == 80
    assert final.positions[0].aggregate_cost_basis == 792
    assert final.corporate_action_realized_pnl == -198 and final.realized_pnl == 0
    assert len(results[0].fills) == len(results[0].orders) == 1
    assert results[0].partial_surrender_policy == PARTIAL_SURRENDER_POLICY
