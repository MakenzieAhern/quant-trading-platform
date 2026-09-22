import csv
from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, date, datetime
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any

from app.data.catalog.checksums import canonical_sha256, sha256_file
from app.data.catalog.freeze import require_unfrozen
from app.data.catalog.models import DatasetPartition


def write_canonical_csv(
    path: Path,
    *,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
    sort_keys: Sequence[str],
) -> DatasetPartition:
    require_unfrozen(path)
    normalized = _canonical_rows(fieldnames, rows, sort_keys)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(
            {key: "" if value is None else value for key, value in row.items()}
            for row in normalized
        )
    return DatasetPartition(
        relative_path=path.name,
        media_type="text/csv",
        row_count=len(normalized),
        sha256=sha256_file(path),
        logical_sha256=_logical_hash(fieldnames, normalized),
    )


def write_canonical_parquet(
    path: Path,
    *,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
    sort_keys: Sequence[str],
) -> DatasetPartition:
    """Write normalized strings/nulls with a metadata-independent logical hash."""
    require_unfrozen(path)
    pa: Any = import_module("pyarrow")
    parquet: Any = import_module("pyarrow.parquet")
    normalized = _canonical_rows(fieldnames, rows, sort_keys)
    schema = pa.schema(tuple(pa.field(field, pa.string(), nullable=True) for field in fieldnames))
    table = pa.Table.from_pylist(normalized, schema=schema)
    path.parent.mkdir(parents=True, exist_ok=True)
    parquet.write_table(
        table,
        path,
        compression="zstd",
        compression_level=3,
        use_dictionary=False,
        write_statistics=False,
        version="2.6",
        data_page_version="1.0",
        store_schema=True,
    )
    return DatasetPartition(
        relative_path=path.name,
        media_type="application/vnd.apache.parquet",
        row_count=len(normalized),
        sha256=sha256_file(path),
        logical_sha256=_logical_hash(fieldnames, normalized),
    )


def _canonical_rows(
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
    sort_keys: Sequence[str],
) -> list[dict[str, str | None]]:
    fields = tuple(fieldnames)
    if len(fields) != len(set(fields)) or any(key not in fields for key in sort_keys):
        raise ValueError("field names must be unique and include every sort key")
    normalized = [{field: _encode_value(row.get(field)) for field in fields} for row in rows]
    normalized.sort(key=lambda row: tuple((row[key] is None, row[key] or "") for key in sort_keys))
    return normalized


def _logical_hash(fieldnames: Sequence[str], rows: list[dict[str, str | None]]) -> str:
    return canonical_sha256({"fields": tuple(fieldnames), "rows": rows})


def _encode_value(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must include a timezone")
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)
