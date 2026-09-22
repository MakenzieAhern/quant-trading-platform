# A-Share Security Master Pilot Audit

Status: **PASS_FOR_PILOT**

Pilot coverage: 2023-01-01 through 2024-07-31

Assessment date: 2026-09-10

The normalized master contains 5,178 securities: 2,287 SSE and 2,891 SZSE. It includes 276
pilot-period IPOs, 72 pilot-period delistings, and 70 post-pilot delistings that were active during
the pilot. There are zero source conflicts, unresolved records, missing-provenance records,
yearbook baseline differences, duplicate active identities, or exchange/board mapping failures.

The security-master checksum is
`d4b02d6934eed85fa8588c65c688de20cb39ee871c17044e41a27c63c140f0ba`. Reversing input order
produces the same checksum. The 192-source raw snapshot manifest checksum is
`71eb74289b6682a3b65cb680872e43d60c86ee3a29b5ecbc16b7344483cee6c1`.

## Official evidence

- SSE current Main Board and STAR Market data come from the public JSON endpoint used by the
  [SSE stock list](https://www.sse.com.cn/assortment/stock/list/share/).
- SSE exited securities come from the endpoint used by the
  [SSE terminated-company list](https://www.sse.com.cn/assortment/stock/list/delisting/).
- SZSE current securities come from the official XLSX download on the
  [SZSE stock list](https://www.szse.cn/market/product/stock/list/index.html).
- SZSE termination decisions come from the
  [SZSE company notices](https://www.szse.cn/disclosure/notice/company/index.html); issuer final
  delisting PDFs come from the
  [SZSE listed-company disclosures](https://www.szse.cn/disclosure/listed/notice/index.html).
- The reconstructed 2022-12-31 SZSE A-share baseline exactly matches 2,736 A-share codes in the
  official [SZSE 2022 Fact Book](https://docs.static.szse.cn/www/market/periodical/year/W020230915392900565815.pdf).

No manual input or third-party security list was used. Seven B-share rows in the fact book are
excluded by their official B-share short names. The voluntary merger exit of `002013` is retained
through the 2023-03-17 effective termination date in the
[official decision](https://www.szse.cn/disclosure/notice/company/t20230315_599254.html).

## Deterministic boundary checks

- 72/72 exited securities checked inside coverage remain eligible before exit.
- 72/72 pilot-period exits are excluded after exit.
- 276/276 pilot IPOs are excluded before listing.
- Stable IDs, official exchange/board classifications, per-record source URLs, source-file hashes,
  raw filenames, retrieval metadata, parser version, normalized checksums, and input-order
  reproducibility pass.

The machine-readable report is stored outside Git at
`/home/yuchen/data/research/security-master-pilot-audit/audit-report.json`; the immutable normalized
Parquet snapshot is alongside it under `security-master-d4b02d6934ee/`.

This result is intentionally limited to the pilot interval. Full 2010-2025 historical-universe
readiness remains **PARTIAL**.
