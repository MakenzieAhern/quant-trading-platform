"""Reapply accepted official listing intervals to the v32 SZSE gap audit."""

import argparse
import json
from collections import Counter
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha

BASE_SHA = "6f15ea6427a21165e8de1a31df2907a652f9de78ed4da3e0cc425f9dace172a5"
PRIOR_SHA = "e34597c37fcfea2bfc193d165a40a8f56537b9bf247f809f8317ddbe6f3ac09d"


def close_report(base: dict, prior: dict, base_sha: str, prior_sha: str) -> dict:
    if (
        base["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_V1"
        or prior["report_version"] != "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V5"
        or base["missing_rows"] != prior["missing_rows"]
        or base["raw_authority_promoted"]
        or prior["raw_authority_promoted"]
    ):
        raise ValueError("AUDIT_INPUT_CHANGED")
    intervals = {}
    for item in prior["official_intervals"]:
        security_id = item["security_id"]
        if security_id in intervals:
            raise ValueError(f"OFFICIAL_INTERVAL_CONFLICT:{security_id}")
        intervals[security_id] = item

    counts = Counter(base["classification_counts"])
    closed = Counter()
    remaining = []
    for row in base["unresolved_rows"]:
        interval = intervals.get(row["security_id"])
        end = (
            interval.get("first_trading_day")
            or interval.get("delisted_on")
            or interval.get("terminal_decision_on")
            if interval
            else None
        )
        if interval and interval["suspended_from"] <= row["date"] < end:
            counts[row["reason"]] -= 1
            counts[interval["classification"]] += 1
            closed[row["security_id"]] += 1
        else:
            remaining.append(row)

    residual_keys = {(row["security_id"], row["date"]) for row in remaining}
    prior_keys = {(row["security_id"], row["date"]) for row in prior["unresolved_rows"]}
    if residual_keys != prior_keys:
        raise ValueError("RESIDUAL_ROW_SCOPE_CHANGED")
    if min(counts.values()) < 0 or sum(counts.values()) != base["missing_rows"]:
        raise ValueError("MISSING_ROW_CONSERVATION_FAILED")

    prior_reasons = {
        (row["security_id"], row["date"]): row["reason"] for row in prior["unresolved_rows"]
    }
    report = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V32_REPLAY_V1",
        "status": "PARTIAL_CORRECTED_SOURCE_PRESENCE_NOT_RAW_AUTHORITY",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "v32_base_report_sha256": base_sha,
        "v32_base_manifest_sha256": base["manifest_sha256"],
        "prior_corrected_report_sha256": prior_sha,
        "prior_corrected_manifest_sha256": prior["manifest_sha256"],
        "suspension_events_sha256": base["suspension_events_sha256"],
        "source_collection_sha256": base["source_collection_sha256"],
        "missing_rows": base["missing_rows"],
        "classification_counts": dict(sorted(counts.items())),
        "official_intervals": [
            {**item, "v32_rebased_closed_rows": closed[item["security_id"]]}
            for item in prior["official_intervals"]
        ],
        "unresolved_rows": remaining,
        "unresolved_symbols": dict(
            sorted(Counter(row["security_id"].split(":")[-1] for row in remaining).items())
        ),
        "unresolved_by_year": dict(sorted(Counter(row["date"][:4] for row in remaining).items())),
        "residual_reason_changes": [
            {
                "security_id": row["security_id"],
                "date": row["date"],
                "prior_reason": prior_reasons[(row["security_id"], row["date"])],
                "v32_reason": row["reason"],
            }
            for row in remaining
            if prior_reasons[(row["security_id"], row["date"])] != row["reason"]
        ],
        "residual_scope_changed": False,
        "raw_authority_promoted": False,
    }
    report["manifest_sha256"] = sha(canonical(report))
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--v32-base", type=Path, required=True)
    parser.add_argument("--prior-corrected", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base_raw, prior_raw = args.v32_base.read_bytes(), args.prior_corrected.read_bytes()
    if sha(base_raw) != BASE_SHA or sha(prior_raw) != PRIOR_SHA:
        raise ValueError("AUDITED_REPORT_BYTES_CHANGED")
    base, prior = json.loads(base_raw), json.loads(prior_raw)
    for report in (base, prior):
        if (
            sha(canonical({k: v for k, v in report.items() if k != "manifest_sha256"}))
            != report["manifest_sha256"]
        ):
            raise ValueError("REPORT_MANIFEST_CHANGED")
    report = close_report(base, prior, BASE_SHA, PRIOR_SHA)
    save(args.output, report)
    print(
        json.dumps(
            {
                "classification_counts": report["classification_counts"],
                "unresolved_rows": len(report["unresolved_rows"]),
                "unresolved_symbols": len(report["unresolved_symbols"]),
                "residual_reason_changes": len(report["residual_reason_changes"]),
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
