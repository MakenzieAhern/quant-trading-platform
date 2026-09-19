"""Probe the fixed 2011-07-25 SZSE raw-row gap; never promotes source authority."""

import argparse
import ast
import base64
import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from importlib import import_module
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

from pypdf import PdfReader

from scripts.audit_amount_impact import QUANTUM, interval_decisions
from scripts.audit_szse_daily_transaction_scope import number, workbook
from scripts.reconcile_sse_cninfo import fetch, save, sha

TARGET_DATE = "2011-07-25"
VERSION = "r5-szse-20110725-raw-candidate-v1"
TENCENT_ENDPOINT = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get"
FACTBOOK_SHA256 = "38289a861878de122015747d09ca3dc1f7e05de127c572ae2ac4792206460bd4"
FACTBOOK_URL = "https://docs.static.szse.cn/www/market/periodical/year/W020250610540370351431.pdf"
BLOCK_CATALOG = "1932_dzjyzqjy_after"


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


def _july_day_25(lines: list[str]) -> str:
    line = next(
        normalized
        for row in lines
        if (normalized := unicodedata.normalize("NFKC", row)).strip().startswith("25")
    )
    numbers: list[str] = re.findall(r"\d+(?:\.\d+)?", line)
    if len(numbers) != 10 or numbers[0] != "25":
        raise ValueError("OFFICIAL_FACTBOOK_TABLE_CHANGED")
    return numbers[6]  # July is the sixth trading-month value on day 25.


def official_aggregate(factbook: Path) -> dict[str, object]:
    if sha(factbook.read_bytes()) != FACTBOOK_SHA256:
        raise ValueError("OFFICIAL_FACTBOOK_CHANGED")
    metadata = json.loads(factbook.with_suffix(f"{factbook.suffix}.meta.json").read_bytes())
    if metadata["sha256"] != FACTBOOK_SHA256 or metadata["url"] != FACTBOOK_URL:
        raise ValueError("OFFICIAL_FACTBOOK_PROVENANCE_CHANGED")
    reader = PdfReader(factbook)
    values = [
        _july_day_25((reader.pages[page].extract_text(extraction_mode="layout") or "").splitlines())
        for page in (162, 163)
    ]
    return {
        "volume_million_shares": values[0],
        "amount_million_cny": values[1],
        "source_url": FACTBOOK_URL,
        "pdf_sha256": FACTBOOK_SHA256,
        "retrieved_at_utc": metadata["retrieved_at_utc"],
        "pdf_pages": {"volume": 163, "amount": 164},
        "printed_pages": {"volume": 147, "amount": 148},
        "parser_version": "szse-yearbook-daily-table-v1",
    }


def _chinext_detail_totals(rows: list[tuple[object, ...]], amount_index: int) -> dict[str, Any]:
    selected = [row for row in rows if str(row[1]).startswith(("300", "301"))]
    return {
        "rows": len(selected),
        "symbols": sorted({str(row[1]) for row in selected}),
        "volume_shares": str(sum((number(row[4]) * 10_000 for row in selected), Decimal(0))),
        "amount_cny": str(
            sum((number(row[amount_index]) * 10_000 for row in selected), Decimal(0))
        ),
    }


def official_block_aggregate(block_root: Path) -> dict[str, object]:
    tables = {}
    sources = {}
    for tab in ("tab1", "tab2", "tab3"):
        path = block_root / f"{tab}.xlsx"
        raw = path.read_bytes()
        metadata = json.loads(path.with_suffix(".xlsx.meta.json").read_bytes())
        url = urlparse(metadata["url"])
        query = parse_qs(url.query)
        if (
            sha(raw) != metadata["sha256"]
            or url.netloc != "www.szse.cn"
            or url.path != "/api/report/ShowReport"
            or query.get("CATALOGID") != [BLOCK_CATALOG]
            or query.get("SHOWTYPE") != ["XLSX"]
            or query.get("TABKEY") != [tab]
            or query.get("txtStart") != [TARGET_DATE]
            or query.get("txtEnd") != [TARGET_DATE]
        ):
            raise ValueError(f"OFFICIAL_BLOCK_SOURCE_CHANGED:{tab}")
        tables[tab] = workbook(path)
        if any(row[0] != TARGET_DATE for row in tables[tab][1:]):
            raise ValueError(f"OFFICIAL_BLOCK_DATE_CHANGED:{tab}")
        sources[tab] = metadata
    if tuple(len(tables[tab][0]) for tab in ("tab1", "tab2", "tab3")) != (5, 8, 5):
        raise ValueError("OFFICIAL_BLOCK_COLUMNS_CHANGED")
    agreement = _chinext_detail_totals(tables["tab2"][1:], 5)
    fixed_price = _chinext_detail_totals(tables["tab3"][1:], 3)
    return {
        "agreement": agreement,
        "fixed_price": fixed_price,
        "detail_rows": int(agreement["rows"]) + int(fixed_price["rows"]),
        "symbols": sorted(set(agreement["symbols"]) | set(fixed_price["symbols"])),
        "volume_shares": str(
            Decimal(str(agreement["volume_shares"])) + Decimal(str(fixed_price["volume_shares"]))
        ),
        "amount_cny": str(
            Decimal(str(agreement["amount_cny"])) + Decimal(str(fixed_price["amount_cny"]))
        ),
        "sources": sources,
    }


