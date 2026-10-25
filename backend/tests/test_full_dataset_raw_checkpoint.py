"""Real temporary JSON/XLSX/Parquet; never open the retained market archive."""

import json
import os
from decimal import ROUND_UP, Decimal, localcontext
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from app.data.catalog.checksums import sha256_file
from scripts import materialize_full_dataset as materializer


def _source(path: Path, exchange: str, day: str, close: int = 10, volume: float = 1) -> None:
    if exchange == "SSE":
        path.write_text(json.dumps({"kline": [[day, 10, 12, 9, close, 100, 1000]]}))
    else:
        workbook = Workbook()
        sheet = workbook.active
        sheet.append(
            [
                "交易日期",
                "证券代码",
                "证券简称",
                "前收",
                "开盘",
                "最高",
                "最低",
                "今收",
                "涨跌幅\uff08%\uff09",
                "成交量(万股)",
                "成交金额(万元)",
                "市盈率",
            ]
        )
        sheet.append([day, "000001", "fixture", 10, 10, 12, 9, close, 0, volume, 10, 5])
        workbook.save(path)
        workbook.close()
    path.with_suffix(path.suffix + ".meta.json").write_text(
        json.dumps(
            {
                "sha256": sha256_file(path),
                "url": "https://example.invalid/isolated-test",
                "retrieved_at_utc": "2026-10-08T00:00:00Z",
            }
        )
    )


def _inputs(
    root: Path, exchange: str
) -> tuple[list[Path], list[dict[str, Any]], list[dict[str, Any]]]:
    root.mkdir()
    symbols = ["600001", "600002"] if exchange == "SSE" else ["000001", "000002"]
    paths = []
    for index, symbol in enumerate(symbols):
        day = f"2010-01-0{index + 4}"
        path = root / (f"{symbol}.json" if exchange == "SSE" else f"{day}.xlsx")
        _source(path, exchange, day.replace("-", "") if exchange == "SSE" else day)
        paths.append(path)
    master = [
        {
            "exchange": exchange,
            "symbol": symbol,
            "effective_from": "2009-01-01",
            "effective_to": None,
            "security_id": f"CN-A:{exchange}:{symbol}",
        }
        for symbol in symbols
    ]
    statuses = [
        {
            "security_id": row["security_id"],
            "effective_from": "2010-01-01",
            "effective_to": "2025-12-31",
            "status": "NORMAL",
        }
        for row in master
    ]
    return paths, master, statuses


def _run(build: Path, exchange: str, inputs: tuple) -> tuple:
    paths, master, statuses = inputs
    return materializer.raw_stage(
        build,
        exchange,
        paths,
        materializer.SecurityResolver(master),
        materializer.StatusResolver(statuses),
    )


def _snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256_file(path) for path in root.rglob("*") if path.is_file()
    }


@pytest.mark.parametrize("exchange", ["SSE", "SZSE"])
def test_raw_checkpoint_repeats_with_reordered_inputs(tmp_path: Path, exchange: str) -> None:
    inputs = _inputs(tmp_path / "sources", exchange)
    build = tmp_path / "build"
    first = _run(build, exchange, inputs)
    before = _snapshot(build)
    assert _run(build, exchange, tuple(list(reversed(rows)) for rows in inputs)) == first
    assert _snapshot(build) == before
    assert _run(tmp_path / "fresh", exchange, inputs) == first
    assert _snapshot(tmp_path / "fresh") == before
    row = pq.read_table(build / first[0][0].relative_path).to_pylist()[0]
    assert row["raw_close"] == "10" and row["risk_status"] == "NORMAL"
    assert row["volume"] == ("100" if exchange == "SSE" else "10000")


@pytest.mark.parametrize("exchange", ["SSE", "SZSE"])
@pytest.mark.parametrize(
    "change",
    ["raw", "metadata", "master", "lifecycle", "status", "paths", "parser", "end", "fields"],
)
def test_raw_checkpoint_rejects_changed_inputs(
    tmp_path: Path, exchange: str, change: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path / "sources", exchange)
    build = tmp_path / "build"
    _run(build, exchange, inputs)
    before = _snapshot(build)
    paths, master, statuses = inputs
    if change == "raw":
        _source(paths[0], exchange, "20100104" if exchange == "SSE" else "2010-01-04", 11)
    elif change == "metadata":
        path = paths[0].with_suffix(paths[0].suffix + ".meta.json")
        metadata = json.loads(path.read_bytes())
        metadata["url"] = "https://example.invalid/different-provenance"
        path.write_text(json.dumps(metadata))
    elif change == "master":
        master[0]["security_id"] += ":new-listing"
    elif change == "lifecycle":
        master[0]["effective_from"] = "2010-01-05"
    elif change == "status":
        statuses[0]["status"] = "STAR_ST"
    elif change == "paths":
        paths.pop()
    elif change == "parser":
        monkeypatch.setattr(materializer, "RAW_PARSER_VERSION", "changed", raising=False)
    elif change == "end":
        monkeypatch.setattr(materializer, "END", "2024-12-31")
    else:
        monkeypatch.setattr(materializer, "RAW_FIELDS", (*materializer.RAW_FIELDS, "changed"))
    with pytest.raises(ValueError, match="RAW_CHECKPOINT_INPUT_MISMATCH"):
        _run(build, exchange, inputs)
    assert _snapshot(build) == before


