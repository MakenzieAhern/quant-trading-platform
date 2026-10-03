"""Thin transport for the independent self-service research workspace."""

import asyncio
from datetime import date
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.api.schemas.experiments import (
    CreateExperimentRequest,
    ExperimentCollection,
    ExperimentPage,
    ExperimentResponse,
)
from app.application.experiments.data import (
    ExperimentDatasetRegistry,
    ExperimentInputError,
    current_dataset_quality,
)
from app.application.experiments.export import export_csv, export_json
from app.application.experiments.service import (
    ExperimentConflictError,
    ExperimentManager,
    collection_availability,
    validate_display_dates,
)
from app.core.config import get_settings
from app.db.models.experiments import ExperimentJobModel
from app.db.session import SessionFactory, engine

router = APIRouter(tags=["experiments"])
experiment_manager = ExperimentManager(
    SessionFactory,
    ExperimentDatasetRegistry(get_settings().research_data_path, get_settings().product_data_path),
    engine,
)
Key = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=1, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$"),
]
Limit = Annotated[int, Query(ge=1, le=200)]
Offset = Annotated[int, Query(ge=0, le=2_147_483_647)]


def _response(row: ExperimentJobModel) -> ExperimentResponse:
    return ExperimentResponse.model_validate(
        {
            "job_id": row.id,
            "name": row.name,
            "status": row.status,
            "mode": row.mode,
            "dataset_id": row.dataset_id,
            "dataset_sha256": row.dataset_sha256,
            "configuration": row.configuration,
            "configuration_sha256": row.configuration_sha256,
            "created_at": row.created_at,
            "started_at": row.started_at,
            "completed_at": row.completed_at,
            "phase": row.phase,
            "completed_sessions": row.completed_sessions,
            "total_sessions": row.total_sessions,
            "cancel_requested": row.cancel_requested,
            "error_code": row.error_code,
            "retry_of": row.retry_of,
            "attempt": row.attempt,
            "result_available": row.summary is not None,
        }
    )


def _error(request: Request, exc: Exception) -> JSONResponse:
    http_status = (
        404
        if isinstance(exc, LookupError)
        else 409
        if isinstance(exc, ExperimentConflictError)
        else 422
    )
    code = exc.code if isinstance(exc, ExperimentInputError) else str(exc)
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "message": code,
            "details": {},
            "request_id": request.headers.get("x-request-id", str(uuid4())),
        },
    )


@router.get("/workbench/capabilities")
async def capabilities() -> dict[str, Any]:
    return await asyncio.to_thread(experiment_manager.registry.capabilities)


@router.post("/experiments", response_model=ExperimentResponse, status_code=202)
async def create_experiment(
    payload: CreateExperimentRequest, request: Request, idempotency_key: Key
) -> ExperimentResponse | JSONResponse:
    try:
        return _response(await experiment_manager.create(payload, idempotency_key))
    except (ExperimentInputError, ExperimentConflictError) as exc:
        return _error(request, exc)


@router.get("/experiments", response_model=ExperimentPage)
async def list_experiments(
    limit: Limit = 20,
    offset: Offset = 0,
    q: Annotated[str, Query(max_length=80)] = "",
    status: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED", "INTERRUPTED"]
    | None = None,
    mode: Literal["historical_exploration", "synthetic_demo"] | None = None,
    sort: Literal["newest", "oldest", "name_asc", "name_desc"] = "newest",
) -> ExperimentPage:
    items, total = await experiment_manager.list_jobs(limit, offset, q, status, mode, sort)
    return ExperimentPage(
        items=[_response(item) for item in items], total=total, limit=limit, offset=offset
    )


@router.get("/experiments/{job_id}", response_model=ExperimentResponse)
async def experiment(job_id: UUID, request: Request) -> ExperimentResponse | JSONResponse:
    try:
        return _response(await experiment_manager.get(job_id))
    except LookupError as exc:
        return _error(request, exc)


@router.post("/experiments/{job_id}/cancel", response_model=ExperimentResponse)
async def cancel_experiment(job_id: UUID, request: Request) -> ExperimentResponse | JSONResponse:
    try:
        return _response(await experiment_manager.cancel(job_id))
    except LookupError as exc:
        return _error(request, exc)


@router.post("/experiments/{job_id}/retry", response_model=ExperimentResponse, status_code=202)
async def retry_experiment(
    job_id: UUID, request: Request, idempotency_key: Key
) -> ExperimentResponse | JSONResponse:
    try:
        return _response(await experiment_manager.retry(job_id, idempotency_key))
    except (LookupError, ExperimentInputError, ExperimentConflictError) as exc:
        return _error(request, exc)


@router.get("/experiments/{job_id}/result", response_model=None)
async def experiment_result(job_id: UUID, request: Request) -> dict[str, Any] | JSONResponse:
    try:
        row = await experiment_manager.get(job_id)
        if row.summary is None:
            raise ExperimentConflictError("RESULT_NOT_READY")
        quality = current_dataset_quality(row.dataset_id, row.dataset_sha256)
        return {**row.summary, "current_dataset_quality": quality} if quality else row.summary
    except (LookupError, ExperimentConflictError) as exc:
        return _error(request, exc)


@router.get("/experiments/{job_id}/export", response_model=None)
async def export_experiment(
    job_id: UUID,
    request: Request,
    format: Literal["json", "csv"] = "json",
    collection: Literal["equity", "trades", "holdings", "decisions"] = "trades",
    start_date: date | None = None,
    end_date: date | None = None,
) -> StreamingResponse | JSONResponse:
    try:
        validate_display_dates(start_date, end_date)
        row = await experiment_manager.get(job_id)
        if row.status != "SUCCEEDED" or row.summary is None:
            raise ExperimentConflictError("RESULT_NOT_READY")
        availability, reason = collection_availability(row, collection)
        if format == "csv" and availability != "AVAILABLE":
            raise ExperimentConflictError(reason)
        content = (
            export_json(experiment_manager, row, start_date, end_date)
            if format == "json"
            else export_csv(experiment_manager, row, collection, start_date, end_date)
        )
        return StreamingResponse(
            content,
            media_type="application/json" if format == "json" else "text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="experiment-{job_id}.{format}"',
                "X-Content-Type-Options": "nosniff",
                "Cache-Control": "no-store",
            },
        )
    except (LookupError, ExperimentInputError, ExperimentConflictError) as exc:
        return _error(request, exc)


@router.get("/experiments/{job_id}/{collection}", response_model=ExperimentCollection)
async def experiment_collection(
    job_id: UUID,
    collection: Literal["equity", "trades", "decisions", "holdings"],
    request: Request,
    limit: Limit = 200,
    offset: Offset = 0,
    start_date: date | None = None,
    end_date: date | None = None,
) -> ExperimentCollection | JSONResponse:
    try:
        items, total = await experiment_manager.collection(
            job_id, collection, limit, offset, start_date, end_date
        )
        availability, reason = collection_availability(
            await experiment_manager.get(job_id), collection
        )
        return ExperimentCollection.model_validate(
            {
                "items": items,
                "total": total,
                "limit": limit,
                "offset": offset,
                "availability": availability,
                "reason_code": reason,
            }
        )
    except (LookupError, ExperimentInputError) as exc:
        return _error(request, exc)
