"""Abrupt process death at SQL batch boundaries; synthetic inputs, never live data."""

import asyncio
import json
import os
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest
from conftest import require_disposable_database
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select

from app.api.routes.paper import paper_manager
from app.core.config import get_settings
from app.db.models.paper import PaperTradingEventModel, PaperTradingSessionModel
from app.db.repositories.paper import SQLAlchemyPaperRepository
from app.db.session import SessionFactory, engine
from app.execution import FixedCommission
from app.main import app
from app.paper.runtime import ASharePaperTradingRuntime, SimulatedAShareSessionProvider
from tests.test_paper_api import a_share_request_body
from tests.test_paper_investor_scope import DailyStarTarget
from tests.test_research_execution_engine import CALENDAR, _star_session


async def capture(client, sid):
    response = await client.get(f"/api/paper-trading/sessions/{sid}/snapshot")
    assert response.status_code == 200
    return {
        "pid": os.getpid(),
        "snapshot": response.json(),
        "events": [paper_manager._wire_event(e) for e in await paper_manager.events(sid)],
    }


def crash(receipt):
    print(json.dumps(receipt, default=str), flush=True)
    # No asyncio cancellation, manager shutdown or SQL cleanup may run.
    os._exit(73)


async def witness(mode, identifier=None):
    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
    if sys.flags.optimize:
        raise RuntimeError("recovery witness requires assertions enabled")
    if mode not in {"after_flush", "after_commit", "recover"}:
        raise ValueError("unknown witness mode")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        if mode == "recover":
            sid = UUID(identifier)
            try:
                async with SessionFactory() as db:
                    active = tuple(
                        (
                            await db.scalars(
                                select(PaperTradingSessionModel.id).where(
                                    PaperTradingSessionModel.status.in_(
                                        ["STARTING", "RUNNING", "PAUSING", "STOPPING"]
                                    )
                                )
                            )
                        ).all()
                    )
                assert active == (sid,), "refuse recovery alongside another active test owner"
                before = await capture(client, sid)
                assert await paper_manager.recover_interrupted() == 1
                after = await capture(client, sid)
                assert await paper_manager.recover_interrupted() == 0
                assert await capture(client, sid) == after
                response = await client.post(f"/api/paper-trading/sessions/{sid}/start")
                assert response.status_code == 409
                assert await capture(client, sid) == after
                return {"before": before, "after": after}
            finally:
                async with SessionFactory() as db:
                    await db.execute(
                        delete(PaperTradingEventModel).where(
                            PaperTradingEventModel.session_id == sid
                        )
                    )
                    await db.execute(
                        delete(PaperTradingSessionModel).where(PaperTradingSessionModel.id == sid)
                    )
                    await db.commit()
                await engine.dispose()

        response = await client.post(
            "/api/paper-trading/sessions",
            json={**a_share_request_body(), "initial_cash": "10000000"},
        )
        assert response.status_code == 201
        sid = UUID(response.json()["session_id"])
        baseline = None
        original_append = SQLAlchemyPaperRepository._append_events_locked

        async def append(repository, session_id, events):
            stored = await original_append(repository, session_id, events)
            if mode == "after_flush" and any(
                kind == "market.session" and payload["trading_date"] == "2024-01-03"
                for kind, _, payload in events
            ):
                await repository._session.flush()
                assert baseline is not None
                assert sum(event.event_type == "fill.created" for event in stored) == 1
                assert any(event.event_type == "portfolio.snapshot" for event in stored)
                crash(baseline)
            return stored

        SQLAlchemyPaperRepository._append_events_locked = append

        def build(session, cursor_date, initial_calendar=None):
            runtime = ASharePaperTradingRuntime(
                initial_cash=session.initial_cash,
                commission_model=FixedCommission(),
                calendar=initial_calendar or CALENDAR,
                strategy=DailyStarTarget(100000),
            )
            provider = SimulatedAShareSessionProvider(
                tuple(_star_session(date(2024, 1, day), is_st=day >= 3) for day in (2, 3, 4)), 0
            )
            original_start = provider.start

            async def start(handler):
                async def consume(item):
                    nonlocal baseline
                    await handler(item)
                    baseline = await capture(client, sid)
                    if mode == "after_commit" and item.trading_date == date(2024, 1, 3):
                        crash(baseline)

                await original_start(consume)

            provider.start = start
            return provider, runtime

        paper_manager._build_runtime = build
        await paper_manager.start(sid)
        await asyncio.wait_for(paper_manager._tasks[sid], 15)
        raise AssertionError("runtime did not reach the intended crash boundary")


@pytest.mark.parametrize("boundary", ["after_flush", "after_commit"])
def test_abrupt_paper_process_death_preserves_committed_journal(boundary, tmp_path):
    settings = get_settings()
    require_disposable_database(settings.app_env, settings.database_url)
    environment = {
        **os.environ,
        "APP_ENV": "test",
        "DATABASE_URL": settings.database_url,
        "PRODUCT_DATA_PATH": str(tmp_path / "product"),
        "RESEARCH_DATA_PATH": str(tmp_path / "no-research"),
    }

    def run(mode, *args):
        return subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), mode, *args],
            env=environment,
            capture_output=True,
            text=True,
            timeout=30,
        )

    writer = run(boundary)
    assert writer.returncode == 73, writer.stderr
    committed = json.loads(writer.stdout)
    sid = committed["snapshot"]["session"]["session_id"]
    reader = run("recover", sid)
    assert reader.returncode == 0, reader.stderr
    recovered = json.loads(reader.stdout)
    before, after = recovered["before"], recovered["after"]
    assert committed.pop("pid") != before["pid"] != os.getpid()
    before.pop("pid")
    after.pop("pid")
    assert before == committed  # Includes rollback of the flushed, uncommitted batch.
    old, new = before["snapshot"], after["snapshot"]
    assert old["session"]["status"] == "RUNNING"
    assert old["latest_session"]["trading_date"] == (
        "2024-01-03" if boundary == "after_commit" else "2024-01-02"
    )
    assert Decimal(old["latest_portfolio"]["cash"]) == (
        9000000 if boundary == "after_commit" else 10000000
    )
    assert new["session"]["status"] == "INTERRUPTED"
    assert new["session"]["error_message"] == "Paper runtime interrupted by backend restart."
    assert new["fills"] == old["fills"]
    assert new["latest_portfolio"] == old["latest_portfolio"]
    assert new["latest_session"] == old["latest_session"]
    assert len(new["fills"]) == (1 if boundary == "after_commit" else 0)
    assert old["orders"][-1]["status"] == "ACCEPTED"
    assert new["orders"] == [
        {**order, "status": "CANCELLED"} if order["status"] == "ACCEPTED" else order
        for order in old["orders"]
    ]
    prefix = before["events"]
    assert after["events"][: len(prefix)] == prefix
    assert [e["type"] for e in after["events"][len(prefix) :]] == [
        "order.updated",
        "session.status",
    ]
    assert [e["sequence"] for e in after["events"]] == list(range(1, len(prefix) + 3))


@pytest.mark.parametrize("optimized", [False, True])
def test_crash_witness_refuses_non_test_environment(optimized):
    result = subprocess.run(
        [
            sys.executable,
            *(["-O"] if optimized else []),
            str(Path(__file__).resolve()),
            "after_flush",
        ],
        env={**os.environ, "APP_ENV": "development"},
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode not in {0, 73}
    assert "require APP_ENV=test and a quant_test database" in result.stderr


if __name__ == "__main__":
    print(json.dumps(asyncio.run(witness(*sys.argv[1:])), default=str))
