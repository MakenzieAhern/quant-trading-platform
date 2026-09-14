"""Small immutable control records; catalog writers reject frozen ancestors."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from app.data.catalog.models import DatasetRevisionError

MARKER = ".freeze.json"


def require_unfrozen(path: Path) -> None:
    for parent in path.resolve().parents:
        if (parent / MARKER).exists():
            raise DatasetRevisionError("DATASET_FROZEN: correction requires a new dataset version")


def write_immutable(path: Path, content: bytes) -> None:
    """Publish complete bytes without replacing any existing record, including on races."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        # Windows cannot unlink a read-only temporary hard link.
        if os.name != "nt":
            temporary.chmod(0o444)
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != content:
                raise DatasetRevisionError("IMMUTABLE_RECORD_CHANGED") from None
    finally:
        temporary.unlink()
    if os.name == "nt":
        path.chmod(0o444)
