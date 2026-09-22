import asyncio
from collections.abc import AsyncIterator, Iterable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError

from app.application.backtests import (
    BacktestApplicationService,
    BacktestRun,
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
    BacktestFillModel,
    BacktestMetricsModel,
    BacktestOrderModel,
    BacktestOrderProposalModel,
    BacktestPortfolioSnapshotModel,
    BacktestRiskDecisionModel,
    BacktestRiskReservationModel,
    BacktestRunModel,
    BacktestSignalModel,
)
from app.db.repositories import SQLAlchemyBacktestRepository
from app.db.session import SessionFactory
from app.domain.risk import RiskConfig
from app.domain.trading import OrderStatus
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


@pytest.mark.parametrize(
    "conversion",
    [
        "demerger",
        "merger",
        "zero_whole_merger",
        "partial_surrender",
        "ceil_surrender_zero",
        "ceil_surrender_odd",
        "pass_through",
        "consolidation",
    ],
)
async def test_mandatory_conversion_survives_repository_roundtrip(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    conversion: str,
) -> None:
    from datetime import date

    from tests.test_demerger_accounting import at, event, funded

    if conversion == "demerger":
        portfolio, _ = funded("137")
        portfolio.recognize_demerger(event(), date(2010, 2, 26), at("2010-02-26"))
        pending = portfolio.snapshot_at(at("2010-02-26"))
        portfolio.activate_demergers(
            date(2010, 3, 19),
            {"601188.SSE": Decimal(5), "601518.SSE": Decimal(4)},
            at("2010-03-19"),
        )
        active = portfolio.snapshot_at(at("2010-03-19"))
        expected_basis = Decimal(411)
    elif conversion == "merger":
        from tests.test_merger_accounting import event as merger_event
        from tests.test_merger_accounting import funded as merger_funded

        portfolio, _ = merger_funded()
        portfolio.recognize_merger(merger_event(), date(2015, 12, 30), at("2015-12-30"))
        pending = portfolio.snapshot_at(at("2015-12-30"))
        portfolio.activate_mergers(
            date(2015, 12, 30), {"001979.SZSE": Decimal(25)}, at("2015-12-30")
        )
        active = portfolio.snapshot_at(at("2015-12-30"))
        expected_basis = Decimal(3000)
    elif conversion == "zero_whole_merger":
        from tests.test_zero_whole_merger import event as zero_event
        from tests.test_zero_whole_merger import funded as zero_funded

        portfolio, _ = zero_funded(1)
        portfolio.recognize_merger(zero_event(), date(2017, 2, 17), at("2017-02-17"))
        pending = portfolio.snapshot_at(at("2017-02-17"))
        portfolio.activate_mergers(date(2017, 2, 27), {"600019.SSE": Decimal(6)}, at("2017-02-27"))
        active = portfolio.snapshot_at(at("2017-02-27"))
        expected_basis = Decimal(0)
    elif conversion == "consolidation":
        from tests.test_consolidation_accounting import event as consolidation_event
        from tests.test_consolidation_accounting import funded as consolidation_funded

        portfolio, _ = consolidation_funded()
        portfolio.apply_consolidation(
            consolidation_event(),
            at("2014-06-25"),
            holder_class=consolidation_event().affected_holder_class,
        )
        pending = portfolio.snapshot_at(at("2014-06-25"))
        active = portfolio.snapshot_at(at("2014-06-26"))
        expected_basis = Decimal(1000)
    elif conversion == "pass_through":
        from tests.test_pass_through_accounting import event as pass_event
        from tests.test_pass_through_accounting import funded as pass_funded

        portfolio, _ = pass_funded()
        portfolio.apply_pass_through(pass_event(), at("2012-07-31"))
        pending = portfolio.snapshot_at(at("2012-07-31"))
        active = portfolio.snapshot_at(at("2012-08-01"))
        expected_basis = Decimal(1000)
    else:
        from tests.test_partial_share_surrender import action as surrender_event
        from tests.test_partial_share_surrender import funded as surrender_funded

        portfolio, _ = surrender_funded()
        e = surrender_event()
        if conversion.startswith("ceil_surrender"):
            from tests.test_partial_share_surrender import approved_convention

            portfolio, _ = surrender_funded("1" if conversion.endswith("zero") else "6")
            e = approved_convention().model_copy(
                update={"research_effective_date": date(2024, 1, 4)}
            )
        portfolio.apply_partial_surrender(e, at("2024-01-04"), holder_class=e.affected_holder_class)
        pending = portfolio.snapshot_at(at("2024-01-04"))
        active = portfolio.snapshot_at(at("2024-01-05"))
        expected_basis = Decimal(800)
        if conversion.startswith("ceil_surrender"):
            expected_basis = Decimal(0 if conversion.endswith("zero") else 40)
    baseline = BacktestEngine(
        CSVDataProvider(FIXTURES),
        (MovingAverageCrossoverStrategy("fixture", "AAPL", 2, 3),),
        BacktestConfig(initial_cash=Decimal(10000), default_order_quantity=Decimal(10)),
    ).run("AAPL")
    # Stub only the test runner result to exercise the production persistence path.
    expected = replace(baseline, portfolio_snapshots=(pending, active))
    monkeypatch.setattr(BacktestEngine, "run", lambda *args, **kwargs: expected)
    response = await client.post("/api/backtests", json=request_body())
    assert response.status_code == 201, response.text
    async with SessionFactory() as session:
        snapshots = await SQLAlchemyBacktestRepository(session).list_snapshots(
            UUID(response.json()["run_id"]), 100, 0
        )
    assert snapshots.items == (pending, active)
    assert sum(p.aggregate_cost_basis for p in snapshots.items[1].positions) == expected_basis


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


