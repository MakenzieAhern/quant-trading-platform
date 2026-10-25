"""Explicit user requests only; never implicitly acquire on page open or app startup."""

from datetime import date
from typing import Annotated, Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse

from app.application.experiments.data import ExperimentDatasetRegistry, ExperimentInputError
from app.application.market_updates.contracts import AUTHORITY, CreateUpdateRequest, UpdateConflict
from app.application.market_updates.service import MarketUpdateManager
from app.application.markets import MarketReader
from app.core.config import get_settings
from app.db.models.market_updates import MarketUpdateJobModel
from app.db.session import SessionFactory, engine

router = APIRouter(prefix="/market-updates", tags=["market-updates"])
market_update_manager = MarketUpdateManager(
    SessionFactory,
    engine,
    MarketReader(
        ExperimentDatasetRegistry(
            get_settings().research_data_path, get_settings().product_data_path
        )
    ),
    get_settings().product_data_path / "market-candidates",
)
Key = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"),
]
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0, le=2_147_483_647)]


def response(row: MarketUpdateJobModel) -> dict[str, Any]:
    return {
        "job_id": str(row.id),
        "status": row.status,
        "phase": row.phase,
        "configuration": row.configuration,
        "configuration_sha256": row.configuration_sha256,
        "master_snapshot": row.master_snapshot,
        "created_at": row.created_at,
        "started_at": row.started_at,
        "completed_at": row.completed_at,
        "completed_requests": row.completed_requests,
        "total_requests": row.total_requests,
        "cancel_requested": row.cancel_requested,
        "error_code": row.error_code,
        "retry_of": str(row.retry_of) if row.retry_of else None,
        "attempt": row.attempt,
        "summary": row.summary,
        "authority": AUTHORITY,
        "mode": "raw_only_candidate",
    }


def error(request: Request, exc: Exception) -> JSONResponse:
    code = exc.code if isinstance(exc, ExperimentInputError) else str(exc)
    return JSONResponse(
        status_code=404
        if isinstance(exc, LookupError)
        else 409
        if isinstance(exc, UpdateConflict)
        else 422,
        content={
            "code": code,
            "message": code,
            "details": {},
            "request_id": request.headers.get("x-request-id", str(uuid4())),
        },
    )


@router.get("/capabilities")
async def capabilities() -> dict[str, Any]:
    return await market_update_manager.capabilities()


@router.post("", status_code=202, response_model=None)
async def create(
    payload: CreateUpdateRequest, request: Request, idempotency_key: Key
) -> dict[str, Any] | JSONResponse:
    try:
        return response(await market_update_manager.create(payload, idempotency_key))
    except (ExperimentInputError, UpdateConflict, LookupError) as exc:
        return error(request, exc)


@router.get("")
async def history(limit: Limit = 20, offset: Offset = 0) -> dict[str, Any]:
    rows, total = await market_update_manager.list_jobs(limit, offset)
    return {
        "items": [response(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/observations", response_model=None)
async def observations(
    request: Request,
    security_id: Annotated[str, Query(pattern=r"^CN-A:(SSE|SZSE):[0-9]{6}$")],
    start_date: date,
    end_date: date,
) -> dict[str, Any] | JSONResponse:
    if not 1 <= (end_date - start_date).days + 1 <= 366:
        return error(request, ExperimentInputError("UPDATE_DATE_RANGE_MUST_BE_1_TO_366_DAYS"))
    try:
        items = await market_update_manager.observations(security_id, start_date, end_date)
        return {
            "items": items,
            "total": len(items),
            "authority": AUTHORITY,
            "mode": "raw_only_candidate",
            "trading_date_timezone": "Asia/Shanghai",
        }
    except ExperimentInputError as exc:
        return error(request, exc)


@router.get("/{job_id}", response_model=None)
async def detail(job_id: UUID, request: Request) -> dict[str, Any] | JSONResponse:
    try:
        return response(await market_update_manager.get(job_id))
    except LookupError as exc:
        return error(request, exc)


@router.post("/{job_id}/cancel", response_model=None)
async def cancel(job_id: UUID, request: Request) -> dict[str, Any] | JSONResponse:
    try:
        return response(await market_update_manager.cancel(job_id))
    except LookupError as exc:
        return error(request, exc)


@router.post("/{job_id}/retry", status_code=202, response_model=None)
async def retry(
    job_id: UUID, request: Request, idempotency_key: Key
) -> dict[str, Any] | JSONResponse:
    try:
        return response(await market_update_manager.retry(job_id, idempotency_key))
    except (LookupError, ExperimentInputError, UpdateConflict) as exc:
        return error(request, exc)


@router.get("/{job_id}/receipts", response_model=None)
async def receipts(
    job_id: UUID, request: Request, limit: Limit = 20, offset: Offset = 0
) -> dict[str, Any] | JSONResponse:
    try:
        items, total = await market_update_manager.receipts(job_id, limit, offset)
        return {"items": items, "total": total, "limit": limit, "offset": offset}
    except (LookupError, ExperimentInputError) as exc:
        return error(request, exc)
