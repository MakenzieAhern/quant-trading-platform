# Controller run

RUN_ID = 20260910-R1-01
STAGE = R1
START_SHA = 92a08589bead59227568888eabb97a071185fae4
END_SHA = 6acbbf1595c904d52e7b30d7a19f86dee1cd680f
STATUS = BLOCKED_AUTHORITATIVE_SOURCE_AMBIGUITY
CHANGES = Persistent roadmap/state/OOS lock; read-only R1-R3 gate checker and regression test; adjustment lineage recovery, bounded source probes and failed canonical source manifest.
TEST_RESULTS = Backend 350 PASS; frontend 74 PASS; Ruff/format/strict mypy/ESLint/TypeScript/build PASS; npm audit zero vulnerabilities; Python dependency audit no known vulnerabilities; PostgreSQL/Redis/three Compose variants/Alembic upgrade,current,check PASS; controller STOP as expected. CI pending checkpoint push.
DATA_RESULTS = BaoStock login failed twice; four Sina candidate samples repeated exactly; Windows Eastmoney raw/HFQ retrieved; methodology non-equivalence verified. Source preflight FAIL. No dataset or study. SSE/SZSE acceptance preserved without rerun.
BLOCKER = ADJUSTMENT_METHOD_AUTHORITY_AMBIGUITY: no audited definition reconciles legacy BaoStock, Sina multiplicative factors and Eastmoney HFQ.
NEXT_STAGE = Stay R1 until authoritative method is resolved and audited; then R2 and R3 automatically, stopping at Gate A.
HUMAN_APPROVAL_REQUIRED = YES

END_SHA identifies the validated implementation checkpoint; the following
documentation/state-only commit contains this report. Resolve its publication SHA
with `git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md`. No self-referential
commit hash or future CI outcome is invented. The final checkpoint response records
the actual published HEAD and CI conclusion; GitHub associates CI with that HEAD.

HUMAN_APPROVAL_GATE = NONE (explicit source-ambiguity exception, not Gate A).
SOURCE_MANIFEST_SHA256 = 7eec56c7d3ba16b137851686258b6a65ef59e83d4f7c291bf4b7331e67729fbb
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
PR_MERGED = NO

Before continuation, read MASTER_ROADMAP and project_state.json. Do not repeat
ST recovery or factor download samples without a changed evidence requirement.
The smallest input is the accepted adjustment definition/provenance or an explicit
resolution of the new candidate methodology; it does not authorize dataset freeze.
