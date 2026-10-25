"""Synthetic accounting observations, not historical prices, tax receipts or admission.

The helpers accept externally verified actions unchanged. Their calendar, positions,
bars, status and rules remain synthetic even when an external proof supplies real
actions. Only same-ex ordinary accounting is exercised, not delayed entitlements.
"""

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
from uuid import UUID

import pytest

from app.data.full_dataset import parse_action_records
from app.domain.markets import CorporateAction, Market, SecurityId
from app.domain.markets.calendar import TradingCalendar, TradingSession
from app.domain.risk import OrderProposal
from app.domain.trading import OrderSide, OrderType
from app.event import Event, EventType
from app.execution import FixedCommission
from app.portfolio import PortfolioError
from app.research.engine import (
    ResearchExecutionDelta,
    ResearchExecutionEngine,
    ResearchExecutionResult,
)
from app.research.models import PortfolioTarget, ResearchSession
from tests.test_portfolio_engine import make_fill
from tests.test_research_execution_engine import _session
from tests.test_rights_issue_policy import rights

RECORD_DATE = date(2011, 5, 5)
EX_DATE = date(2011, 5, 6)
SECURITY_ID = SecurityId(value="CN-A:SZSE:300155")
SYMBOL = "300155.SZSE"
SOURCE = "SYNTHETIC_ACCOUNTING_TEST"
CALENDAR = TradingCalendar(
    market=Market.CN_A,
    sessions=tuple(
        TradingSession(session_date=day, is_open=True, source_version=SOURCE)
        for day in (RECORD_DATE, EX_DATE)
    ),
)
EXTENDED_CALENDAR = TradingCalendar(
    market=Market.CN_A,
    sessions=CALENDAR.sessions
    + tuple(
        TradingSession(session_date=day, is_open=True, source_version=SOURCE)
        for day in (date(2011, 5, 9), date(2011, 5, 10))
    ),
)


class NoTargets:
    """Observe the completed-session path without a research strategy or signals."""

    strategy_id = "ordinary-distribution-accounting-test"

    def __init__(self) -> None:
        self.calls = 0

    def target_for_completed_session(
        self, session: ResearchSession, available_equity: Decimal
    ) -> PortfolioTarget | None:
        self.calls += 1
        return None

    def reset(self) -> None:
        self.calls = 0


def action_records() -> list[dict[str, str]]:
    common = dict(
        security_id=SECURITY_ID,
        announcement_date=date(2011, 4, 27),
        record_date=RECORD_DATE,
        ex_date=EX_DATE,
        effective_date=EX_DATE,
        source_provider=SOURCE,
        source_version="1",
        source_record_hash="a" * 64,
        completeness="COMPLETE",
    )
    actions = (
        CorporateAction(
            **common,
            action_type="CASH_DIVIDEND",
            cash_per_share=Decimal("0.8"),
            payment_date=EX_DATE,
        ),
        CorporateAction(
            **common,
            action_type="BONUS_SHARE",
            share_ratio=Decimal("1.5"),
            listing_date=EX_DATE,
        ),
    )
    return [
        dict(
            application_date=EX_DATE.isoformat(),
            security_id=str(SECURITY_ID),
            event_kind="CORPORATE_ACTION",
            event_json=action.model_dump_json(),
            event_checksum=action.event_checksum,
        )
        for action in actions
    ]


def _actions() -> tuple[CorporateAction, ...]:
    return tuple(
        parse_action_records(action_records(), str(EX_DATE))[str(EX_DATE)]["CORPORATE_ACTION"]
    )


