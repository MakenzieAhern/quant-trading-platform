# Controller run

RUN_ID = 20260911-R1-05
STAGE = R1
START_SHA = 54f788d072f9e4f1553f2222157bfefe7e39435d
END_SHA = Resolve with git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md
STATUS = BLOCKED_RULE_BYTES
CHANGES = Recorded user source resolution; downloaded two official effective-date announcements; versioned Main/ChiNext transition in .4; added boundary/risk/lot/tick/suspension/cost/prefix tests; persisted request metadata and manifests outside Git.
TEST_RESULTS = Backend 354 PASS; Ruff/format/strict mypy PASS. Frontend unchanged (previous 74 PASS). GitHub CI pending this publication; actual outcome is associated with publication HEAD.
DATA_RESULTS = Effective date 2023-04-10 verified; notice/PDF retrieval still 404; PDF_SHA256 unavailable. Normalized rule checksum recorded. Full market-rule authority PARTIAL.
BLOCKER = SZSE_2023_RULE_BYTES_UNAVAILABLE
NEXT_STAGE = Obtain actual official PDF/notice files; validate source provenance before R2/R3.
HUMAN_APPROVAL_REQUIRED = YES

RULE_SOURCE_IDENTITY = RESOLVED_BY_USER
RULE_SOURCE_PROVENANCE = PARTIAL
RULE_EFFECTIVE_DATES = PASS
RULE_VERSION = cn-a-2010-2025.4
RULE_MANIFEST_SHA256 = cc582b47330923d331e48deb9e3a0818e1d9b2a3e439fa9fbe6315625e85bdce
SOURCE_MANIFEST_SHA256 = 9ceacf24b3ab83007bf8bdba4cee8f7ebb06d66d4d6b63391f9ec13a12ee7ed7
MARKET_RULE_AUTHORITY = PARTIAL
SOURCE_AUTHORITY_PREFLIGHT = FAIL
PILOT_DATASET_CREATED = NO
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
HUMAN_APPROVAL_GATE = NONE
PR_MERGED = NO

Implementation checks pass for board precedence, ST, listing age, price limits,
lots, ticks, suspension, transaction costs, input order and normalized checksums.
These are not substitutes for missing official rule bytes. Source documents
and errors retained under market-rules-user-resolution-20260911 outside Git.
All prior accepted research/data decisions preserved. No market ingestion run.
