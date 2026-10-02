"""Offline causal-calendar checks through the real paper manager, not a forward feed."""

import asyncio
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.api.schemas.paper import PaperEventResponse
from app.application.paper_trading import service
from app.application.paper_trading.service import PaperTradingManager
from app.data.catalog.checksums import canonical_sha256
from app.domain.markets.calendar import TradingCalendar
from app.execution import FixedCommission
from app.paper.models import PaperEventRecord, PaperSessionStatus
from app.paper.runtime import ASharePaperTradingRuntime, SimulatedAShareSessionProvider
from tests.test_paper_plan_checkpoint import FixtureStrategy, account
from tests.test_research_execution_engine import CALENDAR, _session

INITIAL = TradingCalendar(market=CALENDAR.market, sessions=CALENDAR.sessions[:1])
FIRST = _session(date(2024, 1, 2), opening="10")
SECOND = _session(date(2024, 1, 3), opening="9.9")
NOW = datetime(2026, 10, 3, tzinfo=UTC)


def manager_with_journal(
    monkeypatch,
    *,
    pause_after_extension=False,
    fail_write=False,
    stream=None,
    start_date="2024-01-02",
    base_calendar=INITIAL,
    pause_on_calendar=CALENDAR,
):
    original = account("PAPER_ACCOUNT_PLAN_V3")
    initial = replace(
        original, strategy_parameters={**original.strategy_parameters, "start_date": start_date}
    )
    journal = []
    current = initial
    manager = PaperTradingManager(MagicMock(), MagicMock(), MagicMock(), clock=lambda: NOW)
    manager.events = AsyncMock(side_effect=lambda _: tuple(journal))
    manager.get = AsyncMock(side_effect=lambda _: current)
    runtimes = []
    manager.calendar_write_attempts = 0
    pause_requested = False

    def publish(session_id, event):
        if event["type"] == "calendar.observed":
            assert journal[event["sequence"] - 1].payload == event["payload"]
            assert (
                canonical_sha256(runtimes[-1].calendar.model_dump(mode="json"))
                == event["payload"]["after_sha256"]
            )

    manager.hub.publish = MagicMock(side_effect=publish)

    async def transition(session, target, *args, **kwargs):
        nonlocal current
        current = replace(session, status=target)
        journal.append(
            PaperEventRecord(
                session.id, len(journal) + 1, "session.status", NOW, {"status": target.value}
            )
        )
        return current

    async def append(session_id, events):
        if events[0][0] == "calendar.observed":
            manager.calendar_write_attempts += 1
        if events[0][0] == "calendar.observed" and (
            fail_write is True or fail_write == events[0][2]["kind"]
        ):
            raise RuntimeError("fixture commit failure")
        saved = tuple(
            PaperEventRecord(session_id, len(journal) + index + 1, kind, timestamp, payload)
            for index, (kind, timestamp, payload) in enumerate(events)
        )
        journal.extend(saved)
        return saved

    manager._transition = transition
    monkeypatch.setattr(
        service, "SQLAlchemyPaperRepository", lambda _: SimpleNamespace(append_events=append)
    )

    def build(session, cursor_date, initial_calendar=None):
        # On resume the source already knows the expanded calendar. Only the durable
        # initial observation may select the reconstruction calendar, not this final one.
        calendar = initial_calendar or (CALENDAR if cursor_date else base_calendar)
        runtime = ASharePaperTradingRuntime(
            initial_cash=session.initial_cash,
            commission_model=FixedCommission(),
            calendar=calendar,
            strategy=FixtureStrategy(),
        )
        runtimes.append(runtime)
        items = stream() if callable(stream) else stream
        if items is None:
            items = (INITIAL, FIRST, CALENDAR, CALENDAR, SECOND)
        provider = SimulatedAShareSessionProvider(items, 0)
        original_start = provider.start

        async def start(handler):
            async def consume(item):
                nonlocal pause_requested
                await handler(item)
                if pause_after_extension and not pause_requested and item is pause_on_calendar:
                    pause_requested = True
                    await manager.pause(session.id)

            await original_start(consume)

        provider.start = start
        return provider, runtime

    manager._build_runtime = build
    return manager, initial, journal, runtimes


