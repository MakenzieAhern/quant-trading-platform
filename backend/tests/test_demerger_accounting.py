from datetime import UTC, date, datetime
from decimal import Decimal
from itertools import permutations
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.markets.demergers import DemergerEvent
from app.domain.trading import OrderSide, PortfolioSnapshot
from app.event import EventBus, EventType
from app.portfolio import PortfolioEngine, PortfolioError
from tests.test_portfolio_engine import make_bar, make_fill


def at(day):
    return datetime.fromisoformat(day).replace(tzinfo=UTC)


def event():
    return DemergerEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600003_demerger.json").read_bytes()
    )


def retained_parent_event():
    return DemergerEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/600649_demerger.json").read_bytes()
    )


def funded(quantity="1", price="3"):
    bus = EventBus()
    emitted = []
    for kind in (EventType.ORDER_CREATED, EventType.ORDER_FILLED, EventType.ORDER_PROPOSAL):
        bus.subscribe(kind, emitted.append)
    portfolio = PortfolioEngine(bus, Decimal(10000))
    portfolio.apply_fill(
        make_fill(1, OrderSide.BUY, quantity, price, symbol="600003.SSE").model_copy(
            update={"timestamp": at("2009-03-12")}
        )
    )
    portfolio.mark_to_market(
        make_bar(1, "3.87", symbol="600003.SSE").model_copy(update={"timestamp": at("2009-03-13")})
    )
    return portfolio, emitted


@pytest.mark.parametrize("quantity", ["1", "100", "137"])
def test_600003_pending_activation_basis_raw_marks_and_later_sale(quantity):
    p, emitted = funded(quantity)
    before = p.latest_snapshot
    action = event()
    assert sum(s.reference_value for s in action.successors) == Decimal("3.87")
    p.recognize_demerger(action, date(2010, 2, 26), at("2010-02-26"))
    assert p.positions == () and "600003.SSE" not in p.marks
    pending = p.pending_demergers[0]
    assert not pending.tradable and not pending.orderable and not pending.executable
    assert pending.valuation_label == "CORPORATE_ACTION_PENDING_CARRY_VALUE"
    for day in ("2010-02-26", "2010-03-01", "2010-03-18"):
        p.activate_demergers(date.fromisoformat(day), {}, at(day))
        snapshot = p.snapshot_at(at(day))
        assert snapshot.cash == before.cash
        assert snapshot.equity == before.equity
        assert snapshot.realized_pnl == before.realized_pnl == 0
        assert snapshot.market_value == Decimal(quantity) * Decimal("3.87")
        assert PortfolioSnapshot.model_validate_json(snapshot.model_dump_json()) == snapshot
    with pytest.raises(PortfolioError, match="NON_ORDERABLE"):
        p.apply_fill(
            make_fill(2, OrderSide.SELL, quantity, "3.87", symbol="600003.SSE").model_copy(
                update={"timestamp": at("2010-03-18")}
            )
        )
    # Arbitrary synthetic observed openings, deliberately different from references.
    p.activate_demergers(
        date(2010, 3, 19), {"601188.SSE": Decimal(5), "601518.SSE": Decimal(4)}, at("2010-03-19")
    )
    assert not p.pending_demergers
    first, second = p.positions
    basis = Decimal(quantity) * Decimal(3)
    assert first.quantity == second.quantity == Decimal(quantity)
    assert first.aggregate_cost_basis == basis * Decimal("2.08") / Decimal("3.87")
    assert first.aggregate_cost_basis + second.aggregate_cost_basis == basis
    assert p.snapshot_at(at("2010-03-19")).market_value == Decimal(quantity) * 9
    assert p.cash == before.cash and emitted == []
    # All cost is realized only on later ordinary sales, never at conversion.
    for index, symbol in enumerate(("601188.SSE", "601518.SSE"), 3):
        p.apply_fill(
            make_fill(index, OrderSide.SELL, quantity, "6", symbol=symbol).model_copy(
                update={"timestamp": at("2010-03-22")}
            )
        )
    final = p.snapshot_at(at("2010-03-22"))
    assert final.realized_pnl == Decimal(quantity) * 12 - basis
    assert all(x.aggregate_cost_basis == 0 for x in p.positions)


