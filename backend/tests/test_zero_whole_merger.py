from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from app.domain.markets.mergers import ZERO_WHOLE_SHARE_POLICY, FractionalShareMethod, MergerEvent
from app.domain.trading import OrderSide, PortfolioSnapshot
from app.event import EventBus, EventType
from app.portfolio import PortfolioEngine
from tests.test_demerger_accounting import at
from tests.test_portfolio_engine import make_bar, make_fill


def event():
    return MergerEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600005_merger.json").read_bytes()
    )


def funded(quantity):
    bus = EventBus()
    emitted = []
    for kind in (EventType.ORDER_CREATED, EventType.ORDER_FILLED, EventType.ORDER_PROPOSAL):
        bus.subscribe(kind, emitted.append)
    p = PortfolioEngine(bus, Decimal(10000))
    # Synthetic raw price/basis/holding inputs, not a historical strategy run.
    p.apply_fill(
        make_fill(1, OrderSide.BUY, str(quantity), "3", symbol="600005.SSE").model_copy(
            update={"timestamp": at("2017-01-20"), "commission": Decimal("0.5")}
        )
    )
    p.mark_to_market(
        make_bar(1, "4", symbol="600005.SSE").model_copy(update={"timestamp": at("2017-01-23")})
    )
    return p, emitted


@pytest.mark.parametrize("q,w,f", [(1, 0, "0.56"), (2, 1, "0.12"), (100, 56, "0"), (3, 1, "0.68")])
def test_verified_600005_conserves_pnl_without_double_count(q, w, f):
    outputs = []
    for reverse in (False, True):
        action = event()
        if reverse:
            action = action.model_copy(update={"sources": tuple(reversed(action.sources))})
        p, emitted = funded(q)
        before = p.latest_snapshot
        with localcontext() as context:
            context.prec = 6
            p.recognize_merger(action, date(2017, 2, 17), at("2017-02-17"))
            after = p.snapshot_at(at("2017-02-17"))
            assert after.cash == before.cash and not after.positions and not emitted
            assert after.realized_pnl == before.realized_pnl == 0
            audit = after.merger_rounding_audits[0]
            assert audit.whole_successor_quantity == w
            assert audit.fractional_remainder == Decimal(f)
            assert audit.zero_whole_share_policy == ZERO_WHOLE_SHARE_POLICY
            if not w:
                assert not after.pending_mergers
                assert after.corporate_action_realized_pnl == -3 * q
                assert after.market_value == after.unrealized_pnl == 0
                assert before.equity - after.equity == 4 * q  # Removed exactly once.
                assert audit.basis_written_off == 3 * q and audit.market_value_removed == 4 * q
                assert (
                    audit.accounting_classification == "CORPORATE_ACTION_FRACTIONAL_FORFEITURE_LOSS"
                )
            else:
                assert after.pending_mergers[0].aggregate_cost_basis == 3 * q
                assert after.corporate_action_realized_pnl == audit.basis_written_off == 0
                assert after.equity == before.equity
            assert after.total_pnl == after.equity - p.initial_cash
            assert after.total_pnl == (
                after.realized_pnl
                + after.corporate_action_realized_pnl
                + after.unrealized_pnl
                - after.cumulative_commission
            )
            assert PortfolioSnapshot.model_validate_json(after.model_dump_json()) == after
            p.activate_mergers(date(2017, 2, 24), {"600019.SSE": Decimal(99)}, at("2017-02-24"))
            assert not p.positions and p.merger_rounding_audits[0].first_available_raw_price is None
            p.activate_mergers(date(2017, 2, 27), {"600019.SSE": Decimal(6)}, at("2017-02-27"))
            final = p.snapshot_at(at("2017-02-27"))
            if w:
                assert p.positions[0].quantity == w and p.positions[0].aggregate_cost_basis == 3 * q
            else:
                assert not p.positions and not p.pending_mergers
                assert p.merger_materiality()["total_basis_written_off"] == 3 * q
                assert p.merger_materiality()["zero_whole_share_position_occurrences"] == 1
            assert final.total_pnl == (
                final.realized_pnl
                + final.corporate_action_realized_pnl
                + final.unrealized_pnl
                - final.cumulative_commission
            )
            outputs.append(final)
        p.reset()
        assert p.snapshot_at(at("2017-02-27")).corporate_action_realized_pnl == 0
        assert not p.merger_rounding_audits
    assert outputs[0] == outputs[1]


def test_official_compensation_never_falls_through_to_writeoff():
    for method in (
        FractionalShareMethod.OFFICIAL_CASH_IN_LIEU,
        FractionalShareMethod.OFFICIAL_DETERMINISTIC_ALLOCATION,
    ):
        p, _ = funded(1)
        before = p.latest_snapshot
        with pytest.raises(ValueError, match="VARIANT_UNRESOLVED"):
            p.recognize_merger(
                event().model_copy(update={"official_fractional_method": method}),
                date(2017, 2, 17),
                at("2017-02-17"),
            )
        assert p.snapshot_at(at("2017-01-23")) == before


