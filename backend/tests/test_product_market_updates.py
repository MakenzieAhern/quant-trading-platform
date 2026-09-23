"""Offline fixture tests only. Never contact a provider or the application database."""

import asyncio
import json
import sys
from contextlib import asynccontextmanager
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.api.routes import market_updates as routes
from app.application.market_updates import transport, worker
from app.application.market_updates.cache import ReceiptCache
from app.application.market_updates.contracts import (
    AUTHORITY,
    FIELDS,
    CreateUpdateRequest,
    UpdateCancelled,
    UpdateConflict,
    UpdateError,
    latest_publishable_date,
    missing_chunks,
    parse_response,
)
from app.application.market_updates.service import MarketUpdateManager
from app.application.market_updates.worker import check_result
from app.core.config import get_settings
from app.data.catalog.checksums import canonical_sha256
from app.db.models.market_updates import MarketReceiptModel, MarketUpdateJobModel
from app.db.session import SessionFactory, engine

SID = "CN-A:SSE:600000"
NOW = datetime(2026, 9, 22, 10, 0, tzinfo=UTC)


def request(start="2026-09-18", end="2026-09-21"):
    return CreateUpdateRequest(security_ids=[SID], start_date=start, end_date=end)


def envelope(day="2026-09-18", **overrides):
    row = {
        "date": day,
        "code": "sh.600000",
        "open": "10.123456789123456789",
        "high": "11",
        "low": "9",
        "close": "10.5",
        "preclose": "10",
        "volume": "100",
        "amount": "1020.123456789123456789",
        "adjustflag": "3",
        "tradestatus": "1",
        "isST": "0",
        **overrides,
    }
    return {
        "fields": FIELDS.split(","),
        "rows": [[row[field] for field in FIELDS.split(",")]],
        "requested_at_utc": (NOW - timedelta(seconds=2)).isoformat(),
        "response_completed_at_utc": (NOW - timedelta(seconds=1)).isoformat(),
    }


class FixtureReader:
    def __init__(self, path):
        self.registry = SimpleNamespace(
            root=path,
            resolve=lambda _: {
                "coverage_end": "2025-12-31",
                "sha256": "a" * 64,
            },
            datasets=lambda: [],
        )

    def security(self, dataset, sid):
        if sid not in {SID, "CN-A:SZSE:000001"}:
            raise LookupError("SECURITY_NOT_FOUND")
        return {"security_id": sid, "listed_from": "2000-01-01", "listed_to": None}


@pytest.fixture
async def manager(tmp_path, monkeypatch):
    assert get_settings().app_env == "test"
    assert "quant_test" in get_settings().database_url
    async with SessionFactory() as db, db.begin():
        await db.execute(
            text(
                "TRUNCATE product_market_observations, product_market_receipts, "
                "product_market_update_jobs"
            )
        )
    calls = []

    async def fixture_fetch(parameters, cancelled):
        calls.append(parameters)
        result = envelope(parameters["start_date"], code=parameters["code"])
        return result, NOW - timedelta(seconds=2), NOW

    manager = MarketUpdateManager(
        SessionFactory,
        engine,
        FixtureReader(tmp_path / "archive"),
        tmp_path / "cache",
        transport=fixture_fetch,
        request_interval=0,
        now=lambda: NOW,
    )
    manager.test_calls = calls
    monkeypatch.setattr(routes, "market_update_manager", manager)
    yield manager
    await manager.shutdown()


