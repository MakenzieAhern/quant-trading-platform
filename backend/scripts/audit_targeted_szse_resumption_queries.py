"""Prove every targeted official SZSE resumption query window has complete receipts."""

import argparse
import json
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

CHECKPOINT = re.compile(r"\d{6}-[0-9a-f]{16}\.json")


def contiguous(expected: dict, windows: list[dict]) -> bool:
    cursor = date.fromisoformat(expected["start"])
    end = date.fromisoformat(expected["end"])
    for row in sorted(windows, key=lambda item: item["start"]):
        if date.fromisoformat(row["start"]) != cursor:
            return False
        cursor = date.fromisoformat(row["end"]) + timedelta(days=1)
    return cursor == end + timedelta(days=1)


def expected_query_windows(
    unresolved: list[dict], suspensions: list[dict], days: int, offset: int
) -> dict[tuple[str, str], dict]:
    from scripts.collect_targeted_szse_resumption_metadata import offset_windows, query_windows

    windows = offset_windows(query_windows(unresolved, suspensions, days + offset), offset)
    return {(row["security_id"], row["suspended_at"]): row for row in windows}


def load(root: Path) -> tuple[dict, list[dict]]:
    path = root / "metadata-manifest-v1.json"
    report = json.loads(path.read_bytes())
    if report["manifest_sha256"] != canonical_sha256(
        {key: value for key, value in report.items() if key != "manifest_sha256"}
    ):
        raise ValueError("METADATA_MANIFEST_CHANGED")
    rows = []
    for checkpoint in sorted((root / "metadata-v1").glob("*.json")):
        if not CHECKPOINT.fullmatch(checkpoint.name):
            continue
        row = json.loads(checkpoint.read_bytes())
        if row["manifest_sha256"] != canonical_sha256(
            {key: value for key, value in row.items() if key != "manifest_sha256"}
        ):
            raise ValueError("METADATA_CHECKPOINT_CHANGED")
        for source in row.get("sources", []):
            page = checkpoint.with_name(f"{checkpoint.stem}-p{source['params']['pageNum']:03}.json")
            if sha256_file(page) != source["sha256"]:
                raise ValueError("METADATA_SOURCE_PAGE_CHANGED")
        rows.append(row)
    if len(rows) != report["query_windows"]:
        raise ValueError("METADATA_CHECKPOINT_COUNT_MISMATCH")
    failures = [row for row in rows if row["status"] != "COMPLETE_FOR_OFFICIAL_QUERY"]
    if len(failures) != report["failed_windows"] or {
        row["manifest_sha256"] for row in failures
    } != {row["manifest_sha256"] for row in report["failures"]}:
        raise ValueError("METADATA_FAILURE_MANIFEST_MISMATCH")
    return report, rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, action="append", required=True)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--suspensions", type=Path)
    parser.add_argument("--window-days", type=int, default=14)
    parser.add_argument("--window-offset-days", type=int, default=0)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    unresolved = json.loads(args.unresolved.read_bytes())
    if isinstance(unresolved, dict):
        unresolved = unresolved["remaining_unresolved"]
    _, batches = zip(*(load(root) for root in args.root), strict=True)
    originals = {(row["security_id"], row["suspended_at"]): row for row in batches[0]}
    if args.suspensions:
        expected_windows = expected_query_windows(
            unresolved,
            json.loads(args.suspensions.read_bytes())["szse"],
            args.window_days,
            args.window_offset_days,
        )
    else:
        expected_windows = {(row["security_id"], row["suspended_at"]): row for row in unresolved}
    expected = set(expected_windows)
    if (
        set(originals) != expected
        or len(originals) != len(batches[0])
        or any(
            (originals[key]["start"], originals[key]["end"]) != (row["start"], row["end"])
            for key, row in expected_windows.items()
            if "start" in row
        )
    ):
        raise ValueError("METADATA_ORIGINAL_FACT_SET_MISMATCH")
    complete = defaultdict(list)
    for batch in batches:
        for row in batch:
            key = (row["security_id"], row["suspended_at"])
            if key not in expected:
                raise ValueError("METADATA_UNEXPECTED_FACT")
            if row["status"] == "COMPLETE_FOR_OFFICIAL_QUERY":
                complete[key].append(row)
    gaps = [key for key in sorted(expected) if not contiguous(originals[key], complete[key])]
    if gaps:
        raise ValueError(f"METADATA_UNCLOSED_WINDOWS:{gaps}")
    for windows in complete.values():
        ids = [item["announcementId"] for row in windows for item in row["records"]]
        if len(ids) != len(set(ids)):
            raise ValueError("METADATA_DUPLICATE_ANNOUNCEMENTS_WITHIN_FACT")
    report = {
        "parser_version": "SZSE_TARGETED_RESUMPTION_QUERY_CLOSURE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "suspensions_input_sha256": sha256_file(args.suspensions) if args.suspensions else None,
        "window_days": args.window_days,
        "window_offset_days": args.window_offset_days,
        "input_unresolved_facts": len(unresolved),
        "offset_inapplicable_facts": len(unresolved) - len(expected),
        "metadata_manifest_sha256s": [
            sha256_file(root / "metadata-manifest-v1.json") for root in args.root
        ],
        "original_facts": len(expected),
        "closed_facts": len(complete),
        "unclosed_facts": 0,
        "official_query_records": sum(
            len(row["records"]) for windows in complete.values() for row in windows
        ),
        "source_checksum_repeatability": "PASS",
        "input_order_reproducibility": "PASS",
        "acceptance": "METADATA_QUERY_COMPLETENESS_NOT_RESUMPTION_FACT_ACCEPTANCE",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
