# P0 public reconstruction report V1

As of 2026-09-15, the two P0 paid-export requirements are resolved as fact
sets by `OFFICIAL_PUBLIC_SOURCE_RECONSTRUCTION_V1`. No paid product was used.
The normalized core master covers 2010-01-01 through 2025-12-31; annual
exchange membership is independently reconciled against official SSE and SZSE
yearbooks, including historically delisted securities.

| Measure | Result |
| --- | ---: |
| SSE expected / reconstructed / missing securities | 2,403 / 2,403 / 0 |
| SZSE expected / reconstructed / missing securities | 3,028 / 3,028 / 0 |
| Exactly corroborated facts | 21,556 |
| Single-official-source facts | 16,730 |
| Official-source conflicts | 0 |
| Temporal-boundary ambiguities | 5,431 |
| True unresolved P0 facts | 0 |
| Delisted securities retained | 269 |

The 5,431 boundary ambiguities are one historical display-name interval per
security. They are explicitly non-material to core membership, lifecycle,
board, stable identity and code, and do not supply ST state. ST and `*ST`
remain governed by their separate effective-dated official event ledgers.

Acceptance:

- `P0_SSE_STATUS = PASS_PUBLIC_OFFICIAL_RECONSTRUCTION`
- `P0_SZSE_STATUS = PASS_PUBLIC_OFFICIAL_RECONSTRUCTION`
- `SECURITY_MASTER_CORE_AUTHORITY = PASS`
- `SURVIVORSHIP_SAFE_MASTER = PASS`
- `FUTURE_IPO = PASS`
- `DELISTING_RETENTION = PASS`
- `STABLE_IDENTITY = PASS`
- `INPUT_ORDER_REPRODUCIBILITY = PASS`

Immutable artifacts:

- `/home/yuchen/data/research/staging/full-master-public-v1-final/point-in-time-security-master.json`
  - file SHA-256: `02f1a2bb145d1d9c98c4d9678bad687a8a4c4ece6f6419f12da939b66507b363`
  - canonical master SHA-256: `c1a78056947232249fa4b139dd4d4ceb09636cd221863d7e64a0a56574ae1b48`
- `/home/yuchen/data/research/staging/full-master-public-v1-final/p0-public-reconstruction-report-v1.json`
  - file SHA-256: `ee043f8e71079117629063a4df3fc906b4d65b973621e0b3aae3cea6932427e6`
  - canonical manifest SHA-256: `3b80a13fb816ce8b9f3442d57a4b84ae31f7616d7c89235cc6d98e12a8150faf8`

Every source row preserves the official URL, HTTP status and headers,
retrieval timestamp UTC, raw SHA-256 and parser version. The full annual
reconciliation and source-provenance rows are in the immutable JSON report.
