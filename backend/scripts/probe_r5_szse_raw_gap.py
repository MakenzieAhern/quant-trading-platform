"""Probe the fixed 2011-07-25 SZSE raw-row gap; never promotes source authority."""

import argparse
import ast
import base64
import csv
import json
import sys
from collections import Counter
from datetime import date
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from scripts.audit_amount_impact import QUANTUM, interval_decisions
from scripts.reconcile_sse_cninfo import fetch, save, sha

TARGET_DATE = "2011-07-25"
VERSION = "r5-szse-20110725-raw-candidate-v1"
TENCENT_ENDPOINT = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"


def tencent_url(symbol: str) -> str:
    return (
        TENCENT_ENDPOINT
        + "?"
        + urlencode(
            {
                "_var": "kline_day2011",
                "param": f"sz{symbol},day,2011-01-01,2012-12-31,640,",
                "r": "0.8205512681390605",
            }
        )
    )


def _decimal(value: object) -> Decimal:
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("NON_FINITE_VALUE")
    return result


def _validated(
    symbol: str,
    day: str,
    open_: object,
    close: object,
    high: object,
    low: object,
    volume: object,
    amount: object,
) -> dict[str, str]:
    date.fromisoformat(day)
    values = {
        name: _decimal(value)
        for name, value in {
            "raw_open": open_,
            "raw_close": close,
            "raw_high": high,
            "raw_low": low,
            "volume": volume,
            "amount": amount,
        }.items()
    }
    if day != TARGET_DATE:
        raise ValueError("WRONG_TARGET_DATE")
    if min(values[name] for name in ("raw_open", "raw_close", "raw_high", "raw_low")) <= 0:
        raise ValueError("NON_POSITIVE_PRICE")
    if values["raw_high"] < max(values["raw_open"], values["raw_close"], values["raw_low"]):
        raise ValueError("INVALID_HIGH")
    if values["raw_low"] > min(values["raw_open"], values["raw_close"], values["raw_high"]):
        raise ValueError("INVALID_LOW")
    if values["volume"] < 0 or values["amount"] < 0:
        raise ValueError("NEGATIVE_VOLUME_OR_AMOUNT")
    return {
        "security_id": f"CN-A:SZSE:{symbol}",
        "trading_date": day,
        **{name: str(value) for name, value in values.items()},
    }


def parse_tencent_target(raw: bytes, symbol: str) -> dict[str, str]:
    payload = json.loads(raw.decode().split("=", 1)[1], parse_float=str)
    if payload.get("code") != 0:
        raise ValueError("TENCENT_SERVICE_ERROR")
    rows = (payload.get("data") or {}).get("sz" + symbol, {}).get("day") or []
    matches = [row for row in rows if row and row[0] == TARGET_DATE]
    if len(matches) != 1:
        raise ValueError("TENCENT_TARGET_ROW_COUNT:" + str(len(matches)))
    row = matches[0]
    if len(row) < 9:
        raise ValueError("TENCENT_ROW_SCHEMA_CHANGED")
    return _validated(
        symbol,
        row[0],
        row[1],
        row[2],
        row[3],
        row[4],
        _decimal(row[5]) * 100,
        _decimal(row[8]) * 10000,
    )


def tencent_amount_history(raw: bytes, symbol: str) -> list[dict[str, str]]:
    payload = json.loads(raw.decode().split("=", 1)[1], parse_float=str)
    if payload.get("code") != 0:
        raise ValueError("TENCENT_SERVICE_ERROR")
    rows = (payload.get("data") or {}).get("sz" + symbol, {}).get("day") or []
    history = [
        {"trading_date": row[0], "amount": str(_decimal(row[8]) * 10000)}
        for row in rows
        if len(row) >= 9
    ]
    if len(history) != len(rows):
        raise ValueError("TENCENT_ROW_SCHEMA_CHANGED")
    if [row["trading_date"] for row in history] != sorted({row["trading_date"] for row in history}):
        raise ValueError("TENCENT_HISTORY_NOT_STRICTLY_ORDERED")
    return history


def liquidity_window_check(rows: list[dict[str, str]]) -> dict[str, object]:
    target = next((i for i, row in enumerate(rows) if row["trading_date"] == TARGET_DATE), None)
    if target is None:
        raise ValueError("TENCENT_TARGET_ROW_COUNT:0")
    windows = [
        interval_decisions(rows[start : start + 20], QUANTUM)[-1]
        for start in range(max(0, target - 19), min(target, len(rows) - 20) + 1)
    ]
    if not windows:
        raise ValueError("INSUFFICIENT_LIQUIDITY_HISTORY")
    return {
        "liquidity_windows_checked": len(windows),
        "liquidity_decision_invariant": all(bool(window["stable"]) for window in windows),
        "minimum_distance_to_threshold_cny": str(
            min(Decimal(str(window["distance_to_threshold"])) for window in windows)
        ),
    }


def _decoder(sdk_root: Path) -> tuple[Any, str]:
    decoder = sdk_root / "akshare/stock/cons.py"
    record = sdk_root / "akshare-1.18.94.dist-info/RECORD"
    expected = next(
        row[1]
        for row in csv.reader(record.read_text().splitlines())
        if row[0] == "akshare/stock/cons.py"
    )
    actual = "sha256=" + base64.urlsafe_b64encode(
        bytes.fromhex(sha(decoder.read_bytes()))
    ).decode().rstrip("=")
    if actual != expected:
        raise ValueError("PINNED_SINA_DECODER_CHANGED")
    tree = ast.parse(decoder.read_text())
    code = next(
        ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == "hk_js_decode" for target in node.targets
        )
    )
    sys.path.append(str(sdk_root))  # Reuse the pinned offline SDK; install nothing.
    runtime = import_module("py_mini_racer").MiniRacer()
    runtime.eval(code)
    return runtime, sha(decoder.read_bytes())


