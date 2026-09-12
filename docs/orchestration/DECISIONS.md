# Decisions

## Approved human methodology decision: ordinary A-share equities only

2026-09-12: PILOT_INSTRUMENT_SCOPE=ORDINARY_A_SHARE_EQUITIES_ONLY;
PILOT_INSTRUMENT_SCOPE_DECISION=APPROVED. Scope decision blocker is resolved;
STATUS=RUNNING, HUMAN_APPROVAL_REQUIRED=NO while applying the approved policy.
Ordinary RMB equities on Main/STAR/ChiNext remain potentially eligible. CDR,
B-share, ETF/fund, bond/convertible, preferred, warrant and other instruments
are outside this release before data completeness is evaluated. No results or
profitability inform this decision. Source-backed classification and generic
eligibility must precede denominator correction; unknown types stay explicit.
689009's preserved SSE CDR listing evidence establishes its out-of-scope type;
its absent Sina factor is not required by the approved Pilot scope. Existing
source/checkpoint artifacts must be retained, not rewritten to hide earlier counts.
Continue existing R2 then R3; no freeze, study, OOS, PR merge or release authorized.


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


- Latest human continuation authorized focused amount acceptance, not tolerance
  widening or automatic Tencent promotion. Controller resumed RUNNING for review.
  Existing strategy code establishes amount REQUIRED for20-observation liquidity
  screening despite nullable provider schema. Audit reused1,719 rows and preserved
  every snapshot; unit mapping verified, rounding/error bound still undocumented.
  Terminal classification INSUFFICIENT_EVIDENCE, SECONDARY_ACCEPTANCE FAIL; stop
  BLOCKED on RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED, not Gate A.
  No methodology change, new provider, primary retry, freeze, study or merge.
  Details and reproducible metrics: docs/research/TENCENT_AMOUNT_ACCEPTANCE.md.


- Failover candidate review completed: six additional primary diagnostics failed
  before HTTP; classify operationally SYSTEMIC_TRANSPORT_FAILURE without
  downgrading primary historical authority. Tencent returned eight repeatable
  histories and matched 1,719 primary dates/OHLC; four amount differences remain
  unresolved after reuse of Sina snapshots plus one targeted raw request.
  CN_A_RAW_OHLCV_FAILOVER_V1 stays disabled; no secondary promotion, production
  failover, bulk retry or new exclusion. Stop only for the remaining narrow
  amount-precision evidence/policy decision, preserving all 657 original inputs.

- Current human failover authorization: resume R2 RUNNING for a bounded six-member
  primary operational diagnostic and independent secondary-route acceptance.
  Preserve primary historical authority and all 657 successful partitions. No
  bulk primary retry or automatic provider substitution. Version the selection
  policy; secondary use requires independent authority and cross-source parity.
  Prior exhausted-run stop is superseded only within this new diagnostic scope.
  Dataset publication/freeze, studies and PR merge remain prohibited until gates.

- 2026-09-11 bounded R2 recovery completed: all 5,178 members accounted for;
  657 RECOVERED_PRIMARY and 4,521 UNRESOLVED_REQUIRED_DATA after all three rounds.
  The final pass recovered 600605 and 600739; it did not resolve 600070, whose five
  actual requests are exhausted. All terminal failures are RemoteDisconnected,
  cause UNKNOWN. Existing policy permits neither fallback nor transport-gap
  exclusion. Stop BLOCKED for source-access/policy resolution, not Gate A; retain
  all partial partitions and evidence. No further retry, R1 reopening, incomplete
  publication, dataset freeze, study or PR merge is authorized.

- 2026-09-11 R2 recovery continuation: user explicitly directs successful
  securities to continue while failures queue as PENDING_RETRY. No R1 reopening,
  new provider, new exclusion, synthetic data, freeze or research. Source snapshots
  and failed-attempt metadata are immutable; final publication requires complete
  required inputs. Existing OHLCV acceptance defines no fallback. Final failed
  members must remain UNRESOLVED_REQUIRED_DATA unless actual recovery or existing
  authoritative policy explains them. Request controls and transport diagnostics
  do not justify guessing an anti-bot or lifecycle cause.

- 2026-09-11 implementation checkpoint: both source authority and separate
  CN_A_DAILY_OPENING_LIMIT_V1 validation PASS. Approval section9 permits retained
  frozen research costs: the unchanged 0.00001 transfer/clearing allowance is
  explicitly SIMULATION_ASSUMPTION, not a verified statutory rate. Its unresolved
  old source claim remains preserved in model_assumptions; no data authority
  was re-audited or weakened. R2 started with the accepted 5,178-member master.
  Stop at new external blocker R2_RAW_ROUTE_CONNECTION_CLOSED_600070 after three
  bounded transport failures. No substitution, security omission or incomplete
  dataset publication. Resume only after source access recovery/authorized route.

