from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.domain.markets import (
    Board,
    DailySecurityStatus,
    EffectiveSymbolPeriod,
    Exchange,
    Market,
    PriceLimitModel,
    Security,
    SecurityId,
    SecurityListingPeriod,
    TradingCalendar,
    TradingRuleResolver,
    TradingRuleSet,
    TradingRuleVersion,
    TradingSession,
    TransactionCostSchedule,
    historical_cn_a_rules,
    is_locked_one_price_bar,
)
from app.domain.trading import OrderSide, OrderType

SECURITY_ID = SecurityId(value="CN-A:SSE:600000")


def _cost(valid_from: date = date(2023, 8, 28)) -> TransactionCostSchedule:
    return TransactionCostSchedule(
        commission_rate=Decimal("0.0003"),
        minimum_commission=Decimal("5"),
        sell_stamp_duty_rate=Decimal("0.0005"),
        transfer_fee_rate=Decimal("0.00001"),
        valid_from=valid_from,
        source_version="mof-2023-39",
    )


def _rule(**overrides: object) -> TradingRuleSet:
    values: dict[str, object] = {
        "rule_set_id": "cn-a-sse-main-2023",
        "exchange": Exchange.SSE,
        "board": Board.SSE_MAIN,
        "valid_from": date(2023, 8, 28),
        "buy_lot_size": 100,
        "minimum_tick": Decimal("0.01"),
        "price_limit_rate": Decimal("0.10"),
        "st_price_limit_rate": Decimal("0.05"),
        "ipo_no_limit_sessions": 5,
        "permitted_order_types": frozenset({OrderType.MARKET, OrderType.LIMIT}),
        "cost_schedule": _cost(),
        "source_version": "sse-rules-2023",
        "source": "SSE",
        "source_publication_date": date(2023, 2, 17),
        "provenance_note": "fixture",
    }
    values.update(overrides)
    return TradingRuleSet(**values)  # type: ignore[arg-type]


def _status(**overrides: object) -> DailySecurityStatus:
    values: dict[str, object] = {
        "security_id": SECURITY_ID,
        "trading_date": date(2024, 1, 2),
        "is_st": False,
        "is_suspended": False,
        "is_tradeable": True,
        "source_version": "dataset-1",
    }
    values.update(overrides)
    return DailySecurityStatus(**values)  # type: ignore[arg-type]


def test_security_identity_and_history_are_explicit_and_effective_dated() -> None:
    security = Security(
        security_id=SECURITY_ID,
        exchange=Exchange.SSE,
        name="浦发银行",
        symbol_periods=(
            EffectiveSymbolPeriod(
                symbol="600000", exchange=Exchange.SSE, valid_from=date(1999, 11, 10)
            ),
        ),
        listing_periods=(
            SecurityListingPeriod(board=Board.SSE_MAIN, listed_from=date(1999, 11, 10)),
        ),
    )
    assert security.listing_periods[0].contains(date(2024, 1, 2))
    assert security.market is Market.CN_A


def test_security_rejects_overlapping_historical_classification() -> None:
    with pytest.raises(ValidationError, match="listing periods must not overlap"):
        Security(
            security_id=SECURITY_ID,
            exchange=Exchange.SSE,
            name="example",
            symbol_periods=(
                EffectiveSymbolPeriod(
                    symbol="600000", exchange=Exchange.SSE, valid_from=date(2000, 1, 1)
                ),
            ),
            listing_periods=(
                SecurityListingPeriod(
                    board=Board.SSE_MAIN,
                    listed_from=date(2000, 1, 1),
                    delisted_on=date(2020, 1, 1),
                ),
                SecurityListingPeriod(
                    board=Board.SSE_STAR,
                    listed_from=date(2019, 1, 1),
                ),
            ),
        )


def test_calendar_rejects_gaps_disguised_as_unsorted_sessions() -> None:
    with pytest.raises(ValidationError, match="unique and chronological"):
        TradingCalendar(
            market=Market.CN_A,
            sessions=(
                TradingSession(session_date=date(2024, 1, 3), is_open=True, source_version="v1"),
                TradingSession(session_date=date(2024, 1, 2), is_open=True, source_version="v1"),
            ),
        )


