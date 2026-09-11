"""Resume accepted-route Pilot inputs; fail closed before incomplete publication."""

import argparse
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from itertools import batched
from pathlib import Path

from scripts.project_controller import next_stage
from scripts.reconcile_sse_cninfo import fetch, save, sha
from scripts.sina_adjustment_audit import factor_at, parse_factors

START, END = "2023-01-01", "2024-07-31"
DATASET_ID = "cn-a-pilot-akshare-20230101-20240731-v1"


def pilot_members(staging: Path) -> list[dict[str, str]]:
    root = staging / "security-master-pilot"
    manifest = json.loads((root / "security-master-input.json").read_bytes())
    if (
        not manifest.get("complete")
        or manifest["coverage_start"] > START
        or manifest["coverage_end"] < END
    ):
        raise ValueError("INCOMPLETE_ACCEPTED_MASTER")
    rows = []
    for source in manifest["sources"]:
        path = root / source["filename"]
        if sha(path.read_bytes()) != source["sha256"]:
            raise ValueError("ACCEPTED_MASTER_CHECKSUM_CHANGED")
        with path.open(encoding="utf-8", newline="") as stream:
            rows.extend(
                row
                for row in csv.DictReader(stream)
                if row["listing_date"] <= END
                and (not row["delisting_date"] or row["delisting_date"] >= START)
            )
    if len({row["security_id"] for row in rows}) != len(rows):
        raise ValueError("DUPLICATE_MASTER_IDENTITY")
    # Test retention risks first; selection is fixed, never performance dependent.
    return sorted(rows, key=lambda row: (not bool(row["delisting_date"]), row["security_id"]))


def raw_url(exchange: str, symbol: str) -> str:
    if exchange not in {"SSE", "SZSE"} or len(symbol) != 6 or not symbol.isdecimal():
        raise ValueError("INVALID_REQUEST_IDENTITY")
    return (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
        "fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116"
        "&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=0"
        f"&secid={1 if exchange == 'SSE' else 0}.{symbol}&beg=20230101&end=20240731"
    )


def snapshot(root: Path, name: str, url: str, round_no: int) -> tuple[Path, bytes]:
    """Each request attempt is immutable; failed requests never block other symbols."""
    candidates = [root / "sources" / name, root / "recovery-controls" / name]
    candidates += [root / "recovery-attempts" / str(n) / name for n in range(3)]
    for path in candidates:
        meta_path = path.with_suffix(path.suffix + ".meta.json")
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_bytes())
        if meta.get("url") != url:
            raise ValueError("SNAPSHOT_REQUEST_IDENTITY_MISMATCH")
        if not meta.get("error") and path.exists():
            raw = path.read_bytes()
            if sha(raw) != meta["sha256"]:
                raise ValueError("SNAPSHOT_CHECKSUM_MISMATCH")
            try:
                if name.endswith(".json"):
                    if not json.loads(raw).get("data", {}).get("klines"):
                        continue
                else:
                    parse_factors(raw, name.split("-")[0], "hfq")
            except (ValueError, TypeError, AttributeError, KeyError):
                continue
            return path, raw
    path = root / "recovery-attempts" / str(round_no) / name
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    if meta_path.exists():
        raise RuntimeError("PERSISTED_ATTEMPT_ALREADY_FAILED")
    if (
        round_no == 0
        and (root / "sources" / name).with_suffix(Path(name).suffix + ".meta.json").exists()
    ):
        raise RuntimeError("PRIOR_FAILURE_PENDING_FINAL_RETRY")
    return path, fetch(path.parent, path.name, url)


