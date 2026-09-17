import json
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.domain.markets.mergers import FractionalShareMethod, MergerEvent
from app.domain.trading import OrderSide, PortfolioSnapshot
from app.event import EventBus, EventType
from app.portfolio import PortfolioEngine, PortfolioError
from tests.test_demerger_accounting import at
from tests.test_portfolio_engine import make_bar, make_fill


def event():
    return MergerEvent.model_validate_json(
        (Path(__file__).parent / "fixtures/000024_merger.json").read_bytes()
    )


def funded(quantity="100"):
    bus = EventBus()
    emitted = []
    for kind in (EventType.ORDER_CREATED, EventType.ORDER_FILLED, EventType.ORDER_PROPOSAL):
        bus.subscribe(kind, emitted.append)
    portfolio = PortfolioEngine(bus, Decimal(100000))
    # Synthetic accounting inputs, not actual trades or a historical strategy run.
    portfolio.apply_fill(
        make_fill(1, OrderSide.BUY, quantity, "30", symbol="000024.SZSE").model_copy(
            update={"timestamp": at("2015-12-04")}
        )
    )
    portfolio.mark_to_market(
        make_bar(1, "40.50", symbol="000024.SZSE").model_copy(
            update={"timestamp": at("2015-12-07")}
        )
    )
    return portfolio, emitted


@pytest.mark.parametrize(
    "quantity,whole,remainder",
    [("100", "160", "0.0800"), ("200", "320", "0.1600"), ("1250", "2001", "0.0000")],
)
def test_000024_floor_basis_cash_pnl_and_materiality(quantity, whole, remainder):
    portfolio, emitted = funded(quantity)
    before = portfolio.latest_snapshot
    portfolio.recognize_merger(event(), date(2015, 12, 30), at("2015-12-30"))
    pending = portfolio.snapshot_at(at("2015-12-30"))
    assert not pending.positions and len(pending.pending_mergers) == 1
    claim = pending.pending_mergers[0]
    assert not claim.tradable and not claim.orderable and not claim.executable
    assert claim.whole_successor_quantity == Decimal(whole)
    assert claim.valuation_label == "CORPORATE_ACTION_PENDING_CARRY_VALUE"
    assert pending.cash == before.cash and pending.equity == before.equity
    assert pending.realized_pnl == 0
    assert PortfolioSnapshot.model_validate_json(pending.model_dump_json()) == pending
    assert portfolio.merger_materiality()["aggregate_estimated_discarded_value"] is None
    # First opening and later high are synthetic raw observations, not reference/adjusted prices.
    portfolio.activate_mergers(date(2015, 12, 30), {"001979.SZSE": Decimal(25)}, at("2015-12-30"))
    position = portfolio.positions[0]
    basis = Decimal(quantity) * 30
    assert position.quantity == Decimal(whole)
    assert position.aggregate_cost_basis == basis
    assert position.average_price == basis / Decimal(whole)
    assert portfolio.cash == before.cash and emitted == []
    assert portfolio.snapshot_at(at("2015-12-30")).realized_pnl == 0
    audit = portfolio.merger_rounding_audits[0]
    assert audit.theoretical_successor_quantity == Decimal(quantity) * Decimal("1.6008")
    assert audit.fractional_remainder == Decimal(remainder)
    assert audit.first_available_raw_price == 25
    assert audit.maximum_estimated_discarded_value == Decimal(remainder) * 25
    portfolio.mark_to_market(
        make_bar(2, "28", symbol="001979.SZSE").model_copy(
            update={"timestamp": at("2015-12-31"), "high": Decimal(30)}
        )
    )
    audit = portfolio.merger_rounding_audits[0]
    assert audit.first_available_raw_price == 25 and audit.maximum_observed_raw_price == 30
    assert audit.maximum_estimated_discarded_value == Decimal(remainder) * 30
    assert audit.maximum_floor_ceil_value_difference == (30 if Decimal(remainder) else 0)
    materiality = portfolio.merger_materiality()
    assert materiality["total_discarded_fractional_shares"] == Decimal(remainder)
    assert materiality["aggregate_estimated_discarded_value"] == Decimal(remainder) * 30
    assert portfolio.positions[0].quantity == Decimal(whole)  # CEIL never reaches holdings.
    portfolio.apply_fill(
        make_fill(2, OrderSide.SELL, whole, "26", symbol="001979.SZSE").model_copy(
            update={"timestamp": at("2016-01-04")}
        )
    )
    final = portfolio.snapshot_at(at("2016-01-04"))
    assert final.realized_pnl == Decimal(whole) * 26 - basis
    assert final.positions[0].aggregate_cost_basis == 0


