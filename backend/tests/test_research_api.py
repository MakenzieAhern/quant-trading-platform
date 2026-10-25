from collections.abc import AsyncIterator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text

from app.db.models.research import (
    ResearchBenchmarkPointModel,
    ResearchDatasetModel,
    ResearchDrawdownPointModel,
    ResearchEquityPointModel,
    ResearchHoldingModel,
    ResearchMetricModel,
    ResearchRebalanceModel,
    ResearchRollingMetricModel,
    ResearchRunModel,
    ResearchTradeModel,
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


async def test_formal_run_api_cannot_append_to_read_only_archive(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _seed_dataset()
    monkeypatch.setenv("GIT_COMMIT", "c" * 40)
    for period_kind in ("DEVELOPMENT", "VALIDATION", "OUT_OF_SAMPLE"):
        response = await client.post(
            "/api/research/runs",
            json={
                "dataset_id": "cn-a-fixture-v1",
                "strategy_id": STRATEGY_ID,
                "benchmark_id": "CSI300",
                "period_kind": period_kind,
            },
        )
        assert response.status_code == 409
        assert response.json()["code"] == "FORMAL_RESEARCH_READ_ONLY"
    async with SessionFactory() as session:
        assert await session.scalar(select(func.count()).select_from(ResearchRunModel)) == 0


async def test_formal_archive_rejects_invalid_strategy_and_oos_writes(client: AsyncClient) -> None:
    await _seed_dataset()
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
    assert invalid.status_code == oos.status_code == 409
    assert invalid.json()["code"] == oos.json()["code"] == "FORMAL_RESEARCH_READ_ONLY"


async def _seed_run() -> UUID:
    await _seed_dataset()
    run_id = UUID("11111111-1111-4111-8111-111111111111")
    async with SessionFactory() as session:
        session.add(
            ResearchRunModel(
                id=run_id,
                status="SUCCEEDED",
                period_kind="VALIDATION",
                git_commit="c" * 40,
                dataset_id="cn-a-fixture-v1",
                dataset_checksum="a" * 64,
                provider="BaoStock",
                provider_version="0.9.3",
                market_rule_version="cn-a-rules-v1",
                strategy_id=STRATEGY_ID,
                strategy_config_hash="b" * 64,
                strategy_config={},
                transaction_cost_config={},
                benchmark_id="CSI300",
                benchmark_version="cn-a-fixture-v1:CSI300",
                temporal_split_hash="d" * 64,
                temporal_split={},
                random_seed=0,
                created_at=datetime(2026, 9, 7, tzinfo=UTC),
                diagnostics={
                    "accounting_policies": {
                        "partial_surrender_policy": (
                            "CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1"
                        ),
                        "zero_whole_share_policy": (
                            "WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"
                        ),
                    }
                },
            )
        )
        await session.flush()
        await session.commit()
    return run_id


async def test_existing_formal_run_lineage_is_readable_without_api_write(
    client: AsyncClient,
) -> None:
    run_id = await _seed_run()
    async with SessionFactory() as session:
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

    run = await client.get(f"/api/research/runs/{run_id}")
    assert run.status_code == 200
    assert run.json()["git_commit"] == "c" * 40
    assert run.json()["dataset_checksum"] == "a" * 64
    assert run.json()["random_seed"] == 0
    assert run.json()["diagnostics"]["accounting_policies"]["partial_surrender_policy"] == (
        "CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1"
    )
    assert run.json()["diagnostics"]["accounting_policies"]["zero_whole_share_policy"] == (
        "WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1"
    )
    metrics = await client.get(f"/api/research/runs/{run_id}/metrics")
    equity = await client.get(f"/api/research/runs/{run_id}/equity")
    assert metrics.json()["items"][0]["value"] == "0.12345678901234567890123456789012345678"
    assert equity.json()["items"][0]["value"] == "100000"
    async with SessionFactory() as session:
        assert await session.scalar(
            select(ResearchRunModel.id).where(ResearchRunModel.id == run_id)
        )


@pytest.fixture
async def dated_run() -> UUID:
    run_id = await _seed_run()
    exact = Decimal("0.12345678901234567890123456789012345678")
    async with SessionFactory() as session:
        session.add(
            ResearchMetricModel(
                run_id=run_id, period_kind="VALIDATION", metric_name="cagr", value=exact
            )
        )
        for sequence in range(202):
            trading_date = date(2017, 1, 1) + timedelta(days=sequence)
            for model in (
                ResearchEquityPointModel,
                ResearchBenchmarkPointModel,
                ResearchDrawdownPointModel,
            ):
                session.add(
                    model(run_id=run_id, sequence=sequence, trading_date=trading_date, value=exact)
                )
            session.add(
                ResearchHoldingModel(
                    run_id=run_id,
                    sequence=sequence,
                    trading_date=trading_date,
                    security_id="SSE:600000",
                    quantity=Decimal("100"),
                    weight=exact,
                    market_value=Decimal("1000"),
                )
            )
            session.add(
                ResearchRebalanceModel(
                    run_id=run_id,
                    sequence=sequence,
                    trading_date=trading_date,
                    turnover=exact,
                    transaction_cost=Decimal("0"),
                )
            )
            session.add(
                ResearchRollingMetricModel(
                    run_id=run_id, trading_date=trading_date, metric_name="sharpe", value=exact
                )
            )
            session.add(
                ResearchTradeModel(
                    run_id=run_id,
                    sequence=sequence,
                    order_id=uuid4(),
                    security_id="SSE:600000",
                    side="BUY",
                    quantity=Decimal("100"),
                    price=exact,
                    transaction_cost=Decimal("0"),
                    timestamp=datetime.combine(trading_date, datetime.min.time(), tzinfo=UTC),
                )
            )
        for sequence, timestamp in enumerate(
            (
                "2017-07-19T15:59:59+00:00",
                "2017-07-19T16:00:00+00:00",
                "2017-07-20T15:59:59+00:00",
                "2017-07-20T16:00:00+00:00",
            ),
            start=202,
        ):
            session.add(
                ResearchTradeModel(
                    run_id=run_id,
                    sequence=sequence,
                    order_id=uuid4(),
                    security_id="SSE:600000",
                    side="BUY",
                    quantity=Decimal("100"),
                    price=exact,
                    transaction_cost=Decimal("0"),
                    timestamp=datetime.fromisoformat(timestamp),
                )
            )
        await session.commit()
    return run_id


@pytest.mark.parametrize(
    "endpoint,value_key",
    (
        ("equity", "value"),
        ("benchmark", "value"),
        ("drawdown", "value"),
        ("holdings", "weight"),
        ("rebalances", "turnover"),
        ("rolling-metrics", "value"),
        ("trades", "price"),
    ),
)
async def test_formal_date_filter_precedes_count_and_paging_and_preserves_metrics(
    client: AsyncClient,
    dated_run: UUID,
    endpoint: str,
    value_key: str,
) -> None:
    path = f"/api/research/runs/{dated_run}/{endpoint}"
    metrics_before = await client.get(f"/api/research/runs/{dated_run}/metrics")
    unfiltered = (await client.get(path)).json()
    assert len(unfiltered["items"]) == unfiltered["limit"] == 200
    assert unfiltered["total"] == (206 if endpoint == "trades" else 202)
    params = {"start_date": "2017-07-20", "end_date": "2017-07-21"}
    filtered = await client.get(path, params=params)
    assert filtered.status_code == 200
    payload = filtered.json()
    assert payload["total"] == len(payload["items"]) == (5 if endpoint == "trades" else 2)
    assert payload["items"][0][value_key] == "0.12345678901234567890123456789012345678"
    if endpoint != "trades":
        assert [item["trading_date"] for item in payload["items"]] == ["2017-07-20", "2017-07-21"]
    page = (await client.get(path, params={**params, "limit": 1, "offset": 1})).json()
    assert page["total"] == payload["total"]
    assert page["items"] == [payload["items"][1]]
    assert (await client.get(path, params={"start_date": "2017-07-22"})).json()["total"] == 0
    assert (await client.get(path, params={"end_date": "2016-12-31"})).json()["total"] == 0
    assert (await client.get(path, params={"start_date": "2017-07-20"})).json() == payload
    assert (await client.get(path, params={"end_date": "2017-07-21"})).json() == unfiltered
    assert (await client.get(path, params={**params, "offset": 200})).json()["items"] == []
    assert (await client.get(path, params={"limit": 201})).status_code == 422
    reversed_dates = await client.get(
        path, params={"start_date": "2017-07-21", "end_date": "2017-07-20"}
    )
    assert reversed_dates.status_code == 422
    assert reversed_dates.json()["code"] == "INVALID_DISPLAY_DATE_RANGE"
    assert (await client.get(path, params={"start_date": "not-a-date"})).status_code == 422
    assert (
        await client.get(f"/api/research/runs/{uuid4()}/{endpoint}", params=params)
    ).status_code == 404
    assert (
        await client.get(f"/api/research/runs/{dated_run}/metrics")
    ).content == metrics_before.content


async def test_formal_trade_dates_use_shanghai_not_utc(
    client: AsyncClient, dated_run: UUID
) -> None:
    response = await client.get(
        f"/api/research/runs/{dated_run}/trades",
        params={"start_date": "2017-07-20", "end_date": "2017-07-20"},
    )
    assert response.status_code == 200
    assert response.json()["total"] == 3
    assert [item["sequence"] for item in response.json()["items"]] == [200, 203, 204]
