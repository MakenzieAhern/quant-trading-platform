import os
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.research import (
    CreateResearchRunRequest,
    DatasetResponse,
    HoldingResponse,
    MarketResponse,
    MetricResponse,
    MonthlyReturnResponse,
    PointResponse,
    RebalanceResponse,
    ResearchPage,
    ResearchRunResponse,
    RollingMetricResponse,
    StrategyResponse,
    TradeResponse,
)
from app.application.backtests.decimal_policy import canonical_decimal
from app.data.catalog.checksums import canonical_sha256
from app.db.models.research import (
    ResearchBenchmarkPointModel,
    ResearchDatasetModel,
    ResearchDrawdownPointModel,
    ResearchEquityPointModel,
    ResearchHoldingModel,
    ResearchMetricModel,
    ResearchMonthlyReturnModel,
    ResearchRebalanceModel,
    ResearchRollingMetricModel,
    ResearchRunModel,
    ResearchTradeModel,
)
from app.db.session import get_session
from app.domain.markets.mergers import MERGER_POLICY, ZERO_WHOLE_SHARE_POLICY
from app.domain.markets.pass_through import PASS_THROUGH_BASIS_POLICY, PASS_THROUGH_POLICY
from app.domain.markets.surrenders import (
    PARTIAL_SURRENDER_BOUNDARY_POLICY,
    PARTIAL_SURRENDER_FRACTION_POLICY,
    PARTIAL_SURRENDER_POLICY,
)
from app.research import INITIAL_SPLIT
from app.research.models import ResearchPeriodKind
from app.strategies.research import (
    STRATEGY_ID,
    STRATEGY_NAME_EN,
    STRATEGY_NAME_ZH,
    ChinaAMomentumLowVolConfig,
)

router = APIRouter(prefix="/research", tags=["research"])
Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0, le=2_147_483_647)]


def _decimal(value: Decimal | None) -> str | None:
    return canonical_decimal(value) if value is not None else None


def _error(request: Request, http_status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "message": message,
            "details": {},
            "request_id": request.headers.get("x-request-id", str(uuid4())),
        },
    )


def _strategy() -> StrategyResponse:
    config = ChinaAMomentumLowVolConfig()
    return StrategyResponse(
        strategy_id=STRATEGY_ID,
        version="1",
        name_en=STRATEGY_NAME_EN,
        name_zh=STRATEGY_NAME_ZH,
        factor_formulas=(
            "MOM_12_1 = adjusted_close[t-21] / adjusted_close[t-252] - 1",
            "TREND_120 = adjusted_close[t] / SMA120[t] - 1",
            "LOW_VOL = -population_std(adjusted_returns[t-19:t])",
        ),
        frozen_configuration=asdict(config),
        configuration_hash=config.configuration_hash,
    )


def _dataset(model: ResearchDatasetModel, *, detail: bool = False) -> DatasetResponse:
    return DatasetResponse(
        dataset_id=model.dataset_id,
        provider=model.provider,
        provider_version=model.provider_version,
        retrieval_timestamp=model.retrieval_timestamp,
        coverage_start=model.coverage_start,
        coverage_end=model.coverage_end,
        security_count=model.security_count,
        canonical_sha256=model.canonical_sha256,
        rule_version=model.rule_version,
        adjustment_method=model.adjustment_method,
        readiness_status=model.readiness_status,
        frozen=model.frozen,
        manifest=model.manifest if detail else None,
    )


def _run(model: ResearchRunModel) -> ResearchRunResponse:
    return ResearchRunResponse(
        run_id=model.id,
        status=model.status,
        period_kind=ResearchPeriodKind(model.period_kind),
        git_commit=model.git_commit,
        dataset_id=model.dataset_id,
        dataset_checksum=model.dataset_checksum,
        provider=model.provider,
        provider_version=model.provider_version,
        market_rule_version=model.market_rule_version,
        strategy_id=model.strategy_id,
        strategy_config_hash=model.strategy_config_hash,
        transaction_cost_config=model.transaction_cost_config,
        benchmark_id=model.benchmark_id,
        benchmark_version=model.benchmark_version,
        temporal_split_hash=model.temporal_split_hash,
        random_seed=model.random_seed,
        created_at=model.created_at,
        started_at=model.started_at,
        completed_at=model.completed_at,
        failure_code=model.failure_code,
        diagnostics=model.diagnostics,
    )


