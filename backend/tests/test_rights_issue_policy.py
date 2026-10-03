"""Offline accounting fixtures; historical terms do not certify full source coverage."""

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from itertools import permutations

import pytest
from pydantic import ValidationError

from app.domain.markets import CorporateAction, CorporateActionType, SecurityId
from app.domain.markets.corporate_actions import RightsVariant, corporate_action_sort_key
from app.domain.trading import OrderSide
from app.event import EventBus, EventType
from app.execution import FixedCommission
from app.portfolio import PortfolioEngine, PortfolioError
from app.research import ResearchExecutionEngine
from tests.test_portfolio_engine import make_bar, make_fill
from tests.test_research_execution_engine import CALENDAR, OneTargetStrategy, _session
from tests.test_security_master import _master, _record


def rights(**updates):
    # 600036 issuer reminder 2010-008: publication March 9, not March 2.
    # Non-transferability: CNINFO 57640259 prospectus, page 36, reviewed separately.
    # This fixture is not full source-coverage acceptance. Listing remains unknown.
    values = dict(
        security_id="CN-A:SSE:600036",
        action_type="RIGHTS_RELATED_EVENT",
        announcement_date="2010-03-09",
        effective_date="2010-03-15",
        record_date="2010-03-04",
        ex_date="2010-03-15",
        subscription_start_date="2010-03-05",
        subscription_end_date="2010-03-11",
        subscription_deadline="2010-03-11",
        subscription_price="8.85",
        share_ratio="0.13",
        eligible_share_basis="15658890016",
        rights_variant="ORDINARY_NON_TRADABLE",
        rights_event_class="STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE",
        entitlement_tradability="NON_TRADABLE_CONFIRMED",
        completeness="COMPLETE",
        source_document="CMB 2010-008; variant corroborated by 57640259 page 36",
        source_provider="issuer-terms-fixture",
        source_version="2010-008",
        source_url="https://file.cmbchina.com/CMBIR/201003/728a6f5d-1759-42c6-91ea-834dfce3e99c.pdf",
        source_document_sha256="eacae9cd6c9060ca1739dd5e22129c345daf3461b1e36e30dd4d144b4bb9e141",
        source_record_hash="eacae9cd6c9060ca1739dd5e22129c345daf3461b1e36e30dd4d144b4bb9e141",
        retrieved_at="2026-09-12T14:29:00.159452+00:00",
    )
    values.update(updates)
    values["security_id"] = SecurityId(value=values["security_id"])
    return CorporateAction.model_validate(values)


@pytest.mark.parametrize("holding", [False, True])
def test_decline_window_and_lapse_preserve_cash_shares_basis_and_raw_marks(holding):
    bus = EventBus()
    emitted = []
    for kind in (EventType.ORDER_FILLED, EventType.ORDER_CREATED, EventType.ORDER_PROPOSAL):
        bus.subscribe(kind, emitted.append)
    portfolio = PortfolioEngine(bus, Decimal(10000))
    record_day = datetime(2010, 3, 4, 7, tzinfo=UTC)
    if holding:
        portfolio.apply_fill(
            make_fill(1, OrderSide.BUY, "100", "15", symbol="600036").model_copy(
                update={"timestamp": record_day}
            )
        )
    before = portfolio.mark_to_market(
        make_bar(1, "15", symbol="600036").model_copy(update={"timestamp": record_day})
    )
    master = _master((_record("600036", listing_date=date(2002, 4, 9)),))
    # Synthetic raw prices, real historical event dates. Suspended-window checks
    # only inspect holdings; no bar/fill is fabricated during the official halt.
    for day in (5, 11):
        assert rights().security_id in master.eligible_universe(date(2010, 3, day))
        assert portfolio.cash == before.cash
        assert portfolio.positions == before.positions
    for day in (15, 19):
        if day == 15:
            portfolio.apply_corporate_action("600036", rights(), datetime(2010, 3, day, tzinfo=UTC))
        after = portfolio.mark_to_market(
            make_bar(2, "12", symbol="600036").model_copy(
                update={"timestamp": datetime(2010, 3, day, 7, tzinfo=UTC)}
            )
        )
        assert rights().security_id in master.eligible_universe(date(2010, 3, day))
        assert after.cash == before.cash
        assert [(p.quantity, p.average_price) for p in after.positions] == [
            (p.quantity, p.average_price) for p in before.positions
        ]
        assert after.equity == before.equity - (Decimal(300) if holding else Decimal(0))
    assert emitted == []
    assert portfolio.cumulative_commission == 0