def test_pending_gap_missing_raw_atomicity_and_replay():
    action = event().model_copy(update={"successor_listing_date": date(2016, 1, 4)})
    results = []
    for sources in (action.sources, tuple(reversed(action.sources))):
        p, _ = funded()
        reordered = action.model_copy(update={"sources": sources})
        assert reordered.event_checksum == action.event_checksum
        with localcontext() as context:
            context.prec = 6
            p.recognize_merger(reordered, date(2015, 12, 30), at("2015-12-30"))
            p.activate_mergers(date(2015, 12, 31), {"001979.SZSE": Decimal(99)}, at("2015-12-31"))
            assert not p.positions and p.merger_rounding_audits[0].first_available_raw_price is None
            assert not p.is_orderable("001979.SZSE") and not p.is_orderable("000024.SZSE")
            with pytest.raises(PortfolioError, match="RAW_PRICE_UNAVAILABLE"):
                p.activate_mergers(date(2016, 1, 4), {}, at("2016-01-04"))
            assert len(p.pending_mergers) == 1
            p.activate_mergers(date(2016, 1, 4), {"001979.SZSE": Decimal(25)}, at("2016-01-04"))
            results.append(p.snapshot_at(at("2016-01-04")))
        p.reset()
        assert not p.pending_mergers and not p.merger_rounding_audits
    assert results[0] == results[1]


def test_merger_zero_holdings_and_existing_successor_basis():
    p = PortfolioEngine(EventBus(), Decimal(100000))
    p.recognize_merger(event(), date(2015, 12, 30), at("2015-12-30"))
    p.activate_mergers(date(2015, 12, 30), {}, at("2015-12-30"))
    assert not p.positions and not p.merger_rounding_audits and p.cash == 100000
    p, _ = funded()
    action = event().model_copy(update={"successor_listing_date": date(2015, 1, 1)})
    p.apply_fill(
        make_fill(5, OrderSide.BUY, "10", "20", symbol="001979.SZSE").model_copy(
            update={"timestamp": at("2015-12-07")}
        )
    )
    p.recognize_merger(action, date(2015, 12, 30), at("2015-12-30"))
    p.activate_mergers(date(2015, 12, 30), {"001979.SZSE": Decimal(25)}, at("2015-12-30"))
    assert p.positions[0].quantity == 170 and p.positions[0].aggregate_cost_basis == 3200


def test_merger_unresolved_variants_and_zero_whole_basis_fail_closed():
    values = event().model_dump(mode="json")
    values["conversion_ratio"] = 1.6008
    with pytest.raises(ValidationError, match="binary float"):
        MergerEvent.model_validate(values)
    for method in (
        FractionalShareMethod.UNRESOLVED,
        FractionalShareMethod.OFFICIAL_CASH_IN_LIEU,
        FractionalShareMethod.OFFICIAL_DETERMINISTIC_ALLOCATION,
    ):
        with pytest.raises(ValueError, match="VARIANT_UNRESOLVED"):
            event().model_copy(update={"official_fractional_method": method}).require_supported()
    # Official 600005 ratio; hypothetical odd-share boundary, not a strategy holding.
    shrinking_ratio = event().model_copy(update={"conversion_ratio": Decimal("0.56")})
    assert shrinking_ratio.quantities(Decimal(100)) == (Decimal(56), Decimal(56), Decimal(0))
    with pytest.raises(ValueError, match="ZERO_WHOLE_SHARES_BASIS_UNRESOLVED"):
        shrinking_ratio.quantities(Decimal(1))
    p, _ = funded("1")
    before = p.snapshot_at(at("2015-12-07"))
    with pytest.raises(ValueError, match="ZERO_WHOLE_SHARES_BASIS_UNRESOLVED"):
        p.recognize_merger(shrinking_ratio, date(2015, 12, 30), at("2015-12-30"))
    assert p.snapshot_at(at("2015-12-07")) == before
    assert not p.pending_mergers and not p.merger_rounding_audits
    with pytest.raises(ValidationError):
        event().conversion_ratio = Decimal(2)


