"""Route unmatched retained factor changes to checksum-bound official bonus evidence."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_full_cash_ledger import verified
from scripts.reconcile_sse_cninfo import canonical, sha

PRICE_TICK = Decimal("0.01")


def security_id(row: dict) -> str:
    exchanges = {item["exchange"] for item in row["evidence"]}
    if len(exchanges) != 1:
        raise ValueError("BONUS_ORACLE_EXCHANGE_CONFLICT")
    return f"CN-A:{exchanges.pop()}:{row['symbol']}"


def rounding_bounds(value: str) -> tuple[Decimal, Decimal]:
    number = Decimal(value.replace(",", ""))
    half_unit = PRICE_TICK / 2
    return number - half_unit, number + half_unit


def displayed_price_check(factor_step: Decimal, evidence: list[dict]) -> tuple[str, list[dict]]:
    checks = []
    for item in evidence:
        source = item["source_evidence"]
        cells = source.get("raw_cells")
        if cells is None:
            continue
        if len(cells) != 14 or not cells[12] or not cells[13]:
            continue
        ex_low, ex_high = rounding_bounds(cells[12])
        pre_low, pre_high = rounding_bounds(cells[13])
        if ex_low <= 0:
            continue
        lower, upper = pre_low / ex_high, pre_high / ex_low
        checks.append(
            {
                "source_sha256": source["source_sha256"],
                "source_url": source["source_url"],
                "reported_ex_price": cells[12],
                "reported_pre_close": cells[13],
                "implied_factor_step_lower": str(lower),
                "implied_factor_step_upper": str(upper),
                "factor_step_within_display_rounding": lower <= factor_step <= upper,
            }
        )
    if not checks:
        return "DISPLAYED_PRICE_RATIO_UNAVAILABLE", []
    status = (
        "DISPLAYED_PRICE_RATIO_BOUNDS_PASS"
        if all(item["factor_step_within_display_rounding"] for item in checks)
        else "DISPLAYED_PRICE_RATIO_BOUNDS_CONFLICT"
    )
    return status, checks


def zero_cash_bonus_ratio_check(
    factor_step: Decimal, evidence: list[dict], cash_absent: bool
) -> str:
    checks = []
    for item in evidence:
        source = item["source_evidence"]
        cells = source.get("raw_cells")
        if cells is not None:
            if len(cells) != 14 or not cells[5] or Decimal(cells[5]) != 0:
                continue
        elif not cash_absent:
            continue
        ratio = Decimal(item["ratio"])
        half_unit = Decimal(1).scaleb(ratio.as_tuple().exponent) / 2
        checks.append(
            Decimal(1) + ratio - half_unit <= factor_step <= Decimal(1) + ratio + half_unit
        )
    if not checks:
        return "NOT_APPLICABLE_OR_UNAVAILABLE"
    return (
        "ZERO_CASH_BONUS_RATIO_BOUNDS_PASS"
        if all(checks)
        else "ZERO_CASH_BONUS_RATIO_BOUNDS_CONFLICT"
    )


def official_cash_dates(ledger: dict) -> set[tuple[str, str]]:
    if (
        ledger["coverage"] != ["2010-01-01", "2025-12-31"]
        or ledger["unresolved_official_cash_events"] != 0
        or ledger["input_order_reproducibility"] != "PASS"
        or ledger["checksum_repeatability"] != "PASS"
    ):
        raise ValueError("OFFICIAL_CASH_COVERAGE_INCOMPLETE")
    return {
        (row["event"]["security_id"]["value"], row["event"]["ex_date"]) for row in ledger["events"]
    }


def route(adjustment: dict, oracle: dict, cash_ledger: dict) -> dict:
    unmatched = {
        (row["security_id"], row["effective_date"]): row
        for row in adjustment["factor_changes"]
        if row["status"] == "NO_SUPPORTED_EVENT_DATE"
    }
    curves = {}
    for interval in adjustment["intervals"]:
        if len(interval["in_interval_variants"]) != 1:
            raise ValueError("UNRESOLVED_FACTOR_CURVE")
        variant = next(iter(interval["in_interval_variants"].values()))
        rows = [variant["baseline"], *variant["period_rows"]]
        rows = [row for index, row in enumerate(rows) if index == 0 or row != rows[index - 1]]
        curves[interval["security_id"]] = rows
    official = {}
    for row in oracle["rows"]:
        key = security_id(row), row["ex_date"]
        if key in official:
            raise ValueError("DUPLICATE_BONUS_ORACLE_DATE")
        official[key] = row
    cash_dates = official_cash_dates(cash_ledger)

    routed = []
    for key, change in sorted(unmatched.items()):
        source = official.get(key)
        if source is None:
            routed.append({**change, "route": "NO_RETAINED_OFFICIAL_BONUS_DATE"})
            continue
        curve = curves[key[0]]
        index = next((i for i, row in enumerate(curve) if row[0] == key[1]), None)
        if index in (None, 0):
            raise ValueError("FACTOR_STEP_BASELINE_MISSING")
        factor_step = Decimal(curve[index][1]) / Decimal(curve[index - 1][1])
        ratios = {Decimal(item["ratio"]) for item in source["evidence"]}
        price_status, price_checks = displayed_price_check(factor_step, source["evidence"])
        cash_absent = key not in cash_dates
        ratio_status = zero_cash_bonus_ratio_check(factor_step, source["evidence"], cash_absent)
        alignment_status = (
            "OFFICIAL_BONUS_FACTOR_ALIGNMENT_PASS"
            if price_status == "DISPLAYED_PRICE_RATIO_BOUNDS_PASS"
            or ratio_status == "ZERO_CASH_BONUS_RATIO_BOUNDS_PASS"
            else "OFFICIAL_BONUS_FACTOR_ALIGNMENT_CONFLICT"
        )
        routed.append(
            {
                **change,
                "route": "RETAINED_OFFICIAL_BONUS_SOURCE_DATE",
                "bonus_ratio_class": (
                    "INTEGER"
                    if all(value == value.to_integral_value() for value in ratios)
                    else "FRACTIONAL"
                ),
                "bonus_ratio_consistency": source["ratio_consistency"],
                "new_share_tradability": source["new_share_tradability"],
                "source_evidence_sha256": source["evidence_sha256"],
                "factor_step_ratio": str(factor_step),
                "displayed_price_ratio_status": price_status,
                "displayed_price_ratio_checks": price_checks,
                "zero_cash_bonus_ratio_status": ratio_status,
                "cash_event_absent_in_complete_official_ledger": cash_absent,
                "factor_economic_alignment_status": alignment_status,
            }
        )
    counts = Counter(row["route"] for row in routed)
    bonus = [row for row in routed if row["route"] == "RETAINED_OFFICIAL_BONUS_SOURCE_DATE"]
    return {
        "report_id": "FULL_ADJUSTMENT_UNMATCHED_ROUTING_V3",
        "status": "PARTIAL_ROUTING_ONLY_NO_AUTHORITY_PROMOTION",
        "requested_coverage": adjustment["requested_coverage"],
        "unmatched_factor_changes": len(routed),
        "route_counts": dict(sorted(counts.items())),
        "bonus_ratio_classes": dict(
            sorted(Counter(row["bonus_ratio_class"] for row in bonus).items())
        ),
        "bonus_tradability_statuses": dict(
            sorted(Counter(row["new_share_tradability"] for row in bonus).items())
        ),
        "displayed_price_ratio_statuses": dict(
            sorted(Counter(row["displayed_price_ratio_status"] for row in bonus).items())
        ),
        "zero_cash_bonus_ratio_statuses": dict(
            sorted(Counter(row["zero_cash_bonus_ratio_status"] for row in bonus).items())
        ),
        "factor_economic_alignment_statuses": dict(
            sorted(Counter(row["factor_economic_alignment_status"] for row in bonus).items())
        ),
        "rows": routed,
        "limitations": [
            "Official summary-table dates and displayed prices are coverage evidence, "
            "not accepted events.",
            "Displayed ex-price bounds do not replace exact issuer economic terms or "
            "registry allocation.",
            "Unrouted factor changes remain unexplained and are not classified as normal.",
        ],
        "adjustment_authority_promoted": False,
        "dataset_created": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adjustment", type=Path, required=True)
    parser.add_argument("--bonus-oracle", type=Path, required=True)
    parser.add_argument("--cash-ledger", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adjustment, oracle, cash_ledger = map(
        verified, (args.adjustment, args.bonus_oracle, args.cash_ledger)
    )
    report = route(adjustment, oracle, cash_ledger)
    replay = route(
        dict(
            adjustment,
            factor_changes=list(reversed(adjustment["factor_changes"])),
            intervals=list(reversed(adjustment["intervals"])),
        ),
        dict(oracle, rows=list(reversed(oracle["rows"]))),
        dict(cash_ledger, events=list(reversed(cash_ledger["events"]))),
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        parser_sha256=sha256_file(Path(__file__)),
        input_order_reproducibility="PASS",
        checksum_repeatability="PASS",
        inputs=[
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (args.adjustment, args.bonus_oracle, args.cash_ledger)
        ],
    )
    report["manifest_sha256"] = sha(canonical(report))
    write_immutable(args.output, canonical(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "unmatched_factor_changes",
                    "route_counts",
                    "bonus_ratio_classes",
                    "bonus_tradability_statuses",
                    "displayed_price_ratio_statuses",
                    "zero_cash_bonus_ratio_statuses",
                    "factor_economic_alignment_statuses",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
