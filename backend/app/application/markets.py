"""Bounded local market inspection. No acquisition and no writes to research archives."""

import re
from collections import Counter, defaultdict
from datetime import date, time
from decimal import Decimal
from functools import lru_cache
from importlib import import_module
from pathlib import Path
from threading import Lock
from typing import Any, cast

from app.application.experiments.data import (
    DEMO_END,
    DEMO_ID,
    DEMO_START,
    HISTORICAL_ID,
    ExperimentDatasetRegistry,
    ExperimentInputError,
)
from app.application.experiments.runner import json_value
from app.data.catalog.checksums import sha256_file
from app.data.catalog.models import DatasetManifest
from app.domain.markets import SecurityId
from app.paper.a_share_fixture import simulated_a_share_fixture

pq: Any = import_module("pyarrow.parquet")
MAX_DAYS = 366


def _suspension_boundary(value: str | None) -> tuple[str | None, time | None]:
    if value is None:
        return None, None
    match = re.match(r"^(\d{4})[-/](\d{2})[-/](\d{2})(?:\s+(\d{1,2}):(\d{2}))?", value)
    if match is None:
        raise ExperimentInputError("DATASET_INTEGRITY_FAILED")
    year, month, day, hour, minute = match.groups()
    return date(int(year), int(month), int(day)).isoformat(), (
        time(int(hour), int(minute)) if hour is not None else None
    )


def _suspension_evidence(row: dict[str, Any], day: str) -> dict[str, Any] | None:
    start, start_time = _suspension_boundary(row["suspended_at"])
    end, end_time = _suspension_boundary(row["resumed_or_ended_at"])
    assert start is not None
    if day < start or (end is not None and day > end):
        return None
    recorded = {"1": True, "0": False}.get(str(row.get("execution_open_blocked")))
    exchange = row.get("exchange") or row["security_id"].split(":")[1]
    if day == start:
        blocked = (
            recorded
            if exchange == "SSE"
            else (start_time <= time(9, 30) if start_time is not None else None)
        )
        semantics = "SUSPENSION_START_DAY"
        active = True
    elif day == end:
        # SSE endStopDate is not a proved resumption-at-open timestamp.
        # SZSE supplements' blocked flag applies to the resumption boundary, not its start.
        blocked = (
            (
                recorded
                if recorded is not None
                else end_time > time(9, 30)
                if end_time is not None
                else None
            )
            if exchange == "SZSE"
            else None
        )
        semantics = (
            "SZSE_RESUMPTION_BOUNDARY" if exchange == "SZSE" else "SSE_END_STOP_DATE_UNCERTAIN"
        )
        active = blocked is True
    else:
        blocked, active, semantics = True, True, "INSIDE_SUSPENSION_INTERVAL"
    return {
        **row,
        "suspended_date": start,
        "resumed_or_ended_date": end,
        "boundary_semantics": semantics,
        "day_open_blocked": blocked,
        "suspension_confirmed_on_day": active,
    }


@lru_cache(maxsize=1)
def _demo() -> tuple[Any, ...]:
    return simulated_a_share_fixture(session_count=340)


