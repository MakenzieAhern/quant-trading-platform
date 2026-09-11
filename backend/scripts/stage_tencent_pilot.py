"""Bounded transport-only failover, preserving the completed primary checkpoint."""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from itertools import batched
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from scripts.audit_amount_impact import QUANTUM, STRATEGY_SHA, interval_decisions, status_lookup
from scripts.audit_raw_failover import merged, normalized
from scripts.probe_raw_failover import tencent_url
from scripts.reconcile_sse_cninfo import canonical, fetch, save, sha
from scripts.sina_adjustment_audit import factor_at, parse_factors
from scripts.stage_akshare_pilot import DATASET_ID, pilot_members


def cached_request(candidates: list[Path], target: Path, url: str) -> tuple[Path, bytes, dict]:
    for path in [*candidates, target]:
        metadata = path.with_suffix(path.suffix + ".meta.json")
        if not metadata.exists():
            continue
        meta = json.loads(metadata.read_bytes())
        if meta["url"] != url:
            raise ValueError("CACHED_REQUEST_IDENTITY_CHANGED")
        if meta.get("error"):
            if path == target:
                failure_path = path.with_suffix(path.suffix + ".failure.json")
                failure = json.loads(failure_path.read_bytes()) if failure_path.exists() else {}
                if failure.get("http_status") is not None:
                    raise HTTPError(
                        url, failure["http_status"], "persisted failed slot", None, None
                    )
                if failure.get("access_denied"):
                    raise RuntimeError("ACCESS_DENIED_STOP")
                if meta["error"] in {
                    "TimeoutError",
                    "RemoteDisconnected",
                    "URLError",
                    "ConnectionResetError",
                    "ConnectionError",
                }:
                    raise ConnectionError("PERSISTED_TRANSPORT_FAILURE:" + meta["error"])
                raise RuntimeError("PERSISTED_ATTEMPT_ALREADY_FAILED")
            continue
        raw = path.read_bytes()
        if sha(raw) != meta["sha256"]:
            raise ValueError("CACHED_SOURCE_HASH_CHANGED")
        return path, raw, meta
    try:
        raw = fetch(target.parent, target.name, url)
    except Exception as exc:
        save(
            target.with_suffix(target.suffix + ".failure.json"),
            dict(
                error_type=type(exc).__name__,
                reason=str(exc),
                http_status=getattr(exc, "code", None),
                access_denied="ACCESS_DENIED" in str(exc),
            ),
        )
        raise
    return target, raw, json.loads(target.with_suffix(target.suffix + ".meta.json").read_bytes())


