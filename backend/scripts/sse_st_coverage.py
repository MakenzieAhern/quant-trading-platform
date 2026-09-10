"""Bounded pilot coverage audit; evidence gaps resolve to EXCLUDED, never NORMAL."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from scripts.reconcile_sse_cninfo import QUERY, STATIC, canonical, fetch, publication, save, sha
from scripts.sse_st_events import compact, extract, normalize, status

START, END = "2023-01-01", "2024-07-31"
LOOKBACK_FLOOR = 2020
STATES = {"NORMAL", "ST", "STAR_ST", "EXCLUDED"}


def header_state(pages: list[str], code: str, name: str) -> str:
    """A dated issuer-header observation, not an invented implementation event."""
    text = "\n".join(pages)[:1200]
    codes = re.findall(r"(?:证券|股票)代码\s*[\uff1a:]\s*([\d\s、,，]{6,55})", text)  # noqa: RUF001
    if not any(code in re.findall(r"(?<!\d)\d{6}(?!\d)", s) for s in codes):
        raise ValueError("HEADER_SECURITY_MISMATCH")
    short = compact(name)
    if not re.search(r"(?:证券|股票)简称[\uff1a:]" + re.escape(short), compact(text)):
        raise ValueError("HEADER_NAME_MISMATCH")
    return status(short)


def non_primary(record: dict[str, Any], pages: list[str]) -> tuple[str, str]:
    """Document-purpose rules, with body checks; classifications do not create transitions."""
    title = compact(record["sse"]["TITLE"])
    body = compact("\n".join(pages))
    if "申请" in title or "撤回" in title:
        return "APPLICATION_ONLY", "Application/withdrawal is not exchange implementation."
    if "进展" in title or "得到清偿" in title or "相关事项的进展公告" in body[:250]:
        return "PROGRESS_NOTICE", "Reports remediation progress, not a new effective transition."
    if "可能" in title or "股票交易风险提示" in title or "预计将于" in body[:1000]:
        return "NON_STATE_RISK_NOTICE", "Conditional risk warning, not definitive implementation."
    if "补充公告" in title and "2022年5月6日起被实施退市风险警示" in body:
        return "DUPLICATE_EVIDENCE", "Restates the already indexed implementation of 2022-05-06."
    if "2020年5月6日" in body and "2022年5月6日" in body:
        return (
            "CONFLICTING_EVIDENCE",
            "Original PDF explicitly states both 2020 and 2022 start dates.",
        )
    if "继续" in title and re.search(r"(?:继续|仍)[^。]{0,25}(?:风险警示|ST|简称)", body):
        return "STATUS_CONFIRMATION", "Confirms continuing warning; no new class change inferred."
    if "叠加" in title and status(record["sse"]["SECURITY_NAME"]) != "NORMAL":
        return "NO_EFFECTIVE_CHANGE", "Additional warning reason while the existing class remains."
    try:
        extract(pages, record)
    except ValueError as exc:
        return ("MISSING_EFFECTIVE_DATE" if "DATE" in str(exc) else "PARSER_FAILURE", str(exc))
    return "PARSER_FAILURE", "Previously unsupported syntax; now parsed with the current parser."


def replay(points: list[dict[str, Any]], day: str) -> str:
    """Observations are usable only on/after knowledge AND effective dates."""
    date.fromisoformat(day)
    eligible = [p for p in points if max(p["known_on"], p["effective_from"]) <= day]
    if not eligible:
        return "EXCLUDED"
    latest = max(p["effective_from"] for p in eligible)
    states = {p["status"] for p in eligible if p["effective_from"] == latest}
    return next(iter(states)) if len(states) == 1 and states <= STATES else "EXCLUDED"


def intervals_for(security: dict[str, str], points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compact last-known evidence intervals, explicitly NOT certified coverage."""
    start = max(START, security["listing_date"])
    end = min(END, security["delisting_date"] or END)
    if start > end:
        return []
    boundaries = sorted(
        {start}
        | {
            max(p["known_on"], p["effective_from"])
            for p in points
            if start < max(p["known_on"], p["effective_from"]) <= end
        }
    )
    result: list[dict[str, Any]] = []
    for index, day in enumerate(boundaries):
        stop = (
            (date.fromisoformat(boundaries[index + 1]) - timedelta(days=1)).isoformat()
            if index + 1 < len(boundaries)
            else end
        )
        state = replay(points, day)
        if result and result[-1]["evidence_status"] == state:
            result[-1]["effective_to"] = stop
        else:
            result.append(
                {
                    "security_id": security["security_id"],
                    "status": "EXCLUDED",
                    "evidence_status": state,
                    "effective_from": day,
                    "effective_to": stop,
                    "coverage_certified": False,
                }
            )
    return result