async def terminal(manager, identifier):
    async with asyncio.timeout(5):
        while True:
            row = await manager.get(identifier)
            if row.status in {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                return row
            await asyncio.sleep(0.01)


def test_bounds_missing_chunks_and_publication_clock():
    whole = request("2026-01-01", "2026-12-31")
    chunks = missing_chunks(whole.start_date, whole.end_date, {date(2026, 1, 15)})
    assert len(chunks) == 13
    assert all((last - first).days <= 30 for first, last in chunks)
    assert not any(first <= date(2026, 1, 15) <= last for first, last in chunks)
    assert latest_publishable_date(datetime(2026, 9, 22, 9, 29, tzinfo=UTC)) == date(2026, 9, 21)
    assert latest_publishable_date(datetime(2026, 9, 22, 9, 30, tzinfo=UTC)) == date(2026, 9, 22)
    for payload in (
        {"security_ids": [SID, SID]},
        {"security_ids": ["../600000"]},
        {"security_ids": [SID] * 21},
        {"security_ids": []},
        {"url": "https://untrusted"},
        {"end_date": "2028-09-21"},
        {"end_date": "2026-01-01"},
    ):
        with pytest.raises(ValidationError):
            CreateUpdateRequest.model_validate({**request().model_dump(mode="json"), **payload})


@pytest.mark.parametrize(
    "changes",
    [
        {"close": "12"},
        {"amount": "-1"},
        {"open": "NaN"},
        {"volume": 10},
        {"isST": ""},
        {"tradestatus": "UNKNOWN"},
        {"adjustflag": "2"},
        {"code": "sz.000001"},
        {"date": "2025-01-01"},
        {"open": "1e100"},
        {"tradestatus": "0", "volume": "100"},
        {"tradestatus": "1", "volume": "", "amount": ""},
        {"tradestatus": "0", "volume": "", "amount": "1"},
    ],
)
def test_parser_fail_closed(changes):
    with pytest.raises(UpdateError, match="INVALID_PROVIDER_RESPONSE"):
        parse_response(envelope(**changes), SID, date(2026, 9, 18), date(2026, 9, 21))


def test_parser_exact_suspension_st_and_duplicate():
    parsed = parse_response(
        envelope(tradestatus="0", volume="0", amount="0", isST="1"),
        SID,
        date(2026, 9, 18),
        date(2026, 9, 21),
    )
    assert parsed[0]["raw"]["open"] == "10.123456789123456789"
    assert parsed[0]["status"] == "VENDOR_SUSPENDED"
    assert parsed[0]["provider_is_st"] == "1" and not parsed[0]["execution_eligible"]
    blank = parse_response(
        envelope(tradestatus="0", volume="", amount=""),
        SID,
        date(2026, 9, 18),
        date(2026, 9, 21),
    )
    assert blank[0]["raw"]["volume"] == blank[0]["raw"]["amount"] == "0"
    assert blank[0]["status"] == "VENDOR_SUSPENDED" and not blank[0]["execution_eligible"]
    duplicate = envelope()
    duplicate["rows"] *= 2
    with pytest.raises(UpdateError):
        parse_response(duplicate, SID, date(2026, 9, 18), date(2026, 9, 21))


def test_cache_separation_atomic_repeat_and_corruption(tmp_path):
    with pytest.raises(UpdateError):
        ReceiptCache(tmp_path / "archive" / "nested", tmp_path / "archive")
    cache = ReceiptCache(tmp_path / "cache", tmp_path / "archive")
    raw = {"fields": [], "rows": []}
    evidence = {"raw_response_sha256": canonical_sha256(raw)}
    first = cache.publish(raw, [], evidence)
    assert cache.publish(raw, [], evidence) == first
    manifest = cache.verify(first)
    assert not list(cache.root.glob(".receipt-*"))
    (cache.root / manifest["raw"]["path"]).write_bytes(b"corrupt fixture")
    with pytest.raises(UpdateError, match="PRODUCT_CACHE_INTEGRITY_FAILED"):
        cache.verify(first)
    with pytest.raises(UpdateError):
        cache.verify("../untrusted")


async def test_create_idempotency_exact_receipts_persistence_missing_only(manager):
    first, repeated = await asyncio.gather(
        manager.create(request(), "same"), manager.create(request(), "same")
    )
    assert first.id == repeated.id
    with pytest.raises(UpdateConflict):
        await manager.create(request(end="2026-09-20"), "same")
    await manager.start()
    done = await terminal(manager, first.id)
    assert done.status == "SUCCEEDED"
    assert done.completed_requests == done.total_requests == 1
    assert done.summary["new_observations"] == 1
    assert done.summary["unresolved_date_count"] == 3
    assert not done.summary["authority"]["execution_eligible"]
    receipts, total = await manager.receipts(done.id, 1, 0)
    assert total == 1
    assert receipts[0]["received_at_utc"] == NOW.isoformat()
    assert (
        receipts[0]["requested_at_utc"]
        < receipts[0]["response_completed_at_utc"]
        < receipts[0]["received_at_utc"]
    )
    assert (
        receipts[0]["raw_response_representation"] == "SDK_DECODED_FIELDS_AND_ROWS_NOT_WIRE_BYTES"
    )
    values = await manager.observations(SID, request().start_date, request().end_date)
    assert values[0]["raw"]["amount"] == "1020.123456789123456789"
    second = await manager.create(request(), "new-user-request")
    done2 = await terminal(manager, second.id)
    assert done2.status == "SUCCEEDED"
    assert manager.test_calls[1]["start_date"] == "2026-09-19"
    assert done2.summary["cached_observations_skipped"] == 1
    assert (await manager.receipts(done.id, 1, 1)) == ([], 1)
    assert (await manager.list_jobs(1, 0))[1] == 2
    # Database itself prevents altering accepted first-seen evidence.
    async with SessionFactory() as db:
        with pytest.raises(DBAPIError, match="append only"):
            await db.execute(text("UPDATE product_market_receipts SET evidence = '{}'::jsonb"))
        await db.rollback()
    await manager.shutdown()
    reopened = MarketUpdateManager(
        SessionFactory,
        engine,
        manager.reader,
        manager.cache.root,
        transport=manager.transport,
        request_interval=0,
        now=lambda: NOW,
    )
    assert (await reopened.receipts(done.id, 1, 0)) == (receipts, total)


async def test_empty_response_remains_unknown_not_holiday_or_suspension(manager):
    async def empty(parameters, cancelled):
        response = envelope()
        response["rows"] = []
        return response, NOW - timedelta(seconds=2), NOW

    manager.transport = empty
    job = await manager.create(request(), "empty")
    await manager.start()
    done = await terminal(manager, job.id)
    assert done.status == "SUCCEEDED" and done.summary["unresolved_date_count"] == 4
    assert done.summary["observations_available"] == 0
    assert (await manager.receipts(job.id, 20, 0))[0][0]["row_count"] == 0


async def test_invalid_source_no_publication_and_bounded_retry_denial_circuit(manager):
    calls = 0

    async def unavailable(parameters, cancelled):
        nonlocal calls
        calls += 1
        raise UpdateError("PROVIDER_TIMEOUT")

    manager.transport = unavailable
    job = await manager.create(request(), "unavailable")
    await manager.start()
    assert (await terminal(manager, job.id)).error_code == "PROVIDER_TIMEOUT"
    assert calls == 3

    async def denied(parameters, cancelled):
        nonlocal calls
        calls += 1
        raise UpdateError("SOURCE_ACCESS_DENIED")

    manager.transport = denied
    retry = await manager.retry(job.id, "denied")
    assert (await terminal(manager, retry.id)).error_code == "SOURCE_ACCESS_DENIED"
    assert calls == 4
    assert (await manager.receipts(job.id, 20, 0))[1] == 0
    with pytest.raises(UpdateConflict, match="SOURCE_ACCESS_DENIED"):
        await manager.create(request(), "no-bypass")


async def test_cancel_running_retry_and_interrupt_recovery(manager):
    entered = asyncio.Event()
    original = manager.transport

    async def waiting(parameters, cancelled):
        entered.set()
        await cancelled.wait()
        raise UpdateCancelled

    manager.transport = waiting
    job = await manager.create(request(), "running")
    await manager.start()
    await asyncio.wait_for(entered.wait(), 3)
    await manager.cancel(job.id)
    assert (await terminal(manager, job.id)).status == "CANCELLED"
    assert (await manager.receipts(job.id, 20, 0))[1] == 0
    manager.transport = original
    retry = await manager.retry(job.id, "retry")
    assert retry.retry_of == job.id and retry.attempt == 2
    assert (await terminal(manager, retry.id)).status == "SUCCEEDED"
    await manager.shutdown()
    # A crash leaves RUNNING; next owner marks interrupted without resuming acquisition.
    async with SessionFactory() as db, db.begin():
        row = await db.get(MarketUpdateJobModel, job.id)
        row.status = "RUNNING"
    await manager.start()
    recovered = await manager.get(job.id)
    assert (
        recovered.status == "INTERRUPTED"
        and recovered.error_code == "WORKER_RESTARTED_RETRY_AVAILABLE"
    )


async def test_shutdown_after_claim_before_execute_does_not_fetch(manager, monkeypatch):
    job = await manager.create(request(), "shutdown-race")
    claimed, proceed = asyncio.Event(), asyncio.Event()
    original = manager._claim

    async def delayed_claim():
        row = await original()
        if row is not None:
            claimed.set()
            await proceed.wait()
        return row

    monkeypatch.setattr(manager, "_claim", delayed_claim)
    await manager.start()
    await asyncio.wait_for(claimed.wait(), 3)
    shutdown = asyncio.create_task(manager.shutdown())
    await asyncio.sleep(0)
    proceed.set()
    await asyncio.wait_for(shutdown, 3)
    assert not manager.test_calls
    assert (await manager.get(job.id)).status == "INTERRUPTED"


async def test_cancel_during_atomic_publication_preserves_received_fact_not_success(
    manager, monkeypatch
):
    job = await manager.create(request(), "cancel-save")
    original = manager.cache.publish

    def publish(*args):
        result = original(*args)
        manager._cancel.set()
        return result

    monkeypatch.setattr(manager.cache, "publish", publish)
    await manager.start()
    assert (await terminal(manager, job.id)).status == "CANCELLED"
    assert (await manager.receipts(job.id, 20, 0))[1] == 1
    values = await manager.observations(SID, request().start_date, request().end_date)
    assert len(values) == 1 and values[0]["execution_eligible"] is False
    assert not manager.cache.pending()


async def test_cache_corruption_stops_missing_date_acquisition(manager):
    job = await manager.create(request(), "first")
    await manager.start()
    await terminal(manager, job.id)
    async with SessionFactory() as db:
        receipt = await db.scalar(select(MarketReceiptModel))
    manifest = manager.cache.verify(receipt.manifest_sha256)
    (manager.cache.root / manifest["rows"]["path"]).write_bytes(b"corrupt fixture")
    next_job = await manager.create(request(), "check-cache")
    assert (await terminal(manager, next_job.id)).error_code == "PRODUCT_CACHE_INTEGRITY_FAILED"
    assert len(manager.test_calls) == 1


async def test_transport_response_duplicate_does_not_publish(manager):
    async def duplicate(parameters, cancelled):
        result = envelope()
        result["rows"] *= 2
        return result, NOW - timedelta(seconds=2), NOW

    manager.transport = duplicate
    job = await manager.create(request(), "duplicate")
    await manager.start()
    assert (await terminal(manager, job.id)).error_code == "INVALID_PROVIDER_RESPONSE"
    assert (await manager.receipts(job.id, 20, 0))[1] == 0


async def test_api_validation_history_cancel_and_missing_archive_scope(manager):
    app = FastAPI()
    app.include_router(routes.router, prefix="/api")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        body = request().model_dump(mode="json")
        assert (await client.post("/api/market-updates", json=body)).status_code == 422
        posted = await client.post(
            "/api/market-updates", json=body, headers={"Idempotency-Key": "api"}
        )
        assert posted.status_code == 202
        job = posted.json()
        assert job["mode"] == "raw_only_candidate" and job["authority"] == AUTHORITY
        assert (await client.get("/api/market-updates?limit=101")).status_code == 422
        assert (await client.get("/api/market-updates?limit=1")).json()["total"] == 1
        assert (await client.post(f"/api/market-updates/{job['job_id']}/cancel")).json()[
            "status"
        ] == "CANCELLED"
        assert (
            await client.get(
                "/api/market-updates/observations",
                params={
                    "security_id": SID,
                    "start_date": "2026-01-01",
                    "end_date": "2028-01-01",
                },
            )
        ).status_code == 422
    with pytest.raises(UpdateError, match="UPDATE_MUST_FOLLOW_FROZEN_COVERAGE"):
        await manager.create(request("2025-12-31"), "archive-no-reacquire")
    with pytest.raises(UpdateError, match="UPDATE_DATE_NOT_YET_PUBLISHABLE"):
        await manager.create(request(end="2026-09-23"), "future")


@pytest.mark.parametrize(
    "code,message",
    [
        ("401", ""),
        ("403", ""),
        ("1", "HTTP403 Forbidden"),
        ("402", "Payment Required"),
        ("1", "Access denied"),
        ("1", "Permission required"),
        ("1", "请填写验证码"),
    ],
)
def test_denial_is_not_transient(code, message):
    with pytest.raises(RuntimeError, match="SOURCE_ACCESS_DENIED"):
        check_result(SimpleNamespace(error_code=code, error_msg=message))


async def test_terminal_database_outage_reconciles_before_next_claim(manager, monkeypatch):
    async def invalid(parameters, cancelled):
        raise UpdateError("INVALID_PROVIDER_RESPONSE")

    original_terminal = manager._terminal
    original_factory = manager.factory
    writes = 0

    @asynccontextmanager
    async def broken_factory():
        raise ConnectionError("fixture transient DB outage")
        yield  # pragma: no cover

    async def flaky_terminal(*args):
        nonlocal writes
        writes += 1
        if writes == 1:
            manager.factory = broken_factory
        try:
            await original_terminal(*args)
        finally:
            manager.factory = original_factory

    manager.transport = invalid
    monkeypatch.setattr(manager, "_terminal", flaky_terminal)
    job = await manager.create(request(), "terminal-recovery")
    await manager.start()
    done = await terminal(manager, job.id)
    assert done.status == "FAILED" and writes == 2
    assert manager._pending_terminal is None
    assert done.summary["active_request"]["start_date"] == "2026-09-18"


async def test_start_failure_releases_advisory_lock_and_second_owner_is_denied(
    manager, monkeypatch
):
    original_factory = manager.factory

    @asynccontextmanager
    async def broken_factory():
        raise ConnectionError("fixture recovery DB failure")
        yield  # pragma: no cover

    manager.factory = broken_factory
    with pytest.raises(ConnectionError):
        await manager.start()
    assert manager._ownership is None
    manager.factory = original_factory
    await manager.start()
    other = MarketUpdateManager(
        SessionFactory,
        engine,
        manager.reader,
        manager.cache.root,
        transport=manager.transport,
        now=lambda: NOW,
    )
    with pytest.raises(UpdateConflict, match="UPDATE_WORKER_ALREADY_OWNED"):
        await other.start()
    await manager.shutdown()
    await other.start()
    await other.shutdown()


async def test_lost_owner_fails_closed_before_publish(manager, monkeypatch):
    original = manager.transport

    async def disconnected(parameters, cancelled):
        value = await original(parameters, cancelled)
        await manager._ownership.invalidate()
        return value

    manager.transport = disconnected
    job = await manager.create(request(), "owner-lost")
    await manager.start()
    done = await terminal(manager, job.id)
    assert done.error_code == "UPDATE_WORKER_OWNERSHIP_LOST"
    assert (await manager.receipts(job.id, 20, 0))[1] == 0
    assert manager._stopping


@pytest.mark.parametrize(
    "mode", ["timeout", "cancel", "oversized", "denied", "success", "malformed"]
)
async def test_supervised_transport_reaps_only_its_offline_child(monkeypatch, mode):
    original_spawn = asyncio.create_subprocess_exec
    processes = []
    scripts = {
        "timeout": "import time; time.sleep(10)",
        "cancel": "import time; time.sleep(10)",
        "oversized": "print('x'*300000)",
        "denied": 'print(\'{"error_code":"SOURCE_ACCESS_DENIED"}\')',
        "success": "import json; from datetime import datetime,timezone; "
        "now=datetime.now(timezone.utc).isoformat(); "
        "print(json.dumps({'requested_at_utc':now,'response_completed_at_utc':now,'rows':[]}))",
        "malformed": "print('[]')",
    }

    async def fixture_spawn(*args, **kwargs):
        assert args[2] == "app.application.market_updates.worker"
        process = await original_spawn(sys.executable, "-c", scripts[mode], **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(transport, "sdk_available", lambda: True)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fixture_spawn)
    cancelled = asyncio.Event()
    loop = asyncio.get_running_loop()
    if mode == "cancel":
        loop.call_later(0.05, cancelled.set)
    if mode == "success":
        payload, requested, received = await transport.fetch({}, cancelled, timeout=2)
        assert payload["rows"] == [] and requested <= received
    else:
        error = UpdateCancelled if mode == "cancel" else UpdateError
        expected = {
            "timeout": "PROVIDER_TIMEOUT",
            "oversized": "PROVIDER_RESPONSE_TOO_LARGE",
            "denied": "SOURCE_ACCESS_DENIED",
            "malformed": "PROVIDER_TRANSPORT_FAILED",
        }
        with pytest.raises(error, match=expected.get(mode)):
            await transport.fetch({}, cancelled, timeout=0.1 if mode == "timeout" else 2)
    assert len(processes) == 1 and processes[0].returncode is not None


def test_raised_http_denial_is_terminal_not_retryable(monkeypatch, capsys):
    class Forbidden(Exception):
        status_code = 403

    def denied():
        raise Forbidden("provider access denied")

    monkeypatch.setattr(worker, "sdk_available", lambda: True)
    monkeypatch.setattr(worker.importlib, "import_module", lambda _: SimpleNamespace(login=denied))
    monkeypatch.setattr(sys, "argv", ["worker", "{}"])
    worker.main()
    assert json.loads(capsys.readouterr().out) == {"error_code": "SOURCE_ACCESS_DENIED"}


async def test_pending_receipt_recovered_after_publish_failure_without_rewriting_first_seen(
    manager,
    monkeypatch,
):
    def interrupted_publication(*args):
        raise OSError("fixture disk publication interruption after durable journal")

    monkeypatch.setattr(manager.cache, "publish", interrupted_publication)
    job = await manager.create(request(), "pending-receipt")
    await manager.start()
    assert (await terminal(manager, job.id)).status == "FAILED"
    await manager.shutdown()
    assert len(manager.cache.pending()) == 1
    reopened = MarketUpdateManager(
        SessionFactory,
        engine,
        manager.reader,
        manager.cache.root,
        transport=manager.transport,
        request_interval=0,
        now=lambda: NOW + timedelta(days=1),
    )
    await reopened.start()
    try:
        receipts, total = await reopened.receipts(job.id, 10, 0)
        assert total == 1 and not manager.cache.pending()
        assert receipts[0]["first_received_at_utc"] == NOW.isoformat()
        assert len(manager.test_calls) == 1
        retry = await reopened.retry(job.id, "recover-then-retry")
        assert (await terminal(reopened, retry.id)).status == "SUCCEEDED"
        assert manager.test_calls[1]["start_date"] == "2026-09-19"
        assert (await reopened.receipts(job.id, 10, 0))[0] == receipts
    finally:
        await reopened.shutdown()


async def test_pending_ack_retry_does_not_duplicate_receipt_or_progress(manager, monkeypatch):
    original = manager.cache.acknowledge
    calls = 0

    def interrupted_ack(journal):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("fixture failed temporary-index cleanup")
        original(journal)

    monkeypatch.setattr(manager.cache, "acknowledge", interrupted_ack)
    job = await manager.create(request(), "ack-crash")
    await manager.start()
    assert (await terminal(manager, job.id)).status == "FAILED"
    async with asyncio.timeout(3):
        while manager.cache.pending():
            await asyncio.sleep(0.01)
    assert (await manager.receipts(job.id, 20, 0))[1] == 1
    assert (await manager.get(job.id)).completed_requests == 1
    assert len(manager.test_calls) == 1


async def test_denial_survives_database_terminal_failure_and_process_restart(manager, monkeypatch):
    async def denied(parameters, cancelled):
        raise UpdateError("SOURCE_ACCESS_DENIED")

    async def failed_terminal(*args):
        manager._stopping = True  # Simulated process exits before a terminal DB write can commit.
        raise ConnectionError("fixture lost terminal write")

    manager.transport = denied
    monkeypatch.setattr(manager, "_terminal", failed_terminal)
    job = await manager.create(request(), "denied-db-crash")
    await manager.start()
    async with asyncio.timeout(3):
        while not manager._stopping:
            await asyncio.sleep(0.01)
    await manager.shutdown()
    assert (await manager.get(job.id)).status == "RUNNING"
    assert manager.cache.denied()
    reopened = MarketUpdateManager(
        SessionFactory,
        engine,
        manager.reader,
        manager.cache.root,
        transport=denied,
        request_interval=0,
        now=lambda: NOW,
    )
    await reopened.start()
    try:
        assert (await reopened.get(job.id)).status == "INTERRUPTED"
        assert (await reopened.capabilities())["reason_code"] == "SOURCE_ACCESS_DENIED"
        with pytest.raises(UpdateConflict, match="SOURCE_ACCESS_DENIED"):
            await reopened.create(request(), "denial-cannot-reset-with-retry")
    finally:
        await reopened.shutdown()


async def test_owner_loss_during_first_timeout_prevents_second_network_attempt(manager):
    calls = 0

    async def disconnected(parameters, cancelled):
        nonlocal calls
        calls += 1
        await manager._ownership.invalidate()
        raise UpdateError("PROVIDER_TIMEOUT")

    manager.transport = disconnected
    job = await manager.create(request(), "no-stale-owner-retry")
    await manager.start()
    assert (await terminal(manager, job.id)).error_code == "UPDATE_WORKER_OWNERSHIP_LOST"
    assert calls == 1


async def test_interrupted_job_cannot_be_overwritten_by_late_success(manager, monkeypatch):
    original = manager.observations
    job = await manager.create(request(), "late-success")

    async def another_owner_interrupted(*args):
        values = await original(*args)
        if values:
            async with SessionFactory() as db, db.begin():
                row = await db.get(MarketUpdateJobModel, job.id)
                row.status = row.phase = "INTERRUPTED"
        return values

    monkeypatch.setattr(manager, "observations", another_owner_interrupted)
    await manager.start()
    assert (await terminal(manager, job.id)).status == "INTERRUPTED"
    await asyncio.sleep(0.03)
    assert (await manager.get(job.id)).status == "INTERRUPTED"


async def test_complete_transport_response_wins_simultaneous_cancel_for_receipt_preservation(
    monkeypatch,
):
    original_spawn, original_wait = asyncio.create_subprocess_exec, asyncio.wait
    cancelled = asyncio.Event()
    script = (
        "import json; from datetime import datetime,timezone; "
        "now=datetime.now(timezone.utc).isoformat(); "
        "print(json.dumps({'requested_at_utc':now,'response_completed_at_utc':now,'rows':[]}))"
    )

    async def fixture_spawn(*args, **kwargs):
        return await original_spawn(sys.executable, "-c", script, **kwargs)

    async def simultaneous(tasks, **kwargs):
        asyncio.get_running_loop().call_later(0.05, cancelled.set)
        return await original_wait(tasks, timeout=2, return_when=asyncio.ALL_COMPLETED)

    monkeypatch.setattr(transport, "sdk_available", lambda: True)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fixture_spawn)
    monkeypatch.setattr(asyncio, "wait", simultaneous)
    payload, _, _ = await transport.fetch({}, cancelled)
    assert cancelled.is_set() and payload["rows"] == []


