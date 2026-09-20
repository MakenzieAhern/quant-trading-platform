"""Audit official suspension observations and expose only unresolved resume facts."""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts.reconcile_sse_cninfo import save

COVERAGE_START = "2010-01-01"
COVERAGE_END = "2025-12-31"


def _date(value: str) -> str:
    if re.fullmatch(r"\d{8}", value):
        return f"{value[:4]}-{value[4:6]}-{value[6:]}"
    match = re.match(r"(\d{4})[/\-](\d{2})[/\-](\d{2})", value)
    if match is None:
        raise ValueError(f"INVALID_SUSPENSION_TIMESTAMP:{value}")
    return "-".join(match.groups())


def _identity_index(master: list[dict]) -> dict[tuple[str, str], list[dict]]:
    result = defaultdict(list)
    for row in master:
        result[(row["exchange"], row["symbol"])].append(row)
    return result


def _identity(index: dict, exchange: str, symbol: str, day: str) -> dict | None:
    matches = [
        row
        for row in index.get((exchange, symbol), [])
        if row["effective_from"] <= day
        and (row["effective_to"] is None or day <= row["effective_to"])
    ]
    if len(matches) > 1:
        raise ValueError("AMBIGUOUS_MASTER_IDENTITY")
    return matches[0] if matches else None


def normalize_sse(rows: list[dict], index: dict, source_hashes: dict[str, str]) -> tuple:
    grouped = defaultdict(list)
    keys = (
        "productCode",
        "productName",
        "startStopDate",
        "endStopDate",
        "stopTime",
        "type",
        "controlType",
        "stopReason",
        "endStopReason",
    )
    for row in rows:
        grouped[tuple(row.get(key, "") for key in keys)].append(row)
    events, non_target = [], 0
    for values, observations in grouped.items():
        row = dict(zip(keys, values, strict=True))
        start, end = _date(row["startStopDate"]), _date(row["endStopDate"])
        identity = _identity(index, "SSE", row["productCode"], max(start, COVERAGE_START))
        if identity is None:
            non_target += 1
            continue
        if end < start:
            raise ValueError("SSE_SUSPENSION_RANGE_REVERSED")
        blocked_at_open = row["type"] == "LXTP" or row["stopTime"] in {"WH", "930", "AM"}
        events.append(
            {
                "exchange": "SSE",
                "security_id": identity["security_id"],
                "symbol": row["productCode"],
                "suspended_at": start,
                "resumed_or_ended_at": end,
                "execution_open_blocked": blocked_at_open,
                "source_observation": row,
                "source_files": sorted({item["source_file"] for item in observations}),
                "source_sha256": sorted(
                    {source_hashes[item["source_file"]] for item in observations}
                ),
            }
        )
    return sorted(events, key=_event_key), non_target, len(rows) - len(grouped)


