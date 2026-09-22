import asyncio
from threading import Event
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app.api.routes import experiments
from app.application.experiments import service
from app.application.experiments.data import DEMO_ID, ExperimentDatasetRegistry
from app.application.experiments.models import CreateExperimentRequest
from app.application.experiments.runner import ExperimentOutput
from app.application.experiments.service import ExperimentManager
from app.core.config import get_settings
from app.db.models.experiments import ExperimentJobModel, ExperimentResultRowModel
from app.db.session import SessionFactory, engine
from app.main import app


@pytest.fixture
async def manager(tmp_path, monkeypatch):
    assert get_settings().app_env == "test", (
        "product integration tests require disposable APP_ENV=test DB"
    )
    assert "quant_test" in get_settings().database_url, "never run against application history"
    async with SessionFactory() as db:
        await db.execute(text("TRUNCATE product_research_rows, product_research_jobs"))
        await db.commit()
    instance = ExperimentManager(SessionFactory, ExperimentDatasetRegistry(tmp_path), engine)
    monkeypatch.setattr(experiments, "experiment_manager", instance)
    yield instance
    await instance.shutdown()


def payload(**changes):
    return {
        "name": "Durable demo",
        "dataset_id": DEMO_ID,
        "start_date": "2030-12-20",
        "end_date": "2031-04-22",
        **changes,
    }


async def terminal(manager, identifier):
    async with asyncio.timeout(30):
        while True:
            row = await manager.get(identifier)
            if row.status in {"SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"}:
                return row
            await asyncio.sleep(0.02)


async def test_concurrent_idempotency_cancel_retry_and_validation(manager):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        headers = {"Idempotency-Key": str(uuid4())}
        left, right = await asyncio.gather(
            *[client.post("/api/experiments", headers=headers, json=payload()) for _ in range(2)]
        )
        assert left.status_code == right.status_code == 202
        job_id = left.json()["job_id"]
        assert job_id == right.json()["job_id"]
        conflict = await client.post(
            "/api/experiments", headers=headers, json=payload(initial_cash="1")
        )
        assert conflict.status_code == 409
        assert conflict.json()["code"] == "IDEMPOTENCY_KEY_CONFLICT"
        cancelled = await client.post(f"/api/experiments/{job_id}/cancel")
        assert cancelled.json()["status"] == "CANCELLED"
        same = await client.post(f"/api/experiments/{job_id}/cancel")
        assert same.json() == cancelled.json()
        retried = await client.post(
            f"/api/experiments/{job_id}/retry", headers={"Idempotency-Key": "retry-one"}
        )
        assert retried.status_code == 202
        assert retried.json()["retry_of"] == job_id and retried.json()["attempt"] == 2
        assert retried.json()["job_id"] != job_id
        unsupported = await client.post(
            "/api/experiments", headers={"Idempotency-Key": "szse"}, json=payload(universe="SZSE")
        )
        assert unsupported.status_code == 422
        assert unsupported.json()["code"] == "UNIVERSE_NOT_AVAILABLE"
        missing_key = await client.post("/api/experiments", json=payload())
        assert missing_key.status_code == 422
        wrong_money = await client.post(
            "/api/experiments",
            headers={"Idempotency-Key": "money"},
            json=payload(initial_cash=100000),
        )
        assert wrong_money.status_code == 422


async def test_worker_results_are_persisted_paginated_and_reopenable(manager):
    job = await manager.create(CreateExperimentRequest.model_validate(payload()), "durable")
    await manager.start()
    row = await terminal(manager, job.id)
    assert row.status == "SUCCEEDED", row.error_code
    assert row.completed_sessions == row.total_sessions == 340
    await manager.shutdown()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        detail = await client.get(f"/api/experiments/{job.id}")
        result = await client.get(f"/api/experiments/{job.id}/result")
        series = await client.get(f"/api/experiments/{job.id}/equity?limit=3&offset=2")
        assert detail.json()["result_available"] is True
        assert result.json()["metrics"]["number_of_fills"] > 0
        assert len(series.json()["items"]) == 3
        assert series.json()["items"][0]["sequence"] == 2
        assert series.json()["total"] > 3
        too_large = await client.get(f"/api/experiments/{job.id}/equity?limit=201")
        assert too_large.status_code == 422
        after_save = await client.post(f"/api/experiments/{job.id}/cancel")
        assert after_save.json()["status"] == "SUCCEEDED"
        assert after_save.json()["cancel_requested"] is False