@pytest.mark.parametrize(
    "change", ["legacy", "missing-target", "missing-receipt", "extra", "partition", "lineage"]
)
def test_raw_checkpoint_rejects_incomplete_or_changed_receipt(tmp_path: Path, change: str) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    build = tmp_path / "build"
    _run(build, "SSE", inputs)
    receipt = build / "raw-sse-checkpoint.json"
    receipt.chmod(0o600)  # Deliberately tamper only with this disposable receipt.
    checkpoint = json.loads(receipt.read_bytes())
    if change == "legacy":
        checkpoint.pop("input_sha256", None)
        receipt.write_text(json.dumps(checkpoint))
    elif change == "missing-target":
        (build / "raw/SSE").rename(build / "retained-result")
    elif change == "missing-receipt":
        receipt.rename(build / "retained-receipt.json")
    elif change == "extra":
        (build / "raw/SSE/extra.parquet").write_bytes(b"unlisted")
    elif change == "partition":
        (build / "raw/SSE/2010-01.parquet").write_bytes(b"changed")
    else:
        checkpoint["lineage"][0]["source_url"] = "https://example.invalid/tampered"
        receipt.write_text(json.dumps(checkpoint))
    before = _snapshot(build)
    with pytest.raises(ValueError, match="RAW_CHECKPOINT"):
        _run(build, "SSE", inputs)
    assert _snapshot(build) == before


@pytest.mark.parametrize("resume", [False, True])
def test_raw_checkpoint_refuses_frozen_build(tmp_path: Path, resume: bool) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    build = tmp_path / "build"
    build.mkdir()
    if resume:
        _run(build, "SSE", inputs)
    (build / ".freeze.json").write_text("{}")
    before = _snapshot(build)
    with pytest.raises(ValueError, match="DATASET_FROZEN"):
        _run(build, "SSE", inputs)
    assert _snapshot(build) == before


def test_raw_units_do_not_inherit_callers_decimal_rounding(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path / "sources", "SZSE")
    _source(inputs[0][0], "SZSE", "2010-01-04", volume=1.23456)
    first = _run(tmp_path / "first", "SZSE", inputs)
    with localcontext() as context:
        context.prec = 3
        context.rounding = ROUND_UP
        second = _run(tmp_path / "second", "SZSE", inputs)
        assert second == first
        assert _run(tmp_path / "first", "SZSE", inputs) == first
        value = "123456789012345678901234567890.12"
        assert materializer.decimal_text(value) == value
    row = pq.read_table(tmp_path / "second" / second[0][0].relative_path).to_pylist()[0]
    assert Decimal(row["volume"]) == Decimal("12345.6")


