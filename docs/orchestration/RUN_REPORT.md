# Controller run

RUN_ID = 20260911-R1-04
STAGE = R1
START_SHA = 7017909152233b2ff099d04053422a511e2abe07
END_SHA = Resolve with git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md
STATUS = BLOCKED_SOURCE_PROVENANCE
CHANGES = Verified/restored existing Docker project services; regression-validated .3 delisting fix; recovered official SSE archived source and recorded failed SZSE retrievals; updated persistent state without redoing accepted authorities.
TEST_RESULTS = Backend 353 PASS; frontend 74 PASS; Ruff/format/strict mypy/ESLint/TypeScript/build PASS; npm audit zero vulnerabilities. Docker engine 29.7.2; Compose v5.5.0; PostgreSQL/Redis/backend healthy; API and project frontend HTTP 200. GitHub CI pending this publication.
DATA_RESULTS = MARKET_RULE PARTIAL; source preflight FAIL. Source snapshots/checksums and failed-request metadata persisted outside Git. No pilot dataset/studies.
BLOCKER = SZSE_2023_RULE_SOURCE_UNAVAILABLE
NEXT_STAGE = Obtain checksum-verifiable official SZSE 2023 trading-rule text/notice, finish R1 source binding/audit, then R2/R3 if PASS.
HUMAN_APPROVAL_REQUIRED = YES

DOCKER_RECOVERY = PASS
DOCKER_RUNTIME_FAILURE = RESOLVED
SOURCE_AUTHORITY_PREFLIGHT = FAIL
SOURCE_MANIFEST_SHA256 = bcc43dc1239651b9bb8538d0434cb20acb71c490f074d2b0a31314f9daed94dc
MARKET_RULE_MANIFEST_SHA256 = 4910e229314ffe4479af3070dbfc5757236b469d9002db38afb3ef8e453af3d6
PILOT_DATASET_CREATED = NO
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
HUMAN_APPROVAL_GATE = NONE
PR_MERGED = NO

Prior seven authority PASS decisions preserved. The missing rule document is
not permission to restart ST/master/factor/price/benchmark acceptance. Code test
success is not equivalent to complete authoritative-source acceptance.
No raw market data or snapshots committed. No Docker data removed.
Actual final publication HEAD/CI is reported after push, not predicted here.
