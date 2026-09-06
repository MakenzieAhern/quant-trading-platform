import asyncio
from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update

from app.api.routes.paper import paper_manager
from app.db.models.paper import PaperTradingSessionModel
from app.db.session import SessionFactory
from app.main import app


@pytest.fixture(autouse=True)
async def clean_paper_tables() -> AsyncIterator[None]:
    await paper_manager.shutdown()
    async with SessionFactory() as session:
        await session.execute(text("TRUNCATE TABLE paper_trading_sessions CASCADE"))
        await session.commit()
    yield
    await paper_manager.shutdown()
    async with SessionFactory() as session:
        await session.execute(text("TRUNCATE TABLE paper_trading_sessions CASCADE"))
        await session.commit()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value


def request_body(initial_cash: str = "100000") -> dict[str, object]:
    return {
        "provider_type": "replay",
        "dataset_id": "AAPL_fixture",
        "symbol": "AAPL",
        "strategy": {
            "type": "moving_average_crossover",
            "parameters": {"short_period": 2, "long_period": 3},
        },
        "initial_cash": initial_cash,
        "default_order_quantity": "10",
        "risk": {"enforce_buying_power": True},
    }


async def test_create_idempotency_validation_and_safe_lookup(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "paper-create-reference"}
    first = await client.post("/api/paper-trading/sessions", json=request_body(), headers=headers)
    repeated = await client.post(
        "/api/paper-trading/sessions", json=request_body(), headers=headers
    )
    assert first.status_code == repeated.status_code == 201
    assert first.json()["session_id"] == repeated.json()["session_id"]
    assert first.json()["initial_cash"] == "100000"

    conflict = await client.post(
        "/api/paper-trading/sessions", json=request_body("100001"), headers=headers
    )
    assert conflict.status_code == 409
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 1
    assert (await client.get(f"/api/paper-trading/sessions/{uuid4()}")).status_code == 404
    assert (await client.get("/api/paper-trading/sessions/not-a-uuid")).status_code == 422

    invalid_provider = {**request_body(), "provider_type": "https://feed.example"}
    invalid_dataset = {**request_body(), "dataset_id": "../../etc/passwd"}
    invalid_strategy = {
        **request_body(),
        "strategy": {"type": "os.system", "parameters": {}},
    }
    for invalid in (invalid_provider, invalid_dataset, invalid_strategy):
        assert (await client.post("/api/paper-trading/sessions", json=invalid)).status_code == 422


async def test_concurrent_idempotent_creation_converges_on_one_session(
    client: AsyncClient,
) -> None:
    headers = {"Idempotency-Key": "paper-concurrent-create"}
    first, second = await asyncio.gather(
        client.post("/api/paper-trading/sessions", json=request_body(), headers=headers),
        client.post("/api/paper-trading/sessions", json=request_body(), headers=headers),
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["session_id"] == second.json()["session_id"]
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 1


async def test_reference_session_runs_to_persisted_exact_snapshot(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    created = await client.post(
        "/api/paper-trading/sessions",
        json=request_body("100000.052500000000000001"),
    )
    session_id = created.json()["session_id"]
    started = await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    assert started.status_code == 200
    assert started.json()["status"] in {"STARTING", "RUNNING"}

    detail: dict[str, object] = {}
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "STOPPED":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "STOPPED"
    snapshot = (await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")).json()
    assert snapshot["session"]["initial_cash"] == "100000.052500000000000001"
    assert snapshot["latest_portfolio"]["equity"] == "100012.252500000000000001"
    assert snapshot["latest_portfolio"]["cash"] == "98160.852500000000000001"
    assert len(snapshot["signals"]) == 1
    assert len(snapshot["risk_decisions"]) == 1
    assert len(snapshot["orders"]) == 1
    assert snapshot["orders"][0]["status"] == "FILLED"
    assert snapshot["fills"][0]["price"] == "183.92"
    assert snapshot["fills"][0]["commission"] == "0"
    assert snapshot["fills"][0]["timestamp"] == "2024-01-09T00:00:00Z"
    assert snapshot["last_sequence"] > 0

    events = await client.get(f"/api/paper-trading/sessions/{session_id}/events")
    assert events.status_code == 200
    sequences = [item["sequence"] for item in events.json()]
    assert sequences == list(range(1, len(sequences) + 1))
    assert all("payload" in item for item in events.json())

    repeat_start = await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    assert repeat_start.status_code == 409
    stopped = await client.post(f"/api/paper-trading/sessions/{session_id}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "STOPPED"


async def test_stop_is_retry_safe_and_sessions_are_isolated(client: AsyncClient) -> None:
    first, second = await asyncio.gather(
        client.post("/api/paper-trading/sessions", json=request_body()),
        client.post("/api/paper-trading/sessions", json=request_body()),
    )
    assert first.json()["session_id"] != second.json()["session_id"]
    first_id = first.json()["session_id"]
    second_id = second.json()["session_id"]
    stopped = await client.post(f"/api/paper-trading/sessions/{first_id}/stop")
    stopped_again = await client.post(f"/api/paper-trading/sessions/{first_id}/stop")
    assert stopped.json()["status"] == stopped_again.json()["status"] == "STOPPED"
    assert (await client.get(f"/api/paper-trading/sessions/{second_id}")).json()[
        "status"
    ] == "CREATED"


async def test_restart_contract_marks_orphaned_runtime_interrupted(client: AsyncClient) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])
    async with SessionFactory() as session:
        await session.execute(
            update(PaperTradingSessionModel)
            .where(PaperTradingSessionModel.id == session_id)
            .values(status="RUNNING")
        )
        await session.commit()
    assert await paper_manager.recover_interrupted() == 1
    detail = await client.get(f"/api/paper-trading/sessions/{session_id}")
    assert detail.json()["status"] == "INTERRUPTED"
    assert detail.json()["error_message"] == "Paper runtime interrupted by backend restart."


async def test_shutdown_marks_an_active_runtime_interrupted(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 10)
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = created.json()["session_id"]
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        detail = await client.get(f"/api/paper-trading/sessions/{session_id}")
        if detail.json()["status"] == "RUNNING":
            break
        await asyncio.sleep(0.01)
    assert detail.json()["status"] == "RUNNING"
    await paper_manager.shutdown()
    interrupted = await client.get(f"/api/paper-trading/sessions/{session_id}")
    assert interrupted.json()["status"] == "INTERRUPTED"
    assert "backend shutdown" in interrupted.json()["error_message"]


async def test_runtime_failure_is_persisted_without_exposing_internal_details(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_to_build_runtime(_session: object) -> object:
        raise RuntimeError("sensitive provider diagnostics")

    monkeypatch.setattr(paper_manager, "_build_runtime", fail_to_build_runtime)
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = created.json()["session_id"]
    assert (await client.post(f"/api/paper-trading/sessions/{session_id}/start")).status_code == 200

    detail: dict[str, object] = {}
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "FAILED":
            break
        await asyncio.sleep(0.01)

    assert detail["status"] == "FAILED"
    assert detail["error_message"] == "RuntimeError: paper session failed"
    assert "sensitive" not in str(detail)
