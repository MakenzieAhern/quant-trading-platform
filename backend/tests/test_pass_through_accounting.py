from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.domain.markets.pass_through import RestructuringBonusPassThroughEvent
from app.domain.trading import OrderSide, PortfolioSnapshot
from app.event import EventBus, EventType
from app.portfolio import PortfolioEngine
from tests.test_demerger_accounting import at
from tests.test_portfolio_engine import make_bar, make_fill


def event():
    return RestructuringBonusPassThroughEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600817_pass_through_v1.json").read_bytes()
    )


def funded(q="100"):
    bus, emitted = EventBus(), []
    for kind in (EventType.ORDER_CREATED, EventType.ORDER_FILLED, EventType.ORDER_PROPOSAL):
        bus.subscribe(kind, emitted.append)
    portfolio = PortfolioEngine(bus, Decimal(100000))
    portfolio.apply_fill(
        make_fill(1, OrderSide.BUY, q, "10", symbol="600817.SSE").model_copy(
            update={"timestamp": at("2012-07-27"), "commission": Decimal(0)}
        )
    )
    # Explicit basis exercises preservation of the existing aggregate-basis representation.
    position = portfolio.positions[0]
    portfolio._positions[position.symbol] = position.model_copy(
        update={"aggregate_cost_basis": Decimal(q) * 10}
    )
    portfolio.snapshot_at(at("2012-07-30"))
    return portfolio, emitted


@pytest.mark.parametrize("q", ["1", "6", "100", "101"])
def test_net_pass_through_is_metadata_only_and_raw_price_has_single_effect(q):
    p, emitted = funded(q)
    before = p.latest_snapshot
    p.apply_pass_through(event(), at("2012-07-31"))
    after = p.snapshot_at(at("2012-07-31"))
    assert after.positions == before.positions
    for field in (
        "cash",
        "equity",
        "realized_pnl",
        "corporate_action_realized_pnl",
        "cumulative_commission",
        "total_pnl",
    ):
        assert getattr(after, field) == getattr(before, field)
    audit = after.pass_through_audits[0]
    assert audit.temporary_bonus_quantity == Decimal(q) * Decimal("0.25")
    assert audit.original_basis == Decimal(q) * 10
    assert not audit.portfolio_cost_basis_allocated and not audit.portfolio_tradable_holding
    assert not emitted
    raw = p.mark_to_market(
        make_bar(1, "8", symbol="600817.SSE").model_copy(update={"timestamp": at("2013-02-08")})
    )
    assert raw.market_value == Decimal(q) * 8
    assert raw.unrealized_pnl == Decimal(q) * -2
    assert raw.corporate_action_realized_pnl == raw.realized_pnl == 0
    assert raw.positions[0].average_price == 10
    assert PortfolioSnapshot.model_validate_json(raw.model_dump_json()) == raw
    with pytest.raises(ValueError):
        p.apply_pass_through(event(), at("2012-07-31"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("original_quantity_preserved", False),
        ("mandatory_transfer", False),
        ("holder_compensation", "PRESENT"),
        ("holder_compensation", "UNRESOLVED"),
        ("tradability_during_pass_through", "PRESENT"),
        ("monetization_during_pass_through", "PRESENT"),
    ],
)
def test_ineligible_variants_fail_before_mutation(field, value):
    p, _ = funded()
    before = p.positions, p.cash, p.pass_through_audits
    e = event().model_copy(update={field: value})
    with pytest.raises(ValueError, match="ELIGIBILITY"):
        p.apply_pass_through(e, at("2012-07-31"))
    assert (p.positions, p.cash, p.pass_through_audits) == before


def test_source_order_replay_and_pre_effective_evidence():
    e = event()
    reordered = e.model_copy(
        update={
            "sources": tuple(reversed(e.sources)),
            "confirmation_sources": tuple(reversed(e.confirmation_sources)),
        }
    )
    assert e.event_checksum == reordered.event_checksum
    assert (
        e.event_checksum == e.model_copy(update={"bonus_ratio": Decimal("0.2500")}).event_checksum
    )
    results = []
    for item in (e, reordered):
        p, _ = funded()
        p.apply_pass_through(item, at("2012-07-31"))
        results.append(p.snapshot_at(at("2012-07-31")))
        with pytest.raises(ValueError, match="duplicate"):
            p.apply_pass_through(item, at("2012-07-31"))
        p.reset()
        assert not p.pass_through_audits
    assert results[0] == results[1]
    with pytest.raises(ValueError, match="PRE_EFFECTIVE"):
        RestructuringBonusPassThroughEvent.model_validate(
            {**e.model_dump(), "sources": e.confirmation_sources}
        )
    for ratio in (0.25, True, "NaN", "Infinity", "0", "-1"):
        with pytest.raises(ValueError):
            RestructuringBonusPassThroughEvent.model_validate(
                {**e.model_dump(), "bonus_ratio": ratio}
            )


