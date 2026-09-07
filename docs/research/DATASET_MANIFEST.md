# Dataset Manifest Contract

Every research dataset is immutable and stored outside Git under `data/research/<dataset-id>/`.
Its canonical JSON manifest records schema version, dataset ID, provider and version, UTC retrieval
time, coverage, sorted security symbols/exchanges, fields, adjustment method, market-rule version,
source lineage, known limitations, partition row counts and SHA-256 hashes, plus a canonical manifest
SHA-256. Paths must be relative POSIX paths and cannot escape the dataset root.

Canonical CSV values use ISO dates, exact base-10 decimal strings, `1`/`0` booleans, LF line endings,
fixed field order and deterministic row sorting. The catalog rejects manifest mutation, traversal,
missing partitions and checksum mismatches. Parquet is an allowed media type but deterministic
Parquet writing is not yet shipped; CSV is the currently verified canonical encoding.