def test_existing_acquirer_not_blocked_by_pending_new_shares():
    p, _ = funded(2)
    p.apply_fill(
        make_fill(2, OrderSide.BUY, "100", "5", symbol="600019.SSE").model_copy(
            update={"timestamp": at("2017-01-23")}
        )
    )
    p.recognize_merger(event(), date(2017, 2, 17), at("2017-02-17"))
    assert p.is_orderable("600019.SSE")
    assert p.positions[0].quantity == 100 and p.pending_mergers[0].whole_successor_quantity == 1
    p.activate_mergers(date(2017, 2, 27), {"600019.SSE": Decimal(6)}, at("2017-02-27"))
    assert p.positions[0].quantity == 101 and p.positions[0].aggregate_cost_basis == 506


def test_forfeiture_not_a_closed_strategy_trade():
    from app.research.analytics import ClosedTrade, analyze_research_period

    p, _ = funded(1)
    p.recognize_merger(event(), date(2017, 2, 17), at("2017-02-17"))
    snap = p.snapshot_at(at("2017-02-17"))
    trades = (ClosedTrade(Decimal(10), 2), ClosedTrade(Decimal(-5), 1))
    baseline = analyze_research_period(
        equity=(Decimal(10000), Decimal(10005)), closed_trades=trades
    )
    adjusted = analyze_research_period(equity=(Decimal(10000), snap.equity), closed_trades=trades)
    assert adjusted.number_of_trades == baseline.number_of_trades == 2
    assert (
        adjusted.win_rate == baseline.win_rate and adjusted.profit_factor == baseline.profit_factor
    )
    assert adjusted.final_equity == snap.cash
    assert snap.pnl_breakdown()["CORPORATE_ACTION_REALIZED_PNL"] == -3


def test_shared_research_engine_records_zero_conversion_on_no_bar_session():
    from app.domain.markets.calendar import TradingCalendar, TradingSession
    from app.domain.markets.identifiers import Market
    from app.execution import FixedCommission
    from app.research import ResearchExecutionEngine, ResearchSession
    from tests.test_research_execution_engine import SECURITY_ID, OneTargetStrategy, _session

    # Synthetic ratio makes the fixture strategy's 100-share lot produce zero whole shares.
    days = [date(2024, 1, n) for n in (2, 3, 4)]
    action = event().model_copy(
        update={
            "parent_security": SECURITY_ID,
            "conversion_ratio": Decimal("0.005"),
            "parent_last_trading_date": days[1],
            "record_date": days[1],
            "effective_date": days[2],
        }
    )
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
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
    sessions = [
        _session(days[0], opening="10"),
        _session(days[1], opening="9.9"),
        ResearchSession(
            trading_date=days[2], bars=(), statuses=(), buy_lot_sizes=(), mergers=(action,)
        ),
    ]
    result = engine.run(sessions)
    assert engine.run(sessions) == result
    final = result.snapshots[-1]
    assert final.timestamp.date() == days[2]
    assert not final.positions and not final.pending_mergers
    assert final.corporate_action_realized_pnl == -990
    assert final.total_pnl == final.equity - Decimal(10000)
    assert final.realized_pnl == 0
    assert len(result.fills) == len(result.orders) == 1
    assert result.zero_whole_share_policy == ZERO_WHOLE_SHARE_POLICY


def test_partial_surrender_is_not_authorized_by_zero_whole_merger_policy():
    from app.domain.markets.corporate_actions import (
        CorporateAction,
        CorporateActionCompleteness,
        CorporateActionType,
    )
    from app.domain.markets.identifiers import SecurityId

    p, _ = funded(1)
    before = p.latest_snapshot
    # Source-shaped unsupported event: the30% issuance goes to a disposal account.
    # No ordinary bonus-share credit or partial-basis convention may be inferred.
    action = CorporateAction(
        security_id=SecurityId(value="CN-A:SSE:600462"),
        action_type=CorporateActionType.MERGER_REORGANIZATION,
        announcement_date=date(2012, 10, 31),
        effective_date=None,
        record_date=date(2012, 10, 25),
        ex_date=None,
        source_provider="CNINFO_OFFICIAL_ISSUER",
        source_version="MANDATORY_SHARE_SURRENDER_SOURCE_REVIEW_V1",
        source_record_hash="9d53f1ea78030b5ee3581af4316f37d6511c4af853623c6b7ea07e42e00cad9a",
        completeness=CorporateActionCompleteness.UNSUPPORTED,
    )
    with pytest.raises(ValueError, match="unsupported or incomplete"):
        p.apply_corporate_action("600462.SSE", action, at("2017-01-23"))
    assert p.snapshot_at(at("2017-01-23")) == before
