"""Measure retained dated-name coverage gaps without promoting full ST authority."""

import argparse
import json
import re
import unicodedata
from bisect import bisect_left
from collections import Counter, defaultdict
from datetime import date, timedelta
from itertools import pairwise
from pathlib import Path

from openpyxl import load_workbook

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.szse_st_recovery import normalize, risk_state, status_on


def replay(members, events, anchors, sessions):
    """Count every session via constant-state intervals using the accepted replay helper."""
    if not sessions or sessions != sorted(set(sessions)):
        raise ValueError("INVALID_REPLAY_CALENDAR")
    aliases = {r["symbol"]: r["security_id"] for r in members}
    byid = {r["security_id"]: r for r in sorted(members, key=lambda r: r["effective_from"])}
    histories = defaultdict(list)
    for event in events:
        histories[aliases[event["symbol"]]].append(event)
    starting = {r["security_id"]: r["anchor"] for r in anchors}
    intervals, counts, ipo_conflicts = [], Counter(), []
    future_ok = True
    for sid, member in sorted(byid.items()):
        history = histories[sid]
        start = max("2010-01-01", member["listing_date"])
        end = min("2025-12-31", member["delisting_date"] or "2025-12-31")
        if member["listing_date"] < "2010-01-01":
            prior = starting.get(sid)
            anchor = dict(
                effective_from="2009-12-31", status=prior["status"] if prior else "UNKNOWN"
            )
        else:
            # Same IPO initialization as the accepted Pilot SZSE auditor; not a new rule.
            anchor = dict(effective_from=member["listing_date"], status="NORMAL")
            first = sorted(history, key=lambda e: e["effective_from"])
            if first and first[0]["old_status"] != "NORMAL":
                ipo_conflicts.append(dict(security_id=sid, first_event=first[0]))
                anchor["status"] = "UNKNOWN"
        stop = (date.fromisoformat(end) + timedelta(days=1)).isoformat()
        boundaries = sorted(
            {start, stop}
            | {e["effective_from"] for e in history if start < e["effective_from"] <= end}
        )
        for left, right in pairwise(boundaries):
            state = status_on(anchor, history, left)
            future_ok &= state == status_on(
                anchor, [e for e in history if e["effective_from"] <= left], left
            )
            days = bisect_left(sessions, right) - bisect_left(sessions, left)
            counts[state] += days
            intervals.append(
                dict(
                    security_id=sid,
                    effective_from=left,
                    effective_to=(date.fromisoformat(right) - timedelta(days=1)).isoformat(),
                    status=state,
                    trading_sessions=days,
                )
            )
    return dict(
        intervals=intervals,
        security_days=dict(sorted(counts.items())),
        ipo_initialization_conflicts=ipo_conflicts,
        future_event_leakage="PASS" if future_ok else "FAIL",
    )


def notice_header(page, issuer):
    # Only issuer labels in the opening header, never other companies in the body.
    header = re.sub(r"\s+", "", unicodedata.normalize("NFKC", page[:180]))
    codes = re.findall(r"(?:证券|股票)代码[:;](\d{6})(?!\d)", header)
    names = re.findall(
        r"(?:证券|股票|公司)简称[:;]([S*]*ST[\u4e00-\u9fff]+?)(?=公告编|(?:证券|股票)代码)",
        header,
    )
    if codes != [issuer] or len(names) != 1:
        raise ValueError("PRESTART_NOTICE_HEADER_AMBIGUOUS")
    return dict(name=names[0], status=risk_state(names[0]), source_page=1)


def notice_corroboration(root):
    path = root / "prestart-pdfs-v1/source-manifest.json"
    manifest = json.loads(path.read_bytes())
    if manifest["manifest_sha256"] != canonical_sha256(
        {k: v for k, v in manifest.items() if k != "manifest_sha256"}
    ):
        raise ValueError("PRESTART_MANIFEST_CHANGED")
    result = defaultdict(list)
    for doc in sorted(manifest["documents"], key=lambda d: (d["published_on"], d["url"])):
        source = (root / doc["source_path"]).resolve()
        if not source.is_relative_to(root.resolve()) or doc["retrieval_status"] != "PASS":
            raise ValueError("PRESTART_SOURCE_INVALID")
        if not "2009-10-01" <= doc["published_on"] <= "2009-12-31":
            raise ValueError("PRESTART_SOURCE_DATE_INVALID")
        extracted = json.loads(
            (root / "batch-v1/text" / f"{doc['source_sha256']}.json").read_bytes()
        )
        if (
            sha256_file(source) != doc["source_sha256"]
            or extracted["source_sha256"] != doc["source_sha256"]
        ):
            raise ValueError("PRESTART_SOURCE_CHANGED")
        result[doc["issuer"]].append(
            dict(**notice_header(extracted["pages"][0], doc["issuer"]), source=doc)
        )
    return result, manifest["manifest_sha256"]


