"""Close P1 cash facts proved by exact official primary or stronger accepted notices."""

import argparse
import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_cash_census_counterexamples import PRIMARY, SECONDARY
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose


def close_facts(triage, requirements, cash, master, source_manifest, source_root, excluded):
    by_id = {row["document_id"]: row for row in requirements}
    by_url = {row["url"]: row for row in source_manifest}
    by_symbol = defaultdict(list)
    by_ex_date = defaultdict(list)
    for row in master:
        by_symbol[row["symbol"]].append(row)
    for row in cash:
        event = row["event"]
        by_ex_date[(event["security_id"]["value"], event["ex_date"])].append(row)
    closed = []
    for row in triage:
        requirement = by_id[row["document_id"]]
        if row["url"] in excluded or row["candidate_class"] not in {"CASH_ONLY", "BOTH"}:
            continue
        if (
            row["preferred_instrument_marker"]
            or row["cash_candidate_per_share"] is None
            or len(row["record_dates"]) != 1
            or len(row["ex_dates"]) != 1
            or row["ex_dates"][0] > "2025-12-31"
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
            continue
        sid, ex = next(iter(identities)), row["ex_dates"][0]
        matches = [
            item
            for item in by_ex_date[(sid, ex)]
            if item["event"]["record_date"] == row["record_dates"][0]
            and Decimal(item["event"]["cash_per_share"]) == Decimal(row["cash_candidate_per_share"])
        ]
        if len(matches) != 1:
            continue
        accepted = matches[0]
        accepted_event = accepted["event"]
        title = requirement["title"]
        primary = bool(PRIMARY.search(title) and not SECONDARY.search(title))
        stronger_accepted = bool(
            accepted_event["source_url"].startswith("https://static.cninfo.com.cn/finalpage/")
            and accepted_event["source_provider"].startswith("OFFICIAL_ISSUER_CNINFO_")
            and re.search(r"实施公告|实施的公告|分派公告", accepted_event["source_document"])
            and not re.search(r"调整|提议|进展|提示|更正|修订", accepted_event["source_document"])
        )
        if not (primary or stronger_accepted):
            continue
        source = by_url[row["url"]]
        pdf = source_root / source["source_path"]
        cache = source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["title"] != requirement["title"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != source["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("P1_MATCHED_CASH_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != source["source_sha256"]:
            raise ValueError("P1_MATCHED_CASH_EXTRACTION_CHANGED")
        parsed = diagnose(extracted["pages"], requirement["issuer"])
        if (
            parsed["candidate_class"] != row["candidate_class"]
            or parsed["record_dates"] != row["record_dates"]
            or parsed["ex_dates"] != row["ex_dates"]
            or Decimal(parsed["cash_candidate_per_share"])
            != Decimal(accepted_event["cash_per_share"])
        ):
            raise ValueError("P1_MATCHED_CASH_TERMS_CHANGED")
        closed.append(
            {
                "document_id": row["document_id"],
                "affected_events": requirement["affected_events"],
                "security_id": sid,
                "url": row["url"],
                "source_sha256": row["source_sha256"],
                "accepted_event_checksum": accepted["event_checksum"],
                "accepted_source_url": accepted_event["source_url"],
                "record_date": row["record_dates"][0],
                "ex_date": ex,
                "cash_per_share": str(Decimal(row["cash_candidate_per_share"])),
                "bonus_component_status": (
                    "SOURCE_TERMS_ONLY_ACCOUNTING_PENDING"
                    if row["candidate_class"] == "BOTH"
                    else "NONE_DETECTED"
                ),
                "classification": (
                    "OFFICIAL_PRIMARY_NOTICE_EXACT_CORROBORATION"
                    if primary
                    else "STRONGER_ACCEPTED_OFFICIAL_NOTICE_SUBSTITUTION"
                ),
            }
        )
    return sorted(closed, key=lambda item: item["document_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--primary-cash", type=Path, required=True)
    parser.add_argument("--preferred", type=Path, required=True)
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    triage, closure, cash, source_manifest, primary_cash, preferred = (
        verified(path)
        for path in (
            args.triage,
            args.closure,
            args.cash_ledger,
            args.source_manifest,
            args.primary_cash,
            args.preferred,
        )
    )
    master = json.loads(args.master.read_bytes())
    requirements = (
        json.loads(args.queue.read_bytes()) if args.queue else closure["remaining_cash_documents"]
    )
    baseline = {row["document_id"]: row for row in closure["remaining_cash_documents"]}
    if (
        len(baseline) != len(closure["remaining_cash_documents"])
        or len({row["document_id"] for row in requirements}) != len(requirements)
        or any(baseline.get(row["document_id"]) != row for row in requirements)
        or len(triage["documents"]) != len(requirements)
        or {row["document_id"] for row in triage["documents"]}
        != {row["document_id"] for row in requirements}
        or triage["source_requirements_sha256" if args.queue else "closure_sha256"]
        != sha256_file(args.queue or args.closure)
        or triage["source_manifest_sha256"] != sha256_file(args.source_manifest)
        or sha256_file(args.master) != closure["input_sha256s"]["master"]
    ):
        raise ValueError("P1_MATCHED_CASH_INPUT_CHANGED")
    excluded = {row["event"]["source_url"] for row in primary_cash["events"]} | {
        row["url"] for row in preferred["excluded"]
    }
    inputs = (
        triage["documents"],
        requirements,
        cash["events"],
        master,
        source_manifest["documents"],
    )
    closed = close_facts(*inputs, args.source_root, excluded)
    if closed != close_facts(
        *(list(reversed(rows)) for rows in inputs), args.source_root, excluded
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    if args.prior:
        prior = verified(args.prior)
        prior_rows = prior["closed"]
        ids = [row["document_id"] for row in [*prior_rows, *closed]]
        if not prior["no_new_economic_event_created"] or len(ids) != len(set(ids)):
            raise ValueError("P1_MATCHED_CASH_PRIOR_CONFLICT")
        closed = sorted([*prior_rows, *closed], key=lambda row: row["document_id"])
    counts = dict(sorted(Counter(row["classification"] for row in closed).items()))
    report = {
        "report_version": (
            "P1_MATCHED_OFFICIAL_CASH_FACT_CLOSURE_V4"
            if args.prior
            else "P1_MATCHED_OFFICIAL_CASH_FACT_CLOSURE_V3"
            if args.queue
            else "P1_MATCHED_OFFICIAL_CASH_FACT_CLOSURE_V2"
        ),
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("triage", args.triage),
                ("closure", args.closure),
                *([("queue", args.queue)] if args.queue else []),
                ("cash_ledger", args.cash_ledger),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
                ("primary_cash", args.primary_cash),
                ("preferred", args.preferred),
                *([("prior", args.prior)] if args.prior else []),
            )
        },
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "classification_counts": counts,
        "closed": closed,
        "input_order_reproducibility": "PASS",
        "no_new_economic_event_created": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
