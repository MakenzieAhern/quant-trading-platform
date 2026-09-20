"""Crosscheck retained factor steps against exact official cash/bonus terms and raw pre-close."""

import argparse
import json
import warnings
from collections import Counter
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from io import BytesIO
from itertools import pairwise
from pathlib import Path

from openpyxl import load_workbook

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.probe_szse_official_daily import HEADERS
from scripts.reconcile_distribution_cash import verified

ROUNDING_TOLERANCE = Decimal("1e-12")


def economics(pre_close: Decimal, cash: Decimal, bonus: Decimal, factor_step: Decimal) -> dict:
    if pre_close <= cash or cash < 0 or bonus < 0:
        raise ValueError("INVALID_CORPORATE_ACTION_ECONOMICS")
    with localcontext() as context:
        context.prec = 50
        expected = pre_close * (Decimal(1) + bonus) / (pre_close - cash)
        delta = abs(expected - factor_step)
        normalized_cash = cash.quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)
        normalized_expected = pre_close * (Decimal(1) + bonus) / (pre_close - normalized_cash)
        normalized_delta = abs(normalized_expected - factor_step)
    exact = delta <= ROUNDING_TOLERANCE
    cash_normalized = cash.as_tuple().exponent < -6 and normalized_delta <= ROUNDING_TOLERANCE
    result = {
        "expected_factor_step": str(expected),
        "observed_factor_step": str(factor_step),
        "absolute_delta": str(delta),
        "status": (
            "GROSS_TERMS_FACTOR_PARITY_PASS"
            if exact
            else (
                "GROSS_TERMS_FACTOR_PARITY_PASS_PROVIDER_CASH_PRECISION"
                if cash_normalized
                else "GROSS_TERMS_FACTOR_PARITY_CONFLICT"
            )
        ),
    }
    if cash_normalized and not exact:
        result.update(
            provider_normalized_cash_per_share=str(normalized_cash),
            provider_normalized_expected_factor_step=str(normalized_expected),
            provider_normalized_absolute_delta=str(normalized_delta),
        )
    return result


def factor_source_symbols(adjustment: dict) -> dict[tuple[str, str], str]:
    result = {}
    for interval in adjustment["intervals"]:
        symbol = interval["symbol"][-6:]
        for variant in interval["in_interval_variants"].values():
            for day in variant["change_dates"]:
                result[interval["security_id"], day] = symbol
    return result


def factor_steps(adjustment: dict) -> dict[tuple[str, str], Decimal]:
    result = {}
    for interval in adjustment["intervals"]:
        if len(interval["in_interval_variants"]) != 1:
            raise ValueError("UNRESOLVED_FACTOR_CURVE")
        variant = next(iter(interval["in_interval_variants"].values()))
        rows = [variant["baseline"], *variant["period_rows"]]
        rows = [row for index, row in enumerate(rows) if index == 0 or row != rows[index - 1]]
        for previous, current in pairwise(rows):
            if Decimal(previous[1]) != Decimal(current[1]):
                result[interval["security_id"], current[0]] = Decimal(current[1]) / Decimal(
                    previous[1]
                )
    return result


def szse_pre_closes(root: Path, report: dict, requests: set[tuple[str, str]]) -> dict:
    receipts = {row["date"]: row for row in report["results"]}
    sessions = sorted(receipts)
    previous = {day: sessions[index - 1] for index, day in enumerate(sessions) if index}
    by_day = {}
    for symbol, day in requests:
        if prior_day := previous.get(day):
            by_day.setdefault(prior_day, {}).setdefault(symbol, set()).add(day)
    result = {}
    for prior_day, targets in sorted(by_day.items()):
        path = root / f"{prior_day}.xlsx"
        if sha256_file(path) != receipts[prior_day]["source_sha256"]:
            raise ValueError("SZSE_DAILY_SOURCE_CHANGED")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            workbook = load_workbook(BytesIO(path.read_bytes()), read_only=True, data_only=True)
        sheet = workbook.active
        sheet.reset_dimensions()
        rows = sheet.values
        if tuple(next(rows)) != HEADERS:
            raise ValueError("SZSE_DAILY_COLUMNS_CHANGED")
        for row in rows:
            if row[1] in targets:
                # On an ex-date, 前收 is already the adjusted reference price.
                # The economic formula needs the prior session's actual 今收.
                for target_day in targets[row[1]]:
                    result[row[1], target_day] = Decimal(str(row[7]))
        workbook.close()
    return result


def sse_pre_closes(root: Path, report: dict, requests: set[tuple[str, str]]) -> dict:
    receipts = {row["symbol"]: row for row in report["results"]}
    result = {}
    for symbol, day in sorted(requests):
        path = root / f"{symbol}.json"
        if sha256_file(path) != receipts[symbol]["source_sha256"]:
            raise ValueError("SSE_DAILY_SOURCE_CHANGED")
        target = int(day.replace("-", ""))
        prior = [row for row in json.loads(path.read_bytes())["kline"] if row[0] < target]
        if prior:
            result[symbol, day] = Decimal(str(prior[-1][4]))
    return result


