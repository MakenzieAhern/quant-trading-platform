from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal

import pytest

from app.data.providers.research import DailyBarRecord, SecurityStatusRecord
from app.domain.markets import DailySecurityStatus, SecurityId
from app.domain.markets.calendar import TradingCalendar, TradingSession
from app.domain.markets.cn_a_rules import historical_cn_a_rules
from app.domain.markets.identifiers import Board, Exchange, Market
from app.domain.markets.rules import (
    PriceLimitModel,
    ResolvedTradingRules,
    TradingRuleResolver,
    TransactionCostSchedule,
)
from app.domain.trading import Order, OrderSide, OrderType
from app.execution import FixedBasisPointSlippage, FixedCommission
from app.research import (
    FeatureOnlyDailyObservation,
    PortfolioTarget,
    ResearchExecutionEngine,
    ResearchSession,
    TargetPosition,
)
from app.research.execution_convention import rejection_reason

SECURITY_ID = SecurityId(value="CN-A:SSE:600000")
CALENDAR = TradingCalendar(
    market=Market.CN_A,
    sessions=tuple(
        TradingSession(session_date=date(2024, 1, day), is_open=True, source_version="fixture")
        for day in (2, 3, 4)
    ),
)


class OneTargetStrategy:
    strategy_id = "research_path_test"

    def __init__(self) -> None:
        self.calls = 0

    def target_for_completed_session(
        self, session: ResearchSession, available_equity: Decimal
    ) -> PortfolioTarget | None:
        self.calls += 1
        if self.calls != 1:
            return None
        return PortfolioTarget(
            positions=(
                TargetPosition(
                    security_id=SECURITY_ID,
                    target_weight=Decimal(1),
                    quantity=Decimal(100),
                    reference_price=Decimal(10),
                ),
            ),
            residual_cash=available_equity - Decimal(1000),
        )

    def reset(self) -> None:
        self.calls = 0


def _session(
    trading_date: date,
    *,
    opening: str,
    suspended: bool = False,
    one_price_limit: bool = False,
) -> ResearchSession:
    bar = DailyBarRecord(
        security_id=SECURITY_ID,
        trading_date=trading_date,
        raw_open=Decimal(opening),
        raw_high=Decimal(opening) + Decimal("0.1"),
        raw_low=Decimal(opening) - Decimal("0.1"),
        raw_close=Decimal(opening),
        volume=Decimal(10000),
        amount=Decimal(100000),
        adjusted_close=Decimal(opening),
        pre_close=Decimal(10),
    )
    status = SecurityStatusRecord(
        status=DailySecurityStatus(
            security_id=SECURITY_ID,
            trading_date=trading_date,
            is_st=False,
            is_suspended=suspended,
            is_tradeable=True,
            is_one_price_limit=one_price_limit,
            source_version="fixture-1",
        )
    )
    return ResearchSession(
        trading_date=trading_date,
        bars=(bar,),
        statuses=(status,),
        buy_lot_sizes=((SECURITY_ID, 100),),
        trading_rules=(
            ResolvedTradingRules(
                security_id=SECURITY_ID,
                trading_date=trading_date,
                buy_lot_size=100,
                minimum_buy_quantity=100,
                buy_quantity_increment=100,
                odd_lot_sell_only=True,
                minimum_tick=Decimal("0.01"),
                maximum_limit_quantity=1000000,
                price_limit_model=PriceLimitModel.PERCENT_FROM_PREVIOUS_CLOSE,
                price_limit_rate=Decimal("0.1"),
                suspended=suspended,
                executable=not suspended,
                t_plus_one_sale=True,
                permitted_order_types=frozenset({OrderType.LIMIT}),
                cost_schedule=TransactionCostSchedule(
                    commission_rate=Decimal("0.0003"),
                    minimum_commission=Decimal(5),
                    sell_stamp_duty_rate=Decimal("0.0005"),
                    transfer_fee_rate=Decimal("0.00001"),
                    valid_from=date(2023, 8, 28),
                    source_version="fixture",
                ),
                rule_source_version="fixture",
            ),
        ),
    )