- 2026-09-11 human execution approval: PILOT_EXECUTION_CONVENTION_DECISION =
  APPROVED. Resume RUNNING without another execution-methodology approval.
  CN_A_DAILY_OPENING_LIMIT_V1 is a SIMULATION_ASSUMPTION, not an official exchange
  rule or proof of actual auction fills. Precommit parameters using completed t
  only; evaluate t+1 eligibility separately; raw open may price a fill only after
  conservative legal/status/liquidity-proxy gates pass. Missing/uncertain evidence
  means no-fill and explicit expiry. No future inputs may set order parameters.
  Source authority and execution-convention validation are separate gates; both
  must pass before R2. Dataset freeze and all studies remain unauthorized.

- 2026-09-11 source-recovery decision supersedes the original-PDF requirement.
  Historical locations return 404 in automated and user normal-browser access;
  classify them SOURCE_LOCATION_RETIRED_OR_UNAVAILABLE, never SOURCE_CONTENT_INVALID.
  Exact retired URLs are in docs/research/SZSE_RULE_CLAIMS.json. No retry this run.
  Accept reproducible rule-level evidence from accessible official SZSE materials;
  do not use mirrors or fabricate downloads. All four alternatives downloaded.
  Technical PDF p18 proves 2023-04-10 implementation; later notice proves publication
  2023-02-17 / 深证上〔2023〕98号 and 2026-07-06 supersession. It supplies identity,
  never 2026 behavior. Investor guidance retains its proper source classification.
  Preserve snapshots outside Git and per-source hashes/claim mapping inside Git.

- 2026-09-11 semantic review: source recovery exposed an execution-methodology
  mismatch, not just missing source bytes. Existing MARKET-at-next-open is not an
  exchange MARKET submission at opening auction. Ask for explicit limit/auction
  convention decision before materially changing that assumption. No decision has
  yet been received. Do not infer auction liquidity from daily OHLCV. No studies.
  Rule .5 corrects only preceding-regime identity/IPO classification; existing
  first-session no-fill preserved. A 2015 yearbook under a 2023 URL is rejected for
  Pilot fees; 0.0003 commission is a model assumption, not statutory rate. The
  0.00001 transfer-fee claim remains open, not fabricated or silently zeroed.

- 2026-09-11 user source resolution: intended SZSE source is the 2023 revision,
  publication 2023-02-17, 深证上〔2023〕98号, effective 2023-04-10, not publication
  day. The supplied April 10/11 official listing pages were retrieved and agree.
  Source identity is resolved. Fresh requests to the supplied notice and both
  PDF routes still returned 404; PDF bytes/hash remain unavailable. Do not
  promote MARKET_RULE merely from the user's link identification. Version .4
  and transition tests are complete; request file attachment to finish provenance.

- 2026-09-11: Docker runtime failure RESOLVED; existing volumes/containers
  preserved, API/frontend and database services verified. No accepted data
  authority was reaudited. Delisting fix .3 passes regression; MARKET_RULE remains
  PARTIAL because official SZSE 2023 source text could not be recovered. Do not
  substitute current rules or promote source acceptance from code tests alone.

- 2026-09-11: The previously specified GitHub identity 'MackenzieAhern' was a
  prompt typo. The intended and authenticated repository identity is
  'MakenzieAhern'. Existing Git configuration and attribution remain unchanged.
  PUSH_IDENTITY_MISMATCH = RESOLVED. Resume R1 without further identity approval.

- 2026-09-10 checkpoint: OHLCV/CSI300 route binding passes; market-rule acceptance
  remains UNVERIFIED. Do not begin R2 with unresolved delisting-period semantics.
  Pause publication for the explicit MackenzieAhern/MakenzieAhern spelling
  mismatch; preserve existing Git identity. This is not Gate A.

- 2026-09-10 acceptance: Sina factor route passes under
  `sina-multiplicative-asof-v1`: P(t)*H(t)/H(T), t<=T, pinned vintage, raw execution.
  Seven route gates pass; no claim of archived publication-time observations or
  full-universe availability. Continue R1 without another provider-choice prompt.

- 2026-09-10 approval: Sina adjustment-factor data is approved as a candidate
  acceptance route for the v1.1 A-share Pilot. It becomes authoritative only after
  reproducibility, semantic, temporal-safety and lineage validation passes.
  Legacy BaoStock acceptance recovery is no longer a prerequisite. No dataset
  freeze, Development, Validation or Official OOS is authorized by this decision.

- 2026-09-10: Continue on existing branch/PR. No scheduler, new branch or conversation.
- Preserve accepted SSE/SZSE/master/calendar work. Ancient 600721 is full-history-only.
- A legacy PASS claim is not checksum-linked pilot authority acceptance.
- Execution always uses raw prices. Provider adjusted close is not an economic cash flow.
- Persist Gates A/B/C and false OOS/release flags. Current research CLI already refuses
  execution without readiness; state files do not grant permission to bypass it.
- Keep generated evidence outside Git; commit small reproducible code and summaries only.
- 2026-09-10 R1: New Sina factors are CANDIDATE_ONLY, not an implicit provider
  substitution. Different adjusted-price algorithms are not treated as corrupt
  data or interchangeable factors. Stop under the explicit authority-ambiguity
  exception while preserving all new recovery evidence; no normal gate reached.
