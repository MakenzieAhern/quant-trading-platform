"""Apply the frozen R7 robustness gates and deterministic selection rule."""

import argparse
import json
from decimal import Decimal
from functools import cmp_to_key
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

ZERO = Decimal(0)
CLOSE = Decimal("0.01")
YEARS = Decimal(4)


def evaluate_candidate(result: dict) -> dict:
    metrics = result["metrics"]
    annual = tuple(Decimal(value) for value in result["annual"].values())
    positive = tuple(value for value in annual if value > ZERO)
    concentration = max(positive) / sum(positive, ZERO) if positive else None
    annualized_turnover = Decimal(metrics["turnover"]) / YEARS
    annualized_cost_ratio = (
        Decimal(metrics["transaction_costs"]) / Decimal(metrics["initial_capital"]) / YEARS
    )
    gates = {
        "total_return": Decimal(metrics["cumulative_return"]) > ZERO,
        "excess_return_vs_csi300": Decimal(metrics["excess_return"]) > ZERO,
        "sharpe_ratio": metrics["sharpe_ratio"] is not None
        and Decimal(metrics["sharpe_ratio"]) > ZERO,
        "maximum_drawdown_absolute": abs(Decimal(metrics["maximum_drawdown"])) < Decimal("0.40"),
        "single_positive_year_share": concentration is not None
        and concentration <= Decimal("0.90"),
        "annualized_turnover": annualized_turnover <= Decimal(24),
        "annualized_transaction_cost_ratio": annualized_cost_ratio <= Decimal("0.05"),
        "accounting_data_integrity": result["execution"]["active_reservations"] == 0,
        "known_implementation_artifact": True,
    }
    return {
        "candidate": result["candidate"],
        "strategy_id": result["strategy_id"],
        "config_sha256": result["config_sha256"],
        "gates": gates,
        "all_gates_pass": all(gates.values()),
        "single_positive_year_share": (
            format(concentration, "f") if concentration is not None else None
        ),
        "annualized_turnover": format(annualized_turnover, "f"),
        "annualized_transaction_cost_ratio": format(annualized_cost_ratio, "f"),
        "metrics": metrics,
        "annual": result["annual"],
    }


def _compare(left: dict, right: dict) -> int:
    for name, lower_is_better in (
        ("information_ratio", False),
        ("sharpe_ratio", False),
        ("maximum_drawdown_absolute", True),
        ("turnover", True),
    ):
        left_value = Decimal(left[name])
        right_value = Decimal(right[name])
        if abs(left_value - right_value) > CLOSE:
            preferred = left_value < right_value if lower_is_better else left_value > right_value
            return -1 if preferred else 1
    return (left["factor_count"] > right["factor_count"]) - (
        left["factor_count"] < right["factor_count"]
    )


def select(evaluations: list[dict], results: dict) -> tuple[str, str]:
    eligible = []
    for item in evaluations:
        if not item["all_gates_pass"]:
            continue
        candidate = item["candidate"]
        metrics = results[candidate]["metrics"]
        eligible.append(
            {
                "candidate": candidate,
                "information_ratio": metrics["information_ratio"],
                "sharpe_ratio": metrics["sharpe_ratio"],
                "maximum_drawdown_absolute": format(abs(Decimal(metrics["maximum_drawdown"])), "f"),
                "turnover": metrics["turnover"],
                "factor_count": len(results[candidate]["config"]["factor_names"]),
            }
        )
    if not eligible:
        return "S4", "NO_CANDIDATE_PASSED_ALL_GATES_S4_REFERENCE_FALLBACK"
    return sorted(eligible, key=cmp_to_key(_compare))[0]["candidate"], "VALIDATION_GATE_SELECTION"


def evaluate(validation: Path, candidate_freeze: Path, output: Path) -> dict:
    result_path = validation / "result.json"
    receipt_path = validation / "receipt.json"
    result = json.loads(result_path.read_bytes())
    receipt = json.loads(receipt_path.read_bytes())
    frozen = json.loads(candidate_freeze.read_bytes())
    if (
        canonical_sha256({key: value for key, value in result.items() if key != "result_sha256"})
        != result["result_sha256"]
        or result["period_kind"] != "VALIDATION"
        or result["period"] != frozen["validation_period"]
        or result["candidate_freeze_sha256"] != frozen["freeze_record_sha256"]
        or result["official_oos_accessed"]
        or receipt["status"] != "PASS"
        or receipt["result_sha256"] != result["result_sha256"]
    ):
        raise ValueError("VALIDATION_RESULT_CHANGED")
    evaluations = [evaluate_candidate(result["results"][name]) for name in frozen["selection_pool"]]
    selected, reason = select(evaluations, result["results"])
    report = {
        "report_id": "R7_VALIDATION_EVALUATION_V1",
        "status": "PASS",
        "period": result["period"],
        "dataset_id": result["dataset_id"],
        "dataset_sha256": result["dataset_sha256"],
        "validation_result_sha256": result["result_sha256"],
        "validation_result_file_sha256": sha256_file(result_path),
        "validation_receipt_file_sha256": sha256_file(receipt_path),
        "candidate_freeze_sha256": frozen["freeze_record_sha256"],
        "validation_gates": frozen["validation_gates"],
        "selection_rule": frozen["selection_rule"],
        "evaluations": evaluations,
        "passing_candidates": [item["candidate"] for item in evaluations if item["all_gates_pass"]],
        "selected_candidate": selected,
        "selected_strategy_id": result["results"][selected]["strategy_id"],
        "selected_config": result["results"][selected]["config"],
        "selected_config_sha256": result["results"][selected]["config_sha256"],
        "selection_reason": reason,
        "validation_established_robust_historical_alpha": any(
            item["all_gates_pass"] for item in evaluations
        ),
        "official_oos_accessed": False,
        "oos_lock": "LOCKED_UNTIL_GATE_C",
    }
    report["report_sha256"] = canonical_sha256(report)
    write_immutable(output, canonical_json_bytes(report) + b"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--candidate-freeze", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.validation, args.candidate_freeze, args.output), sort_keys=True))
