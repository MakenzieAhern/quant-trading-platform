"""Exact, metadata-bearing exports of immutable personal results (never formal studies)."""

import csv
import io
import json
import re
from collections.abc import AsyncIterator, Iterable
from datetime import UTC, date, datetime
from typing import Any

from app.application.experiments.service import (
    COLLECTIONS,
    ExperimentManager,
    collection_availability,
)
from app.db.models.experiments import ExperimentJobModel

CSV_FIELDS = {
    "equity": ("sequence", "trading_date", "equity", "benchmark", "drawdown"),
    "trades": (
        "sequence",
        "trading_date",
        "timestamp",
        "order_id",
        "security_id",
        "side",
        "quantity",
        "price",
        "transaction_cost",
    ),
    "decisions": (
        "sequence",
        "trading_date",
        "timestamp",
        "proposal_id",
        "security_id",
        "approved",
        "reason_code",
        "message",
    ),
    "holdings": (
        "sequence",
        "trading_date",
        "timestamp",
        "cash",
        "equity",
        "market_value",
        "realized_pnl",
        "corporate_action_realized_pnl",
        "total_pnl",
        "unrealized_pnl",
        "cumulative_commission",
        "pending_corporate_action_value",
        "positions",
    ),
}


def report_metadata(
    row: ExperimentJobModel, start: date | None, end: date | None
) -> dict[str, Any]:
    summary = row.summary or {}
    missing = [
        key
        for key in (
            "provenance",
            "implementation_sha256",
            "effective_transaction_cost_schedules",
            "effective_risk_limits",
            "execution_model",
        )
        if key not in summary
    ]
    return {
        "report_schema_version": 1,
        "job_id": str(row.id),
        "name": row.name,
        "status": row.status,
        "mode": row.mode,
        "created_at_utc": row.created_at.isoformat(),
        "completed_at_utc": row.completed_at.isoformat() if row.completed_at else None,
        "exported_at_utc": datetime.now(UTC).isoformat(),
        "timestamp_timezone": "UTC",
        "trading_date_timezone": "Asia/Shanghai",
        "configuration": row.configuration,
        "configuration_sha256": row.configuration_sha256,
        "dataset": {
            "id": row.dataset_id,
            "sha256": row.dataset_sha256,
            "provenance": summary.get("provenance"),
        },
        "strategy": {
            "id": row.configuration["strategy_id"],
            "version": summary.get("strategy_version", "1"),
            "parameters": row.configuration["strategy"],
        },
        "implementation_sha256": summary.get("implementation_sha256"),
        "execution_model": summary.get("execution_model"),
        "requested_costs": row.configuration["costs"],
        "effective_transaction_cost_schedules": summary.get("effective_transaction_cost_schedules"),
        "requested_risk": row.configuration["risk"],
        "effective_risk_limits": summary.get("effective_risk_limits"),
        "requested_dates": {
            "start": row.configuration["start_date"],
            "end": row.configuration["end_date"],
        },
        "actual_dates": {"start": summary.get("date_start"), "end": summary.get("date_end")},
        "display_filter": {
            "start_date": start.isoformat() if start else None,
            "end_date": end.isoformat() if end else None,
            "inclusive": True,
            "changes_full_run_metrics": False,
        },
        "limitations": summary.get("limitations", []),
        "legacy_metadata_not_recorded": missing,
        "collection_availability": {
            name: {
                "availability": collection_availability(row, name)[0],
                "reason_code": collection_availability(row, name)[1],
            }
            for name in COLLECTIONS
        },
        "csv_notes": [
            "EXACT_DECIMAL_TEXT_IMPORT_NUMERIC_COLUMNS_AS_TEXT",
            "FORMULA_LIKE_TEXT_PREFIXED_WITH_APOSTROPHE",
            "HOLDINGS_POSITIONS_COLUMN_IS_JSON",
        ],
    }


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def csv_cell(value: Any) -> str:
    """Quoted CSV is not formula-safe. Keep exact canonical decimals, escape other prefixes."""
    if value is None:
        return ""
    text = _json(value) if isinstance(value, (dict, list, bool)) else str(value)
    if re.fullmatch(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?", text):
        return text
    if text.lstrip().startswith(("=", "+", "-", "@")) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def _csv_row(values: Iterable[Any]) -> str:
    buffer = io.StringIO(newline="")
    csv.writer(buffer).writerow([csv_cell(value) for value in values])
    return buffer.getvalue()


async def _rows(
    manager: ExperimentManager,
    row: ExperimentJobModel,
    collection: str,
    start: date | None,
    end: date | None,
) -> AsyncIterator[dict[str, Any]]:
    if collection_availability(row, collection)[0] != "AVAILABLE":
        return
    offset = 0
    while True:
        items, total = await manager.collection(row.id, collection, 200, offset, start, end)
        for item in items:
            yield item
        offset += len(items)
        if not items or offset >= total:
            break


async def export_json(
    manager: ExperimentManager, row: ExperimentJobModel, start: date | None, end: date | None
) -> AsyncIterator[str]:
    yield '{"metadata":' + _json(report_metadata(row, start, end))
    yield ',"full_period_summary":' + _json(row.summary) + ',"collections":{'
    for index, collection in enumerate(COLLECTIONS):
        yield ("," if index else "") + _json(collection) + ":["
        first = True
        async for item in _rows(manager, row, collection, start, end):
            yield ("" if first else ",") + _json(item)
            first = False
        yield "]"
    yield "}}"


async def export_csv(
    manager: ExperimentManager,
    row: ExperimentJobModel,
    collection: str,
    start: date | None,
    end: date | None,
) -> AsyncIterator[str]:
    fields = CSV_FIELDS[collection]
    yield _csv_row(("record_type", "field", "value", *fields))
    metadata = report_metadata(row, start, end)
    for field, value in {**metadata, "full_period_summary": row.summary}.items():
        yield _csv_row(("metadata", field, value, *([""] * len(fields))))
    async for item in _rows(manager, row, collection, start, end):
        yield _csv_row((collection, "", "", *(item.get(field) for field in fields)))
