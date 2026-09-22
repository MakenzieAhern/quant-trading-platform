"""Execute pre-authorized Gate C and freeze the selected strategy specification."""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.run_research import implementation_sha256


def _verified(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    key = "report_sha256" if "report_sha256" in value else "freeze_record_sha256"
    digest = value.pop(key)
    if canonical_sha256(value) != digest:
        raise ValueError(f"CONTROL_RECORD_CHANGED:{path.name}")
    value[key] = digest
    return value


def freeze(
    validation: Path,
    evaluation: Path,
    candidates: Path,
    output: Path,
    repository: Path,
) -> dict:
    result_path = validation / "result.json"
    receipt_path = validation / "receipt.json"
    result = json.loads(result_path.read_bytes())
    receipt = json.loads(receipt_path.read_bytes())
    evaluated = _verified(evaluation)
    frozen = _verified(candidates)
    selected = evaluated["selected_candidate"]
    if (
        result["period_kind"] != "VALIDATION"
        or result["official_oos_accessed"]
        or result["candidate_freeze_sha256"] != frozen["freeze_record_sha256"]
        or receipt["status"] != "PASS"
        or receipt["result_sha256"] != result["result_sha256"]
        or evaluated["validation_result_sha256"] != result["result_sha256"]
        or evaluated["official_oos_accessed"]
        or evaluated["oos_lock"] != "LOCKED_UNTIL_GATE_C"
        or selected not in frozen["selection_pool"]
        or evaluated["selected_config_sha256"] != frozen["candidates"][selected]["config_sha256"]
    ):
        raise ValueError("GATE_C_CONDITIONS_FAILED")
    record = {
        "freeze_id": "FROZEN_STRATEGY_SPEC_V1",
        "status": "FROZEN",
        "dataset_id": result["dataset_id"],
        "dataset_sha256": result["dataset_sha256"],
        "candidate_freeze_sha256": frozen["freeze_record_sha256"],
        "development_result_sha256": frozen["development_result_sha256"],
        "validation_result_sha256": result["result_sha256"],
        "validation_result_file_sha256": sha256_file(result_path),
        "validation_receipt_file_sha256": sha256_file(receipt_path),
        "validation_evaluation_sha256": evaluated["report_sha256"],
        "selected_candidate": selected,
        "selected_strategy_id": evaluated["selected_strategy_id"],
        "selected_config": evaluated["selected_config"],
        "selected_config_sha256": evaluated["selected_config_sha256"],
        "selection_reason": evaluated["selection_reason"],
        "validation_established_robust_historical_alpha": evaluated[
            "validation_established_robust_historical_alpha"
        ],
        "benchmark": "CSI300_PRICE_INDEX",
        "oos_period": {"start": "2022-01-01", "end": "2025-12-31"},
        "official_oos_run_limit": 1,
        "official_oos_runs_at_freeze": 0,
        "oos_implementation_sha256": implementation_sha256(repository),
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
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--evaluation", required=True, type=Path)
    parser.add_argument("--candidates", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            freeze(
                args.validation,
                args.evaluation,
                args.candidates,
                args.output,
                args.repository,
            ),
            sort_keys=True,
        )
    )
