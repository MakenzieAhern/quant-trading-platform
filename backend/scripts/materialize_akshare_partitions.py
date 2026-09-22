"""Build verified partial raw/factor partitions; never publish an incomplete Pilot."""

import argparse
import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.catalog import write_canonical_parquet
from app.data.providers.research import DailyBarRecord
from app.domain.markets import SecurityId
from scripts.reconcile_sse_cninfo import save, sha
from scripts.sina_adjustment_audit import parse_factors
from scripts.stage_akshare_pilot import END, START, pilot_members

POLICY_PATH = Path(__file__).resolve().parents[2] / "docs/research/CN_A_RAW_OHLCV_FAILOVER_V1.json"


def normalized_bars(raw: bytes, member: dict, sessions: set[str]) -> list[dict]:
    data = json.loads(raw)["data"]
    if data["code"] != member["symbol"]:
        raise ValueError("RAW_IDENTITY_MISMATCH")
    result = []
    seen = set()
    for line in data["klines"]:
        fields = line.split(",")
        if len(fields) < 11:
            raise ValueError("RAW_SCHEMA_MISMATCH")
        day, opening, closing, high, low, lots, amount = fields[:7]
        if day in seen or day not in sessions or not START <= day <= END:
            raise ValueError("INVALID_OR_DUPLICATE_TRADING_DATE")
        if day < member["listing_date"] or (
            member["delisting_date"] and day >= member["delisting_date"]
        ):
            raise ValueError("BAR_OUTSIDE_LISTING_LIFECYCLE")
        seen.add(day)
        bar = DailyBarRecord(
            security_id=SecurityId(value=member["security_id"]),
            trading_date=date.fromisoformat(day),
            raw_open=Decimal(opening),
            raw_close=Decimal(closing),
            raw_high=Decimal(high),
            raw_low=Decimal(low),
            volume=Decimal(lots) * 100,
            amount=Decimal(amount),
        )
        row = bar.model_dump(mode="python")
        row["security_id"] = member["security_id"]
        row["source"] = "AKShare:stock_zh_a_hist:Eastmoney:fqt=0"
        result.append(row)
    if not result:
        raise ValueError("EMPTY_RAW_PARTITION")
    return sorted(result, key=lambda row: row["trading_date"])


