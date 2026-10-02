import asyncio
from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text, update
from sqlalchemy.exc import DBAPIError

from app.api.routes import paper as paper_routes
from app.api.routes.paper import paper_manager, paper_session_websocket, settings
from app.application.backtests.registry import UnknownDatasetError
from app.application.experiments.data import HISTORICAL_ID, ExperimentInputError
from app.application.paper_trading.service import PaperTradingManager
from app.db.models.paper import PaperTradingSessionModel
from app.db.repositories.paper import SQLAlchemyPaperRepository
from app.db.session import SessionFactory
from app.execution import FixedCommission, OrderManager
from app.main import app
from app.paper.models import PaperSession, PaperSessionConcurrencyError
from app.paper.runtime import (
    ASharePaperTradingRuntime,
    PaperBroker,
    ReplayMarketDataProvider,
    SimulatedAShareSessionProvider,
)
from app.portfolio import PortfolioEngine
from app.risk import RiskEngine
from app.strategies import MovingAverageCrossoverStrategy
from tests.test_paper_calendar_journal import INITIAL
from tests.test_paper_plan_checkpoint import FixtureStrategy
from tests.test_research_execution_engine import CALENDAR, _session


async def test_calendar_journal_survives_new_manager_and_rest_hydration(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Real disposable PostgreSQL/API; synthetic inputs, not forward authority."""
    first_manager = PaperTradingManager(
        SessionFactory, paper_manager._datasets, paper_manager._strategies
    )
    items = (
        INITIAL,
        _session(date(2024, 1, 2), opening="10"),
        CALENDAR,
        _session(date(2024, 1, 3), opening="9.9"),
    )

    def install(manager, *, pause=False):
        def build(session, cursor_date, initial_calendar=None):
            runtime = ASharePaperTradingRuntime(
                initial_cash=session.initial_cash,
                commission_model=FixedCommission(),
                calendar=initial_calendar or (CALENDAR if cursor_date else INITIAL),
                strategy=FixtureStrategy(),
            )
            provider = SimulatedAShareSessionProvider(items, 0)
            original_start = provider.start

            async def start(handler):
                async def consume(item):
                    await handler(item)
                    if pause and item is CALENDAR:
                        await manager.pause(session.id)

                await original_start(consume)

            provider.start = start
            return provider, runtime

        manager._build_runtime = build
        monkeypatch.setattr(paper_routes, "paper_manager", manager)

    install(first_manager, pause=True)
    created = (await client.post("/api/paper-trading/sessions", json=a_share_request_body())).json()
    session_id = UUID(created["session_id"])
    try:
        await first_manager.start(session_id)
        await first_manager._tasks[session_id]
        assert (await first_manager.get(session_id)).status.value == "PAUSED"
        before = await first_manager.events(session_id)
        controls = [item for item in before if item.event_type == "calendar.observed"]
        assert [item.payload["after_completed_sessions"] for item in controls] == [0, 1]
        hydrated = await client.get(f"/api/paper-trading/sessions/{session_id}/events")
        assert hydrated.status_code == 200
        assert len([item for item in hydrated.json() if item["type"] == "calendar.observed"]) == 2
        await first_manager.shutdown()
        restarted = PaperTradingManager(
            SessionFactory, paper_manager._datasets, paper_manager._strategies
        )
        install(restarted)
        try:
            assert await restarted.recover_interrupted() == 0
            await restarted.start(session_id)
            await restarted._tasks[session_id]
            after = await restarted.events(session_id)
            assert after[: len(before)] == before
            assert [item.sequence for item in after] == list(range(1, len(after) + 1))
            assert len([item for item in after if item.event_type == "calendar.observed"]) == 2
            snapshot = await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")
            assert snapshot.status_code == 200
            state = snapshot.json()
            assert state["session"]["status"] == "STOPPED"
            assert state["latest_session"]["trading_date"] == "2024-01-03"
            assert Decimal(state["latest_portfolio"]["cash"]) == Decimal(created["initial_cash"])
            assert state["orders"] == state["fills"] == []
            journal_response = await client.get(f"/api/paper-trading/sessions/{session_id}/events")
            assert journal_response.status_code == 200
            assert [item["type"] for item in journal_response.json()].count("market.session") == 2
        finally:
            await restarted.shutdown()
    finally:
        await first_manager.shutdown()


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


def a_share_request_body() -> dict[str, object]:
    return {
        "provider_type": "simulated_a_share",
        "dataset_id": "CN_A_SIMULATED_PAPER_FIXTURE_V1",
        "symbol": "CN-A",
        "strategy": {
            "type": "cn_a_cross_sectional_momentum_low_vol_v1",
            "parameters": {},
        },
        "initial_cash": "100000000",
        "default_order_quantity": "1",
        "risk": {"enforce_buying_power": True},
    }


def historical_request_body() -> dict[str, object]:
    return {
        "provider_type": "historical_a_share",
        "dataset_id": "cn-a-research-20100101-20251231-v1",
        "symbol": "CN-A",
        "strategy": {
            "type": "cn_a_cross_sectional_momentum_low_vol_v1",
            "parameters": {
                "start_date": "2011-03-01",
                "end_date": "2011-03-31",
                "rebalance_sessions": 20,
                "maximum_holdings": 20,
                "max_position_weight": "0.1",
                "universe": "ALL",
                "commission_rate": "0.0003",
                "minimum_commission": "5",
            },
        },
        "initial_cash": "100000",
        "default_order_quantity": "1",
        "risk": {"enforce_buying_power": True, "max_leverage": "1"},
    }


async def test_historical_a_share_account_creation_has_distinct_mode_and_dated_config(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert paper_manager._historical_datasets is not None
    monkeypatch.setattr(
        paper_manager._historical_datasets,
        "resolve",
        lambda _: {
            "coverage_start": "2010-01-01",
            "coverage_end": "2025-12-31",
            "sha256": "a" * 64,
        },
    )
    headers = {"Idempotency-Key": "historical-paper-march-2011"}
    created = await client.post(
        "/api/paper-trading/sessions", json=historical_request_body(), headers=headers
    )
    assert created.status_code == 201
    assert created.json()["provider_type"] == "historical_a_share"
    assert created.json()["strategy_parameters"]["start_date"] == "2011-03-01"
    assert created.json()["strategy_parameters"]["dataset_sha256"] == "a" * 64
    assert created.json()["strategy_parameters"]["plan_version"] == "PAPER_ACCOUNT_PLAN_V3"
    assert created.json()["risk"]["max_drawdown"] == "-0.2"
    same = await client.post(
        "/api/paper-trading/sessions", json=historical_request_body(), headers=headers
    )
    assert same.json()["session_id"] == created.json()["session_id"]
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 1


async def test_historical_plan_checksum_covers_effective_account_risk(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert paper_manager._historical_datasets is not None
    monkeypatch.setattr(
        paper_manager._historical_datasets,
        "resolve",
        lambda _: {
            "coverage_start": "2010-01-01",
            "coverage_end": "2025-12-31",
            "sha256": "a" * 64,
        },
    )
    first = await client.post("/api/paper-trading/sessions", json=historical_request_body())
    changed = historical_request_body()
    changed["risk"] = {
        "enforce_buying_power": True,
        "max_leverage": "1",
        "max_order_notional": "5000",
    }
    second = await client.post("/api/paper-trading/sessions", json=changed)
    assert first.status_code == second.status_code == 201
    original = await paper_manager.get(UUID(first.json()["session_id"]))
    limited = await paper_manager.get(UUID(second.json()["session_id"]))
    assert original is not None and limited is not None
    original_request = paper_manager._historical_request(original)
    limited_request = paper_manager._historical_request(limited)
    assert original_request == limited_request
    assert paper_manager._historical_plan_sha(
        original, original_request
    ) != paper_manager._historical_plan_sha(limited, limited_request)


async def test_historical_account_rejects_cash_the_shared_engine_cannot_run(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert paper_manager._historical_datasets is not None
    monkeypatch.setattr(
        paper_manager._historical_datasets,
        "resolve",
        lambda _: {
            "coverage_start": "2010-01-01",
            "coverage_end": "2025-12-31",
            "sha256": "a" * 64,
        },
    )
    body = historical_request_body()
    body["initial_cash"] = "1000000000000.000000000000001"
    rejected = await client.post("/api/paper-trading/sessions", json=body)
    assert rejected.status_code == 422
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 0
    body["initial_cash"] = "1000000000000"
    accepted = await client.post("/api/paper-trading/sessions", json=body)
    assert accepted.status_code == 201
    assert accepted.json()["status"] == "CREATED"
    session = await paper_manager.get(UUID(accepted.json()["session_id"]))
    assert session is not None
    assert str(paper_manager._historical_request(session).initial_cash) == body["initial_cash"]


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


async def test_event_history_pages_preserve_order_transitions(client: AsyncClient) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])
    order_id = uuid4()
    timestamp = datetime.now(UTC)
    order = {
        "order_id": str(order_id),
        "strategy_id": "pagination-check",
        "symbol": "AAPL",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": "10",
        "price": None,
        "created_at": timestamp.isoformat(),
    }
    async with SessionFactory() as db:
        await SQLAlchemyPaperRepository(db).append_events(
            session_id,
            tuple(
                ("order.updated", timestamp, {**order, "status": status})
                for status in ("CREATED", "ACCEPTED", "FILLED")
            ),
        )

    path = f"/api/paper-trading/sessions/{session_id}/events"
    full = await client.get(path)
    assert full.status_code == 200
    assert [event["sequence"] for event in full.json()] == [1, 2, 3, 4]
    assert [event["payload"]["status"] for event in full.json()[1:]] == [
        "CREATED",
        "ACCEPTED",
        "FILLED",
    ]
    recent = await client.get(path, params={"limit": 2})
    assert [event["sequence"] for event in recent.json()] == [4, 3]
    assert [event["payload"]["status"] for event in recent.json()] == [
        "FILLED",
        "ACCEPTED",
    ]
    older = await client.get(path, params={"limit": 2, "before_sequence": 3})
    assert [event["sequence"] for event in older.json()] == [2, 1]
    before_only = await client.get(path, params={"before_sequence": 4})
    assert [event["sequence"] for event in before_only.json()] == [3, 2, 1]
    assert (await client.get(path, params={"before_sequence": 1})).json() == []
    for params in (
        {"limit": 0},
        {"limit": 201},
        {"before_sequence": 0},
        {"before_sequence": 2147483648},
    ):
        assert (await client.get(path, params=params)).status_code == 422


async def test_fill_time_cancellation_reason_survives_saved_account_reads(
    client: AsyncClient,
) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])
    timestamp = datetime.now(UTC)
    order = {
        "order_id": str(uuid4()),
        "strategy_id": "gap-check",
        "symbol": "AAPL",
        "side": "BUY",
        "order_type": "MARKET",
        "quantity": "10",
        "price": None,
        "status": "CANCELLED",
        "created_at": timestamp.isoformat(),
        "cancellation_reason_code": "INSUFFICIENT_BUYING_POWER",
    }
    async with SessionFactory() as db:
        await SQLAlchemyPaperRepository(db).append_events(
            session_id, (("order.updated", timestamp, order),)
        )

    path = f"/api/paper-trading/sessions/{session_id}"
    assert (await client.get(f"{path}/snapshot")).json()["orders"][0][
        "cancellation_reason_code"
    ] == "INSUFFICIENT_BUYING_POWER"
    assert (await client.get(f"{path}/events")).json()[-1]["payload"][
        "cancellation_reason_code"
    ] == "INSUFFICIENT_BUYING_POWER"


async def test_create_receipt_finds_committed_session_after_request_validation_fails(
    client: AsyncClient,
) -> None:
    headers = {"Idempotency-Key": "paper-lost-create-response"}
    created = await client.post("/api/paper-trading/sessions", json=request_body(), headers=headers)
    assert created.status_code == 201

    # A later request can fail current schema validation before create() sees the key.
    invalid = {**request_body(), "provider_type": "removed_provider"}
    assert (
        await client.post("/api/paper-trading/sessions", json=invalid, headers=headers)
    ).status_code == 422
    receipt = await client.get("/api/paper-trading/sessions/receipt", headers=headers)
    assert receipt.status_code == 200
    assert receipt.headers["cache-control"] == "no-store"
    assert receipt.json() == created.json()
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 1


async def test_create_receipt_absence_does_not_claim_request_will_never_commit(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    headers = {"Idempotency-Key": "paper-in-flight-create"}
    entered = asyncio.Event()
    proceed = asyncio.Event()
    original_create = SQLAlchemyPaperRepository.create

    async def delayed_create(
        self: SQLAlchemyPaperRepository, session: PaperSession
    ) -> PaperSession:
        entered.set()
        await proceed.wait()
        return await original_create(self, session)

    monkeypatch.setattr(SQLAlchemyPaperRepository, "create", delayed_create)
    pending = asyncio.create_task(
        client.post("/api/paper-trading/sessions", json=request_body(), headers=headers)
    )
    try:
        await asyncio.wait_for(entered.wait(), timeout=10)
        unknown = await client.get("/api/paper-trading/sessions/receipt", headers=headers)
        assert unknown.status_code == 404
        assert unknown.headers["cache-control"] == "no-store"
        assert "currently" in unknown.json()["detail"]
    finally:
        proceed.set()
    created = await pending
    assert created.status_code == 201
    found = await client.get("/api/paper-trading/sessions/receipt", headers=headers)
    assert found.status_code == 200
    assert found.json()["session_id"] == created.json()["session_id"]

    absent = await client.get(
        "/api/paper-trading/sessions/receipt",
        headers={"Idempotency-Key": "paper-never-sent"},
    )
    assert absent.status_code == 404
    assert absent.headers["cache-control"] == "no-store"
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 1
    assert (await client.get("/api/paper-trading/sessions/receipt")).status_code == 422
    assert (
        await client.get(
            "/api/paper-trading/sessions/receipt",
            headers={"Idempotency-Key": "x" * 256},
        )
    ).status_code == 422


@pytest.mark.parametrize("historical", [False, True])
async def test_create_replay_precedes_mutable_dataset_validation(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, historical: bool
) -> None:
    body = historical_request_body() if historical else request_body()
    headers = {"Idempotency-Key": f"paper-source-outage-{historical}"}
    if historical:
        assert paper_manager._historical_datasets is not None
        monkeypatch.setattr(
            paper_manager._historical_datasets,
            "resolve",
            lambda _: {
                "coverage_start": "2010-01-01",
                "coverage_end": "2025-12-31",
                "sha256": "a" * 64,
            },
        )
    created = await client.post("/api/paper-trading/sessions", json=body, headers=headers)
    assert created.status_code == 201

    if historical:

        def unavailable_historical(_: str) -> None:
            raise ExperimentInputError("DATASET_NOT_MOUNTED")

        monkeypatch.setattr(paper_manager._historical_datasets, "resolve", unavailable_historical)
    else:

        def unavailable_replay(_: str, __: str) -> None:
            raise UnknownDatasetError("dataset unavailable")

        monkeypatch.setattr(paper_manager._datasets, "resolve", unavailable_replay)

    replay = await client.post("/api/paper-trading/sessions", json=body, headers=headers)
    assert replay.status_code == 201
    assert replay.json() == created.json()
    changed = await client.post(
        "/api/paper-trading/sessions", json={**body, "initial_cash": "100001"}, headers=headers
    )
    assert changed.status_code == 409
    new_key = await client.post(
        "/api/paper-trading/sessions",
        json=body,
        headers={"Idempotency-Key": f"paper-source-outage-new-{historical}"},
    )
    assert new_key.status_code == (422 if historical else 404)
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 1


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


async def test_frozen_a_share_simulation_persists_signal_fill_and_portfolio(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    created = await client.post("/api/paper-trading/sessions", json=a_share_request_body())
    assert created.status_code == 201
    session_id = created.json()["session_id"]
    assert (await client.post(f"/api/paper-trading/sessions/{session_id}/start")).status_code == 200

    detail: dict[str, object] = {}
    for _ in range(500):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "STOPPED":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "STOPPED"
    snapshot = (await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")).json()
    assert snapshot["latest_session"] == {
        "trading_date": "2030-12-23",
        "security_count": 10,
        "source": "SIMULATED_SCENARIO_NOT_RESEARCH_EVIDENCE_V1",
    }
    assert len(snapshot["signals"]) == len(snapshot["risk_decisions"]) == 1
    assert len(snapshot["orders"]) == len(snapshot["fills"]) == 1
    assert snapshot["orders"][0]["status"] == "FILLED"
    assert len(snapshot["latest_portfolio"]["positions"]) == 1
    assert snapshot["latest_portfolio"]["cash"] == "1223.5"
    assert snapshot["fills"][0]["price"] == "23.845"
    assert snapshot["fills"][0]["commission"] == "0"
    assert snapshot["fills"][0]["timestamp"] == "2030-12-23T01:25:00Z"
    assert snapshot["last_sequence"] > 0

    events = await client.get(f"/api/paper-trading/sessions/{session_id}/events")
    assert events.status_code == 200
    sequences = [item["sequence"] for item in events.json()]
    assert sequences == list(range(1, len(sequences) + 1))
    assert all("payload" in item for item in events.json())
    event_types = [item["type"] for item in events.json()]
    fill_index = event_types.index("fill.created")
    assert event_types[fill_index - 2 : fill_index + 2] == [
        "market.session",
        "order.updated",
        "fill.created",
        "portfolio.snapshot",
    ]

    repeat_start = await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    assert repeat_start.status_code == 409
    stopped = await client.post(f"/api/paper-trading/sessions/{session_id}/stop")
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "STOPPED"


async def test_paused_a_share_replays_checkpoint_after_restart_without_duplicate_ledger(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    baseline = (
        await client.post("/api/paper-trading/sessions", json=a_share_request_body())
    ).json()
    baseline_id = baseline["session_id"]
    await client.post(f"/api/paper-trading/sessions/{baseline_id}/start")
    for _ in range(500):
        if (await client.get(f"/api/paper-trading/sessions/{baseline_id}")).json()[
            "status"
        ] == "STOPPED":
            break
        await asyncio.sleep(0.01)
    assert (await client.get(f"/api/paper-trading/sessions/{baseline_id}")).json()[
        "status"
    ] == "STOPPED"
    expected = (await client.get(f"/api/paper-trading/sessions/{baseline_id}/events")).json()
    expected_market = [
        (item["type"], item["payload"]) for item in expected if item["type"] != "session.status"
    ]

    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0.1)
    created = (await client.post("/api/paper-trading/sessions", json=a_share_request_body())).json()
    session_id = created["session_id"]
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        events = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
        if any(item["type"] == "market.session" for item in events):
            break
        await asyncio.sleep(0.01)
    assert any(item["type"] == "market.session" for item in events)
    assert (await client.post(f"/api/paper-trading/sessions/{session_id}/pause")).json()[
        "status"
    ] in {"PAUSING", "PAUSED"}
    for _ in range(100):
        paused = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if paused["status"] == "PAUSED":
            break
        await asyncio.sleep(0.01)
    assert paused["status"] == "PAUSED"
    assert await paper_manager.recover_interrupted() == 0
    await paper_manager.shutdown()
    assert (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()[
        "status"
    ] == "PAUSED"

    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    assert (await client.post(f"/api/paper-trading/sessions/{session_id}/start")).json()[
        "status"
    ] == "STARTING"
    for _ in range(500):
        resumed = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if resumed["status"] in {"STOPPED", "FAILED"}:
            break
        await asyncio.sleep(0.01)
    assert resumed["status"] == "STOPPED", resumed
    assert resumed["started_at"] == paused["started_at"]
    actual = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
    actual_market = [
        (item["type"], item["payload"]) for item in actual if item["type"] != "session.status"
    ]
    assert actual_market == expected_market
    assert [item["payload"]["status"] for item in actual if item["type"] == "session.status"] == [
        "CREATED",
        "STARTING",
        "RUNNING",
        "PAUSING",
        "PAUSED",
        "STARTING",
        "RUNNING",
        "STOPPED",
    ]


async def test_paused_bar_replay_matches_uninterrupted_ledger(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    baseline_id = (await client.post("/api/paper-trading/sessions", json=request_body())).json()[
        "session_id"
    ]
    await client.post(f"/api/paper-trading/sessions/{baseline_id}/start")
    for _ in range(100):
        baseline = (await client.get(f"/api/paper-trading/sessions/{baseline_id}")).json()
        if baseline["status"] == "STOPPED":
            break
        await asyncio.sleep(0.01)
    assert baseline["status"] == "STOPPED"

    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 10)
    session_id = (await client.post("/api/paper-trading/sessions", json=request_body())).json()[
        "session_id"
    ]
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        events = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
        if any(item["type"] == "market.bar" for item in events):
            break
        await asyncio.sleep(0.01)
    assert any(item["type"] == "market.bar" for item in events)
    await client.post(f"/api/paper-trading/sessions/{session_id}/pause")
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "PAUSED":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "PAUSED"
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] in {"STOPPED", "FAILED"}:
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "STOPPED", detail
    expected = (await client.get(f"/api/paper-trading/sessions/{baseline_id}/events")).json()
    actual = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
    assert [
        (item["type"], item["payload"]) for item in actual if item["type"] != "session.status"
    ] == [(item["type"], item["payload"]) for item in expected if item["type"] != "session.status"]


@pytest.mark.parametrize("provider_type", ["replay", "simulated_a_share"])
async def test_missing_resume_checkpoint_does_not_append_unverified_market_ledger(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, provider_type: str
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 10)
    body = request_body() if provider_type == "replay" else a_share_request_body()
    session_id = (await client.post("/api/paper-trading/sessions", json=body)).json()["session_id"]
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        before = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
        if any(item["type"] in {"market.bar", "market.session"} for item in before):
            break
        await asyncio.sleep(0.01)
    assert any(item["type"] in {"market.bar", "market.session"} for item in before)
    await client.post(f"/api/paper-trading/sessions/{session_id}/pause")
    for _ in range(100):
        paused = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if paused["status"] == "PAUSED":
            break
        await asyncio.sleep(0.01)
    assert paused["status"] == "PAUSED"
    before = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
    build_runtime = paper_manager._build_runtime

    def missing_checkpoint(session, cursor_date):
        provider, runtime = build_runtime(session, cursor_date)
        if isinstance(provider, ReplayMarketDataProvider):
            provider._bars = provider._bars[1:]
        else:
            assert isinstance(provider, SimulatedAShareSessionProvider)
            provider._sessions = tuple(provider._sessions)[1:]
        return provider, runtime

    monkeypatch.setattr(paper_manager, "_build_runtime", missing_checkpoint)
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(500):
        failed = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if failed["status"] in {"STOPPED", "FAILED"}:
            break
        await asyncio.sleep(0.01)
    assert failed["status"] == "FAILED", failed
    after = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
    assert [
        (item["type"], item["payload"]) for item in after if item["type"] != "session.status"
    ] == [(item["type"], item["payload"]) for item in before if item["type"] != "session.status"]
    assert (await client.post(f"/api/paper-trading/sessions/{session_id}/start")).status_code == 409


async def test_real_archive_pause_resume_preserves_pending_orders_and_fills(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not (settings.research_data_path / HISTORICAL_ID).is_dir():
        pytest.skip("optional read-only historical archive is not mounted")
    body = historical_request_body()
    assert isinstance(body["strategy"], dict)
    body["strategy"]["parameters"]["end_date"] = "2011-03-23"

    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    baseline = await client.post("/api/paper-trading/sessions", json=body)
    assert baseline.status_code == 201, baseline.text
    assert baseline.json()["strategy_parameters"]["plan_version"] == "PAPER_ACCOUNT_PLAN_V3"
    baseline_id = baseline.json()["session_id"]
    await client.post(f"/api/paper-trading/sessions/{baseline_id}/start")
    for _ in range(1200):
        baseline_status = (await client.get(f"/api/paper-trading/sessions/{baseline_id}")).json()
        if baseline_status["status"] in {"STOPPED", "FAILED"}:
            break
        await asyncio.sleep(0.05)
    assert baseline_status["status"] == "STOPPED", baseline_status
    baseline_events = (await client.get(f"/api/paper-trading/sessions/{baseline_id}/events")).json()
    assert sum(item["type"] == "fill.created" for item in baseline_events) == 6
    baseline_plans = [
        item["payload"]["plan"]
        for item in baseline_events
        if item["type"] == "portfolio.snapshot" and item["payload"].get("plan")
    ]
    for plan in baseline_plans:
        assert plan["plan_version"] == "PAPER_ACCOUNT_PLAN_V3"
        assert plan["account_snapshot_trading_date"] == (
            plan["as_of_trading_date"] if plan["account"] is not None else None
        )
        assert plan["not_today_advice"] is True
    assert baseline_plans[-2]["as_of_trading_date"] == "2011-03-22"
    assert baseline_plans[-2]["paper_session_id"] == baseline_id
    assert baseline_plans[-2]["submitted_to_account"] is True
    assert baseline_plans[-2]["candidates"]
    assert baseline_plans[-2]["account_mode"] == "HISTORICAL_PAPER_REPLAY"
    baseline_session = await paper_manager.get(UUID(baseline_id))
    assert baseline_session is not None
    assert baseline_plans[-2]["configuration_sha256"] == paper_manager._historical_plan_sha(
        baseline_session, paper_manager._historical_request(baseline_session)
    )
    baseline_snapshot = (
        await client.get(f"/api/paper-trading/sessions/{baseline_id}/snapshot")
    ).json()
    assert baseline_snapshot["latest_session"]["trading_date"] == "2011-03-23"
    assert baseline_snapshot["latest_portfolio"]["plan"]["status"] == "NOT_REBALANCE_SESSION"
    assert baseline_snapshot["last_rebalance_plan"]["as_of_trading_date"] == "2011-03-22"
    assert baseline_snapshot["last_rebalance_plan"]["paper_session_id"] == baseline_id

    legacy = await client.post("/api/paper-trading/sessions", json=body)
    assert legacy.status_code == 201, legacy.text
    legacy_id = legacy.json()["session_id"]
    legacy_parameters = dict(legacy.json()["strategy_parameters"])
    legacy_parameters.pop("plan_version")
    async with SessionFactory() as db:
        await db.execute(
            update(PaperTradingSessionModel)
            .where(PaperTradingSessionModel.id == UUID(legacy_id))
            .values(strategy_parameters=legacy_parameters)
        )
        await db.commit()
    legacy_row = await paper_manager.get(UUID(legacy_id))
    assert legacy_row is not None and "plan_version" not in legacy_row.strategy_parameters
    await client.post(f"/api/paper-trading/sessions/{legacy_id}/start")
    for _ in range(1200):
        legacy_status = (await client.get(f"/api/paper-trading/sessions/{legacy_id}")).json()
        if legacy_status["status"] in {"STOPPED", "FAILED"}:
            break
        await asyncio.sleep(0.05)
    assert legacy_status["status"] == "STOPPED", legacy_status
    legacy_events = (await client.get(f"/api/paper-trading/sessions/{legacy_id}/events")).json()
    assert sum(item["type"] == "fill.created" for item in legacy_events) == 6
    assert all(
        item["payload"].get("plan") is None
        for item in legacy_events
        if item["type"] == "portfolio.snapshot"
    )
    assert all(
        "plan" not in item.payload
        for item in await paper_manager.events(UUID(legacy_id))
        if item.event_type == "portfolio.snapshot"
    )
    legacy_snapshot = (await client.get(f"/api/paper-trading/sessions/{legacy_id}/snapshot")).json()
    assert legacy_snapshot["last_rebalance_plan"] is None

    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0.3)
    created = await client.post("/api/paper-trading/sessions", json=body)
    assert created.status_code == 201, created.text
    session_id = created.json()["session_id"]
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(1200):
        current = (await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")).json()
        if current["latest_session"] and current["latest_session"]["trading_date"] == "2011-03-22":
            break
        if current["session"]["status"] in {"FAILED", "STOPPED"}:
            break
        await asyncio.sleep(0.05)
    assert current["latest_session"]["trading_date"] == "2011-03-22", current
    assert current["latest_portfolio"]["plan"]["as_of_trading_date"] == "2011-03-22"
    assert current["latest_portfolio"]["plan"]["paper_session_id"] == session_id
    await client.post(f"/api/paper-trading/sessions/{session_id}/pause")
    for _ in range(100):
        paused = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if paused["status"] == "PAUSED":
            break
        await asyncio.sleep(0.01)
    assert paused["status"] == "PAUSED"
    assert (
        len(
            (await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")).json()[
                "orders"
            ]
        )
        == 20
    )
    paused_events = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
    await paper_manager.shutdown()
    # Fresh runtime ownership, with no tasks/providers/cache inherited from the old manager.
    restarted = paper_routes.PaperTradingManager(
        SessionFactory,
        paper_routes.DatasetRegistry.phase7(settings.backtest_fixture_path),
        paper_routes.StrategyRegistry(),
        historical_datasets=paper_routes.ExperimentDatasetRegistry(settings.research_data_path),
        replay_interval_seconds=0,
    )
    try:
        monkeypatch.setattr(paper_routes, "paper_manager", restarted)
        assert await restarted.recover_interrupted() == 0
        restored = await restarted.get(UUID(session_id))
        assert restored is not None and restored.status.value == "PAUSED"
        assert (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json() == (
            paused_events
        )
        started = await client.post(f"/api/paper-trading/sessions/{session_id}/start")
        assert started.status_code == 200
        for _ in range(1200):
            resumed = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
            if resumed["status"] in {"STOPPED", "FAILED"}:
                break
            await asyncio.sleep(0.05)
    finally:
        await restarted.shutdown()
    assert resumed["status"] == "STOPPED", resumed
    assert resumed["started_at"] == paused["started_at"]
    resumed_events = (await client.get(f"/api/paper-trading/sessions/{session_id}/events")).json()
    assert resumed_events[: len(paused_events)] == paused_events
    resumed_snapshot = (
        await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")
    ).json()
    assert resumed_snapshot["last_rebalance_plan"]["as_of_trading_date"] == "2011-03-22"
    assert resumed_snapshot["last_rebalance_plan"]["paper_session_id"] == session_id

    def comparable_events(events: list[dict[str, object]]) -> list[tuple[object, object]]:
        result = []
        for item in events:
            if item["type"] == "session.status":
                continue
            payload = item["payload"]
            assert isinstance(payload, dict)
            if item["type"] == "portfolio.snapshot" and payload.get("plan"):
                plan = payload["plan"]
                assert isinstance(plan, dict)
                payload = {**payload, "plan": {**plan, "paper_session_id": "<account>"}}
            result.append((item["type"], payload))
        return result

    assert comparable_events(resumed_events) == comparable_events(baseline_events)


async def test_stopping_paused_account_cancels_persisted_pending_order(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 10)
    session_id = (await client.post("/api/paper-trading/sessions", json=request_body())).json()[
        "session_id"
    ]
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "RUNNING":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "RUNNING"
    await client.post(f"/api/paper-trading/sessions/{session_id}/pause")
    for _ in range(100):
        detail = (await client.get(f"/api/paper-trading/sessions/{session_id}")).json()
        if detail["status"] == "PAUSED":
            break
        await asyncio.sleep(0.01)
    assert detail["status"] == "PAUSED"
    order_id = uuid4()
    async with SessionFactory() as session:
        await SQLAlchemyPaperRepository(session).append_events(
            UUID(session_id),
            (
                (
                    "order.updated",
                    datetime.now(UTC),
                    {
                        "order_id": str(order_id),
                        "strategy_id": "pause-audit",
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
    assert (await client.post(f"/api/paper-trading/sessions/{session_id}/stop")).json()[
        "status"
    ] == "STOPPED"
    snapshot = (await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")).json()
    assert snapshot["orders"][0]["order_id"] == str(order_id)
    assert snapshot["orders"][0]["status"] == "CANCELLED"
    assert snapshot["fills"] == []


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


async def test_terminal_paper_account_rejects_late_market_events(client: AsyncClient) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])
    stopped = await client.post(f"/api/paper-trading/sessions/{session_id}/stop")
    assert stopped.json()["status"] == "STOPPED"
    before = await paper_manager.events(session_id)
    async with SessionFactory() as db:
        with pytest.raises(PaperSessionConcurrencyError, match="already terminal"):
            await SQLAlchemyPaperRepository(db).append_events(
                session_id, (("market.bar", datetime.now(UTC), {}),)
            )
    assert await paper_manager.events(session_id) == before


@pytest.mark.parametrize(
    "order_status, expected_status",
    [
        ("CREATED", "CANCELLED"),
        ("SUBMITTED", "CANCELLED"),
        ("ACCEPTED", "CANCELLED"),
        ("PARTIALLY_FILLED", "CANCELLED"),
        ("FILLED", "FILLED"),
        ("CANCELLED", "CANCELLED"),
        ("REJECTED", "REJECTED"),
    ],
)
async def test_restart_contract_marks_orphaned_runtime_interrupted(
    client: AsyncClient, order_status: str, expected_status: str
) -> None:
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
                        "status": order_status,
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
    assert events.json()[-2]["payload"]["status"] == expected_status
    snapshot = await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")
    assert snapshot.json()["orders"][0]["status"] == expected_status


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
    def fail_to_build_runtime(_session: object, _cursor_date: object) -> object:
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
    assert statuses in (
        ["CREATED", "STARTING", "STOPPING", "STOPPED"],
        ["CREATED", "STARTING", "RUNNING", "STOPPING", "STOPPED"],
    )
    if "RUNNING" not in statuses:
        assert all(item["type"] not in {"market.bar", "market.session"} for item in events)


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


async def test_rest_snapshot_status_matches_its_journal_during_replay(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        snapshot = await paper_manager.snapshot(session_id)
        assert snapshot is not None
        session, events = snapshot
        statuses = [
            item.payload["status"] for item in events if item.event_type == "session.status"
        ]
        assert statuses[-1] == session.status.value
        if session.status.value == "STOPPED":
            break
        await asyncio.sleep(0.01)
    assert session.status.value == "STOPPED"


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


async def test_runtime_failure_cancels_order_persisted_after_replay_started(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = created.json()["session_id"]
    order_id = uuid4()

    async def fail_after_order_was_saved(
        _provider: ReplayMarketDataProvider, _on_bar: object
    ) -> None:
        async with SessionFactory() as db:
            await SQLAlchemyPaperRepository(db).append_events(
                UUID(session_id),
                (
                    (
                        "order.updated",
                        datetime.now(UTC),
                        {
                            "order_id": str(order_id),
                            "strategy_id": "failure-audit",
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
        raise RuntimeError("uncommitted market step")

    monkeypatch.setattr(ReplayMarketDataProvider, "start", fail_after_order_was_saved)
    await client.post(f"/api/paper-trading/sessions/{session_id}/start")
    for _ in range(100):
        snapshot = (await client.get(f"/api/paper-trading/sessions/{session_id}/snapshot")).json()
        if snapshot["session"]["status"] == "FAILED":
            break
        await asyncio.sleep(0.01)
    assert snapshot["session"]["status"] == "FAILED"
    assert snapshot["orders"][0]["order_id"] == str(order_id)
    assert snapshot["orders"][0]["status"] == "CANCELLED"
    assert snapshot["fills"] == []

    # A fresh manager must observe the committed terminal journal, not replay
    # the failed runtime's in-memory order or append another terminal event.
    before_restart = await paper_manager.snapshot(UUID(session_id))
    restarted = paper_routes.PaperTradingManager(
        SessionFactory,
        paper_routes.DatasetRegistry.phase7(settings.backtest_fixture_path),
        paper_routes.StrategyRegistry(),
        historical_datasets=paper_routes.ExperimentDatasetRegistry(settings.research_data_path),
    )
    try:
        assert await restarted.recover_interrupted() == 0
        assert await restarted.snapshot(UUID(session_id)) == before_restart
        with pytest.raises(paper_routes.PaperSessionStateError, match="cannot start from FAILED"):
            await restarted.start(UUID(session_id))
        assert await restarted.snapshot(UUID(session_id)) == before_restart
    finally:
        await restarted.shutdown()


class FakeWebSocket:
    def __init__(self, *, fail_after_connect: bool = False, origin: str | None = None) -> None:
        self.headers = {"origin": origin or settings.frontend_origin}
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


async def test_websocket_rejects_untrusted_origin() -> None:
    websocket = FakeWebSocket(origin="https://untrusted.example")
    await paper_session_websocket(websocket, UUID(int=0))  # type: ignore[arg-type]
    assert websocket.closed == (4403, "origin not allowed")


@pytest.mark.parametrize("origin", ["http://localhost:5173", "http://127.0.0.1:5173"])
async def test_websocket_disconnect_and_delivery_failure_release_subscriptions(
    client: AsyncClient,
    origin: str,
) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])

    websocket = FakeWebSocket(origin=origin)
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
    assert response.json() == {"detail": "internal server error"}
    assert "sensitive" not in response.text


async def test_cancelling_websocket_handler_releases_child_tasks(client: AsyncClient) -> None:
    created = await client.post("/api/paper-trading/sessions", json=request_body())
    session_id = UUID(created.json()["session_id"])
    before = asyncio.all_tasks()
    websocket = FakeWebSocket()
    task = asyncio.create_task(paper_session_websocket(websocket, session_id))  # type: ignore[arg-type]
    for _ in range(100):
        if websocket.sent:
            break
        await asyncio.sleep(0.001)
    await asyncio.sleep(0)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.sleep(0)
    assert paper_manager.hub.subscriber_count(session_id) == 0
    assert not (asyncio.all_tasks() - before)


async def test_session_lifecycle_rejects_a_naive_clock(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(paper_manager, "_clock", lambda: datetime(2026, 9, 6))
    response = await client.post("/api/paper-trading/sessions", json=request_body())
    assert response.status_code == 422
    assert response.json()["detail"] == "paper session clock must be timezone-aware"
    assert (await client.get("/api/paper-trading/sessions")).json()["total"] == 0
