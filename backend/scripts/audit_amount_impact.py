"""Amount-only interval audit. No factors, rankings, portfolios, orders or returns."""

import argparse
import base64
import csv
import json
from collections import defaultdict, deque
from decimal import ROUND_CEILING, Decimal
from pathlib import Path

from scripts.audit_raw_failover import merged, normalized
from scripts.audit_tencent_amount import comparison
from scripts.probe_raw_failover import TENCENT_SAMPLE, tencent_url
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import END, START, pilot_members

VERSION = "pilot-amount-decision-impact-v1"
QUANTUM = Decimal(100)
THRESHOLD = Decimal(10000000)
EXTRA_SAMPLE = ("600666", "688211")  # Nearest ST and normal primary-cache windows.
SDK_SHA = "aa9199665d356ba3a054297004e349d3926fa83026abfd2d50c4b7f832226d84"
STRATEGY_SHA = "14bd3d21a48560faa28527fa061883a4ceb69bcf7a6332176ac06467152dbde0"


def interval_decisions(rows: list[dict], width: Decimal) -> list[dict]:
    """Union of floor/ceiling/nearest quantization cells; no favorable rounding mode."""
    if width < 0 or not width.is_finite():
        raise ValueError("INVALID_INTERVAL_WIDTH")
    history: deque[Decimal] = deque(maxlen=20)
    result = []
    previous = ""
    for row in rows:
        day, amount = row["trading_date"], Decimal(row["amount"])
        if day <= previous or not amount.is_finite() or amount < 0:
            raise ValueError("INVALID_AMOUNT_HISTORY")
        previous = day
        history.append(amount)
        enough = len(history) == 20
        lower = sum((max(Decimal(0), a - width) for a in history), Decimal(0)) / len(history)
        upper = sum(history, Decimal(0)) / len(history) + width
        low_decision, high_decision = enough and lower >= THRESHOLD, enough and upper >= THRESHOLD
        result.append(
            dict(
                day=day,
                observations=len(history),
                lower=str(lower),
                upper=str(upper),
                decision_with_lower_bound=low_decision,
                decision_with_upper_bound=high_decision,
                stable=low_decision == high_decision,
                distance_to_threshold=str(abs(sum(history, Decimal(0)) / len(history) - THRESHOLD)),
            )
        )
    return result