@pytest.mark.parametrize(
    "field",
    [
        "effective_date",
        "rights_event_class",
        "source_document",
        "source_url",
        "source_document_sha256",
        "retrieved_at",
    ],
)
def test_missing_terms_fail_closed_even_without_holdings(field):
    action = rights(**{field: None})
    with pytest.raises(PortfolioError, match="EVENT_IDENTITY_UNRESOLVED"):
        PortfolioEngine(EventBus(), Decimal(10000)).apply_corporate_action(
            "600036", action, datetime(2010, 3, 15, tzinfo=UTC)
        )


@pytest.mark.parametrize(
    "tradability", ["NOT_EVIDENCED", "NON_TRADABLE_CONFIRMED", "TRADABLE_CONFIRMED"]
)
def test_standard_structure_is_separate_from_tradability_and_nonessential_metadata(tradability):
    action = rights(
        rights_variant=None,
        entitlement_tradability=tradability,
        completeness="PARTIAL",
        announcement_date=None,
        record_date=None,
        subscription_price=None,
        share_ratio=None,
        subscription_start_date=None,
        subscription_end_date=None,
        subscription_deadline=None,
        eligible_share_basis=None,
    )
    assert action.rights_classification == "STANDARD_PARTIAL_BUT_ACCOUNTING_SAFE"
    assert action.rights_metadata_gaps()
    portfolio = PortfolioEngine(EventBus(), Decimal(10000))
    portfolio.apply_fill(
        make_fill(1, OrderSide.BUY, "100", "15", symbol="600036").model_copy(
            update={"timestamp": datetime(2010, 3, 4, tzinfo=UTC)}
        )
    )
    before = (portfolio.cash, portfolio.positions)
    portfolio.apply_corporate_action("600036", action, datetime(2010, 3, 15, tzinfo=UTC))
    assert (portfolio.cash, portfolio.positions) == before


def test_000960_verified_standard_not_evidenced_regression():
    action = rights(
        security_id="CN-A:SZSE:000960",
        announcement_date="2010-01-13",
        record_date="2010-01-18",
        ex_date="2010-01-27",
        effective_date="2010-01-27",
        subscription_start_date="2010-01-19",
        subscription_end_date="2010-01-25",
        subscription_deadline="2010-01-25",
        subscription_price="8.98",
        share_ratio="0.24",
        eligible_share_basis="651086660",
        rights_variant=None,
        entitlement_tradability="NOT_EVIDENCED",
        source_document="000960 issuer 2010-004; result 2010-010",
        source_url="https://static.cninfo.com.cn/finalpage/2010-01-13/57498926.PDF",
        source_document_sha256="d54ceccd9b163bf071f39a13e08d5f755ab0df8fa4a9ae27e5db3dd8341df0b5",
    )
    assert action.rights_classification == "STANDARD_COMPLETE"
    assert action.entitlement_tradability == "NOT_EVIDENCED"
    portfolio = PortfolioEngine(EventBus(), Decimal(10000))
    portfolio.apply_corporate_action("000960", action, datetime(2010, 1, 27, tzinfo=UTC))
    assert portfolio.cash == 10000 and portfolio.positions == ()


