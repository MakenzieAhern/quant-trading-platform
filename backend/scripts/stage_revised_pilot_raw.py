"""Validate and checkpoint changed/new raw inputs under the existing failover policy."""

import argparse
import json
from pathlib import Path

import pyarrow.parquet as pq

from scripts.audit_amount_impact import QUANTUM, interval_decisions
from scripts.audit_raw_failover import normalized
from scripts.materialize_akshare_partitions import normalized_bars
from scripts.reconcile_sse_cninfo import canonical, fetch, save, sha
from scripts.sina_adjustment_audit import factor_at, parse_factors
from scripts.stage_akshare_pilot import raw_url


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--v1", type=Path, required=True)
    args = parser.parse_args()
    staging = args.staging
    root = staging / "pilot-v2-raw"
    impact = json.loads((staging / "pilot-v2-master/master-impact.json").read_bytes())
    members = json.loads((staging / "pilot-v2-master/candidate-master.json").read_bytes())
    required = set(impact["new_active_during_pilot"]) | {
        r["security_id"] for r in impact["changed_lifecycles"]
    }
    sessions = json.loads(
        (staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json").read_bytes()
    )
    lineage = {
        r["security_id"]: json.loads(r["input_lineage_json"])
        for r in pq.read_table(args.v1 / "lineage.parquet").to_pylist()
    }
    completed, failures = {}, {}
    for member in members:
        sid, symbol = member["security_id"], member["symbol"]
        if sid not in required:
            continue
        try:
            if sid in lineage:
                inputs = lineage[sid]
                raw_path = staging / inputs["raw_path"]
                factor_path = staging / inputs["factor_path"]
                for kind, path in (("raw", raw_path), ("factor", factor_path)):
                    if sha(path.read_bytes()) != inputs[kind + "_sha256"]:
                        raise ValueError("PARENT_SOURCE_CHANGED")
                if inputs.get("provider") == "Tencent":
                    rows = normalized(
                        (staging / inputs["sources"][0]["path"]).read_bytes(), member, set(sessions)
                    )
                else:
                    rows = normalized_bars(raw_path.read_bytes(), member, set(sessions))
                provider = inputs.get("provider", "Eastmoney")
            else:
                probe = staging / "pilot-v2-star-repair-probe-v1"
                failure = json.loads((probe / f"Eastmoney-{symbol}.raw.meta.json").read_bytes())
                if (
                    failure["url"] != raw_url(member["exchange"], symbol)
                    or failure.get("error") != "RemoteDisconnected"
                ):
                    raise ValueError("PRIMARY_FAILURE_NOT_QUALIFIED")
                primary_raw = None
                attempts = [failure]
                for attempt in (1, 2):
                    name = f"primary/{symbol}-{attempt}.json"
                    meta_path = (root / name).with_suffix(".json.meta.json")
                    if meta_path.exists():
                        meta = json.loads(meta_path.read_bytes())
                        if meta["url"] != failure["url"]:
                            raise ValueError("PRIMARY_REQUEST_CHANGED")
                        if meta.get("error") == "RemoteDisconnected":
                            attempts.append(meta)
                            continue
                    try:
                        primary_raw = fetch(root, name, failure["url"])
                    except Exception:
                        meta = json.loads(meta_path.read_bytes())
                        attempts.append(meta)
                        if meta.get("error") != "RemoteDisconnected":
                            raise
                    else:
                        break
                if primary_raw is not None:
                    raise ValueError("PRIMARY_RECOVERED_REQUIRES_PRIMARY_PARTITION_PATH")
                if len(attempts) != 3:
                    raise ValueError("PRIMARY_BUDGET_NOT_EXHAUSTED")
                raw_path = probe / f"Tencent-{symbol}.raw"
                factor_path = probe / f"Sina-{symbol}.raw"
                for path in (raw_path, factor_path):
                    meta = json.loads(path.with_suffix(".raw.meta.json").read_bytes())
                    if meta.get("error") or sha(path.read_bytes()) != meta["sha256"]:
                        raise ValueError("CACHED_PROBE_CHANGED")
                rows = normalized(raw_path.read_bytes(), member, set(sessions))
                provider = "Tencent"
                inputs = dict(
                    provider=provider,
                    raw_path=str(raw_path.relative_to(staging)),
                    raw_sha256=sha(raw_path.read_bytes()),
                    factor_path=str(factor_path.relative_to(staging)),
                    factor_sha256=sha(factor_path.read_bytes()),
                    primary_attempts=attempts,
                )
            curve = parse_factors(
                factor_path.read_bytes(),
                ("sh" if member["exchange"] == "SSE" else "sz") + symbol,
                "hfq",
            )
            first_day = str(rows[0]["trading_date"])
            factor_at(curve, first_day)
            if provider == "Tencent":
                decisions = interval_decisions(rows, QUANTUM)
                scheduled = {
                    d for i, d in enumerate(sessions, 1) if i >= 253 and (i - 253) % 20 == 0
                }
                if any(not r["stable"] and r["day"] in scheduled for r in decisions):
                    raise ValueError("AMBIGUOUS_AMOUNT_DECISION")
            completed[sid] = dict(
                member=member,
                inputs=inputs,
                provider=provider,
                raw_rows=len(rows),
                normalized_rows_sha256=sha(canonical(rows)),
                factor_rows=len(curve),
                lifecycle_revalidated=True,
                partition_reuse=False,
            )
        except Exception as exc:
            failures[sid] = dict(error_type=type(exc).__name__, reason=str(exc))
        save(
            root / "checkpoint.json", dict(completed=completed, failures=failures, published=False)
        )
        print(sid, "VALIDATED" if sid in completed else failures[sid], flush=True)
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
