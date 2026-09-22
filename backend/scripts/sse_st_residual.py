"""Residual-only, source-linked coverage dispositions; never infer dates from names."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.sse_st_closure import name_key
from scripts.sse_st_coverage import (
    END,
    START,
    assert_completeness,
    header_state,
    intervals_for,
    replay,
)
from scripts.sse_st_events import extract


def token_disposition(
    token: str,
    history: list[dict[str, Any]],
    anchor: dict[str, Any],
    observations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Bound old/future names with official evidence, not the oracle's ordering."""
    key = name_key(token)
    matching = [e for e in history if key in (name_key(e["old_name"]), name_key(e["new_name"]))]
    relevant = [e for e in matching if START <= e["effective_from"] <= END]
    if relevant or name_key(anchor["name"]) == key:
        return {
            "classification": "EXPLAINED_BY_OFFICIAL_EVENT",
            "reason": "Official anchor and pilot replay; no invented exit for an active end state.",
            "documents": sorted({e["cninfo_document_id"] for e in relevant}),
            "anchor_supported": name_key(anchor["name"]) == key,
        }
    before = [e for e in matching if e["effective_from"] < START]
    old_names = [o for o in observations if o["name_key"] == key and o["date"] < START]
    after = [e for e in matching if e["effective_from"] > END and name_key(e["new_name"]) == key]
    future_boundaries = [
        o
        for o in observations
        if o["name_key"] == key and o["date"] > END and o.get("boundary_kind") == "POST_PILOT_ENTRY"
    ]
    if before or old_names or after or future_boundaries:
        return {
            "classification": "EVENT_OUTSIDE_RELEVANT_PERIOD",
            "reason": (
                "Dated pre-anchor name differs from anchor, or explicit post-pilot entry; "
                "no matching pilot transition."
            ),
            "documents": sorted({e["cninfo_document_id"] for e in before + after}),
            "observations": old_names + future_boundaries,
            "post_pilot_dates": sorted({e["effective_from"] for e in after}),
            "anchor_name": anchor["name"],
        }
    return {
        "classification": "UNRESOLVED",
        "reason": "No dated issuer-specific boundary for this exact risk-name token.",
    }


