# Blockers

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
