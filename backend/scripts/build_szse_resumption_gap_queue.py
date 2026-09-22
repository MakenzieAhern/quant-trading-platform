"""Reuse cached CNINFO metadata and bytes for unresolved SZSE resumptions."""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date

CNINFO_QUERY = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
CNINFO_STATIC = "https://static.cninfo.com.cn/"


def suspension_intervals(unresolved: list[dict], suspensions: list[dict]) -> dict[str, list[dict]]:
    starts = defaultdict(list)
    for row in suspensions:
        starts[row["symbol"]].append(row["suspended_at"][:10].replace("/", "-"))
    result = defaultdict(list)
    for row in unresolved:
        start = row["suspended_at"][:10].replace("/", "-")
        end = min((day for day in starts[row["symbol"]] if day > start), default="2026-01-01")
        result[row["symbol"]].append({"start": start, "end": end, "fact": row})
    return result


def candidate_queue(
    announcements: list[tuple[dict, dict]], intervals: dict, processed_urls: set[str]
) -> list[dict]:
    rows = {}
    for item, source in announcements:
        symbol = str(item.get("secCode", ""))
        if symbol not in intervals or not item.get("adjunctUrl"):
            continue
        published_on = publication_date(item["announcementTime"])
        title = re.sub(r"</?em>", "", item["announcementTitle"])
        affected = [
            value["fact"]
            for value in intervals[symbol]
            if value["start"] <= published_on < value["end"]
        ]
        url = CNINFO_STATIC + item["adjunctUrl"]
        if not affected or url in processed_urls:
            continue
        identity = (symbol, published_on, title, url)
        key = str(item["announcementId"])
        previous = rows.get(key)
        if previous and previous["identity"] != identity:
            raise ValueError("CONFLICTING_CNINFO_ANNOUNCEMENT_IDENTITY")
        row = previous or {
            "identity": identity,
            "announcement_id": key,
            "url": url,
            "issuer": symbol,
            "title": title,
            "published_on": published_on,
            "queue_type": "SZSE_TARGETED_RESUMPTION_INTERVAL_EVIDENCE",
            "affected_suspensions": sorted(
                {(value["security_id"], value["suspended_at"]) for value in affected}
            ),
            "metadata_sources": [],
        }
        row["metadata_sources"].append(source)
        rows[key] = row
    return [
        {
            **{key: value for key, value in row.items() if key != "identity"},
            "metadata_sources": sorted(
                {
                    json.dumps(value, sort_keys=True): value for value in row["metadata_sources"]
                }.values(),
                key=lambda value: (value["path"], value["sha256"]),
            ),
        }
        for row in sorted(rows.values(), key=lambda value: value["identity"])
    ]


def cached_urls(roots: list[Path]) -> set[str]:
    result = set()
    for root in roots:
        for receipt in root.rglob("*.pdf.meta.json"):
            meta = json.loads(receipt.read_bytes())
            source = Path(str(receipt).removesuffix(".meta.json"))
            if meta.get("url") and source.exists() and sha256_file(source) == meta.get("sha256"):
                result.add(meta["url"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata-root", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, action="append", default=[])
    parser.add_argument("--suspensions", type=Path, required=True)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--existing-manifest", type=Path, action="append", default=[])
    parser.add_argument("--existing-manifest-root", type=Path, action="append", default=[])
    parser.add_argument("--cached-queue", type=Path, required=True)
    parser.add_argument("--retrieval-queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    suspensions = json.loads(args.suspensions.read_bytes())["szse"]
    unresolved = json.loads(args.unresolved.read_bytes())
    intervals = suspension_intervals(unresolved, suspensions)
    manifest_paths = sorted(
        {
            *args.existing_manifest,
            *(
                path
                for root in args.existing_manifest_root
                for path in root.glob("full-szse-resumption*/**/source-manifest.json")
            ),
        }
    )
    if not manifest_paths:
        raise ValueError("EXISTING_RESUMPTION_MANIFEST_REQUIRED")
    processed_urls = {
        row["url"] for path in manifest_paths for row in json.loads(path.read_bytes())["documents"]
    }
    announcements, metadata_pages = [], []
    for path in sorted(args.metadata_root.rglob("*.json")):
        receipt = Path(str(path) + ".meta.json")
        if not receipt.exists():
            continue
        meta = json.loads(receipt.read_bytes())
        if meta.get("url") != CNINFO_QUERY or sha256_file(path) != meta.get("sha256"):
            continue
        page = json.loads(path.read_bytes())
        rows = page.get("announcements") or []
        if not rows:
            continue
        source = {
            "path": str(path),
            "sha256": meta["sha256"],
            "url": meta["url"],
            "retrieved_at_utc": meta["retrieved_at_utc"],
        }
        metadata_pages.append(source)
        announcements.extend((row, source) for row in rows)
    queue = candidate_queue(announcements, intervals, processed_urls)
    if queue != candidate_queue(list(reversed(announcements)), intervals, processed_urls):
        raise ValueError("INPUT_ORDER_CHANGED")
    local_urls = cached_urls(args.source_root)
    cached = [row for row in queue if row["url"] in local_urls]
    retrieval = [row for row in queue if row["url"] not in local_urls]
    write_immutable(args.cached_queue, canonical_json_bytes(cached) + b"\n")
    write_immutable(args.retrieval_queue, canonical_json_bytes(retrieval) + b"\n")
    covered = {tuple(fact) for row in queue for fact in row["affected_suspensions"]}
    report = {
        "parser_version": "SZSE_CACHED_RESUMPTION_GAP_QUEUE_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "suspensions_input_sha256": sha256_file(args.suspensions),
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "existing_manifest_sha256s": [sha256_file(path) for path in manifest_paths],
        "metadata_page_count": len(metadata_pages),
        "metadata_page_manifest_sha256": canonical_sha256(metadata_pages),
        "unresolved_facts": len(unresolved),
        "facts_with_cached_metadata_candidates": len(covered),
        "facts_without_cached_metadata_candidates": len(unresolved) - len(covered),
        "candidate_documents": len(queue),
        "cached_source_documents": len(cached),
        "targeted_retrieval_documents": len(retrieval),
        "input_order_reproducibility": "PASS",
        "acceptance": "DOCUMENT_LEADS_ONLY_REQUIRE_EXACT_OFFICIAL_RESUMPTION_RECONCILIATION",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
