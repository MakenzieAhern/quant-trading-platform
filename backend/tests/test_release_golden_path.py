import asyncio
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.routes.paper import paper_manager
from app.db.repositories import SQLAlchemyBacktestRepository
from app.db.session import SessionFactory
from app.main import app


async def test_persisted_backtest_and_paper_golden_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same fixture through both public APIs; persisted financial output must agree."""
    body = {
        "dataset_id": "AAPL_fixture",
        "symbol": "AAPL",
        "strategy": {
            "type": "moving_average_crossover",
            "parameters": {"short_period": 2, "long_period": 3},
        },
        "initial_cash": "100000.052500000000000001",
        "default_order_quantity": "10",
        "risk": {"enforce_buying_power": True},
    }
    monkeypatch.setattr(paper_manager, "_replay_interval_seconds", 0)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        run = await client.post("/api/backtests", json=body)
        assert run.status_code == 201
        run_id = run.json()["run_id"]
        root = f"/api/backtests/{run_id}"
        detail = (await client.get(root)).json()
        assert detail["status"] == "SUCCEEDED"
        assert detail["metrics"]["final_equity"] == "100012.252500000000000001"
        collections = {}
        for name in ("signals", "risk-decisions", "orders", "fills", "equity"):
            response = await client.get(f"{root}/{name}")
            assert response.status_code == 200
            collections[name] = response.json()["items"]
            assert collections[name]
        async with SessionFactory() as db:
            snapshots = await SQLAlchemyBacktestRepository(db).list_snapshots(UUID(run_id), 200, 0)
            assert snapshots.total == 6
        session = await client.post("/api/paper-trading/sessions", json=body)
        assert session.status_code == 201
        session_id = UUID(session.json()["session_id"])
        paper_root = f"/api/paper-trading/sessions/{session_id}"
        async with paper_manager.hub.subscribe(session_id) as queue:
            assert (await client.post(f"{paper_root}/start")).status_code == 200
            for _ in range(200):
                state = (await client.get(paper_root)).json()
                if state["status"] == "STOPPED":
                    break
                await asyncio.sleep(0.01)
            assert state["status"] == "STOPPED"
            assert not queue.empty()
        assert (await client.post(f"{paper_root}/stop")).status_code == 200
        snapshot = (await client.get(f"{paper_root}/snapshot")).json()
        reloaded = (await client.get(f"{paper_root}/snapshot")).json()
        assert snapshot == reloaded
        assert snapshot["signals"] == collections["signals"]
        # Each engine uses its own deterministic order-ID namespace.
        for name in ("fills", "orders"):
            assert [
                {key: value for key, value in item.items() if key != "order_id"}
                for item in snapshot[name]
            ] == [
                {key: value for key, value in item.items() if key != "order_id"}
                for item in collections[name]
            ]
        assert snapshot["latest_portfolio"]["equity"] == detail["metrics"]["final_equity"]
        assert snapshot["latest_portfolio"]["cash"] == collections["equity"][-1]["cash"]
    await paper_manager.shutdown()