def status_on(intervals: list[dict[str, Any]], security_id: str, day: str) -> str:
    """Fail closed for missing, overlapping, invalid or uncertified coverage."""
    date.fromisoformat(day)
    rows = [
        r
        for r in intervals
        if r["security_id"] == security_id and r["effective_from"] <= day <= r["effective_to"]
    ]
    if len(rows) != 1 or not rows[0].get("coverage_certified"):
        return "EXCLUDED"
    value = rows[0]["status"]
    return str(value) if value in STATES else "EXCLUDED"


def assert_completeness(
    master: list[dict[str, str]], intervals: list[dict[str, Any]], sessions: list[str]
) -> dict[str, Any]:
    """Structural safety is separate from the material-exclusion acceptance gate."""
    if sessions != sorted(set(sessions)) or any(not START <= d <= END for d in sessions):
        raise ValueError("INVALID_PILOT_CALENDAR")
    identities = {s["security_id"] for s in master}
    if len(identities) != len(master) or any(r["security_id"] not in identities for r in intervals):
        raise ValueError("INVALID_MASTER_IDENTITY")
    by_id = {
        s: sorted(
            (r for r in intervals if r["security_id"] == s), key=lambda r: r["effective_from"]
        )
        for s in identities
    }
    excluded: Counter[str] = Counter()
    daily: list[dict[str, Any]] = []
    for day in sessions:
        eligible = [s for s in master if s["listing_date"] <= day <= (s["delisting_date"] or END)]
        count = 0
        for security in eligible:
            identity = security["security_id"]
            rows = by_id[identity]
            matches = [r for r in rows if r["effective_from"] <= day <= r["effective_to"]]
            if len(matches) != 1:
                raise ValueError("TIMELINE_GAP_OR_OVERLAP")
            state = status_on(rows, identity, day)
            if state not in STATES:
                raise ValueError("UNSAFE_STATUS")
            if state == "EXCLUDED":
                excluded[identity] += 1
                count += 1
        daily.append({"date": day, "eligible": len(eligible), "excluded": count})
    for rows in by_id.values():
        for previous, current in pairwise(rows):
            if (
                date.fromisoformat(previous["effective_to"]) + timedelta(days=1)
            ).isoformat() != current["effective_from"]:
                raise ValueError("TIMELINE_GAP_OR_OVERLAP")
    total = sum(r["eligible"] for r in daily)
    return {
        "eligible_security_days": total,
        "excluded_security_days": sum(excluded.values()),
        "excluded_security_count": len(excluded),
        "excluded_security_days_by_id": dict(excluded),
        "excluded_security_day_percentage": 100 * sum(excluded.values()) / total if total else 0,
        "daily": daily,
        "timeline_gaps": 0,
        "timeline_overlaps": 0,
    }


