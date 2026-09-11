"""Offline candidate-only Tencent parity audit. Never changes ingestion authority."""

import argparse
import json
from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.data.providers.research import DailyBarRecord
from app.domain.markets import SecurityId
from scripts.probe_raw_failover import TENCENT_SAMPLE, tencent_url
from scripts.reconcile_sse_cninfo import canonical, save, sha
from scripts.stage_akshare_pilot import END, START, pilot_members

VERSION = "tencent-raw-candidate-v1"


def normalized(raw: bytes, member: dict, sessions: set[str]) -> list[dict]:
    """Inspect raw day only, with explicit candidate units; never use adjusted fallback."""
    text = raw.decode("utf-8")
    payload = json.loads(text.split("=", 1)[1], parse_float=str)
    if payload["code"] != 0:
        raise ValueError("CANDIDATE_SERVICE_ERROR")
    symbol = ("sh" if member["exchange"] == "SSE" else "sz") + member["symbol"]
    rows = payload["data"][symbol].get("day")
    if not rows:
        raise ValueError("RAW_DAY_UNAVAILABLE_NO_ADJUSTED_FALLBACK")
    previous = ""
    result = []
    for row in rows:
        day = row[0]
        date.fromisoformat(day)
        if day <= previous:
            raise ValueError("NON_MONOTONIC_OR_DUPLICATE_DATE")
        previous = day
        if not START <= day <= END:
            continue  # SDK response pads years to 640 rows; filter before use.
        if (
            day not in sessions
            or day < member["listing_date"]
            or (member["delisting_date"] and day >= member["delisting_date"])
        ):
            raise ValueError("DATE_OUTSIDE_CALENDAR_OR_LIFECYCLE")
        # Candidate normalization, not a claim the pinned SDK converts SZSE 000 correctly.
        volume_multiplier = 1 if member["board"] == "SSE_STAR" else 100
        bar = DailyBarRecord(
            security_id=SecurityId(value=member["security_id"]),
            trading_date=date.fromisoformat(day),
            raw_open=Decimal(row[1]),
            raw_close=Decimal(row[2]),
            raw_high=Decimal(row[3]),
            raw_low=Decimal(row[4]),
            volume=Decimal(row[5]) * volume_multiplier,
            amount=Decimal(row[8]) * 10000,
        )
        result.append(bar.model_dump(mode="json"))
    if not result:
        raise ValueError("EMPTY_PILOT_HISTORY")
    return result


def merged(parts: list[list[dict]]) -> list[dict]:
    result = {}
    for rows in parts:
        for row in rows:
            day = row["trading_date"]
            if day in result and result[day] != row:
                raise ValueError("CONFLICTING_YEAR_OVERLAP")
            result[day] = row
    return [result[day] for day in sorted(result)]


def parity(candidate: list[dict], primary_raw: bytes, star: bool) -> list[dict]:
    primary = {r.split(",")[0]: r.split(",") for r in json.loads(primary_raw)["data"]["klines"]}
    other = {r["trading_date"]: r for r in candidate}
    result = []
    for day in sorted(primary.keys() | other.keys()):
        if day not in primary or day not in other:
            result.append(dict(day=day, field="date", classification="MISSING_DATE_DIFFERENCE"))
            continue
        a, b = primary[day], other[day]
        for index, field in enumerate(("raw_open", "raw_close", "raw_high", "raw_low"), 1):
            delta = abs(Decimal(a[index]) - Decimal(b[field]))
            result.append(
                dict(
                    day=day,
                    field=field,
                    difference=str(delta),
                    classification=(
                        "MATERIAL_PRICE_DIFFERENCE"
                        if delta
                        else "NUMERICALLY_EQUIVALENT_WITH_FORMATTING_DIFFERENCE"
                    ),
                )
            )
        for field, value, quantum in (
            ("volume", Decimal(a[5]) * 100, Decimal(50) if star else Decimal(0)),
            ("amount", Decimal(a[6]), Decimal(50)),
        ):
            delta = abs(value - Decimal(b[field]))
            classification = "NUMERICALLY_EQUIVALENT_WITH_FORMATTING_DIFFERENCE"
            if delta:
                classification = (
                    (
                        "DOCUMENTED_VENDOR_VOLUME_DIFFERENCE"
                        if field == "volume"
                        else "NUMERICALLY_EQUIVALENT_WITH_FORMATTING_DIFFERENCE"
                    )
                    if delta <= quantum
                    else "UNEXPLAINED_DIFFERENCE"
                )
            result.append(
                dict(
                    day=day,
                    field=field,
                    primary=str(value),
                    candidate=b[field],
                    difference=str(delta),
                    classification=classification,
                )
            )
    return result


