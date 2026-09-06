import asyncio
import logging
from contextlib import suppress
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.exc import IntegrityError

from app.api.schemas.paper import (
    CreatePaperSessionRequest,
    MarketBarPayload,
    PaperEventResponse,
    PaperOrderResponse,
    PaperSessionPage,
    PaperSessionResponse,
    PaperSnapshotResponse,
    PortfolioPayload,
)
from app.application.backtests import DatasetRegistry, StrategyRegistry
from app.application.backtests.decimal_policy import canonical_decimal
from app.application.backtests.registry import (
    InvalidStrategyParametersError,
    UnknownDatasetError,
    UnknownStrategyError,
)
from app.application.paper_trading import (
    PaperSessionConflictError,
    PaperSessionStateError,
    PaperTradingManager,
)
from app.core.config import get_settings
from app.db.session import SessionFactory
from app.domain.risk import RiskConfig
from app.paper.models import CreatePaperSessionCommand, PaperEventRecord, PaperSession

settings = get_settings()
logger = logging.getLogger(__name__)
paper_manager = PaperTradingManager(
    SessionFactory,
    DatasetRegistry.phase7(settings.backtest_fixture_path),
    StrategyRegistry(),
)

router = APIRouter(prefix="/paper-trading/sessions", tags=["paper-trading"])


def _session_response(session: PaperSession) -> PaperSessionResponse:
    return PaperSessionResponse(
        session_id=session.id,
        status=session.status,
        provider_type=session.provider_type,
        dataset_id=session.dataset_id,
        symbol=session.symbol,
        strategy_type=session.strategy_type,
        strategy_parameters=session.strategy_parameters,
        initial_cash=canonical_decimal(session.initial_cash),
        default_order_quantity=canonical_decimal(session.default_order_quantity),
        risk=session.risk,
        created_at=session.created_at,
        started_at=session.started_at,
        stopped_at=session.stopped_at,
        error_message=session.error_message,
    )


async def _require_session(session_id: UUID) -> PaperSession:
    session = await paper_manager.get(session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "paper session not found")
    return session


@router.post("", response_model=PaperSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_paper_session(
    request: CreatePaperSessionRequest,
    idempotency_key: Annotated[str | None, Header(max_length=255)] = None,
) -> PaperSessionResponse:
    try:
        session = await paper_manager.create(
            CreatePaperSessionCommand(
                provider_type=request.provider_type,
                dataset_id=request.dataset_id,
                symbol=request.symbol,
                strategy_type=request.strategy.type,
                strategy_parameters=request.strategy.parameters.model_dump(),
                initial_cash=request.initial_cash,
                default_order_quantity=request.default_order_quantity,
                risk=RiskConfig(**request.risk.model_dump()),
                client_request_id=idempotency_key,
            )
        )
    except UnknownDatasetError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "paper dataset not found") from exc
    except PaperSessionConflictError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
    except IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "idempotency key is already in use") from exc
    except (UnknownStrategyError, InvalidStrategyParametersError, ValueError) as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc
    return _session_response(session)


@router.get("", response_model=PaperSessionPage)
async def list_paper_sessions(
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PaperSessionPage:
    sessions, total = await paper_manager.list(limit, offset)
    return PaperSessionPage(
        items=[_session_response(item) for item in sessions],
        limit=limit,
        offset=offset,
        total=total,
    )


@router.get("/{session_id}", response_model=PaperSessionResponse)
async def get_paper_session(session_id: UUID) -> PaperSessionResponse:
    return _session_response(await _require_session(session_id))


@router.post("/{session_id}/start", response_model=PaperSessionResponse)
async def start_paper_session(session_id: UUID) -> PaperSessionResponse:
    try:
        return _session_response(await paper_manager.start(session_id))
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "paper session not found") from exc
    except PaperSessionStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.post("/{session_id}/stop", response_model=PaperSessionResponse)
async def stop_paper_session(session_id: UUID) -> PaperSessionResponse:
    try:
        return _session_response(await paper_manager.stop(session_id))
    except LookupError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "paper session not found") from exc
    except PaperSessionStateError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc


@router.get("/{session_id}/events", response_model=list[PaperEventResponse])
async def get_paper_events(session_id: UUID) -> list[PaperEventResponse]:
    await _require_session(session_id)
    return [_event_response(item) for item in await paper_manager.events(session_id)]


@router.get("/{session_id}/snapshot", response_model=PaperSnapshotResponse)
async def get_paper_snapshot(session_id: UUID) -> PaperSnapshotResponse:
    session = await _require_session(session_id)
    events = await paper_manager.events(session_id)
    latest_bar: MarketBarPayload | None = None
    latest_portfolio: PortfolioPayload | None = None
    signals = []
    decisions = []
    fills = []
    orders: dict[str, PaperOrderResponse] = {}
    for event in events:
        payload = event.payload
        if event.event_type == "market.bar":
            latest_bar = MarketBarPayload.model_validate(payload)
        elif event.event_type == "signal.created":
            from app.api.schemas.backtests import SignalResponse

            signals.append(SignalResponse.model_validate(payload))
        elif event.event_type == "risk.decision":
            from app.api.schemas.backtests import RiskDecisionResponse

            decisions.append(RiskDecisionResponse.model_validate(payload))
        elif event.event_type == "order.updated":
            order = PaperOrderResponse.model_validate(payload)
            orders[str(order.order_id)] = order
        elif event.event_type == "fill.created":
            from app.api.schemas.backtests import FillResponse

            fills.append(FillResponse.model_validate(payload))
        elif event.event_type == "portfolio.snapshot":
            latest_portfolio = PortfolioPayload.model_validate(payload)
    return PaperSnapshotResponse(
        session=_session_response(session),
        last_sequence=events[-1].sequence if events else 0,
        latest_bar=latest_bar,
        signals=signals,
        risk_decisions=decisions,
        orders=list(orders.values()),
        fills=fills,
        latest_portfolio=latest_portfolio,
    )


@router.websocket("/ws/{session_id}")
async def paper_session_websocket(websocket: WebSocket, session_id: UUID) -> None:
    origin = websocket.headers.get("origin")
    if origin is not None and origin != settings.frontend_origin:
        await websocket.close(code=4403, reason="origin not allowed")
        return
    if await paper_manager.get(session_id) is None:
        await websocket.close(code=4404, reason="paper session not found")
        return
    async with paper_manager.hub.subscribe(session_id) as queue:
        await websocket.accept()
        await websocket.send_json(
            {
                "sequence": None,
                "type": "stream.connected",
                "occurred_at": None,
                "payload": {"message": "REST snapshot remains authoritative"},
            }
        )
        receive_task = asyncio.create_task(websocket.receive())
        try:
            while True:
                event_task = asyncio.create_task(queue.get())
                done, _ = await asyncio.wait(
                    {receive_task, event_task}, return_when=asyncio.FIRST_COMPLETED
                )
                if receive_task in done:
                    event_task.cancel()
                    with suppress(asyncio.CancelledError):
                        await event_task
                    message = receive_task.result()
                    if message["type"] == "websocket.disconnect":
                        break
                    receive_task = asyncio.create_task(websocket.receive())
                    continue
                event = event_task.result()
                await websocket.send_json(event)
                payload = event.get("payload")
                if (
                    event.get("type") == "session.status"
                    and isinstance(payload, dict)
                    and payload.get("status") in {"STOPPED", "FAILED", "INTERRUPTED"}
                ):
                    await websocket.close(code=1000, reason="paper session is terminal")
                    break
        except WebSocketDisconnect:
            logger.info("Paper WebSocket disconnected for session %s", session_id)
        finally:
            receive_task.cancel()
            with suppress(asyncio.CancelledError):
                await receive_task


def _event_response(event: PaperEventRecord) -> PaperEventResponse:
    return PaperEventResponse.model_validate(
        {
            "sequence": event.sequence,
            "type": event.event_type,
            "occurred_at": event.occurred_at,
            "payload": event.payload,
        }
    )
