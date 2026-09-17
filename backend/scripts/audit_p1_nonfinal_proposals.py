"""Out-scope official proposals with no final distribution terms or dates."""

import argparse
import json
import re
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.triage_p1_remaining_distribution_docs import diagnose

PROPOSAL_TITLE = re.compile(r"提议.*分红|拟实施.*中期分红|授权董事会.*(?:中期分红|中期利润分配)")
CONDITIONAL_TEXT = re.compile(r"尚需|不确定|后续.*方案|届时.*公告|提请.*授权")


def classify(requirements, triage, already_closed):
    by_id = {row["document_id"]: row for row in triage}
    rows = []
    for requirement in requirements:
        document_id = requirement["document_id"]
        if document_id in already_closed or not PROPOSAL_TITLE.search(requirement["title"]):
            continue
        row = by_id[document_id]
        if (
            row["candidate_class"] != "NEITHER"
            or row["record_dates"]
            or row["ex_dates"]
            or row["preferred_instrument_marker"]
        ):
            continue
        rows.append(
            {
                "document_id": document_id,
                "affected_events": requirement["affected_events"],
                "issuer": requirement["issuer"],
                "title": requirement["title"],
                "url": requirement["url"],
                "source_sha256": row["source_sha256"],
                "text_cache_sha256": row["text_cache_sha256"],
                "classification": "NONFINAL_PROPOSAL_NO_EXECUTABLE_CASH_OR_BONUS_TERMS",
            }
        )
    return sorted(rows, key=lambda item: item["document_id"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--triage", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    closure, triage, prior, sources = (
        verified(path) for path in (args.closure, args.triage, args.prior, args.source_manifest)
    )
    if triage["closure_sha256"] != sha256_file(args.closure):
        raise ValueError("TRIAGE_CLOSURE_CHANGED")
    excluded = {row["document_id"] for row in prior["closed"]}
    rows = classify(closure["remaining_cash_documents"], triage["documents"], excluded)
    if rows != classify(
        list(reversed(closure["remaining_cash_documents"])),
        list(reversed(triage["documents"])),
        excluded,
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    by_url = {row["url"]: row for row in sources["documents"]}
    for row in rows:
        source = by_url[row["url"]]
        pdf = args.source_root / source["source_path"]
        cache = args.source_root / "batch-v1/text" / f"{row['source_sha256']}.json"
        if (
            source["retrieval_status"] != "PASS"
            or source["issuer"] != row["issuer"]
            or source["title"] != row["title"]
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(pdf) != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
        ):
            raise ValueError("PROPOSAL_SOURCE_CHANGED")
        extracted = json.loads(cache.read_bytes())
        text = "\n".join(extracted["pages"])
        parsed = diagnose(extracted["pages"], row["issuer"])
        if (
            extracted["source_sha256"] != row["source_sha256"]
            or parsed["candidate_class"] != "NEITHER"
            or parsed["record_dates"]
            or parsed["ex_dates"]
            or not CONDITIONAL_TEXT.search(re.sub(r"\s+", "", text))
        ):
            raise ValueError("PROPOSAL_NOT_NONFINAL")
    report = {
        "report_version": "P1_OFFICIAL_NONFINAL_PROPOSAL_SCOPE_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            key: sha256_file(path)
            for key, path in (
                ("closure", args.closure),
                ("triage", args.triage),
                ("prior", args.prior),
                ("source_manifest", args.source_manifest),
            )
        },
        "closed_documents": len(rows),
        "closed_facts": sum(len(row["affected_events"]) for row in rows),
        "closed": rows,
        "input_order_reproducibility": "PASS",
        "no_new_economic_event_created": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
