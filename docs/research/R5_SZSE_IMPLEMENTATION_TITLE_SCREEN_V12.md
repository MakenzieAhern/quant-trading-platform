# R5 SZSE implementation-title screen v12

Date: 2026-09-19

## Scope

This bounded screen tested two previously unprocessed, high-information title
families from the v11 SZSE resumption residual. It reused the retained CNINFO
metadata join and acquired only documents already bound to an unresolved
suspension event. It did not restart acquisition or expand into the 74,569
low-precision residual leads.

| Batch | Exact title family | Official PDFs | Failures | Exact-date documents | Accepted boundaries |
|---|---|---:|---:|---:|---:|
| v6 | Share-reform implementation, merger cash-option result, asset-purchase implementation/result, reorganisation completion | 17 | 0 | 1 | 0 |
| v7 | Share-change/additional-share listing notices | 23 | 0 | 0 | 0 |
| Total | — | 40 | 0 | 1 | 0 |

All 40 documents were fetched from official CNINFO URLs, checksum-bound and
parsed from the acquired PDF bytes.

## Exact-date review

The only exact-date document is CN-A:SZSE:000509's 2014-01-07
`股权分置改革方案实施公告`. It states a 2014-01-09 resumption and is bound to the
2013-12-19 halt. It is not accepted as closure because the official suspension
ledger contains a distinct new halt for 000509 at 2014-01-09 09:30. The
document therefore does not prove a tradable interval after the earlier halt;
accepting it would hide the same-day re-halt.

- official URL: `https://static.cninfo.com.cn/finalpage/2014-01-07/63460200.PDF`
- PDF SHA-256: `331936b0998af1c697f73b66e63347bf7f024d85824b87d04c023bdb8e5f4564`
- classification: exact date found, rejected as a new accepted boundary

The other 39 documents do not state an exact official resumption date for the
bound suspension event. Listing or implementation language is not treated as
proof of trading resumption.

## Deterministic evidence

### Batch v6

- priority queue SHA-256: `9285fa897df43844ccd9d3b86507eacbb98f76f0e791528213707bbf8b4ec12e`
- priority report SHA-256: `7cf25d998a6f823143fb8fe0e61372a95ac51414b18b27ed6f8739b3ac32fae3`
- priority report manifest: `78a08bee06b428dcb279b771fd00ebbc71bf2875de3d4531087a07ea500dd657`
- source manifest SHA-256: `29c3767d82a0b7b9a19af9942d5837b14c2966634dbf8d81aa3167e26c263385`
- source report manifest: `099768130b35a551347c7c893a1e8f5067d4466bd5694c0a635b006ed7fcf5d4`
- reconciliation file SHA-256: `31a8af0f617c302ae0061dc20713b4bf4ba7e2dc0fda83810134eee500de4a1d`
- reconciliation manifest: `14f11c3b03ac5de1847c26dbce7f9776f0833306ec5ad46c2828ef95b67f3eff`

### Batch v7

- priority queue SHA-256: `b69f7b1c422f03eccd4b5fc45fe6a69c4d04184d59c573a9241867356b4f29f0`
- priority report SHA-256: `1d05865622544fce076f6de5ea49331910259c5346322267cdcb72569916df93`
- priority report manifest: `24239a68f2e5e39d1c2788be5180c108266c77fb55f90e3962573b7610e7c859`
- source manifest SHA-256: `782a837f116b550a59511d8c70a41058599ba8a4f782a2042ae1891895c1f75a`
- source report manifest: `55108b581cbdf8c5b1e8828591a89913e9a3d9bea68bd269bb9d2f9dffa6dc50`
- reconciliation file SHA-256: `a8329eba803c46e4762dc3b2e7f7e9e832e9e244a756009c7c6f176ed81a5431`
- reconciliation manifest: `eaa11653420cdcad8a3237c72c32ce2539b5de878992e440504fd1a8c63f95aa`

## Decision

The bounded implementation/listing title route is exhausted with zero new
accepted boundaries. Blind bulk retrieval of the remaining low-precision
metadata leads is not justified by this zero-yield screen.

Authoritative counts remain:

- exact SZSE resumptions: 7,303
- terminal closures: 58
- unresolved exact SZSE boundaries: 3,444
- conflicts: 0
- suspension authority: `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`

No Full Dataset was created or frozen, and no Development, Validation or
Official OOS study was run.
