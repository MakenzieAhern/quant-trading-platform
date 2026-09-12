# v1.1 controller roadmap

## Current: revised freeze approved; final verification PASS

Latest human approval supersedes prior revised-freeze STOP. All eight approved
component hashes, partition bytes, counts,25 R3 checks and preserved v1 verify.
Freeze execution pending; then unchanged R4 v2 and, on PASS, R5 full-history
materialization/audit. Next gate GATE_FULL_RESEARCH_DATASET_FREEZE, unfrozen.
No formal studies, PR merge or release. Previous acceptance decisions unchanged.

## Historical checkpoints below (superseded)

## Current override: revised Pilot gate (2026-09-12)

Human-approved repair completed through v2 materialization and full revised R3.
V2 CREATED/AUDITED=YES, FROZEN=NO, readiness READY. Stop at
GATE_A_REVISED_DATASET_FREEZE; explicit human approval required.
Do not execute the historical R4/R5 automatic path below. R4 v2 is NOT_RUN;
R5 remains BLOCKED_PENDING_REVISED_PILOT_ACCEPTANCE. V1 is frozen, superseded,
research acceptance invalidated. See `../research/REVISED_PILOT_DATASET_REVIEW.md`.

## Historical v1 roadmap and checkpoints (superseded by override)

Current exception (2026-09-12): R4 engineering completed, but R5 uncovered a
frozen Pilot master omission of three STAR exits. Historical R1/R2/R3 completion
does not remain a current completeness acceptance. Pause at revised Gate A
dataset review; preserve frozen v1, repair via a new version and new audit/freeze
review. R5 full2010-2025 materialization/audit remains unfinished. Intended next
full-dataset gate remains GATE_FULL_RESEARCH_DATASET_FREEZE after valid completion.
See `../research/PILOT_FREEZE_R4_R5_CHECKPOINT.md` before following stage rows below.

Read `.research/project_state.json`, CURRENT_STATE, RUN_REPORT and BLOCKERS before
each continuation. Preserve newer evidence. These small files are the persistent
controller state, not a background scheduler or an authorization bypass.

Current checkpoint (2026-09-12 UTC): R1 PASS, R2 atomic publication complete,
R3 all22 checks PASS. Gate A APPROVED; Pilot v1 frozen after read-only verification.
5177 ordinary A shares,1922088 raw bars; READY/AUDITED/FROZEN YES.
Official daily suspension/tradeability is still unknown and fail-closed under
the approved execution convention; this is not execution-readiness certification.
See [final R2/R3 report](../research/R2_R3_ORDINARY_A_SHARE_REPORT.md).

| Stage | Acceptance and automatic next action |
| --- | --- |
| R1 Source authority | Master, SSE, SZSE, raw OHLCV, adjustment, calendar, CSI300 PASS; market rules PASS_FOR_PILOT. Canonical source manifest required. Separately require EXECUTION_CONVENTION_VALIDATION PASS (simulation assumption, not exchange fact). Then R2. |
| R2 Materialization | `cn-a-pilot-akshare-20230101-20240731-v1`, 2023-01-01..2024-07-31. Accepted PIT inputs, raw execution prices, separate adjustments, suspension/tradeability and supported actions. Deterministic bounded retries/concurrency, checkpoints, failure manifest, partitioned Parquet, logical/physical hashes and atomic complete publication. Then R3. |
| R3 Audit | COMPLETE, all22 checks PASS. Gate A subsequently approved; Pilot v1 frozen. |
| R4 Pilot engineering smoke | Frozen real Pilot through PIT/factors/ranking/construction/RiskEngine/OMS/execution/portfolio/analytics/persistence/API/UI. PILOT_ENGINEERING_SMOKE_ONLY, never formal research evidence. Unchanged strategy; deterministic replay and NO FILL on unknown executable liquidity. |
| R5 Full historical dataset | Target2010-01-01..2025-12-31 subject to audited coverage, same scope/PIT/lineage standards with historical regime boundaries. Reuse resumable pipeline; never extrapolate Pilot authority backward. Materialize/audit then STOP at GATE_FULL_RESEARCH_DATASET_FREEZE, unfrozen. Formal research remains locked. |
| R6 Methodology freeze | Hash dataset, strategy/factors, universe, rules, costs, rebalance, construction, benchmark and splits. OOS lock remains unauthorized. STOP at Gate B. |
| R7 Official OOS | Explicit authorization and frozen methodology only; exactly once, immutable result lineage. Never replace a bad result. Then R8. |
| R8 Portfolio release | Bilingual UI/results, benchmark/equity/drawdown/heatmap/rolling views, methodology, reproducibility, limitations, architecture, READMEs, screenshots and release notes. STOP at Gate C before merge/tag/public visibility change. |

R3 audits: SURVIVORSHIP, FUTURE_IPO, DELISTING_RETENTION, LOOK_AHEAD,
ST_POINT_IN_TIME, STABLE_ID, OHLC_VALIDITY, TRADING_CALENDAR,
ADJUSTMENT_SEPARATION, ADJUSTMENT_TEMPORAL_SAFETY, SUSPENSION_HANDLING,
BENCHMARK_ALIGNMENT, MARKET_RULE_RESOLUTION, CHECKSUM_REPEATABILITY, INPUT_ORDER_REPRODUCIBILITY,
RESUME_RESTART. Report securities by exchange, sessions, bars/raw rows, adjustment
rows, benchmark rows, failures, missing/rejected rows, ST/*ST/suspension observations.
Missing counts are UNKNOWN, never invented zeroes.

Approved v1.1 instrument scope: ordinary RMB A-share equities only, independent
of board. Explicit original listing/type evidence is required before inclusion;
CDR/B-share/fund/bond/preferred/warrant/other instruments are out of scope before
market-data requirements. Preserve the broader master and every exclusion.
R3 additionally requires INSTRUMENT_TYPE_SCOPE, NON_A_SHARE_INSTRUMENT_LEAKAGE=0,
INSTRUMENT_CLASSIFICATION_REPRODUCIBILITY, PROVIDER_LINEAGE, CROSS_SOURCE_PARITY
and AMOUNT_SEMANTIC_VALIDATION. No strategy performance is inspected for scope.

Future formal metrics (locked): return/CAGR, volatility, Sharpe/Sortino, drawdown/Calmar, win rate,
profit factor, turnover/holding period/costs, benchmark/excess return, tracking
error/information ratio, rolling/monthly metrics and regime stability.

After each coherent milestone: focused checks; update state/current/run/blockers;
local commit if changed; push at a meaningful checkpoint; check CI; reread state
and continue to the next permitted action. Normal milestones do not require prompts.
Stop only at Gates A/B/C, purchase/credentials/CAPTCHA/human login, unresolved
authority ambiguity, destructive Git history requirement, or remaining meaningful
data-integrity failure. Record the exact exception and next action.

Only push existing `feature/a-share-research-v1.1` / PR #12. Never change main,
merge, release, expose secrets/raw datasets, silently substitute providers, fabricate
data/results, enable live trading or ML/GPU. Do not repeat accepted SSE/SZSE audits
without regression; do not revisit ancient 600721 history unless relevant to the newly requested full period.
No formal studies before the Full Research Dataset freeze gate.