def parse_sina_target(raw: bytes, symbol: str, runtime: Any) -> dict[str, str]:
    encoded = raw.decode().split("=", 1)[1].split(";", 1)[0].strip().strip('"')
    rows = runtime.call("d", encoded)
    matches = [row for row in rows if str(row.get("date", ""))[:10] == TARGET_DATE]
    if len(matches) != 1:
        raise ValueError("SINA_TARGET_ROW_COUNT:" + str(len(matches)))
    row = matches[0]
    return _validated(
        symbol,
        TARGET_DATE,
        row["open"],
        row["close"],
        row["high"],
        row["low"],
        row["volume"],
        row["amount"],
    )


def comparison(tencent: dict[str, str], sina: dict[str, str]) -> dict[str, object]:
    price_fields = ("raw_open", "raw_close", "raw_high", "raw_low")
    amount_difference = abs(Decimal(tencent["amount"]) - Decimal(sina["amount"]))
    return {
        "price_parity": all(Decimal(tencent[key]) == Decimal(sina[key]) for key in price_fields),
        "volume_parity": Decimal(tencent["volume"]) == Decimal(sina["volume"]),
        "amount_difference_cny": str(amount_difference),
        "amount_within_accepted_uncertainty_interval": amount_difference <= Decimal(100),
    }


def _targets(gap_report: Path) -> list[str]:
    report = json.loads(gap_report.read_bytes())
    rows = report["unresolved_rows"]
    if len(rows) != 239 or any(
        row["date"] != TARGET_DATE or not row["security_id"].startswith("CN-A:SZSE:300")
        for row in rows
    ):
        raise ValueError("FIXED_RESIDUAL_SCOPE_CHANGED")
    symbols = sorted({row["security_id"].rsplit(":", 1)[1] for row in rows})
    if len(symbols) != len(rows):
        raise ValueError("DUPLICATE_RESIDUAL_SECURITY_DATE")
    return symbols


def run(staging: Path, sdk_root: Path, limit: int) -> dict[str, object]:
    root = staging / "full-raw-coverage-v1"
    output = root / "tencent-sina-20110725-candidate-v1"
    gap_report = root / "szse-official-row-gaps-v32-replay-v1.json"
    symbols = _targets(gap_report)
    if limit < 1 or limit > len(symbols):
        raise ValueError("LIMIT_OUTSIDE_FIXED_SCOPE")
    runtime, decoder_sha = _decoder(sdk_root)
    results = []
    stopped = False
    for symbol in symbols[:limit]:
        result: dict[str, object] = {"security_id": f"CN-A:SZSE:{symbol}"}
        try:
            t_url = tencent_url(symbol)
            s_url = (
                f"https://finance.sina.com.cn/realstock/company/sz{symbol}/hisdata_klc2/klc_kl.js"
            )
            t_path = output / "tencent" / f"{symbol}.json"
            s_path = output / "sina" / f"{symbol}.js"
            t_raw = fetch(t_path.parent, t_path.name, t_url)
            s_raw = fetch(s_path.parent, s_path.name, s_url)
            t_row = parse_tencent_target(t_raw, symbol)
            s_row = parse_sina_target(s_raw, symbol, runtime)
            checks = comparison(t_row, s_row)
            checks.update(liquidity_window_check(tencent_amount_history(t_raw, symbol)))
            accepted = bool(
                checks["price_parity"]
                and checks["volume_parity"]
                and checks["amount_within_accepted_uncertainty_interval"]
                and checks["liquidity_decision_invariant"]
            )
            result.update(
                status="DUAL_SOURCE_PARITY" if accepted else "DUAL_SOURCE_DIFFERENCE",
                tencent=t_row,
                sina=s_row,
                comparison=checks,
                sources=[
                    {
                        "provider": "Tencent",
                        "url": t_url,
                        "sha256": sha(t_raw),
                        "metadata": json.loads(t_path.with_suffix(".json.meta.json").read_bytes()),
                    },
                    {
                        "provider": "Sina",
                        "url": s_url,
                        "sha256": sha(s_raw),
                        "metadata": json.loads(s_path.with_suffix(".js.meta.json").read_bytes()),
                    },
                ],
            )
        except Exception as exc:
            denied = getattr(exc, "code", None) in {403, 429} or "ACCESS_DENIED" in str(exc)
            result.update(status="ACCESS_DENIAL_STOP" if denied else "UNRESOLVED", error=str(exc))
            stopped = denied
        results.append(result)
        counts = dict(Counter(str(row["status"]) for row in results))
        report: dict[str, object] = {
            "report_version": VERSION,
            "candidate_only": True,
            "promoted": False,
            "target_date": TARGET_DATE,
            "fixed_residual_total": len(symbols),
            "requested_limit": limit,
            "completed": len(results),
            "classification_counts": counts,
            "source_gap_report_sha256": sha(gap_report.read_bytes()),
            "sina_decoder_sha256": decoder_sha,
            "input_order_reproducibility": (
                "PASS"
                if sorted(results, key=lambda row: str(row["security_id"]))
                == sorted(reversed(results), key=lambda row: str(row["security_id"]))
                else "FAIL"
            ),
            "status": "ACCESS_DENIAL_STOP" if stopped else "CANDIDATE_EVIDENCE_ONLY",
            "results": results,
        }
        save(output / "report.json", report)
        print(symbol, result["status"], flush=True)
        if stopped:
            break
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(run(args.staging, args.sdk_root, args.limit), ensure_ascii=False))
