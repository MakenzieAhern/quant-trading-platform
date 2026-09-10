"""Fail-closed point-in-time A-share security master."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import date, timedelta
from enum import StrEnum
from importlib import import_module
from itertools import pairwise
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.data.catalog.checksums import canonical_sha256, sha256_file
from app.domain.common import UtcDateTime
from app.domain.markets import Board, Exchange, SecurityId


class SecurityMasterError(ValueError):
    pass


class SecurityMasterStatus(StrEnum):
    LISTED = "LISTED"
    DELISTED = "DELISTED"
    SUSPENDED = "SUSPENDED"
    UNKNOWN = "UNKNOWN"


class SecuritySourceVersion(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: str = Field(min_length=1)
    version: str = Field(min_length=1)


class _SecurityMasterRecordValues(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    security_id: SecurityId
    exchange: Exchange
    symbol: str = Field(pattern=r"^[0-9]{6}$")
    name: str | None = None
    board: Board
    listing_date: date
    delisting_date: date | None = None
    effective_from: date
    effective_to: date | None = None
    status: SecurityMasterStatus
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    retrieval_timestamp: UtcDateTime
    source_document_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    provenance: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_identity_and_dates(self) -> _SecurityMasterRecordValues:
        if self.security_id.value.split(":")[1] != self.exchange.value:
            raise ValueError("security_id exchange must match exchange")
        if self.delisting_date is not None and self.delisting_date < self.listing_date:
            raise ValueError("delisting_date must not precede listing_date")
        if self.effective_from < self.listing_date:
            raise ValueError("effective_from must not precede listing_date")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("effective_to must not precede effective_from")
        if self.provenance != tuple(sorted(set(self.provenance))):
            raise ValueError("provenance must be unique and sorted")
        return self


class SecurityMasterRecord(_SecurityMasterRecordValues):
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def create(cls, **values: object) -> SecurityMasterRecord:
        parsed = _SecurityMasterRecordValues.model_validate(values)
        payload = parsed.model_dump(mode="json")
        return cls(**payload, checksum=canonical_sha256(payload))

    @model_validator(mode="after")
    def validate_checksum(self) -> SecurityMasterRecord:
        payload = self.model_dump(mode="json", exclude={"checksum"})
        if self.checksum != canonical_sha256(payload):
            raise ValueError("SECURITY_MASTER_RECORD_CHECKSUM_MISMATCH")
        return self

    def active_on(self, trading_date: date) -> bool:
        effective = self.effective_from <= trading_date and (
            self.effective_to is None or trading_date <= self.effective_to
        )
        listed = self.listing_date <= trading_date and (
            self.delisting_date is None or trading_date <= self.delisting_date
        )
        return effective and listed


class PointInTimeSecurityMaster(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    coverage_start: date
    coverage_end: date
    complete: bool
    source_versions: tuple[SecuritySourceVersion, ...]
    records: tuple[SecurityMasterRecord, ...]
    checksum: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def create(
        cls,
        *,
        coverage_start: date,
        coverage_end: date,
        complete: bool,
        source_versions: Iterable[SecuritySourceVersion],
        records: Iterable[SecurityMasterRecord],
    ) -> PointInTimeSecurityMaster:
        ordered_sources = tuple(
            sorted(source_versions, key=lambda item: (item.source, item.version))
        )
        ordered_records = tuple(sorted(records, key=_record_key))
        payload = {
            "coverage_start": coverage_start.isoformat(),
            "coverage_end": coverage_end.isoformat(),
            "complete": complete,
            "source_versions": [item.model_dump(mode="json") for item in ordered_sources],
            "record_checksums": [item.checksum for item in ordered_records],
        }
        return cls(
            coverage_start=coverage_start,
            coverage_end=coverage_end,
            complete=complete,
            source_versions=ordered_sources,
            records=ordered_records,
            checksum=canonical_sha256(payload),
        )

    @model_validator(mode="after")
    def validate_master(self) -> PointInTimeSecurityMaster:
        if self.coverage_end < self.coverage_start:
            raise ValueError("coverage_end must not precede coverage_start")
        if self.source_versions != tuple(
            sorted(set(self.source_versions), key=lambda item: (item.source, item.version))
        ):
            raise ValueError("source versions must be unique and sorted")
        if self.records != tuple(sorted(self.records, key=_record_key)):
            raise ValueError("security master records must be sorted")
        allowed = {(item.source, item.version) for item in self.source_versions}
        if any((item.source, item.source_version) not in allowed for item in self.records):
            raise ValueError("SECURITY_MASTER_SOURCE_VERSION_MISMATCH")
        _validate_periods(self.records)
        payload = {
            "coverage_start": self.coverage_start.isoformat(),
            "coverage_end": self.coverage_end.isoformat(),
            "complete": self.complete,
            "source_versions": [item.model_dump(mode="json") for item in self.source_versions],
            "record_checksums": [item.checksum for item in self.records],
        }
        if self.checksum != canonical_sha256(payload):
            raise ValueError("SECURITY_MASTER_CHECKSUM_MISMATCH")
        return self

    def eligible_universe(self, trading_date: date) -> tuple[SecurityId, ...]:
        self._require_queryable(trading_date)
        return tuple(
            sorted(
                {item.security_id for item in self.records if item.active_on(trading_date)},
                key=str,
            )
        )

    def board_on(self, security_id: SecurityId, trading_date: date) -> Board:
        self._require_queryable(trading_date)
        matches = tuple(
            item.board
            for item in self.records
            if item.security_id == security_id and item.active_on(trading_date)
        )
        if len(matches) != 1:
            raise SecurityMasterError("SECURITY_MASTER_CLASSIFICATION_MISSING")
        return matches[0]

    def snapshot_checksum(self, trading_date: date) -> str:
        security_ids = self.eligible_universe(trading_date)
        return canonical_sha256(
            {
                "trading_date": trading_date.isoformat(),
                "security_master_checksum": self.checksum,
                "security_ids": [str(item) for item in security_ids],
            }
        )

    def _require_queryable(self, trading_date: date) -> None:
        if not self.complete:
            raise SecurityMasterError("SECURITY_MASTER_INCOMPLETE")
        if not self.coverage_start <= trading_date <= self.coverage_end:
            raise SecurityMasterError("SECURITY_MASTER_DATE_OUTSIDE_COVERAGE")


class SecurityMasterInputSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    filename: str = Field(pattern=r"^[^/\\]+\.(csv|json|xlsx)$")
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    source_url: str = Field(min_length=1)
    retrieval_timestamp: UtcDateTime
    complete: bool


class SecurityMasterInputManifest(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: str = "1.0"
    coverage_start: date
    coverage_end: date
    complete: bool
    sources: tuple[SecurityMasterInputSource, ...]


def load_security_master(staging_root: Path) -> PointInTimeSecurityMaster:
    manifest_path = staging_root / "security-master-input.json"
    if not manifest_path.is_file():
        raise SecurityMasterError("SECURITY_MASTER_INPUT_MANIFEST_MISSING")
    try:
        manifest = SecurityMasterInputManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as exc:
        raise SecurityMasterError("SECURITY_MASTER_INPUT_MANIFEST_INVALID") from exc
    required_sources = {"SSE_OFFICIAL", "SZSE_OFFICIAL"}
    if {item.source for item in manifest.sources} != required_sources:
        raise SecurityMasterError("SECURITY_MASTER_REQUIRED_SOURCES_MISSING")
    records: list[SecurityMasterRecord] = []
    for source in manifest.sources:
        path = staging_root / source.filename
        if not path.is_file() or sha256_file(path) != source.sha256:
            raise SecurityMasterError("SECURITY_MASTER_SOURCE_FILE_MISSING_OR_CHANGED")
        for row in _read_rows(path):
            values = _normalize_row(row)
            row_source_url = values.pop("source_url", None)
            provenance = (str(row_source_url or source.source_url),)
            records.append(
                SecurityMasterRecord.create(
                    **values,
                    source=source.source,
                    source_version=source.source_version,
                    retrieval_timestamp=source.retrieval_timestamp,
                    source_document_sha256=source.sha256,
                    provenance=provenance,
                )
            )
    return PointInTimeSecurityMaster.create(
        coverage_start=manifest.coverage_start,
        coverage_end=manifest.coverage_end,
        complete=manifest.complete and all(item.complete for item in manifest.sources),
        source_versions=(
            SecuritySourceVersion(source=item.source, version=item.source_version)
            for item in manifest.sources
        ),
        records=records,
    )


def _read_rows(path: Path) -> list[Mapping[str, object]]:
    if path.suffix.lower() == ".csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            return list(csv.DictReader(stream))
    if path.suffix.lower() == ".json":
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list) or not all(isinstance(row, dict) for row in value):
            raise SecurityMasterError("SECURITY_MASTER_JSON_ROWS_INVALID")
        return value
    if path.suffix.lower() == ".xlsx":
        openpyxl: Any = import_module("openpyxl")
        sheet = openpyxl.load_workbook(path, read_only=True, data_only=True).active
        values = sheet.iter_rows(values_only=True)
        try:
            header = tuple(str(value) for value in next(values))
        except StopIteration as exc:
            raise SecurityMasterError("SECURITY_MASTER_XLSX_EMPTY") from exc
        return [dict(zip(header, row, strict=True)) for row in values]
    raise SecurityMasterError("SECURITY_MASTER_FILE_TYPE_UNSUPPORTED")


def _normalize_row(row: Mapping[str, object]) -> dict[str, object]:
    required = {
        "security_id",
        "exchange",
        "symbol",
        "name",
        "board",
        "listing_date",
        "delisting_date",
        "effective_from",
        "effective_to",
        "status",
    }
    optional = {"source_url"}
    if not required <= set(row) or set(row) - required - optional:
        raise SecurityMasterError("SECURITY_MASTER_SOURCE_SCHEMA_INVALID")
    normalized = {
        key: None if key in {"name", "delisting_date", "effective_to"} and value == "" else value
        for key, value in row.items()
    }
    normalized["security_id"] = SecurityId(value=str(normalized["security_id"]))
    normalized["symbol"] = str(normalized["symbol"])
    return normalized


def _record_key(record: SecurityMasterRecord) -> tuple[str, date, str, date]:
    return (str(record.security_id), record.effective_from, record.symbol, record.listing_date)


def _validate_periods(records: tuple[SecurityMasterRecord, ...]) -> None:
    by_security: dict[str, list[SecurityMasterRecord]] = defaultdict(list)
    by_symbol: dict[tuple[Exchange, str], list[SecurityMasterRecord]] = defaultdict(list)
    for record in records:
        by_security[str(record.security_id)].append(record)
        by_symbol[(record.exchange, record.symbol)].append(record)
    for grouped in (*by_security.values(), *by_symbol.values()):
        ordered = sorted(grouped, key=lambda item: item.effective_from)
        for previous, current in pairwise(ordered):
            if previous.effective_to is None or current.effective_from <= previous.effective_to:
                raise ValueError("SECURITY_MASTER_EFFECTIVE_PERIOD_OVERLAP")
    for grouped in by_security.values():
        ordered = sorted(grouped, key=lambda item: item.effective_from)
        first, last = ordered[0], ordered[-1]
        if first.effective_from != first.listing_date:
            raise ValueError("SECURITY_MASTER_HISTORY_GAP")
        identity_dates = {(item.listing_date, item.delisting_date) for item in ordered}
        if len(identity_dates) != 1:
            raise ValueError("SECURITY_MASTER_IDENTITY_DATE_MISMATCH")
        for previous, current in pairwise(ordered):
            assert previous.effective_to is not None
            if current.effective_from != previous.effective_to + timedelta(days=1):
                raise ValueError("SECURITY_MASTER_HISTORY_GAP")
        if last.delisting_date is None and last.effective_to is not None:
            raise ValueError("SECURITY_MASTER_HISTORY_GAP")
        if last.delisting_date is not None and last.effective_to != last.delisting_date:
            raise ValueError("SECURITY_MASTER_HISTORY_GAP")
