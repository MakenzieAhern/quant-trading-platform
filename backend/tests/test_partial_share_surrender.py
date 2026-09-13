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


def approved_convention():
    return MandatoryPartialShareSurrenderEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600462_surrender_convention_v1.json").read_bytes()
    )


@pytest.mark.parametrize("q,retained", [("1", "0"), ("6", "4"), ("101", "80"), ("100", "80")])
def test_approved_ceil_surrender_preserves_basis_and_zero_position(q, retained):
    e = approved_convention().model_copy(update={"research_effective_date": date(2024, 1, 4)})
    p, emitted = funded(q)
    before = p.latest_snapshot
    p.apply_partial_surrender(e, at("2024-01-04"), holder_class=e.affected_holder_class)
    after = p.snapshot_at(at("2024-01-04"))
    a = after.partial_surrender_audits[0]
    assert a.retained_quantity == Decimal(retained)
    assert a.surrendered_quantity + a.retained_quantity == Decimal(q)
    assert a.retained_basis == Decimal(retained) * 10
    assert a.retained_basis + a.surrendered_basis == Decimal(q) * 10
    assert after.corporate_action_realized_pnl == -a.surrendered_basis
    assert after.realized_pnl == before.realized_pnl == 0
    assert after.cash == before.cash and not emitted
    assert after.total_pnl == after.equity - p.initial_cash
    assert before.equity - after.equity == a.market_value_removed
    assert after.positions[0].average_price == (10 if Decimal(retained) else 0)
    assert a.historical_registry_date is None
    assert a.research_fraction_rule == "CEIL_SURRENDER_FLOOR_RETAINED_V1"
    assert a.extra_shares_vs_floor == (0 if Decimal(q) % 5 == 0 else 1)
    assert a.estimated_value_difference == a.extra_shares_vs_floor * 15
    assert PortfolioSnapshot.model_validate_json(after.model_dump_json()) == after


def test_approved_boundary_requires_provenance_not_an_invented_registry_date():
    e = approved_convention()
    assert e.effective_date is None and e.application_date == date(2012, 11, 19)
    assert (
        e.event_checksum
        == e.model_copy(
            update={
                "sources": tuple(reversed(e.sources)),
                "confirmation_sources": tuple(reversed(e.confirmation_sources)),
                "boundary_sources": tuple(reversed(e.boundary_sources)),
            }
        ).event_checksum
    )
    for update in (
        {"boundary_sources": ()},
        {"convention_approval_sha256": None},
        {"nontrading_from": date(2012, 11, 19)},
    ):
        with pytest.raises(ValueError):
            MandatoryPartialShareSurrenderEvent.model_validate({**e.model_dump(), **update})


def test_resumption_mutation_precedes_bar_and_is_price_independent(monkeypatch):
    from dataclasses import replace

    from app.domain.markets.calendar import TradingCalendar, TradingSession
    from app.domain.markets.identifiers import Market
    from app.execution import FixedCommission
    from app.research import ResearchExecutionEngine, ResearchSession
    from tests.test_research_execution_engine import SECURITY_ID, OneTargetStrategy, _session

    days = [
        date(2012, 2, 7),
        date(2012, 2, 8),
        date(2012, 11, 16),
        date(2012, 11, 19),
        date(2012, 11, 20),
    ]
    # Sparse calendar is an ordering fixture, not full historical-calendar evidence.
    calendar = TradingCalendar(
        market=Market.CN_A,
        sessions=tuple(
            TradingSession(session_date=d, is_open=True, source_version="boundary_fixture")
            for d in days
        ),
    )
    e = approved_convention().model_copy(update={"security_id": SECURITY_ID})
    original = PortfolioEngine.apply_partial_surrender
    observed = []

    def apply(p, event, timestamp, *, holder_class):
        assert p.positions[0].quantity == 100
        assert p.marks["600000.SSE"] == Decimal("9.9")
        original(p, event, timestamp, holder_class=holder_class)
        assert p.positions[0].quantity == 80
        observed.append(p.partial_surrender_audits[0])

    monkeypatch.setattr(PortfolioEngine, "apply_partial_surrender", apply)
    for opening in ("5", "20"):
        engine = ResearchExecutionEngine(
            OneTargetStrategy(),
            initial_cash=Decimal(10000),
            commission_model=FixedCommission(),
            calendar=calendar,
        )
        sessions = [
            _session(days[0], opening="10"),
            _session(days[1], opening="9.9"),
            ResearchSession(trading_date=days[2], bars=(), statuses=(), buy_lot_sizes=()),
            replace(
                _session(days[3], opening=opening),
                partial_surrenders=(e,),
                surrender_holder_class=e.affected_holder_class,
            ),
            _session(days[4], opening=opening),
        ]
        result = engine.run(sessions)
        assert len(result.fills) == len(result.orders) == 1
        assert result.snapshots[-1].positions[0].quantity == 80
        assert result.snapshots[-1].positions[0].aggregate_cost_basis == 792
        assert result.partial_surrender_boundary_policy == "FIRST_POST_EVENT_TRADING_BOUNDARY_V1"
    assert observed[0] == observed[1]
    bad = replace(sessions[3], bars=())
    with pytest.raises(ValueError, match="FIRST_TRADABLE_BOUNDARY_REQUIRED"):
        engine.run([*sessions[:3], bad])


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


def test_quantity_residue_reachability_not_a_historical_position_certificate():
    # All integer holdings reduce to five residues for S=1/5. These are account
    # domain witnesses, not proof of an actual historical strategy position.
    e = action()
    for q in range(1, 1001):
        p, _ = funded(str(q))
        if q % 5:
            before = p.latest_snapshot
            with pytest.raises(ValueError, match="FRACTIONAL_ALLOCATION_UNRESOLVED"):
                p.apply_partial_surrender(e, at("2024-01-04"), holder_class=e.affected_holder_class)
            assert p.latest_snapshot == before
        else:
            p.apply_partial_surrender(e, at("2024-01-04"), holder_class=e.affected_holder_class)
            assert p.positions[0].quantity == Decimal(q) * Decimal("0.8")
    assert all((Decimal(q) * Decimal("0.2")) % 1 == 0 for q in range(0, 100001, 100))


def test_official_aggregate_counts_do_not_establish_holder_rounding_or_registry_date():
    import json

    chain = json.loads(
        (Path(__file__).parent / "fixtures/600462_registry_evidence_chain_v1.json").read_bytes()
    )
    c = chain["counts"]
    assert c["pre_event_total"] + c["separate_issuance"] == c["post_total"]
    assert c["pre_event_total"] - c["actual_surrender_all_classes"] == c["post_unrestricted"]
    assert c["actual_surrender_all_classes"] + c["separate_issuance"] == c["post_restricted"]
    assert c["post_unrestricted"] + c["post_restricted"] == c["post_total"]
    assert c["expected_all_classes"] - c["actual_surrender_all_classes"] == 28163
    assert 28163 - sum(c["listed_unexecuted_quantities"]) == 116
    assert chain["timing"]["first_post_event_trading_boundary"] == "2012-11-19"
    assert chain["timing"]["exact_registry_date"] is None
    assert chain["fractional_execution_rule"] == "NOT_EVIDENCED"


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