@pytest.mark.parametrize(
    "kind",
    [
        "SEPARATELY_LISTED_TRADABLE_RIGHT",
        "TRANSFERABLE_RIGHTS_INSTRUMENT",
        "MANDATORY_CONVERSION",
        "CASH_SETTLED_RIGHT",
        "AUTOMATIC_COMPENSATION",
        "RIGHTS_WITH_SEPARATE_MARKET_PRICE",
        "OTHER_NONSTANDARD_RIGHTS_INSTRUMENT",
    ],
)
def test_explicit_instrument_structure_never_becomes_standard(kind):
    action = rights(rights_event_class=kind)
    assert action.rights_classification == "EXPLICIT_UNSUPPORTED_VARIANT"
    with pytest.raises(PortfolioError, match="RIGHTS_EVENT_UNSUPPORTED_VARIANT"):
        PortfolioEngine(EventBus(), Decimal(10000)).apply_corporate_action(
            "600036", action, datetime(2010, 3, 15, tzinfo=UTC)
        )


def test_missing_ex_date_remains_material_even_for_noop():
    action = rights(ex_date=None, completeness="PARTIAL")
    assert action.rights_classification == "EVENT_IDENTITY_UNRESOLVED"


@pytest.mark.parametrize(
    "variant", [v for v in RightsVariant if v is not RightsVariant.ORDINARY_NON_TRADABLE]
)
def test_nonstandard_variants_fail_closed(variant):
    with pytest.raises(PortfolioError, match="RIGHTS_EVENT_UNSUPPORTED_VARIANT"):
        PortfolioEngine(EventBus(), Decimal(10000)).apply_corporate_action(
            "600036", rights(rights_variant=variant), datetime(2010, 3, 15, tzinfo=UTC)
        )


def test_event_is_immutable_missing_listing_remains_null_and_bad_dates_fail():
    action = rights()
    assert action.listing_date is None
    assert action.announcement_date == date(2010, 3, 9)
    assert action.rights_issues() == ()
    assert (
        action.event_checksum
        == CorporateAction.model_validate(
            dict(reversed(list(action.model_dump().items())))
        ).event_checksum
    )
    assert action.event_checksum != rights(subscription_price="8.86").event_checksum
    with pytest.raises(ValidationError):
        action.share_ratio = Decimal(1)
    assert (
        "CONTRADICTORY_SUBSCRIPTION_WINDOW"
        in rights(subscription_start_date="2010-03-12").rights_issues()
    )
    assert "CONTRADICTORY_DEADLINE" in rights(subscription_deadline="2010-03-12").rights_issues()


def test_rights_same_day_ordering_replay_raw_adjustment_separation_and_universe_retention():
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    first = _session(date(2024, 1, 2), opening="10")
    second = _session(date(2024, 1, 3), opening="9.9")
    third = _session(date(2024, 1, 4), opening="8")
    # Synthetic mixed-event session on another security: no symbol exception.
    action = rights(
        security_id=str(first.bars[0].security_id),
        ex_date="2024-01-04",
        effective_date="2024-01-04",
    )
    common = dict(
        security_id=action.security_id,
        ex_date="2024-01-04",
        completeness="COMPLETE",
        source_provider="synthetic",
        source_version="test",
        source_record_hash="0" * 64,
    )
    cash = CorporateAction.model_validate(
        dict(common, action_type="CASH_DIVIDEND", cash_per_share="1")
    )
    bonus = CorporateAction.model_validate(
        dict(common, action_type="BONUS_SHARE", share_ratio="0.1")
    )
    another = rights(
        security_id=str(action.security_id),
        ex_date="2024-01-04",
        effective_date="2024-01-04",
        source_record_hash="1" * 64,
    )
    assert sorted((action, bonus, cash), key=corporate_action_sort_key) == [cash, bonus, action]
    expected = None
    for events in permutations((action, cash, bonus, another)):
        result = engine.run(
            (
                first,
                second,
                replace(
                    third,
                    corporate_actions=events,
                    bars=(third.bars[0].model_copy(update={"adjusted_close": Decimal(999)}),),
                ),
            )
        )
        final = result.snapshots[-1]
        assert final.cash == Decimal(9110)  # 10000 - 100*9.9 + 100*1
        assert final.positions[0].quantity == Decimal(110)
        assert final.positions[0].quantity * final.positions[0].average_price == Decimal(990)
        assert final.market_value == Decimal(880)  # Raw 8, not adjusted 999.
        assert len(result.orders) == len(result.fills) == 1
        assert result.active_reservations == ()
        stable = (result.orders, result.fills, result.snapshots)
        if expected is None:
            expected = stable
        assert stable == expected
    # Session still contains the rights security: actions do not filter the universe.
    assert third.bars[0].security_id == SecurityId(value="CN-A:SSE:600000")


