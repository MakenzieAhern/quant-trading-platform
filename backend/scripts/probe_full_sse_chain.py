"""Diagnose cached provisional chains, never certify full-universe daily states."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_distribution_cash import verified


def diagnose(events, initial, last):
    dates = defaultdict(list)
    for event in events:
        dates[event["effective_from"]].append(event)
    current = initial
    gaps, conflicts, trace = [], [], []
    for day, rows in sorted(dates.items()):
        finals = {r["status"] for r in rows}
        pairs = {(r["old_status"], r["status"]) for r in rows if r["old_status"] != r["status"]}
        documents = sorted({r.get("official_document_id", r["cninfo_document_id"]) for r in rows})
        if len(finals) != 1 or len(pairs) > 1:
            conflicts.append(dict(date=day, document_ids=documents))
            current, last = "UNKNOWN", day
            continue
        expected = next(iter(pairs))[0] if pairs else next(iter(finals))
        if current != expected:
            gaps.append(
                dict(
                    after_last_observed_date=last,
                    before_transition_date=day,
                    last_observed_state=current,
                    required_old_state=expected,
                    document_ids=documents,
                )
            )
        current, last = next(iter(finals)), day
        trace.append(dict(date=day, state=current, document_ids=documents))
    return dict(initial_state=initial, gaps=gaps, conflicts=conflicts, trace=trace)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--parsed", action="append", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    root = args.staging / "full-sse-st-v1"
    parsed_paths = [root / path for path in args.parsed]
    evidence_paths = [
        args.staging / "sse-st-pilot/residual-20260910/combined-events.json",
        root / "prestart-anchor-v2.json",
        args.staging / "full-code-transitions-v1/master-code-intervals.json",
    ]
    parsed = [verified(path) for path in parsed_paths]
    anchor, master = (verified(evidence_paths[i]) for i in (1, 2))
    events = [
        row["event"] for document in parsed for row in document["results"] if "event" in row
    ] + json.loads(evidence_paths[0].read_bytes())
    anchors = {r["symbol"]: r["status"] for r in anchor["anchors"]}
    by_symbol, by_id = defaultdict(list), defaultdict(list)
    for member in master["records"]:
        if member["exchange"] == "SSE":
            by_symbol[member["symbol"]].append(member)
            by_id[member["security_id"]].append(member)
    mapped, unmapped, outside = defaultdict(list), [], []
    for event in events:
        day = event["effective_from"]
        if not "2010-01-01" <= day <= "2025-12-31":
            outside.append(event)
            continue
        matches = [
            m
            for m in by_symbol[event["symbol"]]
            if m["effective_from"] <= day <= (m["effective_to"] or "2025-12-31")
        ]
        if len(matches) != 1:
            unmapped.append(event)
        else:
            mapped[matches[0]["security_id"]].append(event)
    rows = []
    for sid, items in sorted(mapped.items()):
        first = min(by_id[sid], key=lambda m: m["effective_from"])
        initial = anchors.get(
            first["symbol"], "NORMAL" if first["listing_date"] >= "2010-01-01" else "UNKNOWN"
        )
        last = max("2009-12-31", first["listing_date"])
        result = diagnose(items, initial, last)
        assert result == diagnose(list(reversed(items)), initial, last)
        rows.append(dict(security_id=sid, **result))
    report = dict(
        scope="PROVISIONAL_CHAIN_DIAGNOSTIC_NOT_AUTHORITY_OR_DAILY_STATE_ACCEPTANCE",
        inputs=[
            dict(path=str(path), sha256=sha256_file(path))
            for path in [*parsed_paths, *evidence_paths]
        ],
        parser_sha256=sha256_file(Path(__file__)),
        rows=rows,
        unmapped=unmapped,
        outside_target_count=len(outside),
        raw_event_evidence=len(events),
        security_chains=len(rows),
        gap_count=sum(len(r["gaps"]) for r in rows),
        conflict_count=sum(len(r["conflicts"]) for r in rows),
        accepted_events=0,
        input_order_reproducibility="PASS",
        ipo_initialization="EXISTING_PILOT_NORMAL_AT_FIRST_IPO_FOR_DIAGNOSTIC_ONLY",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(root / args.report, canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"rows", "unmapped", "inputs"}}))


if __name__ == "__main__":
    main()
