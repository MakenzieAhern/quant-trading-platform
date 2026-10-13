"""Disposable-DB accounting transport through REST and ASGI WebSocket JSON, not TCP/browser."""

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.routes.paper import paper_manager, settings
from app.application.paper_trading.service import PaperTradingManager
from app.db.models.paper import PaperTradingEventModel
from app.db.repositories.paper import SQLAlchemyPaperRepository
from app.db.session import SessionFactory
from app.domain.markets import (
    CorporateAction,
    CorporateActionCompleteness,
    CorporateActionType,
    SecurityId,
)
from app.domain.trading import OrderSide
from app.event import EventBus
from app.main import app
from app.portfolio import PortfolioEngine
from tests.test_paper_api import a_share_request_body
from tests.test_paper_api import clean_paper_tables as clean_paper_tables
from tests.test_portfolio_engine import make_bar, make_fill

ACCOUNTING = {
    "accounting_version": "PNL_BREAKDOWN_V1",
    "corporate_action_realized_pnl": "10.000000000000000001",
    "total_pnl": "205.000000000000000001",
}


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value


def dividend_snapshot():
    portfolio = PortfolioEngine(EventBus(), Decimal(2000))
    portfolio.apply_fill(make_fill(1, OrderSide.BUY, "100", "10", "2", "600000.SSE"))
    portfolio.apply_corporate_action(
        "600000.SSE",
        CorporateAction(
            security_id=SecurityId(value="CN-A:SSE:600000"),
            announcement_date=date(2024, 1, 1),
            ex_date=date(2024, 1, 3),
            source_provider="fixture",
            source_version="1",
            source_record_hash="a" * 64,
            completeness=CorporateActionCompleteness.COMPLETE,
            action_type=CorporateActionType.CASH_DIVIDEND,
            cash_per_share=Decimal("0.10000000000000000001"),
        ),
        datetime(2024, 1, 3, tzinfo=UTC),
    )
    portfolio.apply_fill(make_fill(3, OrderSide.SELL, "40", "12", "3", "600000.SSE"))
    snapshot = portfolio.mark_to_market(make_bar(3, "12", "600000.SSE"))
    assert snapshot is not None
    assert snapshot.realized_pnl == 80 and snapshot.cumulative_commission == 5
    assert snapshot.unrealized_pnl == 120
    assert snapshot.total_pnl == snapshot.equity - Decimal(2000)
    return snapshot


@asynccontextmanager
async def websocket_frames(session_id):
    """Exercise FastAPI routing and Starlette's actual JSON-frame serialization in this loop."""
    incoming = asyncio.Queue(maxsize=2)
    outgoing = asyncio.Queue(maxsize=4)
    path = f"/api/paper-trading/sessions/ws/{session_id}"
    scope = {
        "type": "websocket",
        "asgi": {"version": "3.0", "spec_version": "2.4"},
        "http_version": "1.1",
        "scheme": "ws",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": [(b"host", b"test"), (b"origin", settings.frontend_origin.encode())],
        "client": ("127.0.0.1", 12345),
        "server": ("test", 80),
        "subprotocols": [],
        "state": {},
    }
    incoming.put_nowait({"type": "websocket.connect"})
    task = asyncio.create_task(app(scope, incoming.get, outgoing.put))
    try:
        accepted = await asyncio.wait_for(outgoing.get(), 5)
        assert accepted["type"] == "websocket.accept"
        connected = await asyncio.wait_for(outgoing.get(), 5)
        assert connected["type"] == "websocket.send"
        assert json.loads(connected["text"])["type"] == "stream.connected"
        yield outgoing
    finally:
        incoming.put_nowait({"type": "websocket.disconnect", "code": 1000})
        await asyncio.wait_for(task, 5)
    assert paper_manager.hub.subscriber_count(session_id) == 0


@pytest.mark.parametrize("legacy", [False, True], ids=["versioned", "legacy-missing-fields"])
async def test_saved_pnl_survives_jsonb_rest_and_asgi_frames_without_rewriting_legacy(
    client, legacy
):
    snapshot = dividend_snapshot()
    payload = PaperTradingManager._snapshot(snapshot)
    assert {key: payload[key] for key in ACCOUNTING} == ACCOUNTING
    if legacy:
        payload = {key: value for key, value in payload.items() if key not in ACCOUNTING}
    original = deepcopy(payload)
    created = await client.post(
        "/api/paper-trading/sessions",
        json={**a_share_request_body(), "initial_cash": "2000"},
    )
    assert created.status_code == 201
    session_id = UUID(created.json()["session_id"])
    base = f"/api/paper-trading/sessions/{session_id}"
    async with websocket_frames(session_id) as frames:
        async with SessionFactory() as db:
            saved = await SQLAlchemyPaperRepository(db).append_events(
                session_id, (("portfolio.snapshot", snapshot.timestamp, payload),)
            )
        query = select(PaperTradingEventModel.payload).where(
            PaperTradingEventModel.session_id == session_id,
            PaperTradingEventModel.sequence == saved[0].sequence,
        )
        # Read through a fresh session: this verifies the committed JSONB, not the ORM object.
        async with SessionFactory() as db:
            assert await db.scalar(query) == original
        paper_manager.hub.publish(session_id, paper_manager._wire_event(saved[0]))
        frame = await asyncio.wait_for(frames.get(), 5)
        assert frame["type"] == "websocket.send" and isinstance(frame["text"], str)
        wire = json.loads(frame["text"])
        assert wire["type"] == "portfolio.snapshot"
        assert wire["sequence"] == saved[0].sequence
        assert wire["payload"] == original
        if legacy:
            assert not ACCOUNTING.keys() & wire["payload"].keys()
        else:
            assert {key: wire["payload"][key] for key in ACCOUNTING} == ACCOUNTING

        reads = []
        for endpoint in ("state", "snapshot"):
            response = await client.get(f"{base}/{endpoint}")
            assert response.status_code == 200
            assert response.json()["last_sequence"] == saved[0].sequence
            reads.append(response.json()["latest_portfolio"])
        response = await client.get(f"{base}/events", params={"limit": 10})
        assert response.status_code == 200
        event = next(item for item in response.json() if item["sequence"] == saved[0].sequence)
        assert event["type"] == "portfolio.snapshot"
        reads.append(event["payload"])
        for read in reads:
            assert {key: read[key] for key in ACCOUNTING} == (
                dict.fromkeys(ACCOUNTING) if legacy else ACCOUNTING
            )
            for key in (
                "cash",
                "equity",
                "realized_pnl",
                "unrealized_pnl",
                "cumulative_commission",
            ):
                assert read[key] == original[key]
        async with SessionFactory() as db:
            after = await db.scalar(query)
        assert after == original == payload
        if legacy:
            assert not ACCOUNTING.keys() & after.keys()
