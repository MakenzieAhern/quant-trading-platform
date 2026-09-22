# Dataset Manifest Contract

Every research dataset is immutable and stored outside Git under `data/research/<dataset-id>/`.
Its canonical JSON manifest records schema version, dataset ID, provider and version, UTC retrieval
time, coverage, sorted security symbols/exchanges, fields, adjustment method, market-rule version,
source lineage, known limitations, partition row counts, byte SHA-256 and logical SHA-256 hashes,
plus aggregate logical-content and canonical manifest SHA-256 values. Paths must be relative POSIX
paths and cannot escape the dataset root.

Canonical CSV and Parquet share one normalization path: fixed column order; security/date sort keys;
exact base-10 Decimal strings; distinct nulls; ISO dates; timestamps normalized to UTC `Z`; and no
index column. Parquet uses a fixed Arrow string schema, Zstandard level 3, no dictionary encoding or
statistics, and Parquet 2.6/data-page 1.0 settings.

The byte hash detects file mutation. The logical hash covers canonical columns and normalized rows,
so it is independent of non-semantic writer metadata. The aggregate logical hash covers ordered
partition paths, row counts and logical hashes. The canonical manifest hash additionally protects
provider/retrieval/provenance metadata. Tests prove identical inputs and reversed input order produce
identical logical and byte checksums under the locked PyArrow version.
