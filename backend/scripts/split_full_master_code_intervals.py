"""Split reviewed code aliases without changing stable identity or claiming completeness."""

import argparse
import json
from datetime import date, timedelta
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def split_intervals(rows, transitions):
    result = []
    used = set()
    for row in rows:
        matches = [
            t
            for t in transitions
            if t["exchange"] == row["exchange"]
            and row["symbol"] in (t["old_symbol"], t["new_symbol"])
        ]
        if len(matches) > 1:
            raise ValueError("MULTIPLE_CODE_TRANSITIONS_REQUIRE_ORDERED_CHAIN")
        if not matches:
            result.append(dict(row))
            continue
        transition = matches[0]
        key = (transition["exchange"], transition["old_symbol"], transition["new_symbol"])
        if key in used:
            raise ValueError("CODE_TRANSITION_DUPLICATE_LIFECYCLE")
        used.add(key)
        boundary = transition["effective_date"]
        if not row["effective_from"] < boundary or (
            row["effective_to"] and boundary > row["effective_to"]
        ):
            raise ValueError("CODE_TRANSITION_OUTSIDE_LIFECYCLE")
        previous_end = (date.fromisoformat(boundary) - timedelta(days=1)).isoformat()
        for symbol, start, end in (
            (transition["old_symbol"], row["effective_from"], previous_end),
            (transition["new_symbol"], boundary, row["effective_to"]),
        ):
            result.append(
                {
                    **row,
                    "symbol": symbol,
                    "effective_from": start,
                    "effective_to": end,
                    "code_transition_source_sha256": transition["sha256"],
                    "code_transition_source_url": transition["source_url"],
                    "name_history_acceptance": (
                        "NOT_ESTABLISHED_CURRENT_REGISTER_NAME_NOT_BACKDATED"
                    ),
                }
            )
    if len(used) != len(transitions):
        raise ValueError("CODE_TRANSITION_LIFECYCLE_MISSING")
    return sorted(result, key=lambda r: (r["security_id"], r["effective_from"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("lifecycles", "transitions", "staging", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads(args.lifecycles.read_bytes())
    transitions = json.loads(args.transitions.read_bytes())["transitions"]
    for t in transitions:
        source = (args.staging / t["source_path"]).resolve()
        if not source.is_relative_to(args.staging.resolve()) or sha256_file(source) != t["sha256"]:
            raise ValueError("TRANSITION_SOURCE_CHECKSUM_MISMATCH")
    result = split_intervals(rows, transitions)
    assert result == split_intervals(list(reversed(rows)), list(reversed(transitions)))
    report = dict(
        parser_version="FULL_MASTER_CODE_INTERVALS_V1",
        source_master_sha256=sha256_file(args.lifecycles),
        transition_review_sha256=sha256_file(args.transitions),
        reviewed_transitions=len(transitions),
        records=result,
        stable_id_count=len({r["security_id"] for r in result}),
        input_order_reproducibility="PASS",
        security_master_completeness="NOT_ESTABLISHED",
        scope="ALL_RETAINED_LIFECYCLES_INCLUDING_OUT_OF_PERIOD_AND_UNCLASSIFIED_INSTRUMENTS",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}))
