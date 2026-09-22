import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.api.routes import markets
from app.application.experiments.data import DEMO_ID, HISTORICAL_ID, ExperimentDatasetRegistry
from app.application.markets import MarketReader
from app.application.watchlist import WatchlistService
from app.core.config import get_settings
from app.db.session import SessionFactory
from app.main import app
from tests.test_product_markets import SID
from tests.test_product_markets import archive as archive


@pytest.fixture
async def watchlist(tmp_path, monkeypatch):
    assert get_settings().app_env == "test"
    assert "quant_test" in get_settings().database_url
    async with SessionFactory() as db, db.begin():
        await db.execute(text("TRUNCATE product_watchlist"))
    service = WatchlistService(SessionFactory, MarketReader(ExperimentDatasetRegistry(tmp_path)))
    monkeypatch.setattr(markets, "watchlist_service", service)
    return service


async def test_watchlist_idempotent_concurrent_persistent_paginated_and_removable(watchlist):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        path = f"/api/markets/watchlist/{SID}"
        left, right = await asyncio.gather(
            *[client.put(path, json={"dataset_id": DEMO_ID}) for _ in range(2)]
        )
        assert left.status_code == right.status_code == 200
        assert left.json() == right.json()
        assert left.json()["security"]["name_temporal_authority"] == "SYNTHETIC_DEMO"
        await client.put(path.replace("600000", "600001"), json={"dataset_id": DEMO_ID})
        page = (await client.get("/api/markets/watchlist?limit=1")).json()
        assert page["total"] == 2 and len(page["items"]) == 1
        assert page["items"][0]["source_available"]
        assert page["items"][0]["source_reason_code"] is None
        # A fresh application service sees persisted rows, not process-local preferences.
        reopened = WatchlistService(SessionFactory, watchlist.reader)
        assert (await reopened.list(1, 1))["items"][0]["security_id"] == SID
        assert (await client.delete(path, params={"dataset_id": DEMO_ID})).status_code == 204
        assert (await client.delete(path, params={"dataset_id": DEMO_ID})).status_code == 204
        assert (await reopened.list(50, 0))["total"] == 1


async def test_watchlist_historical_snapshot_survives_optional_archive_unmount(
    watchlist,
    archive,  # noqa: F811 - imported shared pytest fixture
    tmp_path,
):
    watchlist.reader = archive
    item = await watchlist.add(HISTORICAL_ID, SID)
    assert item["security"]["source_observed_name"] == "测试银行"
    watchlist.reader = MarketReader(ExperimentDatasetRegistry(tmp_path / "not-mounted"))
    listed = await watchlist.list(50, 0)
    assert listed["items"][0]["security"] == item["security"]
    assert listed["items"][0]["source_available"] is False
    assert listed["items"][0]["source_reason_code"] == "DATASET_NOT_MOUNTED"
    await watchlist.remove(HISTORICAL_ID, SID)
    assert (await watchlist.list(50, 0))["total"] == 0


async def test_watchlist_rejects_unknown_security_dataset_and_unsafe_input(watchlist):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        path = f"/api/markets/watchlist/{SID}"
        assert (await client.put(path, json={"dataset_id": "unknown"})).status_code == 422
        assert (await client.put(path, json={"dataset_id": HISTORICAL_ID})).json()[
            "code"
        ] == "DATASET_NOT_MOUNTED"
        assert (
            await client.put(path.replace("600000", "600999"), json={"dataset_id": DEMO_ID})
        ).status_code == 404
        for body in ({"dataset_id": "../escape"}, {"dataset_id": DEMO_ID, "name": "injected"}):
            assert (await client.put(path, json=body)).status_code == 422
        assert (await client.get("/api/markets/watchlist?limit=1000")).status_code == 422
        assert (await client.get("/api/markets/watchlist")).json()["items"] == []
