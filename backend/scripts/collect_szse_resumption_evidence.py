"""Collect official CNINFO resumption leads for unresolved SZSE suspension facts."""

import argparse
import calendar
import functools
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path
from threading import Event, Lock

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date
from scripts.recover_distribution_metadata import collect_window


def load_checkpoint(root: Path, start: date, end: date) -> dict | None:
    checkpoint = root / "metadata-v1" / f"{start}-{end}-checkpoint.json"
    if not checkpoint.exists():
        return None
    value = json.loads(checkpoint.read_bytes())
    if value["manifest_sha256"] != canonical_sha256(
        {key: item for key, item in value.items() if key != "manifest_sha256"}
    ):
        raise ValueError("RESUMPTION_CHECKPOINT_CHANGED")
    for source in value["sources"]:
        path = root / "metadata-v1" / f"{start}-{end}-p{source['params']['pageNum']:03}.json"
        if sha256_file(path) != source["sha256"]:
            raise ValueError("RESUMPTION_SOURCE_CHANGED")
    return value


def months() -> list[tuple[date, date]]:
    return [
        (date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1]))
        for year in range(2010, 2026)
        for month in range(1, 13)
    ]


def queue_rows(results: list[dict], unresolved: list[dict]) -> list[dict]:
    earliest = {}
    for fact in unresolved:
        day = fact["suspended_at"][:10].replace("/", "-")
        earliest[fact["symbol"]] = min(day, earliest.get(fact["symbol"], day))
    rows = {}
    for result in results:
        for item in result.get("records", []):
            published = publication_date(item["announcementTime"])
            symbol = item["secCode"]
            if symbol not in earliest or published < earliest[symbol]:
                continue
            url = "https://static.cninfo.com.cn/" + item["adjunctUrl"]
            identity = (symbol, item["announcementTime"], url)
            previous = rows.get(item["announcementId"])
            if previous and previous["identity"] != identity:
                raise ValueError("CONFLICTING_CNINFO_ANNOUNCEMENT_IDENTITY")
            rows[item["announcementId"]] = {
                "identity": identity,
                "announcement_id": item["announcementId"],
                "url": url,
                "issuer": symbol,
                "title": item["announcementTitle"],
                "published_on": published,
                "queue_type": "SZSE_OFFICIAL_RESUMPTION_EVIDENCE_PDF",
            }
    return [
        {key: value for key, value in row.items() if key != "identity"}
        for row in sorted(rows.values(), key=lambda item: item["identity"])
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    # ponytail: cache DNS for this bounded batch; use a new batch if the endpoint changes.
    socket.getaddrinfo = functools.lru_cache(maxsize=32)(socket.getaddrinfo)
    socket.getaddrinfo("www.cninfo.com.cn", 443)
    unresolved = json.loads(args.unresolved.read_bytes())
    circuit, circuit_lock = Event(), Lock()
    consecutive_transient_failures = 0

    def collect(window: tuple[date, date]) -> dict:
        nonlocal consecutive_transient_failures
        start, end = window
        if circuit.is_set():
            return {
                "start": str(start),
                "end": str(end),
                "status": "NOT_ATTEMPTED_AFTER_TRANSIENT_NETWORK_CIRCUIT",
                "sources": [],
            }
        checkpoint = args.root / "metadata-v1" / f"{start}-{end}-checkpoint.json"
        for root in (args.root, *args.source_root):
            value = load_checkpoint(root, start, end)
            if value and value["status"] == "COMPLETE_FOR_OFFICIAL_QUERY":
                return value
        sources = []
        try:
            records = collect_window(
                args.root,
                start,
                end,
                sources,
                keyword="复牌",
                category="",
                prefix="metadata-v1",
            )
            value = {
                "start": str(start),
                "end": str(end),
                "status": "COMPLETE_FOR_OFFICIAL_QUERY",
                "records": records,
                "sources": sources,
            }
            with circuit_lock:
                consecutive_transient_failures = 0
        except Exception as exc:
            reason = f"{type(exc).__name__}: {exc}"
            transient = any(
                token in reason
                for token in (
                    "Name or service not known",
                    "Temporary failure in name resolution",
                    "No route to host",
                    "Network is unreachable",
                    "timed out",
                )
            )
            value = {
                "start": str(start),
                "end": str(end),
                "status": "FAILED",
                "error": reason,
                "sources": sources,
            }
            with circuit_lock:
                consecutive_transient_failures = (
                    consecutive_transient_failures + 1 if transient else 0
                )
                if consecutive_transient_failures >= 3 or "HTTP Error 403" in reason:
                    circuit.set()
            if transient:
                print(start, value["status"], 0, flush=True)
                return value
        value["manifest_sha256"] = canonical_sha256(value)
        write_immutable(checkpoint, canonical_json_bytes(value) + b"\n")
        print(start, value["status"], len(value.get("records", [])), flush=True)
        return value

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(collect, months()))
    failures = [result for result in results if result["status"] != "COMPLETE_FOR_OFFICIAL_QUERY"]
    queue = queue_rows(results, unresolved)
    write_immutable(args.root / "resumption-pdf-queue-v1.json", canonical_json_bytes(queue) + b"\n")
    report = {
        "parser_version": "SZSE_RESUMPTION_METADATA_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "source_roots": [str(root) for root in args.source_root],
        "months": len(results),
        "failed_months": len(failures),
        "official_query_records": sum(len(result.get("records", [])) for result in results),
        "target_document_leads": len(queue),
        "failures": failures,
        "acceptance": "DOCUMENT_LEADS_NOT_RESUMPTION_FACTS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.root / "metadata-manifest-v1.json", canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "failures"}))


if __name__ == "__main__":
    main()
