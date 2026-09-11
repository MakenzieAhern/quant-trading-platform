# Pilot amount decision-impact acceptance

## Reachability correction and continued audit

The follow-up code trace conservatively includes DELISTING_PERIOD before other
eligibility gates: a delisting label is not itself is_st=true. The initial available
sample therefore has4,335 potential checks, not4,334:000996/2024-06-20 adds one
stable primary-source check. The original artifacts remain immutable; this does
not change the zero-ambiguity conclusion, thresholds, policy hash or source data.
The shared recovery/audit guard now explicitly covers NORMAL and DELISTING_PERIOD,
skips only ST/STAR_ST under the unchanged policy, and rejects unknown status labels.

The --include-recovered audit reads all completed secondary inputs as well as
primary/candidate evidence and writes separate amount-impact-current-* artifacts,
never replacing the initial authority report. A follow-up snapshot covered1,040
available securities/377,808 rows and6,429 potentially evaluated decisions;
all6,429 were stable, including five delisting-period checks. These are progress
counts, not a claim of final full-universe acceptance.

## New decision supersedes the earlier precision-semantics stop

The human continuation explicitly authorizes decision-invariance acceptance.
TENCENT_AMOUNT_CLASSIFICATION = LIMITED_PRECISION_PARITY.
SECONDARY_AMOUNT_AUTHORITY = PASS_FOR_PILOT.
SECONDARY_ACCEPTANCE = PASS_FOR_PILOT, subject to identical per-recovery guards.
No exact tick-level parity or specific vendor rounding algorithm is asserted.
No strategy threshold, schedule, ST policy, factor or cost has changed.

## Units and pinned implementation

- AKSHARE_VERSION = 1.18.94.
- AKSHARE_SOURCE_FILE = akshare/stock_feature/stock_hist_tx.py.
- TENCENT_UPSTREAM_AMOUNT_UNIT = 10,000 CNY.
- AKSHARE_RETURNED_AMOUNT_UNIT = CNY (already multiplied by10,000).
- UPSTREAM_DISPLAY_PRECISION = observed two decimal places in every candidate row.
- CANONICAL_CNY_GRANULARITY = nominal100 CNY, not1 CNY.
- SOURCE_FILE_SHA256 = aa9199665d356ba3a054297004e349d3926fa83026abfd2d50c4b7f832226d84.
- Installed package RECORD SHA256 = 2b76ea3f72326845b61e849eac98ed4d5ccadf344f9b4922b9c51257516a7098.
- Package METADATA SHA256 = 3df3bdf672fd80e6b38bc41a3feac1cf3ed2c757f3fb6012ecb585c5c31ede49.
- Upstream Git commit / wheel archive hash = not recoverable from installed metadata;
  RECORD hash is not falsely labeled a wheel/package archive hash.

The installed source declares output volume in shares and amount in yuan, selects
raw field8 as amount and executes `big_df["amount"] = big_df["amount"] * 10000`.
Its SHA matches the package RECORD entry. Exact source text, identity and hashes
are preserved outside Git in raw-failover-v1/amount-sdk-evidence.json, SHA256
9677f4d3433e272e3b2158a72306b567a1405fe84226af150dd5ae53c5f1aa48.
The production candidate parser operates on upstream raw responses, so it applies
Decimal(raw_string)*Decimal(10000) once. SDK-returned CNY must never be scaled again.
The previous final answer's unqualified unit label referred to the upstream field,
not the AKShare return; the distinct labels above are authoritative going forward.

## Actual code trace: AMOUNT_USAGE_SITES

Paths below are repository-relative; line numbers refer to the unchanged consumer.

| File | Function / lines | Rule or formula | Decision type |
| --- | --- | --- | --- |
| backend/app/integrations/akshare/sdk.py | AKShareSdkSource.daily_rows /31 | Map provider 成交额 to amount | Transport mapping, no threshold |
| backend/app/integrations/akshare/adapter.py | AKShareValidationAdapter.daily_bars /50 | Optional Decimal conversion | Presence/validation |
| backend/app/integrations/baostock/adapter.py | daily_bars /169 | Historical alternate adapter amount mapping | Not the current recovery route |
| backend/app/data/providers/research.py | DailyBarRecord /47 | Nonnegative Decimal or None | Schema, not optional Pilot liquidity |
| backend/scripts/materialize_akshare_partitions.py | normalized_bars /43 | Parse primary CNY exactly | Partition normalization |
| backend/scripts/audit_raw_failover.py | normalized /55 | Upstream field8 times10,000 | Candidate normalization |
| backend/app/research/strategy.py | __init__ /24–29 | Default minimum_average_daily_amount=10,000,000; reject negative config | Fixed config validation |
| backend/app/research/strategy.py | target_for_completed_session /40–46 | Append non-null amount only when adjusted close exists | History presence |
| backend/app/research/strategy.py | target_for_completed_session /48–60 | After253 completed sessions, every20; skip missing status, suspended and ST when include_st=false | Existing reachability gates |
| backend/app/research/strategy.py | target_for_completed_session /63–68 | Last20 non-null observations; require count20; sum/20 >=10,000,000 CNY | Liquidity eligibility boundary |
| backend/app/research/strategy.py | reset /93 | Clear amount history | Lifecycle, no monetary boundary |