def test_replay_order_and_no_future_price_basis():
    expected = None
    for successors in permutations(event().successors):
        action = event().model_copy(update={"successors": successors})
        assert action.event_checksum == event().event_checksum
        p, _ = funded()
        p.recognize_demerger(action, date(2010, 2, 26), at("2010-02-26"))
        pending = p.snapshot_at(at("2010-03-01"))
        assert "reference_value" not in pending.model_dump_json()
        p.activate_demergers(
            date(2010, 3, 19),
            dict(reversed(list({"601188.SSE": Decimal(50), "601518.SSE": Decimal(1)}.items()))),
            at("2010-03-19"),
        )
        actual = [(x.symbol, x.quantity, x.aggregate_cost_basis) for x in p.positions]
        if expected is None:
            expected = actual
        assert actual == expected
        assert actual[0][2] == Decimal(3) * Decimal("2.08") / Decimal("3.87")
        p.reset()
        assert p.positions == p.pending_demergers == ()


def test_600649_retained_parent_floor_replay_and_zero_whole_writeoff():
    action = retained_parent_event()
    for quantity in (Decimal(100), Decimal(1)):
        p = PortfolioEngine(EventBus(), Decimal(10000))
        p.apply_fill(
            make_fill(1, OrderSide.BUY, str(quantity), "20", symbol="600649.SSE").model_copy(
                update={"timestamp": at("2016-12-02")}
            )
        )
        p.mark_to_market(
            make_bar(1, "20.34", symbol="600649.SSE").model_copy(
                update={"timestamp": at("2016-12-05")}
            )
        )
        p.recognize_demerger(action, action.application_date, at("2017-03-31"))
        p.activate_demergers(
            action.application_date,
            {"600649.SSE": Decimal("18.31"), "601200.SSE": Decimal("24.41")},
            at("2017-03-31"),
        )
        audits = p.demerger_rounding_audits
        assert len(audits) == 2 and not p.pending_demergers
        if quantity == 100:
            positions = {position.symbol: position for position in p.positions}
            assert {symbol: position.quantity for symbol, position in positions.items()} == {
                "600649.SSE": Decimal(78),
                "601200.SSE": Decimal(21),
            }
            assert sum(position.aggregate_cost_basis for position in positions.values()) == 2000
            assert p.is_orderable("600649.SSE") and p.is_orderable("601200.SSE")
            assert sum(audit.basis_written_off for audit in audits) == 0
        else:
            assert not p.positions
            assert sum(audit.basis_written_off for audit in audits) == 20
            assert p.snapshot_at(at("2017-03-31")).corporate_action_realized_pnl == -20


def test_missing_price_activation_is_atomic_and_other_methods_fail_closed():
    p, _ = funded()
    p.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
    with pytest.raises(PortfolioError, match="RAW_PRICE_UNAVAILABLE"):
        p.activate_demergers(date(2010, 3, 19), {"601188.SSE": Decimal(5)}, at("2010-03-19"))
    assert p.positions == () and len(p.pending_demergers) == 1
    for method in (
        "UNRESOLVED",
        "FIRST_COMMON_MARKET_VALUE",
        "OFFICIAL_TAX_ALLOCATION",
        "OFFICIAL_ASSET_ALLOCATION",
    ):
        with pytest.raises(ValueError, match="ALLOCATION_UNRESOLVED"):
            event().model_copy(update={"basis_allocation": method}).require_supported()
    with pytest.raises(ValidationError):
        event().effective_date = date(2010, 1, 1)


def test_zero_holdings_never_create_entitlement_or_cash():
    p = PortfolioEngine(EventBus(), Decimal(10000))
    p.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
    assert p.pending_demergers == p.positions == ()
    assert p.cash == 10000 and not p.is_orderable("600003.SSE")
    assert not p.is_orderable("601188.SSE")
    p.activate_demergers(date(2010, 3, 19), {}, at("2010-03-19"))
    assert p.is_orderable("601188.SSE")


