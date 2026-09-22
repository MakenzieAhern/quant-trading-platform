"""Checkpoint official distribution implementation metadata by year, not ticker."""

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date
from scripts.reconcile_sse_cninfo import QUERY, fetch


def complete_announcements(pages):
    totals = {p["totalAnnouncement"] for p in pages}
    rows = [r for p in pages for r in (p.get("announcements") or [])]
    unique = {r["announcementId"]: r for r in rows}
    if (
        len(unique) != len(rows)
        or totals != {len(unique)}
        or not any(not p["hasMore"] for p in pages)
    ):
        raise ValueError("NOTICE_PAGINATION_INCOMPLETE_OR_DUPLICATED")
    return sorted(rows, key=lambda r: r["announcementId"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    category_file = args.root / "list-search.json"
    category_receipt = json.loads(Path(str(category_file) + ".meta.json").read_bytes())
    if sha256_file(category_file) != category_receipt["sha256"]:
        raise ValueError("OFFICIAL_CATEGORY_SOURCE_CHANGED")
    categories = json.loads(category_file.read_bytes())
    if not any(
        r["key"] == "category_qyfpxzcs_szsh" and r["value"] == "权益分派"
        for r in categories["sse"]["category"]
    ):
        raise ValueError("OFFICIAL_CATEGORY_CHANGED")

    def collect(year):
        pages, receipts, seen = [], [], set()
        try:
            for page in range(1, 201):
                params = dict(
                    pageNum=page,
                    pageSize=30,
                    column="sse",
                    tabName="fulltext",
                    stock="",
                    searchkey="实施",
                    secid="",
                    plate="",
                    category="category_qyfpxzcs_szsh",
                    trade="",
                    seDate=f"{year}-01-01~{year}-12-31",
                    sortName="",
                    sortType="",
                    isHLtitle="false",
                )
                name = f"implementation-{year}-p{page:03}.json"
                payload = json.loads(fetch(args.root, name, QUERY, params))
                identifiers = {r["announcementId"] for r in (payload.get("announcements") or [])}
                if seen & identifiers:
                    raise ValueError("REPEATED_PAGE_STOP_NO_FURTHER_REQUESTS_FOR_YEAR")
                seen.update(identifiers)
                pages.append(payload)
                receipts.append(json.loads((args.root / (name + ".meta.json")).read_bytes()))
                if not payload["hasMore"]:
                    break
                if not payload.get("announcements"):
                    raise ValueError("NOTICE_PAGINATION_STALLED")
            rows = complete_announcements(pages)
            documents = [
                dict(
                    issuer=r["secCode"],
                    title=r["announcementTitle"],
                    announcement_id=r["announcementId"],
                    published_on=publication_date(r["announcementTime"]),
                    url="https://static.cninfo.com.cn/" + r["adjunctUrl"],
                    status="DOCUMENT_LEAD_NOT_ACCEPTED_EVENT",
                )
                for r in rows
            ]
            result = dict(
                year=year,
                status="METADATA_COMPLETE_FOR_QUERY",
                sources=receipts,
                documents=documents,
            )
        except Exception as exc:
            result = dict(
                year=year, status="FAILED", sources=receipts, error=f"{type(exc).__name__}: {exc}"
            )
        print(year, result["status"], len(result.get("documents", [])), flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(collect, range(2010, 2026)))
    report = dict(
        parser_version="CNINFO_DISTRIBUTION_METADATA_V2",
        parser_sha256=sha256_file(Path(__file__)),
        category_source_sha256=sha256_file(category_file),
        results=results,
        failure_manifest=[r for r in results if r["status"] == "FAILED"],
        acceptance="COVERAGE_QUERY_ONLY_MUST_CROSSCHECK_EXCHANGE_ROWS",
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        args.root / "implementation-metadata-v2.json", canonical_json_bytes(report) + b"\n"
    )


if __name__ == "__main__":
    main()
