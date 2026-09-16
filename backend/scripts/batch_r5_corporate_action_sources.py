"""Resume retained corporate-action document queues by type, without promoting leads."""

import argparse
import functools
import json
import re
import socket
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from threading import Event, Lock
from zoneinfo import ZoneInfo

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_sse_cninfo import fetch

VERSION = "R5_CA_SOURCE_BATCH_V4"
BATCH = "batch-v4"


def publication_date(milliseconds: int) -> str:
    # CNINFO historical epochs can be midnight in Shanghai, not midnight UTC.
    return datetime.fromtimestamp(milliseconds / 1000, ZoneInfo("Asia/Shanghai")).date().isoformat()


def leads(root: Path) -> list[dict]:
    rows = {}
    rights_pages = sorted((root / "batch-v1/metadata").glob("rights-issuance-p???.json"))
    if rights_pages:
        announcements = {}
        totals = set()
        for path in rights_pages:
            meta = json.loads(Path(str(path) + ".meta.json").read_bytes())
            if sha256_file(path) != meta["sha256"]:
                raise ValueError("SOURCE_CHECKSUM_MISMATCH")
            page = json.loads(path.read_bytes())
            totals.add(page["totalAnnouncement"])
            for item in page["announcements"]:
                announcements[item["announcementId"]] = item
        if totals != {len(announcements)}:
            raise ValueError("RIGHTS_METADATA_PAGINATION_INCOMPLETE")
        for item in announcements.values():
            title = unicodedata.normalize("NFKC", item["announcementTitle"])
            if not (
                re.search(r"配股(?:\(A股\)|公开)?发行(?:的)?公告", title) or "配股发行结果" in title
            ):
                continue
            url = "https://static.cninfo.com.cn/" + item["adjunctUrl"]
            rows[url] = dict(
                url=url,
                issuer=item["secCode"],
                title=item["announcementTitle"],
                published_on=publication_date(item["announcementTime"]),
                queue_type="RIGHTS_ISSUANCE_AND_RESULT",
            )
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
                published_on=publication_date(item["announcementTime"]),
                queue_type="RESTRUCTURING_CAPITAL_ADJUSTMENT",
            )
    merger_leads = root / "merger-implementation-leads-v1.json"
    if merger_leads.exists():
        for item in json.loads(merger_leads.read_bytes()):
            rows.setdefault(item["url"], {**item, "queue_type": "MERGER_CONVERSION"})
    if not rows:
        raise ValueError("NO_SOURCE_QUEUE")
    return sorted(rows.values(), key=lambda r: (r["queue_type"], r["published_on"], r["url"]))


def run(
    root: Path,
    *,
    queue: Path | None = None,
    batch: str = BATCH,
    source_roots: tuple[Path, ...] = (),
    workers: int = 2,
) -> dict:
    existing = {}
    circuit, circuit_lock = Event(), Lock()
    consecutive_unavailable = 0
    receipts = sorted(
        {
            path
            for source_root in (root, *source_roots)
            for path in source_root.rglob("*.pdf.meta.json")
        }
    )
    for path in receipts:
        meta = json.loads(path.read_bytes())
        pdf = Path(str(path).removesuffix(".meta.json"))
        if pdf.exists() and meta.get("http_status") == 200:
            if sha256_file(pdf) != meta["sha256"]:
                raise ValueError("SOURCE_CHECKSUM_MISMATCH")
            if meta["url"] in existing and sha256_file(existing[meta["url"]]) != meta["sha256"]:
                raise ValueError("CONFLICTING_SOURCE_SNAPSHOTS")
            existing[meta["url"]] = pdf

    def acquire(row: dict) -> dict:
        nonlocal consecutive_unavailable
        if circuit.is_set():
            raise RuntimeError("ACCESS_CIRCUIT_OPEN")
        url = row["url"]
        if not url.startswith("https://static.cninfo.com.cn/finalpage/"):
            raise ValueError("NON_OFFICIAL_SOURCE")
        key = canonical_sha256(url)
        receipt = root / batch / "receipts" / (key + ".json")
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
                legacy = root / "batch-v1" / "receipts" / (key + ".json")
                if legacy.exists():
                    previous = json.loads(legacy.read_bytes())
                    if previous["retrieval_status"] == "UNAVAILABLE":
                        raise ValueError(
                            "PRESERVED_EXHAUSTED_RETRIEVAL:" + previous.get("reason", "")
                        )
                path = root / batch / "pdf" / (key + ".pdf")
                fetch(root, path.relative_to(root).as_posix(), url)
            meta = json.loads(Path(str(path) + ".meta.json").read_bytes())
            if sha256_file(path) != meta["sha256"]:
                raise ValueError("SOURCE_CHECKSUM_INVALID")
            is_pdf = path.read_bytes().startswith(b"%PDF")
            if url.lower().endswith(".pdf") and not is_pdf:
                raise ValueError("PDF_INVALID")
            result.update(
                source_path=(
                    path.relative_to(root) if path.is_relative_to(root) else path
                ).as_posix(),
                source_sha256=meta["sha256"],
                retrieved_at_utc=meta["retrieved_at_utc"],
                retrieval_status="PASS" if is_pdf else "NON_PDF_ATTACHMENT",
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
        with circuit_lock:
            consecutive_unavailable = (
                consecutive_unavailable + 1 if result["retrieval_status"] == "UNAVAILABLE" else 0
            )
            if consecutive_unavailable >= 20:
                circuit.set()
        return result

    with ThreadPoolExecutor(max_workers=workers) as pool:
        candidates = json.loads(queue.read_bytes()) if queue else leads(root)
        candidates = sorted(
            candidates, key=lambda r: (r["queue_type"], r["published_on"], r["url"])
        )
        results = list(pool.map(acquire, candidates))
    report = dict(
        parser_version=VERSION,
        documents=results,
        document_leads=len(results),
        accepted_events=None,
        census_status="PARTIAL_SOURCE_DOCUMENTS_NOT_EVENT_CENSUS",
        failures=sum(r["retrieval_status"] == "UNAVAILABLE" for r in results),
        non_pdf_attachments=sum(r["retrieval_status"] == "NON_PDF_ATTACHMENT" for r in results),
    )
    if queue:
        report["input_queue_sha256"] = sha256_file(queue)
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(root / batch / "source-manifest.json", canonical_json_bytes(report) + b"\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--batch", default=BATCH)
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    parser.add_argument("--workers", type=int, choices=range(1, 3), default=2)
    args = parser.parse_args()
    # ponytail: cache DNS for this bounded batch; re-run a batch if the CDN endpoint changes.
    socket.getaddrinfo = functools.lru_cache(maxsize=32)(socket.getaddrinfo)
    report = run(
        args.root,
        queue=args.queue,
        batch=args.batch,
        source_roots=tuple(args.source_root),
        workers=args.workers,
    )
    print(json.dumps({k: v for k, v in report.items() if k != "documents"}))


if __name__ == "__main__":
    main()
