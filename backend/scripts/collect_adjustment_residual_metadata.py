"""Collect bounded official CNINFO metadata for unrouted factor changes."""

import argparse
import functools
import json
import socket
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date
from scripts.collect_targeted_szse_resumption_metadata import check_page_progress
from scripts.reconcile_sse_cninfo import QUERY, fetch


def nested_dicts(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from nested_dicts(item)
    elif isinstance(value, list):
        for item in value:
            yield from nested_dicts(item)


def org_ids(paths: list[Path], symbols: set[str]) -> dict[str, str]:
    found = {symbol: set() for symbol in symbols}
    for path in paths:
        for row in nested_dicts(json.loads(path.read_bytes())):
            symbol, org_id = str(row.get("secCode", "")), row.get("orgId")
            if symbol in found and org_id:
                found[symbol].add(str(org_id))
    conflicts = {symbol: sorted(values) for symbol, values in found.items() if len(values) > 1}
    missing = sorted(symbol for symbol, values in found.items() if not values)
    if conflicts:
        raise ValueError(f"CNINFO_ORG_ID_CONFLICT:{conflicts}")
    if missing:
        raise ValueError(f"CNINFO_ORG_ID_MISSING:{missing}")
    return {symbol: next(iter(values)) for symbol, values in found.items()}


def gaps(report: dict, lookback_days: int, post_days: int) -> list[dict]:
    rows = []
    for item in report["uncovered"]:
        security_id, effective_date = item["factor_change"].removeprefix("FACTOR:").rsplit(":", 1)
        effective = date.fromisoformat(effective_date)
        rows.append(
            {
                "factor_change": item["factor_change"],
                "security_id": security_id,
                "symbol": security_id.rsplit(":", 1)[-1],
                "effective_date": effective_date,
                "start": str(effective - timedelta(days=lookback_days)),
                "end": str(effective + timedelta(days=post_days)),
            }
        )
    return sorted(rows, key=lambda row: row["factor_change"])


def complete_bounded_announcements(pages: list[dict]) -> list[dict]:
    totals = {page["totalAnnouncement"] for page in pages}
    rows = [row for page in pages for row in (page.get("announcements") or [])]
    if totals != {len(rows)} or not any(not page["hasMore"] for page in pages):
        raise ValueError("NOTICE_PAGINATION_INCOMPLETE")
    unique = {}
    for row in rows:
        prior = unique.setdefault(row["announcementId"], row)
        if prior != row:
            raise ValueError("NOTICE_PAGINATION_IDENTITY_CONFLICT")
    return sorted(unique.values(), key=lambda row: row["announcementId"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uncovered", type=Path, required=True)
    parser.add_argument("--org-metadata", type=Path, action="append", required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--lookback-days", type=int, default=365)
    parser.add_argument("--post-days", type=int, default=7)
    parser.add_argument("--workers", type=int, choices=(1, 2), default=2)
    parser.add_argument("--output-name", default="bounded-metadata-v1.json")
    args = parser.parse_args()
    if args.lookback_days < 1 or args.post_days < 0:
        raise ValueError("INVALID_QUERY_WINDOW")
    report = json.loads(args.uncovered.read_bytes())
    if report["manifest_sha256"] != canonical_sha256(
        {key: value for key, value in report.items() if key != "manifest_sha256"}
    ):
        raise ValueError("UNCOVERED_REPORT_CHANGED")
    work = gaps(report, args.lookback_days, args.post_days)
    organizations = org_ids(args.org_metadata, {row["symbol"] for row in work})
    if organizations != org_ids(list(reversed(args.org_metadata)), set(organizations)):
        raise ValueError("ORG_METADATA_INPUT_ORDER_CHANGED")
    socket.getaddrinfo = functools.lru_cache(maxsize=32)(socket.getaddrinfo)
    socket.getaddrinfo("www.cninfo.com.cn", 443)

    def collect(row: dict) -> dict:
        identity = canonical_sha256(row)[:16]
        pages, sources, seen_pages = [], [], set()
        try:
            for number in range(1, 101):
                params = {
                    "pageNum": number,
                    "pageSize": 30,
                    "column": "sse",
                    "tabName": "fulltext",
                    "stock": f"{row['symbol']},{organizations[row['symbol']]}",
                    "searchkey": "",
                    "secid": "",
                    "plate": "",
                    "category": "",
                    "trade": "",
                    "seDate": f"{row['start']}~{row['end']}",
                    "sortName": "time",
                    "sortType": "asc",
                    "isHLtitle": "false",
                }
                name = f"metadata/{row['symbol']}-{identity}-p{number:03}.json"
                page = json.loads(fetch(args.root, name, QUERY, params))
                if any(
                    item.get("secCode") != row["symbol"]
                    or item.get("orgId") != organizations[row["symbol"]]
                    for item in page.get("announcements") or []
                ):
                    raise ValueError("CNINFO_SECURITY_FILTER_LEAKAGE")
                check_page_progress(page, seen_pages)
                pages.append(page)
                sources.append(json.loads((args.root / (name + ".meta.json")).read_bytes()))
                if not page["hasMore"]:
                    break
            documents = [
                {
                    "announcement_id": item["announcementId"],
                    "issuer": item["secCode"],
                    "published_on": publication_date(item["announcementTime"]),
                    "title": item["announcementTitle"],
                    "url": "https://static.cninfo.com.cn/" + item["adjunctUrl"],
                }
                for item in complete_bounded_announcements(pages)
            ]
            return {
                **row,
                "status": "METADATA_COMPLETE_FOR_BOUNDED_OFFICIAL_QUERY",
                "documents": documents,
                "sources": sources,
            }
        except Exception as exc:
            return {
                **row,
                "status": "FAILED",
                "sources": sources,
                "error": f"{type(exc).__name__}: {exc}",
            }

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = sorted(pool.map(collect, work), key=lambda row: row["factor_change"])
    output = {
        "report_id": "FULL_ADJUSTMENT_RESIDUAL_CNINFO_METADATA_V1",
        "status": (
            "COMPLETE_BOUNDED_OFFICIAL_METADATA"
            if all(row["status"] != "FAILED" for row in results)
            else "PARTIAL_BOUNDED_OFFICIAL_METADATA"
        ),
        "lookback_days": args.lookback_days,
        "post_days": args.post_days,
        "results": results,
        "failure_manifest": [row for row in results if row["status"] == "FAILED"],
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in [args.uncovered, *sorted(set(args.org_metadata))]
        ],
        "parser_sha256": sha256_file(Path(__file__)),
        "input_order_reproducibility": "PASS",
        "dataset_created": False,
    }
    output["manifest_sha256"] = canonical_sha256(output)
    write_immutable(args.root / args.output_name, canonical_json_bytes(output) + b"\n")
    print(
        json.dumps(
            {
                "factor_changes": len(results),
                "documents": sum(len(row.get("documents", [])) for row in results),
                "failures": len(output["failure_manifest"]),
                "manifest_sha256": output["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
