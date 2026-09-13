"""Resume retained corporate-action document queues by type, without promoting leads."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_sse_cninfo import fetch

VERSION = "R5_CA_SOURCE_BATCH_V1"


def leads(root: Path) -> list[dict]:
    rows = {}
    for path in sorted((root / "metadata").glob("capital-adjustment-p???.json")):
        meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
        if sha256_file(path) != meta["sha256"]:
            raise ValueError("SOURCE_CHECKSUM_MISMATCH")
        for item in json.loads(path.read_bytes())["announcements"]:
            url = "https://static.cninfo.com.cn/" + item["adjunctUrl"]
            rows[url] = dict(
                url=url,
                issuer=item["secCode"],
                title=item["announcementTitle"],
                published_on=datetime.fromtimestamp(item["announcementTime"] / 1000, UTC)
                .date()
                .isoformat(),
                queue_type="RESTRUCTURING_CAPITAL_ADJUSTMENT",
            )
    for item in json.loads((root / "merger-implementation-leads-v1.json").read_bytes()):
        rows.setdefault(item["url"], {**item, "queue_type": "MERGER_CONVERSION"})
    return sorted(rows.values(), key=lambda r: (r["queue_type"], r["published_on"], r["url"]))


def run(root: Path) -> dict:
    existing = {}
    for path in sorted(root.rglob("*.pdf.meta.json")):
        meta = json.loads(path.read_bytes())
        pdf = Path(str(path).removesuffix(".meta.json"))
        if pdf.exists() and meta.get("http_status") == 200:
            if sha256_file(pdf) != meta["sha256"]:
                raise ValueError("SOURCE_CHECKSUM_MISMATCH")
            existing[meta["url"]] = pdf

    def acquire(row: dict) -> dict:
        url = row["url"]
        if not url.startswith("https://static.cninfo.com.cn/finalpage/"):
            raise ValueError("NON_OFFICIAL_SOURCE")
        key = canonical_sha256(url)
        receipt = root / "batch-v1" / "receipts" / (key + ".json")
        if receipt.exists():
            result = json.loads(receipt.read_bytes())
            if result["url"] != url:
                raise ValueError("RECEIPT_IDENTITY_MISMATCH")
            if (
                result.get("source_path")
                and sha256_file(root / result["source_path"]) != result["source_sha256"]
            ):
                raise ValueError("SOURCE_CHECKSUM_MISMATCH")
            return result
        result = {
            **row,
            "parser_version": VERSION,
            "support_state": "DOCUMENT_LEAD_NOT_ACCEPTED_EVENT",
        }
        try:
            path = existing.get(url)
            if path is None:
                path = root / "batch-v1" / "pdf" / (key + ".pdf")
                fetch(root, path.relative_to(root).as_posix(), url)
            meta = json.loads(Path(str(path) + ".meta.json").read_bytes())
            if not path.read_bytes().startswith(b"%PDF") or sha256_file(path) != meta["sha256"]:
                raise ValueError("PDF_OR_CHECKSUM_INVALID")
            result.update(
                source_path=path.relative_to(root).as_posix(),
                source_sha256=meta["sha256"],
                retrieved_at_utc=meta["retrieved_at_utc"],
                retrieval_status="PASS",
            )
        except Exception as exc:
            # Persist exhausted bounded attempts; reruns do not hammer an unavailable URL.
            result.update(retrieval_status="UNAVAILABLE", error=type(exc).__name__, reason=str(exc))
        write_immutable(receipt, canonical_json_bytes(result) + b"\n")
        print(
            json.dumps(
                {
                    "queue": row["queue_type"],
                    "issuer": row["issuer"],
                    "retrieval": result["retrieval_status"],
                }
            ),
            flush=True,
        )
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(acquire, leads(root)))
    report = dict(
        parser_version=VERSION,
        documents=results,
        document_leads=len(results),
        accepted_events=None,
        census_status="PARTIAL_SOURCE_DOCUMENTS_NOT_EVENT_CENSUS",
        failures=sum(r["retrieval_status"] != "PASS" for r in results),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(root / "batch-v1/source-manifest.json", canonical_json_bytes(report) + b"\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.root)
    print(json.dumps({k: v for k, v in report.items() if k != "documents"}))


if __name__ == "__main__":
    main()