async def test_startup_recovers_orphans_without_false_success_or_results(manager):
    job = await manager.create(CreateExperimentRequest.model_validate(payload()), "orphan")
    async with SessionFactory() as db, db.begin():
        row = await db.get(ExperimentJobModel, job.id)
        row.status = "RUNNING"
        row.phase = "EXECUTING"
        row.completed_sessions = 17
    await manager.start()
    recovered = await manager.get(job.id)
    assert recovered.status == "INTERRUPTED"
    assert recovered.error_code == "WORKER_RESTARTED_RETRY_AVAILABLE"
    assert recovered.completed_sessions == 17
    assert recovered.summary is None
    async with SessionFactory() as db:
        assert (
            await db.scalar(
                select(ExperimentResultRowModel).where(ExperimentResultRowModel.job_id == job.id)
            )
            is None
        )


async def test_single_worker_ownership_prevents_second_process_recovery(manager, tmp_path):
    await manager.start()
    other = ExperimentManager(SessionFactory, ExperimentDatasetRegistry(tmp_path), engine)
    with pytest.raises(RuntimeError, match="another process owns"):
        await other.start()


async def test_shutdown_while_claim_returns_never_dispatches_calculation(manager, monkeypatch):
    job = await manager.create(CreateExperimentRequest.model_validate(payload()), "shutdown-race")
    pending = await manager.create(CreateExperimentRequest.model_validate(payload()), "queued-next")
    claimed, release = asyncio.Event(), asyncio.Event()
    original_claim = manager._claim
    calculations = []

    async def paused_claim():
        result = await original_claim()
        claimed.set()
        await release.wait()
        return result

    def unexpected_calculation(*args):
        calculations.append(args)
        raise AssertionError("shutdown must not dispatch calculation")

    monkeypatch.setattr(manager, "_claim", paused_claim)
    monkeypatch.setattr(service, "run_experiment", unexpected_calculation)
    await manager.start()
    await asyncio.wait_for(claimed.wait(), 2)
    shutdown = asyncio.create_task(manager.shutdown())
    await asyncio.sleep(0)
    assert manager._stopping is True
    release.set()
    await asyncio.wait_for(shutdown, 2)
    assert calculations == []
    stopped = await manager.get(job.id)
    assert stopped.status == "INTERRUPTED"
    assert stopped.error_code == "WORKER_STOPPED_RETRY_AVAILABLE"
    assert stopped.summary is None
    assert (await manager.get(pending.id)).status == "QUEUED"


async def test_cancel_committed_before_save_leaves_no_partial_results(manager, monkeypatch):
    job = await manager.create(CreateExperimentRequest.model_validate(payload()), "cancel-save")
    ready, release = asyncio.Event(), Event()
    loop = asyncio.get_running_loop()

    def completed_calculation(*args):
        loop.call_soon_threadsafe(ready.set)
        assert release.wait(2), "test did not release completed calculation"
        return ExperimentOutput(summary={"test": "complete"}, rows={"equity": [{"sequence": 0}]})

    monkeypatch.setattr(service, "run_experiment", completed_calculation)
    await manager.start()
    await asyncio.wait_for(ready.wait(), 2)
    try:
        cancelled = await manager.cancel(job.id)
        assert cancelled.cancel_requested
    finally:
        release.set()
    stopped = await terminal(manager, job.id)
    assert stopped.status == "CANCELLED"
    assert stopped.summary is None
    assert await manager.collection(job.id, "equity", 20, 0) == ([], 0)