@pytest.mark.parametrize("variant", ("duplicate_cash", "duplicate_share", "two_share_kinds"))
@pytest.mark.parametrize("held", (False, True))
@pytest.mark.parametrize("pre_close", (None, Decimal("9.9")))
def test_ordinary_distribution_ambiguity_fails_before_accounting_even_with_rights(
    variant, held, pre_close
):
    strategy = OneTargetStrategy()
    engine = ResearchExecutionEngine(
        strategy,
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    if held:
        engine.process_session(_session(date(2024, 1, 2), opening="10"))
        engine.process_session(_session(date(2024, 1, 3), opening="9.9"))
    third = _session(date(2024, 1, 4), opening="9.9")
    action = rights(
        security_id=str(third.bars[0].security_id),
        ex_date="2024-01-04",
        effective_date="2024-01-04",
    )
    common = dict(
        security_id=action.security_id,
        ex_date="2024-01-04",
        completeness="COMPLETE",
        source_provider="synthetic",
        source_version="test",
        source_record_hash="0" * 64,
    )
    cash = CorporateAction.model_validate(
        dict(common, action_type="CASH_DIVIDEND", cash_per_share="1")
    )
    bonus = CorporateAction.model_validate(
        dict(common, action_type="BONUS_SHARE", share_ratio="0.1")
    )
    original = cash if variant == "duplicate_cash" else bonus
    extra = original.model_copy(
        update={"action_type": CorporateActionType.STOCK_DIVIDEND}
        if variant == "two_share_kinds"
        else {"source_version": "another-official-receipt"}
    )
    assert extra.event_checksum != original.event_checksum
    before = engine.finish()
    calls, completed = strategy.calls, engine.last_completed_session
    financial_before = (
        engine._portfolio.cash,
        tuple(position.model_dump_json() for position in engine._portfolio.positions),
        engine._portfolio.retained_bonus_rounding_audits,
        engine._active_session,
    )
    for events in ((action, cash, bonus, extra), (extra, bonus, cash, action)):
        with pytest.raises(
            ValueError,
            match=r"DUPLICATE_ORDINARY_DISTRIBUTION|MULTIPLE_SHARE_DISTRIBUTIONS_UNSUPPORTED",
        ):
            engine.process_session(
                replace(
                    third,
                    bars=(third.bars[0].model_copy(update={"pre_close": pre_close}),),
                    corporate_actions=events,
                )
            )
        assert engine.finish() == before
        assert strategy.calls == calls
        assert engine.last_completed_session == completed
        assert (
            engine._portfolio.cash,
            tuple(position.model_dump_json() for position in engine._portfolio.positions),
            engine._portfolio.retained_bonus_rounding_audits,
            engine._active_session,
        ) == financial_before


@pytest.mark.parametrize(
    "kind",
    [
        CorporateActionType.SPLIT_OR_SHARE_CHANGE,
        CorporateActionType.MERGER_REORGANIZATION,
        CorporateActionType.UNKNOWN_UNSUPPORTED,
    ],
)
def test_unknown_structural_actions_fail_closed_even_without_position(kind):
    with pytest.raises(PortfolioError, match="unsupported corporate action type"):
        PortfolioEngine(EventBus(), Decimal(10000)).apply_corporate_action(
            "600036", rights(action_type=kind), datetime(2010, 3, 15, tzinfo=UTC)
        )
