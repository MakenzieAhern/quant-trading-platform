import json
from pathlib import Path

import pytest

from app.data.catalog import DatasetRevisionError, load_manifest, write_manifest
from app.data.catalog.freeze import MARKER, write_immutable
from app.data.catalog.normalized import write_canonical_csv, write_canonical_parquet
from tests.test_research_data_catalog import _build_dataset


def test_frozen_catalog_rejects_every_shared_writer(tmp_path: Path) -> None:
    root = tmp_path / _build_dataset(tmp_path)
    manifest = load_manifest(root / "manifest.json")
    before = (root / "daily-bars.csv").read_bytes()
    write_immutable(root / MARKER, b"freeze-control\n")
    for writer, name in (
        (write_canonical_csv, "daily-bars.csv"),
        (write_canonical_parquet, "new/partition.parquet"),
    ):
        with pytest.raises(DatasetRevisionError, match="DATASET_FROZEN"):
            writer(root / name, fieldnames=("id",), rows=({"id": 1},), sort_keys=("id",))
    with pytest.raises(DatasetRevisionError, match="DATASET_FROZEN"):
        write_manifest(root / "manifest.json", manifest)
    assert (root / "daily-bars.csv").read_bytes() == before
    assert not (root / "new").exists()
    # A correction remains possible only in another dataset directory/version.
    write_canonical_csv(
        tmp_path / "v2/bars.csv", fieldnames=("id",), rows=({"id": 1},), sort_keys=("id",)
    )


def test_control_record_is_atomic_idempotent_and_not_replaceable(tmp_path: Path) -> None:
    path = tmp_path / "record.json"
    write_immutable(path, b"original")
    write_immutable(path, b"original")
    with pytest.raises(DatasetRevisionError, match="IMMUTABLE_RECORD_CHANGED"):
        write_immutable(path, b"replacement")
    assert path.read_bytes() == b"original"
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("changed", ["review", "context"])
def test_revised_freeze_rejects_changed_approved_evidence(tmp_path: Path, changed: str) -> None:
    from app.data.catalog.checksums import sha256_file
    from scripts.freeze_pilot import freeze

    dataset = tmp_path / "cn-a-pilot-akshare-20230101-20240731-v2"
    dataset.mkdir()
    approvals = tmp_path / ".research/approvals"
    reports = tmp_path / ".research/reports"
    build = tmp_path / "pilot-v2-build"
    for directory in (approvals, reports, build):
        directory.mkdir(parents=True)
    paths = {
        "review": reports / "revised-pilot-v2.json",
        "context": build / "revision-context.json",
    }
    for path in paths.values():
        path.write_text("{}")
    (approvals / "gate-a-pilot-v2.json").write_text(
        json.dumps(
            dict(
                decision="APPROVED",
                dataset_id=dataset.name,
                review_sha256=sha256_file(paths["review"]),
                context_sha256=sha256_file(paths["context"]),
            )
        )
    )
    paths[changed].write_text('{"changed": true}')
    with pytest.raises(ValueError, match="PRE_FREEZE_APPROVED_V2_EVIDENCE_CHANGED"):
        freeze(tmp_path, dataset, tmp_path)
    assert not (dataset / MARKER).exists()
    assert not (tmp_path / ".research/freezes").exists()
