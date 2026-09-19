"""Route unexplained factor changes to retained CNINFO implementation metadata."""

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.build_cash_gap_queue import verified


def candidates(routing: dict, metadata: dict, days: int = 60) -> tuple[list[dict], list[dict]]:
    by_symbol = defaultdict(list)
    for result in metadata["results"]:
        for row in result["documents"]:
            by_symbol[row["issuer"]].append(row)
    queued = {}
    uncovered = []
    for row in sorted(
        (item for item in routing["rows"] if item["route"] == "NO_RETAINED_OFFICIAL_BONUS_DATE"),
        key=lambda item: (item["effective_date"], item["security_id"]),
    ):
        effective = date.fromisoformat(row["effective_date"])
        matches = [
            item
            for item in by_symbol[row["symbol"][2:]]
            if item["published_on"] <= row["effective_date"]
            and (effective - date.fromisoformat(item["published_on"])).days <= days
        ]
        key = f"FACTOR:{row['security_id']}:{row['effective_date']}"
        if not matches:
            uncovered.append(
                {
                    "factor_change": key,
                    "reason": "NO_RETAINED_CNINFO_IMPLEMENTATION_METADATA_WITHIN_60_DAYS",
                }
            )
            continue
        for item in matches:
            queued.setdefault(item["url"], {**item, "affected_factor_changes": set()})[
                "affected_factor_changes"
            ].add(key)
    queue = [
        {
            "affected_factor_changes": sorted(row.pop("affected_factor_changes")),
            "issuer": row["issuer"],
            "published_on": row["published_on"],
            "queue_type": "OFFICIAL_ADJUSTMENT_GAP_CANDIDATE_PDF",
            "title": row["title"],
            "url": row["url"],
        }
        for row in queued.values()
    ]
    queue.sort(key=lambda row: (row["published_on"], row["url"]))
    return queue, uncovered


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    routing, metadata = verified(args.routing), verified(args.metadata)
    queue, uncovered = candidates(routing, metadata)
    replay = candidates(
        dict(routing, rows=list(reversed(routing["rows"]))),
        dict(metadata, results=list(reversed(metadata["results"]))),
    )
    if (queue, uncovered) != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    covered = {event for row in queue for event in row["affected_factor_changes"]}
    report = {
        "report_id": "FULL_ADJUSTMENT_GAP_CNINFO_CANDIDATES_V1",
        "status": "CANDIDATES_ONLY_NO_EVENT_OR_AUTHORITY_ACCEPTANCE",
        "candidate_window_days": 60,
        "unrouted_factor_changes": len(covered) + len(uncovered),
        "factor_changes_with_candidates": len(covered),
        "factor_changes_without_candidates": len(uncovered),
        "candidate_documents": len(queue),
        "uncovered": uncovered,
        "input_order_reproducibility": "PASS",
        "dataset_created": False,
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (args.routing, args.metadata)
        ],
        "parser_sha256": sha256_file(Path(__file__)),
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.queue, canonical_json_bytes(queue) + b"\n")
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
