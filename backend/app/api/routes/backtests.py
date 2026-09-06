from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas.backtests import (
    CreateBacktestRequest,
    CreateBacktestResponse,
    EquityResponse,
    FillResponse,
    LinkSet,
    MetricsResponse,
    OrderResponse,
    PageResponse,
    ResultResponse,
    RiskDecisionResponse,
    RunResponse,
    SignalResponse,
)
from app.application.backtests import (
    BacktestApplicationService,
    BacktestRun,
    BacktestRunStatus,
    CreateBacktestCommand,
    DatasetRegistry,
    StrategyRegistry,
)
from app.application.backtests.decimal_policy import canonical_decimal
from app.application.backtests.registry import (
    InvalidStrategyParametersError,
    UnknownDatasetError,
    UnknownStrategyError,
)
from app.application.backtests.service import (
    BacktestExecutionError,
    IdempotencyConflictError,
    IdempotencyInProgressError,
)
from app.core.config import get_settings
from app.db.repositories import SQLAlchemyBacktestRepository
from app.db.session import get_session
from app.domain.analytics import PerformanceMetrics
from app.domain.risk import RiskConfig

router = APIRouter(prefix="/backtests", tags=["backtests"])
PaginationLimit = Annotated[int, Query(ge=1, le=200)]
PaginationOffset = Annotated[int, Query(ge=0, le=2147483647)]


def _decimal(value: Decimal | None) -> str | None:
    return canonical_decimal(value) if value is not None else None


def _links(run_id: UUID) -> LinkSet:
    root = f"/api/backtests/{run_id}"
    return LinkSet(
        self=root,
        result=f"{root}/result",
        signals=f"{root}/signals",
        risk_decisions=f"{root}/risk-decisions",
        orders=f"{root}/orders",
        fills=f"{root}/fills",
        equity=f"{root}/equity",
    )


def _metrics_response(metrics: PerformanceMetrics) -> MetricsResponse:
    return MetricsResponse(
        initial_equity=_decimal(metrics.initial_equity) or "0",
        final_equity=_decimal(metrics.final_equity) or "0",
        total_return=_decimal(metrics.total_return) or "0",
        cagr=_decimal(metrics.cagr),
        max_drawdown=_decimal(metrics.max_drawdown) or "0",
        sharpe_ratio=_decimal(metrics.sharpe_ratio),
        sortino_ratio=_decimal(metrics.sortino_ratio),
        total_commission=_decimal(metrics.total_commission) or "0",
        number_of_fills=metrics.number_of_fills,
    )


def _run_response(run: BacktestRun, metrics: PerformanceMetrics | None = None) -> RunResponse:
    parameters = {
        key: str(value) if isinstance(value, Decimal) else value
        for key, value in run.strategy_parameters.items()
    }
    return RunResponse(
        run_id=run.id,
        status=run.status,
        strategy_id=run.strategy_id,
        strategy_type=run.strategy_type,
        strategy_parameters=parameters,
        symbol=run.symbol,
        dataset_id=run.dataset_id,
        created_at=run.created_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        initial_cash=_decimal(run.initial_cash) or "0",
        default_order_quantity=_decimal(run.default_order_quantity) or "0",
        risk=run.risk,
        start=run.start,
        end=run.end,
        error_message=run.error_message,
        metrics=_metrics_response(metrics) if metrics is not None else None,
        links=_links(run.id),
    )


def _repository(session: AsyncSession) -> SQLAlchemyBacktestRepository:
    return SQLAlchemyBacktestRepository(session)


async def _require_run(repository: SQLAlchemyBacktestRepository, run_id: UUID) -> BacktestRun:
    run = await repository.get(run_id)
    if run is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "backtest run not found")
    return run


@router.post("", response_model=CreateBacktestResponse, status_code=status.HTTP_201_CREATED)
async def create_backtest(
    request: CreateBacktestRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
) -> CreateBacktestResponse:
    repository = _repository(session)
    settings = get_settings()
    service = BacktestApplicationService(
        repository,
        DatasetRegistry.phase7(settings.backtest_fixture_path),
        StrategyRegistry(),
    )
    try:
        run = await service.create_and_run(
            CreateBacktestCommand(
                dataset_id=request.dataset_id,
                symbol=request.symbol,
                strategy_type=request.strategy.type,
                strategy_parameters=request.strategy.parameters.model_dump(),
                initial_cash=request.initial_cash,
                default_order_quantity=request.default_order_quantity,
                risk=RiskConfig(**request.risk.model_dump()),
                start=request.start,
                end=request.end,
                client_request_id=idempotency_key,
            )
        )
    except UnknownDatasetError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "dataset not found") from exc
    except IdempotencyConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except IdempotencyInProgressError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except (UnknownStrategyError, InvalidStrategyParametersError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "idempotency key is already in use") from exc
    except BacktestExecutionError as exc:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            {"message": "backtest execution failed", "run_id": str(exc.run_id)},
        ) from exc
    return CreateBacktestResponse(run_id=run.id, status=run.status, links=_links(run.id))


