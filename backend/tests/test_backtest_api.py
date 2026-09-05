import asyncio
from collections.abc import AsyncIterator
from decimal import Decimal
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select, text

from app.application.backtests import (
    BacktestApplicationService,
    BacktestRunStatus,
    CreateBacktestCommand,
    StrategyRegistry,
)
from app.application.backtests.registry import DatasetRegistry
from app.application.backtests.service import BacktestExecutionError
from app.backtest import BacktestConfig, BacktestEngine
from app.backtest.result import BacktestResult
from app.data.providers import CSVDataProvider, MarketDataProvider
from app.db.models.backtest import (
    BacktestMetricsModel,
    BacktestPortfolioSnapshotModel,
    BacktestSignalModel,
)
from app.db.repositories import SQLAlchemyBacktestRepository
from app.db.session import SessionFactory
from app.domain.risk import RiskConfig
from app.main import app
from app.strategies import MovingAverageCrossoverStrategy

FIXTURES = Path(__file__).parents[2] / "data" / "fixtures"


@pytest.fixture(autouse=True)
async def clean_phase7_tables() -> AsyncIterator[None]:
    async with SessionFactory() as session:
        await session.execute(text("TRUNCATE TABLE backtest_runs CASCADE"))
        await session.commit()
    yield
    async with SessionFactory() as session:
        await session.execute(text("TRUNCATE TABLE backtest_runs CASCADE"))
        await session.commit()


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value


def request_body(initial_cash: str = "100000") -> dict[str, object]:
    return {
        "dataset_id": "AAPL_fixture",
        "symbol": "AAPL",
        "strategy": {
            "type": "moving_average_crossover",
            "parameters": {"short_period": 2, "long_period": 3},
        },
        "initial_cash": initial_cash,
        "default_order_quantity": "10",
    }


async def test_api_persists_reference_result_and_exact_decimals(
    client: AsyncClient,
) -> None:
    unusual = "105.052500000000000001"
    expected = BacktestEngine(
        CSVDataProvider(FIXTURES),
        (MovingAverageCrossoverStrategy("moving_average_crossover:AAPL", "AAPL", 2, 3),),
        BacktestConfig(initial_cash=Decimal(unusual), default_order_quantity=Decimal("10")),
    ).run("AAPL")
    response = await client.post("/api/backtests", json=request_body(unusual))
    assert response.status_code == 201, response.text
    created = response.json()
    assert created["status"] == "SUCCEEDED"

    detail = await client.get(f"/api/backtests/{created['run_id']}")
    result = await client.get(f"/api/backtests/{created['run_id']}/result")
    equity = await client.get(f"/api/backtests/{created['run_id']}/equity")
    signals = await client.get(f"/api/backtests/{created['run_id']}/signals")
    orders = await client.get(f"/api/backtests/{created['run_id']}/orders")
    fills = await client.get(f"/api/backtests/{created['run_id']}/fills")
    assert detail.json()["initial_cash"] == unusual
    assert result.status_code == 200
    assert result.json()["metrics"]["initial_equity"] == unusual
    assert equity.status_code == 200
    assert equity.json()["items"][0]["equity"] == unusual
    assert result.json()["snapshot_count"] == equity.json()["total"]
    assert result.json()["signal_count"] == len(expected.signals)
    assert result.json()["proposal_count"] == len(expected.order_proposals)
    assert result.json()["fill_count"] == len(expected.fills)
    assert Decimal(result.json()["metrics"]["final_equity"]) == (
        expected.performance_metrics.final_equity
    )
    assert [Decimal(item["equity"]) for item in equity.json()["items"]] == [
        item.equity for item in expected.equity_curve
    ]
    assert [
        (item["strategy_id"], item["symbol"], item["timestamp"], item["signal_type"])
        for item in signals.json()["items"]
    ] == [
        (
            item.strategy_id,
            item.symbol,
            item.timestamp.isoformat().replace("+00:00", "Z"),
            item.signal_type.value,
        )
        for item in expected.signals
    ]
    assert [
        (
            item["order_id"],
            item["status"],
            Decimal(item["quantity"]),
            item["created_at"],
        )
        for item in orders.json()["items"]
    ] == [
        (
            str(item.id),
            item.status.value,
            item.quantity,
            item.created_at.isoformat().replace("+00:00", "Z"),
        )
        for item in expected.orders
    ]
    assert [
        (
            item["order_id"],
            Decimal(item["quantity"]),
            Decimal(item["price"]),
            Decimal(item["commission"]),
            item["timestamp"],
        )
        for item in fills.json()["items"]
    ] == [
        (
            str(item.order_id),
            item.quantity,
            item.price,
            item.commission,
            item.timestamp.isoformat().replace("+00:00", "Z"),
        )
        for item in expected.fills
    ]
    async with SessionFactory() as session:
        snapshots = (
            await session.scalars(
                select(BacktestPortfolioSnapshotModel)
                .where(BacktestPortfolioSnapshotModel.run_id == UUID(created["run_id"]))
                .order_by(BacktestPortfolioSnapshotModel.sequence)
            )
        ).all()
    assert [
        (
            item.timestamp,
            item.cash,
            item.market_value,
            item.equity,
            item.realized_pnl,
            item.unrealized_pnl,
            item.cumulative_commission,
            item.drawdown,
        )
        for item in snapshots
    ] == [
        (
            item.timestamp,
            item.cash,
            item.market_value,
            item.equity,
            item.realized_pnl,
            item.unrealized_pnl,
            item.cumulative_commission,
            item.drawdown,
        )
        for item in expected.portfolio_snapshots
    ]


