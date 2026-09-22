"""Close unresolved SZSE suspensions at the first later official traded day."""

import argparse
import json
import warnings
from collections import defaultdict, deque
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts.audit_full_suspensions import _date, _identity, _identity_index, _lifecycle_ends
from scripts.audit_szse_official_daily_scope import CALENDAR_SHA, MASTER_SHA, validate_traded_row
from scripts.probe_szse_official_daily import HEADERS, request
from scripts.reconcile_sse_cninfo import save, sha

CLOSURE = "OFFICIAL_DAILY_TRADE_OBSERVATION_CONSERVATIVE_BOUNDARY"
TERMINAL_CLOSURE = "OFFICIAL_MASTER_TERMINATION_AFTER_DAILY_NONTRADE"
RIGHT_CENSORED_CLOSURE = "COVERAGE_END_RIGHT_CENSORED_ACTIVE_SUSPENSION"


def pending_events(rows: list[dict]) -> dict[str, deque]:
    pending = defaultdict(deque)
    seen = set()
    for row in sorted(rows, key=lambda item: (item["security_id"], item["suspended_at"])):
        key = (row["security_id"], row["suspended_at"])
        if key in seen:
            raise ValueError("DUPLICATE_UNRESOLVED_SUSPENSION")
        seen.add(key)
        pending[row["security_id"]].append(row)
    return pending