def test_merger_pending_counts_as_risk_exposure_not_cash():
    from app.domain.risk import RiskConfig, RiskReasonCode
    from app.risk import RiskEngine
    from tests.test_risk_engine import proposal

    p, _ = funded()
    p.recognize_merger(event(), date(2015, 12, 30), at("2015-12-30"))
    snapshot = p.snapshot_at(at("2015-12-30"))
    intent = proposal(quantity="1").model_copy(update={"signal_timestamp": snapshot.timestamp})
    decision = RiskEngine(RiskConfig(max_gross_exposure=Decimal(4060))).evaluate(
        intent, snapshot, {"AAPL": Decimal(20)}
    )
    assert decision.reason_code is RiskReasonCode.GROSS_EXPOSURE_LIMIT
    assert decision.projected_gross_exposure == decision.projected_net_exposure == Decimal(4070)
    assert decision.projected_cash == snapshot.cash - 20


def test_research_engine_merger_before_strategy_and_deterministic_replay():
    from dataclasses import replace

    from app.domain.markets.calendar import TradingCalendar, TradingSession
    from app.domain.markets.identifiers import Market
    from app.execution import FixedCommission
    from app.research import ResearchExecutionEngine, ResearchSession
    from tests.test_research_execution_engine import SECURITY_ID, OneTargetStrategy, _session

    # Synthetic sessions test engine ordering, not a historical study.
    action = event().model_copy(
        update={
            "parent_security": SECURITY_ID,
            "parent_last_trading_date": date(2024, 1, 3),
            "record_date": date(2024, 1, 3),
            "effective_date": date(2024, 1, 4),
            "successor_listing_date": date(2024, 1, 8),
        }
    )
    observed = []

    class Strategy(OneTargetStrategy):
        def target_for_completed_session(self, session, available_equity):
            assert session.mergers == () and session.demergers == ()
            if session.trading_date == date(2024, 1, 8):
                observed.append(tuple((p.symbol, p.quantity) for p in engine._portfolio.positions))
                return None
            return super().target_for_completed_session(session, available_equity)

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
                mergers=(action,) if day == days[2] else (),
            )
        )
    sid = action.successor_security
    for day in days[4:]:
        base = _session(day, opening="5")
        sessions.append(
            replace(
                base,
                bars=(
                    base.bars[0].model_copy(update={"security_id": sid, "pre_close": Decimal(5)}),
                ),
                statuses=(
                    base.statuses[0].model_copy(
                        update={
                            "status": base.statuses[0].status.model_copy(
                                update={"security_id": sid}
                            )
                        }
                    ),
                ),
                trading_rules=(base.trading_rules[0].model_copy(update={"security_id": sid}),),
            )
        )
    result = engine.run(sessions)
    assert engine.run(sessions) == result
    assert observed == [(("001979.SZSE", Decimal(160)),)] * 2
    assert [f.side for f in result.fills] == [OrderSide.BUY]
    assert len(result.orders) == len(result.proposals) == 1
    pending = [s for s in result.snapshots if s.pending_mergers]
    assert len(pending) == 2 and all(s.market_value == Decimal(990) for s in pending)
    assert result.snapshots[-1].merger_rounding_audits[0].fractional_remainder == Decimal("0.08")


