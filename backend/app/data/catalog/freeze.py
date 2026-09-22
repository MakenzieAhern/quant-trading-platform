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
        except OSError as exc:
            if os.name != "nt" or getattr(exc, "winerror", None) != 50:
                raise
            try:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
            except FileExistsError:
                if path.read_bytes() != content:
                    raise DatasetRevisionError("IMMUTABLE_RECORD_CHANGED") from None
            else:
                with os.fdopen(descriptor, "wb") as target:
                    target.write(content)
                    target.flush()
                    os.fsync(target.fileno())
    finally:
        temporary.unlink()
    if os.name == "nt":
        path.chmod(0o444)