class MarketReader:
    def __init__(self, registry: ExperimentDatasetRegistry) -> None:
        self.registry = registry
        self._verified: dict[str, tuple[Any, ...]] = {}
        self._masters: dict[str, list[dict[str, Any]]] = {}
        self._lock = Lock()

    def _manifest(self, dataset_id: str) -> DatasetManifest | None:
        self.registry.resolve(dataset_id)
        return None if dataset_id == DEMO_ID else self.registry.manifest()

    def _read(
        self, manifest: DatasetManifest, relative: str, *, filters: Any = None
    ) -> list[dict[str, Any]]:
        root = self.registry.root / HISTORICAL_ID
        path = (root / relative).resolve()
        partition = next((p for p in manifest.partitions if p.relative_path == relative), None)
        if not path.is_relative_to(root.resolve()) or partition is None:
            raise ExperimentInputError("DATASET_INTEGRITY_FAILED")
        try:
            stat = path.stat()
            stamp = (
                stat.st_dev,
                stat.st_ino,
                stat.st_size,
                stat.st_mtime_ns,
                stat.st_ctime_ns,
                partition.sha256,
            )
            with self._lock:
                # Only a touched immutable partition is hashed, once per file version.
                if self._verified.get(relative) != stamp:
                    if sha256_file(path) != partition.sha256:
                        raise ExperimentInputError("DATASET_INTEGRITY_FAILED")
                    self._verified[relative] = stamp
            return cast(list[dict[str, Any]], pq.read_table(path, filters=filters).to_pylist())
        except (OSError, ValueError) as exc:
            raise ExperimentInputError("DATASET_INTEGRITY_FAILED") from exc

    def _master(self, manifest: DatasetManifest | None) -> list[dict[str, Any]]:
        if manifest is None:
            return [
                {
                    "security_id": f"CN-A:SSE:{600000 + i}",
                    "symbol": str(600000 + i),
                    "exchange": "SSE",
                    "board": "SSE_MAIN",
                    "name": None,
                    "source_observed_name": None,
                    "name_temporal_authority": "SYNTHETIC_DEMO",
                    "instrument_type": "COMMON_A_SHARE",
                    "effective_from": DEMO_START.isoformat(),
                    "effective_to": DEMO_END.isoformat(),
                    "source_id": DEMO_ID,
                }
                for i in range(10)
            ]
        # This is a small security index, not the all-market price history.
        try:
            stamp = (self.registry.root / HISTORICAL_ID / "securities.parquet").stat()
        except OSError as exc:
            raise ExperimentInputError("DATASET_INTEGRITY_FAILED") from exc
        key = f"{manifest.canonical_sha256}:{stamp.st_mtime_ns}:{stamp.st_ctime_ns}:{stamp.st_size}"
        with self._lock:
            cached = self._masters.get(key)
        if cached is None:
            cached = self._read(manifest, "securities.parquet")
            with self._lock:
                self._masters = {key: cached}
        return cached

    @staticmethod
    def _security(rows: list[dict[str, Any]]) -> dict[str, Any]:
        ordered = sorted(rows, key=lambda row: row["effective_from"])
        latest = ordered[-1]
        return {
            "security_id": latest["security_id"],
            "symbol": latest["symbol"],
            "exchange": latest["exchange"],
            "board": latest["board"],
            "name": latest.get("name"),
            "source_observed_name": latest.get("source_observed_name"),
            "name_temporal_authority": latest.get("name_temporal_authority"),
            "source_id": latest.get("source_id"),
            "source_url": latest.get("source_url"),
            "source_sha256": latest.get("source_sha256"),
            "listed_from": ordered[0]["effective_from"],
            "listed_to": latest["effective_to"],
        }

    def _metadata(self, dataset_id: str, manifest: DatasetManifest | None) -> dict[str, Any]:
        registered = self.registry.resolve(dataset_id)
        return {
            **registered,
            "provider": manifest.provider if manifest else "DETERMINISTIC_SYNTHETIC_GENERATOR",
            "provider_version": manifest.provider_version if manifest else DEMO_ID,
            "retrieved_at_utc": manifest.retrieval_timestamp.isoformat() if manifest else None,
            "market_rule_version": manifest.rule_version
            if manifest
            else "SYNTHETIC_SCENARIO_RULES",
            "source_lineage": list(manifest.source_lineage)
            if manifest
            else ["SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE"],
            "trading_date_timezone": "Asia/Shanghai",
            "is_live": False,
            "network_access_used": False,
            "incremental_update_available": False,
            "adjustment_basis": "RAW_TIMES_EFFECTIVE_HFQ_FACTOR_NO_END_DATE_REBASING",
            "adjustment_method": manifest.adjustment_method
            if manifest
            else "SYNTHETIC_IDENTITY_FACTOR",
            "limitations": [
                "READ_ONLY_ARCHIVE_NOT_LIVE_DATA",
                "NAMES_MAY_BE_SOURCE_OBSERVED_NOT_POINT_IN_TIME",
                "SUSPENSION_ENDPOINT_TIMING_MAY_BE_UNKNOWN",
                *(
                    list(manifest.known_limitations)
                    if manifest
                    else ["SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE"]
                ),
            ],
        }

    def search(
        self, dataset_id: str, q: str, exchange: str, limit: int, offset: int
    ) -> dict[str, Any]:
        manifest = self._manifest(dataset_id)
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in self._master(manifest):
            if row["instrument_type"] == "COMMON_A_SHARE":
                grouped[row["security_id"]].append(row)
        needle = q.casefold().strip()
        found = []
        for _, rows in sorted(grouped.items()):
            security = self._security(rows)
            if exchange != "ALL" and security["exchange"] != exchange:
                continue
            # Search all observed aliases, never assert these names held on a historical date.
            haystack = " ".join(
                str(r.get(k) or "")
                for r in rows
                for k in ("security_id", "symbol", "name", "source_observed_name")
            )
            if needle in haystack.casefold():
                found.append(security)
        return {
            "items": found[offset : offset + limit],
            "total": len(found),
            "limit": limit,
            "offset": offset,
            "metadata": self._metadata(dataset_id, manifest),
        }

    def security(self, dataset_id: str, security_id: str) -> dict[str, Any]:
        SecurityId(value=security_id)
        manifest = self._manifest(dataset_id)
        rows = [r for r in self._master(manifest) if r["security_id"] == security_id]
        if not rows:
            raise LookupError("SECURITY_NOT_FOUND")
        return self._security(rows)

    def bars(self, dataset_id: str, security_id: str, start: date, end: date) -> dict[str, Any]:
        SecurityId(value=security_id)
        if end < start or (end - start).days >= MAX_DAYS:
            raise ExperimentInputError("MARKET_DATE_RANGE_MUST_BE_1_TO_366_DAYS")
        manifest = self._manifest(dataset_id)
        registered = self.registry.resolve(dataset_id)
        if (
            not date.fromisoformat(registered["coverage_start"])
            <= start
            <= end
            <= date.fromisoformat(registered["coverage_end"])
        ):
            raise ExperimentInputError("DATES_OUTSIDE_DATASET")
        members = [r for r in self._master(manifest) if r["security_id"] == security_id]
        if not members:
            raise LookupError("SECURITY_NOT_FOUND")
        if manifest is None:
            return self._demo_bars(security_id, start, end, members)
        dates = self._read(
            manifest,
            "calendar.parquet",
            filters=[
                ("session_date", ">=", start.isoformat()),
                ("session_date", "<=", end.isoformat()),
            ],
        )
        days = sorted(r["session_date"] for r in dates if r["is_open"] in (True, "1"))
        exchange = security_id.split(":")[1]
        paths = sorted(
            p.relative_path
            for p in manifest.partitions
            if p.relative_path.startswith(f"raw/{exchange}/")
            and start.strftime("%Y-%m") <= Path(p.relative_path).stem <= end.strftime("%Y-%m")
        )
        filters = [
            ("security_id", "=", security_id),
            ("trading_date", ">=", start.isoformat()),
            ("trading_date", "<=", end.isoformat()),
        ]
        raw = {}
        for path in paths:
            for row in self._read(manifest, path, filters=filters):
                if row["trading_date"] in raw:
                    raise ExperimentInputError("DUPLICATE_MARKET_OBSERVATION")
                raw[row["trading_date"]] = row
        factors = self._read(
            manifest,
            "adjustment-factors.parquet",
            filters=[("security_id", "=", security_id), ("effective_date", "<=", end.isoformat())],
        )
        features = {
            r["trading_date"]: r
            for r in self._read(manifest, "feature-only-observations.parquet", filters=filters)
        }
        suspensions = self._read(
            manifest,
            "suspension-events.parquet",
            # Accepted SZSE timestamps retain slash dates/intraday text. Never compare
            # those raw strings with ISO dates; still restrict the read to one security.
            filters=[("security_id", "=", security_id)],
        )
        items = []
        for day in days:
            bar, feature = raw.get(day), features.get(day)
            listed = any(
                r["effective_from"] <= day
                and (r["effective_to"] is None or day <= r["effective_to"])
                for r in members
            )
            evidence = [e for r in suspensions if (e := _suspension_evidence(r, day)) is not None]
            open_states = [r["day_open_blocked"] for r in evidence]
            open_blocked = True if True in open_states else None if None in open_states else False
            suspended = any(r["suspension_confirmed_on_day"] for r in evidence)
            status = (
                "OBSERVED"
                if bar and Decimal(bar["volume"]) > 0
                else "OUTSIDE_LISTING"
                if not listed
                else "SUSPENDED"
                if suspended
                else "FEATURE_ONLY"
                if feature
                else "SUSPENSION_BOUNDARY_UNCERTAIN"
                if evidence and open_blocked is None
                else "OBSERVED"
                if bar
                else "MISSING_OBSERVATION"
            )
            eligible = sorted(
                (
                    r
                    for r in factors
                    if r["interval_from"] <= day <= r["interval_to"] and r["effective_date"] <= day
                ),
                key=lambda r: r["effective_date"],
            )
            if len({(r["interval_from"], r["interval_to"]) for r in eligible}) > 1:
                raise ExperimentInputError("AMBIGUOUS_ADJUSTMENT_INTERVAL")
            factor = eligible[-1] if eligible else None
            values = {
                key: bar.get(f"raw_{key}")
                if bar
                else feature.get("raw_close")
                if feature and key == "close"
                else None
                for key in ("open", "high", "low", "close")
            }
            values.update(
                volume=bar["volume"] if bar else None, amount=bar["amount"] if bar else None
            )
            items.append(
                {
                    "trading_date": day,
                    "raw": values,
                    "adjusted": {
                        k: json_value(Decimal(str(values[k])) * Decimal(factor["hfq_factor"]))
                        if values[k] is not None and factor
                        else None
                        for k in ("open", "high", "low", "close")
                    },
                    "adjustment_factor": factor["hfq_factor"] if factor else None,
                    "adjustment_effective_date": factor["effective_date"] if factor else None,
                    "adjustment_lineage": factor["lineage"] if factor else None,
                    "status": status,
                    "risk_status": (bar or feature or {}).get("risk_status"),
                    "execution_open_blocked": open_blocked,
                    "suspension_evidence": evidence,
                    "source_lineage": bar["source_lineage"]
                    if bar
                    else feature["lineage"]
                    if feature
                    else "OFFICIAL_SUSPENSION_EVIDENCE"
                    if evidence
                    else None,
                }
            )
        used = {
            *paths,
            "securities.parquet",
            "calendar.parquet",
            "adjustment-factors.parquet",
            "feature-only-observations.parquet",
            "suspension-events.parquet",
        }
        metadata = self._metadata(dataset_id, manifest)
        metadata["partitions"] = [
            {"path": p.relative_path, "sha256": p.sha256}
            for p in manifest.partitions
            if p.relative_path in used
        ]
        return self._response(metadata, self._security(members), items, start, end)

    def _demo_bars(
        self, security_id: str, start: date, end: date, members: list[dict[str, Any]]
    ) -> dict[str, Any]:
        _, sessions, _ = _demo()
        items = []
        for session in sessions:
            if not start <= session.trading_date <= end:
                continue
            bar = next(b for b in session.bars if str(b.security_id) == security_id)
            prices = {
                k: json_value(getattr(bar, f"raw_{k}")) for k in ("open", "high", "low", "close")
            }
            items.append(
                {
                    "trading_date": session.trading_date.isoformat(),
                    "raw": {
                        **prices,
                        "volume": json_value(bar.volume),
                        "amount": json_value(bar.amount),
                    },
                    "adjusted": prices,
                    "adjustment_factor": "1",
                    "adjustment_effective_date": DEMO_START.isoformat(),
                    "adjustment_lineage": "SYNTHETIC_IDENTITY_FACTOR",
                    "status": "OBSERVED",
                    "risk_status": "NORMAL",
                    "execution_open_blocked": False,
                    "suspension_evidence": [],
                    "source_lineage": "SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE",
                }
            )
        metadata = self._metadata(DEMO_ID, None)
        metadata["partitions"] = []
        return self._response(metadata, self._security(members), items, start, end)

    @staticmethod
    def _response(
        metadata: dict[str, Any],
        security: dict[str, Any],
        items: list[dict[str, Any]],
        start: date,
        end: date,
    ) -> dict[str, Any]:
        counts = dict(sorted(Counter(item["status"] for item in items).items()))
        metadata.update(
            requested_start=start.isoformat(),
            requested_end=end.isoformat(),
            status_counts=counts,
            adjustment_missing_observations=sum(
                i["raw"]["close"] is not None and i["adjustment_factor"] is None for i in items
            ),
        )
        return {"security": security, "metadata": metadata, "items": items, "total": len(items)}