def test_merger_source_audit_checksum_and_order(tmp_path):
    import hashlib
    import json

    from app.domain.markets.mergers import MERGER_POLICY
    from scripts.audit_merger_evidence import audit

    sources, documents = [], []
    for index, source in enumerate(event().sources):
        raw = b"%PDF synthetic merger source " + str(index).encode()
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
    action = event().model_copy(update={"sources": tuple(sources)})
    review = dict(policy=MERGER_POLICY, documents=documents)
    receipt = audit(review, action, tmp_path)
    assert receipt == audit(
        {**review, "documents": list(reversed(documents))},
        action.model_copy(update={"sources": tuple(reversed(sources))}),
        tmp_path,
    )
    (tmp_path / "0.pdf").write_bytes(b"%PDF changed")
    with pytest.raises(ValueError, match="SOURCE_BYTES_MISMATCH"):
        audit(review, action, tmp_path)


def test_reciprocal_official_ratio_uses_exact_fraction_before_floor():
    import json
    from fractions import Fraction

    original = event()
    assert (
        original.model_copy(update={"conversion_denominator": Decimal("1.00")}).event_checksum
        == original.event_checksum
    )
    action = original.model_copy(
        update={"conversion_ratio": Decimal(1), "conversion_denominator": Decimal("2.90")}
    )
    for precision in (3, 28, 60):
        with localcontext() as context:
            context.prec = precision
            assert action.quantities(Decimal(29)) == (Decimal(10), Decimal(10), Decimal(0))
            assert action.theoretical_fraction(Decimal(100)) == Fraction(1000, 29)
            assert action.quantities(Decimal(100))[1] == 34
            p, emitted = funded()
            cash = p.cash
            p.recognize_merger(action, date(2015, 12, 30), at("2015-12-30"))
            audit = p.merger_rounding_audits[0]
            assert (audit.exact_theoretical_numerator, audit.exact_theoretical_denominator) == (
                1000,
                29,
            )
            p.activate_mergers(date(2015, 12, 30), {"001979.SZSE": Decimal(25)}, at("2015-12-30"))
            assert p.positions[0].quantity == 34 and p.positions[0].aggregate_cost_basis == 3000
            assert p.cash == cash and emitted == []
            assert (
                PortfolioSnapshot.model_validate_json(
                    p.snapshot_at(at("2015-12-30")).model_dump_json()
                ).merger_rounding_audits
                == p.merger_rounding_audits
            )
    with pytest.raises(ValueError, match="whole long"):
        action.quantities(Decimal("1.5"))
    values = original.model_dump(mode="json")
    values["conversion_denominator"] = 2.9
    with pytest.raises(ValidationError, match="binary float"):
        MergerEvent.model_validate(values)
    cases = json.loads(
        (Path(__file__).parent / "fixtures/reciprocal_merger_ratios.json").read_bytes()
    )
    for case in cases["cases"]:
        ratio_only = original.model_copy(
            update={
                "conversion_ratio": Decimal(case["numerator"]),
                "conversion_denominator": Decimal(case["denominator"]),
            }
        )
        assert ratio_only.quantities(Decimal(case["exact_parent_quantity"]))[1] == Decimal(
            case["exact_successor_quantity"]
        )
        assert ratio_only.quantities(Decimal(100))[1] == Decimal(
            case["hundred_parent_whole_quantity"]
        )


def test_cross_exchange_identity_routing_preserves_same_exchange_event_identity():
    from scripts.reconcile_merger_implementation_batch import event_from_review

    review = json.loads(
        (Path(__file__).parent / "fixtures/merger_implementation_batch_v1.json").read_bytes()
    )["cases"][0]
    legacy = event_from_review(review)
    explicit = dict(review, parent_exchange="SZSE", successor_exchange="SZSE")
    assert event_from_review(explicit).event_checksum == legacy.event_checksum
    # Synthetic routing fixture, not source evidence for an actual merger.
    cross = dict(review, successor="600000", parent_exchange="SZSE", successor_exchange="SSE")
    assert str(event_from_review(cross).successor_security) == "CN-A:SSE:600000"
    test_reviewed_merger_batch_reuses_basis_floor_and_no_election_policy(cross)


