import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.models import DatasetManifest, DatasetRevisionError


def finalize_manifest(values: dict[str, Any]) -> DatasetManifest:
    candidate_values = {**values, "canonical_sha256": "0" * 64}
    candidate = DatasetManifest.model_validate(candidate_values)
    checksum = canonical_sha256(candidate.canonical_payload())
    return candidate.model_copy(update={"canonical_sha256": checksum})


def write_manifest(path: Path, manifest: DatasetManifest) -> None:
    if path.exists():
        existing = load_manifest(path)
        if existing != manifest:
            raise DatasetRevisionError(
                "immutable dataset manifest already exists with other content"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(manifest.model_dump(mode="json")) + b"\n")


def load_manifest(path: Path) -> DatasetManifest:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        manifest = DatasetManifest.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise DatasetRevisionError("dataset manifest is invalid") from exc
    expected = canonical_sha256(manifest.canonical_payload())
    if manifest.canonical_sha256 != expected:
        raise DatasetRevisionError("DATASET_CHECKSUM_MISMATCH")
    return manifest


def verify_dataset(dataset_root: Path, manifest: DatasetManifest) -> None:
    resolved_root = dataset_root.resolve()
    for partition in manifest.partitions:
        candidate = (resolved_root / partition.relative_path).resolve()
        if not candidate.is_relative_to(resolved_root):
            raise DatasetRevisionError("partition escapes dataset root")
        if not candidate.is_file() or sha256_file(candidate) != partition.sha256:
            raise DatasetRevisionError("DATASET_CHECKSUM_MISMATCH")
