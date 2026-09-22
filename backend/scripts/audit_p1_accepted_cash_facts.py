"""Close P1 cash-source requests already proved by the accepted official cash ledger."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified


def reconcile(
    queue: list[dict], events: list[dict], master: list[dict]
) -> tuple[list[dict], list[dict]]:
    by_url = defaultdict(list)
    for row in events:
        event = row["event"]
        by_url[event["source_url"]].append((event, row["event_checksum"]))
    by_symbol = defaultdict(list)
    for row in master:
        by_symbol[row["symbol"]].append(row)

    accepted, remaining = [], []
    for row in queue:
        if row["queue_type"] != "OFFICIAL_ISSUER_DISTRIBUTION_IMPLEMENTATION_PDF":
            remaining.append(row)
            continue
        identities = [
            item["security_id"]
            for item in by_symbol[row["issuer"]]
            if item["effective_from"] <= row["published_on"]
            and (item["effective_to"] is None or row["published_on"] <= item["effective_to"])
            and item["instrument_type"] == "COMMON_A_SHARE"
        ]
        candidates = [
            (event, checksum)
            for event, checksum in by_url[row["url"]]
            if len(identities) == 1
            and event["security_id"]["value"] == identities[0]
            and event["announcement_date"] == row["published_on"]
            and event["action_type"] == "CASH_DIVIDEND"
            and event["source_provider"].startswith("OFFICIAL_ISSUER_CNINFO_")
            and event["cash_per_share"] is not None
            and event["record_date"]
            and event["ex_date"]
        ]
        if len(candidates) != 1:
            remaining.append(row)
            continue
        event, checksum = candidates[0]
        accepted.append(
            {
                "document_id": row["document_id"],
                "affected_events": row["affected_events"],
                "issuer": row["issuer"],
                "security_id": identities[0],
                "url": row["url"],
                "source_sha256": event["source_document_sha256"],
                "cash_event_checksum": checksum,
                "record_date": event["record_date"],
                "ex_date": event["ex_date"],
                "cash_per_share": event["cash_per_share"],
                "classification": "SAME_OFFICIAL_DOCUMENT_ACCEPTED_CASH_FACT",
            }
        )
    return (
        sorted(accepted, key=lambda item: item["document_id"]),
        sorted(remaining, key=lambda item: item["document_id"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--p1-report", type=Path, required=True)
    parser.add_argument("--p1-queue", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prior, cash = verified(args.p1_report), verified(args.cash_ledger)
    queue = json.loads(args.p1_queue.read_bytes())
    master = json.loads(args.master.read_bytes())
    if canonical_sha256(queue) != prior["queue_sha256"]:
        raise ValueError("P1_QUEUE_CHANGED")
    if sha256_file(args.master) not in {row["sha256"] for row in prior["inputs"]}:
        raise ValueError("P1_MASTER_CHANGED")
    if (
        cash["accepted_events"] != len(cash["events"])
        or cash["unresolved_events"]
        or cash["checksum_repeatability"] != "PASS"
        or cash["input_order_reproducibility"] != "PASS"
    ):
        raise ValueError("CASH_LEDGER_NOT_ACCEPTED")
    accepted, remaining = reconcile(queue, cash["events"], master)
    if (accepted, remaining) != reconcile(
        list(reversed(queue)), list(reversed(cash["events"])), list(reversed(master))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    established = sum(len(row["affected_events"]) for row in accepted)
    report = {
        "report_version": "P1_ACCEPTED_CASH_FACT_CLOSURE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            "p1_report": sha256_file(args.p1_report),
            "p1_queue": sha256_file(args.p1_queue),
            "cash_ledger": sha256_file(args.cash_ledger),
            "master": sha256_file(args.master),
        },
        "p1_raw_requirements": prior["p1_raw_requirements"],
        "p1_facts_already_established": prior["p1_facts_already_established"] + established,
        "p1_resolved_by_official_substitution": prior["p1_resolved_by_official_substitution"],
        "p1_true_missing_source_facts": prior["p1_true_missing_source_facts"] - established,
        "p1_unestablished_unique_documents": prior["p1_unresolved_unique_documents"]
        - len(accepted),
        "p1_cash_documents_established_by_same_official_url": len(accepted),
        "p1_cash_documents_not_yet_established": len(remaining),
        "p1_other_document_requirements": prior["p1_other_documents_still_required"],
        "accepted_cash_matches": accepted,
        "remaining_cash_documents": remaining,
        "input_order_reproducibility": "PASS",
        "no_new_source_substitution_claimed": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if not isinstance(value, list)},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