def test_rule_resolution_applies_ipo_then_st_status_and_suspension() -> None:
    resolver = TradingRuleResolver(TradingRuleVersion(version="cn-a-2023.1", rules=(_rule(),)))

    ipo = resolver.resolve(
        security_id=SECURITY_ID,
        market=Market.CN_A,
        exchange=Exchange.SSE,
        board=Board.SSE_MAIN,
        trading_date=date(2024, 1, 2),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        security_status=_status(),
        listing_age_sessions=2,
    )
    assert ipo.price_limit_model is PriceLimitModel.NONE
    assert ipo.price_limit_rate is None

    st = resolver.resolve(
        security_id=SECURITY_ID,
        market=Market.CN_A,
        exchange=Exchange.SSE,
        board=Board.SSE_MAIN,
        trading_date=date(2024, 1, 2),
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        security_status=_status(is_st=True, is_suspended=True),
        listing_age_sessions=10,
    )
    assert st.price_limit_rate == Decimal("0.05")
    assert st.suspended is True
    assert st.executable is False
    assert st.t_plus_one_sale is True


def test_rule_resolution_requires_confirmed_tradeability() -> None:
    resolver = TradingRuleResolver(TradingRuleVersion(version="test", rules=(_rule(),)))
    for tradeable in (None, False, True):
        resolved = resolver.resolve(
            security_id=SECURITY_ID,
            market=Market.CN_A,
            exchange=Exchange.SSE,
            board=Board.SSE_MAIN,
            trading_date=date(2024, 1, 2),
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            security_status=_status(is_tradeable=tradeable),
            listing_age_sessions=100,
        )
        assert resolved.executable is (tradeable is True)


def test_security_specific_rule_precedes_board_rule() -> None:
    security_rule = _rule(
        rule_set_id="security-exception",
        security_id=SECURITY_ID,
        minimum_tick=Decimal("0.001"),
        source_version="security-exception-1",
    )
    resolver = TradingRuleResolver(
        TradingRuleVersion(version="cn-a-2023.1", rules=(_rule(), security_rule))
    )
    resolved = resolver.resolve(
        security_id=SECURITY_ID,
        market=Market.CN_A,
        exchange=Exchange.SSE,
        board=Board.SSE_MAIN,
        trading_date=date(2024, 1, 2),
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        security_status=_status(),
        listing_age_sessions=10,
    )
    assert resolved.minimum_tick == Decimal("0.001")
    assert resolved.rule_source_version.endswith("security-exception-1")


def test_rule_version_rejects_overlapping_ranges_within_same_scope() -> None:
    with pytest.raises(ValidationError, match="must not overlap"):
        TradingRuleVersion(
            version="invalid",
            rules=(
                _rule(valid_to=date(2024, 1, 1)),
                _rule(valid_from=date(2024, 1, 1), cost_schedule=_cost(date(2024, 1, 1))),
            ),
        )


def test_historical_rule_timeline_versions_chinext_reform_and_star_lots() -> None:
    resolver = TradingRuleResolver(historical_cn_a_rules())
    before = resolver.resolve(
        security_id=SecurityId(value="CN-A:SZSE:300001"),
        market=Market.CN_A,
        exchange=Exchange.SZSE,
        board=Board.SZSE_CHINEXT,
        trading_date=date(2020, 8, 21),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        security_status=_status(
            security_id=SecurityId(value="CN-A:SZSE:300001"),
            trading_date=date(2020, 8, 21),
        ),
        listing_age_sessions=100,
    )
    after = resolver.resolve(
        security_id=SecurityId(value="CN-A:SZSE:300001"),
        market=Market.CN_A,
        exchange=Exchange.SZSE,
        board=Board.SZSE_CHINEXT,
        trading_date=date(2020, 8, 24),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        security_status=_status(
            security_id=SecurityId(value="CN-A:SZSE:300001"),
            trading_date=date(2020, 8, 24),
        ),
        listing_age_sessions=100,
    )
    star = resolver.resolve(
        security_id=SecurityId(value="CN-A:SSE:688001"),
        market=Market.CN_A,
        exchange=Exchange.SSE,
        board=Board.SSE_STAR,
        trading_date=date(2020, 8, 24),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        security_status=_status(
            security_id=SecurityId(value="CN-A:SSE:688001"),
            trading_date=date(2020, 8, 24),
        ),
        listing_age_sessions=100,
    )
    assert before.price_limit_rate == Decimal("0.10")
    assert after.price_limit_rate == Decimal("0.20")
    assert after.rule_source_version != before.rule_source_version
    assert star.minimum_buy_quantity == 200
    assert star.buy_quantity_increment == 1