def test_dates_fractional_quantity_and_duplicate_events_fail_closed():
    p, _ = funded()
    with pytest.raises(PortfolioError, match="effective session"):
        p.recognize_demerger(event(), date(2010, 2, 25), at("2010-02-25"))
    stale = event().model_copy(update={"parent_last_trading_date": date(2009, 3, 12)})
    with pytest.raises(PortfolioError, match="last raw close"):
        p.recognize_demerger(stale, date(2010, 2, 26), at("2010-02-26"))
    fractional = event().model_copy(
        update={
            "successors": tuple(
                s.model_copy(update={"conversion_ratio": Decimal("0.5")})
                for s in event().successors
            )
        }
    )
    with pytest.raises(PortfolioError, match="FRACTIONAL_QUANTITY_UNRESOLVED"):
        p.recognize_demerger(fractional, date(2010, 2, 26), at("2010-02-26"))
    assert not p.pending_demergers and len(p.positions) == 1
    p.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
    with pytest.raises(PortfolioError, match="duplicate demerger"):
        p.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
    values = event().model_dump(mode="json")
    values["conversion_source"]["published_on"] = "2010-02-27"
    with pytest.raises(ValidationError, match="EVIDENCE_NOT_AVAILABLE"):
        DemergerEvent.model_validate(values)
    late = event().model_copy(
        update={
            "allocation_sources": tuple(
                s.model_copy(update={"published_on": date(2010, 3, 19)})
                for s in event().allocation_sources
            )
        }
    )
    with pytest.raises(ValueError, match="PRELISTING"):
        late.require_supported()


def test_pending_carry_counts_as_risk_exposure_but_not_buying_power():
    from app.domain.risk import RiskConfig, RiskReasonCode
    from app.risk import RiskEngine
    from tests.test_risk_engine import proposal

    p, _ = funded("100")
    p.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
    snapshot = p.snapshot_at(at("2010-02-26"))
    intent = proposal(quantity="1").model_copy(update={"signal_timestamp": snapshot.timestamp})
    decision = RiskEngine(RiskConfig(max_gross_exposure=Decimal(400))).evaluate(
        intent, snapshot, {"AAPL": Decimal(20)}
    )
    assert decision.reason_code is RiskReasonCode.GROSS_EXPOSURE_LIMIT
    assert decision.projected_gross_exposure == decision.projected_net_exposure == Decimal(407)
    assert decision.projected_cash == snapshot.cash - 20


def test_partial_successor_sales_conserve_basis_and_preserve_parent_realizations():
    p, _ = funded("138")
    p.apply_fill(
        make_fill(10, OrderSide.SELL, "1", "4", symbol="600003.SSE").model_copy(
            update={"timestamp": at("2009-03-13")}
        )
    )
    p.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
    assert p.snapshot_at(at("2010-02-26")).realized_pnl == 1
    p.activate_demergers(
        date(2010, 3, 19), {"601188.SSE": Decimal(5), "601518.SSE": Decimal(4)}, at("2010-03-19")
    )
    for symbol in ("601188.SSE", "601518.SSE"):
        for count, qty in enumerate(("37", "100")):
            p.apply_fill(
                make_fill(20 + count, OrderSide.SELL, qty, "6", symbol=symbol).model_copy(
                    update={"timestamp": at("2010-03-22")}
                )
            )
    final = p.snapshot_at(at("2010-03-22"))
    assert final.realized_pnl == 1 + 137 * (12 - 3)
    assert sum(x.aggregate_cost_basis for x in p.positions) == 0