def _accounting_session(day: date, actions: tuple[CorporateAction, ...] = ()) -> ResearchSession:
    opening = "10" if day == RECORD_DATE else "3.68"
    template = _session(day, opening=opening)
    rules = template.trading_rules[0]
    # The borrowed fixture's 2024 schedule is not evidence about historical 2011 rules.
    costs = rules.cost_schedule.model_copy(
        update={"valid_from": date(2010, 1, 1), "source_version": SOURCE}
    )
    return replace(
        template,
        bars=(
            template.bars[0].model_copy(
                update={
                    "security_id": SECURITY_ID,
                    "pre_close": Decimal(opening),
                    "adjusted_close": Decimal(999),
                }
            ),
        ),
        statuses=(
            template.statuses[0].model_copy(
                update={
                    "status": template.statuses[0].status.model_copy(
                        update={"security_id": SECURITY_ID, "source_version": SOURCE}
                    )
                }
            ),
        ),
        buy_lot_sizes=((SECURITY_ID, 100),),
        trading_rules=(
            rules.model_copy(
                update={
                    "security_id": SECURITY_ID,
                    "cost_schedule": costs,
                    "rule_source_version": SOURCE,
                }
            ),
        ),
        corporate_actions=actions,
    )


def _engine(
    *, held: bool, fee: Decimal = Decimal(0), calendar: TradingCalendar = CALENDAR
) -> ResearchExecutionEngine:
    engine = ResearchExecutionEngine(
        NoTargets(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=calendar,
    )
    if held:
        # An explicit opening-account fixture, not a broker execution or strategy result.
        engine._portfolio.apply_fill(
            make_fill(1, OrderSide.BUY, "100", "10", str(fee), SYMBOL).model_copy(
                update={"timestamp": datetime(2011, 5, 4, 7, tzinfo=UTC)}
            )
        )
    return engine


def run_holder_case(
    actions: tuple[CorporateAction, ...], fee: Decimal = Decimal(0)
) -> tuple[ResearchExecutionEngine, tuple[ResearchExecutionDelta, ...], ResearchExecutionResult]:
    engine = _engine(held=True, fee=fee)
    deltas = (
        engine.process_session(_accounting_session(RECORD_DATE)),
        engine.process_session(_accounting_session(EX_DATE, actions)),
    )
    return engine, deltas, engine.finish()


def run_unheld_case(
    actions: tuple[CorporateAction, ...],
) -> tuple[ResearchExecutionEngine, tuple[ResearchExecutionDelta, ...], ResearchExecutionResult]:
    engine = _engine(held=False)
    before = engine.process_session(_accounting_session(RECORD_DATE))
    if before.snapshot is None:
        raise ValueError("synthetic record-day snapshot missing")
    decision, order = engine._oms.process_proposal(
        OrderProposal(
            proposal_id=UUID(int=2),
            strategy_id=NoTargets.strategy_id,
            symbol=SYMBOL,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            limit_price=Decimal("3.68"),
            quantity=Decimal(100),
            signal_timestamp=before.snapshot.timestamp,
            intended_execution_session=EX_DATE,
        )
    )
    if not decision.approved or order is None:
        raise ValueError("synthetic precommitted buy was not accepted by risk/OMS")
    after = engine.process_session(_accounting_session(EX_DATE, actions))
    return engine, (before, after), engine.finish()


def _state(engine: ResearchExecutionEngine) -> tuple:
    return (
        engine._portfolio.cash,
        engine._portfolio.positions,
        engine._portfolio.snapshots,
        engine._portfolio.retained_bonus_rounding_audits,
        engine._portfolio.marks,
        engine._portfolio.cumulative_commission,
        engine._oms.proposals,
        engine._oms.orders,
        engine._oms.active_reservations,
        engine._broker.fills,
        engine._broker.pending_orders,
        engine.last_completed_session,
        engine._active_session,
        tuple(engine._execution_checks),
        engine._strategy.calls,
    )


def test_loader_retains_actions_and_ex_date_boundary() -> None:
    records = action_records()
    assert not parse_action_records(records, str(RECORD_DATE))
    actions = _actions()
    assert [action.event_checksum for action in actions] == [
        row["event_checksum"] for row in records
    ]
    assert actions[0].payment_date == actions[1].listing_date == EX_DATE
    assert all(str(action.entitlement_tradability.value) == "NOT_EVIDENCED" for action in actions)


@pytest.mark.parametrize("fee", (Decimal(0), Decimal(5)))
def test_holder_exact_accounting_is_order_and_decimal_context_independent(fee: Decimal) -> None:
    expected = None
    for precision in (6, 50):
        for actions in (_actions(), tuple(reversed(_actions()))):
            with localcontext() as context:
                context.prec = precision
                engine, deltas, result = run_holder_case(actions, fee)
            before, final = result.snapshots
            assert before.cash == Decimal(9000) - fee
            assert before.positions[0].quantity == 100
            assert before.corporate_action_realized_pnl == 0
            assert final.cash == Decimal(9080) - fee
            assert final.positions[0].quantity == 250
            assert final.positions[0].aggregate_cost_basis == 1000
            assert final.positions[0].average_price == 4
            assert final.market_value == 920  # Synthetic raw 3.68, never adjusted 999.
            assert final.equity == Decimal(10000) - fee
            assert final.realized_pnl == 0
            assert final.corporate_action_realized_pnl == 80
            assert final.unrealized_pnl == -80
            assert final.cumulative_commission == fee
            assert final.total_pnl == -fee
            assert final.total_pnl == (
                final.realized_pnl
                + final.corporate_action_realized_pnl
                + final.unrealized_pnl
                - final.cumulative_commission
            )
            assert len(final.retained_bonus_rounding_audits) == 1
            assert not result.proposals and not result.orders and not result.fills
            assert not result.active_reservations and not result.execution_checks
            assert not deltas[-1].proposals and not deltas[-1].orders and not deltas[-1].fills
            assert engine.last_completed_session == EX_DATE
            if expected is None:
                expected = result
            assert result == expected


@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("precision", (6, 50))
def test_ex_day_precommitted_buy_is_rejected_without_entitlement(
    reverse: bool, precision: int
) -> None:
    actions = tuple(reversed(_actions())) if reverse else _actions()
    with localcontext() as context:
        context.prec = precision
        engine, deltas, result = run_unheld_case(actions)
    final = result.snapshots[-1]
    assert final.cash == final.equity == 10000
    assert not final.positions and final.market_value == 0
    assert final.realized_pnl == final.corporate_action_realized_pnl == final.unrealized_pnl == 0
    assert final.total_pnl == final.cumulative_commission == 0
    assert not final.retained_bonus_rounding_audits
    assert len(result.proposals) == len(result.orders) == 1
    assert not result.fills and not result.active_reservations
    assert result.orders[0].status.value == "CANCELLED"
    assert result.expired_order_ids == (result.orders[0].id,)
    assert result.execution_checks == (
        (result.orders[0].id, "CORPORATE_ACTION_OPENING_UNCERTAINTY"),
    )
    assert not deltas[-1].proposals and not deltas[-1].fills
    assert engine.last_completed_session == EX_DATE


def test_actions_emit_no_order_events_or_synthetic_fills() -> None:
    engine = _engine(held=True)
    engine.process_session(_accounting_session(RECORD_DATE))
    emitted: list[Event] = []
    for kind in EventType:
        if kind.value.startswith("ORDER_"):
            engine._event_bus.subscribe(kind, emitted.append)
    delta = engine.process_session(_accounting_session(EX_DATE, _actions()))
    assert not emitted and not delta.proposals and not delta.orders and not delta.fills


def test_identical_precommitted_buy_is_fillable_without_the_action_boundary() -> None:
    _, _, result = run_unheld_case(())
    assert len(result.fills) == 1
    assert result.execution_checks == ((result.orders[0].id, "ELIGIBLE_SIMULATION_ASSUMPTION"),)
    assert result.fills[0].quantity == 100 and result.fills[0].price == Decimal("3.68")
    assert result.snapshots[-1].cash == 9632
    assert result.snapshots[-1].positions[0].quantity == 100
    assert result.snapshots[-1].corporate_action_realized_pnl == 0
    assert not result.expired_order_ids and not result.active_reservations


@pytest.mark.parametrize("corruption", ("outer_date", "checksum", "security"))
def test_bad_record_is_rejected_before_date_filter_and_accounting(corruption: str) -> None:
    records = action_records()
    field, value = {
        "outer_date": ("application_date", "2011-05-09"),
        "checksum": ("event_checksum", "0" * 64),
        "security": ("security_id", "CN-A:SSE:600000"),
    }[corruption]
    records[1][field] = value
    engine = _engine(held=True)
    engine.process_session(_accounting_session(RECORD_DATE))
    before = _state(engine)
    with pytest.raises(ValueError, match="CORPORATE_ACTION_RECORD_MISMATCH"):
        parse_action_records(records, str(RECORD_DATE))
    assert _state(engine) == before


@pytest.mark.parametrize("variant", ("wrong_ex_session", "duplicate_cash", "invalid_bonus"))
def test_bad_session_actions_fail_before_any_partial_accounting(variant: str) -> None:
    cash, bonus = _actions()
    actions: tuple[CorporateAction, ...] = (cash, bonus)
    error = "corporate action must belong to the research session"
    if variant == "wrong_ex_session":
        actions = (
            cash,
            bonus.model_copy(
                update={
                    "ex_date": date(2011, 5, 9),
                    "effective_date": date(2011, 5, 9),
                    "listing_date": date(2011, 5, 9),
                }
            ),
        )
    elif variant == "duplicate_cash":
        actions = (cash, bonus, cash.model_copy(update={"source_record_hash": "b" * 64}))
        error = "DUPLICATE_ORDINARY_DISTRIBUTION"
    else:
        actions = (cash, bonus.model_copy(update={"share_ratio": Decimal(0)}))
        error = "unsupported corporate action type"
    engine = _engine(held=True)
    engine.process_session(_accounting_session(RECORD_DATE))
    before = _state(engine)
    with pytest.raises(ValueError, match=error):
        engine.process_session(_accounting_session(EX_DATE, actions))
    assert _state(engine) == before
    engine.process_session(_accounting_session(EX_DATE, _actions()))
    assert engine._portfolio.cash == 9080
    assert engine._portfolio.positions[0].quantity == 250


def test_repeated_session_cannot_credit_the_cash_again() -> None:
    engine, _, _ = run_holder_case(_actions())
    before = _state(engine)
    with pytest.raises(ValueError, match="strictly chronological"):
        engine.process_session(_accounting_session(EX_DATE, _actions()))
    assert _state(engine) == before


@pytest.mark.parametrize("held", (False, True))
@pytest.mark.parametrize("entry", ("session", "portfolio"))
@pytest.mark.parametrize(
    ("index", "field", "value", "code"),
    (
        (0, "payment_date", date(2011, 5, 9), "PAYMENT_DATE_UNSUPPORTED"),
        (0, "effective_date", date(2011, 5, 9), "EFFECTIVE_DATE_UNSUPPORTED"),
        (1, "effective_date", date(2011, 5, 9), "EFFECTIVE_DATE_UNSUPPORTED"),
        (0, "record_date", EX_DATE, "RECORD_DATE_UNSUPPORTED"),
        (1, "record_date", EX_DATE, "RECORD_DATE_UNSUPPORTED"),
        (0, "record_date", date(2011, 5, 9), "RECORD_DATE_UNSUPPORTED"),
        (1, "record_date", date(2011, 5, 9), "RECORD_DATE_UNSUPPORTED"),
    ),
)
def test_contradictory_ordinary_dates_fail_before_accounting(
    held: bool, entry: str, index: int, field: str, value: date, code: str
) -> None:
    records = action_records()
    changed = CorporateAction.model_validate_json(records[index]["event_json"]).model_copy(
        update={field: value}
    )
    records[index].update(
        event_json=changed.model_dump_json(),
        event_checksum=changed.event_checksum,
        application_date=str(changed.effective_date),
    )
    # Valid outer identity/checksum must not bless contradictory inner dates.
    parsed = parse_action_records(records, "2011-05-09")
    actions = tuple(action for day in parsed.values() for action in day["CORPORATE_ACTION"])
    engine = _engine(held=held)
    engine.process_session(_accounting_session(RECORD_DATE))
    before = _state(engine)
    with pytest.raises((ValueError, PortfolioError), match="ORDINARY_DISTRIBUTION_" + code):
        if entry == "session":
            engine.process_session(_accounting_session(EX_DATE, actions))
        else:
            engine._portfolio.apply_corporate_action(
                SYMBOL, changed, datetime(2011, 5, 6, 1, 25, tzinfo=UTC)
            )
    assert _state(engine) == before


@pytest.mark.parametrize("entry", ("session", "portfolio"))
def test_unknown_legacy_dates_remain_unknown_without_changing_existing_accounting(
    entry: str,
) -> None:
    actions = tuple(
        action.model_copy(
            update={
                "record_date": None,
                "effective_date": None,
                "payment_date": None,
                "listing_date": None,
            }
        )
        for action in _actions()
    )
    if entry == "session":
        engine, _, result = run_holder_case(actions)
        assert result.snapshots[-1].corporate_action_realized_pnl == 80
    else:
        engine = _engine(held=True)
        for action in actions:
            engine._portfolio.apply_corporate_action(
                SYMBOL, action, datetime(2011, 5, 6, 1, 25, tzinfo=UTC)
            )
    assert engine._portfolio.cash == 9080
    assert engine._portfolio.positions[0].quantity == 250
    assert all(action.payment_date is None and action.listing_date is None for action in actions)


@pytest.mark.parametrize("held", (False, True))
@pytest.mark.parametrize("kind", ("BONUS_SHARE", "STOCK_DIVIDEND"))
@pytest.mark.parametrize("listing", (None, EX_DATE, date(2011, 5, 9)))
def test_same_or_next_accepted_listing_and_unknown_legacy_listing_preserve_accounting(
    held: bool, kind: str, listing: date | None
) -> None:
    cash, share = _actions()
    share = CorporateAction.model_validate(
        {**share.model_dump(), "action_type": kind, "listing_date": listing}
    )
    engine = _engine(held=held, calendar=EXTENDED_CALENDAR)
    engine.process_session(_accounting_session(RECORD_DATE))
    delta = engine.process_session(_accounting_session(EX_DATE, (cash, share)))
    assert delta.snapshot is not None
    assert delta.snapshot.cash == (9080 if held else 10000)
    assert delta.snapshot.corporate_action_realized_pnl == (80 if held else 0)
    assert not delta.orders and not delta.fills and not delta.proposals
    if held:
        assert delta.snapshot.positions[0].quantity == 250
    else:
        assert not delta.snapshot.positions


@pytest.mark.parametrize("held", (False, True))
@pytest.mark.parametrize("kind", ("BONUS_SHARE", "STOCK_DIVIDEND"))
@pytest.mark.parametrize(
    ("calendar", "listing"),
    (
        (EXTENDED_CALENDAR, RECORD_DATE),
        (EXTENDED_CALENDAR, date(2011, 5, 10)),
        (CALENDAR, date(2011, 5, 9)),
    ),
    ids=("before_ex", "later_than_next_accepted", "next_accepted_unknown"),
)
def test_unsupported_listing_boundary_fails_before_cash_or_share_accounting(
    held: bool, kind: str, calendar: TradingCalendar, listing: date
) -> None:
    cash, share = _actions()
    share = CorporateAction.model_validate(
        {**share.model_dump(), "action_type": kind, "listing_date": listing}
    )
    engine = _engine(held=held, calendar=calendar)
    engine.process_session(_accounting_session(RECORD_DATE))
    before = _state(engine)
    with pytest.raises(ValueError, match="ORDINARY_DISTRIBUTION_LISTING_DATE_UNSUPPORTED"):
        engine.process_session(_accounting_session(EX_DATE, (cash, share)))
    assert _state(engine) == before


def test_later_rights_listing_is_not_reclassified_as_ordinary_share_distribution() -> None:
    action = rights(
        security_id=str(SECURITY_ID),
        announcement_date="2011-04-27",
        record_date="2011-04-28",
        subscription_start_date="2011-04-29",
        subscription_end_date="2011-05-05",
        subscription_deadline="2011-05-05",
        ex_date=str(EX_DATE),
        effective_date=str(EX_DATE),
        listing_date="2011-05-10",
    )
    engine = _engine(held=True, calendar=EXTENDED_CALENDAR)
    engine.process_session(_accounting_session(RECORD_DATE))
    delta = engine.process_session(_accounting_session(EX_DATE, (action,)))
    assert delta.snapshot is not None
    assert delta.snapshot.cash == 9000
    assert delta.snapshot.positions[0].quantity == 100
    assert delta.snapshot.corporate_action_realized_pnl == 0
    assert not delta.orders and not delta.fills and not delta.proposals
