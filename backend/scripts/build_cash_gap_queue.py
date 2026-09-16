"""Build a candidate-only CNINFO queue for cash facts with no linked source URL."""

import argparse
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def candidate_queue(requirements: list[dict], metadata: list[dict], days: int = 60):
    by_symbol = defaultdict(list)
    for row in metadata:
        for symbol in {row["issuer"], row.get("source_symbol")} - {None}:
            by_symbol[symbol].append(row)
    queued, covered, uncovered = {}, set(), []
    for requirement in requirements:
        if not (
            requirement["priority"] == "P1"
            and requirement["source_group"] == "CNINFO"
            and requirement["required_document_types"]
            == ["FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"]
            and not requirement["known_urls"]
        ):
            continue
        for event in requirement["affected_events"]:
            kind, symbol, record_date, _ = event.split(":")
            if kind != "CASH":
                raise ValueError("NON_CASH_REQUIREMENT")
            record = date.fromisoformat(record_date)
            candidates = [
                row
                for row in by_symbol[symbol]
                if row["published_on"] <= record_date
                and (record - date.fromisoformat(row["published_on"])).days <= days
            ]
            if not candidates:
                uncovered.append(event)
                continue
            covered.add(event)
            for row in candidates:
                queued.setdefault(row["url"], {**row, "affected_events": set()})[
                    "affected_events"
                ].add(event)
    queue = [
        {
            "affected_events": sorted(row.pop("affected_events")),
            "issuer": row.get("source_symbol", row["issuer"]),
            "published_on": row["published_on"],
            "queue_type": "OFFICIAL_CASH_GAP_CANDIDATE_PDF",
            "title": row["title"],
            "url": row["url"],
        }
        for row in queued.values()
    ]
    queue.sort(key=lambda row: (row["published_on"], row["url"]))
    return queue, sorted(covered), sorted(uncovered)


def verified(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    if value["manifest_sha256"] != canonical_sha256(
        {key: item for key, item in value.items() if key != "manifest_sha256"}
    ):
        raise ValueError("INPUT_MANIFEST_CHANGED")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    requirements, metadata = map(verified, (args.requirements, args.metadata))
    documents = [row for result in metadata["results"] for row in result["documents"]]
    queue, covered, uncovered = candidate_queue(requirements["documents"], documents)
    if (queue, covered, uncovered) != candidate_queue(
        list(reversed(requirements["documents"])), list(reversed(documents))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    write_immutable(args.queue, canonical_json_bytes(queue) + b"\n")
    report = {
        "parser_version": "P1_CASH_GAP_CANDIDATE_QUEUE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (args.requirements, args.metadata)
        ],
        "cash_fact_requirements_without_urls": len(covered) + len(uncovered),
        "facts_with_official_candidates": len(covered),
        "facts_without_candidates": len(uncovered),
        "candidate_documents": len(queue),
        "candidate_window_days": 60,
        "uncovered_facts": uncovered,
        "acceptance": "CANDIDATES_ONLY_REQUIRE_DATE_AND_ECONOMIC_RECONCILIATION",
        "input_order_reproducibility": "PASS",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
