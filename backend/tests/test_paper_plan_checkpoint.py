"""Offline projection compatibility; no SQL, archive, account or provider acquisition."""

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.application.paper_trading import service
from app.application.paper_trading.service import PaperTradingManager
from app.data.catalog.checksums import canonical_sha256
from app.execution import FixedCommission
from app.paper.models import PaperEventRecord, PaperSession, PaperSessionStatus
from app.paper.runtime import (
    FROZEN_A_SHARE_STRATEGY_ID,
    ASharePaperTradingRuntime,
    SimulatedAShareSessionProvider,
)
from app.research import ResearchSession
from tests.test_research_execution_engine import CALENDAR, OneTargetStrategy, _session

V1 = "PAPER_ACCOUNT_PLAN_V1"
V2 = "PAPER_ACCOUNT_PLAN_V2"
V3 = "PAPER_ACCOUNT_PLAN_V3"


class FixtureStrategy(OneTargetStrategy):
    strategy_id = FROZEN_A_SHARE_STRATEGY_ID


def account(version=V1):
    return PaperSession(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        status=PaperSessionStatus.STARTING,
        provider_type="historical_a_share",
        dataset_id="cn-a-research-20100101-20251231-v1",
        symbol="CN-A",
        strategy_type=FROZEN_A_SHARE_STRATEGY_ID,
        strategy_parameters={
            "start_date": "2024-01-02",
            "end_date": "2024-01-04",
            "rebalance_sessions": 20,
            "maximum_holdings": 20,
            "max_position_weight": "0.1",
            "universe": "ALL",
            "commission_rate": "0.0003",
            "minimum_commission": "5",
            "dataset_sha256": "a" * 64,
            **({"plan_version": version} if version is not None else {}),
        },
        initial_cash=Decimal("10000.000000000000000001"),
        default_order_quantity=Decimal(1),
        risk={"max_drawdown": "-0.2"},
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
        started_at=None,
        stopped_at=None,
        error_message=None,
        client_request_id=None,
        request_hash=None,
    )


def source_runtime(session):
    sessions = (
        _session(date(2024, 1, 2), opening="10"),
        *(
            ResearchSession(trading_date=date(2024, 1, day), bars=(), statuses=(), buy_lot_sizes=())
            for day in (3, 4)
        ),
    )
    return sessions, ASharePaperTradingRuntime(
        initial_cash=session.initial_cash,
        commission_model=FixedCommission(Decimal(5)),
        calendar=CALENDAR,
        strategy=FixtureStrategy(),
    )


async def checkpoint(session, version):
    sessions, runtime = source_runtime(session)
    events = []
    request = PaperTradingManager._historical_request(session)
    for item in sessions[:2]:
        delta = await runtime.process_session(item)
        plan = (
            PaperTradingManager._historical_plan(
                session,
                request,
                delta,
                runtime.next_accepted_session(item.trading_date),
                runtime.completed_sessions,
                version=version,
            )
            if version is not None
            else None
        )
        for kind, timestamp, payload in PaperTradingManager._serialize_a_share_delta(
            delta,
            source=service.HISTORICAL_SOURCE,
            plan=plan,
        ):
            events.append(PaperEventRecord(session.id, len(events) + 1, kind, timestamp, payload))
    events.append(
        PaperEventRecord(
            session.id, len(events) + 1, "session.status", session.created_at, {"status": "PAUSED"}
        )
    )
    return tuple(events)


