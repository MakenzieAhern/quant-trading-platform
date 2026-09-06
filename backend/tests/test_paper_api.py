import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update
from sqlalchemy.exc import DBAPIError

from app.api.routes.paper import paper_manager, paper_session_websocket, settings
from app.db.models.paper import PaperTradingSessionModel
from app.db.repositories.paper import SQLAlchemyPaperRepository
from app.db.session import SessionFactory
from app.execution import OrderManager
from app.main import app
from app.paper.runtime import PaperBroker, ReplayMarketDataProvider
from app.portfolio import PortfolioEngine
from app.risk import RiskEngine
from app.strategies import MovingAverageCrossoverStrategy


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
    event_types = [item["type"] for item in events.json()]
    fill_index = event_types.index("fill.created")
    assert event_types[fill_index - 2 : fill_index + 2] == [
        "market.bar",
        "order.updated",
        "fill.created",
        "portfolio.snapshot",
    ]

    repeat_start = await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    assert repeat_start.status_code == 409
    stopped = await client.post(f"/api/paper-trading/sessions/{session_id}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "STOPPED"


async def test_repeated_sessions_release_runtime_resources(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    session_ids: list[str] = []

    for _ in range(10):
        created = await client.post("/api/paper-trading/sessions", json=request_body())
        session_id = created.json()["session_id"]
        session_ids.append(session_id)
        assert (
            await client.post(f"/api/paper-trading/sessions/{session_id}/start")
        ).status_code == 200

    for session_id in session_ids:
        for _ in range(100):
            detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
            if detail["status"] == "STOPPED":
                break
            await asyncio.sleep(0.01)
        assert detail["status"] == "STOPPED"

    await asyncio.sleep(0)
    assert paper_manager._tasks == {}
    assert paper_manager._providers == {}
    assert all(paper_manager.hub.subscriber_count(UUID(value)) == 0 for value in session_ids)


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
        await SQLAlchemyPaperRepository(session).append_events(
            session_id,
            (
                (
                    "order.updated",
                    datetime.now(UTC),
                    {
                        "order_id": str(uuid4()),
                        "strategy_id": "restart-audit",
                        "symbol": "AAPL",
                        "side": "BUY",
                        "order_type": "MARKET",
                        "quantity": "10",
                        "price": None,
                        "status": "ACCEPTED",
                        "created_at": "2024-01-08T00:00:00+00:00",
                    },
                ),
            ),
        )
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
    events = await client.get(f"/api/paper-trading/sessions/{session_id}/events")
    assert events.json()[-1]["payload"] == {"status": "INTERRUPTED"}
    assert events.json()[-2]["payload"]["status"] == "CANCELLED"
    snapshot = await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")
    assert snapshot.json()["orders"][0]["status"] == "CANCELLED"


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


async def test_concurrent_start_stop_commands_create_one_runtime_and_terminal_sequence(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 10)
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = created.json()["session_id"]
    starts = await asyncio.gather(
        client.post(f"/api/paper-trading/sessions/{session_id}/start"),
        client.post(f"/api/paper-trading/sessions/{session_id}/start"),
    )
    assert all(response.status_code == 200 for response in starts)
    assert len(paper_manager._tasks) == 1

    stops = await asyncio.gather(
        client.post(f"/api/paper-trading/sessions/{session_id}/stop"),
        client.post(f"/api/paper-trading/sessions/{session_id}/stop"),
    )
    assert all(response.status_code == 200 for response in stops)
    detail: dict[str, object] = {}
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "STOPPED":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "STOPPED"
    events = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
    statuses = [item["payload"]["status"] for item in events if item["type"] == "session.status"]
    assert statuses == ["CREATED", "STARTING", "RUNNING", "STOPPING", "STOPPED"]


async def test_start_stop_race_terminates_without_duplicate_runtime(client: AsyncClient) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = created.json()["session_id"]
    await asyncio.gather(
        client.post(f"/api/paper-trading/sessions/{session_id}/start"),
        client.post(f"/api/paper-trading/sessions/{session_id}/stop"),
    )
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "STOPPED":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "STOPPED"
    assert sum(1 for task in paper_manager._tasks if str(task) == session_id) <= 1


async def test_event_batches_and_lifecycle_transition_roll_back_atomically(
    client: AsyncClient,
) -> None:
    first = await client.post("/api/paper-trading/sessions", json=request_body())
    first_id = UUID(first.json()["session_id"])
    async with SessionFactory() as db:
        with pytest.raises(DBAPIError):
            await SQLAlchemyPaperRepository(db).append_events(
                first_id,
                (
                    ("market.bar", datetime.now(UTC), {}),
                    ("x" * 65, datetime.now(UTC), {}),
                ),
            )
    assert len(await paper_manager.events(first_id)) == 1

    second = await client.post("/api/paper-trading/sessions", json=request_body())
    second_id = UUID(second.json()["session_id"])
    session = await paper_manager.get(second_id)
    assert session is not None
    async with SessionFactory() as db:
        with pytest.raises(DBAPIError):
            await SQLAlchemyPaperRepository(db).transition_with_event(
                second_id,
                session.status,
                type(session.status).STARTING,
                datetime.now(UTC),
                "x" * 65,
            )
    unchanged = await paper_manager.get(second_id)
    assert unchanged is not None and unchanged.status.value == "CREATED"
    assert len(await paper_manager.events(second_id)) == 1


@pytest.mark.parametrize(
    ("layer", "target", "attribute"),
    [
        ("provider", ReplayMarketDataProvider, "start"),
        ("strategy", MovingAverageCrossoverStrategy, "_process_bar"),
        ("risk", RiskEngine, "evaluate"),
        ("oms", OrderManager, "process_proposal"),
        ("broker", PaperBroker, "submit"),
        ("portfolio", PortfolioEngine, "mark_to_market"),
        ("persistence", SQLAlchemyPaperRepository, "append_events"),
    ],
)
async def test_layer_failures_are_terminal_and_safely_reported(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    layer: str,
    target: type[object],
    attribute: str,
) -> None:
    async def fail_async(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"sensitive {layer} details")

    def fail_sync(*_args: object, **_kwargs: object) -> object:
        raise RuntimeError(f"sensitive {layer} details")

    monkeypatch.setattr(
        target,
        attribute,
        fail_async if layer in {"provider", "persistence"} else fail_sync,
    )
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = created.json()["session_id"]
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "FAILED":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "FAILED"
    assert detail["error_message"] == "RuntimeError: paper session failed"
    assert "sensitive" not in str(detail)


class FakeWebSocket:
    def __init__(self, *, fail_after_connect: bool = False) -> None:
        self.headers = {"origin": settings.frontend_origin}
        self.accepted = False
        self.sent: list[dict[str, object]] = []
        self.closed: tuple[int, str] | None = None
        self.disconnected = asyncio.Event()
        self.fail_after_connect = fail_after_connect

    async def accept(self) -> None:
        self.accepted = True

    async def close(self, code: int, reason: str) -> None:
        self.closed = (code, reason)

    async def send_json(self, value: dict[str, object]) -> None:
        if self.fail_after_connect and self.sent:
            raise RuntimeError("serialization transport failed")
        self.sent.append(value)

    async def receive(self) -> dict[str, object]:
        await self.disconnected.wait()
        return {"type": "websocket.disconnect"}


async def test_websocket_disconnect_and_delivery_failure_release_subscriptions(
    client: AsyncClient,
) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])

    websocket = FakeWebSocket()
    task = asyncio.create_task(paper_session_websocket(websocket, session_id))  # type: ignore[arg-type]
    for _ in range(100):
        if paper_manager.hub.subscriber_count(session_id) == 1:
            break
        await asyncio.sleep(0.001)
    websocket.disconnected.set()
    await task
    assert websocket.accepted
    assert websocket.sent[0]["type"] == "stream.connected"
    assert paper_manager.hub.subscriber_count(session_id) == 0

    failing = FakeWebSocket(fail_after_connect=True)
    task = asyncio.create_task(paper_session_websocket(failing, session_id))  # type: ignore[arg-type]
    for _ in range(100):
        if paper_manager.hub.subscriber_count(session_id) == 1:
            break
        await asyncio.sleep(0.001)
    paper_manager.hub.publish(
        session_id,
        {
            "sequence": 2,
            "type": "market.bar",
            "occurred_at": datetime.now(UTC).isoformat(),
            "payload": {},
        },
    )
    with pytest.raises(RuntimeError, match="serialization transport failed"):
        await task
    assert paper_manager.hub.subscriber_count(session_id) == 0
    assert (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()[
        "status"
    ] == "CREATED"

    terminal = FakeWebSocket()
    task = asyncio.create_task(paper_session_websocket(terminal, session_id))  # type: ignore[arg-type]
    for _ in range(100):
        if paper_manager.hub.subscriber_count(session_id) == 1:
            break
        await asyncio.sleep(0.001)
    paper_manager.hub.publish(
        session_id,
        {
            "sequence": 2,
            "type": "session.status",
            "occurred_at": datetime.now(UTC).isoformat(),
            "payload": {"status": "STOPPED"},
        },
    )
    await task
    assert terminal.closed == (1000, "paper session is terminal")
    assert paper_manager.hub.subscriber_count(session_id) == 0


async def test_unexpected_api_failure_returns_opaque_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_safely(_session_id: UUID) -> object:
        raise RuntimeError("sensitive database URL and SQL")

    monkeypatch.setattr(paper_manager, "get", fail_safely)
    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False),
        base_url="http://test",
    ) as safe_client:
        response = await safe_client.get(f"/api/paper-trading/sessions/{uuid4()}")
    assert response.status_code == 500
    assert response.text == "Internal Server Error"
    assert "sensitive" not in response.text


async def test_session_lifecycle_rejects_a_naive_clock(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_clock", lambda: datetime(2026, 9, 6))
    response = await client.post("/api/paper-trading/sessions", json=request_body())
    assert response.status_code == 422
    assert response.json()["detail"] == "paper session clock must be timezone-aware"
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 0