async def test_calendar_knowledge_is_durable_and_resume_does_not_create_past_intent(monkeypatch):
    manager, initial, journal, runtimes = manager_with_journal(
        monkeypatch, pause_after_extension=True
    )
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.PAUSED
    controls = [item for item in journal if item.event_type == "calendar.observed"]
    assert [item.payload["kind"] for item in controls] == ["initial", "extension"]
    assert [item.payload["after_completed_sessions"] for item in controls] == [0, 1]
    assert controls[0].payload["after_sha256"] == canonical_sha256(INITIAL.model_dump(mode="json"))
    assert controls[1].payload["before_sha256"] == controls[0].payload["after_sha256"]
    assert all(item.occurred_at == NOW for item in controls)
    assert runtimes[0].completed_sessions == 1  # Paused after a committed trailing extension.
    before = repr(journal)
    before_count = len(journal)
    await manager.shutdown()
    await manager.start(initial.id)
    await manager._tasks[initial.id]
    assert (await manager.get(initial.id)).status is PaperSessionStatus.STOPPED
    assert repr(journal[:before_count]) == before
    assert len([item for item in journal if item.event_type == "calendar.observed"]) == 2
    assert [
        item.payload["trading_date"] for item in journal if item.event_type == "market.session"
    ] == ["2024-01-02", "2024-01-03"]
    assert not any(item.event_type in {"order.updated", "fill.created"} for item in journal)
    assert runtimes[-1].completed_sessions == 2
    assert runtimes[-1].finish().snapshots[-1].cash == Decimal("10000.000000000000000001")

    baseline, baseline_initial, uninterrupted, _ = manager_with_journal(monkeypatch)
    await baseline._run(baseline_initial)

    def financial(events):
        return [
            (item.event_type, item.payload)
            for item in events
            if item.event_type not in {"session.status", "calendar.observed"}
        ]

    assert financial(journal) == financial(uninterrupted)


async def test_calendar_commit_failure_never_publishes_or_consumes_market(monkeypatch):
    manager, initial, journal, runtimes = manager_with_journal(monkeypatch, fail_write=True)
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.FAILED
    assert runtimes[0].completed_sessions == 0
    assert all(item.event_type == "session.status" for item in journal)
    assert manager.calendar_write_attempts == 1
    manager.hub.publish.assert_not_called()


async def test_extension_write_failure_keeps_previous_calendar_and_market_checkpoint(monkeypatch):
    manager, initial, journal, runtimes = manager_with_journal(monkeypatch, fail_write="extension")
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.FAILED
    assert runtimes[0].completed_sessions == 1 and runtimes[0].calendar == INITIAL
    assert [item.payload["kind"] for item in journal if item.event_type == "calendar.observed"] == [
        "initial"
    ]
    assert [
        item.payload["trading_date"] for item in journal if item.event_type == "market.session"
    ] == ["2024-01-02"]
    assert not any(
        call.args[1]["payload"].get("kind") == "extension"
        for call in manager.hub.publish.call_args_list
    )


async def test_initial_observation_cannot_disguise_final_calendar_as_prior_knowledge(monkeypatch):
    manager, initial, journal, runtimes = manager_with_journal(monkeypatch, base_calendar=CALENDAR)
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.FAILED
    assert runtimes[0].completed_sessions == manager.calendar_write_attempts == 0
    assert all(item.event_type == "session.status" for item in journal)


async def test_initial_only_pause_restores_knowledge_without_duplicate_control(monkeypatch):
    manager, initial, journal, _ = manager_with_journal(
        monkeypatch,
        pause_after_extension=True,
        pause_on_calendar=INITIAL,
        stream=(INITIAL, CALENDAR, FIRST, SECOND),
    )
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.PAUSED
    assert not any(item.event_type == "market.session" for item in journal)
    await manager.start(initial.id)
    await manager._tasks[initial.id]
    assert (await manager.get(initial.id)).status is PaperSessionStatus.STOPPED
    assert [item.payload["kind"] for item in journal if item.event_type == "calendar.observed"] == [
        "initial",
        "extension",
    ]


async def test_calendar_extension_after_warmup_is_restored_before_first_visible_market(monkeypatch):
    manager, initial, journal, runtimes = manager_with_journal(
        monkeypatch, pause_after_extension=True, start_date="2024-01-03"
    )
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.PAUSED
    assert runtimes[0].completed_sessions == 1
    assert not any(item.event_type == "market.session" for item in journal)
    await manager.start(initial.id)
    await manager._tasks[initial.id]
    assert (await manager.get(initial.id)).status is PaperSessionStatus.STOPPED
    assert [
        item.payload["trading_date"] for item in journal if item.event_type == "market.session"
    ] == ["2024-01-03"]
    assert runtimes[-1].completed_sessions == 2


