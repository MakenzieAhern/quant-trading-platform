from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.data.catalog import (
    DatasetRevisionError,
    LocalDatasetCatalog,
    finalize_manifest,
    load_manifest,
    verify_dataset,
    write_manifest,
)
from app.data.catalog.normalized import write_canonical_csv, write_canonical_parquet
from app.data.providers.research import DailyBarRecord
from app.domain.markets import Exchange, SecurityId


def _build_dataset(root: Path, *, close: Decimal = Decimal("10.20")) -> str:
    dataset_id = "cn-a-test-2024"
    dataset_root = root / dataset_id
    partition = write_canonical_csv(
        dataset_root / "daily-bars.csv",
        fieldnames=("security_id", "trading_date", "raw_close"),
        rows=(
            {
                "security_id": "CN-A:SSE:600000",
                "trading_date": date(2024, 1, 3),
                "raw_close": close,
            },
            {
                "security_id": "CN-A:SSE:600000",
                "trading_date": date(2024, 1, 2),
                "raw_close": Decimal("10.1"),
            },
        ),
        sort_keys=("security_id", "trading_date"),
    )
    manifest = finalize_manifest(
        {
            "dataset_id": dataset_id,
            "provider": "fixture",
            "provider_version": "1",
            "retrieval_timestamp": datetime(2024, 1, 4, tzinfo=UTC),
            "coverage_start": date(2024, 1, 2),
            "coverage_end": date(2024, 1, 3),
            "security_count": 1,
            "symbols": ("600000",),
            "exchanges": (Exchange.SSE,),
            "fields": ("raw_close",),
            "adjustment_method": "none",
            "rule_version": "fixture-rules-1",
            "source_lineage": ("fixture",),
            "partitions": (partition,),
            "known_limitations": ("test fixture only",),
        }
    )
    write_manifest(dataset_root / "manifest.json", manifest)
    return dataset_id


def test_csv_and_manifest_are_deterministic_and_verifiable(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_id = _build_dataset(first)
    second_id = _build_dataset(second)

    first_manifest = load_manifest(first / first_id / "manifest.json")
    second_manifest = load_manifest(second / second_id / "manifest.json")
    assert first_manifest.canonical_sha256 == second_manifest.canonical_sha256
    assert (first / first_id / "daily-bars.csv").read_bytes() == (
        second / second_id / "daily-bars.csv"
    ).read_bytes()
    assert LocalDatasetCatalog(first).get(first_id) == first_manifest


def test_partition_revision_is_detected(tmp_path: Path) -> None:
    dataset_id = _build_dataset(tmp_path)
    dataset_root = tmp_path / dataset_id
    (dataset_root / "daily-bars.csv").write_text("changed\n", encoding="utf-8")
    manifest = load_manifest(dataset_root / "manifest.json")
    with pytest.raises(DatasetRevisionError, match="DATASET_CHECKSUM_MISMATCH"):
        verify_dataset(dataset_root, manifest)


def test_parquet_is_deterministic_without_index_or_writer_metadata_in_logical_hash(
    tmp_path: Path,
) -> None:
    rows = (
        {
            "security_id": "CN-A:SSE:600001",
            "trading_date": date(2024, 1, 3),
            "value": Decimal("1.2300"),
            "nullable": None,
            "timestamp": datetime(2024, 1, 3, 8, tzinfo=UTC),
        },
        {
            "security_id": "CN-A:SSE:600000",
            "trading_date": date(2024, 1, 2),
            "value": Decimal("2.00"),
            "nullable": "",
            "timestamp": datetime(2024, 1, 2, 16, tzinfo=UTC),
        },
    )
    fields = ("security_id", "trading_date", "value", "nullable", "timestamp")
    first = write_canonical_parquet(
        tmp_path / "first.parquet",
        fieldnames=fields,
        rows=rows,
        sort_keys=("security_id", "trading_date"),
    )
    second = write_canonical_parquet(
        tmp_path / "second.parquet",
        fieldnames=fields,
        rows=reversed(rows),
        sort_keys=("security_id", "trading_date"),
    )
    assert first.logical_sha256 == second.logical_sha256
    assert first.sha256 == second.sha256
    assert (tmp_path / "first.parquet").read_bytes() == (tmp_path / "second.parquet").read_bytes()


def test_normalized_writer_rejects_naive_timestamps(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timezone"):
        write_canonical_parquet(
            tmp_path / "invalid.parquet",
            fieldnames=("timestamp",),
            rows=({"timestamp": datetime(2024, 1, 1)},),
            sort_keys=("timestamp",),
        )


def test_manifest_cannot_be_silently_replaced(tmp_path: Path) -> None:
    dataset_id = _build_dataset(tmp_path)
    path = tmp_path / dataset_id / "manifest.json"
    existing = load_manifest(path)
    changed = existing.model_copy(update={"provider_version": "2"})
    with pytest.raises(DatasetRevisionError, match="immutable"):
        write_manifest(path, changed)


def test_malformed_ohlc_is_rejected() -> None:
    with pytest.raises(ValidationError, match="raw_high"):
        DailyBarRecord(
            security_id=SecurityId(value="CN-A:SSE:600000"),
            trading_date=date(2024, 1, 2),
            raw_open=Decimal("10"),
            raw_high=Decimal("9"),
            raw_low=Decimal("8"),
            raw_close=Decimal("10"),
            volume=Decimal("100"),
        )