@pytest.mark.parametrize(
    "version,paused", [(V1, True), (V2, True), (V3, True), (None, True), (V1, False)]
)
async def test_saved_plan_versions_resume_strictly_and_only_new_plans_use_v3(
    monkeypatch, version, paused
):
    initial = account(version)
    history = await checkpoint(initial, version) if paused else ()
    original = repr(history)
    manager = PaperTradingManager(MagicMock(), MagicMock(), MagicMock())
    manager.events = AsyncMock(return_value=history)
    current = initial
    stored = []

    async def transition(session, target, *args, **kwargs):
        nonlocal current
        current = replace(session, status=target)
        return current

    async def append(session_id, events):
        saved = tuple(
            PaperEventRecord(session_id, len(history) + index + 1, kind, timestamp, payload)
            for index, (kind, timestamp, payload) in enumerate(events)
        )
        stored.extend(saved)
        return saved

    manager.get = AsyncMock(side_effect=lambda _: current)
    manager._transition = transition
    monkeypatch.setattr(
        service, "SQLAlchemyPaperRepository", lambda _: SimpleNamespace(append_events=append)
    )

    def build(session, cursor_date):
        sessions, runtime = source_runtime(session)
        return SimulatedAShareSessionProvider(sessions, 0), runtime

    manager._build_runtime = build
    await manager._run(initial)
    assert current.status is PaperSessionStatus.STOPPED
    assert repr(history) == original
    assert [
        item.payload["trading_date"] for item in stored if item.event_type == "market.session"
    ] == (["2024-01-04"] if paused else ["2024-01-02", "2024-01-03", "2024-01-04"])
    snapshots = [item.payload for item in stored if item.event_type == "portfolio.snapshot"]
    latest = snapshots[-1]
    if version is not None:
        assert latest["plan"]["plan_version"] == V3
        assert latest["plan"]["status"] == "ACCOUNT_SNAPSHOT_UNAVAILABLE"
        assert latest["plan"]["account"] is None
        assert latest["plan"]["account_snapshot_trading_date"] is None
    else:
        assert "plan" not in latest  # Original pre-plan accounts retain their event contract.
    if not paused:
        assert initial.strategy_parameters["plan_version"] == V1
        assert all(item["plan"]["plan_version"] == V3 for item in snapshots)
        assert snapshots[0]["plan"]["account_snapshot_trading_date"] == "2024-01-02"
        return  # This fixture has never paused; do not fabricate a resume marker.

    # Resume again across mixed saved/current history: no duplicate event or financial change.
    history = (*history, *stored)
    manager.events.return_value = history
    stored.clear()
    current = replace(initial, status=PaperSessionStatus.STARTING)
    await manager._run(current)
    assert current.status is PaperSessionStatus.STOPPED
    assert stored == []

    # Exact comparison remains mandatory: altered cash may never admit new market events.
    damaged = tuple(
        replace(item, payload={**item.payload, "cash": "0"})
        if item.event_type == "portfolio.snapshot"
        else item
        for item in history
    )
    manager.events.return_value = damaged
    current = replace(initial, status=PaperSessionStatus.STARTING)
    await manager._run(current)
    assert current.status is PaperSessionStatus.FAILED
    assert stored == []


async def test_legacy_projection_reproduces_old_stale_account_but_new_projection_refuses_it():
    initial = account()
    history = await checkpoint(initial, V1)
    stale = [item.payload["plan"] for item in history if item.event_type == "portfolio.snapshot"][
        -1
    ]
    assert stale["as_of_trading_date"] == "2024-01-03"
    assert stale["status"] == "INSUFFICIENT_WARMUP"
    assert stale["account"]["cash"] == "10000.000000000000000001"
    # Captured from the unmodified e2a3aa9 builder, not a new-version self-comparison.
    assert canonical_sha256(stale) == (
        "31d2998d1b1b25990a98c3c9f2fa5fb98525f9f35d7d790c2c5e46e693fd37c0"
    )
    sessions, runtime = source_runtime(initial)
    await runtime.process_session(sessions[0])
    delta = await runtime.process_session(sessions[1])
    request = PaperTradingManager._historical_request(initial)
    new = PaperTradingManager._historical_plan(initial, request, delta, date(2024, 1, 4), 2)
    assert new["status"] == "ACCOUNT_SNAPSHOT_UNAVAILABLE"
    assert new["account"] is None and new["candidates"] == []
    assert new["estimated_cash_required"] is None
    with pytest.raises(ValueError, match="unsupported"):
        PaperTradingManager._historical_plan(
            initial, request, delta, date(2024, 1, 4), 2, version="PAPER_ACCOUNT_PLAN_V4"
        )


async def test_original_v2_projection_remains_byte_identical_without_new_metadata():
    history = await checkpoint(account(V2), V2)
    plans = [item.payload["plan"] for item in history if item.event_type == "portfolio.snapshot"]
    assert all("account_snapshot_trading_date" not in item for item in plans)
    # Captured from unmodified ddc1f24, before adding the V3 metadata.
    assert [canonical_sha256(item) for item in plans] == [
        "82ed1233c54dce4d658149a1f14df8b3c8b1116fc62f45f0ee59c5a9050c9dfa",
        "34fa94cc478079e0021dc6f900fb1105f6ff6cc00c0e95a8591cfb7f734b3ccb",
    ]
