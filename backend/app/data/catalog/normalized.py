import csv
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import sha256_file
from app.data.catalog.models import DatasetPartition


def write_canonical_csv(
    path: Path,
    *,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
    sort_keys: Sequence[str],
) -> DatasetPartition:
    normalized = [{field: _encode_value(row.get(field)) for field in fieldnames} for row in rows]
    normalized.sort(key=lambda row: tuple(row[key] for key in sort_keys))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(normalized)
    return DatasetPartition(
        relative_path=path.name,
        media_type="text/csv",
        row_count=len(normalized),
        sha256=sha256_file(path),
    )


def _encode_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)
