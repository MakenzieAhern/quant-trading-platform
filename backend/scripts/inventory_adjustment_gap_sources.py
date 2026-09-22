"""Reuse retained official PDFs for adjustment-gap candidates and emit missing-only work."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def inventory(staging: Path, queue: list[dict]) -> tuple[list[dict], list[dict]]:
    wanted = {row["url"]: row for row in queue}
    found = {}
    for metadata_path in staging.glob("**/*.pdf.meta.json"):
        metadata = json.loads(metadata_path.read_bytes())
        url = metadata.get("url")
        if url not in wanted or metadata.get("error") or metadata.get("http_status") != 200:
            continue
        pdf = Path(str(metadata_path).removesuffix(".meta.json"))
        if not pdf.exists() or sha256_file(pdf) != metadata.get("sha256"):
            raise ValueError("RETAINED_SOURCE_CHANGED")
        prior = found.get(url)
        if prior and prior["source_sha256"] != metadata["sha256"]:
            raise ValueError("RETAINED_URL_BYTE_CONFLICT")
        candidate = {
            **wanted[url],
            "source_path": pdf.relative_to(staging).as_posix(),
            "source_sha256": metadata["sha256"],
            "metadata_path": metadata_path.relative_to(staging).as_posix(),
            "metadata_sha256": sha256_file(metadata_path),
            "retrieved_at_utc": metadata["retrieved_at_utc"],
            "retrieval_status": "PASS_RETAINED_OFFICIAL_BYTES",
        }
        if prior is None or candidate["source_path"] < prior["source_path"]:
            found[url] = candidate
    missing = [row for row in queue if row["url"] not in found]
    return [found[url] for url in sorted(found)], sorted(missing, key=lambda row: row["url"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--missing", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_bytes())
    retained, missing = inventory(args.staging, queue)
    if (retained, missing) != inventory(args.staging, list(reversed(queue))):
        raise ValueError("INPUT_ORDER_CHANGED")
    write_immutable(args.inventory, canonical_json_bytes(retained) + b"\n")
    write_immutable(args.missing, canonical_json_bytes(missing) + b"\n")
    report = {
        "report_id": "FULL_ADJUSTMENT_GAP_RETAINED_SOURCES_V1",
        "status": "RETAINED_SOURCE_REUSE_COMPLETE_MISSING_ONLY_QUEUE_READY",
        "candidate_documents": len(queue),
        "retained_official_documents": len(retained),
        "missing_official_documents": len(missing),
        "retained_inventory_sha256": sha256_file(args.inventory),
        "missing_queue_sha256": sha256_file(args.missing),
        "source_retrieval_performed": False,
        "dataset_created": False,
        "input_order_reproducibility": "PASS",
        "inputs": [{"path": str(args.queue), "sha256": sha256_file(args.queue)}],
        "parser_sha256": sha256_file(Path(__file__)),
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