def normalize_szse(
    rows: list[dict],
    index: dict,
    source_hashes: dict[str, str],
    lifecycle_end: dict[str, str | None],
    supplements: dict[tuple[str, str], dict] | None = None,
) -> tuple:
    supplements = supplements or {}
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["symbol"], row["suspended_at"])].append(row)
    events, unresolved, conflicts, non_target = [], [], [], 0
    for (symbol, timestamp), observations in grouped.items():
        start = _date(timestamp)
        identity = _identity(index, "SZSE", symbol, max(start, COVERAGE_START))
        if identity is None:
            non_target += 1
            continue
        resumes = sorted(
            {
                item["resumed_at"]
                for item in observations
                if item["resumed_at"] and not item["resumed_at"].startswith("9999/")
            }
        )
        if len(resumes) > 1:
            conflicts.append(
                {
                    "security_id": identity["security_id"],
                    "suspended_at": timestamp,
                    "values": resumes,
                }
            )
        resume = resumes[0] if len(resumes) == 1 else None
        supplement = supplements.get((identity["security_id"], timestamp))
        terminal = supplement.get("terminal_at") if supplement else None
        censored = supplement.get("censored_at") if supplement else None
        if resume is None and supplement and not terminal and not censored:
            resume = supplement["resumed_at"]
        end = lifecycle_end[identity["security_id"]]
        closure = (
            supplement.get("closure", "OFFICIAL_TERMINATION_NO_DELISTING_PERIOD")
            if terminal
            else supplement.get("closure")
            if censored
            else supplement.get("closure", "OFFICIAL_RESUMPTION_DOCUMENT")
            if supplement and resume == supplement["resumed_at"]
            else "OFFICIAL_RESUMPTION"
            if resume
            else None
        )
        if terminal and (resume or terminal != end or terminal < start):
            raise ValueError("INVALID_TERMINAL_SUSPENSION_CLOSURE")
        if censored and (resume or terminal or censored != COVERAGE_END or censored < start):
            raise ValueError("INVALID_RIGHT_CENSORED_SUSPENSION_CLOSURE")
        if resume is None and end is not None and end <= start:
            closure = "MASTER_LIFECYCLE_END"
        event = {
            "exchange": "SZSE",
            "security_id": identity["security_id"],
            "symbol": symbol,
            "suspended_at": timestamp,
            "resumed_at": resume,
            "execution_open_blocked": supplement.get("execution_open_blocked")
            if supplement
            else None,
            "closure": closure,
            "source_files": sorted({item["source_file"] for item in observations}),
            "source_sha256": sorted({source_hashes[item["source_file"]] for item in observations}),
        }
        if supplement:
            event["closure_evidence"] = supplement["evidence"]
        if terminal:
            event["terminal_at"] = terminal
        if censored:
            event["censored_at"] = censored
        events.append(event)
        if closure is None:
            unresolved.append(
                {
                    "security_id": identity["security_id"],
                    "symbol": symbol,
                    "suspended_at": timestamp,
                    "missing_fact": "OFFICIAL_RESUMPTION_OR_LIFECYCLE_TERMINATION_BOUNDARY",
                    "evidence_searched": event["source_files"],
                }
            )
    return (
        sorted(events, key=_event_key),
        sorted(unresolved, key=lambda row: (row["suspended_at"], row["security_id"])),
        sorted(conflicts, key=lambda row: (row["suspended_at"], row["security_id"])),
        non_target,
        len(rows) - len(grouped),
    )


def _event_key(row: dict) -> tuple:
    return (
        row["suspended_at"],
        row["security_id"],
        json.dumps(row, ensure_ascii=False, sort_keys=True),
    )


def _lifecycle_ends(master: list[dict]) -> dict[str, str | None]:
    ends = defaultdict(list)
    for row in master:
        ends[row["security_id"]].append(row["effective_to"])
    return {
        security_id: None if any(value is None for value in values) else max(values)
        for security_id, values in ends.items()
    }