def test_research_order_uses_existing_risk_oms_broker_fill_and_portfolio_path() -> None:
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(Decimal(5)),
        calendar=CALENDAR,
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="9.9"),
        )
    )
    assert len(result.proposals) == 1
    assert result.decisions[0].approved is True
    assert len(result.orders) == 1
    assert len(result.fills) == 1
    assert result.fills[0].price == Decimal("9.9")
    assert result.orders[0].price == Decimal(10)
    assert result.orders[0].created_at < result.fills[0].timestamp
    assert result.fills[0].commission == Decimal(5)
    assert result.snapshots[-1].cumulative_commission == Decimal(5)
    assert result.active_reservations == ()


def test_incremental_research_execution_matches_batch_without_future_access() -> None:
    sessions = (
        _session(date(2024, 1, 2), opening="10"),
        _session(date(2024, 1, 3), opening="9.9"),
    )
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(Decimal(5)),
        calendar=CALENDAR,
    )
    engine.reset()
    first = engine.process_session(sessions[0])
    second = engine.process_session(sessions[1])
    incremental = engine.finish()
    batch = engine.run(sessions)

    assert len(first.proposals) == len(first.decisions) == len(first.orders) == 1
    assert first.fills == ()
    assert len(second.fills) == len(second.orders) == 1
    assert second.fills[0].price == Decimal("9.9")
    assert [item.model_dump() for item in incremental.fills] == [
        item.model_dump() for item in batch.fills
    ]
    assert incremental.snapshots == batch.snapshots


def test_append_only_calendar_extension_preserves_precommitted_orders_and_batch_result() -> None:
    calendar = TradingCalendar(market=Market.CN_A, sessions=CALENDAR.sessions[:2])
    extended = TradingCalendar(
        market=Market.CN_A,
        sessions=(
            *calendar.sessions,
            TradingSession(session_date=date(2024, 1, 4), is_open=False, source_version="fixture"),
            TradingSession(session_date=date(2024, 1, 5), is_open=True, source_version="fixture"),
        ),
    )
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal("10000.000000000000000001"),
        commission_model=FixedCommission(Decimal(5)),
        calendar=calendar,
    )
    first = engine.process_session(_session(date(2024, 1, 2), opening="10"))
    assert first.proposals[0].intended_execution_session == date(2024, 1, 3)
    assert engine.next_accepted_session(date(2024, 1, 3)) is None
    engine.extend_calendar(extended)
    engine.extend_calendar(extended)  # Identical publication is retry-safe.
    assert engine.next_accepted_session(date(2024, 1, 3)) == date(2024, 1, 5)
    assert first.proposals[0].intended_execution_session == date(2024, 1, 3)
    with pytest.raises(ValueError, match="missing calendar session"):
        engine.process_session(_session(date(2024, 1, 5), opening="9.9"))
    with pytest.raises(ValueError, match="outside accepted calendar"):
        engine.process_session(_session(date(2024, 1, 4), opening="9.9"))
    second = engine.process_session(_session(date(2024, 1, 3), opening="9.9"))
    assert len(second.fills) == 1
    assert second.fills[0].price == Decimal("9.9")
    engine.process_session(_session(date(2024, 1, 5), opening="9.9"))
    incremental = engine.finish()
    assert incremental == engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="9.9"),
            _session(date(2024, 1, 5), opening="9.9"),
        )
    )


@pytest.mark.parametrize("change", ["shorter", "source", "open", "insert"])
def test_calendar_extension_rejects_changed_prefix_without_mutating_orders(change: str) -> None:
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    first = engine.process_session(_session(date(2024, 1, 2), opening="10"))
    sessions = CALENDAR.sessions
    if change == "shorter":
        sessions = sessions[:-1]
    elif change in {"source", "open"}:
        sessions = (
            sessions[0],
            sessions[1].model_copy(
                update={"source_version": "changed"} if change == "source" else {"is_open": False}
            ),
            *sessions[2:],
        )
    else:
        sessions = (
            TradingSession(session_date=date(2024, 1, 1), is_open=True, source_version="fixture"),
            *sessions,
        )
    with pytest.raises(ValueError, match="append-only"):
        engine.extend_calendar(TradingCalendar(market=Market.CN_A, sessions=sessions))
    assert engine.next_accepted_session(date(2024, 1, 3)) == date(2024, 1, 4)
    second = engine.process_session(_session(date(2024, 1, 3), opening="9.9"))
    assert second.orders[0].id == first.orders[0].id
    assert len(second.fills) == 1