def stage_one(staging: Path, row: dict[str, str], round_no: int) -> dict:
    root = staging / "pilot-akshare-20260911"
    sid, symbol, exchange = row["security_id"], row["symbol"], row["exchange"]
    request_url = raw_url(exchange, symbol)
    try:
        accepted_raw = staging / "raw-route-20260910" / f"{symbol}-1.json"
        if accepted_raw.exists():
            manifest = json.loads((accepted_raw.parent / "acceptance-manifest.json").read_bytes())
            expected = next(
                item["sha256"] for item in manifest["files"] if item["path"] == accepted_raw.name
            )
            if sha(accepted_raw.read_bytes()) != expected:
                raise ValueError("ACCEPTED_RAW_CHECKSUM_CHANGED")
            raw_path = accepted_raw
            raw = raw_path.read_bytes()
        else:
            raw_path, raw = snapshot(root, f"{symbol}.json", request_url, round_no)
        payload = json.loads(raw).get("data")
        if not payload or not payload.get("klines"):
            raise ValueError("RAW_HISTORY_UNAVAILABLE")
        if payload.get("code") != symbol:
            raise ValueError("RAW_SECURITY_IDENTITY_MISMATCH")
        provider_symbol = ("sh" if exchange == "SSE" else "sz") + symbol
        request_url = f"https://finance.sina.com.cn/realstock/company/{provider_symbol}/hfq.js"
        accepted_factor = (
            staging / "sina-acceptance-20260910/factors" / f"{provider_symbol}-hfq-1.js"
        )
        if accepted_factor.exists():
            meta = json.loads(accepted_factor.with_suffix(".js.meta.json").read_bytes())
            factor_raw = accepted_factor.read_bytes()
            if sha(factor_raw) != meta["sha256"] or meta["url"] != request_url:
                raise ValueError("ACCEPTED_FACTOR_CHECKSUM_CHANGED")
            factor_path = accepted_factor
        else:
            factor_path, factor_raw = snapshot(
                root, f"{provider_symbol}-hfq.js", request_url, round_no
            )
        curve = parse_factors(factor_raw, provider_symbol, "hfq")
        first = min(line.split(",")[0] for line in payload["klines"])
        factor_at(curve, first)
        return dict(
            security_id=sid,
            status="RECOVERED_PRIMARY",
            raw_path=raw_path.relative_to(staging).as_posix(),
            raw_sha256=sha(raw),
            factor_path=factor_path.relative_to(staging).as_posix(),
            factor_sha256=sha(factor_raw),
            raw_rows=len(payload["klines"]),
        )
    except Exception as exc:
        return dict(
            security_id=sid,
            status="PENDING_RETRY" if round_no < 2 else "UNRESOLVED_REQUIRED_DATA",
            effective_from=max(START, row["listing_date"]),
            effective_to=min(END, row["delisting_date"] or END),
            error_type=type(exc).__name__,
            error=str(exc),
            source_url=request_url,
            round=round_no,
            recorded_at_utc=datetime.now(UTC).isoformat(),
            provider_stop=getattr(exc, "code", None) in {403, 429} or "ACCESS_DENIED" in str(exc),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    args = parser.parse_args()
    state = json.loads((args.repository / ".research/project_state.json").read_bytes())
    lock = json.loads((args.repository / ".research/oos_lock.json").read_bytes())
    if next_stage(state, lock) != "R2" or state["current_stage"] != "R2":
        raise ValueError("CONTROLLER_DOES_NOT_AUTHORIZE_R2")
    root = args.staging / "pilot-akshare-20260911"
    members = pilot_members(args.staging)
    checkpoint_path = root / "recovery-checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_bytes()) if checkpoint_path.exists() else {}
    completed = checkpoint.get("completed", {})
    history = checkpoint.get("failure_history", [])
    # Validate cached completed input bytes rather than trusting counters after restart.
    for result in completed.values():
        for kind in ("raw", "factor"):
            if (
                sha((args.staging / result[kind + "_path"]).read_bytes())
                != result[kind + "_sha256"]
            ):
                raise ValueError("CHECKPOINT_INPUT_CHANGED")
    stopped = False
    pending = checkpoint.get("pending", {})
    for round_no, delay in enumerate((0, 30, 60)):
        processed_failures = {(item["security_id"], item["round"]) for item in history}
        remaining = [
            row
            for row in members
            if row["security_id"] not in completed
            and (row["security_id"], round_no) not in processed_failures
        ]
        if not remaining:
            continue
        if delay:
            time.sleep(delay)
        failed_batches = 0
        with ThreadPoolExecutor(max_workers=2) as pool:
            for batch in batched(remaining, 2):
                results = list(
                    pool.map(lambda row, n=round_no: stage_one(args.staging, row, n), batch)
                )
                for result in results:
                    sid = result["security_id"]
                    if result["status"] == "RECOVERED_PRIMARY":
                        completed[sid] = result
                        pending.pop(sid, None)
                    else:
                        history.append(result)
                        pending[sid] = result
                        stopped = stopped or result.get("provider_stop", False)
                record = dict(
                    dataset_id=DATASET_ID,
                    total=len(members),
                    completed=completed,
                    pending=pending,
                    failure_history=history,
                    round=round_no,
                    published=False,
                    retry_policy=dict(
                        rounds=3,
                        backoff_seconds=[0, 30, 60],
                        workers=2,
                        jitter=False,
                        inter_batch_seconds=2,
                        failed_batch_cooldown_seconds=20,
                        cooldown_after_consecutive_failed_batches=10,
                    ),
                )
                save(checkpoint_path, record)
                save(
                    root / "recovery-failure-manifest.json",
                    dict(
                        dataset_id=DATASET_ID,
                        pending=pending,
                        failure_history=history,
                        published=False,
                    ),
                )
                print(
                    f"round={round_no} completed={len(completed)}/{len(members)} "
                    f"pending={len(pending)}",
                    flush=True,
                )
                if stopped:
                    break
                failed_batches = (
                    failed_batches + 1
                    if all(r["status"] != "RECOVERED_PRIMARY" for r in results)
                    else 0
                )
                # Bounded global cooldown, not a retry blocking the queue on one security.
                time.sleep(20 if failed_batches and failed_batches % 10 == 0 else 2)
        if stopped:
            break
    if len(completed) == len(members):
        save(
            root / "input-manifest.json",
            dict(
                dataset_id=DATASET_ID,
                inputs=[completed[sid] for sid in sorted(completed)],
                published=False,
            ),
        )
    else:
        print("UNRESOLVED_REQUIRED_DATA; FINAL_PUBLICATION_PROHIBITED", flush=True)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
