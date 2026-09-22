# R5 distribution notice recovery — in progress

Accepted Pilot v2, R4 and source/policy decisions remain unchanged.
Documents and query coverage are NOT accepted economic events.

The annual CNINFO implementation query completed 2010/2018/2019/2020 with
1,114/2,931/2,761/2,898 announcements. Canonical manifest SHA-256:
`f94d4546b79a68ca7a35e61268e5182ebf0c0927d37d0cdacaf9d5367cc89825`.
Twelve years retain explicit HTTP 502/504, timeout or repeated-page failures.
For 2023 and 2024, page 101 repeated page 1; neither year was accepted.

2010: 1,113 successful PDFs indexed, one HTTP 502 failure (601588,
announcement 58164210). Source manifest canonical SHA-256:
`8ac52513f9c268e5e00eda4a5a24e3edbc0161c2e339463a15e2c9135742a6fe`.
2018–2020: 8,590 document leads downloading resumably, reusing verified PDFs
from prior rights, merger and SSE source roots.
External root: `/home/yuchen/data/research/staging/full-distribution-notices-v1`.

Missing-range recovery verifies retained manifest/page checksums and descending
publication order. It reuses later-year pages, querying only missing earlier
dates in monthly windows. The partially retrieved boundary day is included;
duplicates reconcile by announcement ID/source identity. The union must match
the original annual total. Completed years are never re-requested.
Two workers, bounded pages, immutable per-year receipts and explicit failures;
no repeated-page, identity-conflict or date-leakage acceptance.
2011 and 2012 recovered totals: 1,468 and 1,780, each matching the original.
External checkpoints/manifests are authoritative for subsequent progress.

566 backend tests/Ruff/format/mypy passed including missing-range recovery.
The new recovery regression checks partial-day coverage, input order,
identity conflicts and missing counts; focused source suite 11 PASS.
Official rounded merger ratio regression: 000562 ratio 2.049382716 gives
floor(81 * ratio) = 165, not 166 from an unrounded price quotient.
This arithmetic check does not accept a new merger lifecycle.

Exact issuer terms, dates, holder classes, corrections and exchange census
reconciliation remain required. R5 RUNNING_BATCH_CLOSURE; full dataset
CREATED/AUDITED/FROZEN=NO, safe start NOT_ESTABLISHED. No new methodology gate,
strategy study, profitability inspection, PR merge or release.
