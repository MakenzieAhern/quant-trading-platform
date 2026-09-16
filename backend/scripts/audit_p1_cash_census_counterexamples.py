"""Cross-check retained official P1 cash notices against the accepted full ledger."""

import argparse
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified

PRIMARY = re.compile(
    r"权益分派实施(?:的)?公告|权益分配实施公告|"
    r"利润分配(?:方案|及资本公积转增股本)?实施公告|利润分派A股实施公告|"
    r"分红派息(?:、转增股本)?实施公告|特别分红实施公告"
)
SECONDARY = re.compile(r"调整|回购|更正|修订|重组|提示|实施结果")


def crosscheck(
    triage: list[dict], requirements: list[dict], cash: list[dict], master: list[dict]
) -> list[dict]:
    by_doc = {row["document_id"]: row for row in requirements}
    by_symbol = defaultdict(list)
    by_ex_date = defaultdict(list)
    for row in master:
        by_symbol[row["symbol"]].append(row)
    for row in cash:
        event = row["event"]
        by_ex_date[(event["security_id"]["value"], event["ex_date"])].append(event)
    results = []
    for row in triage:
        requirement = by_doc[row["document_id"]]
        title = requirement["title"]
        if not PRIMARY.search(title) or SECONDARY.search(title):
            continue
        if (
            row["preferred_instrument_marker"]
            or row["cash_candidate_per_share"] is None
            or len(row["record_dates"]) != 1
            or len(row["ex_dates"]) != 1
        ):
            continue
        identities = {
            item["security_id"]
            for item in by_symbol[requirement["issuer"]]
            if item["effective_from"] <= requirement["published_on"]
            and (
                item["effective_to"] is None or requirement["published_on"] <= item["effective_to"]
            )
            and item["instrument_type"] == "COMMON_A_SHARE"
        }
        if len(identities) != 1:
            raise ValueError(f"P1_PRIMARY_IDENTITY_AMBIGUOUS:{row['document_id']}")
        security_id = next(iter(identities))
        record_date, ex_date = row["record_dates"][0], row["ex_dates"][0]
        amount = Decimal(row["cash_candidate_per_share"])
        peers = by_ex_date[(security_id, ex_date)]
        if ex_date > "2025-12-31":
            finding = "OUTSIDE_FULL_DATASET_PERIOD"
        elif any(
            event["record_date"] == record_date and Decimal(event["cash_per_share"]) == amount
            for event in peers
        ):
            finding = "EXACT_ACCEPTED_EVENT"
        elif peers:
            finding = "ACCEPTED_EX_DATE_TERM_CONFLICT"
        else:
            finding = "NO_ACCEPTED_EX_DATE_EVENT"
        results.append(
            {
                "document_id": row["document_id"],
                "security_id": security_id,
                "published_on": requirement["published_on"],
                "title": title,
                "url": row["url"],
                "source_sha256": row["source_sha256"],
                "record_date": record_date,
                "ex_date": ex_date,
                "cash_candidate_per_share": str(amount),
                "finding": finding,
                "accepted_peers": [
                    {
                        "record_date": event["record_date"],
                        "cash_per_share": event["cash_per_share"],
                        "source_url": event["source_url"],
                    }
                    for event in peers
                ],
            }
        )
    return sorted(results, key=lambda item: item["document_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    triage, closure, cash = (
        verified(path) for path in (args.triage, args.closure, args.cash_ledger)
    )
    if sha256_file(args.cash_ledger) != closure["input_sha256s"]["cash_ledger"]:
        raise ValueError("P1_CASH_LEDGER_CHANGED")
    if sha256_file(args.master) != closure["input_sha256s"]["master"]:
        raise ValueError("P1_MASTER_CHANGED")
    master = json.loads(args.master.read_bytes())
    inputs = (triage["documents"], closure["remaining_cash_documents"], cash["events"], master)
    findings = crosscheck(*inputs)
    if findings != crosscheck(*(list(reversed(rows)) for rows in inputs)):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "report_version": "P1_OFFICIAL_PRIMARY_CASH_CENSUS_CROSSCHECK_V3",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("triage", args.triage),
                ("closure", args.closure),
                ("cash_ledger", args.cash_ledger),
                ("master", args.master),
            )
        },
        "candidate_count": len(findings),
        "finding_counts": dict(sorted(Counter(row["finding"] for row in findings).items())),
        "findings": findings,
        "input_order_reproducibility": "PASS",
        "acceptance": "COUNTEREXAMPLES_REQUIRE_OFFICIAL_RECONCILIATION_NOT_NEW_ACCEPTED_EVENTS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "findings"}, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
