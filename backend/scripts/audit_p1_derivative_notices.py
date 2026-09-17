"""Scope non-primary bond, option and buyback notices to accepted issuer cash."""

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose

DERIVATIVE = re.compile(r"停止转股|转股价格|股票期权.*行权价格|回购价格上限")


def classify(requirements, triage, prior_ids, cash):
    by_id = {row["document_id"]: row for row in triage}
    by_symbol = defaultdict(list)
    for row in cash:
        event = row["event"]
        by_symbol[event["security_id"]["value"].split(":")[-1]].append(row)
    closed = []
    for requirement in requirements:
        document_id = requirement["document_id"]
        if document_id in prior_ids or not DERIVATIVE.search(requirement["title"]):
            continue
        row = by_id[document_id]
        if (
            row["candidate_class"] != "CASH_ONLY"
            or row["cash_candidate_per_share"] is None
            or row["record_dates"]
            or row["ex_dates"]
            or row["preferred_instrument_marker"]
        ):
            continue
        candidates = [
            accepted
            for accepted in by_symbol[requirement["issuer"]]
            if -10
            <= (
                date.fromisoformat(accepted["event"]["ex_date"])
                - date.fromisoformat(requirement["published_on"])
            ).days
            <= 75
            and Decimal(accepted["event"]["cash_per_share"])
            == Decimal(row["cash_candidate_per_share"])
            and accepted["event"]["source_url"].startswith(
                "https://static.cninfo.com.cn/finalpage/"
            )
            and accepted["event"]["source_provider"].startswith("OFFICIAL_ISSUER_CNINFO_")
            and accepted["event"]["source_url"] != row["url"]
        ]
        if len(candidates) != 1:
            continue
        accepted = candidates[0]
        closed.append(
            {
                "document_id": document_id,
                "affected_events": requirement["affected_events"],
                "issuer": requirement["issuer"],
                "title": requirement["title"],
                "published_on": requirement["published_on"],
                "url": row["url"],
                "source_sha256": row["source_sha256"],
                "text_cache_sha256": row["text_cache_sha256"],
                "cash_per_share": row["cash_candidate_per_share"],
                "accepted_event_checksum": accepted["event_checksum"],
                "accepted_event_ex_date": accepted["event"]["ex_date"],
                "accepted_primary_source_url": accepted["event"]["source_url"],
                "classification": "NON_PRIMARY_DERIVATIVE_EXACT_ACCEPTED_ISSUER_EVENT",
            }
        )
    return sorted(closed, key=lambda row: row["document_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "closure",
        "triage",
        "prior",
        "cash-ledger",
        "source-manifest",
        "source-root",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    closure, triage, prior, cash, sources = (
        verified(path)
        for path in (args.closure, args.triage, args.prior, args.cash_ledger, args.source_manifest)
    )
    if triage["closure_sha256"] != sha256_file(args.closure):
        raise ValueError("DERIVATIVE_TRIAGE_CHANGED")
    ids = {row["document_id"] for row in prior["closed"]}
    inputs = (closure["remaining_cash_documents"], triage["documents"], cash["events"])
    closed = classify(*inputs[:2], ids, inputs[2])
    if closed != classify(
        *(list(reversed(rows)) for rows in inputs[:2]), ids, list(reversed(inputs[2]))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    by_url = {row["url"]: row for row in sources["documents"]}
    for row in closed:
        source = by_url[row["url"]]
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != row["issuer"]
            or source["title"] != row["title"]
            or source["published_on"] != row["published_on"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("DERIVATIVE_OFFICIAL_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        parsed = diagnose(extracted["pages"], row["issuer"])
        if (
            extracted["source_sha256"] != row["source_sha256"]
            or parsed["candidate_class"] != "CASH_ONLY"
            or parsed["record_dates"]
            or parsed["ex_dates"]
            or Decimal(parsed["cash_candidate_per_share"]) != Decimal(row["cash_per_share"])
        ):
            raise ValueError("DERIVATIVE_NOTICE_TERMS_CHANGED")
    report = {
        "report_version": "P1_NON_PRIMARY_DERIVATIVE_CASH_SCOPE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("closure", args.closure),
                ("triage", args.triage),
                ("prior", args.prior),
                ("cash_ledger", args.cash_ledger),
                ("source_manifest", args.source_manifest),
            )
        },
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "closed": closed,
        "input_order_reproducibility": "PASS",
        "no_new_economic_event_created": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
