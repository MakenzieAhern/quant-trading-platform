"""Paper accounting transport and recovery checks; no database or archive access."""

from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from app.api.schemas.paper import PortfolioPayload
from app.application.paper_trading import service
from app.application.paper_trading.service import PaperTradingManager
from app.backtest import BacktestConfig
from app.domain.markets import (
    CorporateAction,
    CorporateActionCompleteness,
    CorporateActionType,
    SecurityId,
)
from app.domain.trading import OrderSide, PortfolioSnapshot
from app.event import EventBus
from app.paper.models import PaperEventRecord, PaperSessionStatus
from app.paper.runtime import (
    PaperTradingRuntime,
    ReplayMarketDataProvider,
    SimulatedAShareSessionProvider,
)
from app.portfolio import PortfolioEngine
from tests.test_paper_plan_checkpoint import V3, account, checkpoint, source_runtime
from tests.test_paper_runtime import bar
from tests.test_portfolio_engine import START, make_bar, make_fill

ACCOUNTING_FIELDS = {"accounting_version", "corporate_action_realized_pnl", "total_pnl"}


@pytest.mark.parametrize(
    "price,realized,unrealized,total", [("12", "80", "120", "205"), ("9", "-40", "-60", "-95")]
)
def test_paper_pnl_explains_dividend_trading_and_costs(price, realized, unrealized, total):
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
            cash_per_share=Decimal("0.1"),
        ),
        datetime(2024, 1, 3, tzinfo=UTC),
    )
    portfolio.apply_fill(make_fill(3, OrderSide.SELL, "40", price, "3", "600000.SSE"))
    snapshot = portfolio.mark_to_market(make_bar(3, price, "600000.SSE"))
    assert snapshot is not None
    wire = PortfolioPayload.model_validate(PaperTradingManager._snapshot(snapshot)).model_dump()
    assert wire["accounting_version"] == "PNL_BREAKDOWN_V1"
    assert wire["corporate_action_realized_pnl"] == "10"
    assert wire["total_pnl"] == total
    assert wire["realized_pnl"] == realized  # Trading only, before separately recorded commissions.
    assert wire["unrealized_pnl"] == unrealized
    assert wire["cumulative_commission"] == "5"
    assert Decimal(total) == Decimal(wire["equity"]) - Decimal(2000)
    assert Decimal(total) == Decimal(realized) + Decimal(10) + Decimal(unrealized) - Decimal(5)


def wire_snapshot():
    return PaperTradingManager._snapshot(
        PortfolioSnapshot(
            timestamp=START,
            cash=Decimal("100.000000000000000002"),
            market_value=Decimal(0),
            equity=Decimal("100.000000000000000002"),
            realized_pnl=Decimal("0.000000000000000003"),
            corporate_action_realized_pnl=Decimal("-0.000000000000000001"),
            total_pnl=Decimal("0.000000000000000002"),
            drawdown=Decimal(0),
        )
    )


def test_paper_pnl_preserves_signed_precision_and_legacy_unknowns():
    wire = wire_snapshot()
    read = PortfolioPayload.model_validate(wire).model_dump(mode="json")
    assert read["corporate_action_realized_pnl"] == "-0.000000000000000001"
    assert read["total_pnl"] == "0.000000000000000002"
    legacy = {key: value for key, value in wire.items() if key not in ACCOUNTING_FIELDS}
    before = repr(legacy)
    unknown = PortfolioPayload.model_validate(legacy).model_dump(mode="json")
    assert all(unknown[key] is None for key in ACCOUNTING_FIELDS)
    assert repr(legacy) == before
    assert PortfolioPayload.model_validate(unknown).model_dump(mode="json") == unknown


@pytest.mark.parametrize(
    "fields",
    [
        {"accounting_version": "PNL_BREAKDOWN_V1"},
        {"accounting_version": "PNL_BREAKDOWN_V1", "total_pnl": "0"},
        {"accounting_version": "PNL_BREAKDOWN_V1", "corporate_action_realized_pnl": "0"},
        {
            "accounting_version": "PNL_BREAKDOWN_V2",
            "total_pnl": "0",
            "corporate_action_realized_pnl": "0",
        },
        {"total_pnl": "0"},
        {"corporate_action_realized_pnl": "0"},
        {"accounting_version": None, "total_pnl": "0", "corporate_action_realized_pnl": "0"},
    ],
)
def test_paper_pnl_rejects_incomplete_or_unversioned_contract(fields):
    legacy = {key: value for key, value in wire_snapshot().items() if key not in ACCOUNTING_FIELDS}
    with pytest.raises(ValidationError):
        PortfolioPayload.model_validate({**legacy, **fields})


@pytest.mark.parametrize("field", ["corporate_action_realized_pnl", "total_pnl"])
@pytest.mark.parametrize("value", [1, 0.1, True, None, "NaN", "Infinity", "", "not-money"])
def test_paper_pnl_rejects_non_decimal_strings(field, value):
    with pytest.raises(ValidationError):
        PortfolioPayload.model_validate({**wire_snapshot(), field: value})


def replay_runtime(session):
    bars = tuple(bar(day, "10") for day in range(3))
    runtime = PaperTradingRuntime((), BacktestConfig(initial_cash=session.initial_cash))
    provider = ReplayMarketDataProvider(bars, 0)
    provider.subscribe("AAPL")
    return bars, provider, runtime


