from pathlib import Path

from app.data.catalog.manifest import load_manifest, verify_dataset
from app.data.catalog.models import DatasetManifest


class DatasetNotFoundError(LookupError):
    pass


class LocalDatasetCatalog:
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()

    def get(self, dataset_id: str) -> DatasetManifest:
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789._-"
        if not dataset_id or any(character not in allowed for character in dataset_id):
            raise DatasetNotFoundError("RESEARCH_DATASET_NOT_FOUND")
        dataset_root = (self._root / dataset_id).resolve()
        if not dataset_root.is_relative_to(self._root):
            raise DatasetNotFoundError("RESEARCH_DATASET_NOT_FOUND")
        manifest_path = dataset_root / "manifest.json"
        if not manifest_path.is_file():
            raise DatasetNotFoundError("RESEARCH_DATASET_NOT_FOUND")
        manifest = load_manifest(manifest_path)
        if manifest.dataset_id != dataset_id:
            raise DatasetNotFoundError("RESEARCH_DATASET_NOT_FOUND")
        verify_dataset(dataset_root, manifest)
        return manifest
