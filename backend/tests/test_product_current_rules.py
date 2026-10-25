from datetime import date
from decimal import Decimal

import pytest

from app.data.catalog.checksums import canonical_sha256
from app.domain.markets.cn_a_rules import (
    candidate_2026_cn_a_costs,
    candidate_2026_cn_a_rules,
    historical_cn_a_rules,
)
from app.domain.markets.identifiers import Board, Exchange, Market, SecurityId
from app.domain.markets.rules import (
    DailySecurityStatus,
    TradingRuleResolver,
    TransactionCostSchedule,
)
from app.domain.trading import OrderSide, OrderType


def _cost(
    *, valid_from: date = date(2026, 7, 6), valid_to: date | None = None
) -> TransactionCostSchedule:
    return TransactionCostSchedule(
        commission_rate=Decimal("0.0003"),
        minimum_commission=Decimal("5"),
        sell_stamp_duty_rate=Decimal("0.0005"),
        transfer_fee_rate=Decimal("0.00001"),
        valid_from=valid_from,
        valid_to=valid_to,
        source_version="test-cost-not-an-authority",
    )


def test_2026_cost_candidate_separates_statutory_rates_from_broker_assumption() -> None:
    cost = candidate_2026_cn_a_costs(
        commission_rate=Decimal("0.0003"), minimum_commission=Decimal("5")
    )
    assert cost.valid_from == date(2026, 1, 1)
    assert cost.sell_stamp_duty_rate == Decimal("0.0005")
    assert cost.transfer_fee_rate == Decimal("0.00001")
    assert cost.commission_rate == Decimal("0.0003")
    assert cost.minimum_commission == Decimal("5")
    assert "broker-assumption" in cost.source_version
    assert all(rule.conservative_no_fill for rule in candidate_2026_cn_a_rules(cost).rules)


@pytest.mark.parametrize(
    ("exchange", "board", "symbol", "limit", "minimum", "increment"),
    (
        (Exchange.SSE, Board.SSE_MAIN, "600000", "0.10", 100, 100),
        (Exchange.SSE, Board.SSE_STAR, "688001", "0.20", 200, 1),
        (Exchange.SZSE, Board.SZSE_MAIN, "000001", "0.10", 100, 100),
        (Exchange.SZSE, Board.SZSE_CHINEXT, "300001", "0.20", 100, 100),
    ),
)
def test_2026_rule_candidate_resolves_boundary_but_never_executes(
    exchange: Exchange,
    board: Board,
    symbol: str,
    limit: str,
    minimum: int,
    increment: int,
) -> None:
    version = candidate_2026_cn_a_rules(_cost())
    resolver = TradingRuleResolver(version)
    sid = SecurityId(value=f"CN-A:{exchange.value}:{symbol}")
    for day, age, is_st in (
        (date(2026, 7, 6), 0, False),
        (date(2026, 7, 7), 4, True),
        (date(2026, 9, 22), 100, False),
        (date(2026, 9, 22), 100, True),
    ):
        resolved = resolver.resolve(
            security_id=sid,
            market=Market.CN_A,
            exchange=exchange,
            board=board,
            trading_date=day,
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            security_status=DailySecurityStatus(
                security_id=sid,
                trading_date=day,
                is_st=is_st,
                is_suspended=False,
                source_version="test-status-not-an-authority",
            ),
            listing_age_sessions=age,
        )
        assert resolved.price_limit_rate == (None if age < 5 else Decimal(limit))
        assert resolved.minimum_buy_quantity == minimum
        assert resolved.buy_quantity_increment == increment
        assert resolved.minimum_tick == Decimal("0.01")
        assert resolved.rule_source_version.startswith("cn-a-product-2026-candidate.1:")
        assert resolved.model_dump(mode="json")["permitted_order_types"] == ["LIMIT", "MARKET"]
        assert not resolved.executable
    assert all(rule.valid_from == date(2026, 7, 6) for rule in version.rules)
    assert all(rule.source_publication_date == date(2026, 4, 24) for rule in version.rules)
    assert all(rule.conservative_no_fill for rule in version.rules)


def test_2026_candidate_rejects_pre_effective_or_missing_cost_and_preserves_history() -> None:
    with pytest.raises(ValueError, match="CURRENT_COST_SCHEDULE_NOT_EFFECTIVE"):
        candidate_2026_cn_a_rules(_cost(valid_from=date(2026, 7, 7)))
    with pytest.raises(ValueError, match="CURRENT_COST_SCHEDULE_NOT_EFFECTIVE"):
        candidate_2026_cn_a_rules(_cost(valid_from=date(2026, 7, 1), valid_to=date(2026, 7, 5)))
    version = candidate_2026_cn_a_rules(_cost())
    sid = SecurityId(value="CN-A:SSE:600000")
    with pytest.raises(LookupError, match="RULE_VERSION_NOT_FOUND"):
        TradingRuleResolver(version).resolve(
            security_id=sid,
            market=Market.CN_A,
            exchange=Exchange.SSE,
            board=Board.SSE_MAIN,
            trading_date=date(2026, 7, 3),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            security_status=DailySecurityStatus(
                security_id=sid,
                trading_date=date(2026, 7, 3),
                is_st=True,
                is_suspended=False,
                source_version="test-status-not-an-authority",
            ),
            listing_age_sessions=100,
        )
    assert canonical_sha256(historical_cn_a_rules().model_dump(mode="json")) == (
        "28a0123ce3d9ebf522f59f0bf69de8e24d1fb0a7cb9da0a795a8404c535a250b"
    )
