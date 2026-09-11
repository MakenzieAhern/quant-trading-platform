# Autonomous Quant Project Checkpoint

## Latest R2 systemic diagnosis and candidate failover checkpoint

STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; HUMAN_APPROVAL_GATE = NONE.
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
PRIMARY_ROUTE_STATUS = PRIMARY_SYSTEMIC_TRANSPORT_FAILURE (6/6 fixed probes).
RAW_OHLCV_PRIMARY_AUTHORITY = PASS; SOURCE_AUTHORITY_PREFLIGHT = PASS (existing,
unchanged primary manifest, not a secondary promotion).
SECONDARY_ACCEPTANCE = NOT_PROMOTED; CROSS_SOURCE_PARITY = PARTIAL.
CN_A_RAW_OHLCV_FAILOVER_V1 = CANDIDATE_NOT_ENABLED.

32 Tencent candidate requests cover 8 securities/two years/two repetitions;
2,418 normalized candidate rows repeat exactly. Six cached primary controls share
1,719 dates, with zero material OHLC/date mismatches. Four unexplained amounts
remain; prior Sina histories plus one targeted 300336 request corroborate the
rounding base but do not prove the remaining primary vendor precision behavior.
No additional tolerance, source substitution, arbitrary exclusion or strategy
performance criterion was introduced. Source snapshots and field-by-field parity
are external; full details in docs/research/R2_RAW_FAILOVER_ACCEPTANCE.md.

PRIMARY_SUCCEEDED = 657; PRIMARY_FAILED_SECONDARY_RECOVERED = 0;
PRIMARY_FAILED_SECONDARY_FAILED = 0 (no production secondary attempts);
AUTHORITATIVELY_NO_DATA_EXPECTED = 0; UNRESOLVED_REQUIRED_DATA = 4521.
All original raw/factor inputs, Parquet files and checkpoint hashes verified
unchanged. Partial production raw rows = 244,073. Candidate rows are not admitted.
No final manifest or Pilot Dataset was published; no R3, freeze, Development,
Validation, OOS, strategy, PR merge or release occurred. All R1 decisions preserved.

Primary probe SHA256 = 513f04d0ec47408b1f49503af5168eb07d2fbf5270b6a661f4c8e32bf3157d9c
Candidate audit SHA256 = ff0e31d2ffca13fb174995a1bd31eb3f4a6342c0c013dfc26779708469c3db47
Policy SHA256 = 47316572b10b3e1f8cc35362614958a7265463be25432f3de2b4a149841d3dcc
Tests: 11 focused recovery checks PASS; full backend 400 PASS; Ruff/format/mypy PASS.
Finished probes and persistent access-denial stops cannot restart on rerun.
Existing feature branch/PR12 retained. No Git identity change. Final milestone CI
is checked after push; this checkpoint does not claim a future CI result.

## Prior checkpoint (superseded by current failover review)

## Terminal R2 recovery checkpoint

STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; HUMAN_APPROVAL_GATE = NONE.
SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070.
Initial pass: 5,178 / 5,178 processed, 504 completed, 4,674 pending.
First retry: 4,674 / 4,674 processed, 151 recovered, 4,523 pending.
Final retry: 4,523 / 4,523 processed, 2 recovered (600605, 600739), 4,521 unresolved.
Last terminal source failure UTC: 2026-09-11T11:49:51.552627+00:00.
The worker ended with FINAL_PUBLICATION_PROHIBITED; no retry process remains.
657 RECOVERED_PRIMARY (493 SSE, 164 SZSE); 0 accepted fallback recoveries;
0 AUTHORITATIVELY_NOT_EXPECTED_TO_HAVE_DATA; 4,521 UNRESOLVED_REQUIRED_DATA
(1,794 SSE, 2,727 SZSE). Every terminal error is RemoteDisconnected from the
accepted Eastmoney raw endpoint. Error classification UNKNOWN, not assumed
anti-bot, outage or lifecycle-driven. 600070 actual requests = 5, all exhausted.
No accepted fallback or existing transport-gap exclusion permits publication.