def test_review_adapter_preserves_reciprocal_terms_and_activation_evidence():
    from scripts.reconcile_merger_implementation_batch import event_from_review

    review = json.loads(
        (Path(__file__).parent / "fixtures/merger_implementation_batch_v1.json").read_bytes()
    )["cases"][0]
    source = event_from_review(review).sources[0].model_dump(mode="json")
    reciprocal = dict(
        review, conversion_ratio="1", conversion_denominator="2.90", activation_sources=[source]
    )
    action = event_from_review(reciprocal)
    assert action.quantities(Decimal(29))[1] == 10
    assert action.activation_sources[0].sha256 == source["sha256"]
    test_reviewed_merger_batch_reuses_basis_floor_and_no_election_policy(reciprocal)


def test_official_rounded_ratio_is_not_recomputed_from_exchange_prices():
    # 000562 implementation, 2015-01-22, PDF pages 3-4; official ratio has nine decimals.
    # Source SHA: aaa254af495f145537662817acb96d646990f626a84754cd90f2e84fa1f11b6d.
    official = event().model_copy(update={"conversion_ratio": Decimal("2.049382716")})
    recomputed = event().model_copy(
        update={"conversion_ratio": Decimal("9.96"), "conversion_denominator": Decimal("4.86")}
    )
    for precision in (3, 28, 60):
        with localcontext() as context:
            context.prec = precision
            assert official.quantities(Decimal(81))[1] == 165
            assert recomputed.quantities(Decimal(81))[1] == 166


def test_000418_official_terms_fail_closed_on_earlier_ratio():
    from scripts.audit_merger_000418 import TERMS, require_terms

    pages = {
        path: {page: " ".join(terms) for page, terms in expected.items()}
        for path, expected in TERMS.items()
    }
    require_terms(pages)
    final_notice = next(path for path in pages if path.startswith("batch-v1/pdf/"))
    pages[final_notice][3] = pages[final_notice][3].replace("1:1.15144821", "1:1.2110")
    with pytest.raises(ValueError, match="OFFICIAL_MERGER_TERM_MISMATCH"):
        require_terms(pages)


def test_600832_official_terms_fail_closed_on_cash_choice_and_ratio():
    from scripts.audit_merger_600832 import TERMS, require_terms

    pages = {
        path: {page: " ".join(terms) for page, terms in expected.items()}
        for path, expected in TERMS.items()
    }
    require_terms(pages)
    cash = next(path for path in pages if "cash-choice" in path)
    pages[cash][0] = "有异议股东申报行使现金选择权"
    with pytest.raises(ValueError, match="OFFICIAL_MERGER_TERM_MISMATCH"):
        require_terms(pages)
    pages = {
        path: {page: " ".join(terms) for page, terms in expected.items()}
        for path, expected in TERMS.items()
    }
    report = next(path for path in pages if "revised-merger-report" in path)
    pages[report][46] = "换股比例为3.00:1"
    with pytest.raises(ValueError, match="OFFICIAL_MERGER_TERM_MISMATCH"):
        require_terms(pages)


def test_600631_official_terms_fail_closed_on_cash_choice():
    from scripts.audit_merger_600631 import TERMS, require_terms

    pages = {
        path: {page: " ".join(terms) for page, terms in expected.items()}
        for path, expected in TERMS.items()
    }
    require_terms(pages)
    cash = next(path for path in pages if "cash-choice-result" in path)
    pages[cash][0] = "有股东申报行使现金选择权"
    with pytest.raises(ValueError, match="OFFICIAL_MERGER_TERM_MISMATCH"):
        require_terms(pages)


@pytest.mark.parametrize("parent", ["600607", "600842"])
def test_2010_dual_parent_official_terms_fail_closed_on_ratio(parent):
    from scripts.audit_merger_2010_dual_parent import COMMON_TERMS, PARENT_TERMS, require_terms

    pages = {
        path: {page: " ".join(terms) for page, terms in expected.items()}
        for path, expected in {**COMMON_TERMS, **PARENT_TERMS[parent]}.items()
    }
    require_terms(pages, parent)
    report = next(path for path in pages if "merger-report" in path)
    ratio = "1:1.61" if parent == "600607" else "1:0.96"
    pages[report][81] = pages[report][81].replace(ratio, "1:0.95")
    with pytest.raises(ValueError, match="OFFICIAL_MERGER_TERM_MISMATCH"):
        require_terms(pages, parent)