def test_main_board_registration_uses_effective_date_not_publication_date() -> None:
    version = historical_cn_a_rules()
    for board in (Board.SSE_MAIN, Board.SZSE_MAIN):
        before = next(
            r for r in version.rules if r.board == board and r.applies_on(date(2023, 3, 1))
        )
        after = next(
            r for r in version.rules if r.board == board and r.applies_on(date(2023, 4, 10))
        )
        assert before.ipo_no_limit_sessions == (1 if board == Board.SZSE_MAIN else 0)
        assert before.conservative_no_fill_listing_sessions == 1
        assert after.ipo_no_limit_sessions == 5
        assert after.source_publication_date == date(2023, 2, 17)
        assert after.valid_from == date(2023, 4, 10)


def test_szse_2023_boundary_status_lots_costs_and_no_future_rule_leakage() -> None:
    version = historical_cn_a_rules()
    boundary = date(2023, 4, 10)
    for board, symbol in ((Board.SZSE_MAIN, "000001"), (Board.SZSE_CHINEXT, "300001")):
        sid = SecurityId(value=f"CN-A:SZSE:{symbol}")
        for day in (
            date(2023, 2, 17),
            date(2023, 4, 7),
            boundary,
            date(2023, 4, 11),
            date(2023, 4, 12),
            date(2023, 8, 25),
            date(2023, 8, 28),
        ):
            selected = next(r for r in version.rules if r.board == board and r.applies_on(day))
            if day < boundary:
                assert selected.source_publication_date < date(2023, 2, 17)
                assert selected.valid_to == date(2023, 4, 9)
            else:
                assert selected.source_publication_date == date(2023, 2, 17)
                assert selected.source_version.endswith("2023-04-10")
            for state in ("NORMAL", "ST", "STAR_ST"):
                for age in (0, 4, 5):
                    for suspended in (False, True):
                        args = dict(
                            security_id=sid,
                            market=Market.CN_A,
                            exchange=Exchange.SZSE,
                            board=board,
                            trading_date=day,
                            side=OrderSide.SELL,
                            order_type=OrderType.MARKET,
                            listing_age_sessions=age,
                            security_status=_status(
                                security_id=sid,
                                trading_date=day,
                                is_st=state != "NORMAL",
                                is_suspended=suspended,
                            ),
                        )
                        resolved = TradingRuleResolver(version).resolve(**args)
                        prefix = version.model_copy(
                            update={
                                "rules": tuple(
                                    r for r in reversed(version.rules) if r.valid_from <= day
                                )
                            }
                        )
                        assert resolved == TradingRuleResolver(prefix).resolve(**args)
                        unlimited = age == 0 or (
                            age < 5 and (board == Board.SZSE_CHINEXT or day >= boundary)
                        )
                        rate = (
                            "0.20"
                            if board == Board.SZSE_CHINEXT
                            else ("0.05" if state != "NORMAL" else "0.10")
                        )
                        assert resolved.price_limit_rate == (None if unlimited else Decimal(rate))
                        assert resolved.buy_lot_size == resolved.minimum_buy_quantity == 100
                        assert resolved.buy_quantity_increment == 100
                        assert resolved.minimum_tick == Decimal("0.01")
                        assert resolved.executable == (
                            not suspended
                            and not (board == Board.SZSE_MAIN and day < boundary and age == 0)
                        )
                        assert resolved.cost_schedule.sell_stamp_duty_rate == Decimal(
                            "0.001" if day < date(2023, 8, 28) else "0.0005"
                        )
                        assert resolved.cost_schedule.transfer_fee_rate == Decimal("0.00001")
                        assert resolved.cost_schedule.commission_rate == Decimal("0.0003")
                        assert resolved.cost_schedule.minimum_commission == 5
                        assert resolved.t_plus_one_sale