@router.get("", response_model=PageResponse[RunResponse])
async def list_backtests(
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: PaginationLimit = 50,
    offset: PaginationOffset = 0,
    run_status: Annotated[BacktestRunStatus | None, Query(alias="status")] = None,
    symbol: Annotated[str | None, Query(min_length=1, max_length=32)] = None,
) -> PageResponse[RunResponse]:
    page = await _repository(session).list_runs(limit, offset, run_status, symbol)
    return PageResponse(
        items=[_run_response(item) for item in page.items],
        limit=page.limit,
        offset=page.offset,
        total=page.total,
    )


@router.get("/{run_id}", response_model=RunResponse)
async def get_backtest(
    run_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> RunResponse:
    repository = _repository(session)
    run = await _require_run(repository, run_id)
    summary = await repository.get_result_summary(run_id)
    return _run_response(run, summary.metrics if summary is not None else None)


@router.get("/{run_id}/result", response_model=ResultResponse)
async def get_result(
    run_id: UUID, session: Annotated[AsyncSession, Depends(get_session)]
) -> ResultResponse:
    repository = _repository(session)
    run = await _require_run(repository, run_id)
    summary = await repository.get_result_summary(run_id)
    if summary is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "backtest result is not available")
    metrics = summary.metrics
    return ResultResponse(
        run_id=run_id,
        status=run.status,
        metrics=_metrics_response(metrics),
        signal_count=summary.signal_count,
        proposal_count=summary.proposal_count,
        risk_decision_count=summary.risk_decision_count,
        risk_rejection_count=summary.risk_rejection_count,
        order_count=summary.order_count,
        fill_count=summary.fill_count,
        snapshot_count=summary.snapshot_count,
        reservation_count=summary.reservation_count,
        start_time=summary.start_time,
        end_time=summary.end_time,
    )


@router.get("/{run_id}/signals", response_model=PageResponse[SignalResponse])
async def get_signals(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: PaginationLimit = 50,
    offset: PaginationOffset = 0,
) -> PageResponse[SignalResponse]:
    repository = _repository(session)
    await _require_run(repository, run_id)
    page = await repository.list_signals(run_id, limit, offset)
    return PageResponse(
        items=[SignalResponse(**item.model_dump()) for item in page.items],
        limit=limit,
        offset=offset,
        total=page.total,
    )


@router.get("/{run_id}/risk-decisions", response_model=PageResponse[RiskDecisionResponse])
async def get_risk_decisions(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: PaginationLimit = 50,
    offset: PaginationOffset = 0,
) -> PageResponse[RiskDecisionResponse]:
    repository = _repository(session)
    await _require_run(repository, run_id)
    page = await repository.list_risk_decisions(run_id, limit, offset)
    items = []
    for item in page.items:
        payload = item.model_dump()
        for key, value in tuple(payload.items()):
            if isinstance(value, Decimal):
                payload[key] = _decimal(value)
        items.append(RiskDecisionResponse(**payload))
    return PageResponse(items=items, limit=limit, offset=offset, total=page.total)


@router.get("/{run_id}/orders", response_model=PageResponse[OrderResponse])
async def get_orders(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: PaginationLimit = 50,
    offset: PaginationOffset = 0,
) -> PageResponse[OrderResponse]:
    repository = _repository(session)
    await _require_run(repository, run_id)
    page = await repository.list_orders(run_id, limit, offset)
    return PageResponse(
        items=[
            OrderResponse(
                order_id=item.id,
                strategy_id=item.strategy_id,
                symbol=item.symbol,
                side=item.side.value,
                order_type=item.order_type.value,
                quantity=_decimal(item.quantity) or "0",
                price=_decimal(item.price),
                status=item.status.value,
                created_at=item.created_at,
            )
            for item in page.items
        ],
        limit=limit,
        offset=offset,
        total=page.total,
    )


@router.get("/{run_id}/fills", response_model=PageResponse[FillResponse])
async def get_fills(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: PaginationLimit = 50,
    offset: PaginationOffset = 0,
) -> PageResponse[FillResponse]:
    repository = _repository(session)
    await _require_run(repository, run_id)
    page = await repository.list_fills(run_id, limit, offset)
    return PageResponse(
        items=[
            FillResponse(
                order_id=item.order_id,
                strategy_id=item.strategy_id,
                symbol=item.symbol,
                side=item.side.value,
                quantity=_decimal(item.quantity) or "0",
                price=_decimal(item.price) or "0",
                commission=_decimal(item.commission) or "0",
                timestamp=item.timestamp,
            )
            for item in page.items
        ],
        limit=limit,
        offset=offset,
        total=page.total,
    )


@router.get("/{run_id}/equity", response_model=PageResponse[EquityResponse])
async def get_equity(
    run_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: PaginationLimit = 50,
    offset: PaginationOffset = 0,
) -> PageResponse[EquityResponse]:
    repository = _repository(session)
    await _require_run(repository, run_id)
    page = await repository.list_equity(run_id, limit, offset)
    return PageResponse(
        items=[
            EquityResponse(
                timestamp=item.timestamp,
                equity=_decimal(item.equity) or "0",
                cash=_decimal(item.cash) or "0",
                market_value=_decimal(item.market_value) or "0",
            )
            for item in page.items
        ],
        limit=limit,
        offset=offset,
        total=page.total,
    )