@pytest.mark.parametrize(
    "review",
    [
        row
        for name in (
            "merger_implementation_batch_v1.json",
            "merger_suspension_boundary_batch_v2.json",
            "merger_suspension_boundary_batch_v3.json",
            "merger_suspension_boundary_batch_v4.json",
            "merger_suspension_boundary_batch_v5.json",
            "merger_suspension_boundary_batch_v6.json",
        )
        for row in json.loads((Path(__file__).parent / "fixtures" / name).read_bytes())["cases"]
    ]
    + [
        json.loads(
            (Path(__file__).parent / "fixtures/merger_000418_recovery_v1.json").read_bytes()
        )["case"]
    ]
    + [
        json.loads(
            (Path(__file__).parent / "fixtures/merger_600832_recovery_v1.json").read_bytes()
        )["case"]
    ]
    + [
        json.loads(
            (Path(__file__).parent / "fixtures/merger_600631_recovery_v1.json").read_bytes()
        )["case"]
    ]
    + [
        json.loads(
            (Path(__file__).parent / f"fixtures/merger_{parent}_recovery_v1.json").read_bytes()
        )["case"]
        for parent in ("600607", "600842")
    ],
    ids=lambda r: r["parent"],
)
def test_reviewed_merger_batch_reuses_basis_floor_and_no_election_policy(review):
    from scripts.reconcile_merger_implementation_batch import event_from_review

    action = event_from_review(review)
    assert MergerEvent.model_validate_json(action.model_dump_json()) == action
    assert action.activation_date >= action.effective_date
    assert all(source.published_on < action.effective_date for source in action.sources)
    assert (
        action.event_checksum
        == action.model_copy(update={"sources": tuple(reversed(action.sources))}).event_checksum
    )
    for quantity in (Decimal(1), Decimal(81), Decimal(100)):
        bus, emitted = EventBus(), []
        bus.subscribe(EventType.ORDER_CREATED, emitted.append)
        bus.subscribe(EventType.ORDER_FILLED, emitted.append)
        portfolio = PortfolioEngine(bus, Decimal(10000))
        exchange = review.get("exchange", "SZSE")
        parent = review["parent"] + "." + review.get("parent_exchange", exchange)
        successor_code = (
            review.get("successor_security_id", "").split(":")[-1] or review["successor"]
        )
        successor = successor_code + "." + review.get("successor_exchange", exchange)
        portfolio.apply_fill(
            make_fill(1, OrderSide.BUY, str(quantity), "10", symbol=parent).model_copy(
                update={"timestamp": at(review["parent_last_trading_date"])}
            )
        )
        portfolio.mark_to_market(
            make_bar(1, "10", symbol=parent).model_copy(
                update={"timestamp": at(review["parent_last_trading_date"])}
            )
        )
        cash = portfolio.cash
        portfolio.recognize_merger(action, action.effective_date, at(review["effective_date"]))
        portfolio.activate_mergers(
            action.activation_date, {successor: Decimal(20)}, at(review["effective_date"])
        )
        _, whole, _ = action.quantities(quantity)
        assert portfolio.cash == cash and emitted == []
        result = portfolio.snapshot_at(at(review["effective_date"]))
        assert PortfolioSnapshot.model_validate_json(result.model_dump_json()) == result
        assert result.realized_pnl == 0
        if whole:
            position = next(p for p in portfolio.positions if p.symbol == successor)
            assert position.quantity == whole
            assert position.aggregate_cost_basis == quantity * 10
            assert result.corporate_action_realized_pnl == 0
        else:
            assert not portfolio.positions
            assert result.corporate_action_realized_pnl == -quantity * 10
        assert not portfolio.is_orderable(parent)
    if review["cash_election_offered"] is None:
        assert action.cash_election_offered is None
        assert (
            action.cash_election_policy == "NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE"
        )
