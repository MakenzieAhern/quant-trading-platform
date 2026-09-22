"""Build a missing-only official notice queue from the audited full cash gaps."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.build_cash_gap_queue import candidate_queue, verified


def gap_requirements(gaps, master):
    requirements = []
    for gap in gaps:
        rows = [
            row
            for row in master
            if row["security_id"] == gap["security_id"]
            and row["instrument_type"] == "COMMON_A_SHARE"
            and row["effective_from"] <= gap["record_date"] <= gap["ex_date"]
            and gap["ex_date"] <= (row["effective_to"] or "2025-12-31")
        ]
        if len(rows) != 1:
            raise ValueError("CASH_GAP_SYMBOL_INTERVAL_UNRESOLVED")
        requirements.append(
            dict(
                priority="P1",
                source_group="CNINFO",
                required_document_types=[
                    "FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"
                ],
                known_urls=[],
                affected_events=[f"CASH:{rows[0]['symbol']}:{gap['record_date']}:{gap['ex_date']}"],
            )
        )
    return requirements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, action="append", required=True)
    parser.add_argument("--queue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    coverage = verified(args.coverage)
    metadata = [verified(path) for path in args.metadata]
    master = json.loads(args.master.read_bytes())
    requirements = gap_requirements(coverage["unresolved_events"], master)
    documents = [
        row
        for source in metadata
        for result in source["results"]
        for row in result.get("documents", [])
    ]
    queue, covered, uncovered = candidate_queue(requirements, documents)
    if (queue, covered, uncovered) != candidate_queue(
        list(reversed(requirements)), list(reversed(documents))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    write_immutable(args.queue, canonical_json_bytes(queue) + b"\n")
    report = dict(
        parser_version="FULL_CASH_GAP_CANDIDATE_QUEUE_V1",
        parser_sha256=sha256_file(Path(__file__)),
        inputs=[
            dict(path=str(path), sha256=sha256_file(path))
            for path in (args.coverage, args.master, *args.metadata)
        ],
        unresolved_cash_events=len(requirements),
        facts_with_official_candidates=len(covered),
        facts_without_official_candidates=len(uncovered),
        candidate_documents=len(queue),
        candidate_window_days=60,
        uncovered_facts=uncovered,
        acceptance="CANDIDATES_ONLY_REQUIRE_OFFICIAL_COMPOSITE_RECONCILIATION",
        input_order_reproducibility="PASS",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
