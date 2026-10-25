"""Read-only local archive inspection and explicit personal watchlist preferences."""

from datetime import date
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Path, Query, Response
from fastapi.responses import JSONResponse
from pydantic import Field

from app.api.schemas.backtests import StrictModel
from app.application.experiments.data import ExperimentDatasetRegistry, ExperimentInputError
from app.application.markets import MarketReader
from app.application.watchlist import WatchlistService
from app.core.config import get_settings
from app.db.session import SessionFactory

router = APIRouter(prefix="/markets", tags=["markets"])
market_reader = MarketReader(
    ExperimentDatasetRegistry(get_settings().research_data_path, get_settings().product_data_path)
)
watchlist_service = WatchlistService(SessionFactory, market_reader)
Security = Annotated[str, Path(pattern=r"^CN-A:(SSE|SZSE):[0-9]{6}$")]
Dataset = Annotated[str, Query(min_length=3, max_length=128, pattern=r"^[a-z0-9][a-z0-9._-]+$")]
Limit = Annotated[int, Query(ge=1, le=50)]
Offset = Annotated[int, Query(ge=0, le=10000)]


class WatchlistAdd(StrictModel):
    dataset_id: str = Field(min_length=3, max_length=128, pattern=r"^[a-z0-9][a-z0-9._-]+$")


def _error(exc: ExperimentInputError | LookupError) -> JSONResponse:
    code = exc.code if isinstance(exc, ExperimentInputError) else str(exc)
    return JSONResponse(
        status_code=404 if isinstance(exc, LookupError) else 422,
        content={"code": code, "message": code, "details": {}},
    )


@router.get("/datasets")
def datasets() -> list[dict[str, Any]]:
    return market_reader.registry.datasets()


@router.get("/securities", response_model=None)
def securities(
    dataset_id: Dataset,
    q: Annotated[str, Query(max_length=80)] = "",
    exchange: Literal["ALL", "SSE", "SZSE"] = "ALL",
    limit: Limit = 20,
    offset: Offset = 0,
) -> dict[str, Any] | JSONResponse:
    try:
        return market_reader.search(dataset_id, q, exchange, limit, offset)
    except (ExperimentInputError, LookupError) as exc:
        return _error(exc)


@router.get("/securities/{security_id}/bars", response_model=None)
def bars(
    security_id: Security, dataset_id: Dataset, start_date: date, end_date: date
) -> dict[str, Any] | JSONResponse:
    try:
        return market_reader.bars(dataset_id, security_id, start_date, end_date)
    except (ExperimentInputError, LookupError) as exc:
        return _error(exc)


@router.get("/watchlist")
async def watchlist(
    limit: Limit = 50, offset: Offset = 0, q: Annotated[str, Query(max_length=80)] = ""
) -> dict[str, Any]:
    return await watchlist_service.list(limit, offset, q)


@router.put("/watchlist/{security_id}", response_model=None)
async def add_watchlist(
    security_id: Security, payload: WatchlistAdd
) -> dict[str, Any] | JSONResponse:
    try:
        return await watchlist_service.add(payload.dataset_id, security_id)
    except (ExperimentInputError, LookupError) as exc:
        return _error(exc)


@router.delete("/watchlist/{security_id}", status_code=204)
async def remove_watchlist(security_id: Security, dataset_id: Dataset) -> Response:
    await watchlist_service.remove(dataset_id, security_id)
    return Response(status_code=204)