def audit(source: Path, output: Path, master_path: Path, calendar_path: Path) -> None:
    """Offline evidence closure; no absence-of-disclosure => NORMAL assumption."""
    records = json.loads((source / "reconciliation.json").read_bytes())
    originals = {
        r["sse_id"] for r in json.loads((source / "unresolved-documents.json").read_bytes())
    }
    candidates = json.loads((source / "candidate-classifications.json").read_bytes())
    targeted = json.loads((output / "targeted-baselines.json").read_bytes())
    master = list(csv.DictReader(master_path.open()))
    sessions = json.loads(calendar_path.read_bytes())
    events, documents, observations = [], [], []
    for record in records:
        cn = record["cninfo"][0]
        raw = (source / "documents" / (cn["announcementId"] + ".pdf")).read_bytes()
        if sha(raw) != record["cninfo_document_sha256"]:
            raise ValueError("DOCUMENT_CHECKSUM_MISMATCH")
        pages = [p.extract_text() for p in PdfReader(io.BytesIO(raw)).pages]
        event = None
        try:
            event = extract(pages, record)
            events.append(event)
        except ValueError:
            pass
        if record["sse"]["ORG_BULLETIN_ID"] in originals:
            category, reason = non_primary(record, pages)
            documents.append(
                {
                    "security_id": "CN-A:SSE:" + cn["secCode"],
                    "document_id": cn["announcementId"],
                    "sha256": sha(raw),
                    "classification": category,
                    "reason": reason,
                    "publication_date": publication(cn),
                    "resolved_by_parser_fix": event is not None,
                    "potential_blocker": event is None
                    and category
                    in {"MISSING_EFFECTIVE_DATE", "PARSER_FAILURE", "CONFLICTING_EVIDENCE"},
                    "body_sha256": sha(canonical(pages)),
                    "support_excerpt": compact("\n".join(pages))[:1500],
                }
            )
            # A header is an observation on publication, never a retroactive event.
            try:
                state = header_state(pages, cn["secCode"], record["sse"]["SECURITY_NAME"])
            except ValueError:
                continue
            observations.append(
                {
                    "security_id": "CN-A:SSE:" + cn["secCode"],
                    "status": state,
                    "known_on": publication(cn),
                    "effective_from": publication(cn),
                    "document_id": cn["announcementId"],
                    "sha256": sha(raw),
                    "kind": "ISSUER_HEADER_OBSERVATION",
                }
            )
    for row in targeted:
        if row["status"] == "EXCLUDED":
            continue
        if row["known_on"] >= START:
            raise ValueError("FUTURE_BASELINE_REJECTED")
        identity = row["cninfo"]["announcementId"]
        paths = [
            output / "targeted/documents" / (identity + ".pdf"),
            output / "targeted-repair/targeted/documents" / (identity + ".pdf"),
        ]
        path = next(p for p in paths if p.exists())
        raw = path.read_bytes()
        if sha(raw) != row["document_sha256"]:
            raise ValueError("TARGETED_CHECKSUM_MISMATCH")
        pages = [p.extract_text() for p in PdfReader(io.BytesIO(raw)).pages]
        if header_state(pages, row["cninfo"]["secCode"], row["cninfo"]["secName"]) != row["status"]:
            raise ValueError("TARGETED_HEADER_MISMATCH")
        observations.append(
            {
                "security_id": row["security_id"],
                "status": row["status"],
                "known_on": row["known_on"],
                "effective_from": row["known_on"],
                "document_id": identity,
                "sha256": sha(raw),
                "kind": row["kind"],
            }
        )
    events = normalize(events)
    points = observations + [
        {
            "security_id": e["security_id"],
            "status": e["status"],
            "known_on": max(e["sse_publication_date"], e["cninfo_publication_date"]),
            "effective_from": e["effective_from"],
            "document_id": e["cninfo_document_id"],
            "sha256": e["cninfo_document_sha256"],
            "kind": "EXPLICIT_EFFECTIVE_EVENT",
        }
        for e in events
    ]
    points.sort(
        key=lambda p: (p["security_id"], p["effective_from"], p["known_on"], p["document_id"])
    )
    table, intervals = [], []
    reason = (
        "No certified exhaustive baseline/transition coverage: dated state observations "
        "and selected risk-warning disclosures do not prove absence of omitted changes."
    )
    for security in master:
        history = [p for p in points if p["security_id"] == security["security_id"]]
        built = intervals_for(security, history)
        if built != intervals_for(security, list(reversed(history))):
            raise ValueError("INPUT_ORDER_DEPENDENCY")
        intervals.extend(built)
        if security["security_id"] not in {c["security_id"] for c in candidates}:
            continue
        before = [p for p in history if max(p["known_on"], p["effective_from"]) < START]
        after = [p for p in history if max(p["known_on"], p["effective_from"]) > END]
        baseline = replay(before, START)
        if baseline != replay(history, START):
            raise ValueError("FUTURE_BASELINE_LEAKAGE")
        table.append(
            {
                "security_id": security["security_id"],
                "symbol": security["symbol"],
                "classification": "CONSERVATIVELY_EXCLUDED",
                "status_on_2023_01_01": "EXCLUDED",
                "last_known_state_not_coverage_certified": baseline,
                "events_during_pilot": [
                    e
                    for e in events
                    if e["security_id"] == security["security_id"]
                    and START <= e["effective_from"] <= END
                ],
                "last_pre_pilot_evidence": before[-1] if before else None,
                "first_post_pilot_evidence_if_relevant": after[0] if after else None,
                "evidence_document_ids": sorted({p["document_id"] for p in history}),
                "evidence_sha256s": sorted({p["sha256"] for p in history}),
                "confidence": "DATED_EVIDENCE_ONLY_NOT_COMPLETE_COVERAGE",
                "reason": reason,
                "missing_predecessor": None
                if before
                else "No validated pre-2023 issuer state; exact missing document identity unknown.",
            }
        )
    if len(table) != len(candidates):
        raise ValueError("CANDIDATE_DISAPPEARED")
    intervals.sort(key=lambda r: (r["security_id"], r["effective_from"]))
    metrics = assert_completeness(master, intervals, sessions)
    pilot = [e for e in events if START <= e["effective_from"] <= END]
    risk = {r["security_id"] for r in intervals if r["evidence_status"] in {"ST", "STAR_ST"}}
    delisted = {
        s["security_id"] for s in master if s["delisting_date"] and s["delisting_date"] <= END
    }
    summary = {
        "master_securities": len(master),
        "candidates": len(table),
        "trading_sessions": len(sessions),
        "candidate_classifications": dict(Counter(r["classification"] for r in table)),
        "pilot_start_states": {
            "NORMAL": 0,
            "ST": 0,
            "STAR_ST": 0,
            "EXCLUDED": len(table),
            "UNKNOWN": 0,
        },
        "last_known_candidate_baseline_not_certified": dict(
            Counter(r["last_known_state_not_coverage_certified"] for r in table)
        ),
        "non_primary_documents": dict(Counter(r["classification"] for r in documents)),
        "parser_failures_fixed": sum(r["resolved_by_parser_fix"] for r in documents),
        "potential_document_blockers": [
            r["document_id"] for r in documents if r["potential_blocker"]
        ],
        "normalized_events": len(events),
        "all_event_types": dict(Counter(e["event_type"] for e in events)),
        "pilot_event_types": dict(Counter(e["event_type"] for e in pilot)),
        "pilot_entries_by_state": dict(
            Counter(e["status"] for e in pilot if e["event_type"] == "ENTRY")
        ),
        "pilot_removals_by_state": dict(
            Counter(e["old_status"] for e in pilot if e["event_type"] == "EXIT")
        ),
        "evidence_risk_securities_lower_bound": len(risk),
        "retained_delisted_securities": len(delisted),
        "excluded_risk_securities": len(risk),
        "excluded_delisted_securities": len(delisted),
        "exclusion_materiality": (
            "FAIL: entire universe excluded; uniform 100% daily exclusion, "
            "not selective ST/delisting attrition. No strategy-dependent threshold."
        ),
        "acceptance_rationale": (
            "Require certified coverage or evidence demonstrating residual exclusions "
            "immaterial; observation-only coverage cannot qualify."
        ),
        "structural_completeness": "PASS",
        "PILOT_START_STATUS": "PARTIAL",
        "ENTRY_EFFECTIVE_DATE": "PASS_FOR_ACCEPTED_EVENTS_ONLY",
        "EXIT_EFFECTIVE_DATE": "PASS_FOR_ACCEPTED_EVENTS_ONLY",
        "DELISTED_RETENTION": "PASS",
        "FUTURE_EVENT_LEAKAGE": "PASS",
        "INPUT_ORDER_REPRODUCIBILITY": "PASS",
        "SSE_HISTORICAL_ST_RECONSTRUCTION": "PARTIAL",
        "PILOT_A_SHARE_DATA_READINESS": "BLOCKED",
        "pilot_dataset_created": False,
        "security_master_sha256": sha(master_path.read_bytes()),
        "st_event_sha256": sha(canonical(events)),
        "calendar_sha256": sha(calendar_path.read_bytes()),
        "interval_count": len(intervals),
        "unresolved_underlying_intervals": len(intervals),
        "excluded_universe_percentage": 100 * metrics["excluded_security_count"] / len(master),
        **metrics,
    }
    for name, value in {
        "candidate-audit": table,
        "non-primary-audit": documents,
        "normalized-events": events,
        "dated-evidence": points,
        "status-intervals": intervals,
        "coverage-summary": summary,
    }.items():
        save(output / (name + ".json"), value)
    manifest = [
        {"path": p.relative_to(output).as_posix(), "sha256": sha(p.read_bytes())}
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "audit-manifest.json"
    ]
    save(
        output / "audit-manifest.json",
        {"files": manifest, "manifest_sha256": sha(canonical(manifest))},
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in summary.items()
                if k not in {"daily", "excluded_security_days_by_id"}
            },
            indent=2,
        )
    )


