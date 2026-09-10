# Point-in-Time A-Share Security Master

The security master is provider-neutral and fail-closed. BaoStock remains eligible for daily market
fields, but it is not accepted as sole evidence of the historical universe. Official SSE and SZSE
reference files are required before `eligible_universe(trading_date)` can return records.

Each normalized record contains stable `security_id`, exchange, symbol, name, board, listing and
delisting dates, effective dates, status, official source/version, retrieval timestamp, source-file
SHA-256, record SHA-256 and source URL. The master rejects source-version drift, duplicate or
overlapping identities, gaps in a security's effective history, backward IPO leakage and incomplete
source declarations. Delisted securities remain eligible through their delisting effective date.

## Official staging contract

Place exactly one file for each exchange in
`/home/yuchen/data/research/staging/security-master/`:

- `sse-security-master.csv`, `.json` or `.xlsx`
- `szse-security-master.csv`, `.json` or `.xlsx`
- `security-master-input.json`

The exchange files contain these required columns and may add row-level `source_url`:

```text
security_id,exchange,symbol,name,board,listing_date,delisting_date,effective_from,effective_to,status,source_url
```

Dates use `YYYY-MM-DD`; nullable values are empty. Symbols in spreadsheets must be text so leading
zeroes survive. Status is `LISTED`, `DELISTED`, `SUSPENDED` or `UNKNOWN`. Board is one of
`SSE_MAIN`, `SSE_STAR`, `SZSE_MAIN`, `SZSE_CHINEXT`.

The input manifest declares `coverage_start`, `coverage_end`, global `complete`, and two source
objects containing `source` (`SSE_OFFICIAL` or `SZSE_OFFICIAL`), `source_version`, filename, actual
file `sha256`, official `source_url`, UTC `retrieval_timestamp`, and source-level `complete`. A false
or missing completeness declaration blocks universe queries.

`source_url` falls back to the source manifest URL for compatible older files. Run
`backend/scripts/fetch_a_share_security_master.py` to capture and reconcile the official pilot
sources automatically, then run `make audit-universe`. A successful audit writes immutable
`securities.parquet`, `manifest.json` and a persisted `audit-report.json` outside Git. Reversed input
order must yield the same master and snapshot checksums.

## Current official-source boundary

The automated official-source reconstruction and 2022 SZSE fact-book reconciliation pass for the
2023-01-01 through 2024-07-31 pilot; see `A_SHARE_SECURITY_MASTER_PILOT_AUDIT.md`. This does not
declare complete point-in-time coverage for 2010 through 2025. Third-party current-stock lists are
not acceptable substitutes for that later expansion.
