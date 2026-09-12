# Ordinary A-share scope, R2 publication and R3 audit

Checkpoint date: 2026-09-12 UTC. Existing branch:
`feature/a-share-research-v1.1`; existing PR #12 remains open and unmerged.
This report supersedes the earlier running/blocked R2 snapshots, not their evidence.

## Scope decision and complete candidate inventory

The human approved `ORDINARY_A_SHARE_EQUITIES_ONLY` as methodology, not as a
response to provider inconvenience or strategy performance. Board and instrument
type remain independent. Generic `COMMON_A_SHARE` classification precedes market
data requirements; existing lifecycle and downstream eligibility gates remain.
No strategy profitability was inspected.

| Instrument type | Candidate securities |
| --- | ---: |
| COMMON_A_SHARE | 5177 |
| CDR | 1 |
| B_SHARE | 0 |
| ETF | 0 |
| FUND | 0 |
| BOND | 0 |
| CONVERTIBLE_BOND | 0 |
| PREFERRED_SHARE | 0 |
| WARRANT | 0 |
| OTHER | 0 |
| UNCLASSIFIED | 0 |
| TOTAL_MASTER_SECURITIES | 5178 |

The complete nonordinary list contains one instrument:

| Security ID | Issuer | Type / venue | Listed | Status |
| --- | --- | --- | --- | --- |
| CN-A:SSE:689009 | Ninebot Limited / 九号有限公司 | CDR / SSE STAR | 2020-10-29 | AUTHORITATIVELY_OUT_OF_SCOPE_INSTRUMENT |