@pytest.mark.parametrize("damage", ["checksum", "chain", "count", "prefix", "version"])
async def test_damaged_calendar_timeline_refuses_new_market(monkeypatch, damage):
    manager, initial, journal, _ = manager_with_journal(monkeypatch, pause_after_extension=True)
    await manager._run(initial)
    extension = next(
        i
        for i, item in enumerate(journal)
        if item.event_type == "calendar.observed" and item.payload["kind"] == "extension"
    )
    payload = dict(journal[extension].payload)
    if damage == "checksum":
        payload["after_sha256"] = "b" * 64
    elif damage == "chain":
        payload["before_sha256"] = "b" * 64
    elif damage == "count":
        payload["after_completed_sessions"] = 50
    elif damage == "version":
        payload["schema_version"] = "PAPER_CALENDAR_V2"
    else:
        calendar = CALENDAR.model_dump(mode="json")
        calendar["sessions"][0]["source_version"] = "rewritten"
        payload["calendar"] = calendar
        payload["after_sha256"] = canonical_sha256(calendar)
    journal[extension] = replace(journal[extension], payload=payload)
    before = tuple(journal)
    await manager.start(initial.id)
    await manager._tasks[initial.id]
    assert (await manager.get(initial.id)).status is PaperSessionStatus.FAILED
    assert tuple(journal[: len(before)]) == before
    assert not any(item.payload.get("trading_date") == "2024-01-03" for item in journal)
    assert manager.calendar_write_attempts == 2


async def test_calendar_does_not_backfill_unanchored_legacy_account(monkeypatch):
    manager, initial, journal, _ = manager_with_journal(monkeypatch, pause_after_extension=True)
    await manager._run(initial)
    journal[:] = [item for item in journal if item.event_type != "calendar.observed"]
    before = tuple(journal)
    await manager.start(initial.id)
    await manager._tasks[initial.id]
    assert (await manager.get(initial.id)).status is PaperSessionStatus.FAILED
    assert tuple(journal[: len(before)]) == before
    assert manager.calendar_write_attempts == 2


async def test_calendar_rest_contract_is_typed_utc_and_strict(monkeypatch):
    manager, initial, journal, _ = manager_with_journal(monkeypatch)
    await manager._run(initial)
    control = next(item for item in journal if item.event_type == "calendar.observed")
    wire = manager._wire_event(control)
    assert PaperEventResponse.model_validate(wire).type == "calendar.observed"
    payload = wire["payload"]
    for altered in (
        {**payload, "extra": "not accepted"},
        {**payload, "applied_at": "2026-10-03T08:00:00+08:00"},
        {**payload, "after_completed_sessions": True},
        {"status": "RUNNING"},
    ):
        with pytest.raises(ValidationError):
            PaperEventResponse.model_validate({**wire, "payload": altered})
    damaged_calendar = INITIAL.model_dump(mode="json")
    damaged_calendar["sessions"][0]["is_open"] = 1
    with pytest.raises(ValidationError):
        PaperEventResponse.model_validate(
            {**wire, "payload": {**payload, "calendar": damaged_calendar}}
        )


async def test_pause_winning_calendar_lock_is_paused_not_failed(monkeypatch):
    manager, initial, journal, runtimes = manager_with_journal(monkeypatch)
    original_build = manager._build_runtime

    def build(session, cursor_date, initial_calendar=None):
        provider, runtime = original_build(session, cursor_date, initial_calendar)

        async def start(handler):
            await manager._lock.acquire()
            try:
                pausing = asyncio.create_task(manager.pause(session.id))
                observing = asyncio.create_task(handler(INITIAL))
                await asyncio.sleep(0)  # Both commands queued; pause requested first.
            finally:
                manager._lock.release()
            await pausing
            await observing

        provider.start = start
        return provider, runtime

    manager._build_runtime = build
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.PAUSED
    assert manager.calendar_write_attempts == 0
    assert runtimes[0].completed_sessions == 0
    assert all(item.event_type == "session.status" for item in journal)


async def test_warmup_count_cannot_substitute_for_the_recorded_trading_date(monkeypatch):
    seed = TradingCalendar(market=CALENDAR.market, sessions=CALENDAR.sessions[:2])
    third = _session(date(2024, 1, 4), opening="9.8")
    manager, initial, journal, _ = manager_with_journal(
        monkeypatch,
        pause_after_extension=True,
        start_date="2024-01-04",
        base_calendar=seed,
        stream=(seed, FIRST, CALENDAR, SECOND, third),
    )
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.PAUSED
    assert not any(item.event_type == "market.session" for item in journal)
    build_with_correct_initial = manager._build_runtime

    def missing_first_warmup(session, cursor_date, initial_calendar=None):
        _, runtime = build_with_correct_initial(session, cursor_date, initial_calendar)
        return SimulatedAShareSessionProvider((seed, CALENDAR, SECOND, third), 0), runtime

    manager._build_runtime = missing_first_warmup
    before = tuple(journal)
    await manager.start(initial.id)
    await manager._tasks[initial.id]
    assert (await manager.get(initial.id)).status is PaperSessionStatus.FAILED
    assert tuple(journal[: len(before)]) == before
    assert not any(item.event_type == "market.session" for item in journal)