All master IDs accounted for exactly once in completed/pending sets; no overlap
or silent drop. Failure history has unique security/round slots, every pending
entry is round 2 terminal, and failure manifest exactly matches checkpoint.
No provider access-denial flag or abandoned .tmp file was found.
657 partial securities: 244,073 raw rows, 1,565 factor rows, quality failures 0.
Source/partition SHA checks pass during offline materialization. These are partial
raw/factor checks, NOT full R3 dataset audits or proof of complete observations.
No final input-manifest.json exists. All data and failure evidence remain outside Git.

External evidence under pilot-akshare-20260911:

- recovery-checkpoint.json SHA-256: ffdc46937ecbd30f74a28660ef1769d2a7b8506ef65d0f1c2ae45ddac4841a68
- recovery-failure-manifest.json SHA-256: e1279921716ebf3c3d424acfedceb7b8f70b950dcdd4f6372829e41c811488ce
- partition-checkpoint.json SHA-256: 7c2916446fc867a39b41aa45a7062c44452be15fd2708a9b0e65882f5e573896
- 600070-recovery-result.json SHA-256: 115ed5b78155e53e9f71396eab1c3baee21ef746808f14b4be7e360ea5ac4185
- recovery-completion-report.json SHA-256: be02bd9cba43320007fe7d6731fcdd060f947d63ca23d6d942ee07c6dcafc887

Final offline repeat reproduced the same partition-checkpoint SHA-256 with no
new network request; six focused recovery tests re-run PASS. Controller JSON
verified BLOCKED with all dataset/study permissions unchanged. GitHub login
re-verified MakenzieAhern; branch feature/a-share-research-v1.1.

SOURCE_AUTHORITY_PREFLIGHT = PASS; all R1 authority decisions unchanged.
PILOT_DATASET_CREATED = NO; PILOT_A_SHARE_DATA_READINESS = BLOCKED.
DATASET_AUDITED = NO; DATASET_FROZEN = NO; R3 = NOT_RUN.
DEVELOPMENT_STUDY = NOT_RUN; VALIDATION_STUDY = NOT_RUN; OFFICIAL_OOS = NOT_RUN.
PR12 remains OPEN/unmerged; no new PR, release or strategy execution.
Existing feature branch and MakenzieAhern identity retained. Backend 395 tests,
Ruff/format/strict mypy and preceding milestone CI passed; terminal documentation
checkpoint CI is checked after its single milestone push.

## Preserved active R2 recovery continuation (superseded by terminal state above)

