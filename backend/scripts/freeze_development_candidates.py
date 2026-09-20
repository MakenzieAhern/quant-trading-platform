"""Freeze the fixed Development candidate family before Validation is inspected."""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def freeze(development: Path, output: Path, repository: Path) -> dict:
    result_path = development / "result.json"
    receipt_path = development / "receipt.json"
    result = json.loads(result_path.read_bytes())
    receipt = json.loads(receipt_path.read_bytes())
    unsigned = {key: value for key, value in result.items() if key != "result_sha256"}
    if (
        result["period_kind"] != "DEVELOPMENT"
        or result["period"] != {"start": "2010-01-01", "end": "2017-12-31"}
        or result["strategy_result_replay"] != "PASS"
        or result["official_oos_accessed"]
        or result["candidate_order"] != ["S0", "S1", "S2", "S3", "S4"]
        or result["selection_pool"] != ["S2", "S3", "S4"]
        or canonical_sha256(unsigned) != result["result_sha256"]
        or receipt["result_sha256"] != result["result_sha256"]
        or receipt["git_commit"] != result["git_commit"]
    ):
        raise ValueError("DEVELOPMENT_RESULT_NOT_FREEZABLE")
    record = {
        "freeze_id": "R6_DEVELOPMENT_CANDIDATES_V1",
        "status": "FROZEN",
        "dataset_id": result["dataset_id"],
        "dataset_sha256": result["dataset_sha256"],
        "development_period": result["period"],
        "validation_period": {"start": "2018-01-01", "end": "2021-12-31"},
        "development_result_sha256": result["result_sha256"],
        "development_result_file_sha256": sha256_file(result_path),
        "development_receipt_file_sha256": sha256_file(receipt_path),
        "development_git_commit": result["git_commit"],
        "implementation_sha256": result["implementation_sha256"],
        "candidate_order": result["candidate_order"],
        "selection_pool": result["selection_pool"],
        "candidates": {
            name: {
                "role": result["results"][name]["role"],
                "strategy_id": result["results"][name]["strategy_id"],
                "config": result["results"][name]["config"],
                "config_sha256": result["results"][name]["config_sha256"],
            }
            for name in result["candidate_order"]
        },
        "validation_gates": {
            "total_return": {"operator": ">", "value": "0"},
            "excess_return_vs_csi300": {"operator": ">", "value": "0"},
            "sharpe_ratio": {"operator": ">", "value": "0"},
            "maximum_drawdown_absolute": {"operator": "<", "value": "0.40"},
            "single_positive_year_share": {
                "definition": "max(positive annual returns) / sum(positive annual returns)",
                "operator": "<=",
                "value": "0.90",
            },
            "annualized_turnover": {"operator": "<=", "value": "24"},
            "annualized_transaction_cost_ratio": {"operator": "<=", "value": "0.05"},
            "accounting_data_integrity": "PASS_REQUIRED",
            "known_implementation_artifact": "NONE_MATERIAL_REQUIRED",
        },
        "selection_rule": [
            "highest_validation_information_ratio",
            "if_within_0.01_higher_validation_sharpe",
            "if_within_0.01_lower_maximum_drawdown_absolute",
            "if_within_0.01_lower_turnover",
            "if_still_tied_simpler_strategy",
        ],
        "no_passing_candidate_fallback": "S4_UNCHANGED_NEGATIVE_OR_NEUTRAL_RESEARCH_TEST",
        "oos_lock": "LOCKED_UNTIL_GATE_C",
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "freeze_git_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True
        ).strip(),
    }
    record["freeze_record_sha256"] = canonical_sha256(record)
    write_immutable(output, canonical_json_bytes(record) + b"\n")
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(freeze(args.development, args.output, args.repository), sort_keys=True))
