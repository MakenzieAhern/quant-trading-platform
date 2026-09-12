# v1.1 controller roadmap

Read `.research/project_state.json`, CURRENT_STATE, RUN_REPORT and BLOCKERS before
each continuation. Preserve newer evidence. These small files are the persistent
controller state, not a background scheduler or an authorization bypass.

| Stage | Acceptance and automatic next action |
| --- | --- |
| R1 Source authority | Master, SSE, SZSE, raw OHLCV, adjustment, calendar, CSI300 PASS; market rules PASS_FOR_PILOT. Canonical source manifest required. Separately require EXECUTION_CONVENTION_VALIDATION PASS (simulation assumption, not exchange fact). Then R2. |
| R2 Materialization | `cn-a-pilot-akshare-20230101-20240731-v1`, 2023-01-01..2024-07-31. Accepted PIT inputs, raw execution prices, separate adjustments, suspension/tradeability and supported actions. Deterministic bounded retries/concurrency, checkpoints, failure manifest, partitioned Parquet, logical/physical hashes and atomic complete publication. Then R3. |
| R3 Audit | All audits below pass with actual counts. READY, audited YES, frozen NO. STOP at Gate A; no R4. |
| R4 Development | Only after human dataset-freeze approval and recorded frozen inputs. Development split only; `cn_a_cross_sectional_momentum_low_vol_v1`, MOM_12_1/TREND_120/LOW_VOL. Version every strategy change. Then R5. |
| R5 Validation | Validation split only; predeclared metrics and stability checks, no endless optimization or OOS access. Then R6. |
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

R5 metrics: return/CAGR, volatility, Sharpe/Sortino, drawdown/Calmar, win rate,
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
without regression; do not revisit ancient 600721 history. No studies before Gate A.
