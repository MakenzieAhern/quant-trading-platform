"""Offline audit of the official dated SZSE abbreviation-change export."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from openpyxl import load_workbook  # type: ignore[import-untyped]
from pypdf import PdfReader

from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.sse_st_coverage import END, START
from scripts.sse_st_events import compact, status

VERSION = "szse-dated-abbreviation-v1"


def risk_state(name: str) -> str:
    name = compact(name)
    if name.startswith("退市") or name.endswith("退"):
        return "DELISTING_PERIOD"
    if name.startswith("PT"):
        return "UNKNOWN"
    return status(name)


def normalize(rows: list[tuple[Any, ...]], allowed_symbols: set[str]) -> list[dict[str, str]]:
    """Current-name column is deliberately ignored; only dated before/after values count."""
    result: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        if len(row) != 5 or not all(isinstance(v, str) and v.strip() for v in row):
            raise ValueError("INVALID_CHANGE_ROW")
        day, symbol, _current, old, new = row
        if date.fromisoformat(day).isoformat() != day:
            raise ValueError("NON_CANONICAL_DATE")
        if not re.fullmatch(r"\d{6}", symbol):
            raise ValueError("INVALID_SECURITY_CODE")
        if symbol not in allowed_symbols:
            continue  # Raw export retains B shares and securities outside the pilot master.
        event = dict(
            security_id=f"CN-A:SZSE:{symbol}",
            symbol=symbol,
            effective_from=day,
            old_name=compact(old),
            new_name=compact(new),
            old_status=risk_state(old),
            status=risk_state(new),
        )
        key = symbol, day
        if key in result and result[key] != event:
            raise ValueError("CONFLICTING_SAME_DAY_CHANGE")
        result[key] = event
    return [result[k] for k in sorted(result)]


def status_on(anchor: dict[str, str], events: list[dict[str, str]], day: str) -> str:
    """Effective-state reconstruction, not a claim of historical publication timestamps."""
    date.fromisoformat(day)
    if anchor["status"] not in {"NORMAL", "ST", "STAR_ST", "DELISTING_PERIOD", "UNKNOWN"}:
        raise ValueError("INVALID_ANCHOR_STATE")
    if day < anchor["effective_from"]:
        return "UNKNOWN"
    state = anchor["status"]
    for event in sorted(events, key=lambda e: (e["effective_from"], canonical(e))):
        if event["effective_from"] == anchor["effective_from"] and event["status"] != state:
            return "UNKNOWN"
        if anchor["effective_from"] < event["effective_from"] <= day:
            if event["old_status"] != state:
                return "UNKNOWN"
            state = event["status"]
    return state


def audit(source: Path, master_root: Path, calendar: Path, output: Path) -> dict[str, Any]:
    raw = source.read_bytes()
    metadata = json.loads(source.with_suffix(source.suffix + ".meta.json").read_bytes())
    if sha(raw) != metadata["sha256"]:
        raise ValueError("SOURCE_CHECKSUM_MISMATCH")
    if metadata["source_url"] != (
        "https://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=SSGSGMXX&TABKEY=tab2"
    ):
        raise ValueError("UNACCEPTED_SOURCE_IDENTITY")
    book = load_workbook(source, read_only=True, data_only=True)
    sheet = book["简称变更"]
    # SZSE declares A1:A1 despite thousands of XML rows. Never trust that dimension.
    sheet.reset_dimensions()
    rows = list(sheet.values)
    book.close()
    if rows[0] != ("变更日期", "证券代码", "证券简称", "变更前简称", "变更后简称"):
        raise ValueError("SOURCE_SCHEMA_CHANGED")
    source_manifest = json.loads((master_root / "source-snapshot-manifest.json").read_bytes())
    pdf = master_root / "raw/szse-yearbook-2022.pdf"
    pdf_record = next(
        s for s in source_manifest["snapshots"] if s["raw_snapshot_filename"] == pdf.name
    )
    if sha(pdf.read_bytes()) != pdf_record["sha256"]:
        raise ValueError("BASELINE_CHECKSUM_MISMATCH")
    master_path = master_root / "szse-security-master.csv"
    master_manifest = json.loads((master_root / "security-master-input.json").read_bytes())
    master_record = next(r for r in master_manifest["sources"] if r["source"] == "SZSE_OFFICIAL")
    if not master_record["complete"] or sha(master_path.read_bytes()) != master_record["sha256"]:
        raise ValueError("MASTER_CHECKSUM_MISMATCH")
    master = list(csv.DictReader(master_path.open()))
    ids = {s["symbol"] for s in master}
    if len(ids) != len(master) or any(
        s["security_id"] != f"CN-A:SZSE:{s['symbol']}" for s in master
    ):
        raise ValueError("INVALID_MASTER_IDENTITY")
    events = normalize(rows[1:], ids)
    order_ok = events == normalize(list(reversed(rows[1:])), ids)
    reader = PdfReader(pdf)
    anchors = {}
    collecting = False
    for index in range(len(reader.pages) - 160, len(reader.pages)):
        text = reader.pages[index].extract_text() or ""
        if "NAMELIST OF LISTED COMPANIES" in text:
            collecting = True
        if collecting and (
            "ADDRESS LIST OF LISTED COMPANIES" in text or "公司全称\nCOMPANY\n地址\nADDRESS" in text
        ):
            break
        if collecting:
            for code, name in re.findall(r"(?m)^(\d{6})\s+(\S+)", text):
                if code in ids:
                    anchors[code] = dict(
                        status=risk_state(name),
                        effective_from="2022-12-31",
                        source_page=str(index + 1),
                        name=name,
                    )
    eligible_start = {s["symbol"] for s in master if s["listing_date"] < START}
    missing_anchors = sorted(eligible_start - anchors.keys())
    sessions = json.loads(calendar.read_bytes())
    if (
        not sessions
        or sessions != sorted(set(sessions))
        or any(not START <= d <= END for d in sessions)
    ):
        raise ValueError("INVALID_CALENDAR")
    timelines, gaps, anchor_conflicts = [], [], []
    unknown = 0
    leakage_ok = True
    day_counts: Counter[str] = Counter()
    pilot_events = [e for e in events if e["symbol"] in ids and START <= e["effective_from"] <= END]
    by_code = {s["symbol"]: s for s in master}
    boundary_errors = [
        e
        for e in pilot_events
        if not (
            by_code[e["symbol"]]["listing_date"]
            <= e["effective_from"]
            <= (by_code[e["symbol"]]["delisting_date"] or END)
        )
    ]
    non_session_events = [e for e in pilot_events if e["effective_from"] not in sessions]
    for security in sorted(master, key=lambda s: s["security_id"]):
        code = security["symbol"]
        anchor = anchors.get(
            code,
            dict(
                status="NORMAL" if security["listing_date"] >= START else "UNKNOWN",
                effective_from=security["listing_date"],
            ),
        )
        history = [e for e in events if e["symbol"] == code]
        before = [e for e in history if e["effective_from"] <= "2022-12-31"]
        if before and code in anchors and before[-1]["status"] != anchor["status"]:
            anchor_conflicts.append(code)
        days = [
            d
            for d in sessions
            if security["listing_date"] <= d <= (security["delisting_date"] or END)
        ]
        states = [(d, status_on(anchor, history, d)) for d in days]
        # ponytail: bounded direct replay; index timelines if the research window expands.
        without_future = [e for e in history if e["effective_from"] <= END]
        leakage_ok &= states == [(d, status_on(anchor, without_future, d)) for d in days]
        order_ok &= states == [(d, status_on(anchor, list(reversed(history)), d)) for d in days]
        if any(state == "UNKNOWN" for _, state in states):
            gaps.append(code)
        unknown += sum(state == "UNKNOWN" for _, state in states)
        day_counts.update(state for _, state in states)
        timelines.append(
            dict(
                security_id=security["security_id"],
                anchor=anchor,
                pilot_events=[e for e in history if START <= e["effective_from"] <= END],
                unknown_security_days=sum(state == "UNKNOWN" for _, state in states),
            )
        )
    complete = (
        not missing_anchors
        and not gaps
        and not anchor_conflicts
        and order_ok
        and leakage_ok
        and not boundary_errors
        and not non_session_events
    )
    summary = dict(
        parser_version=VERSION,
        source_rows=len(rows) - 1,
        normalized_name_events=len(events),
        source_date_min=min(e["effective_from"] for e in events),
        source_date_max=max(e["effective_from"] for e in events),
        master_securities=len(master),
        anchor_securities=len(anchors),
        pilot_name_events=len(pilot_events),
        pilot_risk_changes=sum(e["status"] != e["old_status"] for e in pilot_events),
        missing_anchors=missing_anchors,
        chain_gap_securities=gaps,
        anchor_conflicts=anchor_conflicts,
        unknown_security_days=unknown,
        boundary_errors=boundary_errors,
        non_session_events=non_session_events,
        state_security_days=dict(day_counts),
        SZSE_ST_AUTHORITY_FOUND="YES" if complete else "NO",
        SZSE_PILOT_START_STATUS="PASS"
        if not missing_anchors and not anchor_conflicts
        else "PARTIAL",
        SZSE_ENTRY_EFFECTIVE_DATE="PASS" if complete else "PARTIAL",
        SZSE_EXIT_EFFECTIVE_DATE="PASS" if complete else "PARTIAL",
        SZSE_FUTURE_EVENT_LEAKAGE="PASS" if leakage_ok else "FAIL",
        SZSE_DELISTED_RETENTION="PASS" if not boundary_errors else "FAIL",
        SZSE_INPUT_ORDER_REPRODUCIBILITY="PASS" if order_ok else "FAIL",
        SZSE_HISTORICAL_ST_FOR_PILOT="PASS" if complete else "PARTIAL",
        source_sha256=sha(raw),
        event_sha256=sha(canonical(events)),
        master_sha256=sha(master_path.read_bytes()),
        baseline_sha256=sha(pdf.read_bytes()),
        publication_timestamps="UNKNOWN; change dates are effective dates, not publication dates",
        scope="SZSE_ST_ONLY_NOT_DATASET_PUBLICATION",
        calendar_sha256=sha(calendar.read_bytes()),
    )
    save(output / "normalized-name-events.json", events)
    risk_events = [e for e in events if e["old_status"] != e["status"]]
    summary["risk_event_sha256"] = sha(canonical(risk_events))
    save(output / "normalized-st-events.json", risk_events)
    save(output / "security-timelines.json", timelines)
    save(output / "audit-summary.json", summary)
    manifest = dict(
        parser_version=VERSION,
        sources=[dict(metadata, raw_snapshot_filename=source.name), pdf_record],
        files=[
            dict(path=p.name, sha256=sha(p.read_bytes()))
            for p in sorted(output.glob("*.json"))
            if p.name != "manifest.json"
        ],
    )
    save(output / "manifest.json", dict(manifest, manifest_sha256=sha(canonical(manifest))))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--master-root", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args.source, args.master_root, args.calendar, args.output)
