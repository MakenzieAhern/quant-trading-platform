"""Bind visually reviewed scan-only SZSE resumption pages to current gaps."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_szse_resumptions import bind_resumptions


def accepted_reviews(scan: dict, reviews: list[dict]) -> list[dict]:
    documents = {row["source_sha256"]: row for row in scan["documents"]}
    evidence = []
    for review in sorted(reviews, key=canonical_json_bytes):
        row = documents.get(review["source_sha256"])
        if row is None or row["ocr_candidate_dates"] != [review["resumed_at"]]:
            raise ValueError("REVIEW_NOT_BOUND_TO_UNIQUE_OCR_DATE")
        if review["pdf_page"] != 1 or review["review_status"] != "EXACT_DATE_CONFIRMED":
            raise ValueError("OFFICIAL_PAGE_VISUAL_REVIEW_INCOMPLETE")
        evidence.append(
            {
                "symbol": row["issuer"],
                "resumed_at": review["resumed_at"],
                "title": row["title"],
                "url": row["url"],
                "published_on": row["published_on"],
                "retrieved_at_utc": row["retrieved_at_utc"],
                "source_sha256": row["source_sha256"],
                "ocr_cache_sha256": row["ocr_cache_sha256"],
                "execution_open_blocked": review["execution_open_blocked"],
                "review": review,
            }
        )
    return evidence


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("scan", "review", "unresolved", "suspensions", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    scan = json.loads(args.scan.read_bytes())
    if scan["manifest_sha256"] != canonical_sha256(
        {key: value for key, value in scan.items() if key != "manifest_sha256"}
    ):
        raise ValueError("SCAN_MANIFEST_CHANGED")
    reviews = json.loads(args.review.read_bytes())
    unresolved = json.loads(args.unresolved.read_bytes())
    suspensions = json.loads(args.suspensions.read_bytes())["szse"]
    evidence = accepted_reviews(scan, reviews)
    accepted, remaining = bind_resumptions(unresolved, suspensions, evidence)
    if len(accepted) != len(reviews):
        raise ValueError("REVIEWED_DATE_DID_NOT_BIND_ONE_CURRENT_GAP")
    if (accepted, remaining) != bind_resumptions(
        list(reversed(unresolved)), list(reversed(suspensions)), list(reversed(evidence))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "parser_version": "SZSE_RETAINED_SCAN_VISUAL_REVIEW_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "scan_input_sha256": sha256_file(args.scan),
        "review_input_sha256": sha256_file(args.review),
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "suspensions_input_sha256": sha256_file(args.suspensions),
        "accepted_resumptions": accepted,
        "accepted_count": len(accepted),
        "remaining_count": len(remaining),
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