def recover(
    staging: Path,
    member: dict,
    failure: dict,
    round_no: int,
    sessions: list[str],
    get_status,
    policy_sha: str,
) -> dict:
    root = staging / "pilot-akshare-20260911"
    sid, symbol = member["security_id"], member["symbol"]
    record = dict(
        security_id=sid,
        round=round_no,
        provider="Tencent",
        recorded_at_utc=datetime.now(UTC).isoformat(),
    )
    url = ""
    try:
        if failure["error_type"] != "RemoteDisconnected" or failure["round"] != 2:
            raise ValueError("PRIMARY_FAILURE_NOT_QUALIFIED_OR_NOT_EXHAUSTED")
        if member["board"] not in {"SSE_MAIN", "SSE_STAR", "SZSE_MAIN", "SZSE_CHINEXT"}:
            raise ValueError("UNACCEPTED_BOARD_NORMALIZATION")
        parts, sources = [], []
        for year in (2023, 2024):
            name = f"{symbol}-{year}.json"
            candidates = [
                staging / "raw-failover-v1" / folder / f"{symbol}-{year}-1.json"
                for folder in ("tencent-candidate", "impact-candidate")
            ]
            candidates += [root / "secondary-attempts" / str(n) / name for n in range(2)]
            url = tencent_url(member["exchange"], symbol, year)
            path, raw, meta = cached_request(
                candidates, root / "secondary-attempts" / str(round_no) / name, url
            )
            parts.append(normalized(raw, member, set(sessions)))
            code = ("sh" if member["exchange"] == "SSE" else "sz") + symbol
            upstream = json.loads(raw.decode().split("=", 1)[1], parse_float=str)["data"][code][
                "day"
            ]
            for row in upstream:
                if row[0] in set(sessions) and (
                    not isinstance(row[8], str) or Decimal(row[8]).as_tuple().exponent != -2
                ):
                    raise ValueError("SOURCE_PRECISION_CHANGED")
            sources.append(
                dict(
                    path=path.relative_to(staging).as_posix(),
                    sha256=sha(raw),
                    retrieval_timestamp_utc=meta["retrieved_at_utc"],
                    request_url=url,
                    request_parameters=parse_qs(urlsplit(url).query),
                )
            )
        rows = merged(parts)
        if rows != merged(list(reversed(parts))):
            raise ValueError("INPUT_ORDER_FAILED")
        scheduled = {d for i, d in enumerate(sessions, 1) if i >= 253 and (i - 253) % 20 == 0}
        decisions = interval_decisions(rows, QUANTUM)
        ambiguous = [
            r
            for r in decisions
            if not r["stable"] and r["day"] in scheduled and get_status(sid, r["day"]) == "NORMAL"
        ]
        if ambiguous:
            record.update(ambiguous_amount_decisions=ambiguous)
            raise ValueError("AMBIGUOUS_AMOUNT_DECISION")
        normalized_path = root / "secondary-normalized" / f"{symbol}.json"
        content = dict(
            format="TENCENT_RAW_V1",
            rows=rows,
            sources=sources,
            policy_sha256=policy_sha,
            amount_decisions_sha256=sha(canonical(decisions)),
            failover_reason="CONNECTION_CLOSED_BEFORE_HTTP",
            primary_failure_sha256=sha(canonical(failure)),
        )
        if normalized_path.exists() and normalized_path.read_bytes() != canonical(content):
            raise ValueError("NORMALIZED_SOURCE_VINTAGE_CHANGED")
        save(normalized_path, content)
        code = ("sh" if member["exchange"] == "SSE" else "sz") + symbol
        url = f"https://finance.sina.com.cn/realstock/company/{code}/hfq.js"
        name = f"{code}-hfq.js"
        candidates = [
            staging / "sina-acceptance-20260910/factors" / f"{code}-hfq-1.js",
            root / "sources" / name,
        ]
        candidates += [root / "recovery-attempts" / str(n) / name for n in range(3)]
        candidates += [root / "secondary-attempts" / str(n) / name for n in range(2)]
        factor_path, factor_raw, _ = cached_request(
            candidates, root / "secondary-attempts" / str(round_no) / name, url
        )
        factor_at(parse_factors(factor_raw, code, "hfq"), rows[0]["trading_date"])
        record.update(
            status="PRIMARY_FAILED_SECONDARY_RECOVERED",
            raw_path=normalized_path.relative_to(staging).as_posix(),
            raw_sha256=sha(canonical(content)),
            raw_rows=len(rows),
            factor_path=factor_path.relative_to(staging).as_posix(),
            factor_sha256=sha(factor_raw),
            policy_sha256=policy_sha,
            normalized_logical_sha256=sha(canonical(rows)),
            provider_interface="AKShare 1.18.94 stock_zh_a_hist_tx raw request path",
            underlying_source="Tencent",
            sources=sources,
            date_coverage=[rows[0]["trading_date"], rows[-1]["trading_date"]],
            failover_reason="CONNECTION_CLOSED_BEFORE_HTTP",
        )
    except Exception as exc:
        code = getattr(exc, "code", None)
        denied = code in {403, 429} or "ACCESS_DENIED" in str(exc)
        retryable = isinstance(exc, (ConnectionError, TimeoutError, URLError)) and (
            not isinstance(exc, HTTPError) or code in {500, 502, 503, 504}
        )
        record.update(
            status="PRIMARY_FAILED_SECONDARY_FAILED",
            error_type=type(exc).__name__,
            error=str(exc),
            source_url=url,
            retryable=retryable and not denied,
            stop=denied or str(exc) == "AMBIGUOUS_AMOUNT_DECISION",
        )
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument(
        "--limit", type=int, default=None, help="Bounded smoke batch; resume keeps slots"
    )
    args = parser.parse_args()
    state = json.loads((args.repository / ".research/project_state.json").read_bytes())
    policy_path = args.repository / "docs/research/CN_A_RAW_OHLCV_FAILOVER_V1.json"
    policy_sha = sha(policy_path.read_bytes())
    if (
        state["status"] != "RUNNING"
        or state["current_stage"] != "R2"
        or state["secondary_acceptance"] != "PASS_FOR_PILOT"
        or state["raw_failover_policy_sha256"] != policy_sha
        or sha((args.repository / "backend/app/research/strategy.py").read_bytes()) != STRATEGY_SHA
    ):
        raise ValueError("FAILOVER_OR_CONSUMER_NOT_AUTHORIZED")
    root = args.staging / "pilot-akshare-20260911"
    primary_path = root / "recovery-checkpoint.json"
    if sha(primary_path.read_bytes()) != state["r2_checkpoint_sha256"]:
        raise ValueError("PRIMARY_CHECKPOINT_CHANGED")
    primary = json.loads(primary_path.read_bytes())
    checkpoint_path = root / "secondary-checkpoint.json"
    checkpoint = json.loads(checkpoint_path.read_bytes()) if checkpoint_path.exists() else {}
    if checkpoint.get("stop"):
        raise ValueError("PERSISTED_SECONDARY_STOP_REQUIRES_REVIEW")
    completed, failures = checkpoint.get("completed", {}), checkpoint.get("failures", {})
    history = checkpoint.get("history", [])
    for result in completed.values():
        if result["policy_sha256"] != policy_sha:
            raise ValueError("COMPLETED_POLICY_CHANGED")
        for kind in ("raw", "factor"):
            if (
                sha((args.staging / result[kind + "_path"]).read_bytes())
                != result[kind + "_sha256"]
            ):
                raise ValueError("COMPLETED_BYTES_CHANGED")
    sessions = json.loads(
        (
            args.staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json"
        ).read_bytes()
    )
    get_status = status_lookup(args.staging)
    members = [m for m in pilot_members(args.staging) if m["security_id"] in primary["pending"]]
    stopped, processed = False, 0
    for round_no in range(2):
        done = {(r["security_id"], r["round"]) for r in history}
        remaining = [
            m
            for m in members
            if m["security_id"] not in completed
            and (m["security_id"], round_no) not in done
            and (round_no == 0 or failures.get(m["security_id"], {}).get("retryable"))
        ]
        if args.limit is not None:
            remaining = remaining[: max(0, args.limit - processed)]
        if not remaining:
            continue
        if round_no:
            time.sleep(60)
        with ThreadPoolExecutor(max_workers=2) as pool:
            for batch in batched(remaining, 2):
                results = list(
                    pool.map(
                        lambda m, n=round_no: recover(
                            args.staging,
                            m,
                            primary["pending"][m["security_id"]],
                            n,
                            sessions,
                            get_status,
                            policy_sha,
                        ),
                        batch,
                    )
                )
                for result in results:
                    sid = result["security_id"]
                    history.append(result)
                    if result["status"] == "PRIMARY_FAILED_SECONDARY_RECOVERED":
                        completed[sid] = result
                        failures.pop(sid, None)
                    else:
                        failures[sid] = result
                        stopped = stopped or result["stop"]
                record = dict(
                    dataset_id=DATASET_ID,
                    policy_sha256=policy_sha,
                    primary_checkpoint_sha256=sha(primary_path.read_bytes()),
                    primary_success=len(primary["completed"]),
                    secondary_success=len(completed),
                    unresolved_required_data=len(members) - len(completed),
                    completed=completed,
                    failures=failures,
                    history=history,
                    stop=stopped,
                    published=False,
                )
                save(checkpoint_path, record)
                save(
                    root / "secondary-failure-manifest.json",
                    dict(
                        failures=failures,
                        not_recovered=sorted(
                            m["security_id"] for m in members if m["security_id"] not in completed
                        ),
                        unresolved_required_data=len(members) - len(completed),
                        published=False,
                    ),
                )
                processed += len(batch)
                print(
                    f"round={round_no} secondary={len(completed)} attempted_failed={len(failures)} "
                    f"unresolved={len(members) - len(completed)} stop={stopped}",
                    flush=True,
                )
                if stopped:
                    break
                time.sleep(2)
        if stopped:
            break
    if stopped:
        raise SystemExit("SECONDARY_STOP_REQUIRES_REVIEW")
    if len(completed) != len(members):
        print("PARTIAL_INPUTS; FINAL_PUBLICATION_PROHIBITED", flush=True)


if __name__ == "__main__":
    main()
