# Controller run

RUN_ID = 20260910-R1-02
STAGE = R1
START_SHA = 5e4903a14005019d7058a4b5ff18bee170ae09ae
END_SHA = Resolve with git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md
STATUS = AWAITING_HUMAN_PUSH_IDENTITY_CLARIFICATION
CHANGES = Sina Decimal parser/audit and regression; frozen adjustment convention; exact OHLCV/CSI300 binding; main-board registration effective-date correction; orchestration checkpoint.
TEST_RESULTS = Backend 352 PASS; frontend 74 PASS; Ruff/format/strict mypy/ESLint/TypeScript/build PASS; npm/Python audits no known vulnerabilities; Docker backend/PostgreSQL/Redis healthy; development/test/release-overlay Compose configs PASS; Alembic upgrade/current/check PASS. No CI for unpushed changes.
DATA_RESULTS = Five Sina factor samples repeated; 21 matched SDK RAW/QFQ/HFQ dates and six raw control dates checked; four corporate-action equations passed; OHLCV five samples repeated; CSI300 382 sessions aligned/repeated. Three acceptance manifests and all listed artifact checksums verified. No dataset/study.
BLOCKER = PUSH_IDENTITY_MISMATCH: required MackenzieAhern; actual Git/GitHub identity MakenzieAhern. Identity unchanged; clarification requested.
NEXT_STAGE = Stay R1; after identity clarification publish checkpoint, complete delisting-period market-rule mapping/audit, then R2/R3 only if source preflight passes.
HUMAN_APPROVAL_REQUIRED = YES

ADJUSTMENT_AUTHORITY = PASS
ADJUSTMENT_TEMPORAL_SAFETY = PASS (frozen as-of convention; not archived knowledge-time data)
OHLCV_AUTHORITY = PASS (route/sample scope)
BENCHMARK_AUTHORITY = PASS (CSI300 price index)
MARKET_RULE_AUTHORITY = UNVERIFIED
SOURCE_AUTHORITY_PREFLIGHT = FAIL
SOURCE_MANIFEST_SHA256 = 541f7eb754d92c27b094f077ab23e37ff1506947330d59afe368136864ae2b19
HUMAN_APPROVAL_GATE = NONE (push identity clarification; not Gate A)
PILOT_DATASET_CREATED = NO
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
PR_MERGED = NO
PUSH_PERFORMED = NO
REMOTE_SYNCHRONIZED = NO (local checkpoint differs from remote)

R1 review found a remaining rule-coverage issue: the boolean status schema cannot
represent delisting-period first-day limits. 300336 on 2023-06-12 is an official
example; either is_st value still yields a 20% limit. Do not promote MARKET_RULE
or start materialization until fixed/audited. This engineering remains authorized;
identity clarification concerns push policy, not routine coding/provider choice.

No raw datasets, snapshots, PDFs or provider caches committed. SSE/SZSE/master/
calendar acceptance preserved. Evidence lives under external staging directories
sina-acceptance-20260910, raw-route-20260910, benchmark-route-20260910.
Uncreated-dataset counts/hashes are unavailable, not zero. Gate A NOT reached.
