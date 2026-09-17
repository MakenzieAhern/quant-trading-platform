"""Corroborate retained P1 issuer bonus terms against official exchange rows."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.retained_bonus_terms import retained_ratio


def corroborate(triage, requirements, oracle, master):
    by_id = {row["document_id"]: row for row in requirements}
    by_key = {(row["symbol"], row["record_date"], row["ex_date"]): row for row in oracle}
    if len(by_id) != len(requirements) or len(by_key) != len(oracle):
        raise ValueError("DUPLICATE_BONUS_IDENTITY")
    results = []
    for row in triage:
        if (
            not row["bonus_candidate_per_share"]
            or len(row["record_dates"]) != 1
            or len(row["ex_dates"]) != 1
            or row["preferred_instrument_marker"]
        ):
            continue
        requirement = by_id[row["document_id"]]
        symbol, record, ex = requirement["issuer"], row["record_dates"][0], row["ex_dates"][0]
        matched = by_key.get((symbol, record, ex))
        identities = {
            item["security_id"]
            for item in master
            if item["symbol"] == symbol
            and item["instrument_type"] == "COMMON_A_SHARE"
            and item["effective_from"] <= record < ex <= (item["effective_to"] or "2025-12-31")
        }
        if (
            not matched
            or len(identities) != 1
            or not requirement["published_on"] <= record < ex <= "2025-12-31"
            or matched["ratio_consistency"] != "SINGLE_DISPLAYED_RATIO"
            or {Decimal(e["ratio"]) for e in matched["evidence"]}
            != {Decimal(row["bonus_candidate_per_share"])}
        ):
            continue
        results.append(
            {
                "document_id": row["document_id"],
                "affected_events": requirement["affected_events"],
                "security_id": next(iter(identities)),
                "issuer": symbol,
                "url": row["url"],
                "source_sha256": row["source_sha256"],
                "text_cache_sha256": row["text_cache_sha256"],
                "record_date": record,
                "ex_date": ex,
                "bonus_ratio": str(Decimal(row["bonus_candidate_per_share"])),
                "exchange_evidence_sha256": matched["evidence_sha256"],
                "candidate_class": row["candidate_class"],
                "classification": "EXACT_OFFICIAL_BONUS_SOURCE_TERMS_ACCOUNTING_PENDING",
            }
        )
    return sorted(results, key=lambda item: item["document_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--triage", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--closure", type=Path)
    source.add_argument("--queue", type=Path)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    triage, oracle, sources = (
        verified(path) for path in (args.triage, args.oracle, args.source_manifest)
    )
    requirements = (
        verified(args.closure)["remaining_cash_documents"]
        if args.closure
        else json.loads(args.queue.read_bytes())
    )
    master = json.loads(args.master.read_bytes())
    if (
        triage["closure_sha256" if args.closure else "source_requirements_sha256"]
        != sha256_file(args.closure or args.queue)
        or triage["source_manifest_sha256"] != sha256_file(args.source_manifest)
        or (
            args.closure
            and sha256_file(args.master) != verified(args.closure)["input_sha256s"]["master"]
        )
    ):
        raise ValueError("BONUS_CROSSCHECK_INPUT_CHANGED")
    inputs = (triage["documents"], requirements, oracle["rows"], master)
    rows = corroborate(*inputs)
    if rows != corroborate(*(list(reversed(value)) for value in inputs)):
        raise ValueError("INPUT_ORDER_CHANGED")
    by_url = {row["url"]: row for row in sources["documents"]}
    for row in rows:
        source = by_url[row["url"]]
        pdf = Path(source["source_path"])
        if not pdf.is_absolute():
            pdf = args.source_root / pdf
        pdf = pdf.resolve()
        cache = args.source_root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            not pdf.is_relative_to(args.source_root.parent.resolve())
            or source["retrieval_status"] != "PASS"
            or source["issuer"] != row["issuer"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError(f"P1_BONUS_SOURCE_CHANGED:{row['document_id']}")
        extracted = json.loads(cache.read_bytes())
        if (
            extracted["source_sha256"] != row["source_sha256"]
            or retained_ratio(extracted["pages"], row["issuer"]) != Decimal(row["bonus_ratio"])
            or notice_dates(extracted["pages"]) != ([row["record_date"]], [row["ex_date"]])
        ):
            raise ValueError(f"P1_BONUS_TERMS_CHANGED:{row['document_id']}")
    report = {
        "report_version": "P1_OFFICIAL_BONUS_SOURCE_TERMS_V2"
        if args.queue
        else "P1_OFFICIAL_BONUS_SOURCE_TERMS_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("triage", args.triage),
                ("queue" if args.queue else "closure", args.queue or args.closure),
                ("oracle", args.oracle),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
            )
        },
        "corroborated_documents": len(rows),
        "candidate_classes": dict(sorted(Counter(row["candidate_class"] for row in rows).items())),
        "corroborated": rows,
        "input_order_reproducibility": "PASS",
        "new_economic_events_created": 0,
        "p1_requirements_closed": 0,
        "reason_not_closed": "CASH_LEGS_AND_CORPORATE_ACTION_ACCOUNTING_NOT_YET_RECONCILED",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "corroborated"}))


if __name__ == "__main__":
    main()
