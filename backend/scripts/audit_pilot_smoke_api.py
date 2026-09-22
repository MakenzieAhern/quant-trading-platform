"""Read-only API parity against the immutable smoke result; no study execution."""

import argparse
import json
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256
from app.data.catalog.freeze import write_immutable
from scripts.run_pilot_smoke import LABEL


def audit(output: Path, api_root: str) -> dict:
    result = json.loads((output / "result.json").read_bytes())
    persistence = json.loads((output / "persistence.json").read_bytes())
    if canonical_sha256(result) != persistence["result_sha256"]:
        raise ValueError("SMOKE_RESULT_CHANGED")
    base = api_root.rstrip("/") + "/api/research/runs/" + persistence["run_id"]

    def read(url):
        with urlopen(url, timeout=15) as response:
            return json.load(response)

    def collection(name):
        items, total = [], None
        while total is None or len(items) < total:
            page = read(base + f"/{name}?limit=200&offset={len(items)}")
            if (total is not None and page["total"] != total) or (
                not page["items"] and page["total"] > len(items)
            ):
                raise ValueError("API_PAGINATION_CHANGED")
            total = page["total"]
            items.extend(page["items"])
        return items

    run = read(base)
    if not (
        run["status"] == "SUCCEEDED"
        and run["period_kind"] == "PILOT_SMOKE"
        and run["diagnostics"]["label"] == LABEL
        and run["diagnostics"]["result_sha256"] == persistence["result_sha256"]
        and run["dataset_checksum"] == result["dataset_checksum"]
        and run["strategy_config_hash"] == result["strategy_config_hash"]
    ):
        raise ValueError("API_RUN_PARITY_FAILED")
    metrics = {
        r["metric_name"]: Decimal(r["value"]) if r["value"] is not None else None
        for r in collection("metrics")
    }
    expected = {k: Decimal(str(v)) if v is not None else None for k, v in result["metrics"].items()}
    if metrics != expected:
        raise ValueError("API_METRIC_PARITY_FAILED")
    for kind in ("equity", "benchmark"):
        points = collection(kind)
        if [(p["trading_date"], Decimal(p["value"])) for p in points] != [
            (p["trading_date"], Decimal(p["value"])) for p in result[kind]
        ] or [p["sequence"] for p in points] != list(range(len(points))):
            raise ValueError("API_CURVE_PARITY_FAILED")
    drawdowns = collection("drawdown")
    if len(drawdowns) != len(result["equity"]) or any(Decimal(p["value"]) != 0 for p in drawdowns):
        raise ValueError("API_DRAWDOWN_PARITY_FAILED")
    if collection("trades") or collection("holdings"):
        raise ValueError("API_FABRICATED_TRADES_OR_HOLDINGS")
    rebalances = collection("rebalances")
    if [r["trading_date"] for r in rebalances] != [r["date"] for r in result["rebalances"]]:
        raise ValueError("API_REBALANCE_PARITY_FAILED")
    report = dict(
        label=LABEL,
        run_id=persistence["run_id"],
        result_sha256=persistence["result_sha256"],
        api_result_parity="PASS",
        metrics=len(metrics),
        points_per_curve=len(result["equity"]),
        trades=0,
        holdings=0,
        rebalances=len(rebalances),
    )
    write_immutable(output / "api-audit.json", canonical_json_bytes(report) + b"\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--api-root", default="http://localhost:8000")
    args = parser.parse_args()
    print(json.dumps(audit(args.output, args.api_root)))