def distribution(values: list[Decimal]) -> dict:
    values = sorted(values)
    n = len(values)
    if not n:
        raise ValueError("EMPTY_DISTRIBUTION")
    return dict(
        median=str((values[(n - 1) // 2] + values[n // 2]) / 2),
        p95=str(
            values[
                int((Decimal(n) * Decimal("0.95")).to_integral_value(rounding=ROUND_CEILING)) - 1
            ]
        ),
        p99=str(
            values[
                int((Decimal(n) * Decimal("0.99")).to_integral_value(rounding=ROUND_CEILING)) - 1
            ]
        ),
        maximum=str(values[-1]),
        method="median midpoint; nearest-rank p95/p99",
    )


def status_lookup(staging: Path):
    intervals = defaultdict(list)
    path = staging / "sse-st-pilot/pilot-scope-20260910/coverage-intervals.json"
    for r in json.loads(path.read_bytes()):
        intervals[r["security_id"]].append((r["effective_from"], r["effective_to"], r["status"]))
    path = staging / "szse-st-recovery-20260910/audit/security-timelines.json"
    for r in json.loads(path.read_bytes()):
        entries = [r["anchor"], *r["pilot_events"]]
        for i, entry in enumerate(entries):
            end = entries[i + 1]["effective_from"] if i + 1 < len(entries) else "9999-12-31"
            intervals[r["security_id"]].append((entry["effective_from"], end, entry["status"]))

    def status(sid: str, day: str) -> str:
        entries = intervals[sid]
        found = [
            s
            for start, end, s in entries
            if start <= day and (day <= end if ":SSE:" in sid else day < end)
        ]
        if len(found) != 1:
            raise ValueError(f"STATUS_NOT_UNIQUE:{sid}:{day}")
        return found[0]

    return status


def audit(staging: Path, sdk_root: Path, repository: Path) -> dict:
    root = staging / "raw-failover-v1"
    sdk_file = sdk_root / "akshare/stock_feature/stock_hist_tx.py"
    sdk = sdk_file.read_bytes()
    record = sdk_root / "akshare-1.18.94.dist-info/RECORD"
    metadata = sdk_root / "akshare-1.18.94.dist-info/METADATA"
    expected = next(
        r[1]
        for r in csv.reader(record.read_text().splitlines())
        if r[0] == "akshare/stock_feature/stock_hist_tx.py"
    )
    if sha(sdk) != SDK_SHA or expected != "sha256=" + base64.urlsafe_b64encode(
        bytes.fromhex(SDK_SHA)
    ).decode().rstrip("="):
        raise ValueError("SDK_PIN_MISMATCH")
    if "Version: 1.18.94\n" not in metadata.read_text():
        raise ValueError("PACKAGE_VERSION_MISMATCH")
    strategy = repository / "backend/app/research/strategy.py"
    if sha(strategy.read_bytes()) != STRATEGY_SHA:
        raise ValueError("AMOUNT_CONSUMER_CHANGED_REVIEW_REQUIRED")
    save(
        root / "amount-sdk-evidence.json",
        dict(
            version="1.18.94",
            file="akshare/stock_feature/stock_hist_tx.py",
            source_file_sha256=SDK_SHA,
            source=sdk.decode(),
            record_sha256=sha(record.read_bytes()),
            metadata_sha256=sha(metadata.read_bytes()),
            record_entry=expected,
            source_commit=None,
            wheel_archive_hash=None,
            upstream_unit="10000 CNY",
            akshare_returned_unit="CNY",
        ),
    )
    sessions = json.loads(
        (staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json").read_bytes()
    )
    scheduled = {d for i, d in enumerate(sessions, 1) if i >= 253 and (i - 253) % 20 == 0}
    members = {r["symbol"]: r for r in pilot_members(staging)}
    checkpoint = json.loads(
        (staging / "pilot-akshare-20260911/recovery-checkpoint.json").read_bytes()
    )
    available, primary_raw, sources = {}, {}, []
    for sid, receipt in sorted(checkpoint["completed"].items()):
        raw = (staging / receipt["raw_path"]).read_bytes()
        if sha(raw) != receipt["raw_sha256"]:
            raise ValueError("PRIMARY_HASH_CHANGED")
        primary_raw[sid] = {
            r.split(",")[0]: r.split(",") for r in json.loads(raw)["data"]["klines"]
        }
        available[sid] = [
            dict(trading_date=d, amount=v[6]) for d, v in sorted(primary_raw[sid].items())
        ]
        sources.append(dict(path=receipt["raw_path"], sha256=sha(raw), provider="Eastmoney"))
    parity_rows, candidate_ids = [], set()
    for symbol in (*TENCENT_SAMPLE, *EXTRA_SAMPLE):
        member = members[symbol]
        sid = member["security_id"]
        candidate_ids.add(sid)
        folder = "tencent-candidate" if symbol in TENCENT_SAMPLE else "impact-candidate"
        repeats, upstream = [], {}
        for repeat in (1, 2):
            parts = []
            for year in (2023, 2024):
                path = root / folder / f"{symbol}-{year}-{repeat}.json"
                raw = path.read_bytes()
                meta = json.loads(path.with_suffix(".json.meta.json").read_bytes())
                if (
                    meta.get("error")
                    or sha(raw) != meta["sha256"]
                    or meta["url"] != tencent_url(member["exchange"], symbol, year)
                ):
                    raise ValueError("CANDIDATE_LINEAGE_FAILED")
                sources.append(
                    dict(
                        path=path.relative_to(staging).as_posix(),
                        sha256=sha(raw),
                        provider="Tencent",
                        metadata=meta,
                    )
                )
                parts.append(normalized(raw, member, set(sessions)))
                code = ("sh" if member["exchange"] == "SSE" else "sz") + symbol
                data = json.loads(raw.decode().split("=", 1)[1], parse_float=str)
                for row in data["data"][code]["day"]:
                    if START <= row[0] <= END:
                        if not isinstance(row[8], str) or Decimal(row[8]).as_tuple().exponent != -2:
                            raise ValueError("UPSTREAM_PRECISION_CHANGED")
                        upstream[row[0]] = row[8]
            rows = merged(parts)
            if rows != merged(list(reversed(parts))):
                raise ValueError("INPUT_ORDER_FAILURE")
            repeats.append(rows)
        if repeats[0] != repeats[1]:
            raise ValueError("REPEATABILITY_FAILURE")
        available[sid] = repeats[0]  # Shadow candidate audit only; production remains primary.
        if sid in primary_raw:
            if set(primary_raw[sid]) != set(upstream):
                raise ValueError("OVERLAP_DATE_MISMATCH")
            for row in repeats[0]:
                d = row["trading_date"]
                p = primary_raw[sid][d]
                if any(
                    Decimal(p[i]) != Decimal(row[f])
                    for i, f in enumerate(("raw_open", "raw_close", "raw_high", "raw_low"), 1)
                ):
                    raise ValueError("OHLC_PARITY_FAILED")
                volume_width = Decimal(50) if member["board"] == "SSE_STAR" else Decimal(0)
                if abs(Decimal(p[5]) * 100 - Decimal(row["volume"])) > volume_width:
                    raise ValueError("VOLUME_PARITY_FAILED")
                parity_rows.append(
                    dict(security_id=sid, day=d, **comparison(p[6], upstream[d], "10000"))
                )
    get_status = status_lookup(staging)
    decisions, stress = [], []
    for sid, rows in sorted(available.items()):
        for item in interval_decisions(rows, QUANTUM if sid in candidate_ids else Decimal(0)):
            item.update(
                security_id=sid,
                candidate_shadow=sid in candidate_ids,
                scheduled=item["day"] in scheduled,
                status=get_status(sid, item["day"]),
            )
            # Count a conservative superset before suspension/factor/portfolio gates.
            item["potential_rule_evaluation"] = item["scheduled"] and item["status"] == "NORMAL"
            if not item["potential_rule_evaluation"]:
                item["actual_decision_stable"] = True
            else:
                item["actual_decision_stable"] = item["stable"]
            decisions.append(item)
        for item in interval_decisions(rows, QUANTUM):
            if not item["stable"]:
                stress.append(dict(security_id=sid, **item))
    ambiguous = [r for r in decisions if not r["actual_decision_stable"]]
    outliers = [r for r in parity_rows if Decimal(r["absolute_difference"]) > QUANTUM]
    save(root / "amount-impact-decisions.json", decisions)
    save(root / "amount-impact-parity.json", parity_rows)
    save(root / "amount-impact-sources.json", sources)
    report = dict(
        parser_version=VERSION,
        upstream_unit="10000 CNY",
        returned_unit="CNY",
        nominal_quantum_cny="100",
        interval="[max(0,A-100), A+100] CNY; quantization-only envelope",
        interval_justification=(
            "Closed union of floor, ceiling and nearest cells for 0.01 upstream units; "
            "no rounding mode asserted."
        ),
        interval_limit=(
            "Not a bound on unrelated vendor measurement or aggregation errors; "
            "outliers fail separately."
        ),
        available_securities=len(available),
        primary_securities=len(primary_raw),
        candidate_shadow_securities=len(candidate_ids),
        available_rows=sum(len(r) for r in available.values()),
        examined_security_dates=len(decisions),
        amount_dependent_decisions_total=sum(r["potential_rule_evaluation"] for r in decisions),
        amount_decisions_ambiguous=len(ambiguous),
        ambiguous=ambiguous,
        amount_decisions_stable=sum(
            r["potential_rule_evaluation"] and r["actual_decision_stable"] for r in decisions
        ),
        all_date_stress_ambiguous=stress,
        scheduled_dates=sorted(scheduled),
        cross_source_rows=len(parity_rows),
        absolute_difference=distribution([Decimal(r["absolute_difference"]) for r in parity_rows]),
        relative_difference=distribution([Decimal(r["relative_difference"]) for r in parity_rows]),
        outliers=outliers,
        outlier_count=len(outliers),
        strategy_sha256=STRATEGY_SHA,
        classification="LIMITED_PRECISION_PARITY"
        if not ambiguous and not outliers
        else "INSUFFICIENT_EVIDENCE",
        scope=(
            "AVAILABLE_SAMPLE_ONLY; every recovered partition must pass the same "
            "interval and provenance checks before publication"
        ),
        decisions_sha256=sha(canonical(decisions)),
        parity_sha256=sha(canonical(parity_rows)),
        sources_sha256=sha(canonical(sources)),
        sdk_evidence_sha256=sha((root / "amount-sdk-evidence.json").read_bytes()),
    )
    save(root / "amount-impact-audit.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--sdk-root", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.staging, args.sdk_root, args.repository)))
