from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.domain.markets.identifiers import Board, Exchange, SecurityId
from app.domain.markets.rules import (
    TradingRuleSet,
    TradingRuleVersion,
    TransactionCostSchedule,
)
from app.domain.trading import OrderType


@dataclass(frozen=True, slots=True)
class _BoardPeriod:
    exchange: Exchange
    board: Board
    start: date
    end: date | None
    limit: str
    st_limit: str
    ipo_no_limit_sessions: int
    conservative_listing_sessions: int = 0
    minimum_buy_quantity: int = 100
    increment: int = 100
    source: str = "exchange trading rules"
    published: date = date(2006, 5, 15)
    note: str = "ordinary A-share auction rules"


_COSTS = (
    TransactionCostSchedule(
        commission_rate=Decimal("0.0003"),
        minimum_commission=Decimal(5),
        sell_stamp_duty_rate=Decimal("0.001"),
        transfer_fee_rate=Decimal("0.00001"),
        valid_from=date(2008, 9, 19),
        valid_to=date(2023, 8, 27),
        source_version="mof-2008-stamp-duty",
    ),
    TransactionCostSchedule(
        commission_rate=Decimal("0.0003"),
        minimum_commission=Decimal(5),
        sell_stamp_duty_rate=Decimal("0.0005"),
        transfer_fee_rate=Decimal("0.00001"),
        valid_from=date(2023, 8, 28),
        source_version="mof-2023-stamp-duty",
    ),
)


_PERIODS = (
    _BoardPeriod(
        Exchange.SSE,
        Board.SSE_MAIN,
        date(2010, 1, 1),
        date(2023, 4, 9),
        "0.10",
        "0.05",
        0,
        conservative_listing_sessions=1,
    ),
    _BoardPeriod(
        Exchange.SSE,
        Board.SSE_MAIN,
        date(2023, 4, 10),
        None,
        "0.10",
        "0.05",
        5,
        published=date(2023, 2, 17),
        note="registration-system first-five-session IPO exception",
    ),
    _BoardPeriod(
        Exchange.SZSE,
        Board.SZSE_MAIN,
        date(2010, 1, 1),
        date(2021, 4, 5),
        "0.10",
        "0.05",
        0,
        conservative_listing_sessions=1,
    ),
    _BoardPeriod(
        Exchange.SZSE,
        Board.SZSE_MAIN,
        date(2021, 4, 6),
        date(2023, 4, 9),
        "0.10",
        "0.05",
        1,
        conservative_listing_sessions=1,
        source="SZSE Trading Rules (2021 March revision), SZSE [2021] No. 337",
        published=date(2021, 3, 31),
        note="IPO first session is not ordinary 10%; separate first-day controls: no fill",
    ),
    _BoardPeriod(
        Exchange.SZSE,
        Board.SZSE_MAIN,
        date(2023, 4, 10),
        None,
        "0.10",
        "0.05",
        5,
        source="SZSE Trading Rules (2023 revision), SZSE [2023] No. 98",
        published=date(2023, 2, 17),
        note="registration-system first-five-session IPO exception",
    ),
    _BoardPeriod(
        Exchange.SSE,
        Board.SSE_STAR,
        date(2019, 7, 22),
        None,
        "0.20",
        "0.20",
        5,
        minimum_buy_quantity=200,
        increment=1,
        source="SSE STAR trading rules",
        published=date(2019, 4, 30),
        note="STAR launch: first five sessions unlimited, then 20%",
    ),
    _BoardPeriod(
        Exchange.SZSE,
        Board.SZSE_CHINEXT,
        date(2010, 1, 1),
        date(2020, 8, 23),
        "0.10",
        "0.05",
        0,
        conservative_listing_sessions=1,
        source="SZSE trading rules",
        note="pre-registration-reform ChiNext rules",
    ),
    _BoardPeriod(
        Exchange.SZSE,
        Board.SZSE_CHINEXT,
        date(2020, 8, 24),
        date(2023, 4, 9),
        "0.20",
        "0.20",
        5,
        source="SZSE ChiNext special provisions",
        published=date(2020, 6, 12),
        note="24 Aug 2020 reform for new and existing shares",
    ),
    _BoardPeriod(
        Exchange.SZSE,
        Board.SZSE_CHINEXT,
        date(2023, 4, 10),
        None,
        "0.20",
        "0.20",
        5,
        source="SZSE Trading Rules (2023 revision), SZSE [2023] No. 98",
        published=date(2023, 2, 17),
        note="2023 consolidated rule version; ChiNext numerical limits unchanged",
    ),
)


def historical_cn_a_rules() -> TradingRuleVersion:
    rules = [rule for period in _PERIODS for rule in _split_by_cost(period)]
    for symbol in ("300090", "300156", "300216"):
        rules.append(_transitional_delisting_exception(symbol))
    return TradingRuleVersion(version="cn-a-2010-2025.6", rules=tuple(rules))


def candidate_2026_cn_a_costs(
    *, commission_rate: Decimal, minimum_commission: Decimal
) -> TransactionCostSchedule:
    """Current statutory components; brokerage commission is an explicit assumption."""
    return TransactionCostSchedule(
        commission_rate=commission_rate,
        minimum_commission=minimum_commission,
        sell_stamp_duty_rate=Decimal("0.0005"),
        transfer_fee_rate=Decimal("0.00001"),
        valid_from=date(2026, 1, 1),
        source_version="chinaclear-sh-sz-2026-01-01+broker-assumption",
    )


