# R2 instrument-scope decision blocker

PILOT_INSTRUMENT_SCOPE = AMBIGUOUS_REQUIRES_HUMAN_DECISION.
SINGLE_SMALLEST_BLOCKER = PILOT_INSTRUMENT_SCOPE_REQUIRES_HUMAN_DECISION.
No scope choice, eligibility correction, CDR exclusion or ingestion restart was made.

## Pre-blocker contract, not a new definition

Evidence baseline: commit97eebf32960ce0d0f32a6d8796a7240435265b2b, before the
689009 factor failure; master implementation originated in6fd6d4f and084d791.
The last completed checkpoint before this audit is a9d6b83e8f0dc17ece06e2a00ef8a3e2195ecbe2.

| Existing evidence | What it establishes; what it does not |
| --- | --- |
| README.md, README.zh-CN.md, ARCHITECTURE.md, ROADMAP.md | China A-share research naming, modular boundaries, no additional asset classes; no ordinary-share/CDR distinction. |
| docs/research/CN_A_MARKET_MODEL.md | CN_A, SSE/SZSE, Main/STAR/ChiNext board scope; no instrument-class allowlist. |
| METHODOLOGY.md and STRATEGY_MOMENTUM_LOW_VOL.md | Fixed factors, liquidity, ST policy and portfolio rules; no CDR inclusion/exclusion clause. |
| POINT_IN_TIME_SECURITY_MASTER.md and DATASET_MANIFEST.md | Identity, board, lifecycle and provenance/schema contracts; no instrument-type field. |
| A_SHARE_SECURITY_MASTER_PILOT_AUDIT.md |5178 members including the current689009 row;7 B-share fact-book rows deliberately excluded. This does not define CDR scope. |
| docs/orchestration/MASTER_ROADMAP.md and prior decision/checkpoint history | Source gates and no silent substitutions/exclusions; no ordinary-equities-only decision. |
| app/data/security_master.py: eligible_universe, active_on | Active effective/listing periods are sufficient; no instrument test. |
| scripts/fetch_a_share_security_master.py: _fetch_sse | STOCK_TYPE1 and8, then A_STOCK_CODE. Type8 includes the official689009 CDR row. |
| Same script: _fetch_szse, _szse_a_symbol, _factbook_b_share | A-share source columns, code screening and explicit B-share fact-book exclusion, not a general instrument classifier. |
| scripts/stage_akshare_pilot.py: pilot_members | Source-hash/complete checks, listing/delisting windows, deterministic ordering; no instrument filter. |
| app/research/strategy.py | Uses supplied bars, factors, liquidity and statuses; never establishes instrument type. |
| Pre-blocker test_security_master.py, test_official_security_master_fetch.py, test_stage_akshare_pilot.py | Identity/lifecycle/order/source safeguards and some B-share/code exclusions; no CDR scope test. |

Searching those pre-blocker research/orchestration documents and master tests for
CDR, depositary, ordinary A-share, 普通股 and 存托 found no scope clause.
Ordinary price-limit language elsewhere describes a rule regime, not a universe contract.
The historical observed inclusion of689009 proves implementation behavior, not an
explicit methodology decision to research CDRs. Conversely, calling the dataset
“A-share” alone cannot establish exclusion, because the consumed official list uses
the A_STOCK_CODE column for this confirmed CDR too. Neither Path A nor Path B is
established sufficiently to choose automatically. Section13 requires this stop.

## Authoritative instrument fact