async def _page(
    session: AsyncSession, statement: Select[Any], limit: int, offset: int
) -> tuple[list[Any], int]:
    total = await session.scalar(select(func.count()).select_from(statement.subquery()))
    items = list((await session.scalars(statement.limit(limit).offset(offset))).all())
    return items, int(total or 0)


async def _require_run(
    request: Request, session: AsyncSession, run_id: UUID
) -> ResearchRunModel | JSONResponse:
    model = await session.get(ResearchRunModel, run_id)
    if model is None:
        return _error(
            request, status.HTTP_404_NOT_FOUND, "RESEARCH_RUN_NOT_FOUND", "Research run not found"
        )
    return model


@router.get("/markets", response_model=list[MarketResponse])
async def markets() -> list[MarketResponse]:
    return [
        MarketResponse(
            market_id="CN_A",
            exchanges=("SSE", "SZSE"),
            boards=("SSE_MAIN", "SSE_STAR", "SZSE_MAIN", "SZSE_CHINEXT"),
        )
    ]


@router.get("/datasets", response_model=ResearchPage[DatasetResponse])
async def datasets(
    session: Annotated[AsyncSession, Depends(get_session)], limit: Limit = 50, offset: Offset = 0
) -> ResearchPage[DatasetResponse]:
    items, total = await _page(
        session,
        select(ResearchDatasetModel).order_by(ResearchDatasetModel.retrieval_timestamp.desc()),
        limit,
        offset,
    )
    return ResearchPage(
        items=[_dataset(item) for item in items], limit=limit, offset=offset, total=total
    )