def materialize(staging: Path) -> dict:
    root = staging / "pilot-akshare-20260911"
    checkpoint = json.loads((root / "recovery-checkpoint.json").read_bytes())
    completed = dict(checkpoint["completed"])
    secondary_path = root / "secondary-checkpoint.json"
    if secondary_path.exists():
        secondary = json.loads(secondary_path.read_bytes())
        if secondary["policy_sha256"] != sha(POLICY_PATH.read_bytes()):
            raise ValueError("SECONDARY_POLICY_CHANGED")
        if completed.keys() & secondary["completed"].keys():
            raise ValueError("SECONDARY_MUST_NOT_REPLACE_PRIMARY")
        completed.update(secondary["completed"])
    members = {r["security_id"]: r for r in pilot_members(staging)}
    # Scope is applied before data requirements. Inputs remain in their immutable
    # provider checkpoints even when a later approved release scope does not use them.
    completed = {sid: result for sid, result in completed.items() if sid in members}
    sessions = set(
        json.loads(
            (
                staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json"
            ).read_bytes()
        )
    )
    destination = root / "dataset-staging"
    receipts_path = root / "partition-checkpoint.json"
    previous = json.loads(receipts_path.read_bytes()) if receipts_path.exists() else {}
    receipts = previous.get("partitions", {})
    out_of_scope_receipts = {
        **previous.get("out_of_scope_preserved_partitions", {}),
        **{sid: record for sid, record in receipts.items() if sid not in members},
    }
    receipts = {sid: record for sid, record in receipts.items() if sid in members}
    failures = {}
    for sid, inputs in sorted(completed.items()):
        source_hashes = {}
        for kind in ("raw", "factor"):
            path = staging / inputs[kind + "_path"]
            source_hashes[kind] = sha(path.read_bytes())
            if source_hashes[kind] != inputs[kind + "_sha256"]:
                raise ValueError("SOURCE_BYTES_CHANGED")
        if inputs.get("provider") == "Tencent":
            payload = json.loads((staging / inputs["raw_path"]).read_bytes())
            for source in payload["sources"]:
                if sha((staging / source["path"]).read_bytes()) != source["sha256"]:
                    raise ValueError("SECONDARY_UNDERLYING_SOURCE_CHANGED")
        existing = receipts.get(sid)
        if existing and existing["source_hashes"] != source_hashes:
            raise ValueError("PARTITION_SOURCE_VINTAGE_CHANGED")
        if existing and existing["source_hashes"] == source_hashes:
            if all(
                sha((destination / item["relative_path"]).read_bytes()) == item["sha256"]
                for item in existing["files"]
            ):
                continue
            raise ValueError("PARTITION_BYTES_CHANGED")
        try:
            member = members[sid]
            raw = (staging / inputs["raw_path"]).read_bytes()
            if inputs.get("provider") == "Tencent":
                payload = json.loads(raw)
                if (
                    payload["format"] != "TENCENT_RAW_V1"
                    or payload["policy_sha256"] != inputs["policy_sha256"]
                ):
                    raise ValueError("SECONDARY_FORMAT_OR_AUTHORITY_CHANGED")
                bars = []
                for item in payload["rows"]:
                    bar = DailyBarRecord.model_validate(item)
                    day = bar.trading_date.isoformat()
                    if (
                        str(bar.security_id) != sid
                        or day not in sessions
                        or day < member["listing_date"]
                        or (member["delisting_date"] and day >= member["delisting_date"])
                    ):
                        raise ValueError("SECONDARY_IDENTITY_OR_LIFECYCLE_CHANGED")
                    row = bar.model_dump(mode="python")
                    row["security_id"] = sid
                    row["source"] = "AKShare:stock_zh_a_hist_tx:Tencent:day:raw"
                    bars.append(row)
                dates = [b["trading_date"] for b in bars]
                if not dates or dates != sorted(set(dates)):
                    raise ValueError("SECONDARY_DUPLICATE_OR_UNSORTED_DATE")
            elif inputs.get("provider") is None:
                bars = normalized_bars(raw, member, sessions)
            else:
                raise ValueError("UNACCEPTED_PARTITION_PROVIDER")
            symbol = ("sh" if member["exchange"] == "SSE" else "sz") + member["symbol"]
            curve = parse_factors((staging / inputs["factor_path"]).read_bytes(), symbol, "hfq")
            baseline = max((day for day, _ in curve if day <= START), default=None)
            factors = [
                dict(
                    security_id=sid,
                    effective_from=day,
                    hfq_factor=value,
                    source="AKShare:Sina:hfq-factor",
                    simulation_use="AS_OF_FEATURE_ONLY",
                )
                for day, value in curve
                if day <= END and (day >= START or day == baseline)
            ]
            files = []
            for kind, rows, keys in (
                ("raw", bars, ("security_id", "trading_date")),
                ("factors", factors, ("security_id", "effective_from")),
            ):
                relative = f"{member['exchange']}/{member['symbol']}/{kind}.parquet"
                target = destination / relative
                temporary = target.with_suffix(".parquet.tmp")
                partition = write_canonical_parquet(
                    temporary, fieldnames=tuple(sorted(rows[0])), rows=rows, sort_keys=keys
                )
                temporary.replace(target)
                files.append(
                    partition.model_copy(update={"relative_path": relative}).model_dump(mode="json")
                )
            receipts[sid] = dict(
                source_hashes=source_hashes,
                files=files,
                raw_rows=len(bars),
                factor_rows=len(factors),
                status="PARTIAL_INPUTS_NOT_PUBLISHED",
            )
            save(
                receipts_path,
                dict(
                    partitions=receipts,
                    published=False,
                    out_of_scope_preserved_partitions=out_of_scope_receipts,
                ),
            )
        except (ValueError, KeyError, IndexError) as exc:
            failures[sid] = dict(error=type(exc).__name__, reason=str(exc))
    report = dict(
        securities_partitioned=len(receipts),
        raw_rows=sum(r["raw_rows"] for r in receipts.values()),
        factor_rows=sum(r["factor_rows"] for r in receipts.values()),
        partitions=receipts,
        failures=failures,
        published=False,
        dataset_audited=False,
        dataset_frozen=False,
        out_of_scope_preserved_partitions=out_of_scope_receipts,
    )
    save(receipts_path, report)
    print(json.dumps({k: v for k, v in report.items() if k != "partitions"}))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    materialize(parser.parse_args().staging)