def test_suspension_expires_order_in_its_intended_session() -> None:
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="11", suspended=True),
        )
    )
    assert result.fills == ()
    assert result.expired_order_ids == (result.orders[0].id,)
    assert result.orders[0].status.value == "CANCELLED"


def test_one_price_limit_bar_is_not_assumed_executable() -> None:
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="11", one_price_limit=True),
        )
    )
    assert result.fills == ()
    assert len(result.expired_order_ids) == 1


def test_zero_volume_suspension_placeholder_does_not_advance_portfolio_mark() -> None:
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    placeholder = _session(date(2024, 1, 4), opening="20")
    placeholder = replace(
        placeholder,
        bars=(placeholder.bars[0].model_copy(update={"volume": Decimal(0)}),),
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="9.9"),
            placeholder,
        )
    )
    assert result.snapshots[-1].equity == result.snapshots[-2].equity


@pytest.mark.parametrize("gap", ["missing", "unknown", "limit", "volume", "rules", "flat"])
def test_v1_rejects_insufficient_evidence_and_never_carries_order(gap):
    second = _session(date(2024, 1, 3), opening="9.9")
    if gap == "missing":
        second = replace(second, bars=())
    elif gap == "unknown":
        second = replace(second, statuses=())
    elif gap == "rules":
        second = replace(second, trading_rules=())
    elif gap == "limit":
        second = _session(date(2024, 1, 3), opening="10.1")
    elif gap == "volume":
        second = replace(
            second, bars=(second.bars[0].model_copy(update={"volume": Decimal(9999)}),)
        )
    else:
        second = replace(
            second,
            bars=(
                second.bars[0].model_copy(
                    update={"raw_high": Decimal("9.9"), "raw_low": Decimal("9.9")}
                ),
            ),
        )
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            second,
            _session(date(2024, 1, 4), opening="9.9"),
        )
    )
    assert not result.fills
    assert len(result.expired_order_ids) == 1
    assert not result.active_reservations


def test_v1_rejects_extra_slippage_and_missing_calendar_session():
    with pytest.raises(ValueError, match="zero additional slippage"):
        ResearchExecutionEngine(
            OneTargetStrategy(),
            initial_cash=Decimal(10000),
            commission_model=FixedCommission(),
            calendar=CALENDAR,
            slippage_model=FixedBasisPointSlippage(Decimal(1)),
        )
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    with pytest.raises(ValueError, match="missing calendar session"):
        engine.run(
            (_session(date(2024, 1, 2), opening="10"), _session(date(2024, 1, 4), opening="9.9"))
        )


def test_feature_only_observation_never_executes() -> None:
    first = _session(date(2024, 1, 2), opening="10")
    second = replace(
        _session(date(2024, 1, 3), opening="9.9"),
        bars=(),
        feature_only_observations=(
            FeatureOnlyDailyObservation(
                security_id=SECURITY_ID,
                trading_date=date(2024, 1, 3),
                raw_close=Decimal("9.9"),
                adjusted_close=Decimal("9.9"),
                volume_lower=Decimal(9000),
                volume_upper=Decimal(11000),
                amount_lower=Decimal(90000),
                amount_upper=Decimal(110000),
                lineage="OFFICIAL_PARTIAL_FEATURE_ONLY_NON_TRADABLE",
            ),
        ),
    )
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    result = engine.run((first, second))
    assert result.fills == ()
    assert result.execution_checks[0][1] == "MISSING_OBSERVATION"


