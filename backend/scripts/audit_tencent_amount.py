"""Offline amount evidence review; never promotes a provider or runs a strategy."""

import argparse
import json
from collections import Counter
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from pathlib import Path

from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import END, START


def comparison(primary: str, secondary: str, multiplier: str) -> dict:
    a, b = Decimal(primary), Decimal(secondary) * Decimal(multiplier)
    if not a.is_finite() or not b.is_finite() or min(a, b) < 0:
        raise ValueError("INVALID_AMOUNT")
    delta = abs(a - b)
    return dict(
        raw_primary_amount=primary,
        raw_secondary_amount=secondary,
        candidate_unit_conversion=multiplier,
        normalized_secondary_amount=str(b),
        absolute_difference=str(delta),
        relative_difference=str(delta / a) if a else ("0" if not delta else None),
        primary_zero=a == 0,
    )


def audit(staging: Path) -> dict:
    root = staging / "raw-failover-v1"
    previous = json.loads((root / "candidate-audit.json").read_bytes())
    for source in previous["sources"]:
        if sha((root / source["path"]).read_bytes()) != source["sha256"]:
            raise ValueError("CANDIDATE_SOURCE_HASH_CHANGED")
        meta = root / (source["path"] + ".meta.json")
        if sha(meta.read_bytes()) != source["metadata_sha256"]:
            raise ValueError("CANDIDATE_METADATA_CHANGED")
    checkpoint_path = staging / "pilot-akshare-20260911/recovery-checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_bytes())
    observations, sample, precisions, types = [], [], Counter(), Counter()
    for member in previous["securities"]:
        identity = member["security_id"]
        if identity not in checkpoint["completed"]:
            continue
        receipt = checkpoint["completed"][identity]
        raw = (staging / receipt["raw_path"]).read_bytes()
        if sha(raw) != receipt["raw_sha256"]:
            raise ValueError("PRIMARY_SOURCE_HASH_CHANGED")
        primary = {r.split(",")[0]: r.split(",") for r in json.loads(raw)["data"]["klines"]}
        symbol = member["member"]["symbol"]
        code = ("sh" if member["member"]["exchange"] == "SSE" else "sz") + symbol
        secondary = {}
        for year in (2023, 2024):
            path = root / "tencent-candidate" / f"{symbol}-{year}-1.json"
            data = json.loads(path.read_text().split("=", 1)[1], parse_float=str)
            for row in data["data"][code]["day"]:
                if START <= row[0] <= END:
                    if row[0] in secondary and secondary[row[0]] != row:
                        raise ValueError("CONFLICTING_YEAR_OVERLAP")
                    secondary[row[0]] = row
        if primary.keys() != secondary.keys():
            raise ValueError("DATE_PARITY_FAILED")
        for day in sorted(primary):
            a, b = primary[day][6], secondary[day][8]
            types[type(b).__name__] += 1
            if b is None or b == "":
                raise ValueError("NULL_AMOUNT_OBSERVED")
            precisions[str(max(0, -Decimal(b).as_tuple().exponent))] += 1
            observations.append(dict(security_id=identity, day=day, **comparison(a, b, "10000")))
        sample.append(
            dict(
                security_id=identity,
                board=member["member"]["board"],
                rows=len(primary),
                raw_close_min=str(min(Decimal(r[2]) for r in primary.values())),
                raw_close_max=str(max(Decimal(r[2]) for r in primary.values())),
                volume_shares_min=str(min(Decimal(r[5]) * 100 for r in primary.values())),
                volume_shares_max=str(max(Decimal(r[5]) * 100 for r in primary.values())),
                primary_sha256=sha(raw),
            )
        )
    if not observations:
        raise ValueError("EMPTY_OVERLAP")
    relationships = {}
    for multiplier in ("1", "100", "10000"):
        rows = [
            comparison(r["raw_primary_amount"], r["raw_secondary_amount"], multiplier)
            for r in observations
        ]
        relationships[multiplier] = dict(
            exact_rows=sum(Decimal(r["absolute_difference"]) == 0 for r in rows),
            max_absolute_difference=str(max(Decimal(r["absolute_difference"]) for r in rows)),
        )
    rounding = {}
    for mode in (ROUND_HALF_UP, ROUND_DOWN):
        rounding[mode] = sum(
            (Decimal(r["raw_primary_amount"]) / 10000).quantize(Decimal("0.01"), rounding=mode)
            == Decimal(r["raw_secondary_amount"])
            for r in observations
        )
    save(root / "amount-observations.json", observations)
    report = dict(
        parser_version="tencent-amount-audit-v1",
        amount_requirement="REQUIRED",
        classification="INSUFFICIENT_EVIDENCE",
        secondary_acceptance="FAIL",
        candidate_audit_sha256=sha((root / "candidate-audit.json").read_bytes()),
        checkpoint_sha256=sha(checkpoint_path.read_bytes()),
        observations_sha256=sha(canonical(observations)),
        sample=sample,
        sample_rows=len(observations),
        raw_types=dict(types),
        decimal_places=dict(precisions),
        null_rows=0,
        null_semantics="UNOBSERVED; SDK coerces invalid values to NaN",
        unit="10000 CNY per pinned SDK field-8 mapping; not inferred from magnitude",
        rounding_semantics="UNDOCUMENTED; candidate fits do not prove provider semantics",
        candidate_scalings=relationships,
        direct_rounding_exact_rows=rounding,
        max_absolute_difference=str(max(Decimal(r["absolute_difference"]) for r in observations)),
        max_relative_difference=str(
            max(
                Decimal(r["relative_difference"])
                for r in observations
                if r["relative_difference"] is not None
            )
        ),
        undefined_relative_rows=sum(r["relative_difference"] is None for r in observations),
        greater_than_50_cny=[r for r in observations if Decimal(r["absolute_difference"]) > 50],
        limitation="Observed maxima are not a documented bound for unobserved securities.",
    )
    save(root / "amount-audit.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    print(json.dumps(audit(parser.parse_args().staging)))
