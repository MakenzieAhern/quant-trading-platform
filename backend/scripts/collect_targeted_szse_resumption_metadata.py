"""Collect bounded all-announcement CNINFO metadata for unresolved SZSE resumptions."""

import argparse
import functools
import json
import socket
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path
from threading import Event, Lock

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date
from scripts.collect_distribution_notices import complete_announcements
from scripts.reconcile_sse_cninfo import QUERY, fetch
from scripts.reconcile_szse_resumptions import unresolved_facts


def query_windows(unresolved: list[dict], suspensions: list[dict], days: int) -> list[dict]:
    starts = defaultdict(list)
    for row in suspensions:
        starts[row["symbol"]].append(date.fromisoformat(row["suspended_at"][:10].replace("/", "-")))
    result = []
    for row in unresolved:
        start = date.fromisoformat(row["suspended_at"][:10].replace("/", "-"))
        next_start = min((value for value in starts[row["symbol"]] if value > start), default=None)
        end = min(start + timedelta(days=days - 1), date(2025, 12, 31))
        if next_start is not None:
            end = min(end, next_start - timedelta(days=1))
        result.append({**row, "start": str(start), "end": str(max(start, end))})
    return sorted(result, key=lambda row: (row["start"], row["security_id"]))


def queue_rows(results: list[dict], processed_urls: set[str]) -> list[dict]:
    rows = {}
    for result in results:
        affected = (result["security_id"], result["suspended_at"])
        for item in result.get("records", []):
            url = "https://static.cninfo.com.cn/" + item["adjunctUrl"]
            if url in processed_urls:
                continue
            identity = (
                str(item["secCode"]),
                publication_date(item["announcementTime"]),
                item["announcementTitle"],
                url,
            )
            key = str(item["announcementId"])
            previous = rows.get(key)
            if previous and previous["identity"] != identity:
                raise ValueError("CONFLICTING_CNINFO_ANNOUNCEMENT_IDENTITY")
            row = previous or {
                "identity": identity,
                "announcement_id": key,
                "url": url,
                "issuer": identity[0],
                "title": identity[2],
                "published_on": identity[1],
                "queue_type": "SZSE_TARGETED_ALL_ANNOUNCEMENT_RESUMPTION_EVIDENCE",
                "affected_suspensions": [],
            }
            row["affected_suspensions"].append(affected)
            rows[key] = row
    return [
        {
            **{key: value for key, value in row.items() if key != "identity"},
            "affected_suspensions": sorted(set(row["affected_suspensions"])),
        }
        for row in sorted(rows.values(), key=lambda value: value["identity"])
    ]


def retry_windows(windows: list[dict], report: dict) -> list[dict]:
    failed = {(row["security_id"], row["suspended_at"]) for row in report["failures"]}
    return [row for row in windows if (row["security_id"], row["suspended_at"]) in failed]


def split_failed_windows(report: dict, days: int) -> list[dict]:
    if days < 1:
        raise ValueError("SPLIT_DAYS_MUST_BE_POSITIVE")
    windows = []
    for failure in report["failures"]:
        if failure["status"] != "FAILED":
            raise ValueError("SPLIT_REQUIRES_FAILED_WINDOW")
        start, end = date.fromisoformat(failure["start"]), date.fromisoformat(failure["end"])
        if start > end:
            raise ValueError("FAILED_WINDOW_REVERSED")
        identity = {key: failure[key] for key in ("security_id", "symbol", "suspended_at")}
        while start <= end:
            boundary = min(start + timedelta(days=days - 1), end)
            windows.append({**identity, "start": str(start), "end": str(boundary)})
            start = boundary + timedelta(days=1)
    return sorted(windows, key=lambda row: (row["start"], row["security_id"]))


def offset_windows(windows: list[dict], offset_days: int) -> list[dict]:
    result = []
    for row in windows:
        start = date.fromisoformat(row["start"]) + timedelta(days=offset_days)
        if start <= date.fromisoformat(row["end"]):
            result.append({**row, "start": str(start)})
    return result