def test_raw_metadata_cannot_be_deleted_as_incomplete_output(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    build = tmp_path / "build"
    incomplete = build / ".raw-sse.incomplete"
    incomplete.mkdir(parents=True)
    metadata = inputs[0][0].with_suffix(".json.meta.json")
    retained_metadata = incomplete / "metadata.json"
    metadata.rename(retained_metadata)
    metadata.symlink_to(retained_metadata)
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="RAW_SOURCE_OUTPUT_OVERLAP"):
        _run(build, "SSE", inputs)
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("exchange", ["SSE", "SZSE"])
def test_raw_source_change_during_parse_cannot_publish(
    tmp_path: Path, exchange: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = _inputs(tmp_path / "sources", exchange)
    original = materializer.verified_bytes

    def change_after_read(path: Path, expected: tuple[str, str] | None = None) -> tuple:
        result = original(path, expected)
        if path == inputs[0][0]:
            _source(path, exchange, "20100104" if exchange == "SSE" else "2010-01-04", 11)
        return result

    monkeypatch.setattr(materializer, "verified_bytes", change_after_read)
    build = tmp_path / "build"
    with pytest.raises(ValueError, match="RAW_CHECKPOINT_INPUT_MISMATCH"):
        _run(build, exchange, inputs)
    assert not (build / "raw" / exchange).exists()
    assert not (build / f"raw-{exchange.lower()}-checkpoint.json").exists()
    # In particular, XLSX parsing must use verified bytes, not reopen the changed path.
    row = pq.read_table(build / f".raw-{exchange.lower()}.incomplete/2010-01.parquet").to_pylist()[
        0
    ]
    assert row["raw_close"] == "10"


@pytest.mark.parametrize("location", ["build", "raw", "receipt", "incomplete", "receipt-tmp"])
def test_raw_output_symlinks_do_not_write_or_remove_targets(tmp_path: Path, location: str) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    build = tmp_path / "build"
    outside = tmp_path / "retained"
    outside.mkdir()
    (outside / "keep").write_bytes(b"retained")
    targets = {
        "build": build,
        "raw": build / "raw",
        "receipt": build / "raw-sse-checkpoint.json",
        "incomplete": build / ".raw-sse.incomplete",
        "receipt-tmp": build / "raw-sse-checkpoint.json.tmp",
    }
    target = targets[location]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(outside, target_is_directory=True)
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="UNSAFE_RAW_CHECKPOINT_PATH"):
        _run(build, "SSE", inputs)
    assert _snapshot(tmp_path) == before


def test_raw_incomplete_disposable_build_can_restart(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    build = tmp_path / "build"
    incomplete = build / ".raw-sse.incomplete"
    incomplete.mkdir(parents=True)
    (incomplete / "2010-01.parquet").write_bytes(b"interrupted")
    assert _run(build, "SSE", inputs) == _run(tmp_path / "fresh", "SSE", inputs)
    assert _snapshot(build) == _snapshot(tmp_path / "fresh")


@pytest.mark.parametrize("change", ["empty", "duplicate", "exchange", "unverified-source"])
def test_raw_invalid_input_does_not_create_output(tmp_path: Path, change: str) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    exchange = "SSE"
    if change == "empty":
        inputs[0].clear()
    elif change == "duplicate":
        inputs[0].append(inputs[0][0])
    elif change == "exchange":
        exchange = "../outside"
    else:
        inputs[0][0].write_bytes(b"unverified changed source")
    with pytest.raises(ValueError, match=r"INVALID_RAW_|SOURCE_CHECKSUM_CHANGED"):
        _run(tmp_path / "build", exchange, inputs)
    assert not (tmp_path / "build").exists()


@pytest.mark.parametrize("change", ["cross-exchange", "duplicate", "partition-symlink"])
def test_raw_checkpoint_checks_partition_paths_even_with_valid_receipt_hash(
    tmp_path: Path, change: str
) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    build = tmp_path / "build"
    _run(build, "SSE", inputs)
    receipt = build / "raw-sse-checkpoint.json"
    receipt.chmod(0o600)  # Deliberately tamper only with this disposable receipt.
    checkpoint = json.loads(receipt.read_bytes())
    if change == "cross-exchange":
        checkpoint["partitions"][0]["relative_path"] = "raw/SZSE/2010-01.parquet"
    elif change == "duplicate":
        checkpoint["partitions"].append(checkpoint["partitions"][0])
    else:
        partition = build / checkpoint["partitions"][0]["relative_path"]
        outside = tmp_path / "retained.parquet"
        partition.rename(outside)
        partition.symlink_to(outside)
    checkpoint.pop("checkpoint_sha256")
    checkpoint["checkpoint_sha256"] = materializer.canonical_sha256(checkpoint)
    receipt.write_text(json.dumps(checkpoint))
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError, match="RAW_CHECKPOINT"):
        _run(build, "SSE", inputs)
    assert _snapshot(tmp_path) == before


@pytest.mark.parametrize("source_kind", ["raw", "metadata"])
def test_raw_receipt_publication_never_overwrites_a_retained_input_hardlink(
    tmp_path: Path, source_kind: str
) -> None:
    inputs = _inputs(tmp_path / "sources", "SSE")
    build = tmp_path / "build"
    build.mkdir()
    source = inputs[0][0]
    if source_kind == "metadata":
        source = source.with_suffix(".json.meta.json")
    old_temporary = build / "raw-sse-checkpoint.json.tmp"
    os.link(source, old_temporary)
    before = _snapshot(tmp_path / "sources")
    expected = sha256_file(old_temporary)
    first = _run(build, "SSE", inputs)
    assert _snapshot(tmp_path / "sources") == before
    assert sha256_file(old_temporary) == expected
    assert _run(build, "SSE", inputs) == first