@pytest.mark.parametrize("command", ["pause", "stop", "source_ends"])
async def test_resume_can_pause_or_stop_before_trailing_calendar_replay(monkeypatch, command):
    manager, initial, journal, _ = manager_with_journal(monkeypatch, pause_after_extension=True)
    await manager._run(initial)
    assert (await manager.get(initial.id)).status is PaperSessionStatus.PAUSED
    before = tuple(journal)
    original_build = manager._build_runtime

    def build(session, cursor_date, initial_calendar=None):
        _, runtime = original_build(session, cursor_date, initial_calendar)
        provider = SimulatedAShareSessionProvider((INITIAL,), 0)
        original_start = provider.start

        async def start(handler):
            async def consume(item):
                await handler(item)
                if command != "source_ends":
                    await getattr(manager, command)(session.id)

            await original_start(consume)

        provider.start = start
        return provider, runtime

    manager._build_runtime = build
    await manager.start(initial.id)
    await manager._tasks[initial.id]
    expected = {
        "pause": PaperSessionStatus.PAUSED,
        "stop": PaperSessionStatus.STOPPED,
        "source_ends": PaperSessionStatus.FAILED,
    }[command]
    assert (await manager.get(initial.id)).status is expected
    assert tuple(journal[: len(before)]) == before
    assert all(item.event_type == "session.status" for item in journal[len(before) :])


@pytest.mark.parametrize("command", ["pause", "stop", "shutdown"])
async def test_manager_can_end_waiting_for_async_session_without_financial_events(
    monkeypatch, command
):
    waiting = asyncio.Event()
    closed = asyncio.Event()

    async def source():
        try:
            yield INITIAL
            waiting.set()
            await asyncio.Event().wait()
            yield FIRST
        finally:
            closed.set()

    manager, initial, journal, runtimes = manager_with_journal(monkeypatch, stream=source())
    task = asyncio.create_task(manager._run(initial))
    manager._tasks[initial.id] = task  # Same owned task as the normal start dispatcher.
    try:
        await asyncio.wait_for(waiting.wait(), 1)
        before = tuple(journal)
        assert (await manager.get(initial.id)).status is PaperSessionStatus.RUNNING
        assert [item.event_type for item in journal].count("calendar.observed") == 1
        if command == "shutdown":
            await asyncio.wait_for(manager.shutdown(), 1)
            assert task.cancelled()
        else:
            await getattr(manager, command)(initial.id)
            await asyncio.wait_for(task, 1)
        assert (await manager.get(initial.id)).status is {
            "pause": PaperSessionStatus.PAUSED,
            "stop": PaperSessionStatus.STOPPED,
            "shutdown": PaperSessionStatus.INTERRUPTED,
        }[command]
        assert tuple(journal[: len(before)]) == before
        assert all(item.event_type == "session.status" for item in journal[len(before) :])
        assert closed.is_set() and runtimes[0].completed_sessions == 0
        assert initial.id not in manager._providers
    finally:
        await manager.shutdown()


async def test_async_session_provider_resume_rebuilds_fresh_source_and_preserves_journal(
    monkeypatch,
):
    waiting = asyncio.Event()
    closed = []
    sources = 0

    async def source():
        nonlocal sources
        sources += 1
        index = sources
        try:
            yield INITIAL
            yield FIRST
            yield CALENDAR
            if index == 1:
                waiting.set()
                await asyncio.Event().wait()
            yield SECOND
        finally:
            closed.append(index)

    manager, initial, journal, runtimes = manager_with_journal(monkeypatch, stream=source)
    task = asyncio.create_task(manager._run(initial))
    manager._tasks[initial.id] = task
    try:
        await asyncio.wait_for(waiting.wait(), 1)
        await manager.pause(initial.id)
        await asyncio.wait_for(task, 1)
        assert (await manager.get(initial.id)).status is PaperSessionStatus.PAUSED
        before = tuple(journal)
        await manager.start(initial.id)
        await asyncio.wait_for(manager._tasks[initial.id], 1)
        assert (await manager.get(initial.id)).status is PaperSessionStatus.STOPPED
        assert tuple(journal[: len(before)]) == before
        assert sources == 2 and closed == [1, 2]
        assert [
            item.payload["trading_date"] for item in journal if item.event_type == "market.session"
        ] == ["2024-01-02", "2024-01-03"]
        assert [
            item.payload["kind"] for item in journal if item.event_type == "calendar.observed"
        ] == [
            "initial",
            "extension",
        ]
        assert not any(item.event_type in {"order.updated", "fill.created"} for item in journal)
        assert runtimes[-1].completed_sessions == 2
        assert runtimes[-1].finish().snapshots[-1].cash == initial.initial_cash
    finally:
        await manager.shutdown()
