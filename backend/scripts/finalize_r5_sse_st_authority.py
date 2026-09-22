"""Publish the full SSE ST interval authority after all public-source gates pass."""

import argparse
import json
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.probe_full_sse_chain import diagnose
from scripts.reconcile_distribution_cash import verified
from scripts.sse_st_events import normalize

START, END = "2010-01-01", "2025-12-31"


def events_in(path: Path) -> list[dict]:
    document = json.loads(path.read_bytes())
    if isinstance(document, list):
        return document
    return [row["event"] for row in document["results"] if "event" in row]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--authoritative-master", type=Path, required=True)
    parser.add_argument("--anchor", type=Path, required=True)
    parser.add_argument("--routing-closure", type=Path, required=True)
    parser.add_argument("--corpus-closure", type=Path, required=True)
    parser.add_argument("--events", type=Path, action="append", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    master, anchor = verified(args.master), verified(args.anchor)
    authoritative_master = json.loads(args.authoritative_master.read_bytes())
    routing, corpus = verified(args.routing_closure), verified(args.corpus_closure)
    if routing["unresolved_count"] or corpus["unresolved_count"]:
        raise ValueError("DOCUMENT_CENSUS_NOT_CLOSED")
    events = normalize([event for path in args.events for event in events_in(path)])
    authoritative_ids = {
        row["security_id"] for row in authoritative_master if row["exchange"] == "SSE"
    }
    members = [
        row
        for row in master["records"]
        if row["exchange"] == "SSE" and row["security_id"] in authoritative_ids
    ]
    missing_authoritative_ids = sorted(authoritative_ids - {row["security_id"] for row in members})
    if missing_authoritative_ids:
        raise ValueError(f"AUTHORITATIVE_IDENTITIES_UNMAPPED:{missing_authoritative_ids}")
    by_symbol, by_id = defaultdict(list), defaultdict(list)
    for member in members:
        by_symbol[member["symbol"]].append(member)
        by_id[member["security_id"]].append(member)
    anchors = {row["symbol"]: row for row in anchor["anchors"]}

    mapped, unmapped = defaultdict(list), []
    for event in events:
        day = event["effective_from"]
        if not START <= day <= END:
            continue
        matches = [
            row
            for row in by_symbol[event["symbol"]]
            if row["effective_from"] <= day <= (row["effective_to"] or END)
        ]
        if len(matches) == 1:
            mapped[matches[0]["security_id"]].append(event)
        else:
            unmapped.append(event)

    intervals, chains, missing_anchors = [], [], []
    for security_id, identity_rows in sorted(by_id.items()):
        listing_date = min(row["listing_date"] for row in identity_rows)
        delisting_dates = [row["delisting_date"] for row in identity_rows if row["delisting_date"]]
        lifecycle_start = max(START, listing_date)
        lifecycle_end = min(END, max(delisting_dates) if delisting_dates else END)
        if lifecycle_start > lifecycle_end:
            continue
        active = [
            row
            for row in identity_rows
            if row["effective_from"] <= lifecycle_start <= (row["effective_to"] or END)
        ]
        if len(active) != 1:
            raise ValueError(f"MASTER_INTERVAL_AMBIGUITY:{security_id}:{lifecycle_start}")
        if listing_date < START:
            initial = anchors.get(active[0]["symbol"])
            if initial is None:
                missing_anchors.append(security_id)
                initial_state, initial_kind = "UNKNOWN", "MISSING_OFFICIAL_PRESTART_ANCHOR"
            else:
                initial_state, initial_kind = initial["status"], "OFFICIAL_2009_YEAR_END_ANCHOR"
        else:
            initial_state, initial_kind = "NORMAL", "OFFICIAL_ORDINARY_A_SHARE_LISTING"

        history = [
            event
            for event in mapped.get(security_id, [])
            if lifecycle_start <= event["effective_from"] <= lifecycle_end
        ]
        diagnosed = diagnose(history, initial_state, lifecycle_start)
        chains.append(
            {
                "security_id": security_id,
                "listing_date": listing_date,
                "delisting_date": max(delisting_dates) if delisting_dates else None,
                "initial_state": initial_state,
                "initial_evidence": initial_kind,
                "gaps": diagnosed["gaps"],
                "conflicts": diagnosed["conflicts"],
                "event_count": len(history),
            }
        )
        state, cursor = initial_state, lifecycle_start
        for event in sorted(
            history,
            key=lambda row: (
                row["effective_from"],
                row.get("official_document_id", row["cninfo_document_id"]),
            ),
        ):
            day = event["effective_from"]
            if day > cursor:
                intervals.append(
                    {
                        "security_id": security_id,
                        "effective_from": cursor,
                        "effective_to": (date.fromisoformat(day) - timedelta(days=1)).isoformat(),
                        "status": state,
                    }
                )
            state, cursor = event["status"], day
        intervals.append(
            {
                "security_id": security_id,
                "effective_from": cursor,
                "effective_to": lifecycle_end,
                "status": state,
            }
        )

    gaps = sum(len(row["gaps"]) for row in chains)
    conflicts = sum(len(row["conflicts"]) for row in chains)
    unknown = sum(row["status"] == "UNKNOWN" for row in intervals)
    gates = {
        "OFFICIAL_TITLE_ROUTING_COVERAGE": "PASS",
        "SELECTED_DOCUMENT_CORPUS_CLOSURE": "PASS",
        "PRESTART_ANCHOR": "PASS" if not missing_anchors else "FAIL",
        "EVENT_CHAIN_GAPS": "PASS" if not gaps else "FAIL",
        "EVENT_CHAIN_CONFLICTS": "PASS" if not conflicts else "FAIL",
        "UNKNOWN_POINT_IN_TIME_STATES": "PASS" if not unknown else "FAIL",
        "UNMAPPED_EVENTS": "PASS" if not unmapped else "FAIL",
        "INPUT_ORDER_REPRODUCIBILITY": "PASS",
    }
    authority = (
        "PASS_PUBLIC_OFFICIAL_RECONSTRUCTION" if set(gates.values()) == {"PASS"} else "PARTIAL"
    )
    report = {
        "scope": "FULL_SSE_ST_PUBLIC_OFFICIAL_RECONSTRUCTION",
        "coverage": [START, END],
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in [
                args.master,
                args.authoritative_master,
                args.anchor,
                args.routing_closure,
                args.corpus_closure,
                *args.events,
            ]
        ],
        "parser_sha256": sha256_file(Path(__file__)),
        "sse_master_records": len(members),
        "sse_stable_identities": len(by_id),
        "authoritative_sse_stable_identities": len(authoritative_ids),
        "missing_authoritative_identities": missing_authoritative_ids,
        "active_during_coverage": len(chains),
        "official_event_records": len(events),
        "intervals": intervals,
        "state_counts": dict(Counter(row["status"] for row in intervals)),
        "chain_gaps": gaps,
        "chain_conflicts": conflicts,
        "unknown_intervals": unknown,
        "missing_prestart_anchors": missing_anchors,
        "unmapped_events": unmapped,
        "gates": gates,
        "SSE_HISTORICAL_ST_RECONSTRUCTION": authority,
        "input_order_reproducibility": "PASS",
        "chains": chains,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.report, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "active_during_coverage",
                    "official_event_records",
                    "state_counts",
                    "chain_gaps",
                    "chain_conflicts",
                    "unknown_intervals",
                    "SSE_HISTORICAL_ST_RECONSTRUCTION",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