def check_page_progress(page: dict, seen: set[tuple[str, ...]]) -> None:
    signature = tuple(str(row["announcementId"]) for row in page.get("announcements") or [])
    if page["hasMore"] and (not signature or signature in seen):
        raise ValueError("TARGETED_RESUMPTION_PAGINATION_NONPROGRESS")
    seen.add(signature)


def org_ids(root: Path, symbols: set[str]) -> dict[str, str]:
    values = defaultdict(set)
    for path in sorted(root.rglob("*.json")):
        receipt = Path(str(path) + ".meta.json")
        if not receipt.exists():
            continue
        meta = json.loads(receipt.read_bytes())
        if meta.get("url") != QUERY or sha256_file(path) != meta.get("sha256"):
            continue
        page = json.loads(path.read_bytes())
        for row in page.get("announcements") or []:
            symbol, org_id = str(row.get("secCode", "")), row.get("orgId")
            if symbol in symbols and org_id:
                values[symbol].add(str(org_id))
    conflicts = {symbol: sorted(items) for symbol, items in values.items() if len(items) != 1}
    missing = sorted(symbols - values.keys())
    if conflicts:
        raise ValueError(f"CNINFO_ORG_ID_CONFLICT:{conflicts}")
    if missing:
        raise ValueError(f"CNINFO_ORG_ID_MISSING:{missing}")
    return {symbol: next(iter(items)) for symbol, items in values.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--org-metadata-root", type=Path, required=True)
    parser.add_argument("--suspensions", type=Path, required=True)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--existing-manifest", type=Path, action="append", default=[])
    parser.add_argument("--retry-failures-from", type=Path)
    parser.add_argument("--split-failed-windows-days", type=int)
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--window-offset-days", type=int, default=0)
    parser.add_argument("--page-size", type=int, choices=(30, 100), default=30)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    if args.window_days < 1 or args.window_offset_days < 0:
        raise ValueError("WINDOW_DAYS_MUST_BE_POSITIVE")

    socket.getaddrinfo = functools.lru_cache(maxsize=32)(socket.getaddrinfo)
    socket.getaddrinfo("www.cninfo.com.cn", 443)
    unresolved = unresolved_facts(json.loads(args.unresolved.read_bytes()))
    suspensions = json.loads(args.suspensions.read_bytes())["szse"]
    if args.split_failed_windows_days is not None:
        if not args.retry_failures_from:
            raise ValueError("SPLIT_REQUIRES_FAILURE_MANIFEST")
        prior = json.loads(args.retry_failures_from.read_bytes())
        if prior["manifest_sha256"] != canonical_sha256(
            {key: value for key, value in prior.items() if key != "manifest_sha256"}
        ):
            raise ValueError("FAILURE_MANIFEST_CHANGED")
        windows = split_failed_windows(prior, args.split_failed_windows_days)
        identities = {(row["security_id"], row["suspended_at"]) for row in unresolved}
        if any((row["security_id"], row["suspended_at"]) not in identities for row in windows):
            raise ValueError("FAILED_WINDOW_OUTSIDE_UNRESOLVED_SET")
    else:
        windows = offset_windows(
            query_windows(unresolved, suspensions, args.window_days + args.window_offset_days),
            args.window_offset_days,
        )
        if args.retry_failures_from:
            windows = retry_windows(windows, json.loads(args.retry_failures_from.read_bytes()))
    organizations = org_ids(args.org_metadata_root, {row["symbol"] for row in windows})
    processed_urls = {
        row["url"]
        for path in args.existing_manifest
        for row in json.loads(path.read_bytes())["documents"]
    }
    circuit, lock = Event(), Lock()
    consecutive_transient_failures = 0

    def collect(window: dict) -> dict:
        nonlocal consecutive_transient_failures
        identity = canonical_sha256(
            {key: window[key] for key in ("security_id", "suspended_at", "start", "end")}
        )[:16]
        checkpoint = args.root / "metadata-v1" / f"{window['symbol']}-{identity}.json"
        if checkpoint.exists():
            value = json.loads(checkpoint.read_bytes())
            if value["manifest_sha256"] != canonical_sha256(
                {key: item for key, item in value.items() if key != "manifest_sha256"}
            ):
                raise ValueError("TARGETED_RESUMPTION_CHECKPOINT_CHANGED")
            return value
        if circuit.is_set():
            return {**window, "status": "NOT_ATTEMPTED_AFTER_TRANSIENT_NETWORK_CIRCUIT"}
        pages, sources, seen_pages = [], [], set()
        try:
            for number in range(1, 101):
                params = {
                    "pageNum": number,
                    "pageSize": args.page_size,
                    "column": "szse",
                    "tabName": "fulltext",
                    "stock": f"{window['symbol']},{organizations[window['symbol']]}",
                    "searchkey": "",
                    "secid": "",
                    "plate": "",
                    "category": "",
                    "trade": "",
                    "seDate": f"{window['start']}~{window['end']}",
                    "sortName": "time",
                    "sortType": "asc",
                    "isHLtitle": "false",
                }
                name = f"metadata-v1/{window['symbol']}-{identity}-p{number:03}.json"
                page = json.loads(fetch(args.root, name, QUERY, params))
                sources.append(json.loads((args.root / (name + ".meta.json")).read_bytes()))
                check_page_progress(page, seen_pages)
                pages.append(page)
                if not page["hasMore"]:
                    break
            else:
                raise ValueError("TARGETED_RESUMPTION_QUERY_EXCEEDS_100_PAGES")
            records = complete_announcements(pages)
            if any(
                not window["start"] <= publication_date(row["announcementTime"]) <= window["end"]
                for row in records
            ):
                raise ValueError("TARGETED_RESUMPTION_DATE_RANGE_LEAKAGE")
            value = {
                **window,
                "status": "COMPLETE_FOR_OFFICIAL_QUERY",
                "records": records,
                "sources": sources,
            }
            with lock:
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
            value = {**window, "status": "FAILED", "error": reason, "sources": sources}
            with lock:
                consecutive_transient_failures = (
                    consecutive_transient_failures + 1 if transient else 0
                )
                if consecutive_transient_failures >= 3 or "HTTP Error 403" in reason:
                    circuit.set()
        value["manifest_sha256"] = canonical_sha256(value)
        write_immutable(checkpoint, canonical_json_bytes(value) + b"\n")
        print(
            window["symbol"],
            window["start"],
            value["status"],
            len(value.get("records", [])),
            flush=True,
        )
        return value

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(collect, windows))
    failures = [row for row in results if row["status"] != "COMPLETE_FOR_OFFICIAL_QUERY"]
    queue = queue_rows(results, processed_urls)
    reversed_queue = queue_rows(list(reversed(results)), processed_urls)
    if queue != reversed_queue:
        raise ValueError("INPUT_ORDER_CHANGED")
    write_immutable(args.root / "resumption-pdf-queue-v1.json", canonical_json_bytes(queue) + b"\n")
    report = {
        "parser_version": "SZSE_TARGETED_ALL_ANNOUNCEMENT_METADATA_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "suspensions_input_sha256": sha256_file(args.suspensions),
        "existing_manifest_sha256s": [sha256_file(path) for path in args.existing_manifest],
        "retry_failures_from_sha256": (
            sha256_file(args.retry_failures_from) if args.retry_failures_from else None
        ),
        "window_days": (
            args.split_failed_windows_days
            if args.split_failed_windows_days is not None
            else args.window_days
        ),
        "window_offset_days": (
            None if args.split_failed_windows_days is not None else args.window_offset_days
        ),
        "split_failed_windows_days": args.split_failed_windows_days,
        "page_size": args.page_size,
        "query_windows": len(windows),
        "complete_windows": len(results) - len(failures),
        "failed_windows": len(failures),
        "official_query_records": sum(len(row.get("records", [])) for row in results),
        "target_document_leads": len(queue),
        "input_order_reproducibility": "PASS",
        "failures": failures,
        "acceptance": "DOCUMENT_LEADS_NOT_RESUMPTION_FACTS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.root / "metadata-manifest-v1.json", canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key != "failures"},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
