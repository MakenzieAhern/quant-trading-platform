# Blockers

## Current: Gate A approved; no active human blocker

Pilot v1 frozen, R4 engineering smoke in progress. The old Gate A wait is resolved.
Next gate is GATE_FULL_RESEARCH_DATASET_FREEZE after R5 full historical audit.
Unknown executable liquidity remains NO FILL, not a newly relaxed authority claim.
Formal studies, OOS, merge and release remain locked.

## Historical checkpoints below (superseded)

## Current: no engineering blocker; Gate A approval required

R2 complete and R3 all22 checks PASS. SINGLE_SMALLEST_BLOCKER=NONE.
STATUS=AWAITING_HUMAN_APPROVAL; HUMAN_APPROVAL_GATE=GATE_A_DATASET_FREEZE;
HUMAN_APPROVAL_REQUIRED=YES. This is the requested approval boundary, not a new
source-recovery or CDR-scope question. All5177 required ordinary A-share inputs
are complete; 689009 is out of scope under the approved methodology.
DATASET_AUDITED=YES; PILOT_A_SHARE_DATA_READINESS=READY; DATASET_FROZEN=NO.
Official daily suspension/tradeability remains unknown and execution fail-closed
under the existing approved convention. No optimistic fill assumption is authorized.
Do not freeze, run any study, merge PR12 or release. Await explicit Gate A approval.

## Historical blockers below (superseded)

## Current: no human blocker; approved scope implementation running

RESOLVED: PILOT_INSTRUMENT_SCOPE_REQUIRES_HUMAN_DECISION.
RETIRED AS REQUIRED DATA: SINA_FACTOR_BASELINE_UNAVAILABLE_689009.
The human has approved ordinary A-share equities only. The dated official CDR
evidence remains valid and its raw/factor failure snapshots remain preserved.
The full scope gate now PASS: 5178 classified, 5177 ordinary A shares, one CDR,
zero unclassified. R2 has resumed its remaining 2597 in-scope inputs from the
existing checkpoint. No additional methodology approval is required.
R1 acceptances unchanged; no freeze, studies, PR merge or new provider authority.

## Historical blockers below (superseded)


## Current: instrument-scope decision required

R2 BLOCKED; SINGLE_SMALLEST_BLOCKER=PILOT_INSTRUMENT_SCOPE_REQUIRES_HUMAN_DECISION.
The pre-blocker97eebf3 contract names CN_A and four boards but does not establish
ordinary-equities-only versus CDR-inclusive scope. Official SSE notice confirms
689009 is a CDR, listed2020-10-29; this fact alone does not authorize exclusion.
Full5178-row type-evidence inventory:1 confirmed CDR,5177 UNCLASSIFIED (not assumed
ordinary, not excluded). No other nonordinary instrument was positively established;
this is NOT a complete certified instrument census or zero-leakage PASS.
New sourced InstrumentClassification model is independent of eligibility. No filter,
master checksum, scope, strategy, factor baseline or frozen failover policy changed.
All657 primary/1923 secondary successes and2580 partitions/951927 raw rows unchanged.
The prior689009 empty-factor evidence remains unresolved if CDR is included.
Human must specify ordinary A-share-only versus CDR-inclusive Pilot scope before
classification/eligibility changes and R2 resume. Worker remains stopped.407 tests
and lint/type checks passed. No dataset publication, R3 PASS, freeze, study or merge.
Evidence:docs/research/R2_INSTRUMENT_SCOPE_AUDIT.md. HUMAN_APPROVAL_REQUIRED=YES;
this is not Gate A. Earlier master authority PASS does not certify instrument scope.

## Earlier checkpoints (superseded)



## Current: R2 factor availability blocker

