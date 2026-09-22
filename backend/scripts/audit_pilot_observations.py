"""Inventory actual observations and missing lifecycle sessions without inventing suspension."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

import pyarrow.parquet as parquet

from scripts.reconcile_sse_cninfo import save, sha
from scripts.stage_akshare_pilot import pilot_members


def missing_intervals(member: dict, sessions: list[str], observed: list[str]) -> list[dict]:
    eligible = [
        day
        for day in sorted(set(sessions))
        if day >= member["listing_date"]
        and (not member["delisting_date"] or day < member["delisting_date"])
    ]
    present = set(observed)
    if len(present) != len(observed) or not present <= set(eligible):
        raise ValueError("DUPLICATE_OR_OUT_OF_LIFECYCLE_OBSERVATION")
    intervals = []
    current = None
    for day in eligible:
        if day in present:
            current = None
            continue
        if current is None:
            current = dict(effective_from=day, effective_to=day, sessions=0)
            intervals.append(current)
        current["effective_to"] = day
        current["sessions"] += 1
    return intervals


def audit(staging: Path) -> dict:
    root = staging / "pilot-akshare-20260911"
    receipt_bytes = (root / "partition-checkpoint.json").read_bytes()
    receipts = json.loads(receipt_bytes)["partitions"]
    members = {row["security_id"]: row for row in pilot_members(staging)}
    sessions = json.loads(
        (staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json").read_bytes()
    )
    missing, observed_total, zero_volume = {}, 0, 0
    for sid, receipt in sorted(receipts.items()):
        partition = next(
            item for item in receipt["files"] if item["relative_path"].endswith("/raw.parquet")
        )
        path = root / "dataset-staging" / partition["relative_path"]
        if sha(path.read_bytes()) != partition["sha256"]:
            raise ValueError("PARTITION_BYTES_CHANGED")
        rows = parquet.read_table(
            path, columns=["security_id", "trading_date", "volume"]
        ).to_pylist()
        if len(rows) != partition["row_count"] or any(row["security_id"] != sid for row in rows):
            raise ValueError("PARTITION_IDENTITY_OR_COUNT_CHANGED")
        intervals = missing_intervals(members[sid], sessions, [row["trading_date"] for row in rows])
        if intervals:
            missing[sid] = intervals
        observed_total += len(rows)
        zero_volume += sum(
            row["volume"] is not None and Decimal(row["volume"]) == 0 for row in rows
        )
    report = dict(
        partition_checkpoint_sha256=sha(receipt_bytes),
        securities_checked=len(receipts),
        securities_pending=sorted(members.keys() - receipts.keys()),
        observations=observed_total,
        zero_volume_observations=zero_volume,
        missing_observations=sum(
            item["sessions"] for intervals in missing.values() for item in intervals
        ),
        missing_intervals=missing,
        missing_classification="MISSING_OBSERVATION_NOT_INFERRED_SUSPENSION",
        dataset_audited=False,
    )
    save(root / "observation-coverage-current.json", report)
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in {"missing_intervals", "securities_pending"}
            }
        )
    )
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    audit(parser.parse_args().staging)