@pytest.mark.parametrize(
    "board,exchange,symbol,quantity,rate",
    [
        (Board.SSE_MAIN, Exchange.SSE, "600000", 100, "0.05"),
        (Board.SSE_STAR, Exchange.SSE, "688008", 201, "0.20"),
        (Board.SZSE_MAIN, Exchange.SZSE, "000001", 100, "0.05"),
        (Board.SZSE_CHINEXT, Exchange.SZSE, "300750", 100, "0.20"),
    ],
)
@pytest.mark.parametrize("day", [date(2023, 4, 7), date(2023, 4, 10), date(2023, 4, 11)])
@pytest.mark.parametrize("side", [OrderSide.BUY, OrderSide.SELL])
def test_convention_board_st_transition_and_sell_constraints(
    board, exchange, symbol, quantity, rate, day, side
):
    sid = SecurityId(value=f"CN-A:{exchange.value}:{symbol}")
    session = _session(day, opening="10")
    bar = session.bars[0].model_copy(update={"security_id": sid, "volume": Decimal(100000)})
    status = session.statuses[0].status.model_copy(update={"security_id": sid, "is_st": True})
    resolver = TradingRuleResolver(historical_cn_a_rules())
    rules = resolver.resolve(
        security_id=sid,
        market=Market.CN_A,
        exchange=exchange,
        board=board,
        trading_date=day,
        side=side,
        order_type=OrderType.LIMIT,
        security_status=status,
        listing_age_sessions=100,
    )
    assert rules.price_limit_rate == Decimal(rate)
    order = Order(
        strategy_id="fixture",
        symbol=f"{symbol}.{exchange.value}",
        side=side,
        order_type=OrderType.LIMIT,
        quantity=Decimal(quantity),
        price=Decimal(10),
        intended_execution_session=day,
        created_at=datetime(2023, 4, 6, 7, 0, 1, tzinfo=UTC),
    )
    assert rejection_reason(order, bar, status, rules, Decimal(quantity)) is None
    invalid_tick = order.model_copy(update={"price": Decimal("10.001")})
    assert rejection_reason(invalid_tick, bar, status, rules, Decimal(quantity)) == "TICK_SIZE"
    invalid_quantity = order.model_copy(update={"quantity": Decimal("99.5")})
    assert rejection_reason(invalid_quantity, bar, status, rules, Decimal(quantity)) is not None
    invalid_limit = order.model_copy(
        update={"price": Decimal("9.99") if side is OrderSide.BUY else Decimal("10.01")}
    )
    assert (
        rejection_reason(invalid_limit, bar, status, rules, Decimal(quantity))
        == "OPEN_OUTSIDE_PRECOMMITTED_LIMIT"
    )
    locked = status.model_copy(update={"is_one_price_limit": True})
    assert (
        rejection_reason(order, bar, locked, rules, Decimal(quantity)) == "SINGLE_PRICE_OR_LOCKED"
    )
    ipo = resolver.resolve(
        security_id=sid,
        market=Market.CN_A,
        exchange=exchange,
        board=board,
        trading_date=day,
        side=side,
        order_type=OrderType.LIMIT,
        security_status=status,
        listing_age_sessions=0,
    )
    assert rejection_reason(order, bar, status, ipo, Decimal(quantity)) is not None
    relisting = resolver.resolve(
        security_id=sid,
        market=Market.CN_A,
        exchange=exchange,
        board=board,
        trading_date=day,
        side=side,
        order_type=OrderType.LIMIT,
        security_status=status.model_copy(update={"relisting_date": day}),
        listing_age_sessions=100,
    )
    assert relisting.price_limit_rate is None
    assert rejection_reason(order, bar, status, relisting, Decimal(quantity)) is not None


