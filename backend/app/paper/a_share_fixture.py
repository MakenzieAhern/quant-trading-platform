from datetime import date, timedelta
from decimal import Decimal

from app.data.providers.research import DailyBarRecord, SecurityStatusRecord
from app.domain.markets import DailySecurityStatus, Market, SecurityId
from app.domain.markets.calendar import TradingCalendar, TradingSession
from app.domain.markets.rules import (
    PriceLimitModel,
    ResolvedTradingRules,
    TransactionCostSchedule,
)
from app.domain.trading import OrderType
from app.research.costs import EffectiveDatedAShareCommission
from app.research.models import ResearchSession

SIMULATED_A_SHARE_DATASET_ID = "CN_A_SIMULATED_PAPER_FIXTURE_V1"
SIMULATED_A_SHARE_SYMBOL = "CN-A"
SIMULATED_SOURCE = "SIMULATED_SCENARIO_NOT_RESEARCH_EVIDENCE_V1"


def simulated_a_share_fixture() -> tuple[
    TradingCalendar,
    tuple[ResearchSession, ...],
    EffectiveDatedAShareCommission,
]:
    """Build a small deterministic future scenario; never replay formal OOS data."""

    days: list[date] = []
    current = date(2030, 1, 2)
    while len(days) < 254:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    cost = TransactionCostSchedule(
        commission_rate=Decimal(0),
        minimum_commission=Decimal(0),
        sell_stamp_duty_rate=Decimal(0),
        transfer_fee_rate=Decimal(0),
        valid_from=days[0],
        source_version=SIMULATED_SOURCE,
    )
    securities = tuple(SecurityId(value=f"CN-A:SSE:{600000 + index:06d}") for index in range(10))
    previous = {security_id: Decimal(10 + index) for index, security_id in enumerate(securities)}
    sessions = []
    for session_index, trading_date in enumerate(days):
        bars, statuses, lots, rules = [], [], [], []
        for security_index, security_id in enumerate(securities):
            trend = Decimal(security_index + 1) / Decimal(10000)
            cycle = Decimal((session_index + security_index * 3) % 7 - 3) / Decimal(1000)
            close = (
                Decimal(10 + security_index) * (Decimal(1) + trend * session_index + cycle)
            ).quantize(Decimal("0.001"))
            prior = previous[security_id]
            if session_index == len(days) - 1:
                close = prior
            previous[security_id] = close
            bars.append(
                DailyBarRecord(
                    security_id=security_id,
                    trading_date=trading_date,
                    raw_open=close,
                    raw_high=(close * Decimal("1.01")).quantize(Decimal("0.001")),
                    raw_low=(close * Decimal("0.99")).quantize(Decimal("0.001")),
                    raw_close=close,
                    volume=Decimal(1000000000 + security_index * 10000000),
                    amount=Decimal(30000000 + security_index * 1000000),
                    adjusted_close=close,
                    pre_close=prior,
                )
            )
            status = DailySecurityStatus(
                security_id=security_id,
                trading_date=trading_date,
                is_st=False,
                is_suspended=False,
                is_tradeable=True,
                is_one_price_limit=False,
                source_version=SIMULATED_SOURCE,
            )
            statuses.append(SecurityStatusRecord(status=status))
            lots.append((security_id, 100))
            rules.append(
                ResolvedTradingRules(
                    security_id=security_id,
                    trading_date=trading_date,
                    buy_lot_size=100,
                    minimum_buy_quantity=100,
                    buy_quantity_increment=100,
                    odd_lot_sell_only=True,
                    minimum_tick=Decimal("0.001"),
                    maximum_limit_quantity=10000000,
                    price_limit_model=PriceLimitModel.PERCENT_FROM_PREVIOUS_CLOSE,
                    price_limit_rate=Decimal("0.1"),
                    suspended=False,
                    executable=True,
                    t_plus_one_sale=True,
                    permitted_order_types=frozenset({OrderType.LIMIT}),
                    cost_schedule=cost,
                    rule_source_version=SIMULATED_SOURCE,
                )
            )
        sessions.append(
            ResearchSession(
                trading_date=trading_date,
                bars=tuple(bars),
                statuses=tuple(statuses),
                buy_lot_sizes=tuple(lots),
                trading_rules=tuple(rules),
            )
        )
    calendar = TradingCalendar(
        market=Market.CN_A,
        sessions=tuple(
            TradingSession(session_date=day, is_open=True, source_version=SIMULATED_SOURCE)
            for day in days
        ),
    )
    return calendar, tuple(sessions), EffectiveDatedAShareCommission((cost,))
