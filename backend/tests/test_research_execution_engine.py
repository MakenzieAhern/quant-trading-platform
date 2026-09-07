from datetime import date
from decimal import Decimal

from app.data.providers.research import DailyBarRecord, SecurityStatusRecord
from app.domain.markets import DailySecurityStatus, SecurityId
from app.execution import FixedBasisPointSlippage, FixedCommission
from app.research import (
    PortfolioTarget,
    ResearchExecutionEngine,
    ResearchSession,
    TargetPosition,
)

SECURITY_ID = SecurityId(value="CN-A:SSE:600000")


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
        raw_high=Decimal(opening),
        raw_low=Decimal(opening),
        raw_close=Decimal(opening),
        volume=Decimal(10000),
        amount=Decimal(100000),
        adjusted_close=Decimal(opening),
    )
    status = SecurityStatusRecord(
        status=DailySecurityStatus(
            security_id=SECURITY_ID,
            trading_date=trading_date,
            is_st=False,
            is_suspended=suspended,
            is_one_price_limit=one_price_limit,
            source_version="fixture-1",
        )
    )
    return ResearchSession(
        trading_date=trading_date,
        bars=(bar,),
        statuses=(status,),
        buy_lot_sizes=((SECURITY_ID, 100),),
    )


def test_research_order_uses_existing_risk_oms_broker_fill_and_portfolio_path() -> None:
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(Decimal(5)),
        slippage_model=FixedBasisPointSlippage(Decimal(10)),
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="11"),
        )
    )
    assert len(result.proposals) == 1
    assert result.decisions[0].approved is True
    assert len(result.orders) == 1
    assert len(result.fills) == 1
    assert result.fills[0].price == Decimal("11.011")
    assert result.fills[0].commission == Decimal(5)
    assert result.snapshots[-1].cumulative_commission == Decimal(5)
    assert result.active_reservations == ()


def test_suspension_defers_then_end_of_run_expires_order() -> None:
    engine = ResearchExecutionEngine(
        OneTargetStrategy(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
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
    )
    result = engine.run(
        (
            _session(date(2024, 1, 2), opening="10"),
            _session(date(2024, 1, 3), opening="11", one_price_limit=True),
        )
    )
    assert result.fills == ()
    assert len(result.expired_order_ids) == 1
