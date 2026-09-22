"""Certify the 2010-2025 ordinary-A rights census from official CNINFO results."""

from __future__ import annotations

import argparse
import json
import re
from collections.abc import Iterable
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

START = "2010-01-01"
END = "2025-12-31"
QUERY = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
STATIC = "https://static.cninfo.com.cn/"


def _ordinary_a_result(title: str) -> bool:
    if "更正" in title or not re.search(r"配股发行结果.*公告", title):
        return False
    return "A股" in title or not re.search(r"[BH]股", title)


def _load_pages(paths: Iterable[Path]) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    announcements: dict[str, dict[str, Any]] = {}
    sources = []
    totals: set[int] = set()
    pages: set[int] = set()
    total_pages: set[int] = set()
    for path in paths:
        meta_path = Path(str(path) + ".meta.json")
        meta = json.loads(meta_path.read_bytes())
        if (
            meta["url"] != QUERY
            or sha256_file(path) != meta["sha256"]
            or meta["params"]["searchkey"] != "配股发行公告"
            or meta["params"]["seDate"] != f"{START}~{END}"
        ):
            raise ValueError(f"RIGHTS_QUERY_SOURCE_CHANGED:{path}")
        payload = json.loads(path.read_bytes())
        totals.add(payload["totalAnnouncement"])
        total_pages.add(payload["totalpages"])
        pages.add(meta["params"]["pageNum"])
        for row in payload["announcements"]:
            prior = announcements.setdefault(row["announcementId"], row)
            if prior != row:
                raise ValueError(f"CONFLICTING_ANNOUNCEMENT:{row['announcementId']}")
        sources.append({"path": str(path), "sha256": meta["sha256"]})
    if len(totals) != 1 or len(total_pages) != 1:
        raise ValueError("RIGHTS_QUERY_TOTAL_CHANGED")
    total = totals.pop()
    expected_pages = total_pages.pop() + 1
    if pages != set(range(1, expected_pages + 1)) or len(announcements) != total:
        raise ValueError("RIGHTS_QUERY_PAGINATION_INCOMPLETE")
    return announcements, sorted(sources, key=lambda row: row["path"])


def certify(
    metadata_paths: Iterable[Path], inventory_path: Path, master_path: Path
) -> dict[str, Any]:
    announcements, sources = _load_pages(metadata_paths)
    inventory = json.loads(inventory_path.read_bytes())
    master = json.loads(master_path.read_bytes())
    master_ids = {row["security_id"] for row in master}
    result_notices = {
        STATIC + row["adjunctUrl"]: row
        for row in announcements.values()
        if _ordinary_a_result(row["announcementTitle"])
        and f"CN-A:{'SSE' if row['pageColumn'].startswith('SH') else 'SZSE'}:{row['secCode']}"
        in master_ids
    }
    event_checksums: set[str] = set()
    assigned_notices: set[str] = set()
    for row in inventory["rows"]:
        event = row["event"]
        security = event["security_id"]
        security_id = security["value"] if isinstance(security, dict) else security
        record = date.fromisoformat(event["record_date"])
        effective = date.fromisoformat(event["effective_date"])
        row_notices = {
            url
            for url, notice in result_notices.items()
            if security_id.endswith(":" + notice["secCode"])
            and record
            <= datetime.fromtimestamp(
                notice["announcementTime"] / 1000, timezone(timedelta(hours=8))
            ).date()
            <= effective + timedelta(days=45)
        }
        if (
            security_id not in master_ids
            or event["action_type"] != "RIGHTS_RELATED_EVENT"
            or event["rights_event_class"] != "STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE"
            or not START <= event["effective_date"] <= END
            or row["event_checksum"] in event_checksums
            or not row_notices
            or row.get("issues")
        ):
            raise ValueError(f"RIGHTS_EVENT_NOT_CENSUS_SAFE:{row.get('event_id')}")
        event_checksums.add(row["event_checksum"])
        assigned_notices.update(row_notices)
    if assigned_notices != set(result_notices) or inventory["unresolved_events"] != 0:
        raise ValueError("RIGHTS_RESULT_NOTICE_COVERAGE_INCOMPLETE")

    report = {
        "report_id": "R5_FULL_RIGHTS_CENSUS_V1",
        "parser_version": "FULL_RIGHTS_CENSUS_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "coverage": [START, END],
        "authority": "CNINFO_OFFICIAL_ISSUER_RESULT_NOTICE_CENSUS",
        "query_announcements": len(announcements),
        "result_notices": len(result_notices),
        "rights_events": len(event_checksums),
        "securities_with_rights_events": len(
            {
                (
                    row["event"]["security_id"].get("value")
                    if isinstance(row["event"]["security_id"], dict)
                    else row["event"]["security_id"]
                )
                for row in inventory["rows"]
            }
        ),
        "unclassified_result_notices": 0,
        "unresolved_events": 0,
        "subscription_policy": "DECLINE_SUBSCRIPTION_NO_MONETIZATION_V1",
        "sources": sources,
        "inventory_path": str(inventory_path),
        "inventory_sha256": sha256_file(inventory_path),
        "master_path": str(master_path),
        "master_sha256": sha256_file(master_path),
        "input_order_reproducibility": "PASS",
        "checksum_repeatability": "PASS",
        "full_census_status": "PASS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--master", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = list(args.metadata.glob("rights-issuance-p[0-9][0-9][0-9].json"))
    report = certify(paths, args.inventory, args.master)
    if certify(reversed(paths), args.inventory, args.master) != report:
        raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "sources"}))


if __name__ == "__main__":
    main()
