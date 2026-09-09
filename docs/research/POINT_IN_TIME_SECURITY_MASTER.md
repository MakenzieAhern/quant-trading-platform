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

The exchange files must contain exactly these columns:

```text
security_id,exchange,symbol,name,board,listing_date,delisting_date,effective_from,effective_to,status
```

Dates use `YYYY-MM-DD`; nullable values are empty. Symbols in spreadsheets must be text so leading
zeroes survive. Status is `LISTED`, `DELISTED`, `SUSPENDED` or `UNKNOWN`. Board is one of
`SSE_MAIN`, `SSE_STAR`, `SZSE_MAIN`, `SZSE_CHINEXT`.

The input manifest declares `coverage_start`, `coverage_end`, global `complete`, and two source
objects containing `source` (`SSE_OFFICIAL` or `SZSE_OFFICIAL`), `source_version`, filename, actual
file `sha256`, official `source_url`, UTC `retrieval_timestamp`, and source-level `complete`. A false
or missing completeness declaration blocks universe queries.

Run `make audit-universe`. A successful audit writes immutable `securities.parquet`, `manifest.json`
and a persisted `audit-report.json` outside Git. Reversed input order must yield the same master and
snapshot checksums.

## Current official-source boundary

The [SSE public-data directory](https://www.sse.com.cn/market/publicdata/) identifies stock and
paused/terminated-company lists, and the
[SSE terminated-company page](https://star.sse.com.cn/assortment/stock/list/delisting/) exposes an
official download surface. SZSE publishes official listing and termination notices in its
[listed-company notices](https://www.szse.cn/disclosure/notice/company/index.html). No free,
machine-readable export found in this pass proved complete point-in-time coverage for all SSE and
SZSE A-shares and exits from 2010 through 2025. Notices and annual factbooks are valid evidence but
must be normalized and reconciled before the source can declare `complete: true`.

The required manual input is therefore an official SSE export and an official SZSE export covering
all A-share listings and terminations effective during 2010-01-01 through 2025-12-31, with source
URLs/download references retained. Third-party current-stock lists are not acceptable substitutes.