def audit(staging: Path) -> dict:
    root = staging / "raw-failover-v1"
    sources = root / "tencent-candidate"
    members = {r["symbol"]: r for r in pilot_members(staging)}
    sessions = set(
        json.loads(
            (
                staging / "sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json"
            ).read_bytes()
        )
    )
    checkpoint = json.loads(
        (staging / "pilot-akshare-20260911/recovery-checkpoint.json").read_bytes()
    )
    reports, inventory = [], []
    for symbol in TENCENT_SAMPLE:
        member = members[symbol]
        repeats = []
        for repeat in (1, 2):
            parts = []
            for year in (2023, 2024):
                path = sources / f"{symbol}-{year}-{repeat}.json"
                raw = path.read_bytes()
                meta_path = path.with_suffix(".json.meta.json")
                meta = json.loads(meta_path.read_bytes())
                if (
                    meta.get("error")
                    or sha(raw) != meta["sha256"]
                    or meta["url"] != tencent_url(member["exchange"], symbol, year)
                ):
                    raise ValueError("SOURCE_LINEAGE_OR_CHECKSUM_FAILURE")
                inventory.append(
                    dict(
                        path=path.relative_to(root).as_posix(),
                        sha256=sha(raw),
                        metadata_sha256=sha(meta_path.read_bytes()),
                        metadata=meta,
                    )
                )
                parts.append(normalized(raw, member, sessions))
            rows = merged(parts)
            if rows != merged(list(reversed(parts))):
                raise ValueError("INPUT_ORDER_CHANGED_RESULT")
            repeats.append(rows)
        if repeats[0] != repeats[1]:
            raise ValueError("REQUEST_REPEATABILITY_FAILURE")
        rows = repeats[0]
        item = dict(
            security_id=member["security_id"],
            member=member,
            rows=len(rows),
            first=rows[0]["trading_date"],
            last=rows[-1]["trading_date"],
            normalized_logical_sha256=sha(canonical(rows)),
            repeatability="PASS",
        )
        cached = checkpoint["completed"].get(member["security_id"])
        if cached:
            raw = (staging / cached["raw_path"]).read_bytes()
            if sha(raw) != cached["raw_sha256"]:
                raise ValueError("PRIMARY_CACHE_CHECKSUM_FAILURE")
            differences = parity(rows, raw, member["board"] == "SSE_STAR")
            save(root / f"parity-{symbol}.json", differences)
            item.update(
                primary_sha256=sha(raw),
                parity_sha256=sha(canonical(differences)),
                comparison_counts=dict(Counter(r["classification"] for r in differences)),
                unexplained=[
                    r
                    for r in differences
                    if r["classification"]
                    in {
                        "MATERIAL_PRICE_DIFFERENCE",
                        "MISSING_DATE_DIFFERENCE",
                        "UNEXPLAINED_DIFFERENCE",
                    }
                ],
            )
        reports.append(item)
    unresolved = [
        dict(security_id=r["security_id"], **d) for r in reports for d in r.get("unexplained", [])
    ]
    report = dict(
        parser_version=VERSION,
        candidate_only=True,
        promoted=False,
        cross_source_parity="PARTIAL" if unresolved else "PASS",
        acceptance="NOT_PROMOTED" if unresolved else "REQUIRES_AUTHORITY_REVIEW",
        securities=reports,
        unresolved_differences=unresolved,
        sources=inventory,
    )
    save(root / "candidate-audit.json", report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    report = audit(parser.parse_args().staging)
    print(json.dumps({k: v for k, v in report.items() if k not in {"securities", "sources"}}))