STATUS = RUNNING; HUMAN_APPROVAL_REQUIRED = NO. Prior stop below superseded.
Independent queue continues through per-security failures; 600070 = UNRESOLVED_REQUIRED_DATA.
Three same-construction SSE controls succeeded, 382 rows each. No fallback is in
the current accepted OHLCV manifest; no new exclusion policy is introduced.
At this checkpoint: 657 securities partitioned, 244,073 raw rows, 1,565 factor rows;
quality failures 0, final publication NO. Periodic counts are checkpoint snapshots,
not final-universe acceptance. External pilot-akshare-20260911/recovery-checkpoint.json
and partition-checkpoint.json retain current counts and exact file hashes.
First acquisition pass completed all 5,178 members: 504 completed, 4,674 pending.
Round 1 completed all 4,674 pending members and recovered 151 additional inputs.
Final round 2 is RUNNING after the fixed 60-second backoff for the remaining 4,523
members; the full queue's retries are not yet exhausted. No dataset publication or full R3 audit
is claimed. The last first-pass completion, 300750, reused accepted raw/factor sample snapshots; it
does not establish a new live network recovery.
Round-1 result: 4,674 / 4,674 processed, 151 additional primary recoveries.
The first two were 600419 and 600420, each 382 rows. 4,523 inputs entered final retry.
600070 exhausted its last authorized request at 2026-09-11T08:29:25.145713Z;
RemoteDisconnected before HTTP response, recorded at 08:29:26.078749Z. Actual
requests total five (three prior client diagnostics and two new recovery slots).
Its terminal classification is UNRESOLVED_REQUIRED_DATA; root cause UNKNOWN.
No accepted fallback or existing transport-gap exclusion exists. Evidence is in
600070-recovery-result.json outside Git. No further 600070 request is authorized;
other securities continue their independent final pass, with final publication barred.
Final-pass progress snapshot: 4,390 / 4,523 processed, two additional primary recoveries.
Milestone feabf7055fab86d72ccde1d0d75ae8ef8d442036 is pushed; CI 34579627544 SUCCESS.
First-pass milestone bfb89fb26dd39422da14bf2f1eab2e6c1de9637f is pushed;
CI 34563889226 completed SUCCESS. No PR merge or dataset freeze occurred.
After recording the source failure at 2026-09-11T05:07:34.160687Z, the Windows
process hit WinError 5 while replacing the WSL-backed checkpoint (no separate
exact error timestamp was captured). Both old and newer temporary checkpoints were preserved;
the newer one was verified as the same state plus two failure records and restored
using WSL-native publication. Exact failure timestamps and provider attempt slots
were retained; no network request was replayed. Evidence is external
checkpoint-publication-recovery.json and its before/after snapshots.
Progress reads now use WSL-native Python, avoiding Windows file-sharing locks.
The shared atomic save retries only PermissionError during publication of the same
bytes, at most five attempts with 0.1/0.2/0.4/0.8-second backoff; persistent failure
still retains the prior checkpoint and temporary bytes. Six focused tests and
395 backend tests PASS; Ruff, format and strict mypy PASS. R2 resumed from the
preserved round-1 checkpoint, not from zero.
Checkpoint-fix milestone b1be221fc793642be07356cbf98764011a34eb08 is pushed;
CI 34565166603 completed SUCCESS. The active recovery worker uses this fix.
The scheduler now uses two workers with two-second inter-batch pacing and a
20-second cooldown after ten consecutive failed batches. Three fixed rounds,
30/60-second round backoff, no jitter; no repeated failed request on restart.
Original failure evidence remains untouched. Backend 395 tests PASS; Ruff,
format and strict mypy PASS. Request construction comparison is external
request-comparison.json; no proxy, standard Python-urllib/3.12 header, 35s timeout.
The earlier budgeted 600070 request used the standard requests 2.34.2 Session on
the same accepted URL at 2026-09-11T01:54:36.190841+00:00. It also closed before
HTTP response (ConnectionError wrapping RemoteDisconnected). This consumes the
round-1 recovery slot; it is not an additional provider or a repeated slot.
At that point, three prior diagnostic requests plus this request made four actual
requests; the round-2 slot subsequently failed as recorded above. Root cause remains UNKNOWN.
Five focused ingestion tests PASS, including physical checksum repeatability,
lost-receipt reconstruction and detection of modified partition bytes.
Recovery-test milestone 6cf7623c05844559540af76d5b3f71af1a9233f5 is pushed to the
existing feature branch; CI 34554480884 completed SUCCESS. PR #12 remains unmerged.
Lifecycle-only expected-session check: every one of the 5,178 accepted members
has at least one calendar session on/after listing and before delisting in the
Pilot interval. Zero members qualify as having no expected sessions solely from
listing/delisting boundaries. This does not infer suspension or excuse missing bars.

## Preserved prior checkpoint (superseded by active R2 recovery above)

RUN_ID = 20260911-R1-R2-07
START_SHA = 14c9f8c4c5a616442775d070f26aa34e858785e6
END_SHA = Resolve with git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md
CURRENT_STAGE = R2
STATUS = BLOCKED
BRANCH = feature/a-share-research-v1.1
PR = 12 OPEN / UNMERGED
CI = Verify final publication HEAD after push

