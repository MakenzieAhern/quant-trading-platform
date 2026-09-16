"""Triage retained official P1 distribution PDFs without accepting new events."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import gross_cash
from scripts.retained_bonus_terms import retained_ratio


def diagnose(pages: list[str], symbol: str) -> dict:
    result = {}
    for name, parser in (("cash", gross_cash), ("bonus", retained_ratio)):
        try:
            result[f"{name}_candidate_per_share"] = str(parser(pages, symbol))
            result[f"{name}_parser_error"] = None
        except ValueError as exc:
            result[f"{name}_candidate_per_share"] = None
            result[f"{name}_parser_error"] = str(exc)
    try:
        result["record_dates"], result["ex_dates"] = notice_dates(pages)
        result["date_parser_error"] = None
    except ValueError as exc:
        result["record_dates"], result["ex_dates"] = [], []
        result["date_parser_error"] = str(exc)
    result["preferred_instrument_marker"] = bool(
        re.search(r"优先股(?:代码|简称)", "\n".join(pages))
    )
    result["candidate_class"] = (
        "BOTH"
        if result["cash_candidate_per_share"] and result["bonus_candidate_per_share"]
        else "CASH_ONLY"
        if result["cash_candidate_per_share"]
        else "BONUS_ONLY"
        if result["bonus_candidate_per_share"]
        else "NEITHER"
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    closure, sources = verified(args.closure), verified(args.source_manifest)
    by_url = {row["url"]: row for row in sources["documents"]}
    if len(by_url) != len(sources["documents"]):
        raise ValueError("DUPLICATE_OFFICIAL_SOURCE_URL")
    rows = []
    for requirement in closure["remaining_cash_documents"]:
        source = by_url[requirement["url"]]
        if source["retrieval_status"] != "PASS":
            raise ValueError("P1_REMAINING_SOURCE_NOT_ACQUIRED")
        pdf = args.source_root / source["source_path"]
        if sha256_file(pdf) != source["source_sha256"]:
            raise ValueError("P1_REMAINING_SOURCE_CHANGED")
        cache = args.source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != source["source_sha256"]:
            raise ValueError("P1_REMAINING_EXTRACTION_CHANGED")
        rows.append(
            {
                "document_id": requirement["document_id"],
                "issuer": requirement["issuer"],
                "url": requirement["url"],
                "source_sha256": source["source_sha256"],
                "text_cache_sha256": sha256_file(cache),
                **diagnose(extracted["pages"], requirement["issuer"]),
            }
        )
    rows.sort(key=lambda row: row["document_id"])
    counts = dict(sorted(Counter(row["candidate_class"] for row in rows).items()))
    report = {
        "parser_version": "P1_REMAINING_DISTRIBUTION_DOCUMENT_TRIAGE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "closure_sha256": sha256_file(args.closure),
        "source_manifest_sha256": sha256_file(args.source_manifest),
        "total_documents": len(rows),
        "candidate_counts": counts,
        "preferred_instrument_markers": sum(row["preferred_instrument_marker"] for row in rows),
        "documents": rows,
        "acceptance": "PARSER_CANDIDATES_ONLY_NO_NEW_ECONOMIC_EVENT_ACCEPTED",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
