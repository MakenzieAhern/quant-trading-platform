"""Recompute accepted overlap comparisons from source bytes for the revised audit."""

import argparse
import json
from decimal import Decimal
from pathlib import Path

from scripts.audit_amount_impact import EXTRA_SAMPLE, QUANTUM
from scripts.audit_raw_failover import merged, normalized
from scripts.audit_tencent_amount import comparison
from scripts.probe_raw_failover import TENCENT_SAMPLE, tencent_url
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import END, START


def audit(staging):
    context = json.loads((staging / "pilot-v2-build/revision-context.json").read_bytes())
    members = {r["symbol"]: r for r in context["members"]}
    root = staging / "raw-failover-v1"
    sessions = json.loads(
        (staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json").read_bytes()
    )
    primary = json.loads(
        (staging / "pilot-akshare-20260911/recovery-checkpoint.json").read_bytes()
    )["completed"]
    comparisons = []
    for symbol in (*TENCENT_SAMPLE, *EXTRA_SAMPLE):
        if symbol not in members:
            continue
        member = members[symbol]
        sid = member["security_id"]
        folder = "tencent-candidate" if symbol in TENCENT_SAMPLE else "impact-candidate"
        repeats, upstream = [], {}
        for repeat in (1, 2):
            parts = []
            for year in (2023, 2024):
                path = root / folder / f"{symbol}-{year}-{repeat}.json"
                raw = path.read_bytes()
                meta = json.loads(path.with_suffix(".json.meta.json").read_bytes())
                if sha(raw) != meta["sha256"] or meta["url"] != tencent_url(
                    member["exchange"], symbol, year
                ):
                    raise ValueError("CROSS_SOURCE_SNAPSHOT_CHANGED")
                parts.append(normalized(raw, member, set(sessions)))
                code = ("sh" if member["exchange"] == "SSE" else "sz") + symbol
                for row in json.loads(raw.decode().split("=", 1)[1], parse_float=str)["data"][code][
                    "day"
                ]:
                    if START <= row[0] <= END:
                        if not isinstance(row[8], str) or Decimal(row[8]).as_tuple().exponent != -2:
                            raise ValueError("AMOUNT_PRECISION_CHANGED")
                        upstream[row[0]] = row[8]
            if merged(parts) != merged(parts[::-1]):
                raise ValueError("CROSS_SOURCE_ORDER_DEPENDENCE")
            repeats.append(merged(parts))
        if repeats[0] != repeats[1]:
            raise ValueError("CROSS_SOURCE_REPEAT_MISMATCH")
        if sid not in primary:
            continue
        receipt = primary[sid]
        raw = (staging / receipt["raw_path"]).read_bytes()
        if sha(raw) != receipt["raw_sha256"]:
            raise ValueError("PRIMARY_SOURCE_CHANGED")
        original = {r.split(",")[0]: r.split(",") for r in json.loads(raw)["data"]["klines"]}
        if set(original) != set(upstream):
            raise ValueError("CROSS_SOURCE_DATE_DIFFERENCE")
        for row in repeats[0]:
            day = row["trading_date"]
            p = original[day]
            if any(
                Decimal(p[i]) != Decimal(row[field])
                for i, field in enumerate(("raw_open", "raw_close", "raw_high", "raw_low"), 1)
            ):
                raise ValueError("CROSS_SOURCE_OHLC_DIFFERENCE")
            width = Decimal(50) if member["board"] == "SSE_STAR" else Decimal(0)
            if abs(Decimal(p[5]) * 100 - Decimal(row["volume"])) > width:
                raise ValueError("CROSS_SOURCE_VOLUME_DIFFERENCE")
            item = dict(security_id=sid, day=day, **comparison(p[6], upstream[day], "10000"))
            if Decimal(item["absolute_difference"]) > QUANTUM:
                raise ValueError("CROSS_SOURCE_AMOUNT_OUTLIER")
            comparisons.append(item)
    if not comparisons or sha(canonical(comparisons)) != context["amount"]["parity_sha256"]:
        raise ValueError("CROSS_SOURCE_REPLAY_NOT_REPRODUCED")
    report = dict(
        status="PASS",
        rows=len(comparisons),
        parity_sha256=sha(canonical(comparisons)),
        recomputed_from_raw_sources=True,
        old_verdict_reused=False,
    )
    save(staging / "pilot-v2-build/cross-source-replay.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    print(json.dumps(audit(parser.parse_args().staging)))
