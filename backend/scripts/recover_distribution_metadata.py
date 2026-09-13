"""Recover only missing date ranges from the retained descending CNINFO year queries."""

import argparse
import calendar
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date
from scripts.collect_distribution_notices import complete_announcements
from scripts.reconcile_sse_cninfo import QUERY, fetch


def recovery_ranges(year, rows):
    dates = [publication_date(r["announcementTime"]) for r in rows]
    if dates != sorted(dates, reverse=True):
        raise ValueError("RETAINED_ORDER_NOT_DESCENDING")
    cutoff = date.fromisoformat(min(dates)) if dates else date(year, 12, 31)
    if cutoff.year != year:
        raise ValueError("RETAINED_YEAR_MISMATCH")
    # Re-query the boundary day: a page may end halfway through its announcements.
    return [
        (date(year, month, 1), min(date(year, month, calendar.monthrange(year, month)[1]), cutoff))
        for month in range(1, cutoff.month + 1)
    ]


def reconcile(rows, total):
    unique = {}
    for row in rows:
        key = row["announcementId"]
        identity = (row["secCode"], row["adjunctUrl"], row["announcementTime"])
        if key in unique:
            old = unique[key]
            if identity != (old["secCode"], old["adjunctUrl"], old["announcementTime"]):
                raise ValueError("CONFLICTING_ANNOUNCEMENT_IDENTITY")
        else:
            unique[key] = row
    if len(unique) != total:
        raise ValueError(f"YEAR_CENSUS_COUNT_MISMATCH:{len(unique)}:{total}")
    return sorted(unique.values(), key=lambda r: r["announcementId"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    prior_path = args.root / "implementation-metadata-v2.json"
    prior = json.loads(prior_path.read_bytes())
    if (
        canonical_sha256({k: v for k, v in prior.items() if k != "manifest_sha256"})
        != prior["manifest_sha256"]
    ):
        raise ValueError("PRIOR_MANIFEST_CHANGED")

    def recover(result):
        year = result["year"]
        if result["status"] == "METADATA_COMPLETE_FOR_QUERY":
            return result
        checkpoint = args.root / f"recovery-v1/year-{year}.json"
        if checkpoint.exists():
            return json.loads(checkpoint.read_bytes())
        receipts, retained, totals = [], [], set()
        try:
            for meta in result["sources"]:
                path = args.root / f"implementation-{year}-p{meta['params']['pageNum']:03}.json"
                if sha256_file(path) != meta["sha256"]:
                    raise ValueError("RETAINED_PAGE_CHANGED")
                page = json.loads(path.read_bytes())
                retained.extend(page.get("announcements") or [])
                totals.add(page["totalAnnouncement"])
            ranges = recovery_ranges(year, retained)
            recovered = []
            for start, end in ranges:
                pages, seen = [], set()
                for number in range(1, 101):
                    params = dict(
                        pageNum=number,
                        pageSize=30,
                        column="sse",
                        tabName="fulltext",
                        stock="",
                        searchkey="实施",
                        secid="",
                        plate="",
                        category="category_qyfpxzcs_szsh",
                        trade="",
                        seDate=f"{start}~{end}",
                        sortName="",
                        sortType="",
                        isHLtitle="false",
                    )
                    name = f"recovery-v1/{start}-{end}-p{number:03}.json"
                    page = json.loads(fetch(args.root, name, QUERY, params))
                    receipts.append(json.loads((args.root / (name + ".meta.json")).read_bytes()))
                    rows = page.get("announcements") or []
                    ids = {r["announcementId"] for r in rows}
                    if seen & ids:
                        raise ValueError("REPEATED_PAGE_STOP")
                    if any(
                        not str(start) <= publication_date(r["announcementTime"]) <= str(end)
                        for r in rows
                    ):
                        raise ValueError("QUERY_DATE_RANGE_LEAKAGE")
                    seen.update(ids)
                    pages.append(page)
                    if not page["hasMore"]:
                        break
                recovered.extend(complete_announcements(pages))
            if len(totals) > 1:
                raise ValueError("RETAINED_TOTAL_CHANGED")
            # With no retained pages all twelve independently complete month queries cover the year.
            total = next(iter(totals)) if totals else len(recovered)
            rows = reconcile([*retained, *recovered], total)
            output = dict(
                year=year,
                status="METADATA_COMPLETE_FOR_QUERY",
                sources=receipts,
                reused_source_count=len(result["sources"]),
                documents=[
                    dict(
                        issuer=r["secCode"],
                        title=r["announcementTitle"],
                        announcement_id=r["announcementId"],
                        published_on=publication_date(r["announcementTime"]),
                        url="https://static.cninfo.com.cn/" + r["adjunctUrl"],
                        status="DOCUMENT_LEAD_NOT_ACCEPTED_EVENT",
                    )
                    for r in rows
                ],
            )
        except Exception as exc:
            output = dict(
                year=year, status="FAILED", sources=receipts, error=f"{type(exc).__name__}: {exc}"
            )
        write_immutable(checkpoint, canonical_json_bytes(output) + b"\n")
        print(year, output["status"], len(output.get("documents", [])), flush=True)
        return output

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(recover, prior["results"]))
    report = dict(
        parser_version="CNINFO_MISSING_RANGE_RECOVERY_V1",
        parser_sha256=sha256_file(Path(__file__)),
        prior_manifest_sha256=sha256_file(prior_path),
        results=results,
        failure_manifest=[r for r in results if r["status"] == "FAILED"],
        acceptance="COVERAGE_QUERY_ONLY_MUST_CROSSCHECK_EXCHANGE_ROWS",
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        args.root / "implementation-metadata-recovery-v1.json", canonical_json_bytes(report) + b"\n"
    )


if __name__ == "__main__":
    main()
