"""Synthetic EOD account isolation, not real source or aggregate-rule admission."""

from dataclasses import replace
from datetime import date
from decimal import Decimal

import pytest

from app.domain.trading import OrderStatus
from app.execution import FixedCommission
from app.paper.runtime import FROZEN_A_SHARE_STRATEGY_ID, ASharePaperTradingRuntime
from tests.test_research_execution_engine import CALENDAR, StarTargetStrategy, _star_session


class DailyStarTarget(StarTargetStrategy):
    strategy_id = FROZEN_A_SHARE_STRATEGY_ID

    def target_for_completed_session(self, session, available_equity):
        # The frozen production strategy is not changed. Exercise repeated daily
        # instructions through its shared execution path using explicit fixtures.
        self.calls = 0
        target = super().target_for_completed_session(session, available_equity)
        target_quantity = self.quantity * Decimal(session.trading_date.day - 1)
        return replace(
            target,
            positions=(replace(target.positions[0], quantity=target_quantity),),
            residual_cash=available_equity - target_quantity * Decimal(10),
        )


def runtime(quantity=100000):
    return ASharePaperTradingRuntime(
        initial_cash=Decimal(10000000),
        commission_model=FixedCommission(),
        calendar=CALENDAR,
        strategy=DailyStarTarget(quantity),
    )


@pytest.mark.parametrize("reverse", [False, True])
async def test_independent_investors_do_not_share_star_daily_quantity_or_replay_state(reverse):
    accounts = [runtime() for _ in range(6)]
    invalid = runtime(100001)
    sessions = tuple(_star_session(date(2024, 1, day), is_st=day >= 3) for day in (2, 3, 4))
    order = tuple(reversed(accounts)) if reverse else tuple(accounts)
    day_fills = []
    for session in sessions:
        deltas = [await account.process_session(session) for account in order]
        rejected = await invalid.process_session(session)
        assert rejected.fills == ()
        for account in accounts:
            # Duplicate delivery is rejected without another strategy/order/fill.
            with pytest.raises(ValueError, match="strictly chronological"):
                await account.process_session(session)
        day_fills.append(sum((fill.quantity for d in deltas for fill in d.fills), Decimal(0)))
        if session.trading_date.day >= 3:
            assert all(len(delta.fills) == 1 for delta in deltas)
            assert all(delta.fills[0].quantity == 100000 for delta in deltas)
            assert len(rejected.execution_checks) == 1
            assert all(reason == "MAXIMUM_QUANTITY" for _, reason in rejected.execution_checks)

    # Six separate investors may exceed500000 in aggregate: never pool accounts.
    assert day_fills == [0, 600000, 600000]
    completed = tuple(account.finish() for account in accounts)
    assert all(result == completed[0] for result in completed)
    assert all(len(result.fills) == len(result.orders) == 2 for result in completed)
    assert all(result.snapshots[-1].cash == 8000000 for result in completed)
    assert all(result.active_reservations == () for result in completed)
    assert all(order.status is OrderStatus.FILLED for order in completed[0].orders)
    assert invalid.finish().fills == ()
    assert len(invalid.finish().orders) == 2
    assert all(order.status is OrderStatus.CANCELLED for order in invalid.finish().orders)

    restored = runtime()
    for session in sessions:
        await restored.process_session(session)
    assert restored.finish() == completed[0]
    assert tuple(account.finish() for account in accounts) == completed
    # Fresh in-memory replay above is not a durable manager/database restart.


async def test_stopping_one_investor_releases_only_its_pending_instruction():
    first, second = runtime(), runtime()
    before = _star_session(date(2024, 1, 2), is_st=False)
    after = _star_session(date(2024, 1, 3), is_st=True)
    first_delta = await first.process_session(before)
    second_delta = await second.process_session(before)
    # Deterministic inner IDs may match: account journals must remain separately scoped.
    assert first_delta.orders[0].id == second_delta.orders[0].id
    cancelled = first.cancel_pending_orders()
    assert len(cancelled) == 1 and cancelled[0].status is OrderStatus.CANCELLED
    stopped = first.finish()
    assert stopped.active_reservations == () and stopped.fills == ()
    executed = await second.process_session(after)
    assert len(executed.fills) == 1 and executed.fills[0].quantity == 100000
    assert first.finish() == stopped
    assert second.finish().snapshots[-1].cash == 9000000