def test_research_engine_orders_ownership_before_strategy_and_replays():
    from dataclasses import replace

    from app.domain.markets.calendar import TradingCalendar, TradingSession
    from app.domain.markets.identifiers import Market
    from app.execution import FixedCommission
    from app.research import PortfolioTarget, ResearchExecutionEngine, ResearchSession
    from tests.test_research_execution_engine import SECURITY_ID, OneTargetStrategy, _session

    # Synthetic sessions exercise the real shared engine, not a historical study.
    action = event().model_copy(
        update={
            "parent_security": SECURITY_ID,
            "parent_last_close": Decimal("9.9"),
            "parent_last_trading_date": date(2024, 1, 3),
            "effective_date": date(2024, 1, 4),
            "completion_date": date(2024, 1, 5),
            "successors": tuple(
                s.model_copy(update={"listing_date": date(2024, 1, 8)}) for s in event().successors
            ),
            "allocation_sources": tuple(
                s.model_copy(update={"published_on": date(2024, 1, 5)})
                for s in event().allocation_sources
            ),
        }
    )
    observed = []

    class Strategy(OneTargetStrategy):
        def target_for_completed_session(self, session, available_equity):
            assert session.demergers == ()
            target = super().target_for_completed_session(session, available_equity)
            if session.trading_date == date(2024, 1, 8):
                observed.append(tuple((p.symbol, p.quantity) for p in engine._portfolio.positions))
                return PortfolioTarget(positions=(), residual_cash=available_equity)
            return target

    days = [date(2024, 1, n) for n in (2, 3, 4, 5, 8, 9)]
    calendar = TradingCalendar(
        market=Market.CN_A,
        sessions=tuple(
            TradingSession(session_date=day, is_open=True, source_version="synthetic")
            for day in days
        ),
    )
    engine = ResearchExecutionEngine(
        Strategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=calendar,
    )
    sessions = [_session(days[0], opening="10"), _session(days[1], opening="9.9")]
    for day in days[2:4]:
        sessions.append(
            ResearchSession(
                trading_date=day,
                bars=(),
                statuses=(),
                buy_lot_sizes=(),
                demergers=(action,) if day == days[2] else (),
            )
        )
    for day in days[4:]:
        base = _session(day, opening="5")
        ids = [s.security_id for s in action.successors]
        sessions.append(
            replace(
                base,
                bars=tuple(
                    base.bars[0].model_copy(update={"security_id": sid, "pre_close": Decimal(5)})
                    for sid in ids
                ),
                statuses=tuple(
                    base.statuses[0].model_copy(
                        update={
                            "status": base.statuses[0].status.model_copy(
                                update={"security_id": sid}
                            )
                        }
                    )
                    for sid in ids
                ),
                trading_rules=tuple(
                    base.trading_rules[0].model_copy(update={"security_id": sid}) for sid in ids
                ),
            )
        )
    result = engine.run(sessions)
    repeated = engine.run([replace(s, bars=tuple(reversed(s.bars))) for s in sessions])
    assert result == repeated
    assert observed == [(("601188.SSE", Decimal(100)), ("601518.SSE", Decimal(100)))] * 2
    assert [f.side for f in result.fills] == [OrderSide.BUY, OrderSide.SELL, OrderSide.SELL]
    assert len(result.orders) == len(result.proposals) == 3
    pending = [s for s in result.snapshots if s.pending_demergers]
    assert len(pending) == 2 and all(s.market_value == Decimal(990) for s in pending)
    assert result.snapshots[-1].realized_pnl == Decimal(10)


def test_evidence_audit_replays_and_detects_changed_original_bytes(tmp_path):
    import hashlib
    import json

    from scripts.audit_demerger_evidence import audit

    sources, documents = [], []
    for index, source in enumerate((event().conversion_source, *event().allocation_sources)):
        raw = b"%PDF synthetic audit bytes " + str(index).encode()
        source = source.model_copy(update={"sha256": hashlib.sha256(raw).hexdigest()})
        path = tmp_path / f"{index}.pdf"
        path.write_bytes(raw)
        meta = dict(
            url=source.url,
            sha256=source.sha256,
            retrieved_at_utc=source.retrieved_at.isoformat(),
            http_status=200,
        )
        path.with_suffix(".pdf.meta.json").write_text(json.dumps(meta))
        documents.append(dict(path=path.name, published_on=source.published_on.isoformat(), **meta))
        sources.append(source)
    action = event().model_copy(
        update={"conversion_source": sources[0], "allocation_sources": tuple(sources[1:])}
    )
    review = dict(policy="CN_A_MANDATORY_DEMERGER_POLICY_V1", documents=documents)
    receipt = audit(review, action, tmp_path)
    assert receipt == audit({**review, "documents": list(reversed(documents))}, action, tmp_path)
    (tmp_path / "0.pdf").write_bytes(b"%PDF changed")
    with pytest.raises(ValueError, match="SOURCE_BYTES_MISMATCH"):
        audit(review, action, tmp_path)