async def test_failed_terminal_write_is_reconciled_before_claiming_more_work(manager, monkeypatch):
    job = await manager.create(CreateExperimentRequest.model_validate(payload()), "terminal-outage")
    failed_write = asyncio.Event()
    original_finish = manager._finish_failure
    writes = 0
    claims = 0
    original_claim = manager._claim

    async def tracked_claim():
        nonlocal claims
        claims += 1
        if claims > 1:
            assert (await manager.get(job.id)).status == "FAILED"
        return await original_claim()

    async def transient_finish(*args):
        nonlocal writes
        writes += 1
        if writes == 1:
            failed_write.set()
            raise ConnectionError("test-only terminal write outage")
        await original_finish(*args)

    def failed_calculation(*args):
        raise RuntimeError("test-only calculation failure")

    monkeypatch.setattr(manager, "_claim", tracked_claim)
    monkeypatch.setattr(manager, "_finish_failure", transient_finish)
    monkeypatch.setattr(service, "run_experiment", failed_calculation)
    await manager.start()
    await asyncio.wait_for(failed_write.wait(), 2)
    manager._wake.set()
    row = await asyncio.wait_for(terminal(manager, job.id), 4)
    assert row.status == "FAILED"
    assert writes == 2
    assert row.error_code == "EXPERIMENT_EXECUTION_FAILED"
    await manager.shutdown()
    retried = await manager.retry(job.id, "after-outage")
    assert retried.status == "QUEUED" and retried.retry_of == job.id


async def test_startup_failure_releases_session_lock_before_returning_connection_to_pool(
    manager, monkeypatch, tmp_path
):
    def failed_session():
        raise ConnectionError("test-only orphan recovery failure")

    monkeypatch.setattr(manager, "factory", failed_session)
    with pytest.raises(ConnectionError, match="orphan recovery"):
        await manager.start()
    assert manager._ownership is None
    assert manager._worker is None
    # Explicitly inspect the session lock: a pooled close must not hide a leaked lock.
    async with engine.connect() as connection:
        count = await connection.scalar(
            text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory' AND objid = :key"),
            {"key": service.OWNER_LOCK},
        )
        assert count == 0
    other = ExperimentManager(SessionFactory, ExperimentDatasetRegistry(tmp_path), engine)
    try:
        await other.start()
    finally:
        await other.shutdown()


async def test_lost_owner_connection_stops_old_worker_and_cannot_overwrite_recovery(
    manager, monkeypatch, tmp_path
):
    job = await manager.create(CreateExperimentRequest.model_validate(payload()), "lost-owner")
    ready, release = asyncio.Event(), Event()
    loop = asyncio.get_running_loop()

    def paused_calculation(registry, request, checksum, cancelled, progress):
        progress("EXECUTING", 1, 10)
        loop.call_soon_threadsafe(ready.set)
        assert release.wait(2)
        progress("EXECUTING", 2, 10)
        raise AssertionError("lost ownership must stop further execution")

    monkeypatch.setattr(service, "run_experiment", paused_calculation)
    await manager.start()
    await asyncio.wait_for(ready.wait(), 2)
    await manager._ownership.invalidate()
    other = ExperimentManager(SessionFactory, ExperimentDatasetRegistry(tmp_path), engine)
    try:
        await other.start()
        release.set()
        await asyncio.wait_for(manager._worker, 2)
        assert manager._ownership_failed
        row = await manager.get(job.id)
        assert row.status == "INTERRUPTED"
        assert row.error_code == "WORKER_RESTARTED_RETRY_AVAILABLE"
        assert row.summary is None
        assert await manager.collection(job.id, "equity", 10, 0) == ([], 0)
        with pytest.raises(service.ExperimentConflictError, match="WORKER_UNAVAILABLE"):
            await manager.create(CreateExperimentRequest.model_validate(payload()), "stale-owner")
    finally:
        release.set()
        await other.shutdown()


async def test_paper_cleanup_runs_even_when_experiment_shutdown_fails(monkeypatch):
    from unittest.mock import AsyncMock

    from app.main import experiment_manager, lifespan, paper_manager

    monkeypatch.setattr(experiment_manager, "start", AsyncMock())
    monkeypatch.setattr(
        experiment_manager, "shutdown", AsyncMock(side_effect=ConnectionError("shutdown"))
    )
    monkeypatch.setattr(paper_manager, "recover_interrupted", AsyncMock(return_value=0))
    paper_shutdown = AsyncMock()
    monkeypatch.setattr(paper_manager, "shutdown", paper_shutdown)
    with pytest.raises(ConnectionError, match="shutdown"):
        async with lifespan(app):
            pass
    paper_shutdown.assert_awaited_once()
