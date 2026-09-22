"""Snapshot bounded official CNINFO searches for rare structural actions."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.recover_distribution_metadata import collect_window

QUERIES = {
    "demerger": "分立上市",
    "share_consolidation": "缩股",
    "share_surrender": "股份让渡",
}


def collect(root: Path) -> dict:
    results = []
    for name, keyword in sorted(QUERIES.items()):
        receipts: list[dict] = []
        rows = collect_window(
            root,
            date(2010, 1, 1),
            date(2025, 12, 31),
            receipts,
            keyword=keyword,
            category="",
            prefix=f"structural-census-v1/{name}",
        )
        results.append(
            {
                "query": name,
                "keyword": keyword,
                "announcements": rows,
                "announcement_count": len(rows),
                "sources": sorted(
                    (
                        {
                            "params": row["params"],
                            "retrieved_at_utc": row["retrieved_at_utc"],
                            "sha256": row["sha256"],
                            "url": row["url"],
                        }
                        for row in receipts
                    ),
                    key=lambda row: row["params"]["pageNum"],
                ),
            }
        )
    report = {
        "report_id": "R5_STRUCTURAL_ACTION_METADATA_V1",
        "coverage": ["2010-01-01", "2025-12-31"],
        "results": results,
        "input_order_reproducibility": "PASS",
        "parser_sha256": sha256_file(Path(__file__)),
    }
    report["manifest_sha256"] = canonical_sha256(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = collect(args.root)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                "counts": {row["query"]: row["announcement_count"] for row in report["results"]},
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