@pytest.mark.parametrize(
    "value",
    [
        "0.000000000000000001",
        "999999999999999999.123456789012345678",
    ],
)
async def test_reference_decimals_round_trip_through_postgresql_and_api(
    client: AsyncClient, value: str
) -> None:
    payload = request_body(value)
    payload["strategy"] = {
        "type": "moving_average_crossover",
        "parameters": {"short_period": 4, "long_period": 5},
    }
    response = await client.post("/api/backtests", json=payload)
    assert response.status_code == 201, response.text
    detail = await client.get(f"/api/backtests/{response.json()['run_id']}")
    result = await client.get(f"/api/backtests/{response.json()['run_id']}/result")
    assert detail.json()["initial_cash"] == value
    assert result.json()["metrics"]["initial_equity"] == value


@pytest.mark.parametrize(
    "value",
    [
        "10000000000000000000000000000000000000000",
        "0.000000000000000000000000000000000000001",
    ],
)
async def test_decimal_overflow_and_excess_scale_are_rejected_without_run(
    client: AsyncClient, value: str
) -> None:
    response = await client.post("/api/backtests", json=request_body(value))
    assert response.status_code == 422
    assert "maximum" in response.text
    assert (await client.get("/api/backtests")).json()["total"] == 0


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


async def test_concurrent_identical_idempotency_key_executes_once(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.application.backtests import service as service_module

    calls = 0
    engine_type = service_module.BacktestEngine

    def counting_engine(*args: object, **kwargs: object) -> BacktestEngine:
        nonlocal calls
        calls += 1
        return engine_type(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(service_module, "BacktestEngine", counting_engine)
    headers = {"Idempotency-Key": "phase7-concurrent-same-key"}
    first, second = await asyncio.gather(
        client.post("/api/backtests", json=request_body(), headers=headers),
        client.post("/api/backtests", json=request_body(), headers=headers),
    )
    assert first.status_code == second.status_code == 201
    assert first.json()["run_id"] == second.json()["run_id"]
    assert first.json()["status"] == second.json()["status"] == "SUCCEEDED"
    assert calls == 1
    async with SessionFactory() as session:
        count = await session.scalar(
            select(func.count())
            .select_from(BacktestRunModel)
            .where(BacktestRunModel.client_request_id == "phase7-concurrent-same-key")
        )
    assert count == 1


async def test_repository_reloads_complete_final_bar_reservation_result(
    client: AsyncClient,
) -> None:
    expected = BacktestEngine(
        CSVDataProvider(FIXTURES),
        (MovingAverageCrossoverStrategy("moving_average_crossover:AAPL", "AAPL", 3, 5),),
        BacktestConfig(initial_cash=Decimal("100000"), default_order_quantity=Decimal("10")),
    ).run("AAPL")
    assert expected.active_risk_reservations
    payload = request_body()
    payload["strategy"] = {
        "type": "moving_average_crossover",
        "parameters": {"short_period": 3, "long_period": 5},
    }
    response = await client.post("/api/backtests", json=payload)
    assert response.status_code == 201
    run_id = UUID(response.json()["run_id"])

    async with SessionFactory() as session:
        repository = SQLAlchemyBacktestRepository(session)
        assert (await repository.list_signals(run_id, 200, 0)).items == expected.signals
        assert (await repository.list_proposals(run_id, 200, 0)).items == (expected.order_proposals)
        assert (await repository.list_risk_decisions(run_id, 200, 0)).items == (
            expected.risk_decisions
        )
        assert (await repository.list_orders(run_id, 200, 0)).items == expected.orders
        assert (await repository.list_fills(run_id, 200, 0)).items == expected.fills
        assert (await repository.list_snapshots(run_id, 200, 0)).items == (
            expected.portfolio_snapshots
        )
        assert (await repository.list_reservations(run_id, 200, 0)).items == (
            expected.active_risk_reservations
        )
        summary = await repository.get_result_summary(run_id)
    assert summary is not None
    assert summary.metrics == expected.performance_metrics
    assert summary.reservation_count == len(expected.active_risk_reservations)
    assert summary.fill_count == 0


async def test_api_counts_and_utc_timestamps_match_postgresql(client: AsyncClient) -> None:
    response = await client.post("/api/backtests", json=request_body())
    assert response.status_code == 201
    run_id = UUID(response.json()["run_id"])
    detail = (await client.get(f"/api/backtests/{run_id}")).json()
    result = (await client.get(f"/api/backtests/{run_id}/result")).json()
    assert detail["status"] == result["status"] == "SUCCEEDED"
    assert detail["metrics"] == result["metrics"]

    model_counts = {
        "signal_count": BacktestSignalModel,
        "proposal_count": BacktestOrderProposalModel,
        "risk_decision_count": BacktestRiskDecisionModel,
        "order_count": BacktestOrderModel,
        "fill_count": BacktestFillModel,
        "snapshot_count": BacktestPortfolioSnapshotModel,
        "reservation_count": BacktestRiskReservationModel,
    }
    async with SessionFactory() as session:
        run = await session.get(BacktestRunModel, run_id)
        assert run is not None
        for api_field, model in model_counts.items():
            count = await session.scalar(
                select(func.count()).select_from(model).where(model.run_id == run_id)
            )
            assert result[api_field] == count

        timestamp_values = [run.created_at, run.started_at, run.completed_at]
        timestamp_columns = (
            (BacktestSignalModel, BacktestSignalModel.timestamp),
            (BacktestOrderProposalModel, BacktestOrderProposalModel.signal_timestamp),
            (BacktestRiskDecisionModel, BacktestRiskDecisionModel.timestamp),
            (BacktestOrderModel, BacktestOrderModel.created_at),
            (BacktestFillModel, BacktestFillModel.timestamp),
            (BacktestPortfolioSnapshotModel, BacktestPortfolioSnapshotModel.timestamp),
        )
        for model, column in timestamp_columns:
            timestamp_values.extend(
                (await session.scalars(select(column).where(model.run_id == run_id))).all()
            )

    assert all(
        value is not None and value.tzinfo is not None and value.utcoffset() == timedelta(0)
        for value in timestamp_values
    )
    for field in ("created_at", "started_at", "completed_at"):
        value = datetime.fromisoformat(detail[field].replace("Z", "+00:00"))
        assert value.utcoffset() == timedelta(0)


async def test_risk_rejection_is_persisted_without_order(client: AsyncClient) -> None:
    payload = request_body()
    payload["risk"] = {"max_order_notional": "1"}
    response = await client.post("/api/backtests", json=payload)
    assert response.status_code == 201
    run_id = UUID(response.json()["run_id"])
    decisions = await client.get(f"/api/backtests/{run_id}/risk-decisions")
    orders = await client.get(f"/api/backtests/{run_id}/orders")
    result = await client.get(f"/api/backtests/{run_id}/result")
    assert decisions.json()["total"] == 1
    assert decisions.json()["items"][0]["approved"] is False
    assert decisions.json()["items"][0]["reason_code"] == "ORDER_NOTIONAL_LIMIT"
    assert orders.json()["total"] == 0
    assert result.json()["proposal_count"] == 1
    assert result.json()["risk_rejection_count"] == 1
    assert result.json()["reservation_count"] == 0


async def test_list_and_child_pagination_is_stable_and_bounded(
    client: AsyncClient,
) -> None:
    run_ids = []
    for cash in ("100000", "100001", "100002"):
        response = await client.post("/api/backtests", json=request_body(cash))
        run_ids.append(response.json()["run_id"])
    first = await client.get("/api/backtests?limit=1&offset=0")
    second = await client.get("/api/backtests?limit=1&offset=1")
    repeated = await client.get("/api/backtests?limit=1&offset=0")
    assert first.json() == repeated.json()
    assert first.json()["items"][0]["run_id"] != second.json()["items"][0]["run_id"]
    assert first.json()["total"] == 3
    assert (await client.get("/api/backtests?limit=200")).status_code == 200
    for query in ("limit=0", "limit=201", "offset=-1"):
        assert (await client.get(f"/api/backtests?{query}")).status_code == 422

    run_id = run_ids[0]
    complete = await client.get(f"/api/backtests/{run_id}/equity?limit=200")
    page_one = await client.get(f"/api/backtests/{run_id}/equity?limit=3&offset=0")
    page_two = await client.get(f"/api/backtests/{run_id}/equity?limit=3&offset=3")
    assert page_one.json()["items"] + page_two.json()["items"] == complete.json()["items"]


async def test_all_run_endpoints_return_consistent_unknown_contract(
    client: AsyncClient,
) -> None:
    missing = uuid4()
    for suffix in (
        "",
        "/result",
        "/signals",
        "/risk-decisions",
        "/orders",
        "/fills",
        "/equity",
    ):
        response = await client.get(f"/api/backtests/{missing}{suffix}")
        assert response.status_code == 404
        assert response.json()["detail"] == "backtest run not found"
    assert (await client.get("/api/backtests/not-a-uuid")).status_code == 422


async def test_dataset_and_strategy_attack_strings_are_rejected(
    client: AsyncClient,
) -> None:
    for dataset_id in (
        "../../etc/passwd",
        "/etc/passwd",
        "C:\\Windows\\system.ini",
        "\\\\server\\share\\AAPL.csv",
        "https://example.invalid/AAPL.csv",
        "%2e%2e%2fetc%2fpasswd",
    ):
        response = await client.post(
            "/api/backtests", json={**request_body(), "dataset_id": dataset_id}
        )
        assert response.status_code == 404
        assert dataset_id not in response.text
    for strategy_type in (
        "module.ClassName",
        "../../strategy.py",
        "__import__",
        "eval('x')",
    ):
        payload = request_body()
        payload["strategy"] = {"type": strategy_type, "parameters": {}}
        response = await client.post("/api/backtests", json=payload)
        assert response.status_code == 422
        assert "Traceback" not in response.text


class FailingProvider:
    def get_historical_bars(self, *_args: object, **_kwargs: object) -> object:
        raise RuntimeError("deliberate test failure with private details")


class FailingDatasetRegistry(DatasetRegistry):
    def __init__(self) -> None:
        super().__init__(())

    def resolve(self, dataset_id: str, symbol: str) -> MarketDataProvider:
        return cast(MarketDataProvider, FailingProvider())


async def test_failed_run_is_safe_and_has_no_partial_result(client: AsyncClient) -> None:
    successful = await client.post("/api/backtests", json=request_body())
    assert successful.status_code == 201
    successful_id = successful.json()["run_id"]
    successful_result = (await client.get(f"/api/backtests/{successful_id}/result")).json()
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
    result = await client.get(f"/api/backtests/{failure.value.run_id}/result")
    assert result.status_code == 409
    assert result.json()["detail"] == "backtest result is not available"
    assert (await client.get(f"/api/backtests/{successful_id}/result")).json() == (
        successful_result
    )


class DeliberatelyCorruptingRepository(SQLAlchemyBacktestRepository):
    async def _add_result(self, run_id: UUID, result: BacktestResult) -> None:
        await super()._add_result(run_id, result)
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


def _two_strategy_result() -> BacktestResult:
    return BacktestEngine(
        CSVDataProvider(FIXTURES),
        (
            MovingAverageCrossoverStrategy("ma-filled", "AAPL", 2, 3),
            MovingAverageCrossoverStrategy("ma-final", "AAPL", 3, 5),
        ),
        BacktestConfig(initial_cash=Decimal("100000"), default_order_quantity=Decimal("10")),
    ).run("AAPL")


def _new_run() -> BacktestRun:
    return BacktestRun(
        id=uuid4(),
        status=BacktestRunStatus.CREATED,
        strategy_id="review-test",
        strategy_type="moving_average_crossover",
        strategy_parameters={"short_period": 2, "long_period": 3},
        symbol="AAPL",
        dataset_id="AAPL_fixture",
        created_at=datetime.now(UTC),
        started_at=None,
        completed_at=None,
        initial_cash=Decimal("100000"),
        default_order_quantity=Decimal("10"),
        risk={
            "max_order_notional": None,
            "max_position_quantity": None,
            "max_symbol_exposure": None,
            "max_gross_exposure": None,
            "max_leverage": None,
            "enforce_buying_power": False,
            "max_drawdown": None,
        },
        start=None,
        end=None,
        error_message=None,
        client_request_id=None,
        request_hash=None,
    )


@pytest.mark.parametrize(
    "target_model",
    [
        BacktestSignalModel,
        BacktestOrderProposalModel,
        BacktestRiskDecisionModel,
        BacktestOrderModel,
        BacktestFillModel,
        BacktestPortfolioSnapshotModel,
        BacktestMetricsModel,
        BacktestRiskReservationModel,
    ],
)
async def test_every_result_stage_rolls_back_as_one_transaction(
    target_model: type[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    result = _two_strategy_result()
    assert result.fills and result.active_risk_reservations
    async with SessionFactory() as session:
        repository = SQLAlchemyBacktestRepository(session)
        run = await repository.create(_new_run())
        await repository.transition(
            run.id,
            BacktestRunStatus.CREATED,
            BacktestRunStatus.RUNNING,
            datetime.now(UTC),
        )
        original_add = session.add
        original_add_all = session.add_all

        def failing_add(instance: object) -> None:
            original_add(instance)
            if isinstance(instance, target_model):
                raise RuntimeError("injected persistence stage failure")

        def failing_add_all(instances: Iterable[object]) -> None:
            values = list(instances)
            original_add_all(values)
            if any(isinstance(instance, target_model) for instance in values):
                raise RuntimeError("injected persistence stage failure")

        monkeypatch.setattr(session, "add", failing_add)
        monkeypatch.setattr(session, "add_all", failing_add_all)
        with pytest.raises(RuntimeError, match="injected persistence stage failure"):
            await repository.persist_success(run.id, result, datetime.now(UTC))
        monkeypatch.setattr(session, "add", original_add)
        monkeypatch.setattr(session, "add_all", original_add_all)
        persisted = await repository.get(run.id)
        assert persisted is not None and persisted.status is BacktestRunStatus.RUNNING
        for model in (
            BacktestSignalModel,
            BacktestOrderProposalModel,
            BacktestRiskDecisionModel,
            BacktestOrderModel,
            BacktestFillModel,
            BacktestPortfolioSnapshotModel,
            BacktestMetricsModel,
            BacktestRiskReservationModel,
        ):
            count = await session.scalar(
                select(func.count()).select_from(model).where(model.run_id == run.id)
            )
            assert count == 0


async def test_database_constraints_prevent_duplicates_orphans_and_audit_deletion(
    client: AsyncClient,
) -> None:
    response = await client.post("/api/backtests", json=request_body())
    run_id = UUID(response.json()["run_id"])
    async with SessionFactory() as session:
        session.add(
            BacktestSignalModel(
                run_id=uuid4(),
                sequence=0,
                strategy_id="orphan",
                symbol="AAPL",
                timestamp=datetime.now(UTC),
                signal_type="BUY",
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        proposal = await session.scalar(
            select(BacktestOrderProposalModel).where(BacktestOrderProposalModel.run_id == run_id)
        )
        assert proposal is not None
        session.add(
            BacktestOrderProposalModel(
                run_id=run_id,
                sequence=999,
                proposal_id=proposal.proposal_id,
                strategy_id=proposal.strategy_id,
                symbol=proposal.symbol,
                side=proposal.side,
                order_type=proposal.order_type,
                quantity=proposal.quantity,
                signal_timestamp=proposal.signal_timestamp,
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()
        await session.rollback()

        with pytest.raises(IntegrityError):
            await session.execute(delete(BacktestRunModel).where(BacktestRunModel.id == run_id))
        await session.rollback()
        assert await session.get(BacktestRunModel, run_id) is not None


async def test_broker_rejection_remains_distinct_from_risk_rejection() -> None:
    source = BacktestEngine(
        CSVDataProvider(FIXTURES),
        (MovingAverageCrossoverStrategy("broker-rejection", "AAPL", 3, 5),),
        BacktestConfig(),
    ).run("AAPL")
    assert len(source.orders) == 1 and source.risk_decisions[0].approved
    rejected = source.orders[0].model_copy(update={"status": OrderStatus.REJECTED})
    result = replace(source, orders=(rejected,), active_risk_reservations=())
    async with SessionFactory() as session:
        repository = SQLAlchemyBacktestRepository(session)
        run = await repository.create(_new_run())
        await repository.transition(
            run.id,
            BacktestRunStatus.CREATED,
            BacktestRunStatus.RUNNING,
            datetime.now(UTC),
        )
        await repository.persist_success(run.id, result, datetime.now(UTC))
        decisions = await repository.list_risk_decisions(run.id, 200, 0)
        orders = await repository.list_orders(run.id, 200, 0)
    assert decisions.items[0].approved is True
    assert orders.items[0].status is OrderStatus.REJECTED


async def test_historical_snapshots_remain_immutable_after_later_run(
    client: AsyncClient,
) -> None:
    first = await client.post("/api/backtests", json=request_body())
    first_id = UUID(first.json()["run_id"])
    async with SessionFactory() as session:
        repository = SQLAlchemyBacktestRepository(session)
        before = (await repository.list_snapshots(first_id, 200, 0)).items
    await client.post("/api/backtests", json=request_body("200000"))
    async with SessionFactory() as session:
        repository = SQLAlchemyBacktestRepository(session)
        after = (await repository.list_snapshots(first_id, 200, 0)).items
    assert before == after
