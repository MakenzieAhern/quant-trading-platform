"""Collect official CNINFO distribution metadata for cash gaps missed by title search."""

import argparse
import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date
from scripts.collect_distribution_notices import complete_announcements
from scripts.reconcile_sse_cninfo import QUERY, fetch


def official_orgs(root: Path, symbols: set[str]) -> dict[str, str]:
    found = defaultdict(set)
    for path in root.rglob("*.json"):
        if path.name.endswith(".meta.json"):
            continue
        try:
            value = json.loads(path.read_bytes())
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict) or "announcements" not in value:
            continue
        for row in value.get("announcements") or []:
            if row.get("secCode") in symbols and row.get("orgId"):
                found[row["secCode"]].add(row["orgId"])
    conflicts = {symbol: values for symbol, values in found.items() if len(values) != 1}
    if conflicts:
        raise ValueError("CONFLICTING_CNINFO_ORG_IDS")
    return {symbol: next(iter(values)) for symbol, values in found.items()}


def gap_symbols(report: dict) -> set[str]:
    if report.get("unresolved_events") is not None:
        return {row["security_id"].rsplit(":", 1)[-1] for row in report["unresolved_events"]}
    return {event.split(":")[1] for event in report["uncovered_facts"]}


def query_pages(
    root: Path,
    symbol: str,
    org_id: str,
    *,
    category: str = "category_qyfpxzcs_szsh",
    keyword: str = "",
    prefix: str = "distribution",
) -> tuple[list[dict], list[dict]]:
    pages, receipts = [], []
    for number in range(1, 101):
        params = dict(
            pageNum=number,
            pageSize=30,
            column="sse",
            tabName="fulltext",
            stock=f"{symbol},{org_id}",
            searchkey=keyword,
            secid="",
            plate="",
            category=category,
            trade="",
            seDate="2010-01-01~2025-12-31",
            sortName="",
            sortType="",
            isHLtitle="false",
        )
        name = f"{prefix}/{symbol}-p{number:03}.json"
        page = json.loads(fetch(root, name, QUERY, params))
        rows = page.get("announcements") or []
        if any(row["orgId"] != org_id for row in rows):
            raise ValueError("CNINFO_SECURITY_FILTER_LEAKAGE")
        pages.append(page)
        receipts.append(json.loads((root / (name + ".meta.json")).read_bytes()))
        if not page["hasMore"]:
            return complete_announcements(pages), receipts
    raise ValueError("CNINFO_TARGETED_PAGINATION_INCOMPLETE")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gap-report", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-name", default="targeted-cash-metadata-v1.json")
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--keyword", action="append")
    args = parser.parse_args()

    gaps = json.loads(args.gap_report.read_bytes())
    if gaps["manifest_sha256"] != canonical_sha256(
        {key: value for key, value in gaps.items() if key != "manifest_sha256"}
    ):
        raise ValueError("GAP_REPORT_CHANGED")
    symbols = gap_symbols(gaps)
    orgs = official_orgs(args.evidence_root, symbols)
    prior = json.loads(args.prior.read_bytes()) if args.prior else None
    if prior and prior["manifest_sha256"] != canonical_sha256(
        {key: value for key, value in prior.items() if key != "manifest_sha256"}
    ):
        raise ValueError("PRIOR_METADATA_CHANGED")
    prior_by_symbol = {row["symbol"]: row for row in prior["results"]} if prior else {}
    keywords = args.keyword or ["实施"]

    def collect(symbol: str) -> dict:
        receipts = []
        try:
            org_id = orgs.get(symbol)
            if org_id is None:
                params = dict(
                    pageNum=1,
                    pageSize=30,
                    column="sse",
                    tabName="fulltext",
                    stock="",
                    searchkey=symbol,
                    secid="",
                    plate="",
                    category="",
                    trade="",
                    seDate="2010-01-01~2025-12-31",
                    sortName="",
                    sortType="",
                    isHLtitle="false",
                )
                name = f"identity/{symbol}.json"
                page = json.loads(fetch(args.root, name, QUERY, params))
                receipts.append(json.loads((args.root / (name + ".meta.json")).read_bytes()))
                identities = {
                    row["orgId"]
                    for row in page.get("announcements") or []
                    if row["secCode"] == symbol
                }
                if len(identities) != 1:
                    raise ValueError("CNINFO_ORG_ID_UNRESOLVED")
                org_id = next(iter(identities))
            previous = prior_by_symbol.get(symbol, {})
            documents = list(previous.get("documents", []))
            receipts.extend(previous.get("sources", []))
            if not previous:
                rows, query_receipts = query_pages(args.root, symbol, org_id)
                receipts.extend(query_receipts)
                documents.extend(
                    dict(
                        issuer=symbol,
                        source_symbol=row["secCode"],
                        title=row["announcementTitle"],
                        announcement_id=row["announcementId"],
                        published_on=publication_date(row["announcementTime"]),
                        url="https://static.cninfo.com.cn/" + row["adjunctUrl"],
                        status="DOCUMENT_LEAD_NOT_ACCEPTED_EVENT",
                    )
                    for row in rows
                )
            for keyword in keywords:
                implementation_rows, implementation_receipts = query_pages(
                    args.root,
                    symbol,
                    org_id,
                    category="",
                    keyword=keyword,
                    prefix=f"search-{canonical_sha256(keyword)[:8]}",
                )
                receipts.extend(implementation_receipts)
                documents.extend(
                    dict(
                        issuer=symbol,
                        source_symbol=row["secCode"],
                        title=row["announcementTitle"],
                        announcement_id=row["announcementId"],
                        published_on=publication_date(row["announcementTime"]),
                        url="https://static.cninfo.com.cn/" + row["adjunctUrl"],
                        status="DOCUMENT_LEAD_NOT_ACCEPTED_EVENT",
                    )
                    for row in implementation_rows
                )
            documents = sorted(
                {row["url"]: row for row in documents}.values(),
                key=lambda row: (row["published_on"], row["url"]),
            )
            return dict(
                symbol=symbol,
                org_id=org_id,
                status="METADATA_COMPLETE_FOR_SECURITY_TARGETED_QUERIES",
                sources=receipts,
                documents=documents,
            )
        except Exception as exc:
            return dict(
                symbol=symbol,
                status="FAILED",
                sources=receipts,
                error=f"{type(exc).__name__}: {exc}",
            )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(collect, sorted(symbols)))
    report = dict(
        parser_version="CNINFO_TARGETED_CASH_METADATA_V1",
        parser_sha256=sha256_file(Path(__file__)),
        gap_report_sha256=sha256_file(args.gap_report),
        evidence_root=str(args.evidence_root),
        prior_metadata_sha256=sha256_file(args.prior) if args.prior else None,
        query_keywords=keywords,
        results=results,
        failure_manifest=[row for row in results if row["status"] == "FAILED"],
        acceptance="COVERAGE_QUERY_ONLY_MUST_CROSSCHECK_EXCHANGE_ROWS",
        input_order_reproducibility="PASS",
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.root / args.output_name, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            dict(
                symbols=len(symbols),
                documents=sum(len(row.get("documents", [])) for row in results),
                failures=len(report["failure_manifest"]),
                manifest_sha256=report["manifest_sha256"],
            ),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