async def test_partial_cancel_preserves_prior_chunk_and_retry_skips_its_cached_dates(manager):
    original = manager.transport
    second_request = asyncio.Event()
    calls = 0

    async def one_then_wait(parameters, cancelled):
        nonlocal calls
        calls += 1
        if calls == 2:
            second_request.set()
            await cancelled.wait()
            raise UpdateCancelled
        return await original(parameters, cancelled)

    manager.transport = one_then_wait
    job = await manager.create(request("2026-01-01", "2026-02-10"), "partial")
    await manager.start()
    await asyncio.wait_for(second_request.wait(), 3)
    await manager.cancel(job.id)
    assert (await terminal(manager, job.id)).status == "CANCELLED"
    before = (await manager.receipts(job.id, 20, 0))[0]
    assert len(before) == 1
    manager.transport = original
    retry = await manager.retry(job.id, "partial-retry")
    done = await terminal(manager, retry.id)
    assert done.status == "SUCCEEDED" and done.summary["cached_observations_skipped"] == 1
    assert manager.test_calls[1]["start_date"] == "2026-01-02"
    assert (await manager.receipts(job.id, 20, 0))[0] == before


async def test_first_journal_io_failure_preserves_db_fact_and_blocks_queued_restart_retry(
    manager,
    monkeypatch,
):
    def unavailable_cache(payload):
        raise OSError("fixture ENOSPC before first atomic journal")

    monkeypatch.setattr(manager.cache, "journal", unavailable_cache)
    first = await manager.create(request(), "no-durable-journal")
    # The fixture clock is fixed; give the second enqueue a later timestamp so
    # this test exercises journal failure, not the UUID tie-breaker in the queue.
    manager.now = lambda: NOW + timedelta(microseconds=1)
    queued = await manager.create(request(), "same-date-queued")
    manager.now = lambda: NOW
    await manager.start()
    done = await terminal(manager, first.id)
    assert done.error_code == "RECEIPT_PERSISTENCE_BLOCKED"
    assert (
        done.summary["unpublished_receipt"]["evidence"]["first_received_at_utc"] == NOW.isoformat()
    )
    assert done.summary["unpublished_receipt"]["raw"]["rows"]
    await manager.shutdown()
    assert len(manager.test_calls) == 1 and (await manager.get(queued.id)).status == "QUEUED"
    reopened = MarketUpdateManager(
        SessionFactory,
        engine,
        manager.reader,
        manager.cache.root,
        transport=manager.transport,
        request_interval=0,
        now=lambda: NOW,
    )
    await reopened.start()
    try:
        assert (await terminal(reopened, queued.id)).error_code == "RECEIPT_PERSISTENCE_BLOCKED"
        assert len(manager.test_calls) == 1
        assert (await reopened.capabilities())["reason_code"] == "RECEIPT_PERSISTENCE_BLOCKED"
        with pytest.raises(UpdateConflict, match="RECEIPT_PERSISTENCE_BLOCKED"):
            await reopened.retry(first.id, "ordinary-retry-cannot-reacquire")
    finally:
        await reopened.shutdown()
