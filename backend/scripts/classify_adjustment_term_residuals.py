"""Classify retained adjustment-term residuals without accepting events."""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_distribution_cash import verified

RESTRUCTURING = re.compile(
    r"重整|定向转增|股东权益调整|开盘参考价|资本公积金转增股票"
)


def classify(terms: dict, sources: list[dict]) -> dict:
    outcomes = {row["source_sha256"]: row for row in terms["documents"]}
    gaps = {
        row["factor_change"]
        for row in terms["factor_results"]
        if row["status"] == "NO_EXACT_OFFICIAL_TERMS_CANDIDATE"
    }
    rows = []
    for event in sorted(gaps):
        documents = [row for row in sources if event in row["affected_factor_changes"]]
        if not documents:
            raise ValueError(f"RESIDUAL_SOURCE_MISSING:{event}")
        titles = " ".join(row["title"] for row in documents)
        statuses = {outcomes[row["source_sha256"]]["status"] for row in documents}
        if RESTRUCTURING.search(titles):
            classification = "RESTRUCTURING_OR_DIRECTED_CAPITAL_MECHANICS"
        elif "EXACT_DATE_NO_SUPPORTED_TERMS" in statuses:
            classification = "COMPLEX_HOLDER_TERMS"
        elif "NOTICE_DATES_NOT_UNIQUE_OR_FACTOR_MISMATCH" in statuses:
            classification = "DISTRIBUTION_DATE_MISMATCH_OR_OCR"
        elif statuses == {"OFFICIAL_SOURCE_PDF_UNREADABLE"}:
            classification = "OFFICIAL_SOURCE_PDF_UNREADABLE"
        else:
            classification = "UNRESOLVED"
        rows.append(
            {
                "factor_change": event,
                "classification": classification,
                "documents": [
                    {
                        "source_sha256": row["source_sha256"],
                        "title": row["title"],
                        "url": row["url"],
                        "parse_status": outcomes[row["source_sha256"]]["status"],
                    }
                    for row in sorted(documents, key=lambda item: item["url"])
                ],
            }
        )
    counts = Counter(row["classification"] for row in rows)
    return {
        "report_id": "FULL_ADJUSTMENT_TERM_RESIDUAL_CLASSIFICATION_V1",
        "status": "CLASSIFIED_OFFICIAL_SOURCES_NO_EVENT_OR_AUTHORITY_ACCEPTANCE",
        "residual_factor_changes": len(rows),
        "counts": dict(sorted(counts.items())),
        "rows": rows,
        "adjustment_authority_promoted": False,
        "dataset_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--terms", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    terms = verified(args.terms)
    sources = json.loads(args.sources.read_bytes())
    report = classify(terms, sources)
    replay = classify(
        dict(terms, factor_results=list(reversed(terms["factor_results"]))),
        list(reversed(sources)),
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        input_order_reproducibility="PASS",
        inputs=[
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (args.terms, args.sources)
        ],
        parser_sha256=sha256_file(Path(__file__)),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                "residual_factor_changes": report["residual_factor_changes"],
                "counts": report["counts"],
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
