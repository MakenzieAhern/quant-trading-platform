# R5 full-range source extension — 2026-09-13

R5 remains RUNNING_BATCH_CLOSURE. These are independently verified source and
engineering milestones, not full-dataset acceptance. Accepted Pilot v2, R4,
stock-price/adjustment authorities and the frozen policy catalog are unchanged.

## Calendar and benchmark

The existing pinned Sina calendar snapshot and accepted decoder produce 3,886
sessions, 2010-01-04 through 2025-12-31. Dates after the target end are excluded;
pre-start listing-age history remains available. Calendar manifest:
`/home/yuchen/data/research/staging/full-calendar-v1/calendar-manifest-v3.json`,
canonical SHA-256
`d3c681d7d2020d3c7a8111d9600092e79a18ff28234b02e5f5020644506620b8`.

Full-range Eastmoney benchmark requests failed from WSL and Windows; receipts
remain preserved. The official CSI public index-performance endpoint recovered
the same CSI300 price index, not another benchmark or a total-return series:
https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=000300&startDate=20100104&endDate=20251231

The first request starting on the January 1 holiday returned one extra duplicate
January 4 payload under January 1. Both raw responses are retained. The canonical
request starts on the actual first session; no row date is rewritten or filled.
All 3,886 sessions align exactly; all 382 accepted Pilot closes match numerically.
OHLC validity, reverse-order replay and Parquet checksum repeatability PASS.
Close-series authority = PASS_FOR_FULL_RANGE_CLOSE_SERIES. This does not accept
index volume/amount or change raw stock execution prices.

Benchmark manifest:
`/home/yuchen/data/research/staging/full-benchmark-v1/acceptance-manifest-v2.json`
canonical SHA-256
`ced39152f1fb94def77faca1414ca80c661dc827803ae275f935ccc294e91c88`.
Parquet SHA-256:
`d5d70158af519376e8477760a9aa3e33fe81655b949ba05cab129bb2c24595b0`.
Every raw response retains URL, UTC receipt, bytes and SHA-256 externally.

## Corporate-action engineering and source census

Exact reciprocal merger ratios now use integer rational arithmetic before
whole-share flooring. Official 000578 ratio 1/2.90 and 600832 ratio 1/3.05 are
regression examples, not newly accepted complete lifecycle events. Existing
finite-ratio event checksums remain unchanged. Quantity, basis, zero-share
writeoff, no fabricated cash/Fill and persisted rational audit fields are tested.

Official SSE historical distribution queries cover 2010–2021; the current schema
covers 2022–2025. Empty historical responses for later years are NOT zero-event
evidence. Both website JavaScript field mappings and raw paginated responses
are retained. Collected: 17,920 A-share dividend source rows and 2,500
bonus/conversion source rows (the latter also contain B-only rows).
These are NOT accepted event counts: stable-ID/lifecycle matching, B-only
separation, restructuring pass-through review and accounting completeness remain.
Gross dividends are DIVIDEND_PER_SHARE2_A in the historical schema, not the
after-tax DIVIDEND_PER_SHARE1_A. Current gross field is A_BEFR_TAX_DIV.

External root:
`/home/yuchen/data/research/staging/full-distribution-census-v1`.
Historical v3 source manifest:
`92c6b20b7da602b2d1894e87b997d31767592c94fa7b00cefece80cac2deac66`.
Current v3 source manifest:
`5d9b7874ca273573565b1b43c0bbdbeb21e90a69a765bbf9d8dd0615e0584083`.
Pagination totals, exact-row duplicates and input-order reproducibility checked;
final source acquisition failure count = 0. Earlier empty/collision receipts
remain preserved, not overwritten.

SSE yearbooks 2012–2022, 2024–2025 were recovered from the official archive,
with snapshots under full-master-sse-baseline-v1. Volume year is not data year.
The 2025 SZSE yearbook explicitly reports no rights issues in its 2025 table
(PDF page 1260, printed page 1243). Full master acceptance remains PARTIAL:
annual price tables are not year-end snapshots, and publication directories can
contain subsequent IPOs. No paused or delisted security is silently dropped.

## Verification and remaining work

### Subsequent distribution row reconciliation

The source-row audit yields 17,862 dividend groups and 2,484 bonus/conversion
groups, plus three retained B-only rows. Exact duplicate source rows are retained
as evidence rather than double-paid. All seven old-code mismatches are records
shown under current 601360 before its legal code change; reviewed stable identity
is distinct from the as-of symbol. No current name/code is backdated.

Eight dividend amount collisions were reviewed against issuer implementation
PDFs. Four are holder-class differences (600989); four combine separate declared
distribution periods (601966 twice, 601898, 603259). Exact ordinary-holder cash
terms are retained in SSE_DISTRIBUTION_CONFLICT_RESOLUTIONS_V1.json.
For example, official 600989 2019 unrestricted cash is 0.32091, not the rounded
table 0.321; 603259 2025 combined cash is 1.33169, not 0.982 + 0.350.
Gross shareholder cash must not be replaced by the issuer's synthetic ex-price
reference dividend. These are deterministic applications of the approved cash
class, not a new methodology request.

Reviewed audit:
`/home/yuchen/data/research/staging/full-distribution-census-v1/row-audit-reviewed-v3.json`
canonical SHA-256
`3cd18a039e79f74bae4931e7b842f1d62c5c62bda792e0d0b588d43c545f5039`.
All eight collisions explained; zero normalization errors. This does NOT accept
the remaining table amounts at display precision or declare the full corporate-
action census complete. Required follow-up includes exact official terms,
historical stable-ID mapping, restructuring retention and exchange census parity.
559 backend tests and quality checks PASS after this audit extension.
Prior milestone CI 34752892295 PASS at aa372accf7ecb3db29bf16297e6643199ca0ea5c.

558 backend tests PASS; Ruff, format and mypy PASS. 78 frontend tests, lint and
production build PASS. No studies or profitability inspection were performed.
Full corporate-action census, master/ST/suspension/rule-regime and raw/factor
coverage closure remain active independent queues. Safe start NOT_ESTABLISHED.
Full dataset CREATED/AUDITED/FROZEN = NO. Human approval gate = NONE.
PR #12 stays open; no merge, release, freeze or strategy run is authorized here.