def accept_traded_day(
    pending: dict[str, deque], accepted: list[dict], security_id: str, day: str, evidence: dict
) -> None:
    rows = pending.get(security_id)
    while rows and _date(rows[0]["suspended_at"]) < day:
        row = rows.popleft()
        accepted.append(
            {
                "security_id": security_id,
                "suspended_at": row["suspended_at"],
                "resumed_at": day,
                "execution_open_blocked": True,
                "closure": CLOSURE,
                "evidence": [evidence],
            }
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--scope-audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    master_bytes, calendar_bytes = args.master.read_bytes(), args.calendar.read_bytes()
    if sha(master_bytes) != MASTER_SHA or sha(calendar_bytes) != CALENDAR_SHA:
        raise ValueError("ACCEPTED_MASTER_OR_CALENDAR_CHANGED")
    master = json.loads(master_bytes)
    sessions = json.loads(calendar_bytes)["sessions"]
    unresolved = json.loads(args.unresolved.read_bytes())
    pending = pending_events(unresolved)
    target_ids = set(pending)
    index = _identity_index(
        [
            row
            for row in master
            if row["security_id"] in target_ids
            and row["exchange"] == "SZSE"
            and row["instrument_type"] == "COMMON_A_SHARE"
        ]
    )

    collection_path = args.source_root / "full-collection-report.json"
    collection_bytes = collection_path.read_bytes()
    collection = json.loads(collection_bytes)
    scope = json.loads(args.scope_audit.read_bytes())
    if scope["manifest_sha256"] != canonical_sha256(
        {key: value for key, value in scope.items() if key != "manifest_sha256"}
    ):
        raise ValueError("SOURCE_SCOPE_AUDIT_MANIFEST_CHANGED")
    if (
        scope["status"] != "COMPLETE_SOURCE_SNAPSHOT_SCOPE_NOT_RAW_AUTHORITY"
        or scope["audited_sessions"] != len(sessions)
        or scope["expected_sessions"] != len(sessions)
        or scope["transport_failures"]
        or scope["source_collection_sha256"] != sha(collection_bytes)
        or collection["calendar_sha256"] != CALENDAR_SHA
        or len(collection["results"]) != len(sessions)
    ):
        raise ValueError("OFFICIAL_SZSE_DAILY_SCOPE_NOT_COMPLETE")

    accepted = []
    for day, result in zip(sessions, collection["results"], strict=True):
        if result["date"] != day or result["status"] == "FAILED":
            raise ValueError("SOURCE_COLLECTION_SESSION_ORDER_CHANGED")
        url, catalog, referer = request(day)
        path = args.source_root / f"{day}.xlsx"
        raw = path.read_bytes()
        meta = json.loads(path.with_suffix(".xlsx.meta.json").read_bytes())
        if (
            sha(raw) != result["source_sha256"]
            or meta["sha256"] != result["source_sha256"]
            or meta["url"] != url
            or meta["referer"] != referer
            or result["catalog"] != catalog
            or not meta["retrieved_at_utc"].endswith("+00:00")
        ):
            raise ValueError(f"OFFICIAL_SZSE_SOURCE_RECEIPT_CHANGED: {day}")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            workbook = load_workbook(BytesIO(raw), read_only=True, data_only=True)
        rows = workbook.active
        rows.reset_dimensions()
        values = rows.values
        if tuple(next(values)) != HEADERS:
            raise ValueError(f"OFFICIAL_SZSE_COLUMNS_CHANGED: {day}")
        for row in values:
            symbol = row[1]
            if row[0] != day or not isinstance(symbol, str):
                raise ValueError(f"OFFICIAL_SZSE_DATE_OR_CODE_CHANGED: {day}")
            if ("SZSE", symbol) not in index or not validate_traded_row(row):
                continue
            identity = _identity(index, "SZSE", symbol, day)
            if identity is None:
                continue
            accept_traded_day(
                pending,
                accepted,
                identity["security_id"],
                day,
                {
                    "source": "SZSE_OFFICIAL_DAILY_ALL_METHODS_EXPORT",
                    "source_file": str(path),
                    "source_url": url,
                    "source_sha256": result["source_sha256"],
                    "retrieved_at_utc": meta["retrieved_at_utc"],
                    "trading_date": day,
                    "symbol": symbol,
                    "name": row[2],
                    "volume_10k_shares": str(row[9]),
                    "amount_10k_cny": str(row[10]),
                    "boundary_semantics": "TRADE_OBSERVED_DURING_DAY; OPEN_REMAINS_BLOCKED",
                },
            )

    remaining = sorted(
        (row for rows in pending.values() for row in rows),
        key=lambda row: (row["suspended_at"], row["security_id"]),
    )
    lifecycle_ends = _lifecycle_ends(master)
    terminal, right_censored, unresolved_after_closure = [], [], []
    for row in remaining:
        identity = _identity(index, "SZSE", row["symbol"], _date(row["suspended_at"]))
        if identity is None:
            unresolved_after_closure.append(row)
            continue
        evidence = [
            {
                "source": "SZSE_OFFICIAL_MASTER_PLUS_COMPLETE_DAILY_NONTRADE",
                "master_source_id": identity["source_id"],
                "master_source_url": identity["source_url"],
                "master_source_sha256": identity["source_sha256"],
                "source_collection_sha256": sha(collection_bytes),
                "source_scope_audit_sha256": sha256_file(args.scope_audit),
                "source_scope_manifest_sha256": scope["manifest_sha256"],
                "boundary_semantics": ("SUSPENSION_REMAINS_ACTIVE_WITH_NO_LATER_POSITIVE_TURNOVER"),
            }
        ]
        end = lifecycle_ends[row["security_id"]]
        common = {
            "security_id": row["security_id"],
            "suspended_at": row["suspended_at"],
            "execution_open_blocked": True,
            "evidence": evidence,
        }
        if end is not None and end <= sessions[-1]:
            terminal.append(
                {
                    **common,
                    "terminal_at": end,
                    "closure": TERMINAL_CLOSURE,
                }
            )
        else:
            right_censored.append(
                {
                    **common,
                    "censored_at": sessions[-1],
                    "closure": RIGHT_CENSORED_CLOSURE,
                }
            )
    accepted.sort(key=lambda row: (row["suspended_at"], row["security_id"]))
    report = {
        "report_version": "SZSE_OFFICIAL_DAILY_TRADE_RESUMPTION_V1",
        "status": (
            "COMPLETE_CONSERVATIVE_BOUNDARIES" if not unresolved_after_closure else "PARTIAL"
        ),
        "method": CLOSURE,
        "same_day_trade_is_not_resumption_evidence": True,
        "execution_open_blocked_on_first_observed_trade_day": True,
        "exact_intraday_resumption_not_claimed": True,
        "parser_sha256": sha256_file(Path(__file__)),
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "master_sha256": MASTER_SHA,
        "calendar_sha256": CALENDAR_SHA,
        "source_collection_sha256": sha(collection_bytes),
        "source_scope_audit_sha256": sha256_file(args.scope_audit),
        "input_unresolved": len(unresolved),
        "accepted_count": len(accepted) + len(terminal) + len(right_censored),
        "daily_trade_boundary_count": len(accepted),
        "terminal_boundary_count": len(terminal),
        "right_censored_boundary_count": len(right_censored),
        "remaining_count": len(unresolved_after_closure),
        "accepted_resumptions": accepted,
        "accepted_terminal_closures": terminal,
        "accepted_right_censored_closures": right_censored,
        "remaining_unresolved": unresolved_after_closure,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    save(args.output, report)
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key
                not in (
                    "accepted_resumptions",
                    "accepted_terminal_closures",
                    "accepted_right_censored_closures",
                    "remaining_unresolved",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