def load_resumption_supplements(paths: list[Path]) -> tuple[dict[tuple[str, str], dict], list[str]]:
    supplements = {}
    hashes = []
    for path in sorted(paths):
        report = json.loads(path.read_bytes())
        if report["manifest_sha256"] != canonical_sha256(
            {key: value for key, value in report.items() if key != "manifest_sha256"}
        ):
            raise ValueError("RESUMPTION_MANIFEST_CHECKSUM_MISMATCH")
        hashes.append(sha256_file(path))
        rows = [
            *report.get("accepted_resumptions", []),
            *report.get("accepted_terminal_closures", []),
            *report.get("accepted_right_censored_closures", []),
        ]
        for row in rows:
            key = (row["security_id"], row["suspended_at"])
            if key in supplements and supplements[key] != row:
                raise ValueError("CONFLICTING_SUSPENSION_CLOSURE_SUPPLEMENTS")
            supplements[key] = row
    return supplements, hashes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--szse-resumptions", type=Path, action="append", default=[])
    args = parser.parse_args()
    source_manifest_path = args.root / "source-manifest-v1.json"
    observations_path = args.root / "official-suspension-observations-v1.json"
    source_manifest = json.loads(source_manifest_path.read_bytes())
    observations = json.loads(observations_path.read_bytes())
    master = json.loads(args.master.read_bytes())
    if source_manifest["manifest_sha256"] != canonical_sha256(
        {key: value for key, value in source_manifest.items() if key != "manifest_sha256"}
    ):
        raise ValueError("SOURCE_MANIFEST_CHECKSUM_MISMATCH")
    source_hashes = {}
    for source in [*source_manifest["sse_sources"], *source_manifest["szse_sources"]]:
        path = args.root / source["path"]
        if sha256_file(path) != source["sha256"]:
            raise ValueError("SOURCE_BYTES_CHANGED")
        source_hashes[source["path"]] = source["sha256"]
        menu = source.get("menu_path")
        if menu and sha256_file(Path(menu)) != source["menu_sha256"]:
            raise ValueError("REUSED_MENU_BYTES_CHANGED")
    index = _identity_index(master)
    supplements, resumption_hashes = load_resumption_supplements(args.szse_resumptions)
    lifecycle_end = _lifecycle_ends(master)
    sse_result = normalize_sse(observations["sse"], index, source_hashes)
    szse_result = normalize_szse(
        observations["szse"], index, source_hashes, lifecycle_end, supplements
    )
    if sse_result != normalize_sse(list(reversed(observations["sse"])), index, source_hashes):
        raise ValueError("SSE_SUSPENSION_INPUT_ORDER_CHANGED")
    if szse_result != normalize_szse(
        list(reversed(observations["szse"])),
        index,
        source_hashes,
        lifecycle_end,
        supplements,
    ):
        raise ValueError("SZSE_SUSPENSION_INPUT_ORDER_CHANGED")
    sse, sse_non_target, sse_duplicates = sse_result
    szse, unresolved, conflicts, szse_non_target, szse_duplicates = szse_result
    authority = {
        "parser_version": "FULL_OFFICIAL_SUSPENSION_AUDIT_V5",
        "parser_sha256": sha256_file(Path(__file__)),
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "observations_sha256": sha256_file(observations_path),
        "master_sha256": sha256_file(args.master),
        "coverage": [COVERAGE_START, COVERAGE_END],
        "sse_source_rows": len(observations["sse"]),
        "sse_target_events": len(sse),
        "sse_duplicate_observations": sse_duplicates,
        "sse_non_target_rows": sse_non_target,
        "sse_unresolved_facts": 0,
        "szse_source_rows": len(observations["szse"]),
        "szse_target_events": len(szse),
        "szse_duplicate_observations": szse_duplicates,
        "szse_non_target_rows": szse_non_target,
        "szse_resume_conflicts": len(conflicts),
        "szse_unresolved_facts": len(unresolved),
        "szse_supplemental_resumptions": sum("resumed_at" in row for row in supplements.values()),
        "szse_supplemental_terminal_closures": sum(
            "terminal_at" in row for row in supplements.values()
        ),
        "szse_supplemental_right_censored_closures": sum(
            "censored_at" in row for row in supplements.values()
        ),
        "szse_resumption_manifest_sha256s": resumption_hashes,
        "source_checksum_repeatability": "PASS",
        "input_order_reproducibility": "PASS",
        "authority_status": (
            "PASS_PUBLIC_OFFICIAL_RECONSTRUCTION"
            if not unresolved and not conflicts
            else "PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES"
        ),
    }
    authority["manifest_sha256"] = canonical_sha256(authority)
    output_root = args.output_root or args.root
    save(output_root / "normalized-suspension-events-v1.json", {"sse": sse, "szse": szse})
    save(output_root / "unresolved-szse-resumption-facts-v1.json", unresolved)
    save(output_root / "szse-resumption-conflicts-v1.json", conflicts)
    save(output_root / "suspension-authority-v1.json", authority)
    print(json.dumps(authority))


if __name__ == "__main__":
    main()