def yearbook_names(pages):
    found = {}
    for number, text in enumerate(pages, 1):
        text = unicodedata.normalize("NFKC", text)
        if "PRICECHANGEOFSTOCKS" not in re.sub(r"\s+", "", text):
            continue
        for match in re.finditer(r"(?m)^\d+\s+(\d{6})\s*\n(.*?)(?=\n\d)", text, re.S):
            code = match[1]
            if code in found:
                raise ValueError("DUPLICATE_YEARBOOK_STOCK")
            # The retained 2009 PDF's E012 glyph is a star, visually checked on p60.
            name = re.sub(r"\s+", "", match[2]).replace("\ue012", "*")
            found[code] = dict(name=name, source_page=number, status=risk_state(name))
    return found


def probe(members, events):
    aliases = {}
    for member in members:
        code, sid = member["symbol"], member["security_id"]
        if code in aliases and aliases[code] != sid:
            raise ValueError("CONFLICTING_STABLE_ID_ALIAS")
        aliases[code] = sid
    byid = {r["security_id"]: r for r in sorted(members, key=lambda r: r["effective_from"])}
    group = defaultdict(list)
    for event in events:
        group[aliases[event["symbol"]]].append(event)
    gaps, anchors, outside = [], [], []
    risk = 0
    for sid, member in sorted(byid.items()):
        history = sorted(group[sid], key=lambda e: (e["effective_from"], canonical_sha256(e)))
        before = [
            e for e in history if member["listing_date"] <= e["effective_from"] < "2010-01-01"
        ]
        if before:
            anchors.append(
                dict(
                    security_id=sid,
                    anchor=before[-1],
                    status="DATED_PRESTART_TRANSITION_ONLY_INDEPENDENT_ANCHOR_PENDING",
                )
            )
        elif member["listing_date"] < "2010-01-01":
            anchors.append(dict(security_id=sid, status="NO_PRESTART_DATED_ANCHOR", anchor=None))
        state = before[-1]["status"] if before else None
        for event in history:
            day = event["effective_from"]
            if not "2010-01-01" <= day <= "2025-12-31":
                continue
            if day < member["listing_date"] or (
                member["delisting_date"] and day > member["delisting_date"]
            ):
                outside.append(dict(security_id=sid, event=event))
                continue
            if state is not None and state != event["old_status"]:
                gaps.append(dict(security_id=sid, previous_status=state, event=event))
            state = event["status"]
            risk += event["status"] != event["old_status"]
    return dict(
        candidate_securities=len(byid),
        target_risk_transitions=risk,
        prestart_anchor_counts=dict(sorted(Counter(x["status"] for x in anchors).items())),
        anchors=anchors,
        risk_chain_gaps=gaps,
        outside_lifecycle=outside,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--report", default="dated-name-coverage-probe-v1.json")
    args = parser.parse_args()
    staging = args.staging
    source = staging / "szse-st-recovery-20260910/windows-short-name-changes.xlsx"
    meta = json.loads(source.with_suffix(".xlsx.meta.json").read_bytes())
    if sha256_file(source) != meta["sha256"]:
        raise ValueError("DATED_NAME_SOURCE_CHANGED")
    master_path = staging / "full-code-transitions-v1/master-code-intervals.json"
    master = json.loads(master_path.read_bytes())
    if master["manifest_sha256"] != canonical_sha256(
        {k: v for k, v in master.items() if k != "manifest_sha256"}
    ):
        raise ValueError("MASTER_CHANGED")
    members = [
        r
        for r in master["records"]
        if r["exchange"] == "SZSE"
        and r["listing_date"] <= "2025-12-31"
        and (not r["delisting_date"] or r["delisting_date"] >= "2010-01-01")
    ]
    book = load_workbook(source, read_only=True, data_only=True)
    sheet = book["简称变更"]
    sheet.reset_dimensions()
    rows = list(sheet.values)
    book.close()
    if rows[0] != ("变更日期", "证券代码", "证券简称", "变更前简称", "变更后简称"):
        raise ValueError("DATED_NAME_SCHEMA_CHANGED")
    allowed = {r["symbol"] for r in members}
    events = normalize(rows[1:], allowed)
    report = probe(members, events)
    if events != normalize(list(reversed(rows[1:])), allowed) or report != probe(
        list(reversed(members)), list(reversed(events))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    text_path = staging / "full-master-evidence/master-text-2009.json"
    yearbook_path = staging / "full-master-evidence/raw/szse-yearbook-2009.pdf"
    extracted = json.loads(text_path.read_bytes())
    snapshots = json.loads(
        (staging / "full-master-evidence/source-snapshot-manifest.json").read_bytes()
    )
    yearbook_source = next(
        r for r in snapshots["snapshots"] if r["raw_snapshot_filename"] == yearbook_path.name
    )
    if (
        extracted["source_sha256"] != sha256_file(yearbook_path)
        or yearbook_source["sha256"] != extracted["source_sha256"]
    ):
        raise ValueError("YEARBOOK_EXTRACTION_SOURCE_CHANGED")
    names = yearbook_names(extracted["pages"])
    notices, notice_manifest = notice_corroboration(staging / "full-szse-st-v1")
    corroboration = []
    for row in report["anchors"]:
        anchor = row["anchor"]
        evidence = names.get(anchor["symbol"]) if anchor else None
        corroboration.append(
            dict(
                security_id=row["security_id"],
                evidence=evidence,
                result="NOT_IN_ANNUAL_TRADING_TABLE"
                if evidence is None
                else "AGREES"
                if evidence["status"] == anchor["status"]
                else "CONFLICT",
            )
        )
    report["yearbook_corroboration"] = corroboration
    report["yearbook_corroboration_counts"] = dict(
        sorted(Counter(r["result"] for r in corroboration).items())
    )
    supplemental = []
    for row in report["anchors"]:
        anchor = row["anchor"]
        if anchor and anchor["symbol"] not in names:
            documents = notices.get(anchor["symbol"], [])
            supplemental.append(
                dict(
                    security_id=row["security_id"],
                    evidence=documents,
                    result="AGREES"
                    if documents and all(d["status"] == anchor["status"] for d in documents)
                    else "UNRESOLVED",
                )
            )
    report["notice_corroboration"] = supplemental
    report["notice_corroboration_counts"] = dict(
        sorted(Counter(r["result"] for r in supplemental).items())
    )
    report["notice_manifest_sha256"] = notice_manifest
    calendar_path = staging / "full-calendar-v1/calendar-manifest-v3.json"
    calendar = json.loads(calendar_path.read_bytes())
    if calendar["manifest_sha256"] != canonical_sha256(
        {k: v for k, v in calendar.items() if k != "manifest_sha256"}
    ):
        raise ValueError("CALENDAR_MANIFEST_CHANGED")
    agreed = {r["security_id"] for r in corroboration + supplemental if r["result"] == "AGREES"}
    replay_anchors = [r for r in report["anchors"] if r["security_id"] in agreed]
    replayed = replay(members, events, replay_anchors, calendar["sessions"])
    if replayed != replay(
        list(reversed(members)), list(reversed(events)), replay_anchors, calendar["sessions"]
    ):
        raise ValueError("REPLAY_INPUT_ORDER_CHANGED")
    report["daily_replay"] = replayed
    report["calendar_manifest_sha256"] = calendar["manifest_sha256"]
    report["yearbook_sha256"] = sha256_file(yearbook_path)
    report["yearbook_source"] = yearbook_source
    report["yearbook_extraction_sha256"] = sha256_file(text_path)
    report.update(
        parser_version="FULL_SZSE_DATED_NAME_COVERAGE_PROBE_V1",
        parser_sha256=sha256_file(Path(__file__)),
        source=meta,
        source_sha256=sha256_file(source),
        source_master_sha256=sha256_file(master_path),
        retained_source_rows=len(rows) - 1,
        normalized_events=len(events),
        input_order_reproducibility="PASS",
        authority="PARTIAL_NOT_FULL_ACCEPTANCE",
        current_name_used=False,
        future_events_used=False,
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        staging / "full-szse-st-v1" / args.report,
        canonical_json_bytes(report) + b"\n",
    )
    print(
        json.dumps(
            {
                k: v
                for k, v in report.items()
                if k
                not in (
                    "anchors",
                    "source",
                    "risk_chain_gaps",
                    "outside_lifecycle",
                    "yearbook_corroboration",
                    "yearbook_source",
                    "notice_corroboration",
                    "daily_replay",
                )
            }
        )
    )
    print(
        "RISK_CHAIN_GAPS",
        len(report["risk_chain_gaps"]),
        "OUTSIDE_LIFECYCLE",
        len(report["outside_lifecycle"]),
    )
    print("REPLAY", json.dumps({k: v for k, v in replayed.items() if k != "intervals"}))


if __name__ == "__main__":
    main()
