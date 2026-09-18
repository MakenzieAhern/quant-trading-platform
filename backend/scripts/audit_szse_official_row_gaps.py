"""Classify absent SZSE daily rows against dated official halt evidence."""

import argparse
import json
import warnings
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from scripts.audit_szse_official_daily_scope import CALENDAR_SHA, MASTER_SHA
from scripts.probe_szse_official_daily import HEADERS
from scripts.reconcile_sse_cninfo import canonical, save, sha

SOURCE_REPORT_SHA = "3edca545dd7b4173c7c95381bb68dd2bb5fd20769faf0930e17da7640edf84ea"


def classify(day: str, effective_to: str | None, events: list[tuple[str, str | None]]) -> str:
    if day == effective_to:
        return "MASTER_DELISTING_BOUNDARY_NO_ROW"
    if any(start <= day < end for start, end in events if end is not None):
        return "DATED_SOURCE_HALT_INTERVAL"
    if any(start <= day for start, end in events if end is None):
        return "UNKNOWN_RESUMPTION_NOT_CLOSED"
    return "NO_MATCHING_HALT_SOURCE"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--suspensions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    master_bytes, calendar_bytes = args.master.read_bytes(), args.calendar.read_bytes()
    if sha(master_bytes) != MASTER_SHA or sha(calendar_bytes) != CALENDAR_SHA:
        raise ValueError("ACCEPTED_MASTER_OR_CALENDAR_CHANGED")
    source_bytes = (args.source_root / "full-collection-report.json").read_bytes()
    if sha(source_bytes) != SOURCE_REPORT_SHA:
        raise ValueError("AUDITED_SOURCE_REPORT_CHANGED")
    source = json.loads(source_bytes)
    sessions = json.loads(calendar_bytes)["sessions"]
    if len(source["results"]) != len(sessions) or source["failure_manifest"]:
        raise ValueError("SOURCE_COLLECTION_INCOMPLETE")
    master = [
        r
        for r in json.loads(master_bytes)
        if r["exchange"] == "SZSE" and r["instrument_type"] == "COMMON_A_SHARE"
    ]
    suspension_bytes = args.suspensions.read_bytes()
    events = defaultdict(list)
    for event in json.loads(suspension_bytes)["szse"]:
        events[event["symbol"]].append(
            (event["suspended_at"][:10].replace("/", "-"), event.get("resumed_at"))
        )
    counts = Counter()
    unresolved = []
    by_symbol = Counter()
    by_year = Counter()
    for day, result in zip(sessions, source["results"], strict=True):
        if result["date"] != day:
            raise ValueError("SOURCE_DATE_ORDER_CHANGED")
        path = args.source_root / f"{day}.xlsx"
        raw = path.read_bytes()
        if sha(raw) != result["source_sha256"]:
            raise ValueError(f"SOURCE_BYTES_CHANGED:{day}")
        active = {
            row["symbol"]: row
            for row in master
            if row["effective_from"] <= day
            and (row["effective_to"] is None or day <= row["effective_to"])
        }
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            workbook = load_workbook(BytesIO(raw), read_only=True, data_only=True)
        sheet = workbook.active
        sheet.reset_dimensions()
        rows = sheet.values
        if tuple(next(rows)) != HEADERS:
            raise ValueError(f"SOURCE_COLUMNS_CHANGED:{day}")
        codes = {row[1] for row in rows}
        workbook.close()
        for symbol in sorted(active.keys() - codes):
            category = classify(day, active[symbol]["effective_to"], events[symbol])
            counts[category] += 1
            if category in {"UNKNOWN_RESUMPTION_NOT_CLOSED", "NO_MATCHING_HALT_SOURCE"}:
                unresolved.append(
                    {"security_id": active[symbol]["security_id"], "date": day, "reason": category}
                )
                by_symbol[symbol] += 1
                by_year[day[:4]] += 1
    report = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V1",
        "status": "PARTIAL_SOURCE_PRESENCE_NOT_RAW_AUTHORITY",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "master_sha256": MASTER_SHA,
        "calendar_sha256": CALENDAR_SHA,
        "source_collection_sha256": SOURCE_REPORT_SHA,
        "suspension_events_sha256": sha(suspension_bytes),
        "missing_rows": sum(counts.values()),
        "classification_counts": dict(sorted(counts.items())),
        "unresolved_rows": unresolved,
        "unresolved_symbols": dict(sorted(by_symbol.items())),
        "unresolved_by_year": dict(sorted(by_year.items())),
        "raw_authority_promoted": False,
    }
    report["manifest_sha256"] = sha(canonical(report))
    save(args.output, report)
    print(
        json.dumps(
            {
                key: report[key]
                for key in ("missing_rows", "classification_counts", "manifest_sha256")
            }
        )
    )


if __name__ == "__main__":
    main()