def aggregate_comparison(
    rows: list[dict[str, object]],
    official: dict[str, object],
    supplement: dict[str, object] | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {}
    added_volume = Decimal(str(supplement["volume_shares"])) if supplement else Decimal(0)
    added_amount = Decimal(str(supplement["amount_cny"])) if supplement else Decimal(0)
    for provider in ("tencent", "sina"):
        total_volume = (
            sum(
                (Decimal(str(row[provider]["volume"])) for row in rows),  # type: ignore[index]
                Decimal(0),
            )
            + added_volume
        )
        total_amount = (
            sum(
                (Decimal(str(row[provider]["amount"])) for row in rows),  # type: ignore[index]
                Decimal(0),
            )
            + added_amount
        )
        volume_million = (total_volume / Decimal(1_000_000)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        amount_million = (total_amount / Decimal(1_000_000)).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        result[provider] = {
            "rows": len(rows),
            "supplement_volume_shares": str(added_volume),
            "supplement_amount_cny": str(added_amount),
            "volume_shares": str(total_volume),
            "amount_cny": str(total_amount),
            "official_minus_total_volume_shares": str(
                Decimal(str(official["volume_million_shares"])) * 1_000_000 - total_volume
            ),
            "official_minus_total_amount_cny": str(
                Decimal(str(official["amount_million_cny"])) * 1_000_000 - total_amount
            ),
            "volume_million_shares_at_official_precision": str(volume_million),
            "amount_million_cny_at_official_precision": str(amount_million),
            "volume_matches_official": volume_million
            == Decimal(str(official["volume_million_shares"])),
            "amount_matches_official": amount_million
            == Decimal(str(official["amount_million_cny"])),
        }
    result["all_provider_aggregates_match_official"] = all(
        bool(result[provider][field])  # type: ignore[index]
        for provider in ("tencent", "sina")
        for field in ("volume_matches_official", "amount_matches_official")
    )
    return result


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


def run(
    staging: Path,
    sdk_root: Path,
    limit: int,
    factbook: Path | None = None,
    block_root: Path | None = None,
) -> dict[str, object]:
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
    if factbook is not None and limit == len(symbols) and not stopped:
        official = official_aggregate(factbook)
        aggregate = aggregate_comparison(results, official)
        block = official_block_aggregate(block_root) if block_root else None
        aggregate_with_block = aggregate_comparison(results, official, block) if block else None
        report.update(
            official_chinext_aggregate=official,
            aggregate_comparison=aggregate,
            official_chinext_block_trades=block,
            aggregate_plus_official_blocks=aggregate_with_block,
            status=(
                "CANDIDATE_EVIDENCE_WITH_OFFICIAL_BLOCK_AGGREGATE_CLOSURE"
                if aggregate_with_block
                and aggregate_with_block["all_provider_aggregates_match_official"]
                else "CANDIDATE_EVIDENCE_WITH_OFFICIAL_AGGREGATE_PARITY"
                if aggregate["all_provider_aggregates_match_official"]
                else "CANDIDATE_EVIDENCE_WITH_OFFICIAL_AGGREGATE_DIFFERENCE"
            ),
        )
        save(output / "report.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--official-factbook", type=Path)
    parser.add_argument("--official-block-root", type=Path)
    args = parser.parse_args()
    print(
        json.dumps(
            run(
                args.staging,
                args.sdk_root,
                args.limit,
                args.official_factbook,
                args.official_block_root,
            ),
            ensure_ascii=False,
        )
    )