async def saved_history(kind, shape):
    initial = account(V3)
    if kind == "replay":
        initial = replace(initial, provider_type="replay", symbol="AAPL")
        bars, _, runtime = replay_runtime(initial)
        records = []
        for item in bars[:2]:
            for event, timestamp, payload in PaperTradingManager._serialize_delta(
                await runtime.process_bar(item)
            ):
                records.append(
                    PaperEventRecord(initial.id, len(records) + 1, event, timestamp, payload)
                )
        records.append(
            PaperEventRecord(
                initial.id, len(records) + 1, "session.status", START, {"status": "PAUSED"}
            )
        )
    else:
        records = list(await checkpoint(initial, V3))
    snapshots = 0
    for index, event in enumerate(records):
        if event.event_type != "portfolio.snapshot":
            continue
        snapshots += 1
        if shape == "legacy" or (shape == "mixed" and snapshots == 1):
            records[index] = replace(
                event,
                payload={
                    key: value
                    for key, value in event.payload.items()
                    if key not in ACCOUNTING_FIELDS
                },
            )
    return initial, tuple(records)


def manager_for_history(monkeypatch, initial, history, kind):
    manager = PaperTradingManager(MagicMock(), MagicMock(), MagicMock())
    manager.events = AsyncMock(return_value=history)
    state = SimpleNamespace(current=initial, stored=[])

    async def transition(session, target, *args, **kwargs):
        state.current = replace(session, status=target)
        return state.current

    async def append(session_id, events):
        saved = tuple(
            PaperEventRecord(
                session_id, len(history) + len(state.stored) + index + 1, event, timestamp, payload
            )
            for index, (event, timestamp, payload) in enumerate(events)
        )
        state.stored.extend(saved)
        return saved

    def build(session, cursor_date):
        if kind == "replay":
            _, provider, runtime = replay_runtime(session)
            return provider, runtime
        sessions, runtime = source_runtime(session)
        return SimulatedAShareSessionProvider(sessions, 0), runtime

    manager.get = AsyncMock(side_effect=lambda _: state.current)
    manager._transition = transition
    manager._build_runtime = build
    monkeypatch.setattr(
        service, "SQLAlchemyPaperRepository", lambda _: SimpleNamespace(append_events=append)
    )
    return manager, state


@pytest.mark.parametrize("kind", ["replay", "a_share"])
@pytest.mark.parametrize("shape", ["legacy", "new", "mixed"])
async def test_paper_pnl_resume_preserves_old_journal_and_appends_only_new_events(
    monkeypatch, kind, shape
):
    initial, history = await saved_history(kind, shape)
    original = repr(history)
    manager, state = manager_for_history(monkeypatch, initial, history, kind)
    await manager._run(initial)
    assert state.current.status is PaperSessionStatus.STOPPED
    assert repr(history) == original
    market_type = "market.bar" if kind == "replay" else "market.session"
    assert sum(event.event_type == market_type for event in state.stored) == 1
    snapshots = [event for event in state.stored if event.event_type == "portfolio.snapshot"]
    assert len(snapshots) == 1
    assert snapshots[0].payload["accounting_version"] == "PNL_BREAKDOWN_V1"
    assert snapshots[0].payload.keys() >= ACCOUNTING_FIELDS
    combined = (*history, *state.stored)
    original_combined = repr(combined)
    manager.events.return_value = combined
    state.stored.clear()
    state.current = initial
    await manager._run(initial)
    assert state.current.status is PaperSessionStatus.STOPPED
    assert state.stored == []
    assert repr(combined) == original_combined


@pytest.mark.parametrize("kind", ["replay", "a_share"])
@pytest.mark.parametrize(
    "damage",
    [
        "missing_version",
        "missing_corporate",
        "missing_total",
        "unknown_version",
        "null_version",
        "changed_corporate",
        "changed_total",
        "changed_cash",
        "extra_key",
        "legacy_cash",
        "legacy_extra",
        "changed_kind",
        "missing_event",
    ],
)
async def test_paper_pnl_resume_rejects_damaged_mixed_history_before_append(
    monkeypatch, kind, damage
):
    initial, history = await saved_history(kind, "mixed")
    records = list(history)
    snapshots = [
        index for index, event in enumerate(records) if event.event_type == "portfolio.snapshot"
    ]
    index = snapshots[0] if damage.startswith("legacy") else snapshots[1]
    event = records[index]
    payload = dict(event.payload)
    if damage.startswith("missing_") and damage != "missing_event":
        field = {
            "missing_version": "accounting_version",
            "missing_corporate": "corporate_action_realized_pnl",
            "missing_total": "total_pnl",
        }[damage]
        payload.pop(field)
    elif damage in {"unknown_version", "null_version"}:
        payload["accounting_version"] = "PNL_BREAKDOWN_V2" if damage == "unknown_version" else None
    elif damage in {"changed_corporate", "changed_total", "changed_cash", "legacy_cash"}:
        field = {
            "changed_corporate": "corporate_action_realized_pnl",
            "changed_total": "total_pnl",
            "changed_cash": "cash",
            "legacy_cash": "cash",
        }[damage]
        payload[field] = "42"
    else:
        payload["unrecognized"] = "must-not-be-ignored"
    records[index] = replace(event, payload=payload)
    if damage == "changed_kind":
        records[index] = replace(event, event_type="fill.created")
    elif damage == "missing_event":
        del records[index]
    damaged = tuple(records)
    original = repr(damaged)
    manager, state = manager_for_history(monkeypatch, initial, damaged, kind)
    await manager._run(initial)
    assert state.current.status is PaperSessionStatus.FAILED
    assert state.stored == []
    assert repr(damaged) == original