def test_temporary_interval_rejects_trading_without_mutation():
    p, _ = funded()
    p.apply_pass_through(event(), at("2012-07-31"))
    before = p.positions, p.cash, p.marks
    for day in ("2012-07-31", "2012-08-01"):
        with pytest.raises(ValueError, match="TRADING_OBSERVATION_CONFLICT"):
            p.mark_to_market(
                make_bar(1, "8", symbol="600817.SSE").model_copy(update={"timestamp": at(day)})
            )
        with pytest.raises(ValueError, match="TRADING_OBSERVATION_CONFLICT"):
            p.apply_fill(
                make_fill(1, OrderSide.SELL, "1", "8", symbol="600817.SSE").model_copy(
                    update={"timestamp": at(day)}
                )
            )
    assert (p.positions, p.cash, p.marks) == before


def test_research_path_strips_future_confirmation_and_rejects_double_leg():
    from app.domain.markets.calendar import TradingCalendar, TradingSession
    from app.execution import FixedCommission
    from app.research.engine import ResearchExecutionEngine
    from app.research.models import ResearchSession

    class NoStrategy:
        strategy_id = "accounting_check_only"

        def reset(self):
            pass

        def target_for_completed_session(self, session, available_equity):
            assert not session.pass_through_events
            return None

    calendar = TradingCalendar(
        market="CN_A",
        sessions=(
            TradingSession(
                session_date=date(2012, 7, 31), is_open=True, source_version="synthetic"
            ),
        ),
    )
    engine = ResearchExecutionEngine(
        NoStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=calendar,
    )
    session = ResearchSession(date(2012, 7, 31), (), (), (), pass_through_events=(event(),))
    first = engine.run((session,))
    assert first == engine.run((session,))
    assert not first.fills and not first.orders
    assert first.snapshots[0].pass_through_audits[0].temporary_bonus_quantity == 0
    with pytest.raises(ValueError, match="ordering"):
        engine.run((replace(session, pass_through_events=(event(), event())),))


def test_raw_adjusted_separation_in_real_session_path():
    from app.domain.markets.calendar import TradingCalendar
    from app.execution import FixedCommission
    from app.research.engine import ResearchExecutionEngine
    from app.research.models import ResearchSession
    from tests.test_research_execution_engine import _session

    class NoStrategy:
        strategy_id = "no_research"

        def reset(self):
            pass

        def target_for_completed_session(self, session, available_equity):
            assert not session.pass_through_events
            return None

    snapshots = []
    for adjusted in ("1", "1000"):
        engine = ResearchExecutionEngine(
            NoStrategy(),
            initial_cash=Decimal(100000),
            commission_model=FixedCommission(),
            calendar=TradingCalendar(market="CN_A", sessions=()),
        )
        # Only test setup owns an imported holding; no production study is created.
        engine._portfolio, _ = funded()
        engine._event_bus.subscribe(EventType.MARKET_DATA, engine._portfolio._on_market_data)
        engine._process_session(
            ResearchSession(date(2012, 7, 31), (), (), (), pass_through_events=(event(),))
        )
        source = _session(date(2013, 2, 8), opening="8").bars[0]
        source = source.model_copy(
            update={"security_id": event().security_id, "adjusted_close": Decimal(adjusted)}
        )
        engine._process_session(ResearchSession(date(2013, 2, 8), (source,), (), ()))
        snapshots.append(engine._portfolio.latest_snapshot)
        assert not engine._broker.fills and not engine._oms.orders
    assert snapshots[0] == snapshots[1]
    assert snapshots[0].market_value == 800
    assert snapshots[0].unrealized_pnl == -200
    assert snapshots[0].corporate_action_realized_pnl == 0
