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
    }
    values.update(overrides)
    return TradingRuleSet(**values)  # type: ignore[arg-type]


def _status(**overrides: object) -> DailySecurityStatus:
    values: dict[str, object] = {
        "security_id": SECURITY_ID,
        "trading_date": date(2024, 1, 2),
        "is_st": False,
        "is_suspended": False,
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
