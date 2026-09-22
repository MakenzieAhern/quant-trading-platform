from decimal import Decimal, localcontext
from pathlib import Path

import pytest

from app.domain.markets.consolidations import ShareConsolidationEvent
from app.domain.markets.surrenders import MandatoryPartialShareSurrenderEvent
from app.domain.trading import OrderSide, PortfolioSnapshot
from app.event import EventBus, EventType
from app.portfolio import PortfolioEngine
from tests.test_demerger_accounting import at
from tests.test_portfolio_engine import make_bar, make_fill


def event():
    return ShareConsolidationEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600381_consolidation_v1.json").read_bytes()
    )


def surrender():
    return MandatoryPartialShareSurrenderEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600381_surrender_v1.json").read_bytes()
    )


def funded(q="100"):
    bus, emitted = EventBus(), []
    for kind in (EventType.ORDER_CREATED, EventType.ORDER_FILLED, EventType.ORDER_PROPOSAL):
        bus.subscribe(kind, emitted.append)
    p = PortfolioEngine(bus, Decimal(1000000))
    p.apply_fill(
        make_fill(1, OrderSide.BUY, q, "10", symbol="600381.SSE").model_copy(
            update={"timestamp": at("2014-06-24"), "commission": Decimal(0)}
        )
    )
    return p, emitted


@pytest.mark.parametrize(
    "q,new,remaining,basis",
    [
        ("10000", "1600", "1408", "88000"),
        ("100", "16", "14", "875"),
        ("101", "16", "14", "883.75"),
        ("1", "0", "0", "0"),
    ],
)
def test_distinct_historical_legs_reconcile_without_trades(q, new, remaining, basis):
    p, emitted = funded(q)
    cash = p.cash
    with localcontext() as context:
        context.prec = 6
        p.apply_consolidation(event(), at("2014-06-25"), holder_class=event().affected_holder_class)
    consolidated = p.snapshot_at(at("2014-06-25"))
    assert consolidated.positions[0].quantity == Decimal(new)
    assert consolidated.positions[0].aggregate_cost_basis == (
        Decimal(q) * 10 if Decimal(new) else 0
    )
    assert not p.is_orderable("600381.SSE") and not p.marks
    with pytest.raises(ValueError, match="NON_ORDERABLE"):
        p.apply_fill(
            make_fill(1, OrderSide.SELL, "1", "10", symbol="600381.SSE").model_copy(
                update={"timestamp": at("2014-06-25")}
            )
        )
    p.apply_partial_surrender(
        surrender(), at("2014-06-30"), holder_class=surrender().affected_holder_class
    )
    final = p.snapshot_at(at("2014-06-30"))
    assert final.positions[0].quantity == Decimal(remaining)
    assert final.positions[0].aggregate_cost_basis == Decimal(basis)
    assert final.corporate_action_realized_pnl == Decimal(basis) - Decimal(q) * 10
    assert final.realized_pnl == 0 and final.cash == cash and not emitted
    if Decimal(new):
        assert (
            final.consolidation_audits[0].event_checksum
            != final.partial_surrender_audits[0].event_checksum
        )
    else:
        assert not final.partial_surrender_audits  # No remaining entitlement to surrender.
    assert PortfolioSnapshot.model_validate_json(final.model_dump_json()) == final
    # Synthetic raw observation only; not a claim about the historical resumption price/date.
    raw = p.mark_to_market(
        make_bar(1, "20", symbol="600381.SSE").model_copy(update={"timestamp": at("2014-07-02")})
    )
    assert p.is_orderable("600381.SSE")
    assert raw.market_value == Decimal(remaining) * 20
    assert raw.unrealized_pnl == Decimal(remaining) * 20 - Decimal(basis)


def test_consolidation_replay_sources_and_fail_closed():
    e = event()
    assert (
        e.event_checksum
        == e.model_copy(update={"new_shares_per_old_share": Decimal("0.1600")}).event_checksum
    )
    results = []
    for item in (
        e,
        e.model_copy(update={"confirmation_sources": tuple(reversed(e.confirmation_sources))}),
    ):
        p, _ = funded("101")
        p.apply_consolidation(item, at("2014-06-25"), holder_class=item.affected_holder_class)
        results.append(p.snapshot_at(at("2014-06-25")))
        with pytest.raises(ValueError, match="duplicate"):
            p.apply_consolidation(item, at("2014-06-25"), holder_class=item.affected_holder_class)
        p.reset()
        assert not p.consolidation_audits
    assert results[0] == results[1]
    for ratio in (True, 0.16, "NaN", "Infinity", "0", "-1"):
        with pytest.raises(ValueError):
            ShareConsolidationEvent.model_validate(
                {**e.model_dump(), "new_shares_per_old_share": ratio}
            )
    with pytest.raises(ValueError, match="PRE_EFFECTIVE"):
        ShareConsolidationEvent.model_validate(
            {**e.model_dump(), "sources": e.confirmation_sources}
        )
    for changes in ({"holder_consideration": "PRESENT"}, {"official_fraction_method": "EXACT"}):
        p, _ = funded("101")
        before = p.positions, p.cash
        with pytest.raises(ValueError):
            p.apply_consolidation(
                e.model_copy(update=changes), at("2014-06-25"), holder_class=e.affected_holder_class
            )
        assert (p.positions, p.cash) == before


def test_research_session_path_hides_evidence_and_preserves_sequencing():
    from datetime import date

    from app.domain.markets.calendar import TradingCalendar
    from app.execution import FixedCommission
    from app.research.engine import ResearchExecutionEngine
    from app.research.models import ResearchSession

    class NoStrategy:
        strategy_id = "accounting_only"

        def reset(self):
            pass

        def target_for_completed_session(self, session, available_equity):
            assert not session.consolidations and not session.partial_surrenders
            assert session.consolidation_holder_class is None
            return None

    results = []
    for _ in range(2):
        engine = ResearchExecutionEngine(
            NoStrategy(),
            initial_cash=Decimal(1000000),
            commission_model=FixedCommission(),
            calendar=TradingCalendar(market="CN_A", sessions=()),
        )
        engine._portfolio, _ = funded("10000")
        engine._process_session(
            ResearchSession(
                date(2014, 6, 25),
                (),
                (),
                (),
                consolidations=(event(),),
                consolidation_holder_class=event().affected_holder_class,
            )
        )
        engine._process_session(
            ResearchSession(
                date(2014, 6, 30),
                (),
                (),
                (),
                partial_surrenders=(surrender(),),
                surrender_holder_class=surrender().affected_holder_class,
            )
        )
        results.append(engine._portfolio.latest_snapshot)
        assert not engine._oms.orders and not engine._broker.fills
    assert results[0] == results[1]
    assert results[0].positions[0].quantity == 1408
    assert results[0].positions[0].aggregate_cost_basis == 88000
