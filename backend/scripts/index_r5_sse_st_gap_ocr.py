"""OCR only cached official documents linked to current SSE ST chain gaps."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_cash_public_substitutions import ocr_pages, ocr_runtime, verified

VERSION = "R5_SSE_ST_GAP_OCR_INDEX_V1"


def select_candidates(queue: dict, chain: dict) -> list[dict]:
    symbols = {row["security_id"].rsplit(":", 1)[-1] for row in chain["rows"] if row["gaps"]}
    return sorted(
        (row for row in queue["candidates"] if row["symbol"] in symbols),
        key=lambda row: (row["symbol"], row["date"], row["id"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--chain", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    from rapidocr import RapidOCR

    inputs = [args.queue, args.chain, args.source_manifest]
    queue, chain, sources = map(verified, inputs)
    source_root = (args.source_root or args.root).resolve()
    by_id = {
        str(row["announcement_id"]): row
        for row in sources["documents"]
        if row["retrieval_status"] == "PASS"
    }
    runtime, engine, results = ocr_runtime(), RapidOCR(), []
    for number, row in enumerate(select_candidates(queue, chain), 1):
        source = by_id.get(str(row["id"]))
        if not source or source["source_sha256"] != row["sha"]:
            raise ValueError(f"SOURCE_NOT_CHECKSUM_BOUND:{row['id']}")
        pdf = (args.root / source["source_path"]).resolve()
        if not pdf.is_relative_to(source_root) or sha256_file(pdf) != row["sha"]:
            raise ValueError(f"SOURCE_CHECKSUM_MISMATCH:{row['id']}")
        cache = args.output_root / f"{row['sha']}.json"
        _, cache_sha256 = ocr_pages(pdf, cache, row["sha"], runtime, engine)
        results.append(
            {
                "announcement_id": str(row["id"]),
                "symbol": row["symbol"],
                "title": row["title"],
                "source_sha256": row["sha"],
                "source_url": source["url"],
                "retrieved_at_utc": source["retrieved_at_utc"],
                "ocr_cache_sha256": cache_sha256,
                "event_acceptance": "NOT_PERFORMED",
            }
        )
        print(number, row["symbol"], row["id"], flush=True)
    report = {
        "report_version": VERSION,
        "runtime": runtime,
        "inputs": [{"path": str(path), "sha256": sha256_file(path)} for path in inputs],
        "documents": results,
        "document_count": len(results),
        "accepted_events": 0,
        "input_order_reproducibility": "PASS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output_root / "manifest.json", canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"documents", "inputs"}}))


if __name__ == "__main__":
    main()