def test_parameters_use_completed_raw_close_and_replay_is_deterministic():
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    first = _session(date(2024, 1, 2), opening="10")
    other = SecurityId(value="CN-A:SSE:600004")
    first = replace(
        first,
        bars=(*first.bars, first.bars[0].model_copy(update={"security_id": other})),
        statuses=(
            *first.statuses,
            SecurityStatusRecord(
                status=first.statuses[0].status.model_copy(update={"security_id": other})
            ),
        ),
        trading_rules=(
            *first.trading_rules,
            first.trading_rules[0].model_copy(update={"security_id": other}),
        ),
    )
    second = _session(date(2024, 1, 3), opening="9.9")
    second = replace(
        second, bars=(second.bars[0].model_copy(update={"adjusted_close": Decimal(999)}),)
    )
    result = engine.run((first, second))
    repeat = engine.run(
        (
            replace(
                first,
                bars=tuple(reversed(first.bars)),
                statuses=tuple(reversed(first.statuses)),
                trading_rules=tuple(reversed(first.trading_rules)),
            ),
            second,
        )
    )
    assert [item.model_dump(exclude={"id"}) for item in result.proposals] == [
        item.model_dump(exclude={"id"}) for item in repeat.proposals
    ]
    assert [(item.price, item.quantity, item.commission) for item in result.fills] == [
        (item.price, item.quantity, item.commission) for item in repeat.fills
    ]
    changed = engine.run((first, _session(date(2024, 1, 3), opening="10.2")))
    assert result.proposals == changed.proposals
    assert changed.fills == ()
    assert result.fills[0].price == Decimal("9.9")


def test_normal_sell_uses_same_oms_path_on_following_session_and_costs_once():
    class RoundTrip(OneTargetStrategy):
        def target_for_completed_session(self, session, available_equity):
            result = super().target_for_completed_session(session, available_equity)
            if self.calls == 2:
                return PortfolioTarget(positions=(), residual_cash=available_equity)
            return result

    engine = ResearchExecutionEngine(
        RoundTrip(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(Decimal(5)),
        calendar=CALENDAR,
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="9.9"),
            _session(date(2024, 1, 4), opening="10"),
        )
    )
    assert [fill.side for fill in result.fills] == [OrderSide.BUY, OrderSide.SELL]
    assert [fill.price for fill in result.fills] == [Decimal("9.9"), Decimal(10)]
    assert result.fills[0].timestamp < result.fills[1].timestamp
    assert result.snapshots[-1].cumulative_commission == Decimal(10)
    assert not result.active_reservations


@pytest.mark.parametrize("zero_volume", [False, True])
def test_unexplained_held_reference_change_stops_before_any_session_side_effect(zero_volume):
    strategy = OneTargetStrategy()
    engine = ResearchExecutionEngine(
        strategy,
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(Decimal(5)),
        calendar=CALENDAR,
    )
    engine.process_session(_session(date(2024, 1, 2), opening="10"))
    held = engine.process_session(_session(date(2024, 1, 3), opening="9.9"))
    before = engine.finish()
    unknown = _session(date(2024, 1, 4), opening="5")
    unknown = replace(
        unknown,
        bars=(
            unknown.bars[0].model_copy(
                update={"volume": Decimal(0) if zero_volume else Decimal(10000)}
            ),
        ),
        unexplained_reference_adjustment_ids=(SECURITY_ID,),
    )
    with pytest.raises(ValueError, match="UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT") as caught:
        engine.process_session(unknown)
    assert caught.value.trading_date == date(2024, 1, 4)
    assert caught.value.security_ids == (str(SECURITY_ID),)
    assert engine.finish() == before
    assert strategy.calls == 2
    assert engine.last_completed_session == date(2024, 1, 3)
    assert held.snapshot.positions[0].quantity == Decimal(100)
    # Rejected input never advances the engine or rewrites its previously saved state.
    engine.process_session(_session(date(2024, 1, 4), opening="10"))
    assert strategy.calls == 3


def test_reference_marker_does_not_invent_an_entitlement_for_an_unheld_security():
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
    )
    first = replace(
        _session(date(2024, 1, 2), opening="10"),
        unexplained_reference_adjustment_ids=(SECURITY_ID,),
    )
    delta = engine.process_session(first)
    assert len(delta.proposals) == 1
    assert delta.fills == ()
    assert delta.snapshot.cash == Decimal(10000)
    assert delta.snapshot.market_value == 0


def test_reference_markers_must_have_distinct_observed_security_identity():
    session = _session(date(2024, 1, 2), opening="10")
    for markers in (
        (SECURITY_ID, SECURITY_ID),
        (SecurityId(value="CN-A:SZSE:000001"),),
    ):
        with pytest.raises(ValueError, match="reference adjustment identity"):
            replace(session, unexplained_reference_adjustment_ids=markers)