PILOT_EXECUTION_CONVENTION_DECISION = APPROVED
MARKET_RULE_AUTHORITY = PASS_FOR_PILOT
EXECUTION_CONVENTION_VALIDATION = PASS
SOURCE_AUTHORITY_PREFLIGHT = PASS
FULL_HISTORY_RULE_AUTHORITY = PARTIAL

Official source claims and simulated execution are now independent gates.
The existing 14 SZSE snapshots support 27 official claims, all VERIFIED.
The old unverified transfer-fee claim remains preserved as an explicitly
non-statutory frozen research allowance under approval section9, not deleted
or promoted to official fact. Rates unchanged. SSE STAR quantity metadata was
checked against official 2019-07-19 Q5-Q6 at
https://edu.sse.com.cn/tib/qa/c/4866268.shtml (raw/meta retained outside Git).

CN_A_DAILY_OPENING_LIMIT_V1 is a SIMULATION_ASSUMPTION. Immutable limit=raw close(t),
signal after close(t), intended next calendar session, independent legal/status/
conservative daily-proxy eligibility, raw OPEN only after acceptance. Unfilled
instructions expire; no synthetic missing bars or extra slippage. The existing
RiskEngine/OMS/broker/portfolio path remains shared. No exact auction-fill claim.
The 1% daily-volume cap is ex-ante model conservatism, not auction liquidity proof.
README, methodology and research report permanently link the limitations.

Backend = 390 tests PASS
Execution convention = 36 focused tests PASS
Ruff / format / strict mypy = PASS

R2 input acquisition started against the 5,178-member accepted master.
A targeted delisting canary 300336 has 91 raw bars and a parsed HFQ curve.
The first fixed-order staging member 600070 failed before receiving HTTP bytes
in three bounded clients. Complete-universe staged count=0; no Parquet publication,
dataset manifest or dataset audit is claimed. A resumable acquisition command,
source metadata and explicit failure manifest remain. Full partition materialization
and R3 audit remain future work after this external access failure is resolved.
Previously accepted master/ST/adjustment/OHLCV/benchmark work was not repeated.

RULE_MANIFEST_SHA256 = cf8689d3e8269ba83bf03fe0b872689d10c441fabd7bf38ded72e30e38ca6583
NORMALIZED_RULE_SHA256 = 5569489384b3af7c7a81c39e6245e27b30bd064e7b801e411fe71de1fd7fd7f1
EXECUTION_VALIDATION_SHA256 = eae4180d8ac77495a82939a165dd94e8fbcf44ff9ad81cc3380c47d97a65f77a
SOURCE_PREFLIGHT_SHA256 = c549b64c562a5b5a08bd7ec7f9c62ba8d58df77ce0eac5eb66ebcc1d7d2ea859
R2_FAILURE_MANIFEST_SHA256 = dc3de6a08fb5377161e17cbf745c4bb51a3ee4535aa30964717b55b3ce3a43ff

DOCKER_RECOVERY = PASS
DOCKER_ENGINE_HEALTHY = YES
DOCKER_COMPOSE_HEALTHY = YES
POSTGRESQL_HEALTHY = YES
REDIS_HEALTHY = YES (PONG)
BACKEND_HEALTHY = YES (/api/health 200)
FRONTEND_HEALTHY = YES (configured 5173 HTTP200)

PILOT_DATASET_CREATED = NO
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
HUMAN_APPROVAL_GATE = NONE (not Gate A)
HUMAN_APPROVAL_REQUIRED = YES
SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070
PR_MERGED = NO
V1.1.0_CREATED = NO

Next external action: restore the accepted 600070 raw-history request or authorize
a complementary source. Do not restart acquisition, discard source failures,
reopen accepted authorities, merge PR12, freeze, or run any study.