R2 BLOCKED; HUMAN_APPROVAL_REQUIRED=YES; HUMAN_APPROVAL_GATE=NONE (not Gate A).
SINGLE_SMALLEST_BLOCKER=SINA_FACTOR_BASELINE_UNAVAILABLE_689009.
Accepted Sina HFQ URL returned HTTP200 with total=0/data=[] for689009.
No baseline can be inferred; no approved substitute/exclusion applies. No retry
of a non-transport failure, fabricated factor1 or third provider was introduced.
657 primary +1923 secondary complete inputs preserved;2580 securities partitioned,
951927 raw rows /6250 factor rows. One factor failure,2597 unattempted;2598 unresolved.
Worker stopped safely at a complete batch for human source resolution; no background
worker remains. Resume this checkpoint after resolving689009, never from zero.
All accepted R1 authorities and Tencent LIMITED_PRECISION_PARITY remain intact.
Entire available amount sample:17068 potential decisions,zero ambiguous (includes
7 separately audited decisions from689009's saved382 raw rows). Dataset unpublished,
unaudited,unfrozen; no studies,merge or release.406 tests/lint/type checks passed.
Full source/error/checksum evidence:docs/research/R2_SINA_FACTOR_COVERAGE_BLOCKER.md.

## Earlier checkpoints (superseded)


## Current decision-invariance acceptance

R2 RUNNING; HUMAN_APPROVAL_REQUIRED = NO. Prior amount-semantics stop RESOLVED
under the new human-authorized decision-invariance criterion, not guessed rounding.
Tencent upstream unit=10,000 CNY; AKShare returned unit=CNY; nominal granularity100 CNY.
659 available securities/244,772 rows,4,334 potentially evaluated amount decisions,
zero ambiguous decisions. All-date600666/2024-01-19 stress ambiguity is retained,
not hidden: already ST-excluded and not a scheduled evaluation date.
Expanded2,478-row overlap has no OHLC/date mismatch or outside-envelope amount outlier.
SECONDARY_ACCEPTANCE = PASS_FOR_PILOT; LIMITED_PRECISION_PARITY, not exact tick parity.
CN_A_RAW_OHLCV_FAILOVER_V1 frozen SHA256
3fb1941b93f127774ec228d27bb78074d48dc2d35ee29e98826a3b207472f740.
Impact audit SHA256=d950fdc3543fbf8373370c8013f8a8a8579140e8b82523f7d0961033a280323c.
Every recovered partition must pass the same unchanged rule/interval check before
admission. Preserve657 primary successes; resume4,521 pending, no primary refetch.
No new exclusion, dataset freeze, study, merge or release. All R1 authorities intact.
Full trace/evidence:docs/research/PILOT_AMOUNT_DECISION_IMPACT.md.

## Earlier checkpoints (superseded)


## Current focused amount authority blocker

RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
PILOT_AMOUNT_REQUIREMENT = REQUIRED; SECONDARY_ACCEPTANCE = FAIL.
Unit10,000 CNY is supported by the pinned SDK; rounding/aggregation semantics and
an error bound sufficient for the existing liquidity screen remain unestablished.
An observed51-CNY maximum is not a documented bound; no tolerance is widened.
Generic schema nullability cannot override required research liquidity inputs.
See docs/research/TENCENT_AMOUNT_ACCEPTANCE.md. No production fallback or new provider.

## Previous candidate evidence checkpoint (superseded)


## Current smallest blocker: secondary amount precision authority

RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
R2 BLOCKED; human input/evidence required; not Gate A.
The six-member primary probe failed 6/6 before HTTP: operationally systemic,
not an isolated 600070 issue. Primary historical acceptance remains unchanged.
Tencent returned eight repeatable candidate histories, including 600070, 300336,
000732 and new IPO 603125. No sampled OHLC/date mismatch; four amount differences
exceed direct hundred-CNY display rounding by 0.02–1 CNY. Sina corroborates
Tencent's rounding base but does not establish the primary vendor's processing.
Do not force cross-source parity PASS or introduce a blanket expanded tolerance.
Required resolution: supported precision evidence or explicit limited amount
precision policy approval. Existing 657 successes remain intact; 4,521 production
gaps remain. No secondary was promoted or used for production ingestion.
Details and exact rows: docs/research/R2_RAW_FAILOVER_ACCEPTANCE.md.

## Prior acquisition blocker (superseded by current failover review)

## Active terminal blocker after complete bounded recovery

SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070.
STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; not Gate A.
All 5,178 members were processed; two retry passes recovered 151 then 2 inputs.
657 inputs/partial partitions retained; 4,521 terminal required raw gaps remain.
Every remaining failure is final-round RemoteDisconnected before HTTP response,
including 600070 (five actual requests total). Root cause remains UNKNOWN.
No accepted raw fallback and no existing exclusion for transport failure exists.
Do not reissue the exhausted requests, fabricate bars, infer suspension, omit any
security, or publish the incomplete dataset. Full failure manifest is preserved
outside Git at pilot-akshare-20260911/recovery-failure-manifest.json, SHA-256
e1279921716ebf3c3d424acfedceb7b8f70b950dcdd4f6372829e41c811488ce.
External source-access recovery or an explicit policy decision is now required;
no generic provider choice or new exclusion threshold has been requested.
All R1 decisions remain accepted; no dataset audit/freeze/study/merge occurred.

## Earlier active-recovery checkpoint (superseded)

Prior continuation: failures are NON-TERMINAL PENDING_RETRY while the independent
R2 queue progresses. STATUS = RUNNING; HUMAN_APPROVAL_REQUIRED = NO.
No new human source choice is requested. The user superseded the prior stop below.
See external recovery-failure-manifest.json for the full pending set; 600070 is
not silently omitted. Final publication is prohibited until required gaps close.
R1 remains PASS. Only after the bounded final retry passes and existing-policy
check may this become a terminal human blocker again.

## Preserved prior checkpoint (superseded)

SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070
HUMAN_APPROVAL_REQUIRED = YES (external source-access recovery, not dataset freeze).

The exact accepted AKShare/Eastmoney raw/unadjusted request for CN-A:SSE:600070,
2023-01-01 through 2024-07-31, closed before an HTTP response:
- Python urllib: RemoteDisconnected, "Remote end closed connection without response".
- Native PowerShell Invoke-WebRequest: "An error occurred while sending the request".
- Windows curl: error 56, "schannel: server closed abruptly (missing close_notify)";
  HTTP_STATUS=000.

Three bounded transport diagnostics completed; no repeated retry loop remains.
Do not interpret this as proof of absent history, or as a Docker failure.
Do not drop 600070, synthesize missing data, change providers, or downgrade the
previous accepted OHLCV route decision to manufacture full-universe acceptance.
The successful 300336 canary proves only that its particular request succeeded.

Required external change: recover access/response for this exact accepted request,
or explicitly authorize a complementary raw-history route for the gap.
Preserve the failure metadata when a recovered response is later snapshotted.
Failure artifact: external staging/pilot-akshare-20260911/failure-manifest.json.
No full dataset has been published; R3 is not yet runnable.

RESOLVED: PILOT_EXECUTION_CONVENTION_DECISION_REQUIRED.
RETIRED: original SZSE attachment dependency; do not retry retired URLs.
RESOLVED: DOCKER_RUNTIME_FAILURE and PUSH_IDENTITY_MISMATCH.
Market source gate and separate execution gate both PASS; seven data authorities
remain accepted. No strategy/studies/freeze/merge authorized. This is NOT Gate A.