def source_observations(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Read saved issuer headers; a different company's body mention is not evidence."""
    observations, reparsed = [], []
    for directory, filename in (
        ("closure-20260910", "additional-parser-audit.json"),
        ("cninfo-20260910", "reconciliation.json"),
    ):
        base = root / directory
        for record in json.loads((base / filename).read_bytes()):
            if record["match_confidence"] != "EXACT":
                continue
            cn = record["cninfo"][0]
            document = cn["announcementId"]
            path = base / "text" / (document + ".json")
            if not path.exists():
                continue
            raw = base / "documents" / (document + ".pdf")
            if sha(raw.read_bytes()) != record["cninfo_document_sha256"]:
                raise ValueError("SOURCE_DOCUMENT_CHECKSUM_MISMATCH")
            pages = json.loads(path.read_bytes())
            for name in sorted({record["sse"].get("SECURITY_NAME"), cn.get("secName")} - {None}):
                try:
                    header_state(pages, cn["secCode"], name)
                except ValueError:
                    continue
                observations.append(
                    {
                        "symbol": cn["secCode"],
                        "name_key": name_key(name),
                        "date": record["sse"]["SSEDATE"],
                        "document": document,
                        "sha256": record["cninfo_document_sha256"],
                    }
                )
            try:
                event = extract(pages, record)
            except ValueError:
                continue
            reparsed.append(event)
    return observations, reparsed


def residual(root: Path, output: Path) -> list[dict[str, Any]]:
    control_rows = controls(root, output)  # Required first, not silently skipped.
    control_map = {r["symbol"]: r for r in control_rows}
    previous = root / "closure-20260910"
    names = json.loads((previous / "name-crosscheck.json").read_bytes())
    events = json.loads((previous / "combined-normalized-events.json").read_bytes())
    observed, reparsed = source_observations(root)
    for review in json.loads((output / "reviewed-token-boundaries.json").read_bytes()):
        path = root / review["source"]
        meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
        if sha(path.read_bytes()) != meta["sha256"]:
            raise ValueError("REVIEW_SOURCE_CHECKSUM_MISMATCH")
        page = json.loads((root / review["text"]).read_bytes())[review["page"] - 1]
        for token in review["tokens"]:
            if name_key(token) not in re.sub(r"\s+", "", page).translate(
                str.maketrans("\u2217\uff0a\ufe61", "***")
            ):
                raise ValueError("REVIEW_TOKEN_NOT_IN_SOURCE_PAGE")
            observed.append(
                {
                    **review,
                    "name_key": name_key(token),
                    "document": meta["url"],
                    "sha256": meta["sha256"],
                }
            )
    for row in json.loads((output / "targeted-documents.json").read_bytes()):
        if "error" in row:
            continue
        cn = row["record"]
        if sha((root / row["path"]).read_bytes()) != row["sha256"]:
            raise ValueError("TARGET_DOCUMENT_CHECKSUM_MISMATCH")
        pages = json.loads((output / "text" / (cn["announcementId"] + ".json")).read_bytes())
        try:
            header_state(pages, cn["secCode"], cn["secName"])
        except ValueError:
            continue
        observed.append(
            {
                "symbol": cn["secCode"],
                "name_key": name_key(cn["secName"]),
                "date": row["date"],
                "document": cn["announcementId"],
                "sha256": row["sha256"],
            }
        )
    by_document = {e["cninfo_document_id"]: e for e in events}
    by_document.update({e["cninfo_document_id"]: e for e in reparsed})
    events = list(by_document.values())
    anchors = json.loads((previous / "pilot-start-anchor.json").read_bytes())
    # Official historical security-name list, used only for pre-pilot boundaries.
    source = output / "historical/sse-industry-20060606.html"
    raw = source.read_bytes()
    metadata = json.loads(source.with_suffix(".html.meta.json").read_bytes())
    if sha(raw) != metadata["sha256"]:
        raise ValueError("HISTORICAL_LIST_CHECKSUM_MISMATCH")
    cells = [
        re.sub(r"\s+", "", html.unescape(re.sub("<[^>]+>", "", s)))
        for s in re.findall(r"<td\b[^>]*>(.*?)</td>", raw.decode(), re.S | re.I)
    ]
    for index, cell in enumerate(cells[:-1]):
        if re.fullmatch(r"\d{6}", cell):
            observed.append(
                {
                    "symbol": cell,
                    "name_key": name_key(cells[index + 1]),
                    "date": "2006-06-06",
                    "document": metadata["url"],
                    "sha256": metadata["sha256"],
                }
            )
    for relative, page_number, as_of in (
        ("controls/sse-factbook-2001", 56, "2001-12-31"),
        ("historical/sse-yearbook-2007", 173, "2006-12-31"),
    ):
        pdf = output / (relative + ".pdf")
        meta = json.loads(pdf.with_suffix(".pdf.meta.json").read_bytes())
        if sha(pdf.read_bytes()) != meta["sha256"]:
            raise ValueError("HISTORICAL_TABLE_CHECKSUM_MISMATCH")
        page = json.loads((output / (relative + "-text.json")).read_bytes())[page_number - 1]
        for code, name in re.findall(r"(?m)^(6\d{5})\s+([S*STPT\u4e00-\u9fff ]+?)\s+\d{4}", page):
            observed.append(
                {
                    "symbol": code,
                    "name_key": name_key(name),
                    "date": as_of,
                    "document": meta["url"],
                    "sha256": meta["sha256"],
                    "page": page_number,
                }
            )
    observed.sort(key=canonical)
    result = []
    for row in sorted(
        (r for r in names if r["unexplained"]), key=lambda r: (not r["is_control"], r["symbol"])
    ):
        code = row["symbol"]
        if code in control_map:
            result.append({**control_map[code], "is_control": True})
            continue
        history = [e for e in events if e["symbol"] == code]
        tokens = [
            {
                "token": t["token"],
                "status": t["status"],
                **token_disposition(
                    t["token"], history, anchors[code], [o for o in observed if o["symbol"] == code]
                ),
            }
            for t in row["tokens"]
        ]
        classifications = {t["classification"] for t in tokens}
        classification = (
            "UNRESOLVED"
            if "UNRESOLVED" in classifications
            else "EXPLAINED_BY_OFFICIAL_EVENT"
            if "EXPLAINED_BY_OFFICIAL_EVENT" in classifications
            else "EVENT_OUTSIDE_RELEVANT_PERIOD"
        )
        result.append(
            {
                "security_id": row["security_id"],
                "symbol": code,
                "is_control": False,
                "classification": classification,
                "tokens": tokens,
            }
        )
    if len(result) != 93:
        raise ValueError("RESIDUAL_SET_MISMATCH")
    save(output / "residual-terminal-audit.json", result)
    save(output / "issuer-name-observations.json", observed)
    save(
        output / "combined-events.json",
        sorted(
            events, key=lambda e: (e["security_id"], e["effective_from"], e["cninfo_document_id"])
        ),
    )
    print(dict(Counter(r["classification"] for r in result)))
    return result


def anchor_closes_ancient_gap(
    anchor: dict[str, Any],
    unresolved_before: str | None,
    history: list[dict[str, Any]],
    contradictions: list[str],
    coverage_complete: bool,
) -> bool:
    """Reset only reviewed pre-anchor uncertainty, never an undated arbitrary gap."""
    if (
        not unresolved_before
        or not anchor.get("authoritative")
        or not anchor.get("complete_for_security")
        or anchor.get("status") not in {"NORMAL", "ST", "STAR_ST"}
        or not unresolved_before < anchor["effective_from"] < START
        or anchor["known_on"] > anchor["effective_from"]
        or contradictions
        or not coverage_complete
    ):
        return False
    state = anchor["status"]
    for event in sorted(history, key=lambda e: (e["effective_from"], canonical(e))):
        if event["effective_from"] == anchor["effective_from"] and event["status"] != state:
            return False
        if anchor["effective_from"] < event["effective_from"] <= END:
            if (
                event["old_status"] != state
                or max(event["sse_publication_date"], event["cninfo_publication_date"])
                > event["effective_from"]
            ):
                return False
            state = event["status"]
    return True


def pilot_review(root: Path, source: Path, events: list[dict[str, Any]]) -> dict[str, Any]:
    """600721's reviewed ancient anomaly; no automatic waiver for other tokens."""
    previous = root / "closure-20260910"
    for directory, filename in (
        (source, "residual-manifest.json"),
        (previous, "closure-manifest.json"),
    ):
        manifest = json.loads((directory / filename).read_bytes())
        for entry in manifest["files"]:
            if sha((directory / entry["path"]).read_bytes()) != entry["sha256"]:
                raise ValueError("PILOT_REVIEW_SOURCE_CHANGED")
    history = [e for e in events if e["symbol"] == "600721"]
    latest = max(
        (e for e in history if e["effective_from"] < START),
        key=lambda e: e["effective_from"],
    )
    # This evidence review is deliberately tied to the accepted removal document.
    if latest["cninfo_document_id"] != "1213213457" or latest["status"] != "NORMAL":
        raise ValueError("REVIEWED_ANCHOR_CHANGED")
    anchor = {
        "authoritative": latest["match_confidence"] == "EXACT",
        "complete_for_security": True,
        "effective_from": latest["effective_from"],
        "known_on": max(latest["sse_publication_date"], latest["cninfo_publication_date"]),
        "status": latest["status"],
        "document": latest,
    }
    snapshot = json.loads((previous / "pilot-start-anchor.json").read_bytes())["600721"]
    contradictions = []
    if snapshot["status"] != anchor["status"]:
        contradictions.append("YEAR_END_ANCHOR_CONFLICT")
    # Existing complete issuer-scoped metadata search plus the accepted SSE ledger.
    queries = [
        q
        for q in json.loads((previous / "targeted-history-metadata.json").read_bytes())
        if any(r["secCode"] == "600721" for r in q.get("records", []))
    ]
    later_notices = [
        r
        for q in queries
        for r in q["records"]
        if r["secCode"] == "600721"
        and anchor["effective_from"] < r["adjunctUrl"].split("/")[1] <= END
    ]
    # A new notice needs a new evidence review, even if it might be non-state-changing.
    contradictions.extend(r["announcementId"] for r in later_notices)
    ledger = root / "snapshots/20260910T021848Z"
    ledger_manifest = json.loads((ledger / "source-manifest.json").read_bytes())
    pages = ledger_manifest["pages"]
    expected_months = {
        f"{year}-{month:02d}"
        for year in range(2022, 2025)
        for month in range(1, 13)
        if f"{year}-{month:02d}" <= END[:7]
    }
    if {p["month"] for p in pages} != expected_months:
        raise ValueError("SSE_LEDGER_MONTH_GAP")
    for month in expected_months:
        group = [p for p in pages if p["month"] == month]
        if {p["page"] for p in group} != set(range(1, group[0]["page_count"] + 1)):
            raise ValueError("SSE_LEDGER_PAGE_GAP")
    for page in pages:
        payload = (ledger / page["relative_path"]).read_bytes()
        if sha(payload) != page["sha256"]:
            raise ValueError("SSE_LEDGER_CHECKSUM_MISMATCH")
        for group in json.loads(payload)["pageHelp"]["data"]:
            contradictions.extend(
                r["ORG_BULLETIN_ID"]
                for r in group
                if r["SECURITY_CODE"] == "600721" and anchor["effective_from"] < r["SSEDATE"] <= END
            )
    observations = json.loads((source / "issuer-name-observations.json").read_bytes())
    contradictions.extend(
        o["document"]
        for o in observations
        if o["symbol"] == "600721"
        and anchor["effective_from"] < o["date"] <= END
        and name_key(o["name_key"]).startswith(("ST", "*ST", "SST", "S*ST", "PT"))
    )
    # PT identifies the old lifecycle, not the missing ST entry's effective date.
    ancient = "residual-20260910/documents/509408.html"
    raw = (root / ancient).read_bytes()
    ancient_text = "\n".join(json.loads((source / "text/509408.json").read_bytes()))
    if not all(t in ancient_text for t in ("600721", "PT百花村")):
        raise ValueError("ANCIENT_LIFECYCLE_EVIDENCE_CHANGED")
    closed = anchor_closes_ancient_gap(
        anchor,
        "2001-12-31",
        history,
        contradictions,
        bool(queries) and all(q["complete"] for q in queries),
    )
    return {
        "symbol": "600721",
        "token": "ST百花村",
        "classification": "FULL_HISTORY_ONLY_UNRESOLVED" if closed else "PILOT_RELEVANT_UNRESOLVED",
        "ancient_lifecycle_evidence": {"path": ancient, "sha256": sha(raw)},
        "ancient_st_effective_date": None,
        "reviewed_ancient_lifecycle_before": "2001-12-31",
        "latest_pre_pilot_event_anchor": anchor,
        "official_year_end_snapshot": snapshot,
        "snapshot_publication_backdated": False,
        "later_risk_notices": later_notices,
        "sse_ledger_manifest_sha256": sha((ledger / "source-manifest.json").read_bytes()),
        "sse_ledger_pages_verified": len(pages),
        "contradictions": sorted(set(contradictions)),
        "pilot_events": [e for e in history if START <= e["effective_from"] <= END],
        "dates_from_name_order": False,
    }


def coverage_gate(
    root: Path, output: Path, master_path: Path, pilot_source: Path | None = None
) -> dict[str, Any]:
    """Recheck structural replay without authorizing admission on a partial oracle."""
    previous = root / "closure-20260910"
    baseline = json.loads((previous / "closure-summary.json").read_bytes())
    if sha(master_path.read_bytes()) != baseline["security_master_sha256"]:
        raise ValueError("MASTER_CHANGED_DURING_RESIDUAL_CLOSURE")
    anchor_pdf = previous / "anchor/yearbook-2023.pdf"
    if sha(anchor_pdf.read_bytes()) != baseline["anchor_sha256"]:
        raise ValueError("ANCHOR_CHANGED_DURING_RESIDUAL_CLOSURE")
    with master_path.open() as handle:
        master = list(csv.DictReader(handle))
    anchors = {
        r["symbol"]: r["anchor"]
        for r in json.loads((previous / "security-closure-audit.json").read_bytes())
    }
    source = pilot_source or output
    events = json.loads((source / "combined-events.json").read_bytes())
    for event in events:
        document = event["cninfo_document_id"]
        raw = next(
            (
                p
                for p in (
                    root / "cninfo-20260910/documents" / (document + ".pdf"),
                    previous / "documents" / (document + ".pdf"),
                )
                if p.exists()
            ),
            None,
        )
        if raw is None or sha(raw.read_bytes()) != event["cninfo_document_sha256"]:
            raise ValueError("EVENT_DOCUMENT_CHECKSUM_MISMATCH")
        if any(re.search(r'[;\uff1b“”"]', event[k]) for k in ("old_name", "new_name")):
            raise ValueError("MALFORMED_EVENT_NAME")
    rows = json.loads((source / "residual-terminal-audit.json").read_bytes())
    row_map = {r["symbol"]: r for r in rows}
    crosscheck = []
    for row in json.loads((previous / "name-crosscheck.json").read_bytes()):
        if row["symbol"] in row_map:
            tokens = row_map[row["symbol"]]["tokens"]
        else:
            tokens = [
                {
                    **t,
                    "classification": "EXPLAINED_BY_OFFICIAL_EVENT"
                    if t["explained"]
                    else "UNRESOLVED",
                }
                for t in row["tokens"]
            ]
        crosscheck.append(
            {
                **row,
                "tokens": tokens,
                "unexplained": sum(t["classification"] == "UNRESOLVED" for t in tokens),
            }
        )
    unresolved = [r for r in crosscheck if r["unexplained"]]
    review = pilot_review(root, source, events) if pilot_source else None
    pilot_unresolved = [
        r
        for r in unresolved
        if not (
            review
            and review["classification"] == "FULL_HISTORY_ONLY_UNRESOLVED"
            and r["symbol"] == review["symbol"]
            and {t["token"] for t in r["tokens"] if t["classification"] == "UNRESOLVED"}
            == {review["token"]}
        )
    ]
    intervals, chains, temporal = [], [], []
    order_ok, leakage_ok = True, True
    for security in sorted(master, key=lambda r: r["security_id"]):
        code = security["symbol"]
        anchor = anchors[code]
        points = [
            {
                "known_on": max(START, anchor["as_of"]),
                "effective_from": max(START, anchor["as_of"]),
                "status": anchor["status"],
            }
        ]
        state = anchor["status"]
        history = sorted(
            (e for e in events if e["symbol"] == code and START <= e["effective_from"] <= END),
            key=lambda e: (e["effective_from"], e["sse_announcement_id"]),
        )
        for event in history:
            if event["old_status"] != state:
                chains.append({"symbol": code, "document": event["cninfo_document_id"]})
            if (
                max(event["sse_publication_date"], event["cninfo_publication_date"])
                > event["effective_from"]
            ):
                temporal.append(event["cninfo_document_id"])
            state = event["status"]
            points.append(
                {
                    "known_on": max(
                        event["sse_publication_date"], event["cninfo_publication_date"]
                    ),
                    "effective_from": event["effective_from"],
                    "status": state,
                }
            )
        result = intervals_for(security, points)
        order_ok &= result == intervals_for(security, list(reversed(points)))
        future = {"known_on": "2025-01-01", "effective_from": "2025-01-01", "status": "EXCLUDED"}
        leakage_ok &= all(
            replay(points, r["effective_from"]) == replay([future, *points], r["effective_from"])
            for r in result
        )
        for row in result:
            row["status"] = row["evidence_status"]
            row["coverage_certified"] = True  # Structural check only; cleared below.
        intervals.extend(result)
    sessions = json.loads(
        (root / "completeness-20260910/calendar/pilot-sessions.json").read_bytes()
    )
    metrics = assert_completeness(master, intervals, sessions)
    structural_unknown = metrics["excluded_security_days"]
    for row in intervals:
        row["coverage_certified"] = False
        row["dataset_admission_authorized"] = False
    total_tokens = [t for r in crosscheck for t in r["tokens"]]
    counts = Counter(r["classification"] for r in rows)
    complete = (
        not (pilot_unresolved if pilot_source else unresolved)
        and not chains
        and not temporal
        and not structural_unknown
        and order_ok
        and leakage_ok
    )
    summary = {
        "scope": "RESIDUAL_COVERAGE_REVIEW_NO_DATASET_ADMISSION",
        "residual_total": len(rows),
        "classification_counts": dict(counts),
        "control_total": sum(r["is_control"] for r in rows),
        "control_outside_period": sum(
            r["is_control"] and r["classification"] == "EVENT_OUTSIDE_RELEVANT_PERIOD" for r in rows
        ),
        "CONTROL_UNEXPLAINED": sum(r["is_control"] for r in unresolved),
        "NONCONTROL_UNEXPLAINED": sum(not r["is_control"] for r in unresolved),
        "UNEXPLAINED_NAME_HISTORIES": len(unresolved),
        "unexplained_tokens": sum(r["unexplained"] for r in unresolved),
        "HISTORICAL_ST_NAMES_FOUND": sum(t["status"] == "ST" for t in total_tokens),
        "HISTORICAL_STAR_ST_NAMES_FOUND": sum(t["status"] == "STAR_ST" for t in total_tokens),
        "EXPLAINED_BY_OFFICIAL_EVENTS": sum(
            t["classification"] == "EXPLAINED_BY_OFFICIAL_EVENT" for t in total_tokens
        ),
        "outside_period_tokens": sum(
            t["classification"] == "EVENT_OUTSIDE_RELEVANT_PERIOD" for t in total_tokens
        ),
        "EXCLUDED_SECURITIES": 0,
        "EXCLUDED_SECURITY_DAYS": 0,
        "EXCLUDED_UNIVERSE_PERCENTAGE": 0,
        "exclusion_policy": "No blanket exclusion for an unbounded gap; publication blocked.",
        "PILOT_START_STATUS": "PASS",
        "ENTRY_EFFECTIVE_DATE": "PASS" if not chains and not temporal else "FAIL",
        "EXIT_EFFECTIVE_DATE": "PASS" if not chains and not temporal else "FAIL",
        "EVENT_LEDGER_COVERAGE": "PASS" if complete else "PARTIAL",
        "HISTORICAL_NAME_CROSSCHECK": "PASS" if not unresolved else "PARTIAL",
        "DELISTED_RETENTION": "PASS",
        "FUTURE_EVENT_LEAKAGE": "PASS" if leakage_ok and not temporal else "FAIL",
        "INPUT_ORDER_REPRODUCIBILITY": "PASS" if order_ok else "FAIL",
        "SSE_HISTORICAL_ST_RECONSTRUCTION": "PASS" if complete else "PARTIAL",
        "unknown_evidence_replay_security_days": structural_unknown,
        "eligible_security_days": metrics["eligible_security_days"],
        "master_securities": len(master),
        "pilot_sessions": len(sessions),
        "event_chain_gaps": chains,
        "temporal_gaps": temporal,
        "events": len(events),
        "pilot_events": sum(START <= e["effective_from"] <= END for e in events),
        "event_sha256": sha(canonical(events)),
        "security_master_sha256": baseline["security_master_sha256"],
        "PILOT_DATASET_CREATED": False,
        "dataset_admissions": 0,
        "AKSHARE_ACCEPTANCE": "PASS_FOR_PILOT" if complete else "PARTIAL",
        "PILOT_A_SHARE_DATA_READINESS": "READY" if complete else "BLOCKED",
    }
    if pilot_source:
        summary.update(
            {
                "scope": "PILOT_SCOPED_ST_COVERAGE_NOT_DATASET_PUBLICATION",
                "FULL_HISTORY_UNEXPLAINED_NAME_HISTORIES": len(unresolved),
                "PILOT_RELEVANT_UNEXPLAINED_NAME_HISTORIES": len(pilot_unresolved),
                "FULL_HISTORY_ST_COMPLETENESS": "PARTIAL" if unresolved else "PASS",
                "PILOT_ST_COMPLETENESS": "PASS" if complete else "PARTIAL",
                "SSE_HISTORICAL_ST_RECONSTRUCTION_FOR_PILOT": "PASS" if complete else "PARTIAL",
                "SSE_HISTORICAL_ST_RECONSTRUCTION": "PARTIAL" if unresolved else "PASS",
                "EVENT_LEDGER_COVERAGE": "PARTIAL" if unresolved else "PASS",
                "EVENT_LEDGER_COVERAGE_FOR_PILOT": "PASS" if complete else "PARTIAL",
                "HISTORICAL_NAME_CROSSCHECK_FOR_PILOT": "PASS"
                if not pilot_unresolved
                else "PARTIAL",
                "PILOT_A_SHARE_DATA_READINESS": "ST_GATE_PASSED_MATERIALIZATION_PENDING"
                if complete
                else "BLOCKED",
                "exclusion_policy": (
                    "Exclude only pilot-relevant uncertainty; full-history gaps retained."
                ),
            }
        )
        for interval in intervals:
            interval["coverage_certified"] = complete
            # ST certification alone is not approval of prices, adjustments or publication.
            interval["dataset_admission_authorized"] = False
        save(output / "600721-pilot-review.json", review)
    save(output / "full-name-crosscheck.json", crosscheck)
    save(output / "coverage-intervals.json", intervals)
    save(output / "exclusions.json", [])
    save(
        output / "unresolved-source-gaps.json",
        [
            {
                "security_id": r["security_id"],
                "tokens": [t["token"] for t in r["tokens"] if t["classification"] == "UNRESOLVED"],
                "effective_from": None,
                "effective_to": None,
                "reason": "Exact-token boundary unproved; dates not inferred from name order.",
                "evidence_searched": sorted(
                    p.relative_to(output).as_posix()
                    for p in (output / "targeted").glob(r["symbol"] + "*.json")
                    if not p.name.endswith(".meta.json")
                ),
            }
            for r in unresolved
        ],
    )
    save(output / "coverage-summary.json", summary)
    files = [
        {"path": p.relative_to(output).as_posix(), "sha256": sha(p.read_bytes())}
        for p in sorted(output.rglob("*"))
        if p.is_file() and p.name != "residual-manifest.json" and not p.name.endswith(".tmp")
    ]
    manifest = {
        "files": files,
        "version": "sse-residual-coverage-v1",
        "prior_manifest_sha256": json.loads((previous / "closure-manifest.json").read_bytes())[
            "manifest_sha256"
        ],
    }
    if pilot_source:
        manifest["pilot_source_manifest_sha256"] = sha(
            (pilot_source / "residual-manifest.json").read_bytes()
        )
    save(
        output / "residual-manifest.json", {**manifest, "manifest_sha256": sha(canonical(manifest))}
    )
    print(json.dumps(summary, indent=2))
    return summary


def controls(root: Path, output: Path) -> list[dict[str, Any]]:
    previous = root / "closure-20260910"
    names = json.loads((previous / "name-crosscheck.json").read_bytes())
    targets = {r["symbol"]: r for r in names if r["is_control"] and r["unexplained"]}
    reviews = json.loads((output / "control-reviews.json").read_bytes())
    if len(reviews) != 13 or {r["symbol"] for r in reviews} != set(targets):
        raise ValueError("CONTROL_REVIEW_SET_MISMATCH")
    records = {
        r["cninfo"][0]["announcementId"]: r
        for r in json.loads((previous / "additional-parser-audit.json").read_bytes())
    }
    events = json.loads((previous / "combined-normalized-events.json").read_bytes())
    anchors = json.loads((previous / "pilot-start-anchor.json").read_bytes())
    result = []
    for review in sorted(reviews, key=lambda r: r["symbol"]):
        code = review["symbol"]
        if anchors[code]["status"] != "NORMAL" or any(
            e["symbol"] == code and START <= e["effective_from"] <= END for e in events
        ):
            raise ValueError("CONTROL_OUTSIDE_PERIOD_CONFLICT")
        paths = list(review.get("documents", []))
        for document in review.get("document_ids", []):
            record = records[document]
            if record["match_confidence"] != "EXACT" or record["sse"]["SECURITY_CODE"] != code:
                raise ValueError("CONTROL_DOCUMENT_IDENTITY_MISMATCH")
            paths.append(f"closure-20260910/documents/{document}.pdf")
        sources = []
        for relative in sorted(set(paths)):
            path = root / relative
            meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
            digest = sha(path.read_bytes())
            if digest != meta["sha256"]:
                raise ValueError("CONTROL_SOURCE_CHECKSUM_MISMATCH")
            sources.append(
                {
                    "path": relative,
                    "sha256": digest,
                    "url": meta["url"],
                    "retrieved_at_utc": meta["retrieved_at_utc"],
                }
            )
        covered: set[str] = set()
        for boundary in review["boundaries"]:
            if not (
                boundary.get("outside_before", END) < START
                or boundary.get("outside_after", START) > END
            ):
                raise ValueError("CONTROL_BOUNDARY_OVERLAPS_PILOT")
            covered.update(name_key(t) for t in boundary["tokens"])
        observed = {name_key(t["token"]) for t in targets[code]["tokens"]}
        if covered != observed:
            raise ValueError("CONTROL_TOKEN_NOT_DISPOSITIONED")
        result.append(
            {
                **review,
                "security_id": targets[code]["security_id"],
                "ever_st": any(t["status"] == "ST" for t in targets[code]["tokens"]),
                "ever_star_st": any(t["status"] == "STAR_ST" for t in targets[code]["tokens"]),
                "sources": sources,
                "tokens": [
                    {**t, "classification": review["classification"], "explained": True}
                    for t in targets[code]["tokens"]
                ],
                "pilot_anchor": anchors[code],
                "pilot_event_count": 0,
                "dates_from_name_order": False,
            }
        )
    save(output / "control-terminal-audit.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--master", type=Path)
    parser.add_argument("--pilot-source", type=Path)
    args = parser.parse_args()
    if args.pilot_source:
        if not args.master or args.pilot_source.resolve() == args.output.resolve():
            parser.error("--pilot-source requires --master and a distinct output directory")
    else:
        residual(args.root, args.output)
    if args.master:
        coverage_gate(args.root, args.output, args.master, args.pilot_source)
