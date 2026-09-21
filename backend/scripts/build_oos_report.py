"""Build the immutable Official OOS performance report without retuning."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def _load_result(path: Path, period: str) -> dict:
    value = json.loads(path.read_bytes())
    if (
        value["period_kind"] != period
        or canonical_sha256({key: item for key, item in value.items() if key != "result_sha256"})
        != value["result_sha256"]
    ):
        raise ValueError(f"{period}_RESULT_CHANGED")
    return value


def calendar_regimes(strategy: dict, benchmark: dict) -> list[dict]:
    return [
        {
            "year": year,
            "regime": "CSI300_UP_YEAR" if Decimal(benchmark[year]) >= 0 else "CSI300_DOWN_YEAR",
            "strategy_return": strategy_return,
            "csi300_return": benchmark[year],
            "excess_return": format(Decimal(strategy_return) - Decimal(benchmark[year]), "f"),
        }
        for year, strategy_return in strategy.items()
    ]


def build(
    development: Path,
    validation: Path,
    oos: Path,
    methodology: Path,
    output: Path,
) -> dict:
    dev = _load_result(development / "result.json", "DEVELOPMENT")
    val = _load_result(validation / "result.json", "VALIDATION")
    official = _load_result(oos / "result.json", "OUT_OF_SAMPLE")
    frozen = json.loads(methodology.read_bytes())
    digest = frozen.pop("freeze_record_sha256")
    if (
        canonical_sha256(frozen) != digest
        or official["methodology_freeze_sha256"] != digest
        or not official["official_oos_accessed"]
        or official["candidate_order"] != ["S0", "S1", frozen["selected_candidate"]]
    ):
        raise ValueError("OFFICIAL_OOS_LINEAGE_CHANGED")
    selected = frozen["selected_candidate"]
    strategy = official["results"][selected]
    benchmark = official["results"]["S0"]
    report = {
        "report_id": "OFFICIAL_OOS_PERFORMANCE_REPORT_V1",
        "status": "COMPLETE",
        "official_oos_run_number": 1,
        "period": official["period"],
        "dataset_id": official["dataset_id"],
        "dataset_sha256": official["dataset_sha256"],
        "methodology_freeze_sha256": digest,
        "official_result_sha256": official["result_sha256"],
        "official_result_file_sha256": sha256_file(oos / "result.json"),
        "official_receipt_file_sha256": sha256_file(oos / "receipt.json"),
        "strategy_id": strategy["strategy_id"],
        "config_sha256": strategy["config_sha256"],
        "performance": strategy["metrics"],
        "annual_returns": strategy["annual"],
        "monthly_heatmap": strategy["monthly"],
        "rolling_metrics": strategy["rolling"],
        "equity_curve": strategy["equity"],
        "drawdown_curve": strategy["drawdown"],
        "benchmark_curve": strategy["benchmark"],
        "trades": strategy["trades"],
        "trade_statistics": {
            "number_of_trades": strategy["metrics"]["number_of_trades"],
            "closed_trade_sessions": strategy["metrics"]["closed_trade_sessions"],
            "win_rate": strategy["metrics"]["win_rate"],
            "profit_factor": strategy["metrics"]["profit_factor"],
            "average_holding_period": strategy["metrics"]["average_holding_period"],
        },
        "holdings_history": [
            {"date": item["date"], **item["target"]} for item in strategy["rebalances"]
        ],
        "rebalances": strategy["rebalances"],
        "regime_breakdown": calendar_regimes(strategy["annual"], benchmark["annual"]),
        "period_comparison": {
            "DEVELOPMENT": dev["results"][selected]["metrics"],
            "VALIDATION": val["results"][selected]["metrics"],
            "OFFICIAL_OOS": strategy["metrics"],
        },
        "benchmark_comparison": benchmark["metrics"],
        "conclusion": (
            "OOS_RETURN_POSITIVE_BUT_WEAK_NO_ROBUST_PROFITABILITY_CLAIM"
            if Decimal(strategy["metrics"]["cumulative_return"]) > 0
            else "OOS_RETURN_NON_POSITIVE_NO_PROFITABILITY_CLAIM"
        ),
        "limitations": [
            "Validation did not establish robust historical alpha; S4 was the frozen fallback.",
            "OOS is a single historical test and does not imply future returns.",
            "The S1 eligible-universe series is an ancillary comparator; "
            "CSI300 is the frozen benchmark.",
            "Execution remains a daily-bar simulation under CN_A_DAILY_OPENING_LIMIT_V1.",
        ],
        "retuning_after_oos": False,
        "second_official_oos_run_allowed": False,
    }
    report["report_sha256"] = canonical_sha256(report)
    write_immutable(output, canonical_json_bytes(report) + b"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--development", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--oos", required=True, type=Path)
    parser.add_argument("--methodology", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            build(
                args.development,
                args.validation,
                args.oos,
                args.methodology,
                args.output,
            ),
            sort_keys=True,
        )
    )
