# Current state

## Latest terminal checkpoint: 2026-09-11 R2 recovery exhausted

STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; HUMAN_APPROVAL_GATE = NONE.
SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070. Not Gate A.
All 5,178 members completed the initial pass and both fixed retry passes.
657 primary inputs have separate raw/factor Parquet partitions (493 SSE, 164 SZSE):
244,073 raw rows, 1,565 factor rows, zero partition quality failures.
4,521 required inputs remain UNRESOLVED_REQUIRED_DATA (1,794 SSE, 2,727 SZSE),
all final-round RemoteDisconnected from the accepted Eastmoney raw endpoint.
600070 used five actual requests including three preserved prior diagnostics;
cause UNKNOWN. No accepted fallback or existing transport-gap exclusion applies.
No additional retry is authorized by the exhausted policy. No security was dropped.
R1/source preflight and execution convention remain PASS; no authority re-audit.
Pilot Dataset NOT created/audited/frozen. R3 and all studies NOT run; PR12 NOT merged.
Next: external source-access recovery or explicit source-policy resolution, then
resume from preserved inputs, not from zero. Do not invent a replacement provider.
Final evidence: external pilot-akshare-20260911/recovery-completion-report.json,
recovery-failure-manifest.json and recovery-checkpoint.json; hashes in RUN_REPORT
and .research/project_state.json. Backend 395 tests and CI passed before this
documentation-only terminal checkpoint; final milestone CI is checked separately.

## Historical checkpoints below (superseded)

Prior continuation: R2 RUNNING, HUMAN_APPROVAL_REQUIRED = NO.
User authorized independent queue progress and bounded final retries. Original
600070 evidence is preserved; old BLOCKED checkpoint below is superseded.
SSE controls 600000/600004/600006 returned 382 rows each with identical construction.
Cause remains UNKNOWN, not guessed as anti-bot or delisting-induced loss.
Two bounded workers; three rounds (0,30,60 second backoff), no jitter; immutable
per-attempt metadata. 600070's prior failure is queued, not immediately retried.
Partial partitions: 190 securities / 69,240 raw rows / 395 factors at this checkpoint.
Live external recovery-checkpoint.json and partition-checkpoint.json are authoritative
for subsequent progress; the final dataset remains unpublished. All R1 PASS unchanged.

Previous checkpoint: R2 BLOCKED: R2_RAW_ROUTE_CONNECTION_CLOSED_600070. Not Gate A.

The 2026-09-11 execution convention decision is APPROVED and implemented.
MARKET_RULE_AUTHORITY = PASS_FOR_PILOT (official claims only).
EXECUTION_CONVENTION_VALIDATION = PASS (CN_A_DAILY_OPENING_LIMIT_V1,
SIMULATION_ASSUMPTION, not actual auction reconstruction).
SOURCE_AUTHORITY_PREFLIGHT = PASS. All seven accepted data authorities preserved.

27 official SZSE claims / 14 preserved sources have no unresolved official claims.
The retained 0.00001 transfer/clearing allowance remains an explicitly frozen
research cost assumption, NOT a verified statutory rate; its old unresolved
provenance is retained in the ledger's model_assumptions inventory. User section
9 permits already accepted/frozen research costs. No fee was zeroed or changed.
Full-history rule authority remains PARTIAL; no future regime is imported.

Backend 390 PASS; Ruff, format and strict mypy PASS. V1 uses completed-session
raw close as its immutable limit, next accepted calendar session only, independent
eligibility, raw OPEN only after eligibility, zero extra slippage, explicit expiry.
Tests cover BUY/SELL, ST/boards, IPO/relisting, dates, bounds/ticks/lots, unknown/
missing/suspended/locked states, costs, replay and reversed input inventories.

R2 input staging enumerated 5,178 eligible master securities, prioritizing
delisting retention. First scheduled member CN-A:SSE:600070 could not be retrieved:
Python RemoteDisconnected; PowerShell send failure; curl error 56 / HTTP000.
This is an external connection failure, not evidence that history is absent.
A same-route canary CN-A:SZSE:300336 returned 91 raw bars and a valid HFQ curve.
No security was dropped; no alternate provider, synthetic bars or factors used.
The canary is NOT a published dataset or a completed full-universe partition.

External roots:
- pilot-execution-20260911: rule audit, normalized rules, execution validation,
  source-authority-preflight.json.
- pilot-akshare-20260911: source snapshots/metadata and failure-manifest.json.

Next: restore the exact accepted route for 600070 (or obtain explicit approval
for a replacement source), preserve failed attempt evidence, resume R2 input
staging, then implement/complete partition publication and all R3 audits.
The staging command is only input acquisition, NOT a finished dataset builder.

Docker/PG/Redis/backend/frontend healthy; API and port5173 HTTP200.
Branch feature/a-share-research-v1.1; MakenzieAhern; PR12 open/unmerged.
Dataset not created/audited/frozen. No Development, Validation, OOS or strategy run.
Canonical artifact checksums are in .research/project_state.json and RUN_REPORT.
