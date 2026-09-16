"""Close official cash notices whose record and ex-dates both follow 2025."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_cash_census_counterexamples import PRIMARY, SECONDARY
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose


def classify(
    findings: list[dict], triage: list[dict], requirements: list[dict]
) -> tuple[list[dict], list[str]]:
    by_id = {row["document_id"]: row for row in triage}
    required = {row["document_id"]: row for row in requirements}
    closed, boundary_open = [], []
    for item in findings:
        if item["finding"] != "OUTSIDE_FULL_DATASET_PERIOD":
            continue
        row, requirement = by_id[item["document_id"]], required[item["document_id"]]
        if (
            row["candidate_class"] != "CASH_ONLY"
            or row["preferred_instrument_marker"]
            or not PRIMARY.search(requirement["title"])
            or SECONDARY.search(requirement["title"])
            or row["ex_dates"] != [item["ex_date"]]
            or row["record_dates"] != [item["record_date"]]
            or row["cash_candidate_per_share"] != item["cash_candidate_per_share"]
        ):
            raise ValueError("OUT_OF_PERIOD_PRIMARY_TERMS_CHANGED")
        if item["record_date"] <= "2025-12-31":
            boundary_open.append(item["document_id"])
            continue
        if not item["record_date"] <= item["ex_date"] or item["ex_date"] <= "2025-12-31":
            raise ValueError("OUT_OF_PERIOD_DATE_CHAIN_INVALID")
        closed.append(
            {
                "document_id": item["document_id"],
                "affected_events": requirement["affected_events"],
                "security_id": item["security_id"],
                "url": item["url"],
                "source_sha256": item["source_sha256"],
                "record_date": item["record_date"],
                "ex_date": item["ex_date"],
                "classification": "BOTH_ENTITLEMENT_DATES_AFTER_FULL_DATASET_END",
            }
        )
    return sorted(closed, key=lambda row: row["document_id"]), sorted(boundary_open)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--counterexamples", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    counterexamples, triage, closure, sources = (
        verified(path)
        for path in (args.counterexamples, args.triage, args.closure, args.source_manifest)
    )
    if counterexamples["input_sha256s"]["triage"] != sha256_file(args.triage) or counterexamples[
        "input_sha256s"
    ]["closure"] != sha256_file(args.closure):
        raise ValueError("OUT_OF_PERIOD_INPUT_CHANGED")
    inputs = (counterexamples["findings"], triage["documents"], closure["remaining_cash_documents"])
    closed, boundary_open = classify(*inputs)
    if (closed, boundary_open) != classify(*(list(reversed(rows)) for rows in inputs)):
        raise ValueError("INPUT_ORDER_CHANGED")
    by_url = {row["url"]: row for row in sources["documents"]}
    by_id = {row["document_id"]: row for row in triage["documents"]}
    requirements = {row["document_id"]: row for row in closure["remaining_cash_documents"]}
    for item in closed:
        row, source = by_id[item["document_id"]], by_url[item["url"]]
        requirement = requirements[item["document_id"]]
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != requirement["issuer"]
            or source["title"] != requirement["title"]
            or source["source_sha256"] != item["source_sha256"]
            or sha256_file(pdf) != item["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("OUT_OF_PERIOD_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != item["source_sha256"]:
            raise ValueError("OUT_OF_PERIOD_EXTRACTION_CHANGED")
        parsed = diagnose(extracted["pages"], source["issuer"])
        if (
            parsed["candidate_class"] != "CASH_ONLY"
            or parsed["record_dates"] != [item["record_date"]]
            or parsed["ex_dates"] != [item["ex_date"]]
            or parsed["cash_candidate_per_share"] != row["cash_candidate_per_share"]
        ):
            raise ValueError("OUT_OF_PERIOD_REPARSE_CHANGED")
    report = {
        "report_version": "P1_OFFICIAL_CASH_OUT_OF_PERIOD_SCOPE_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("counterexamples", args.counterexamples),
                ("triage", args.triage),
                ("closure", args.closure),
                ("source_manifest", args.source_manifest),
            )
        },
        "excluded_documents": len(closed),
        "excluded_facts": sum(len(row["affected_events"]) for row in closed),
        "year_end_record_date_documents_kept_open": boundary_open,
        "excluded": closed,
        "input_order_reproducibility": "PASS",
        "new_economic_events_created": 0,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "excluded"}))


if __name__ == "__main__":
    main()