async def test_api_pagination_errors_and_idempotency(client: AsyncClient) -> None:
    headers = {"Idempotency-Key": "phase7-retry"}
    first = await client.post("/api/backtests", json=request_body(), headers=headers)
    repeat = await client.post("/api/backtests", json=request_body(), headers=headers)
    assert first.status_code == repeat.status_code == 201
    assert first.json()["run_id"] == repeat.json()["run_id"]

    conflict = await client.post("/api/backtests", json=request_body("200000"), headers=headers)
    assert conflict.status_code == 409
    assert (await client.get("/api/backtests?limit=1&offset=0")).json()["total"] == 1
    assert (await client.get("/api/backtests?limit=201")).status_code == 422
    assert (await client.get(f"/api/backtests/{uuid4()}")).status_code == 404
    assert (
        await client.post(
            "/api/backtests",
            json={**request_body(), "dataset_id": "../../etc/passwd"},
        )
    ).status_code == 404
    invalid_decimal = {**request_body(), "initial_cash": 100000.0}
    assert (await client.post("/api/backtests", json=invalid_decimal)).status_code == 422
    invalid_strategy = {
        **request_body(),
        "strategy": {"type": "os.system", "parameters": {}},
    }
    assert (await client.post("/api/backtests", json=invalid_strategy)).status_code == 422


async def test_independent_concurrent_runs(client: AsyncClient) -> None:
    first, second = await asyncio.gather(
        client.post("/api/backtests", json=request_body()),
        client.post("/api/backtests", json=request_body()),
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["run_id"] != second.json()["run_id"]
    first_result = (await client.get(f"/api/backtests/{first.json()['run_id']}/result")).json()
    second_result = (await client.get(f"/api/backtests/{second.json()['run_id']}/result")).json()
    assert first_result["metrics"] == second_result["metrics"]
    assert first_result["snapshot_count"] == second_result["snapshot_count"]


class FailingProvider:
    def get_historical_bars(self, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("deliberate test failure with private details")


class FailingDatasetRegistry(DatasetRegistry):
    def __init__(self) -> None:
        super().__init__(())

    def resolve(self, dataset_id: str, symbol: str) -> MarketDataProvider:
        return cast(MarketDataProvider, FailingProvider())


async def test_failed_run_is_safe_and_has_no_partial_result() -> None:
    async with SessionFactory() as session:
        repository = SQLAlchemyBacktestRepository(session)
        service = BacktestApplicationService(
            repository, FailingDatasetRegistry(), StrategyRegistry()
        )
        with pytest.raises(BacktestExecutionError) as failure:
            await service.create_and_run(
                CreateBacktestCommand(
                    dataset_id="failing",
                    symbol="AAPL",
                    strategy_type="moving_average_crossover",
                    strategy_parameters={"short_period": 2, "long_period": 3},
                    initial_cash=Decimal("100000"),
                    default_order_quantity=Decimal("10"),
                    risk=RiskConfig(),
                )
            )
        run = await repository.get(failure.value.run_id)
        assert run is not None
        assert run.status is BacktestRunStatus.FAILED
        assert run.error_message == "RuntimeError: backtest execution failed"
        assert "private details" not in run.error_message
        assert await session.get(BacktestMetricsModel, run.id) is None
        signal_count = await session.scalar(
            select(func.count())
            .select_from(BacktestSignalModel)
            .where(BacktestSignalModel.run_id == run.id)
        )
        assert signal_count == 0


class DeliberatelyCorruptingRepository(SQLAlchemyBacktestRepository):
    def _add_result(self, run_id: UUID, result: BacktestResult) -> None:
        super()._add_result(run_id, result)
        signal = result.signals[0]
        self._session.add(
            BacktestSignalModel(
                run_id=run_id,
                sequence=0,
                strategy_id=signal.strategy_id,
                symbol=signal.symbol,
                timestamp=signal.timestamp,
                signal_type=signal.signal_type.value,
            )
        )


async def test_success_result_transaction_rolls_back_atomically() -> None:
    async with SessionFactory() as session:
        repository = DeliberatelyCorruptingRepository(session)
        service = BacktestApplicationService(
            repository, DatasetRegistry.phase7(FIXTURES), StrategyRegistry()
        )
        with pytest.raises(BacktestExecutionError) as failure:
            await service.create_and_run(
                CreateBacktestCommand(
                    dataset_id="AAPL_fixture",
                    symbol="AAPL",
                    strategy_type="moving_average_crossover",
                    strategy_parameters={"short_period": 2, "long_period": 3},
                    initial_cash=Decimal("100000"),
                    default_order_quantity=Decimal("10"),
                    risk=RiskConfig(),
                )
            )
        run = await repository.get(failure.value.run_id)
        assert run is not None and run.status is BacktestRunStatus.FAILED
        assert await session.get(BacktestMetricsModel, run.id) is None
        assert (
            await session.scalar(
                select(func.count())
                .select_from(BacktestSignalModel)
                .where(BacktestSignalModel.run_id == run.id)
            )
            == 0
        )
