"""Collect bounded official CNINFO evidence for the residual surrender census."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.batch_r5_corporate_action_sources import publication_date
from scripts.collect_distribution_notices import complete_announcements
from scripts.reconcile_sse_cninfo import QUERY, fetch

TARGETS = {
    "000017": ("gssz0000017", "2012-01-01", "2014-06-30"),
    "000030": ("gssz0000030", "2010-01-01", "2013-12-31"),
    "000034": ("gssz0000034", "2010-01-01", "2013-07-31"),
    "000557": ("gssz0000557", "2011-01-01", "2015-12-31"),
    "000587": ("gssz0000587", "2010-01-01", "2011-08-31"),
    "000677": ("gssz0000677", "2012-01-01", "2012-12-31"),
    "000787": ("gssz0000787", "2011-01-01", "2013-05-31"),
    "000820": ("gssz0000820", "2012-01-01", "2014-12-31"),
    "600678": ("gssh0600678", "2011-01-01", "2012-12-31"),
    "600699": ("gssh0600699", "2010-01-01", "2011-12-31"),
    "600757": ("gssh0600757", "2010-01-01", "2011-12-31"),
}
KEYWORDS = ("重整计划", "让渡", "复牌", "恢复上市")


def documents(rows: list[dict]) -> list[dict]:
    unique = {
        "https://static.cninfo.com.cn/" + row["adjunctUrl"]: {
            "announcement_id": str(row["announcementId"]),
            "issuer": str(row["secCode"]),
            "published_on": publication_date(row["announcementTime"]),
            "title": row["announcementTitle"],
            "url": "https://static.cninfo.com.cn/" + row["adjunctUrl"],
        }
        for row in rows
    }
    return sorted(unique.values(), key=lambda row: (row["published_on"], row["url"]))


def collect(root: Path, symbol: str, org_id: str, start: str, end: str) -> dict:
    rows, receipts = [], []
    for keyword in KEYWORDS:
        pages = []
        for page_number in range(1, 101):
            params = {
                "pageNum": page_number,
                "pageSize": 30,
                "column": "sse",
                "tabName": "fulltext",
                "stock": f"{symbol},{org_id}",
                "searchkey": keyword,
                "secid": "",
                "plate": "",
                "category": "",
                "trade": "",
                "seDate": f"{start}~{end}",
                "sortName": "time",
                "sortType": "asc",
                "isHLtitle": "false",
            }
            name = f"metadata/{symbol}/{canonical_sha256(keyword)[:8]}-p{page_number:03}.json"
            page = json.loads(fetch(root, name, QUERY, params))
            page_rows = page.get("announcements") or []
            if any(row["secCode"] != symbol or row["orgId"] != org_id for row in page_rows):
                raise ValueError(f"CNINFO_SECURITY_FILTER_LEAKAGE:{symbol}")
            pages.append(page)
            receipts.append(json.loads((root / (name + ".meta.json")).read_bytes()))
            if not page["hasMore"]:
                break
        else:
            raise ValueError(f"CNINFO_PAGINATION_INCOMPLETE:{symbol}:{keyword}")
        matches = complete_announcements(pages)
        if any(not start <= publication_date(row["announcementTime"]) <= end for row in matches):
            raise ValueError(f"CNINFO_DATE_RANGE_LEAKAGE:{symbol}:{keyword}")
        rows.extend(matches)
    result = documents(rows)
    if result != documents(list(reversed(rows))):
        raise ValueError("INPUT_ORDER_CHANGED")
    return {
        "documents": result,
        "end": end,
        "org_id": org_id,
        "sources": sorted(receipts, key=lambda row: json.dumps(row["params"], sort_keys=True)),
        "start": start,
        "status": "COMPLETE_FOR_BOUNDED_OFFICIAL_QUERIES",
        "symbol": symbol,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    args = parser.parse_args()
    results = [collect(args.root, symbol, *TARGETS[symbol]) for symbol in sorted(TARGETS)]
    report = {
        "acceptance": "DOCUMENT_LEADS_NOT_ACCEPTED_EVENTS",
        "input_order_reproducibility": "PASS",
        "parser_sha256": sha256_file(Path(__file__)),
        "parser_version": "R5_SURRENDER_EVIDENCE_COLLECTION_V1",
        "query_keywords": list(KEYWORDS),
        "results": results,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        args.root / "surrender-evidence-metadata-v1.json",
        canonical_json_bytes(report) + b"\n",
    )
    print(
        json.dumps(
            {
                "documents": sum(len(row["documents"]) for row in results),
                "manifest_sha256": report["manifest_sha256"],
                "symbols": len(results),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