@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def dataset_detail(
    dataset_id: str, request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> DatasetResponse | JSONResponse:
    model = await session.get(ResearchDatasetModel, dataset_id)
    if model is None:
        return _error(request, 404, "RESEARCH_DATASET_NOT_FOUND", "Research dataset not found")
    return _dataset(model, detail=True)


@router.get("/strategies", response_model=list[StrategyResponse])
async def strategies() -> list[StrategyResponse]:
    return [_strategy()]


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def strategy_detail(strategy_id: str, request: Request) -> StrategyResponse | JSONResponse:
    if strategy_id != STRATEGY_ID:
        return _error(request, 404, "RESEARCH_STRATEGY_NOT_FOUND", "Research strategy not found")
    return _strategy()


@router.post("/runs", response_model=ResearchRunResponse, status_code=201)
async def create_run(
    payload: CreateResearchRunRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResearchRunResponse | JSONResponse:
    if payload.strategy_id != STRATEGY_ID:
        return _error(request, 422, "RESEARCH_STRATEGY_NOT_FOUND", "Research strategy not found")
    if (
        payload.dataset_id.startswith("cn-a-pilot-")
        or payload.period_kind is ResearchPeriodKind.PILOT_SMOKE
    ):
        return _error(
            request,
            409,
            "PILOT_NOT_FORMAL_RESEARCH",
            "Use the approved engineering-smoke command; formal studies remain locked",
        )
    if payload.benchmark_id not in {"CSI300", "CSI500", "ELIGIBLE_EQUAL_WEIGHT"}:
        return _error(request, 422, "BENCHMARK_DATA_MISSING", "Benchmark is not registered")
    dataset = await session.get(ResearchDatasetModel, payload.dataset_id)
    if dataset is None:
        return _error(request, 404, "RESEARCH_DATASET_NOT_FOUND", "Research dataset not found")
    if not dataset.frozen or dataset.readiness_status != "PASSED":
        return _error(
            request, 409, "RESEARCH_DATASET_NOT_READY", "Research dataset is not frozen and ready"
        )
    if payload.period_kind is ResearchPeriodKind.OUT_OF_SAMPLE:
        return _error(
            request,
            409,
            "OOS_APPROVAL_REQUIRED",
            "Official out-of-sample execution requires operator approval",
        )
    git_commit = os.getenv("GIT_COMMIT", "")
    if len(git_commit) != 40 or any(
        character not in "0123456789abcdef" for character in git_commit
    ):
        return _error(
            request, 409, "REPRODUCIBILITY_METADATA_MISSING", "Build Git commit is not pinned"
        )
    config = ChinaAMomentumLowVolConfig()
    split = {
        "development": {
            "start": INITIAL_SPLIT.development.start.isoformat(),
            "end": INITIAL_SPLIT.development.end.isoformat(),
        },
        "validation": {
            "start": INITIAL_SPLIT.validation.start.isoformat(),
            "end": INITIAL_SPLIT.validation.end.isoformat(),
        },
        "out_of_sample": {
            "start": INITIAL_SPLIT.out_of_sample.start.isoformat(),
            "end": INITIAL_SPLIT.out_of_sample.end.isoformat(),
        },
    }
    now = datetime_now_utc()
    model = ResearchRunModel(
        id=uuid4(),
        status="CREATED",
        period_kind=payload.period_kind.value,
        git_commit=git_commit,
        dataset_id=dataset.dataset_id,
        dataset_checksum=dataset.canonical_sha256,
        provider=dataset.provider,
        provider_version=dataset.provider_version,
        market_rule_version=dataset.rule_version,
        strategy_id=STRATEGY_ID,
        strategy_config_hash=config.configuration_hash,
        strategy_config=asdict(config),
        transaction_cost_config={"schedule": "effective-dated-cn-a-v1"},
        benchmark_id=payload.benchmark_id,
        benchmark_version=f"{dataset.dataset_id}:{payload.benchmark_id}",
        temporal_split_hash=canonical_sha256(split),
        temporal_split=split,
        random_seed=0,
        created_at=now,
        diagnostics={
            "accounting_policies": {
                "pass_through_policy": PASS_THROUGH_POLICY,
                "pass_through_basis_policy": PASS_THROUGH_BASIS_POLICY,
                "merger_policy": MERGER_POLICY,
                "zero_whole_share_policy": ZERO_WHOLE_SHARE_POLICY,
                "partial_surrender_policy": PARTIAL_SURRENDER_POLICY,
                "partial_surrender_fraction_policy": PARTIAL_SURRENDER_FRACTION_POLICY,
                "partial_surrender_boundary_policy": PARTIAL_SURRENDER_BOUNDARY_POLICY,
            }
        },
    )
    session.add(model)
    await session.commit()
    return _run(model)


def datetime_now_utc() -> datetime:
    return datetime.now(UTC)


@router.get("/runs", response_model=ResearchPage[ResearchRunResponse])
async def runs(
    session: Annotated[AsyncSession, Depends(get_session)], limit: Limit = 50, offset: Offset = 0
) -> ResearchPage[ResearchRunResponse]:
    items, total = await _page(
        session,
        select(ResearchRunModel).order_by(ResearchRunModel.created_at.desc()),
        limit,
        offset,
    )
    return ResearchPage(
        items=[_run(item) for item in items], limit=limit, offset=offset, total=total
    )


@router.get("/runs/{run_id}", response_model=ResearchRunResponse)
async def run_detail(
    run_id: UUID, request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> ResearchRunResponse | JSONResponse:
    model = await _require_run(request, session, run_id)
    return model if isinstance(model, JSONResponse) else _run(model)


async def _run_rows(
    request: Request,
    session: AsyncSession,
    run_id: UUID,
    model: Any,
    order_columns: tuple[Any, ...],
    limit: int,
    offset: int,
) -> tuple[list[Any], int] | JSONResponse:
    required = await _require_run(request, session, run_id)
    if isinstance(required, JSONResponse):
        return required
    statement = select(model).where(model.run_id == run_id).order_by(*order_columns)
    return await _page(session, statement, limit, offset)


@router.get("/runs/{run_id}/metrics", response_model=ResearchPage[MetricResponse])
async def metrics(
    run_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Limit = 200,
    offset: Offset = 0,
) -> ResearchPage[MetricResponse] | JSONResponse:
    result = await _run_rows(
        request,
        session,
        run_id,
        ResearchMetricModel,
        (ResearchMetricModel.period_kind, ResearchMetricModel.metric_name),
        limit,
        offset,
    )
    if isinstance(result, JSONResponse):
        return result
    items, total = result
    return ResearchPage(
        items=[
            MetricResponse(
                period_kind=ResearchPeriodKind(item.period_kind),
                metric_name=item.metric_name,
                value=_decimal(item.value),
            )
            for item in items
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


def _point_route(model: type[Any], path: str) -> None:
    async def endpoint(
        run_id: UUID,
        request: Request,
        session: Annotated[AsyncSession, Depends(get_session)],
        limit: Limit = 200,
        offset: Offset = 0,
    ) -> ResearchPage[PointResponse] | JSONResponse:
        result = await _run_rows(request, session, run_id, model, (model.sequence,), limit, offset)
        if isinstance(result, JSONResponse):
            return result
        items, total = result
        return ResearchPage(
            items=[
                PointResponse(
                    sequence=item.sequence,
                    trading_date=item.trading_date,
                    value=_decimal(item.value) or "0",
                )
                for item in items
            ],
            limit=limit,
            offset=offset,
            total=total,
        )

    router.add_api_route(
        path, endpoint, methods=["GET"], response_model=ResearchPage[PointResponse]
    )


_point_route(ResearchEquityPointModel, "/runs/{run_id}/equity")
_point_route(ResearchBenchmarkPointModel, "/runs/{run_id}/benchmark")
_point_route(ResearchDrawdownPointModel, "/runs/{run_id}/drawdown")


@router.get("/runs/{run_id}/monthly-returns", response_model=ResearchPage[MonthlyReturnResponse])
async def monthly_returns(
    run_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Limit = 200,
    offset: Offset = 0,
) -> ResearchPage[MonthlyReturnResponse] | JSONResponse:
    result = await _run_rows(
        request,
        session,
        run_id,
        ResearchMonthlyReturnModel,
        (ResearchMonthlyReturnModel.month,),
        limit,
        offset,
    )
    if isinstance(result, JSONResponse):
        return result
    items, total = result
    return ResearchPage(
        items=[
            MonthlyReturnResponse(month=item.month, value=_decimal(item.value)) for item in items
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/runs/{run_id}/rolling-metrics", response_model=ResearchPage[RollingMetricResponse])
async def rolling_metrics(
    run_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Limit = 200,
    offset: Offset = 0,
) -> ResearchPage[RollingMetricResponse] | JSONResponse:
    result = await _run_rows(
        request,
        session,
        run_id,
        ResearchRollingMetricModel,
        (ResearchRollingMetricModel.trading_date, ResearchRollingMetricModel.metric_name),
        limit,
        offset,
    )
    if isinstance(result, JSONResponse):
        return result
    items, total = result
    return ResearchPage(
        items=[
            RollingMetricResponse(
                trading_date=item.trading_date,
                metric_name=item.metric_name,
                value=_decimal(item.value),
            )
            for item in items
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/runs/{run_id}/rebalances", response_model=ResearchPage[RebalanceResponse])
async def rebalances(
    run_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Limit = 200,
    offset: Offset = 0,
) -> ResearchPage[RebalanceResponse] | JSONResponse:
    result = await _run_rows(
        request,
        session,
        run_id,
        ResearchRebalanceModel,
        (ResearchRebalanceModel.sequence,),
        limit,
        offset,
    )
    if isinstance(result, JSONResponse):
        return result
    items, total = result
    return ResearchPage(
        items=[
            RebalanceResponse(
                sequence=item.sequence,
                trading_date=item.trading_date,
                turnover=_decimal(item.turnover) or "0",
                transaction_cost=_decimal(item.transaction_cost) or "0",
            )
            for item in items
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/runs/{run_id}/holdings", response_model=ResearchPage[HoldingResponse])
async def holdings(
    run_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Limit = 200,
    offset: Offset = 0,
) -> ResearchPage[HoldingResponse] | JSONResponse:
    result = await _run_rows(
        request,
        session,
        run_id,
        ResearchHoldingModel,
        (ResearchHoldingModel.sequence,),
        limit,
        offset,
    )
    if isinstance(result, JSONResponse):
        return result
    items, total = result
    return ResearchPage(
        items=[
            HoldingResponse(
                sequence=item.sequence,
                trading_date=item.trading_date,
                security_id=item.security_id,
                quantity=_decimal(item.quantity) or "0",
                weight=_decimal(item.weight) or "0",
                market_value=_decimal(item.market_value) or "0",
            )
            for item in items
        ],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/runs/{run_id}/trades", response_model=ResearchPage[TradeResponse])
async def trades(
    run_id: UUID,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: Limit = 200,
    offset: Offset = 0,
) -> ResearchPage[TradeResponse] | JSONResponse:
    result = await _run_rows(
        request, session, run_id, ResearchTradeModel, (ResearchTradeModel.sequence,), limit, offset
    )
    if isinstance(result, JSONResponse):
        return result
    items, total = result
    return ResearchPage(
        items=[
            TradeResponse(
                sequence=item.sequence,
                order_id=item.order_id,
                security_id=item.security_id,
                side=item.side,
                quantity=_decimal(item.quantity) or "0",
                price=_decimal(item.price) or "0",
                transaction_cost=_decimal(item.transaction_cost) or "0",
                timestamp=item.timestamp,
            )
            for item in items
        ],
        limit=limit,
        offset=offset,
        total=total,
    )