[Official SSE listing notice](https://www.sse.com.cn/disclosure/announcement/listing/c/c_20201027_5242851.shtml),
published 2020-10-28, 上证公告（存托凭证）〔2020〕189号. Preserved HTML SHA-256:
`c7be576b891a548e6548f7c1852cde496071b3f7e3ec668b865f556d9eaf9c85`;
retrieved `2026-09-11T23:27:20.449429+00:00`.
Its historical raw/factor failure evidence remains preserved; it is not a failed
required security, provider exclusion, or survivorship exclusion.

All candidates have explicit full-lifecycle type evidence. Nonmixed venues use
original typed A-listing register columns and dates, not symbol-prefix inference.
The mixed STAR venue uses original dated stock/CDR IPO listing metadata; a later
current SEC_TYPE snapshot alone cannot backdate classification. Future published
reclassifications, overlaps, gaps, and missing evidence fail closed.

```
PILOT_INSTRUMENT_SCOPE_DECISION = APPROVED
PRE_SCOPE_FILTER_CANDIDATES = 5178
POST_SCOPE_FILTER_COMMON_A_SHARE_SECURITIES = 5177
EXCLUDED_CDRS = 1
EXCLUDED_B_SHARES = 0
EXCLUDED_ETF_FUNDS = 0
EXCLUDED_OTHER_INSTRUMENTS = 0
```

## R2 completed publication

Dataset: `cn-a-pilot-akshare-20230101-20240731-v1`.
Coverage: `2023-01-01` through `2024-07-31`.
Local external catalog: `/home/yuchen/data/research/cn-a-pilot-akshare-20230101-20240731-v1`.
Source evidence remains under `/home/yuchen/data/research/staging`; neither the
catalog nor large source snapshots are committed to Git.

| Metric | Count |
| --- | ---: |
| SECURITIES | 5177 |
| SSE_SECURITIES | 2286 |
| SZSE_SECURITIES | 2891 |
| SSE_MAIN | 1715 |
| SZSE_MAIN | 1531 |
| STAR_COMMON_A_SHARE | 571 |
| CHINEXT_COMMON_A_SHARE | 1360 |
| TRADING_SESSIONS | 382 |
| TOTAL_BARS | 1922088 |
| ADJUSTMENT_ROWS | 12528 |
| BENCHMARK_ROWS | 382 |
| PRIMARY_SOURCE_SECURITIES / PRIMARY_SUCCESS | 657 |
| SECONDARY_SOURCE_SECURITIES / SECONDARY_SUCCESS | 4520 |
| PRIMARY_FAILED_SECONDARY_RECOVERED | 4520 |
| PRIMARY_FAILED_SECONDARY_FAILED | 0 |
| AUTHORITATIVELY_OUT_OF_SCOPE_INSTRUMENT | 1 |
| AUTHORITATIVELY_NO_DATA_EXPECTED (in scope) | 0 |
| FAILED_SECURITIES | 0 |
| UNRESOLVED_REQUIRED_DATA | 0 |
| MISSING_OBSERVATIONS | 4210 |
| REJECTED_OBSERVATIONS | 0 |
| ST_OBSERVATIONS (ST only, observed bars) | 26906 |
| STAR_ST_OBSERVATIONS (observed bars) | 20726 |

The original 657 primary +1923 secondary inputs, 2580 partitions and 951927 raw
rows were preserved. Remaining 2597 ordinary A-share inputs were recovered using
the unchanged frozen Eastmoney-to-Tencent policy. Two Tencent transport timeouts
(300889 and 300890) recovered in the single allowed final transport-only retry
round after its fixed backoff. The worker exited successfully; no retry loop is
left running. Original timeout records and the out-of-scope 689009 record remain.

Raw/factor Parquet bytes were copied without re-encoding. The complete catalog
was built on the same filesystem and atomically renamed into its final external
directory. A second publication invocation verified the same input/manifest
hashes with `source_refetched=false` and `partitions_rewritten=false`.

The full amount audit covers 5177 securities /1922088 rows and 34799 potentially
reachable scheduled liquidity decisions: zero ambiguous decisions, zero outliers.
The accepted 2478-row cross-source sample retains zero OHLC/date mismatches and
maximum amount difference 51 CNY. Acceptance is LIMITED_PRECISION_PARITY, not
exact amount parity or an independently established vendor-error bound.
Two all-date stress ambiguities remain disclosed (600666/2024-01-19 and
301088/2024-06-24); neither is a scheduled evaluation date. No tolerance, schedule,
strategy parameter, provider policy or performance criterion was changed.

## Critical interpretation limits

There are 1926298 in-lifecycle security-sessions. Official daily suspension and
tradeability evidence is **not certified** for these sessions: both fields remain
null. Confirmed suspension observations in this catalog = 0 is a count of
confirmed evidence, **not a claim that no suspensions occurred**.
The 4210 missing observations remain explicit missing intervals; they are not
fabricated bars or inferred suspensions. There are no unknown Pilot ST states.

Under the already approved `CN_A_DAILY_OPENING_LIMIT_V1`, execution remains
`NO_FILL_UNLESS_SEPARATE_OFFICIAL_TRADEABILITY_EVIDENCE`. Raw pre_close is not
fabricated. A suspension-handling audit PASS means fail-closed representation,
not complete suspension history or execution readiness. No exact auction-fill
claim is made. HFQ feature factors are not a complete corporate-action cash-flow
ledger. Master names are display metadata, not historical eligibility; CSI300
is a price-index history, not a constituent-membership history.

## R3 audit

The actual published-catalog audit completed with exit code 0. All 22 checks
below passed; 5725 distinct market-rule cases were checked. Original source
responses were replayed into normalized rows; reversed input rows reproduced
all Parquet physical/logical hashes and the canonical manifest. The original
2580-partition receipt digest was independently reconstructed unchanged.

| Audit | Result |
| --- | --- |
| SURVIVORSHIP | PASS |
| FUTURE_IPO | PASS |
| DELISTING_RETENTION | PASS |
| LOOK_AHEAD | PASS |
| ST_POINT_IN_TIME | PASS |
| STABLE_ID | PASS |
| OHLC_VALIDITY | PASS |
| TRADING_CALENDAR | PASS |
| ADJUSTMENT_SEPARATION | PASS |
| ADJUSTMENT_TEMPORAL_SAFETY | PASS |
| SUSPENSION_HANDLING | PASS — unknown stays null / no-fill |
| BENCHMARK_ALIGNMENT | PASS |
| MARKET_RULE_RESOLUTION | PASS |
| PROVIDER_LINEAGE | PASS |
| CROSS_SOURCE_PARITY | PASS — accepted limited-precision contract |
| AMOUNT_SEMANTIC_VALIDATION | PASS — unchanged decision-invariance criterion |
| CHECKSUM_REPEATABILITY | PASS |
| INPUT_ORDER_REPRODUCIBILITY | PASS |
| INSTRUMENT_TYPE_SCOPE | PASS |
| NON_A_SHARE_INSTRUMENT_LEAKAGE | PASS / 0 |
| INSTRUMENT_CLASSIFICATION_REPRODUCIBILITY | PASS |
| RESUME_RESTART | PASS |

Backend regression suite: 419 tests PASS; Ruff and mypy PASS. CI run34665563160
passed backend/frontend/compose on implementation commit
`5be77b05fa0b674c0f37bc04e19267bdac50b24b`. Final documentation commit receives
its own CI; inspect the existing [PR #12](https://github.com/MakenzieAhern/quant-trading-platform/pull/12).
No market dataset was committed or uploaded to GitHub.

## Final autonomous checkpoint

```
CURRENT_STAGE = R3
LAST_COMPLETED_STAGE = R3
STATUS = AWAITING_HUMAN_APPROVAL
SOURCE_AUTHORITY_PREFLIGHT = PASS
PILOT_DATASET_CREATED = YES
PILOT_A_SHARE_DATA_READINESS = READY
DATASET_AUDITED = YES
DATASET_FROZEN = NO
HUMAN_APPROVAL_GATE = GATE_A_DATASET_FREEZE
HUMAN_APPROVAL_REQUIRED = YES
SINGLE_SMALLEST_BLOCKER = NONE (intentional approval gate)
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
PR_MERGED = NO
V1.1.0_CREATED = NO
```

Stop here. READY means the Pilot passes the approved data/audit contract with
the limitations above; it does not authorize freezing or strategy research and
does not certify executable daily fills. Human Gate A approval is still required.

## Evidence checksums

All SHA-256 values below identify preserved bytes unless explicitly canonical.
Relative paths refer to the external staging directory.

| Evidence | SHA-256 |
| --- | --- |
| `instrument-scope-20260912/approved-classifications.json` | `28d56696d2dc3de6d3c217dc557b9d8139729b3389245beb8fa580897ce8b7d7` |
| `instrument-scope-20260912/approved-instrument-inventory.json` | `8d94f1f9ed4c3e562dcb84617c01c1156e75030e7ef139e7fc54ccffce126694` |
| `instrument-scope-20260912/approved-scope-manifest.json` | `0b7fa3f26b99ffc19c179bc19a492693d6eb1c5249f4779251d8d9b03427334d` |
| Original primary checkpoint | `ffdc46937ecbd30f74a28660ef1769d2a7b8506ef65d0f1c2ae45ddac4841a68` |
| Original 2580 partition receipt reconstruction | `ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6` |
| `pilot-akshare-20260911/secondary-checkpoint.json` | `cb8ebaf9b1c00382d3fafd5e790afdf6caa9c56f2c066effae613d49cdfffcf2` |
| `pilot-akshare-20260911/partition-checkpoint.json` | `de6c5be30cfa24a07d729df7fcff8ecb65298c87e46f539ec8ce99ad348ce1cd` |
| `raw-failover-v1/amount-impact-current-audit.json` | `0b0a6e6bf14e90c6aff83a6dc6f55549d20f33c90aea313e84305f42131e1ece` |
| Accepted source preflight (canonical) | `c549b64c562a5b5a08bd7ec7f9c62ba8d58df77ce0eac5eb66ebcc1d7d2ea859` |
| Frozen raw failover policy | `3fb1941b93f127774ec228d27bb78074d48dc2d35ee29e98826a3b207472f740` |
| `pilot-akshare-20260911/publication-report.json` | `5206b0babab1b8a6b43462af26e45ff5576a105dfa657414cba967103d3b8c22` |
| `pilot-akshare-20260911/publication-resume-verification.json` | `4f17aaae3859768dab18b0bae6381afe813784f2c274769453397b074424d68c` |
| Publication input digest | `f562bb918632100add02f356c333b8db720bf5c89242560a30e77cd2942ac408` |
| MANIFEST_SHA256 (canonical) | `0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490` |
| Final manifest file SHA-256 | `e0e0e6ebed5947bde70dcb894e2b2ff041f450d5df858636b78df17513f709fd` |
| `pilot-akshare-20260911/dataset-audit.json` | `88fa6df2892876bb7318ceabd24883539ca9b7920ec7abf1f2d88be5e9d892d1` |

Publication/report receipts describe their own stage: the preserved R2 publication
receipt says `dataset_audited=false`. A later successful R3 audit is a separate
artifact; neither the receipt nor the dataset manifest is rewritten to manufacture
audit history.
