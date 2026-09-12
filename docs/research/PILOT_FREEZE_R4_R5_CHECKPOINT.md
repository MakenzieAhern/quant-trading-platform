# Pilot freeze, R4 smoke and R5 counterexample

2026-09-12 UTC. Current stop: newly discovered material frozen-universe defect.
This report supersedes prior current readiness claims, not historical receipts.

## What completed

The approved5177-security Pilot passed the final read-only identity comparison
against its existing R3 receipt and all22 recorded checks. Every partition hash
and the exact path set matched. No source or methodology was substituted.
Pilot v1 was frozen; canonical manifest remains
`0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490`.
Freeze record canonical SHA256:
`74870e7d64a9197bd75a6ee32e7bf019aecaf5159d7ed9d1023078df7ce0ad31`.
The immutable freeze receipt and dataset bytes remain preserved. Application
writers reject frozen destinations; this is not administrator-proof WORM storage.

R4 engineering exercised382 sessions,7 rebalances,140 proposals and140 orders
through the unchanged v1 strategy, risk, OMS, broker, portfolio and analytics.
All orders expired NOT_CONFIRMED_TRADEABLE;0 fills,0 positions, cash unchanged.
Unknown liquidity was not converted to a fill. Deterministic reversed-input
replay and truncated-future replay passed. Actual API/UI parity passed21 exact
metrics and382 points for each daily curve. Run:
`b35d4f54-1ac1-57d7-bb5a-057a371c2373`.
Every result is PILOT_ENGINEERING_SMOKE_ONLY, never formal research evidence.
Small historical engineering receipt: `.research/reports/pilot-smoke-v1.json`.
Current acceptance is invalidated by the independent finding below; the
historical pipeline checks are not being retroactively represented as unrun.

## R5 uncovered omitted STAR securities

The original SSE master fetcher requested terminated STOCK_TYPE=1,2 but current
STOCK_TYPE=1 and8. Consequently STAR exits absent from the current register were
never included in the candidate master. The prior R3 checks tested the supplied
candidate population, not an independent all-board exit census. Passing byte
identity checks cannot detect a population omitted before publication.

New official SSE STOCK_TYPE=8 exit response, retrieved2026-09-12T12:43:46.088846Z:
SHA256 `76caaccf32448f2033f93e458e82f81ad7d8090e0ca0b069fd798dd9d97f6a48`.
Exact URL and reproducible countercheck are recorded in
`.research/reports/pilot-v1-master-omissions.json`.

| Security | Official SSE listing | Official SSE delisting | Frozen candidate / securities / exclusions |
| --- | --- | --- | --- |
|688086|2020-02-26|2023-07-07|Absent / absent / absent|
|688555|2020-06-23|2023-07-07|Absent / absent / absent|
|688287|2022-05-25|2026-06-10|Absent / absent / absent|

All three lifecycles overlap the Pilot. 688287's future delisting must not remove
it from2023-2024. This is a candidate-population counterexample, not a shortcut
to accepting instrument classification, ST timelines, or a corrected final count.
Current SECURITY_MASTER completeness, SURVIVORSHIP and DELISTING_RETENTION
acceptance are invalidated. Pilot readiness is NOT_READY. Other accepted
source decisions are not arbitrarily replaced, but their supplied-universe
scope does not certify these omitted candidates.

Root query now includes1,2,8, with a new snapshot filename so replay cannot
overwrite the old accepted source. A regression check covers both Pilot-period
and post-Pilot STAR exits. This code fix does not repair the frozen dataset.
The mutable application dataset registration is now FAILED while frozen=true
and its original checksum/manifest remain unchanged. The historical run retains
its metrics and receives an explicit dataset-acceptance warning, verified in the
actual API/UI. No frozen source/data/result bytes were replaced by this warning.

Targeted repair feasibility reused the accepted endpoints: all three Tencent
raw histories and Sina factor curves returned data. Eastmoney returned
RemoteDisconnected for each. These are retained probe snapshots, NOT newly
accepted partitions. No claim that a provider is unavailable is used to justify
this stop. A corrected v2 still requires source/instrument/ST closure, audited
partition composition, all completeness checks and revised human freeze review.

## R5 source discovery retained

No full dataset was published, audited or frozen. Target remains2010-2025.
Official SZSE yearbook2009 SHA256:
`123a972d867cd0560954c7c7500b3a463c9541040e228bee8400eb59bf9f4484`.
Official SZSE yearbook2025 SHA256:
`ccb975c5346f037a405a9c09f52f78465cfd262dd976065cec8b66df0ce325b0`.
Official SZSE exit workbook returned208 rows (not all ordinary A shares or all
within the target): SHA256
`715cb8d92582356ee0fd939f111750e1a2b9c1e533a0cc4ac1f2532790509735`.
The initially named szse-yearbook-2024.pdf is actually2008, as the official
index and document title show; it is retained as rejected candidate evidence,
not accepted2024 authority. New evidence is outside Git under
`staging/full-master-evidence`; source URLs/timestamps/checksums are preserved.
The fetch parser label identifies reused transport code, not full-period acceptance.

The fixed2010 raw probe returned Tencent230 target-year rows for600000 and195
for exited600553; both Eastmoney requests disconnected. These are coverage
controls, not a full calendar, amount-parity or full-universe acceptance.
External checkpoints: `staging/full-raw-coverage-v1` and
`staging/pilot-v2-star-repair-probe-v1`. Do not restart successful requests.

## Stop and required review

SINGLE_SMALLEST_BLOCKER=FROZEN_PILOT_MASTER_OMITS_STAR_EXIT_SECURITIES.
HUMAN_APPROVAL_GATE=GATE_A_REVISED_DATASET_REVIEW. This is not a request to freeze
an unbuilt v2 and is not the full-dataset freeze gate. The newly discovered
material scope defect invalidates the premise of the existing Gate A acceptance.
Preserve v1 for reproducibility; do not silently patch it or transfer its approval
to a corrected hash. Review the revised Pilot version path before continuing.

Full coverage/counts/bar totals/manifest are NOT_AVAILABLE, not zero.
Development, Validation and Official OOS remain NOT_RUN. PR12 remains unmerged.
No release, visibility change, live trading, GPU/ML work or parameter tuning.

Verification:424 backend tests,78 frontend tests, Ruff, mypy116 modules, frontend
lint and production build pass. The new source regression fails if STAR exits
are omitted again. The independently run frozen-master audit correctly FAILS
with three missing candidates; code-test success is not dataset-audit success.
