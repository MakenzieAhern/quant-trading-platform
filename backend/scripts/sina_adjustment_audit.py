"""Decimal-safe Sina factor parsing and offline acceptance checks, never execution prices."""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from scripts.reconcile_sse_cninfo import canonical, save, sha

VERSION = "sina-multiplicative-asof-v1"
FactorCurve = list[tuple[str, Decimal]]


def parse_factors(raw: bytes, symbol: str, mode: str) -> FactorCurve:
    if not re.fullmatch(r"(?:sh|sz)\d{6}", symbol) or mode not in {"hfq", "qfq"}:
        raise ValueError("INVALID_FACTOR_IDENTITY")
    line = raw.decode("utf-8").splitlines()[0].rstrip(";")
    prefix = f"var {symbol}{mode}="
    if not line.startswith(prefix):
        raise ValueError("WRONG_FACTOR_RESPONSE")
    payload = json.loads(line[len(prefix) :])
    rows = payload["data"]
    if not rows or payload["total"] != len(rows):
        raise ValueError("INCOMPLETE_FACTOR_RESPONSE")
    normalized: dict[str, Decimal] = {}
    for row in rows:
        day, value = row["d"], Decimal(row["f"])
        if date.fromisoformat(day).isoformat() != day or not value.is_finite() or value <= 0:
            raise ValueError("INVALID_FACTOR_ROW")
        if day in normalized:
            raise ValueError("DUPLICATE_FACTOR_DATE")
        normalized[day] = value
    return sorted(normalized.items())


def factor_at(curve: FactorCurve, day: str) -> Decimal:
    if date.fromisoformat(day).isoformat() != day:
        raise ValueError("NON_CANONICAL_FACTOR_DATE")
    eligible = [(d, v) for d, v in curve if d <= day]
    if not eligible:
        raise ValueError("UNKNOWN_FACTOR_BASELINE")
    return max(eligible, key=lambda row: row[0])[1]


def feature_close(raw: Decimal, day: str, as_of: str, curve: FactorCurve) -> Decimal:
    """Frozen-vintage, as-of-normalized research price; never an execution quote."""
    if day > as_of or not raw.is_finite() or raw <= 0:
        raise ValueError("INVALID_RESEARCH_PRICE")
    return raw * factor_at(curve, day) / factor_at(curve, as_of)


def audit(root: Path) -> dict[str, Any]:
    comparisons, factors, failures = [], {}, []
    samples = json.loads((root / "sample-contract.json").read_bytes())
    for sample in samples:
        symbol = sample["symbol"]
        curves = {}
        for mode in ("hfq", "qfq"):
            paths = [root / "factors" / f"{symbol}-{mode}-{n}.js" for n in (1, 2)]
            parsed = []
            for path in paths:
                meta = json.loads(path.with_suffix(".js.meta.json").read_bytes())
                if (
                    meta.get("sha256") != sha(path.read_bytes())
                    or meta["url"]
                    != f"https://finance.sina.com.cn/realstock/company/{symbol}/{mode}.js"
                    or not meta.get("retrieved_at_utc")
                ):
                    raise ValueError("FACTOR_LINEAGE_INVALID")
                parsed.append(parse_factors(path.read_bytes(), symbol, mode))
            if parsed[0] != parsed[1]:
                failures.append(f"{symbol}:FACTOR_REPEATABILITY")
            curves[mode] = parsed[0]
        h, q = curves["hfq"], curves["qfq"]
        factors[symbol] = {m: [(d, str(v)) for d, v in c] for m, c in curves.items()}
        constant = h[-1][1]
        for d, value in h:
            if abs(value * factor_at(q, d) / constant - 1) > Decimal("1e-11"):
                failures.append(f"{symbol}:QFQ_BASE_RELATIONSHIP")
        if sample.get("control"):
            if any("2023-01-01" <= d <= "2024-07-31" for d, _ in h):
                failures.append(f"{symbol}:CONTROL_HAS_FACTOR_EVENT")
            controls = [json.loads((root / f"control-raw-{n}.json").read_bytes()) for n in (1, 2)]
            if not controls[0] or controls[0] != controls[1]:
                failures.append(f"{symbol}:CONTROL_RAW_REPEATABILITY")
            for row in controls[0]:
                d, raw = row["date"][:10], Decimal(str(row["close"]))
                if feature_close(raw, d, "2024-07-31", h) != raw:
                    failures.append(f"{symbol}:CONTROL_CHANGED")
            continue
        prices = {}
        for mode in ("raw", "qfq", "hfq"):
            files = [root / f"prices-{n}" / f"{symbol}-{mode}.json" for n in (1, 2)]
            rows = [json.loads(p.read_bytes())["rows"] for p in files]
            if not rows[0] or rows[0] != rows[1]:
                failures.append(f"{symbol}:PRICE_REPEATABILITY")
            prices[mode] = {r["date"][:10]: Decimal(str(r["close"])) for r in rows[0]}
            if len(prices[mode]) != len(rows[0]):
                failures.append(f"{symbol}:DUPLICATE_PRICE_DATE")
        if any(set(v) != set(prices["raw"]) for v in prices.values()):
            raise ValueError("PRICE_DATE_MISMATCH")
        for d, raw in sorted(prices["raw"].items()):
            expected = {"hfq": raw * factor_at(h, d), "qfq": raw / factor_at(q, d)}
            errors = {m: abs(expected[m] - prices[m][d]) for m in expected}
            if any(error > Decimal("0.00500001") for error in errors.values()):
                failures.append(f"{symbol}:{d}:PRICE_TRANSFORMATION")
            truncated = [(day, value) for day, value in h if day <= d]
            for historical_day, historical_raw in prices["raw"].items():
                if historical_day <= d and feature_close(
                    historical_raw, historical_day, d, h
                ) != feature_close(historical_raw, historical_day, d, truncated):
                    failures.append(f"{symbol}:FUTURE_EVENT_LEAKAGE")
            comparisons.append(
                dict(
                    symbol=symbol,
                    date=d,
                    raw=str(raw),
                    qfq=str(prices["qfq"][d]),
                    hfq=str(prices["hfq"][d]),
                )
            )
        ex = sample["ex_date"]
        prior = max(d for d in prices["raw"] if d < ex)
        p = prices["raw"][prior]
        implied = p * factor_at(h, prior) / factor_at(h, ex)
        expected_reference = (p - Decimal(sample["cash_per_share"])) / (
            1 + Decimal(sample["bonus_ratio"])
        )
        if ex not in dict(h) or abs(implied - expected_reference) > Decimal("0.00000001"):
            failures.append(f"{symbol}:CORPORATE_ACTION_ALIGNMENT")
        evidence = root / sample["disclosure_file"]
        if sha(evidence.read_bytes()) != sample["disclosure_sha256"]:
            raise ValueError("DISCLOSURE_CHECKSUM_MISMATCH")
    summary = dict(
        parser_version=VERSION,
        samples=len(samples),
        price_comparisons=len(comparisons),
        failures=failures,
        mathematical_sample_checks="PASS" if not failures else "FAIL",
        historical_revision_policy="UNKNOWN; frozen-vintage convention is required",
        ADJUSTMENT_AUTHORITY="PARTIAL",
        note="Sample math alone is insufficient; temporal and control review remain mandatory.",
    )
    save(root / "normalized-factors.json", factors)
    save(root / "price-comparisons.json", comparisons)
    summary["NORMALIZED_FACTOR_SHA256"] = sha(canonical(factors))
    save(root / "factor-audit.json", summary)
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    audit(parser.parse_args().root)