def targeted_baseline(code: str, name: str, org: str | None, output: Path) -> dict[str, Any]:
    """Look backward for one unresolved issuer only; never use post-pilot content."""
    scanned = []
    for year in range(2022, LOOKBACK_FLOOR - 1, -1):
        params: dict[str, object] = {
            "pageNum": 1,
            "pageSize": 30,
            "column": "sse",
            "tabName": "fulltext",
            "stock": f"{code},{org}" if org else "",
            "searchkey": "" if org else name,
            "secid": "",
            "plate": "",
            "category": "",
            "trade": "",
            "seDate": f"{year}-01-01~{year}-12-31",
            "sortName": "",
            "sortType": "",
            "isHLtitle": "false",
        }
        raw = fetch(output, f"targeted/{code}-{year}-p001.json", QUERY, params)
        payload = json.loads(raw)
        scanned.append({"year": year, "metadata_sha256": sha(raw)})
        rows = sorted(
            (r for r in payload.get("announcements") or [] if r["secCode"] == code),
            key=lambda r: (publication(r), r["announcementId"]),
            reverse=True,
        )
        # Inspect newest-first. Never step past a potential transition without resolving it.
        if not rows:
            continue
        newest = publication(rows[0])
        if newest >= START:
            raise ValueError("FUTURE_BASELINE_REJECTED")
        for cn in rows:
            path = cn["adjunctUrl"]
            if not re.fullmatch(r"finalpage/\d{4}-\d{2}-\d{2}/\d+\.PDF", path):
                continue
            pdf = fetch(output, f"targeted/documents/{cn['announcementId']}.pdf", STATIC + path)
            if not pdf.startswith(b"%PDF"):
                raise ValueError("NON_PDF_RESPONSE")
            pages = [p.extract_text() for p in PdfReader(io.BytesIO(pdf)).pages]
            save(output / "targeted/text" / (cn["announcementId"] + ".json"), pages)
            try:
                state = header_state(pages, code, cn["secName"])
            except ValueError:
                if "风险警示" in cn["announcementTitle"]:
                    break
                continue
            return {
                "security_id": "CN-A:SSE:" + code,
                "status": state,
                "known_on": publication(cn),
                "kind": "CNINFO_ISSUER_HEADER_OBSERVATION",
                "cninfo": cn,
                "document_sha256": sha(pdf),
                "metadata_sha256": sha(raw),
                "scanned": scanned,
                "coverage_certified": False,
                "reason": (
                    "Issuer state observation only; does not prove absence of later transitions."
                ),
            }
        return {
            "security_id": "CN-A:SSE:" + code,
            "status": "EXCLUDED",
            "scanned": scanned,
            "reason": "Newest pre-pilot disclosure has no validated matching issuer header.",
        }
    return {
        "security_id": "CN-A:SSE:" + code,
        "status": "EXCLUDED",
        "scanned": scanned,
        "reason": f"No validated predecessor by bounded historical floor {LOOKBACK_FLOOR}-01-01.",
    }