def audit(adjustment: dict, terms: dict, pre_closes: dict) -> dict:
    steps = factor_steps(adjustment)
    rows = []
    for candidate in terms["factor_results"]:
        if candidate["status"] != "UNIQUE_EXACT_OFFICIAL_TERMS_CANDIDATE":
            continue
        evidence = candidate["evidence"][0]
        if evidence["cash_per_share"] is None or evidence["bonus_share_ratio"] is None:
            continue
        event, day = candidate["factor_change"].removeprefix("FACTOR:").rsplit(":", 1)
        symbol = event.rsplit(":", 1)[-1]
        pre_close = pre_closes.get((symbol, day))
        if pre_close is None:
            rows.append(
                {
                    "factor_change": candidate["factor_change"],
                    "status": "OFFICIAL_RAW_PRE_CLOSE_UNAVAILABLE",
                }
            )
            continue
        rows.append(
            {
                "factor_change": candidate["factor_change"],
                "pre_close": str(pre_close),
                "cash_per_share": evidence["cash_per_share"],
                "bonus_share_ratio": evidence["bonus_share_ratio"],
                "official_terms_source_sha256": evidence["source_sha256"],
                **economics(
                    pre_close,
                    Decimal(evidence["cash_per_share"]),
                    Decimal(evidence["bonus_share_ratio"]),
                    steps[event, day],
                ),
            }
        )
    return {
        "report_id": "FULL_ADJUSTMENT_FACTOR_ECONOMICS_V2",
        "status": "GROSS_TERMS_DIAGNOSTIC_ONLY_NO_AUTHORITY_PROMOTION",
        "eligible_exact_cash_bonus_terms": len(rows),
        "counts": dict(sorted(Counter(row["status"] for row in rows).items())),
        "rows": sorted(rows, key=lambda row: row["factor_change"]),
        "rounding_tolerance": str(ROUNDING_TOLERANCE),
        "adjustment_authority_promoted": False,
        "dataset_created": False,
        "limitations": [
            "Gross shareholder cash is not replaced by tax-net or synthetic ex-price terms.",
            "Historical provider factor cash-basis conventions are not established by this audit.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adjustment", type=Path, required=True)
    parser.add_argument("--terms", type=Path, required=True)
    parser.add_argument("--szse-root", type=Path, required=True)
    parser.add_argument("--szse-report", type=Path, required=True)
    parser.add_argument("--sse-root", type=Path, required=True)
    parser.add_argument("--sse-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adjustment, terms = verified(args.adjustment), verified(args.terms)
    szse_report = json.loads(args.szse_report.read_bytes())
    sse_report = json.loads(args.sse_report.read_bytes())
    eligible = [
        row
        for row in terms["factor_results"]
        if row["status"] == "UNIQUE_EXACT_OFFICIAL_TERMS_CANDIDATE"
        and row["evidence"][0]["cash_per_share"] is not None
        and row["evidence"][0]["bonus_share_ratio"] is not None
    ]
    source_symbols = factor_source_symbols(adjustment)
    requests = {
        (
            source_symbols.get(
                (
                    row["factor_change"].removeprefix("FACTOR:").rsplit(":", 1)[0],
                    row["factor_change"].split(":")[-1],
                ),
                row["factor_change"].split(":")[-2],
            ),
            row["factor_change"].split(":")[-1],
        )
        for row in eligible
    }
    szse_requests = {item for item in requests if item[0].startswith(("0", "3"))}
    sse_requests = requests - szse_requests
    raw_pre_closes = {
        **szse_pre_closes(args.szse_root, szse_report, szse_requests),
        **sse_pre_closes(args.sse_root, sse_report, sse_requests),
    }
    pre_closes = dict(raw_pre_closes)
    aliases = []
    for (security_id, day), source_symbol in sorted(source_symbols.items()):
        current_symbol = security_id.rsplit(":", 1)[-1]
        if source_symbol != current_symbol and (source_symbol, day) in raw_pre_closes:
            pre_closes[current_symbol, day] = raw_pre_closes[source_symbol, day]
            aliases.append(
                {
                    "security_id": security_id,
                    "date": day,
                    "source_symbol": source_symbol,
                }
            )
    report = audit(adjustment, terms, pre_closes)
    replay = audit(
        dict(adjustment, intervals=list(reversed(adjustment["intervals"]))),
        dict(terms, factor_results=list(reversed(terms["factor_results"]))),
        pre_closes,
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        historical_symbol_aliases=aliases,
        input_order_reproducibility="PASS",
        inputs=[
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (
                args.adjustment,
                args.terms,
                args.szse_report,
                args.sse_report,
            )
        ],
        parser_sha256=sha256_file(Path(__file__)),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "eligible_exact_cash_bonus_terms",
                    "counts",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