[SSE listing notice](https://www.sse.com.cn/disclosure/announcement/listing/c/c_20201027_5242851.shtml):
关于九号有限公司存托凭证科创板上市交易的公告, published2020-10-28,
上证公告（存托凭证）〔2020〕189号. It identifies code689009, issuer九号有限公司,
CDR listing on the STAR Market, effective2020-10-29. The stored official SSE
reference row independently provides English issuer name Ninebot Limited and the
same listing date. This is not a code-prefix inference.

Listing snapshot SHA256:
c7be576b891a548e6548f7c1852cde496071b3f7e3ec668b865f556d9eaf9c85.
Retrieval UTC:2026-09-11T23:27:20.449429+00:00; HTTP200.
English-name source security-master-pilot/raw/sse-current-8.json SHA256:
cc3402efab6ce1f4acd1ab8dbbbdba7146aed450531ebc22d8b8182ff9664960.
Evidence is persisted outside Git under staging/instrument-scope-20260912/;
classification facts keep publication date separate from effective and retrieval dates.

## Full-master instrument evidence inventory

All5178 rows were inventoried without changing source files or admission. Before/after:
5178/5178 total,2287/2287 SSE,2891/2891 SZSE; exclusions0.

| Requested count | Result |
| --- | --- |
| TOTAL_MASTER_SECURITIES |5178 |
| ORDINARY_A_SHARE_SECURITIES |UNKNOWN;5177 are not independently instrument-typed |
| CDR_SECURITIES |1 confirmed:689009; completeness beyond confirmed evidence not certified |
| B_SHARE_SECURITIES |UNKNOWN final type count;0 newly confirmed admitted examples |
| ETF_OR_FUND_SECURITIES |UNKNOWN final type count;0 confirmed examples |
| OTHER_SECURITIES (including bond/preferred) |UNKNOWN final type count;0 confirmed examples |
| UNCLASSIFIED_INSTRUMENT_SECURITIES |5177 |
| CONFIRMED_NON_ORDINARY_SYMBOLS |[689009] |
| OTHER_CDR_SECURITIES / OTHER_NON_A_SHARE_SECURITIES |None additionally confirmed; NOT a certified empty set |

UNCLASSIFIED means the old normalized schema lacks explicit instrument evidence;
it does not mean the5177 are non-A-shares, missing market data, or excluded.
The earlier security-master PASS covered lifecycle/source reconciliation, not a
separate instrument-type proof. No zero-leakage PASS or assumed5177 ordinary-share
count is fabricated. A fully certified type census remains incomplete; resolve
the scope decision before further classification/acquisition as section13 directs.

Full per-security inventory SHA256:
1e2afa2a9b0e362b5362f6edb41837d3b5dee4121a6b99bb4c7af70eda3e8ca6.
Audit report SHA256:
b349b18cb61f92eab2a0b5e92a6552b39e2ebc52317f4565b0ff23cf36a187a9.
Run offline: `python -m scripts.audit_instrument_scope --staging STAGING --evidence EVIDENCE`.
Reversed member/fact order yields identical output. Unknown types stay explicit.

## Minimal representation, no implicit scope change

InstrumentType and immutable InstrumentClassification represent explicit sourced,
effective-dated facts independently of market/board/eligibility. Required provenance
includes URL, publication date, response SHA256 and UTC retrieval. There is no
default COMMON_STOCK and no production689009 branch or prefix classifier.
Existing master records/checksums, strategy, dataset schemas and filters are unchanged.
No database migration or new dependency was needed for this isolated evidence model.

Tests cover the authoritative689009 fixture, explicit types with synthetic identical
prefixes, missing-type rejection, publication/effective boundaries, serialization,
duplicate evidence rejection, unknown preservation and input-order reproducibility.
Ordinary-share exclusion/inclusion tests are NOT claimed: that rule has not been authorized.
407 backend tests, Ruff/format and strict mypy pass. No strategy execution/results inspection.

## Preserved R2 state and required decision

PRIMARY_SUCCESS=657; SECONDARY_RECOVERED=1923; PARTITIONED_SECURITIES=2580;
RAW_ROWS=951927. One persisted factor failure and2597 unattempted members remain.
Primary checkpoint SHA ffdc46937ecbd30f74a28660ef1769d2a7b8506ef65d0f1c2ae45ddac4841a68;
secondary31598dfc8fc9d0697953ecb84cd94ac279758e9ad758e0352a496189ebd4b49b;
partitions ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6.
All match the prior checkpoint. No failed security was relabeled out-of-scope.
Sina's empty factor response remains preserved, not resolved by the CDR fact alone.
Tencent LIMITED_PRECISION_PARITY and frozen failover policy remain accepted.

Human decision needed: whether this Pilot admits ordinary A-share equities only
or also CDRs. If ordinary-only is approved, perform a generic sourced instrument
classification/eligibility correction and complete the full type census before
resuming. If CDRs are included, retain689009 and establish CDR adjustment authority.
Do not assume its baseline or conversion/corporate-action model from ordinary shares.

PILOT_DATASET_CREATED=NO; DATASET_AUDITED=NO; DATASET_FROZEN=NO.
DEVELOPMENT_STUDY=NO; VALIDATION_STUDY=NO; OFFICIAL_OOS=NO; PR_MERGED=NO.
HUMAN_APPROVAL_REQUIRED=YES; this is not GATE_A_DATASET_FREEZE.