def acquire(source: Path, output: Path, snapshot: Path | None = None, repair: bool = False) -> None:
    classes = json.loads((source / "candidate-classifications.json").read_bytes())
    records = json.loads((source / "reconciliation.json").read_bytes())
    orgs = {}
    if snapshot:
        for path in sorted((snapshot / "metadata").glob("*.json")):
            for group in json.loads(path.read_bytes())["pageHelp"]["data"]:
                for row in group:
                    orgs[row["SECURITY_CODE"]] = (row["SECURITY_NAME"], None)
    for path in sorted((source / "metadata").glob("*.json")):
        if path.name.endswith(".meta.json"):
            continue
        for cn in json.loads(path.read_bytes()).get("announcements") or []:
            orgs[cn["secCode"]] = (cn["secName"], cn["orgId"])
    for record in records:
        cn = record["cninfo"][0]
        orgs[cn["secCode"]] = (cn["secName"], cn["orgId"])
    selected = [c for c in classes if c["last_known_pilot_start_status"] == "UNKNOWN"]
    results = {}
    checkpoint = output / "targeted-baselines.json"
    if checkpoint.exists():
        results = {r["security_id"]: r for r in json.loads(checkpoint.read_bytes())}
    if repair and not (output / "targeted-baselines-before-repair.json").exists():
        save(output / "targeted-baselines-before-repair.json", list(results.values()))
    with ThreadPoolExecutor(max_workers=4) as pool:
        pending = {}
        for candidate in selected:
            identity = candidate["security_id"]
            if identity in results and (not repair or results[identity]["status"] != "EXCLUDED"):
                continue
            code = identity[-6:]
            name, org = orgs.get(code, (code, None))
            lookup_root = output / "targeted-repair" if repair else output
            pending[pool.submit(targeted_baseline, code, name, org, lookup_root)] = identity
        for future in as_completed(pending):
            identity = pending[future]
            try:
                results[identity] = future.result()
            except (OSError, ValueError, RuntimeError) as exc:
                results[identity] = {
                    "security_id": identity,
                    "status": "EXCLUDED",
                    "reason": type(exc).__name__,
                    "lookup_failed": True,
                }
            save(checkpoint, [results[k] for k in sorted(results)])
            print(f"targeted predecessor audits={len(results)}/{len(selected)}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sse-snapshot", type=Path)
    parser.add_argument("--repair", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--master", type=Path)
    parser.add_argument("--calendar", type=Path)
    args = parser.parse_args()
    if args.audit:
        if not args.master or not args.calendar:
            parser.error("--audit requires --master and --calendar")
        audit(args.source, args.output, args.master, args.calendar)
    else:
        acquire(args.source, args.output, args.sse_snapshot, args.repair)
