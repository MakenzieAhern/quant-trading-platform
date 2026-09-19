"""Build a high-specificity official-PDF queue for residual factor changes."""

import argparse
import json
import re
from collections import defaultdict
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.build_cash_gap_queue import verified

DIVIDEND = re.compile(r"(?:分红派息|年度权益分派|年度权益分配|特别派息).*(?:实施)?公告")
IMPLEMENTATION = re.compile(
    r"(?:股权分置改革方案(?:\uff08[^\uff09]+\uff09)?实施公告|股权分置改革.*追送股份实施公告|"
    r"重大资产重组追加送股方案实施公告|股权分置改革方案追送对价股份实施公告|"
    r"资本公积金转增股本事项实施(?:的)?公告|缩股方案实施的公告|"
    r"股份变动暨新增股份上市公告书|"
    r"除权参考价.*公告)"
)
TRADING_BOUNDARY = re.compile(
    r"(?:股票恢复上市公告书|恢复上市首日.*(?:提示|开盘参考价)|"
    r"(?:公司股票|股票).*恢复上市.*(?:公告|提示)|"
    r"退市整理期.*(?:开盘参考价|交易).*(?:公告|提示))"
)


def candidate(title: str, days_from_factor: int) -> str | None:
    if DIVIDEND.search(title) and -30 <= days_from_factor <= 0:
        return "OFFICIAL_DISTRIBUTION_TERMS"
    if IMPLEMENTATION.search(title) and -365 <= days_from_factor <= 7:
        return "OFFICIAL_CAPITAL_ACTION_MECHANICS"
    if TRADING_BOUNDARY.search(title) and -30 <= days_from_factor <= 7:
        return "OFFICIAL_TRADING_OR_REFERENCE_BOUNDARY"
    return None


def queue(metadata: dict) -> tuple[list[dict], list[dict]]:
    selected = {}
    coverage = defaultdict(set)
    for result in metadata["results"]:
        effective = date.fromisoformat(result["effective_date"])
        for document in result["documents"]:
            route = candidate(
                document["title"],
                (date.fromisoformat(document["published_on"]) - effective).days,
            )
            if route is None or not document["url"].lower().endswith(".pdf"):
                continue
            row = selected.setdefault(
                document["url"],
                {
                    "affected_factor_changes": set(),
                    "issuer": document["issuer"],
                    "published_on": document["published_on"],
                    "queue_type": "OFFICIAL_ADJUSTMENT_RESIDUAL_CANDIDATE_PDF",
                    "route": route,
                    "title": document["title"],
                    "url": document["url"],
                },
            )
            if row["route"] != route:
                raise ValueError("CANDIDATE_ROUTE_CONFLICT")
            row["affected_factor_changes"].add(result["factor_change"])
            coverage[result["factor_change"]].add(document["url"])
    rows = [
        {**row, "affected_factor_changes": sorted(row["affected_factor_changes"])}
        for row in selected.values()
    ]
    rows.sort(key=lambda row: (row["published_on"], row["url"]))
    uncovered = [
        {
            "factor_change": result["factor_change"],
            "reason": "NO_HIGH_SPECIFICITY_OFFICIAL_DOCUMENT",
        }
        for result in metadata["results"]
        if result["factor_change"] not in coverage
    ]
    return rows, uncovered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    metadata = verified(args.metadata)
    rows, uncovered = queue(metadata)
    replay = queue(dict(metadata, results=list(reversed(metadata["results"]))))
    if (rows, uncovered) != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    write_immutable(args.queue, canonical_json_bytes(rows) + b"\n")
    report = {
        "report_id": "FULL_ADJUSTMENT_RESIDUAL_SOURCE_QUEUE_V1",
        "status": (
            "HIGH_SPECIFICITY_OFFICIAL_SOURCE_QUEUE_COMPLETE"
            if not uncovered
            else "HIGH_SPECIFICITY_OFFICIAL_SOURCE_QUEUE_PARTIAL"
        ),
        "factor_changes": len(metadata["results"]),
        "covered_factor_changes": len(metadata["results"]) - len(uncovered),
        "candidate_documents": len(rows),
        "uncovered": uncovered,
        "queue_sha256": sha256_file(args.queue),
        "input_order_reproducibility": "PASS",
        "inputs": [{"path": str(args.metadata), "sha256": sha256_file(args.metadata)}],
        "parser_sha256": sha256_file(Path(__file__)),
        "dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