No traded_amount/turnover_amount aliases or separate amount-based ranking cuts were
found in actual app code. Research engine calls target_for_completed_session but
does not separately consume market amount. Factor formulas use adjusted closes;
portfolio construction receives the screened factor set and raw reference prices;
risk uses order quantity*reference price; execution uses raw prices and share volume;
costs use fill notional. FixedCommission.amount is a fee parameter, not daily traded
amount. CSI300 comparison consumes index/equity returns, not daily traded amount.
The single amount-dependent numeric eligibility rule propagates indirectly to
selection, portfolio and downstream risk; invariant input eligibility leaves those
amount dependencies unchanged. No rankings, orders, returns or strategy were run.

Pinned consumer SHA256 = 14bd3d21a48560faa28527fa061883a4ceb69bcf7a6332176ac06467152dbde0.
The audit refuses a changed consumer until its rule trace is reviewed.

## Conservative interval and propagation

For normalized Tencent amount A, use [max(0,A-100), A+100] CNY.
This closed envelope covers the union of floor, ceiling and nearest rounding cells
of a0.01 upstream-unit grid. It does not select a favorable rounding mode. It is a
quantization model, not a claimed bound on unrelated provider aggregation errors;
cross-source discrepancies outside the envelope fail separately.
The prior half-quantum50-CNY direct-rounding classifier is preserved as historical
evidence, not silently relabeled. The new human-authorized envelope is derived from
representation before testing decisions, not tuned to the observed51-CNY maximum.

Propagate each observation's lower/upper bound through the same trailing20 mean.
Exactly20 observations remains required. The lower mean meeting the threshold means
both pass; an upper mean strictly below it means both fail; otherwise record ambiguity.
Exact equality uses the existing >= rule, never a new tie-breaker. Nulls are not
imputed. Suspensions/factor availability may remove evaluations; the audit counts
a conservative superset before those gates, so they cannot hide an amount flip.

## Scope and results

All657 accepted primary histories were scanned; ten Tencent candidate histories
were shadow-audited without replacing any primary partition. Their union is659
securities /244,772 bars. Primary rows without Tencent observations retain zero
source uncertainty; an additional all-date +/-100 stress scan covers those too.
Two targeted controls (600666,688211) were selected by proximity to the unchanged
liquidity threshold, not performance. Eight additional bounded Tencent requests
(two years/two repetitions each) extend the prior evidence; no primary was refetched.

Original AMOUNT_DEPENDENT_DECISIONS_TOTAL = 4334 (corrected to4335 above; before
suspension/factor/portfolio gates, across all available histories).
Original AMOUNT_DECISIONS_STABLE = 4334 (corrected to4335 above).
AMOUNT_DECISIONS_AMBIGUOUS = 0.
SECURITIES_WITH_AMBIGUOUS_AMOUNT_DECISION = 0.
DATES_WITH_AMBIGUOUS_AMOUNT_DECISION = 0.
MAX_DISTANCE_TO_THRESHOLD_FOR_AMBIGUOUS_CASES = N/A (empty set).

One all-date stress window is explicitly retained:600666/2024-01-19, Tencent mean
9,999,975 CNY, interval[9,999,875,10,000,075], distance25 CNY. The primary mean is
9,999,971.95 CNY. It is not an actual amount-rule ambiguity: this is calendar
session256, not a scheduled evaluation, and the accepted PIT status is ST, which
the unchanged include_st=false policy rejects before amount evaluation. Its existing
primary data remain authoritative in production. No new exclusion was introduced.

Scheduled Pilot sessions:2024-01-16,02-21,03-20,04-19,05-22,06-20,07-18.
Missing securities are not claimed audited: the remaining4,521 production gaps
must each pass the frozen interval/lineage guards during recovery and final R3.

## Expanded cross-source empirical validation

Original1,719 rows and hashes remain untouched. Expanded comparison has2,478 rows,
with identical Decimal OHLC/dates and previously accepted board-volume normalization.
Raw upstream strings, CNY conversion and row-level differences are retained.

| Statistic | Absolute CNY difference | Relative difference (fraction) |
| --- | ---: | ---: |
| Median | 25.00 | 6.64873513023468793280315087E-8 |
| p95 | 47.84 | 0.000003915446293246994183070606887 |
| p99 | 50.00 | 0.00001063212542262698554942267559 |
| Maximum | 51.00 | 0.0009661835748792270531400966184 |

Percentiles use nearest rank; median averages the middle pair. Signed normalized
Tencent-minus-primary differences range[-49.46,+51.00] CNY.24 rows are exactly equal;
the fixed SDK-backed10,000 scaling is consistent across every row. Outliers outside
the representation envelope=0. The larger relative maximum is the low-amount
600666/2023-02-22 observation:primary51,750, Tencent51,800 CNY; not an amount decision.
All repeated normalized requests match. No profitability statistic was inspected.

## Evidence and next stage

External raw-failover-v1/amount-impact-audit.json SHA256:
d950fdc3543fbf8373370c8013f8a8a8579140e8b82523f7d0961033a280323c.
All security-date bounds and decisions:amount-impact-decisions.json SHA256
38f3dff0f2f56f269364550fe4caa52c0ca562595267ebae353b508affe1b3ee.
Expanded raw-value comparisons:amount-impact-parity.json SHA256
16f7e008aaaeea4e7d9322a4894277a8d8cce8209a44d871ccc81e9bd69acfa8.
Source inventory:amount-impact-sources.json SHA256
4e237101793174c2023442a481c8be15154d1fd4bee3bc64186645299486babd.

CN_A_RAW_OHLCV_FAILOVER_V1 is now frozen for Pilot recovery, transport/service
failures only. Preserve657 primary inputs; recover pending members with explicit
lineage and stop on genuinely ambiguous required decisions. Raw prices remain
execution prices and adjustment data remain separate. Dataset freeze, studies,
PR12 merge and releases remain unauthorized.
