"""Authorized v1/v2 engineering diagnostics; never strategy selection or tuning."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256
from app.data.catalog.freeze import write_immutable
from scripts.run_pilot_smoke import LABEL, frozen_inputs


def compare(v1: dict, v2: dict) -> dict:
    if (
        v1["label"] != LABEL
        or v2["label"] != LABEL
        or v1["strategy_config_hash"] != v2["strategy_config_hash"]
        or v1["strategy_config"] != v2["strategy_config"]
    ):
        raise ValueError("SMOKE_COMPARISON_SCOPE_OR_STRATEGY_CHANGED")
    report = {"label": LABEL, "signal_definition": "RiskEngine order proposals, not factor rows"}
    for prefix, result in (("V1", v1), ("V2", v2)):
        report.update(
            {
                prefix + "_SIGNAL_COUNT": len(result["proposals"]),
                prefix + "_ORDER_COUNT": len(result["orders"]),
                prefix + "_FILL_COUNT": result["fills"],
                prefix + "_FINAL_EQUITY": result["metrics"]["final_equity"],
                prefix + "_TOTAL_RETURN": result["metrics"]["cumulative_return"],
            }
        )
    report["rebalance_differences"] = [
        dict(
            date=b["date"],
            factor_count_delta=b["factor_count"] - a["factor_count"],
            scores_changed=a["scores_sha256"] != b["scores_sha256"],
            targets_changed=a["target"] != b["target"],
        )
        for a, b in zip(v1["rebalances"], v2["rebalances"], strict=True)
    ]
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--repository", type=Path, required=True)
    args = parser.parse_args()
    results, manifests = [], []
    for version in (1, 2):
        output = args.root / "results" / f"pilot-smoke-v{version}"
        result = json.loads((output / "result.json").read_bytes())
        receipt = json.loads((output / "receipt.json").read_bytes())
        _, manifest = frozen_inputs(args.root / result["dataset_id"], args.repository)
        if canonical_sha256(result) != receipt["result_sha256"]:
            raise ValueError("ORIGINAL_SMOKE_RESULT_CHANGED")
        results.append(result)
        manifests.append({p.relative_path: p.logical_sha256 for p in manifest.partitions})
    report = compare(*results)
    # Both 600190 listing dates precede all Pilot/prehistory sessions. Its inputs
    # and effective Pilot states must agree before attributing changes elsewhere.
    if any(
        manifests[0][f"SSE/600190/{name}.parquet"] != manifests[1][f"SSE/600190/{name}.parquet"]
        for name in ("raw", "factors", "daily-state")
    ):
        raise ValueError("LIFECYCLE_CORRECTION_HAS_UNANALYZED_PILOT_INPUT_EFFECT")
    report["DIFFERENCE_CAUSED_BY_LIFECYCLE_CORRECTION"] = (
        "600190 master date corrected; Pilot raw/factors/daily-state logical hashes identical; "
        "both listing dates precede warm-up, so no Pilot input or rule-age effect."
    )
    report["DIFFERENCE_CAUSED_BY_NEW_SECURITIES"] = (
        "Three added STAR members and 555 raw bars enter v2. 688086/688555 exit before "
        "the first rebalance; 688287 remains available. Per-rebalance count/hash/target "
        "differences above measure propagation, not profitability acceptance."
    )
    report["v1_acceptance"] = "INVALIDATED; historical diagnostic only"
    target = args.root / "results/pilot-smoke-v2/comparison.json"
    write_immutable(target, canonical_json_bytes(report) + b"\n")
    print(json.dumps(report))
