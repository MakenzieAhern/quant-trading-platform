# Pilot v2 freeze, R4 and R5 source checkpoint

## Completed: exact approved v2 freeze and fresh engineering smoke

All approved v2 counts,25 recorded R3 checks, partition bytes and eight component
hashes reproduced before freeze. Immutable receipt canonical SHA256:
`f9add5f27e310d8c355c8c9d56326a2baa22f98eb49d0dffc6d20f653635bcb3`.
Frozen at2026-09-12T14:11:48.249819+00:00, implementation Git08bdc45099f21fbe6dbda48e0bd4ec69d59c4881.
Current accepted Pilot: `cn-a-pilot-akshare-20230101-20240731-v2`.
Manifest `187b8c31d333fa33c5784d31bca60949e44a0c3a0c37a021235e49115bf92600`.
V1 remains frozen/superseded/acceptance INVALIDATED; no original data or evidence
was overwritten. V2's original manifest publication-stage not-frozen note remains
historical metadata; its separate later freeze receipt supplies current status.
Shared immutable-writer tests remain enforced; any v2 dataset correction needs v3.

R4 v2 PASS: full/reversed/prefix replay, PIT master, factors/winsorization/scoring,
construction/risk/OMS/execution, no-fill accounting/analytics/benchmark, persistence,
API and actual UI. Run `e2373467-ccda-5892-84f0-c20dca8e6736`, result checksum
`5019aca8af83e845159b3c8813b835609ca306b7d18f3897ea9984e0c33aa2a4`.
Configuration unchanged: `4b65a80b36c44a8aef34ff50d81d76625b11a49d6b29bce124c718eb69f33255`.
API verifies21 exact metrics,382 points per curve,7 rebalances and no fabricated
trades/holdings. Actual UI shows v2 lineage, all21 metric labels,382 SVG curve
points and OOS not run. Positive-fill accounting is separately covered by synthetic
tests; this real no-fill smoke does not certify full corporate-action accounting.

### PILOT_ENGINEERING_SMOKE_ONLY comparison

| Diagnostic | V1 (invalidated dataset) | V2 |
| --- | ---: | ---: |
| Signals (RiskEngine proposals) |140|140|
| Orders |140|140|
| Fills |0|0|
| Final equity, CNY |1000000|1000000|
| Total return |0|0|

Three newly retained members contribute555 raw bars.688287 adds one factor row
at every rebalance; all7 score hashes change, all7 targets remain unchanged.
688086/688555 exit before the first rebalance.600190's listing correction precedes
warm-up; Pilot raw/factor/daily-state logical hashes match v1, with no Pilot effect.
No parameter tuning or profitability acceptance. Replay command:
`python -m scripts.compare_pilot_smoke --root "$RESEARCH_ROOT" --repository "$REPOSITORY"`.

## R5 progressed, then stopped at a genuine methodology boundary

Full target remains2010-01-01..2025-12-31, not silently shortened. Corrected saved
current-and-exit inventories yield5432 provisional overlapping lifecycles across
all four boards, NOT a certified ordinary-share master. Full2009 baseline,
instrument and dated code/board transition checks remain pending. This count
includes the known CDR and is not reported as final dataset securities.
All124 pre-Pilot exits overlapping2010-2025 have a preserved Sina factor baseline;
this is availability evidence, not full factor/event authority. Saved2010 raw
controls and accepted Pilot partitions are reused, not fetched from zero.

The old BaoStock0.8.9 host still fails10002007. The official0.9.3 wheel was
hash-verified and inspected; its public-api.baostock.com endpoint works. Isolated
probes recovered four security-year dividend responses for600000/600036 in2010
and2025. Project dependencies, accepted Sina factors and frozen datasets unchanged.
No claim that corporate-action data is generally unavailable remains.

The concrete counterexample is600036's2010 rights issue. The issuer notice2010-008
(published2010-03-09) records0.13 rights per share,8.85 CNY subscription price,
record dateMarch4, paymentMarch5-11 and scheduled successful ex-dateMarch15.
SSE's2011 factbook (PDF103, printed95) confirms March19 listing and inventories17
2010 SSE rights issues. BaoStock's2010 dividend response contains only the July1
cash dividend, not this rights issue. A successful dividend query is not a complete
corporate-action census; adjustment factors cannot replace cash/share events.

`CORPORATE_ACTION_POLICY.md` explicitly declares RIGHTS_RELATED_EVENT unsupported.
The common portfolio engine rejects it even with complete source terms; a new
regression proves no automatic cash/quantity change. Choosing subscription,
forfeiture, funding/rounding, or exclusion of affected intervals/holdings changes
research methodology. No such choice is implied by permission to fetch full history.
The source is available; the required economic treatment is not approved.

SINGLE_SMALLEST_BLOCKER = FULL_HISTORY_RIGHTS_ISSUE_TREATMENT_REQUIRES_HUMAN_DECISION.
Required input: approve a deterministic rights participation/accounting policy
(including insufficient cash and listing availability), or explicitly approve a
bounded eligibility policy and how existing holdings are treated. No exclusions,
cash injections, inferred subscriptions or forfeitures were applied.

Full master/ST/raw/adjustment/calendar/benchmark/rule/corporate-action coverage
and audits remain incomplete. In particular, official2015 fee evidence establishes
a historical fee basis/rate transition; the provisional model's constant allowance
cannot be treated as official2010-2025 authority. That is queued engineering work,
not an additional human decision being requested at this checkpoint.

REQUESTED_START_DATE=2010-01-01; VERIFIED_SAFE_START_DATE=NOT_ESTABLISHED.
No later start has been verified across all eight required authorities; do not
claim2010 impossible, invent a safe date or change the reserved research split.
Full dataset CREATED/AUDITED/FROZEN=NO; all final counts and manifest are unavailable,
not zero. Full-freeze gate has NOT been reached. Pilot v2 acceptance is unaffected.

Source URLs, UTC retrieval times, PDF/wheel/source hashes and probe receipts:
`.research/reports/r5-source-preflight.json`. External snapshots live under
`staging/full-corporate-action-preflight-v1`, `full-adjustment-preflight-v1` and
`full-rule-preflight-v1`; large data/PDFs are not in Git.

Formal Development/Validation/Official OOS NOT_RUN; no tuning, full freeze,
PR12 merge, release, public visibility, live trading or ML/GPU work.
Verification:439 backend tests,78 frontend tests, Ruff/format/mypy, frontend
lint/type/build pass. All bounded probes completed; no ingestion worker remains.