def candidate_2026_cn_a_rules(cost_schedule: TransactionCostSchedule) -> TradingRuleVersion:
    """Official 2026 board terms; fail closed until other current inputs are audited."""
    effective = date(2026, 7, 6)
    if not cost_schedule.valid_from <= effective or (
        cost_schedule.valid_to is not None and cost_schedule.valid_to < effective
    ):
        raise ValueError("CURRENT_COST_SCHEDULE_NOT_EFFECTIVE")
    periods = (
        _BoardPeriod(
            Exchange.SSE,
            Board.SSE_MAIN,
            effective,
            None,
            "0.10",
            "0.10",
            5,
            source="SSE Trading Rules (2026 revision), SSE [2026] No. 41",
            published=date(2026, 4, 24),
            note="current rule candidate; other execution authorities not yet accepted",
        ),
        _BoardPeriod(
            Exchange.SSE,
            Board.SSE_STAR,
            effective,
            None,
            "0.20",
            "0.20",
            5,
            minimum_buy_quantity=200,
            increment=1,
            source="SSE Trading Rules (2026 revision), SSE [2026] No. 41",
            published=date(2026, 4, 24),
            note="current rule candidate; other execution authorities not yet accepted",
        ),
        _BoardPeriod(
            Exchange.SZSE,
            Board.SZSE_MAIN,
            effective,
            None,
            "0.10",
            "0.10",
            5,
            source="SZSE Trading Rules (2026 revision), SZSE [2026] No. 551",
            published=date(2026, 4, 24),
            note="current rule candidate; other execution authorities not yet accepted",
        ),
        _BoardPeriod(
            Exchange.SZSE,
            Board.SZSE_CHINEXT,
            effective,
            None,
            "0.20",
            "0.20",
            5,
            source="SZSE Trading Rules (2026 revision), SZSE [2026] No. 551",
            published=date(2026, 4, 24),
            note="current rule candidate; other execution authorities not yet accepted",
        ),
    )
    return TradingRuleVersion(
        version="cn-a-product-2026-candidate.1",
        rules=tuple(
            rule.model_copy(update={"conservative_no_fill": True})
            for period in periods
            for rule in _split_by_cost(period, (cost_schedule,))
        ),
    )


def _split_by_cost(
    period: _BoardPeriod, costs: tuple[TransactionCostSchedule, ...] = _COSTS
) -> tuple[TradingRuleSet, ...]:
    rules = []
    for cost in costs:
        start = max(period.start, cost.valid_from)
        ends = tuple(value for value in (period.end, cost.valid_to) if value is not None)
        end = min(ends) if ends else None
        if end is not None and end < start:
            continue
        rules.append(
            TradingRuleSet(
                rule_set_id=f"{period.board.value.lower()}-{start.isoformat()}",
                exchange=period.exchange,
                board=period.board,
                valid_from=start,
                valid_to=end,
                buy_lot_size=period.increment,
                minimum_buy_quantity=period.minimum_buy_quantity,
                buy_quantity_increment=period.increment,
                minimum_tick=Decimal("0.01"),
                maximum_limit_quantity=(
                    100000
                    if period.board is Board.SSE_STAR
                    else 300000
                    if period.board is Board.SZSE_CHINEXT and period.start >= date(2020, 8, 24)
                    else 1000000
                ),
                price_limit_rate=Decimal(period.limit),
                st_price_limit_rate=Decimal(period.st_limit),
                ipo_no_limit_sessions=period.ipo_no_limit_sessions,
                conservative_no_fill_listing_sessions=period.conservative_listing_sessions,
                permitted_order_types=frozenset({OrderType.MARKET, OrderType.LIMIT}),
                cost_schedule=cost,
                source=period.source,
                source_publication_date=period.published,
                provenance_note=period.note,
                source_version=f"{period.board.value}-{period.start.isoformat()}",
            )
        )
    return tuple(rules)


def _transitional_delisting_exception(symbol: str) -> TradingRuleSet:
    return TradingRuleSet(
        rule_set_id=f"chinext-delisting-transition-{symbol}",
        exchange=Exchange.SZSE,
        board=Board.SZSE_CHINEXT,
        security_id=SecurityId(value=f"CN-A:SZSE:{symbol}"),
        valid_from=date(2020, 8, 24),
        valid_to=date(2020, 12, 31),
        buy_lot_size=100,
        minimum_tick=Decimal("0.01"),
        price_limit_rate=Decimal("0.10"),
        st_price_limit_rate=Decimal("0.10"),
        conservative_no_fill=True,
        permitted_order_types=frozenset({OrderType.MARKET, OrderType.LIMIT}),
        cost_schedule=_COSTS[0],
        source="SZSE 2020 ChiNext implementation notice",
        source_publication_date=date(2020, 8, 21),
        provenance_note=(
            "named transition security; excluded because daily bars cannot prove liquidity"
        ),
        source_version="szse-chinext-transition-2020",
    )
