"""OCR retained low-text SZSE gap documents; never accept OCR-derived events."""

import argparse
import json
import re
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_cash_public_substitutions import ocr_pages, ocr_runtime, verified
from scripts.build_szse_resumption_gap_queue import suspension_intervals
from scripts.reconcile_szse_resumptions import (
    REJECTED_TITLE,
    exact_resume_dates,
    non_equity_resumption_title,
    official_document_text,
)


def select_candidates(records: list[dict], intervals: dict) -> list[dict]:
    selected = {}
    for row in sorted(records, key=canonical_json_bytes):
        if row["text_characters"] >= 60:
            continue
        affected = sorted(
            [value["fact"]["security_id"], value["fact"]["suspended_at"]]
            for value in intervals.get(row["issuer"], [])
            if value["start"] <= row["published_on"] < value["end"]
        )
        if affected:
            key = (row["issuer"], row["published_on"], row["source_sha256"])
            selected.setdefault(key, {**row, "affected_suspensions": affected})
    return [selected[key] for key in sorted(selected)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--suspensions", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    unresolved = json.loads(args.unresolved.read_bytes())
    suspensions = json.loads(args.suspensions.read_bytes())["szse"]
    intervals = suspension_intervals(unresolved, suspensions)
    records, inputs = [], [args.unresolved, args.suspensions]
    for path in sorted(args.staging.glob("full-szse-resumption*/**/source-manifest.json")):
        manifest = verified(path)
        inputs.append(path)
        for document in manifest["documents"]:
            if document["retrieval_status"] != "PASS" or document["issuer"] not in intervals:
                continue
            if REJECTED_TITLE.search(document["title"]) or non_equity_resumption_title(
                document["title"]
            ):
                continue
            root = path.parent.parent
            text = official_document_text(root, document)
            records.append(
                {
                    **document,
                    "source_root": str(root),
                    "source_manifest": str(path),
                    "text_characters": len(re.sub(r"\s+", "", text)),
                }
            )
    queue = select_candidates(records, intervals)
    if queue != select_candidates(list(reversed(records)), intervals):
        raise ValueError("INPUT_ORDER_CHANGED")
    write_immutable(args.output_root / "queue.json", canonical_json_bytes(queue) + b"\n")

    from rapidocr import RapidOCR

    runtime, engine, results = ocr_runtime(), RapidOCR(), []
    for number, row in enumerate(queue, 1):
        source = Path(row["source_root"]) / row["source_path"]
        if sha256_file(source) != row["source_sha256"]:
            raise ValueError("SOURCE_CHECKSUM_MISMATCH")
        cache = args.output_root / "ocr" / f"{row['source_sha256']}.json"
        pages, cache_hash = ocr_pages(source, cache, row["source_sha256"], runtime, engine)
        dates = exact_resume_dates("\n".join(pages), row["published_on"])
        results.append(
            {
                **row,
                "ocr_cache_path": str(cache),
                "ocr_cache_sha256": cache_hash,
                "ocr_candidate_dates": dates,
                "event_acceptance": "NOT_PERFORMED_REQUIRES_OFFICIAL_PAGE_CORROBORATION",
            }
        )
        print(number, len(queue), row["issuer"], dates, flush=True)
    report = {
        "parser_version": "SZSE_RETAINED_SCAN_GAP_INDEX_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "inputs": [{"path": str(path), "sha256": sha256_file(path)} for path in inputs],
        "runtime": runtime,
        "selection": "RETAINED_PDF_UNDER_60_TEXT_CHARACTERS_IN_CURRENT_UNRESOLVED_INTERVAL",
        "documents": results,
        "document_count": len(results),
        "candidate_date_documents": sum(bool(row["ocr_candidate_dates"]) for row in results),
        "accepted_events": 0,
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output_root / "manifest.json", canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "documents"}))


if __name__ == "__main__":
    main()
