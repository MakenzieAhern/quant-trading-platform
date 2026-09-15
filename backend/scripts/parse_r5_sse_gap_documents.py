"""Parse a bounded, exactly reconciled SSE ST gap-document batch."""

import argparse
import io
import json
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from pypdf import PdfReader

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.sse_st_events import extract, normalize


def verified(path: Path) -> dict:
    document = json.loads(path.read_bytes())
    body = {key: value for key, value in document.items() if key != "manifest_sha256"}
    if document["manifest_sha256"] != canonical_sha256(body):
        raise ValueError(f"INPUT_MANIFEST_CHANGED:{path}")
    return document


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reconciliation", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, action="append", required=True)
    parser.add_argument("--source-root", type=Path, action="append", required=True)
    parser.add_argument("--text-root", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if len(args.source_manifest) != len(args.source_root):
        raise ValueError("SOURCE_MANIFEST_ROOT_COUNT_MISMATCH")

    reconciliation = verified(args.reconciliation)
    sources = {}
    for manifest_path, source_root in zip(args.source_manifest, args.source_root, strict=True):
        for row in verified(manifest_path)["documents"]:
            announcement_id = row.get("announcement_id") or Path(urlparse(row["url"]).path).stem
            sources[str(announcement_id)] = (row, source_root)

    results, text_inputs = [], []
    for checkpoint in reconciliation["results"]:
        for record in checkpoint["records"]:
            cn = record["cninfo"][0]
            announcement_id = str(cn["announcementId"])
            result = {
                "announcement_id": announcement_id,
                "symbol": cn["secCode"],
                "status": "PARSER_UNRESOLVED",
            }
            try:
                source, source_root = sources[announcement_id]
                pdf = source_root / source["source_path"]
                if sha256_file(pdf) != source["source_sha256"]:
                    raise ValueError("PDF_SOURCE_CHANGED")
                cache = (
                    args.text_root / f"{source['source_sha256']}.json" if args.text_root else None
                )
                if cache and cache.exists():
                    cached = json.loads(cache.read_bytes())
                    if cached["source_sha256"] != source["source_sha256"]:
                        raise ValueError("TEXT_SOURCE_CHANGED")
                    pages = cached["pages"]
                    extraction_sha256 = sha256_file(cache)
                    text_inputs.append(cache)
                else:
                    pages = [
                        unicodedata.normalize("NFKC", page.extract_text() or "")
                        for page in PdfReader(io.BytesIO(pdf.read_bytes())).pages
                    ]
                    extraction_sha256 = canonical_sha256(pages)
                bound = dict(record, cninfo_document_sha256=source["source_sha256"])
                event = extract(pages, bound)
                event["extraction_sha256"] = extraction_sha256
                event["retrieved_at_utc"] = source["retrieved_at_utc"]
                event["event_sha256"] = canonical_sha256(event)
                result.update(
                    source_sha256=source["source_sha256"],
                    extraction_sha256=extraction_sha256,
                    event=event,
                    status="PARSED_TRANSITION_REQUIRES_LIFECYCLE_AND_COVERAGE_REVIEW",
                )
            except (KeyError, ValueError) as exc:
                result["reason"] = str(exc)
            results.append(result)

    events = [row["event"] for row in results if "event" in row]
    if normalize(events) != normalize(list(reversed(events))):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "scope": "TARGETED_SSE_ST_GAP_DOCUMENTS_NOT_COMPLETE_EVENT_CENSUS",
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in [args.reconciliation, *args.source_manifest, *sorted(set(text_inputs))]
        ],
        "accepted_events": 0,
        "input_order_reproducibility": "PASS",
        "results": results,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.report, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                "parsed": len(events),
                "unresolved": len(results) - len(events),
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
