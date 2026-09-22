"""Quantify the factor-window impact of the unresolved SZSE 2011-07-25 rows."""

import argparse
import bisect
import json
from collections import defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def _verified_manifest(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    expected = value.get("manifest_sha256")
    if not expected or expected != canonical_sha256(
        {key: item for key, item in value.items() if key != "manifest_sha256"}
    ):
        raise ValueError(f"MANIFEST_CHANGED:{path}")
    return value


def build_report(
    gap: dict,
    candidate: dict,
    calendar: dict,
    master: dict,
    *,
    lookback_sessions: int = 253,
    rebalance_sessions: int = 20,
) -> dict:
    rows = gap["unresolved_rows"]
    security_ids = sorted({row["security_id"] for row in rows})
    dates = {row["date"] for row in rows}
    if len(rows) != len(security_ids) or len(dates) != 1:
        raise ValueError("GAP_ROWS_NOT_ONE_UNIQUE_DATE_PER_SECURITY")
    target_date = dates.pop()
    if candidate["target_date"] != target_date or len(candidate["results"]) != len(rows):
        raise ValueError("CANDIDATE_SCOPE_CHANGED")
    if candidate["promoted"] or not candidate["completed"]:
        raise ValueError("CANDIDATE_AUTHORITY_CHANGED")

    sessions = calendar["sessions"]
    if sessions != sorted(set(sessions)) or calendar["trading_sessions"] != len(sessions):
        raise ValueError("CALENDAR_ORDER_OR_COUNT_CHANGED")
    target_index = sessions.index(target_date)
    affected_sessions = sessions[target_index : target_index + lookback_sessions]
    if len(affected_sessions) != lookback_sessions:
        raise ValueError("INCOMPLETE_FACTOR_WINDOW")

    intervals: dict[str, list[dict]] = defaultdict(list)
    for record in master["records"]:
        if record["security_id"] in security_ids:
            intervals[record["security_id"]].append(record)
    if set(intervals) != set(security_ids):
        raise ValueError("GAP_SECURITY_MISSING_FROM_MASTER")

    def active(security_id: str, trading_date: str) -> bool:
        return any(
            record["listing_date"] <= trading_date
            and (not record["delisting_date"] or trading_date <= record["delisting_date"])
            for record in intervals[security_id]
        )

    def observed_history_count(security_id: str, session_index: int) -> int:
        first_listing = min(record["listing_date"] for record in intervals[security_id])
        first_index = bisect.bisect_left(sessions, first_listing)
        return session_index - first_index  # inclusive history minus the missing target row

    lifecycle_security_days = sum(
        active(security_id, trading_date)
        for security_id in security_ids
        for trading_date in affected_sessions
    )
    bridge_by_security = {}
    for security_id in security_ids:
        bridge_dates = [
            trading_date
            for session_index, trading_date in enumerate(affected_sessions[1:], target_index + 1)
            if active(security_id, trading_date)
            and observed_history_count(security_id, session_index) >= lookback_sessions
        ]
        bridge_by_security[security_id] = {
            "first_affected_date": bridge_dates[0] if bridge_dates else None,
            "affected_sessions": len(bridge_dates),
        }

    affected_set = set(affected_sessions)
    rebalance_dates = [
        trading_date
        for session_index, trading_date in enumerate(sessions)
        if session_index + 1 >= lookback_sessions
        and (session_index + 1 - lookback_sessions) % rebalance_sessions == 0
        and trading_date in affected_set
    ]
    rebalance_impact = [
        {
            "trading_date": trading_date,
            "observed_only_bridge_securities": sum(
                active(security_id, trading_date)
                and observed_history_count(security_id, sessions.index(trading_date))
                >= lookback_sessions
                for security_id in security_ids
            ),
        }
        for trading_date in rebalance_dates
    ]
    bridge_evaluations = sum(row["affected_sessions"] for row in bridge_by_security.values())
    return {
        "report_version": "SZSE_RAW_GAP_FACTOR_IMPACT_V1",
        "status": "MATERIAL_FACTOR_TREATMENT_DECISION_REQUIRED",
        "gap_date": target_date,
        "gap_securities": len(security_ids),
        "factor_lookback_sessions": lookback_sessions,
        "affected_window": [affected_sessions[0], affected_sessions[-1]],
        "affected_calendar_sessions": len(affected_sessions),
        "lifecycle_security_days": lifecycle_security_days,
        "observed_only_bridge_security_days": bridge_evaluations,
        "observed_only_bridge_securities": sum(
            row["affected_sessions"] > 0 for row in bridge_by_security.values()
        ),
        "strategy_rebalance_sessions": len(rebalance_dates),
        "observed_only_bridge_rebalance_evaluations": sum(
            row["observed_only_bridge_securities"] for row in rebalance_impact
        ),
        "rebalance_impact": rebalance_impact,
        "per_security_impact": bridge_by_security,
        "candidate_evidence": {
            "rows": len(candidate["results"]),
            "status": candidate["status"],
            "promoted": candidate["promoted"],
        },
        "treatments": {
            "CURRENT_OBSERVED_ONLY": "REJECT_SILENT_CALENDAR_HORIZON_DRIFT",
            "OFFICIAL_ONLY_STRICT_CONTIGUITY": "CONSERVATIVE_FACTOR_UNAVAILABLE",
            "DUAL_PROVIDER_CANDIDATE_FEATURE_ONLY": "REQUIRES_SOURCE_METHODOLOGY_APPROVAL",
        },
        "strategy_run": False,
        "profitability_inspected": False,
        "full_dataset_created": False,
        "full_dataset_frozen": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("gap-report", "candidate-report", "calendar", "master", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    gap = _verified_manifest(args.gap_report)
    calendar = _verified_manifest(args.calendar)
    master = _verified_manifest(args.master)
    candidate = json.loads(args.candidate_report.read_bytes())
    report = build_report(gap, candidate, calendar, master)
    report["inputs"] = [
        {"path": str(path), "sha256": sha256_file(path)}
        for path in (args.gap_report, args.candidate_report, args.calendar, args.master)
    ]
    report["parser_sha256"] = sha256_file(Path(__file__))
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "gap_securities",
                    "affected_window",
                    "observed_only_bridge_security_days",
                    "observed_only_bridge_rebalance_evaluations",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
