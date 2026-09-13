from collections.abc import AsyncIterator
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app.db.models.research import (
    ResearchDatasetModel,
    ResearchEquityPointModel,
    ResearchMetricModel,
    ResearchRunModel,
)
from app.db.session import SessionFactory
from app.main import app
from app.strategies.research import STRATEGY_ID


@pytest.fixture(autouse=True)
async def clean_research_tables() -> AsyncIterator[None]:
    async with SessionFactory() as session:
        await session.execute(text("TRUNCATE TABLE research_datasets CASCADE"))
        await session.commit()
    yield
    async with SessionFactory() as session:
        await session.execute(text("TRUNCATE TABLE research_datasets CASCADE"))
        await session.commit()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value


async def _seed_dataset(*, ready: bool = True) -> None:
    async with SessionFactory() as session:
        session.add(
            ResearchDatasetModel(
                dataset_id="cn-a-fixture-v1",
                provider="BaoStock",
                provider_version="0.9.3",
                retrieval_timestamp=datetime(2026, 9, 7, tzinfo=UTC),
                coverage_start=date(2010, 1, 1),
                coverage_end=date(2025, 12, 31),
                security_count=3,
                canonical_sha256="a" * 64,
                rule_version="cn-a-rules-v1",
                adjustment_method="BaoStock pre-adjusted close with raw execution prices",
                manifest={"financial": "1.2300"},
                readiness_status="PASSED" if ready else "BLOCKED",
                frozen=ready,
            )
        )
        await session.commit()


async def test_market_and_strategy_registries_are_read_only(client: AsyncClient) -> None:
    markets = await client.get("/api/research/markets")
    strategies = await client.get("/api/research/strategies")
    assert markets.status_code == 200
    assert markets.json()[0]["market_id"] == "CN_A"
    assert strategies.status_code == 200
    assert strategies.json()[0]["strategy_id"] == STRATEGY_ID


async def test_unknown_dataset_uses_stable_error_contract(client: AsyncClient) -> None:
    response = await client.get("/api/research/datasets/not-found")
    assert response.status_code == 404
    assert response.json()["code"] == "RESEARCH_DATASET_NOT_FOUND"
    assert response.json()["details"] == {}
    assert response.json()["request_id"]


async def test_run_creation_rejects_unregistered_strategy_and_unapproved_oos(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _seed_dataset()
    monkeypatch.setenv("GIT_COMMIT", "b" * 40)
    invalid = await client.post(
        "/api/research/runs",
        json={
            "dataset_id": "cn-a-fixture-v1",
            "strategy_id": "os.system",
            "benchmark_id": "CSI300",
            "period_kind": "DEVELOPMENT",
        },
    )
    oos = await client.post(
        "/api/research/runs",
        json={
            "dataset_id": "cn-a-fixture-v1",
            "strategy_id": STRATEGY_ID,
            "benchmark_id": "CSI300",
            "period_kind": "OUT_OF_SAMPLE",
        },
    )
    assert invalid.json()["code"] == "RESEARCH_STRATEGY_NOT_FOUND"
    assert oos.json()["code"] == "OOS_APPROVAL_REQUIRED"


async def test_created_run_persists_complete_lineage_and_survives_new_session(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _seed_dataset()
    monkeypatch.setenv("GIT_COMMIT", "c" * 40)
    created = await client.post(
        "/api/research/runs",
        json={
            "dataset_id": "cn-a-fixture-v1",
            "strategy_id": STRATEGY_ID,
            "benchmark_id": "CSI300",
            "period_kind": "VALIDATION",
        },
    )
    assert created.status_code == 201, created.text
    run_id = UUID(created.json()["run_id"])
    async with SessionFactory() as session:
        persisted = await session.get(ResearchRunModel, run_id)
        assert persisted is not None
        assert persisted.git_commit == "c" * 40
        assert persisted.dataset_checksum == "a" * 64
        assert persisted.random_seed == 0
        assert persisted.diagnostics["accounting_policies"]["zero_whole_share_policy"] == (
            "WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"
        )
        session.add(
            ResearchMetricModel(
                run_id=run_id,
                period_kind="VALIDATION",
                metric_name="cagr",
                value=Decimal("0.12345678901234567890123456789012345678"),
            )
        )
        session.add(
            ResearchEquityPointModel(
                run_id=run_id,
                sequence=1,
                trading_date=date(2018, 1, 2),
                value=Decimal("100000.00000000000000000000000000000000000000"),
            )
        )
        await session.commit()

    metrics = await client.get(f"/api/research/runs/{run_id}/metrics")
    equity = await client.get(f"/api/research/runs/{run_id}/equity")
    assert metrics.json()["items"][0]["value"] == "0.12345678901234567890123456789012345678"
    assert equity.json()["items"][0]["value"] == "100000"
    async with SessionFactory() as session:
        assert await session.scalar(
            select(ResearchRunModel.id).where(ResearchRunModel.id == run_id)
        )