def test_delisting_period_overrides_st_without_losing_suspension_or_order_reproducibility() -> None:
    version = historical_cn_a_rules()
    for exchange, board, symbol, rate in (
        (Exchange.SSE, Board.SSE_MAIN, "600000", "0.10"),
        (Exchange.SZSE, Board.SZSE_MAIN, "000001", "0.10"),
        (Exchange.SSE, Board.SSE_STAR, "688001", "0.20"),
        (Exchange.SZSE, Board.SZSE_CHINEXT, "300336", "0.20"),
    ):
        sid = SecurityId(value=f"CN-A:{exchange.value}:{symbol}")
        for day in (date(2023, 6, 12), date(2023, 6, 13)):
            status = _status(
                security_id=sid,
                trading_date=day,
                is_st=True,
                is_suspended=True,
                delisting_period_start=date(2023, 6, 12),
            )
            args = dict(
                security_id=sid,
                market=Market.CN_A,
                exchange=exchange,
                board=board,
                trading_date=day,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                security_status=status,
                listing_age_sessions=999,
            )
            normal = TradingRuleResolver(version).resolve(**args)
            reversed_rules = version.model_copy(update={"rules": tuple(reversed(version.rules))})
            assert normal == TradingRuleResolver(reversed_rules).resolve(**args)
            assert normal.price_limit_rate == (None if day.day == 12 else Decimal(rate))
            assert not normal.executable and normal.suspended
    with pytest.raises(ValidationError, match="cannot start after"):
        _status(delisting_period_start=date(2025, 1, 1))
    from scripts.ingest_research_data import _status_row

    assert _status_row(status)["delisting_period_start"] == date(2023, 6, 12)
    with pytest.raises(ValueError, match="IDENTITY_MISMATCH"):
        TradingRuleResolver(version).resolve(**dict(args, trading_date=date(2023, 6, 14)))
    with pytest.raises(ValueError, match="INVALID_LISTING_AGE"):
        TradingRuleResolver(version).resolve(**dict(args, listing_age_sessions=-1))
    later = date(2025, 1, 1)
    with pytest.raises(LookupError, match="OUTSIDE_AUDITED_PERIOD"):
        TradingRuleResolver(version).resolve(
            **dict(
                args,
                trading_date=later,
                security_status=status.model_copy(update={"trading_date": later}),
            )
        )


def test_named_chinext_transition_exception_is_conservative_no_fill() -> None:
    security_id = SecurityId(value="CN-A:SZSE:300216")
    resolved = TradingRuleResolver(historical_cn_a_rules()).resolve(
        security_id=security_id,
        market=Market.CN_A,
        exchange=Exchange.SZSE,
        board=Board.SZSE_CHINEXT,
        trading_date=date(2020, 8, 24),
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        security_status=_status(security_id=security_id, trading_date=date(2020, 8, 24)),
        listing_age_sessions=100,
    )
    assert resolved.price_limit_rate == Decimal("0.10")
    assert resolved.executable is False


def test_one_price_limit_lock_requires_a_limit_regime_and_blocks_both_directions() -> None:
    resolver = TradingRuleResolver(historical_cn_a_rules())
    rules = resolver.resolve(
        security_id=SECURITY_ID,
        market=Market.CN_A,
        exchange=Exchange.SSE,
        board=Board.SSE_MAIN,
        trading_date=date(2020, 1, 2),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        security_status=_status(trading_date=date(2020, 1, 2)),
        listing_age_sessions=100,
    )
    assert is_locked_one_price_bar(
        raw_open=Decimal("11"),
        raw_high=Decimal("11"),
        raw_low=Decimal("11"),
        raw_close=Decimal("11"),
        pre_close=Decimal("10"),
        rules=rules,
    )
    assert not is_locked_one_price_bar(
        raw_open=Decimal("11"),
        raw_high=Decimal("11.01"),
        raw_low=Decimal("10.99"),
        raw_close=Decimal("11"),
        pre_close=Decimal("10"),
        rules=rules,
    )
