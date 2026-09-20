# Current state

## R5 commission-scope route closure / preflight v12 — 2026-09-20

The checksum-bound 2012 Guangdong CSRC notice explicitly distinguishes net
commission from all-in commission and requires treatment according to the
customer agreement or actual account practice. Generic official public rules
therefore cannot select the research account convention. The public-source
transaction-cost residual falls from four groups to three; the executable
model is unchanged and an account contract or explicit human research
convention remains required.

Full-source preflight V12 remains blocked by 239 official raw rows, 2,009 SZSE
suspension boundaries, adjustment economics, three historical transaction-cost
evidence groups and the account-specific commission convention. See
`../research/R5_TRANSACTION_COST_OFFICIAL_SOURCES_V5.md`.

Local offline-safe validation passes: 743 backend tests, Ruff, format, strict
mypy, 78 frontend tests, ESLint, TypeScript and an isolated production build.
The PostgreSQL-backed subset remains unavailable while Docker Engine is
offline.

The smallest new methodology gate is whether the already frozen Pilot cost
model applies unchanged to the 2010-2025 R5 study or is replaced by an
account-specific net-versus-all-in convention. Docker recovery is separately
`DEFERRED_NONBLOCKING`.

## R5 SZSE post-close scope closure / preflight v11 — 2026-09-20

Official SZSE guidance and technical notices explain all 223 separate
2023-04-10 ChiNext scope differences: post-close fixed-price trades execute at
the close and enter the final daily total, while the official spot close file
excludes them. Of 2,761 comparisons, 2,504 match directly, 34 reconcile to
official block trades, 223 have this deterministic signature and zero remain
unexplained.

This closes the transaction-scope diagnostic only. It does not promote the
239 separate 2011-07-25 Tencent/Sina candidate rows to official per-security
OHLCV authority. Full-source preflight V11 remains blocked by those 239 rows,
2,009 SZSE suspension boundaries, adjustment economics and four historical
transaction-cost claim groups. See
`../research/R5_SZSE_POST_CLOSE_SCOPE_V2.md`.

Local offline-safe validation passes: 742 backend tests, Ruff, format, strict
mypy, 78 frontend tests, ESLint, TypeScript and an isolated production build.
The 63 PostgreSQL-backed backend tests could not be validated because the
Docker Engine was offline; no Docker data or generated root-owned build output
was altered.

## R5 ChinaClear transaction-cost closure / preflight v10 — 2026-09-20

Two original ChinaClear operative notices resolve the 2012 SSE transfer-base
contradiction in favor of traded face value: 0.375 per mille from 2012-06-01
and 0.3 per mille from 2012-09-01. The SZSE rate remains 0.0255 per mille of
traded amount. The conflicting CSRC news wording is preserved but does not
override the fee collector's original notice.

Historical transaction-cost gaps fall from five to four. Minimums, full
pre-2015 intervals, broker/customer commission component scope and continuous
non-handling coverage remain incomplete; no executable rule changed. Full-
source preflight V10 remains blocked by suspension, raw authority, adjustment
economics and historical transaction-cost authority. Backend 804/804 and
frontend 78/78 tests, lint, type checks and the frontend production build pass.
See `../research/R5_TRANSACTION_COST_OFFICIAL_SOURCES_V4.md`.

## R5 SZSE official aggregate crosscheck / preflight v9 — 2026-09-20

The fixed 239-row ChiNext residual was replayed from checksum-bound Tencent and
Sina responses. All 239 rows have exact OHLC and volume parity; every amount is
inside the accepted plus-or-minus 100 CNY interval, with a maximum difference
of 52 CNY. All 4,684 contiguous 20-observation windows containing the target
date keep the same liquidity decision; the minimum threshold distance is 365
CNY. Input-order reproducibility passes.

The checksum-bound official SZSE 2011 yearbook reports 432.73 million shares and
9,673.76 million CNY for ChiNext on 2011-07-25. The 239 candidate rows sum to
431.34 million shares and 9,649.92 million CNY. Two official SZSE agreement
block trades for 300020 and 300166 total 1,390,000 shares and 23,837,000 CNY;
adding them closes both providers to the yearbook's published precision.

The report SHA-256 is
`1afdab62bb7b244beef5be97604bf6a47f37ea43bdac7d73b0a101b3e8372919`.
This closes the date's aggregate transaction-scope diagnostic, not per-security
official OHLC authority or the separate 223-symbol after-hours scope. Full-
source preflight V9 therefore stays blocked on suspension, raw authority,
adjustment economics and historical transaction-cost authority. See
`../research/R5_SZSE_20110725_RAW_CANDIDATE_V1.md`. Backend 803/803, Ruff,
format and strict mypy pass.

## R5 public-source closure v68 and preflight v7 — 2026-09-20

Corporate-action P1 facts are closed: **16,318 / 16,320** requirements are
established with **2,034** official substitutions, all **13,590** cash documents
are supported, and the two residual requirements are only
`RAW:FULL_UNIVERSE` and `SUSPENSION:FULL_DAILY`. One newly accepted official
SZSE disclosure moves suspension authority to 8,738 exact resumptions, 58
terminal closures and **2,009** unresolved boundaries, still PARTIAL.

Five newly retained official CSRC/SSE/SZSE fee pages close the exact regulator
boundary but confirm a material 2012 SSE transfer-base contradiction and do not
define the research-account commission scope. Full-source preflight V7 remains
blocked by suspension, raw, adjustment-economics and historical transaction-
cost authority. The Full Dataset is not created, audited or frozen; no study has
run. Backend 802/802, frontend 78/78, Ruff, format, mypy and the frontend
production build pass; PostgreSQL, Redis, backend, frontend and `/api/health`
are healthy. See `../research/R5_PUBLIC_SOURCE_FACT_CLOSURE_V2.md`,
`../research/R5_SZSE_OFFICIAL_SURFACE_RECOVERY_V25.md` and
`../research/R5_TRANSACTION_COST_OFFICIAL_SOURCES_V3.md`.

## R5 public-source fact closure v65 — 2026-09-20

Retained official bytes close two additional merger facts without a commercial
product: `MERGER:000578:000792` and `MERGER_NEW:600253:600056`. Cumulative P1
now establishes **16,313 / 16,320** facts with **2,031** explicit official-source
substitutions. Seven exact facts remain: three cash notices, two cross-market
successor-account mappings, full-universe raw authority and full daily
suspension authority. The cash subset supports **13,587 / 13,590** documents.

The retained-bonus fraction policy is implemented and its methodology gate is
resolved. Full-source preflight V6 nevertheless remains blocked by irreducible
official-source and methodology gaps: 2,010 SZSE suspension boundaries, 239
SZSE source rows, adjustment economics, two cross-market account paths and six
transaction-cost claim groups. Verified safe start is unresolved. Full Dataset
creation/audit/freeze and all studies remain NO/NOT RUN. See
`../research/R5_PUBLIC_SOURCE_FACT_CLOSURE_V1.md`.

Verification: backend 799/799, frontend 78/78, Ruff, format, mypy, ESLint,
TypeScript, production build and all Compose configurations pass. PostgreSQL,
Redis, backend, frontend and `/api/health` are healthy.

## Local Docker runtime recurrence recovered — 2026-09-20

Docker Desktop repeated the stale `sailor-ingest.sock` and secrets-engine socket
failure. After stopping Docker, shutting down WSL and moving only those runtime
folders to timestamped recoverable siblings, Engine 29.7.2 and Ubuntu
integration recovered. PostgreSQL, Redis, backend and frontend are healthy;
Redis returns PONG and both `/api/health` and port 5173 return HTTP 200. Backend
tests pass 790/790; frontend tests pass 78/78 and the production build passes.
No image, volume, database or project data was deleted.

## R5 retained adjustment-date review v4 — 2026-09-20

Checksum-bound visual review closes six ambiguous official notice dates without
supplying economic terms. Five become unique exact candidates, taking totals to
**1,348** unique and **35** no-exact cases. Residuals are now 27 restructuring,
six date mismatch/OCR and two complex-holder cases. All 478 combined gross
cash-plus-bonus checks conflict, so no event or authority is promoted. See
`../research/R5_FULL_ADJUSTMENT_DATE_REVIEW_V4.md`.

## R5 retained adjustment-term recovery v3 — 2026-09-20

Two additional deterministic PDF-text artifacts are removed, taking the total
newly recovered exact-date candidates to 32. Unique terms are now **1,343** and
no-exact-term cases are **40**. The remaining set is explicitly classified as
27 restructuring/directed-capital mechanics, 12 official date-mismatch/OCR
boundaries and one complex-holder distribution. All 477 gross cash-plus-bonus
checks remain conflicts, so no event or authority is promoted. See
`../research/R5_FULL_ADJUSTMENT_TERMS_RECOVERY_V3.md`.

## R5 retained adjustment-term recovery v2 — 2026-09-20

Fail-closed shared parser fixes recover 30 additional exact-date official term
candidates from the existing 1,421 checksum-bound CNINFO documents. Unique
terms rise from 1,311 to **1,341** and no-exact-term cases fall from 72 to
**42**. The recovered shapes total 824 cash-only, 476 cash-plus-bonus and 41
bonus-only; three differentiated cash candidates retain their exact ordinary
public-A holder policy. All 476 gross cash-plus-bonus checks still conflict with
the historical provider factor step, so no event or authority is promoted. See
`../research/R5_FULL_ADJUSTMENT_TERMS_RECOVERY_V2.md`.

## R5 adjustment residual official-source closure — 2026-09-19

All 33 factor changes that lacked a retained implementation candidate now have
checksum-bound official CNINFO coverage. Twenty-five official capital/share
mechanics match the retained factor step; seven exact gross-cash terms were
recovered; source-uncovered residuals are zero. Eight provider conventions
remain unresolved: the seven cash-factor bases and 000156's additional-issue
normalization. This is a source-discovery closure, not adjustment-authority
promotion. Full adjustment authority stays PARTIAL. See
`../research/R5_ADJUSTMENT_RESIDUAL_MECHANICS_V1.md`.

## R5 current full-source preflight v5 — 2026-09-20

The obsolete batch-preflight pointer is replaced by
`.research/reports/r5-full-source-preflight-v5.json`. Security master, both ST
authorities, calendar and CSI300 close series remain accepted. Required Full
Dataset inputs still PARTIAL are suspension (2,010 SZSE boundaries), raw OHLCV
(239 source rows and a separate 223-symbol after-hours scope gap), adjustment
economic alignment (2,328 unmatched change dates plus six supported events
without a curve change), corporate-action completeness/accounting, and full
historical rules/transaction costs. Verified safe start remains unresolved;
Full Dataset creation/audit/freeze and all studies remain NO/NOT RUN.

Deterministic adjustment-gap routing now maps 912 of the 2,328 unmatched
factor dates to exact retained official bonus-source dates. Of 628 SZSE rows
with displayed pre-close/ex-price fields, 621 fit the factor step within the
accepted `0.01` price-tick bounds and seven conflict; 284 SSE rows lack that
displayed-price crosscheck and 1,416 changes have no retained official bonus
date. These remain diagnostics, not accepted events or authority promotion.

The original retained-metadata join gave candidates for **1,383** of the 1,416
dates and left **33** source-uncovered. A targeted bounded official query now
covers all 33: 25 capital/share mechanics match the factor step and seven exact
gross-cash terms are recovered. Eight provider factor conventions remain
unresolved, including those seven cash cases and 000156. The original strict
candidate corpus now has **1,343** unique exact term signatures and **40**
without one. The 477 cases carrying both gross cash and bonus terms all conflict
with the historical provider factor step under the gross-cash formula, so no
tax-net/provider convention is silently substituted into the accepted ledger.

The current v32 suspension ledger was replayed through every retained SZSE
daily workbook and the 27 existing official listing intervals. It moves 377
rows from `UNKNOWN_RESUMPTION_NOT_CLOSED` to `DATED_SOURCE_HALT_INTERVAL`, but
the final residual key set is unchanged: 239 securities, one row each on
2011-07-25. Two rows exchange their reason labels; neither is added or removed.
The checksum-bound replay manifest is
`5ad2a1aac5ad867c724bcf45a48fdac6aec8566ccab20c2d35733c20b95e1cda`.

## R5 retained-scan SZSE recovery v24 — 2026-09-19

Twenty-nine retained low-text official PDFs were processed offline. Original
page review confirms two exact 2011-09-15 resumptions (000545 and 002033); the
other 27 remain unaccepted. Authority now has **8,737** exact resumptions, 58
terminal closures, zero date conflicts and **2,010** unresolved boundaries.
Explicit open/afternoon timing is preserved so a date boundary is not silently
treated as opening eligibility. See
`../research/R5_SZSE_SCAN_RECOVERY_V24.md`.

## R5 adjustment and cost inventories — 2026-09-19

All 5,436 accepted-master intervals have one checksum-consistent retained
factor curve, and all 153 supported rights events align by date, but full
economic alignment is not established. Separately,
retained official fee sources establish dated 2012 and 2015 claims while
sixteen official SZSE yearbooks additionally establish the annual snapshot path
and exact 2023-08-28 handling boundary. Six claim groups remain unresolved,
including the 2012 SSE transfer-base contradiction and whether the approved
research commission is net or all-in. Both authorities remain PARTIAL; no
executable rule was changed.
See `../research/R5_FULL_ADJUSTMENT_INVENTORY_V1.md` and
`../research/R5_FULL_ADJUSTMENT_ROUTING_V3.md` and
`../research/R5_FULL_ADJUSTMENT_SOURCE_RECOVERY_V1.md` and
`../research/R5_FULL_ADJUSTMENT_TERMS_RECOVERY_V2.md` and
`../research/R5_FULL_ADJUSTMENT_TERMS_RECOVERY_V3.md` and
`../research/R5_FULL_TRANSACTION_COST_GAPS_V2.md`.

## R5 SZSE event-outcome recovery v23 — 2026-09-19

Twenty-three bounded official CNINFO PDFs across six high-information outcome
families were acquired with zero failures. Seven exact boundaries were added;
no prior boundary was lost or changed. Authority now has **8,735** exact
resumptions, 58 terminal closures, zero conflicts and **2,012** unresolved SZSE
boundaries. The screened title routes are exhausted and broad generic metadata
retrieval remains unjustified. Suspension authority is still PARTIAL and the
retained-bonus methodology gate is unchanged. See
`../research/R5_SZSE_EVENT_OUTCOME_RECOVERY_V23.md`.

## R5 SZSE generic-clarification recovery v22 — 2026-09-19

Nineteen bounded official CNINFO explanation/self-check PDFs were acquired with
zero failures. Generic explanation notices close 000602 and 002526; transaction
explanations and staged self-check results add no unique date. No prior boundary
was lost or changed. Authority now has **8,728** exact resumptions, 58 terminal
closures, zero conflicts and **2,019** unresolved SZSE boundaries. Suspension
authority remains PARTIAL and the retained-bonus methodology gate is unchanged.
See `../research/R5_SZSE_GENERIC_CLARIFICATION_RECOVERY_V22.md`.

## R5 SZSE media-clarification recovery v21 — 2026-09-19

Three bounded official CNINFO title families contributed 37 attachments with
zero final acquisition failures. Acquisition/asset-transfer completion notices
yielded no boundary; media/rumour/concern clarification notices closed eight
exact boundaries with no prior loss or change. Authority now has **8,726** exact
resumptions, 58 terminal closures, zero conflicts and **2,021** unresolved SZSE
boundaries. Source checksum and reverse-order replay pass. Suspension authority
remains PARTIAL and the retained-bonus methodology gate is unchanged. See
`../research/R5_SZSE_MEDIA_CLARIFICATION_RECOVERY_V21.md`.

## R5 SZSE residual regulatory-review screen v20 — 2026-09-19

A bounded 26-document official CNINFO regulatory-review title screen completed
with zero acquisition failures. Retained-byte replay produced zero new, removed
or changed accepted boundaries, so authority remains at **8,718** exact
resumptions, 58 terminal closures, zero conflicts and **2,029** unresolved SZSE
boundaries. The title family is exhausted; its 72,598 generic remainder is not a
justified blind acquisition queue. Suspension authority remains PARTIAL and the
retained-bonus methodology gate is unchanged. See
`../research/R5_SZSE_RESIDUAL_REVIEW_SCREEN_V20.md`.

## R5 SZSE residual clarification screen v19 — 2026-09-19

The corrected residual was rejoined to all retained official CNINFO metadata.
A bounded four-document clarification screen acquired four official PDFs with
zero failures and closes 000030 and 000541. Authority now has **8,718** exact
resumptions, 58 terminal closures, zero conflicts and **2,029** unresolved SZSE
boundaries. The remaining 72,620 generic document leads are not a justified
blind acquisition queue. Suspension authority remains PARTIAL; the retained-
bonus gate is unchanged. See
`../research/R5_SZSE_RESIDUAL_CLARIFICATION_SCREEN_V19.md`.

## R5 SZSE non-equity evidence screen v18 — 2026-09-19

The shared resumption classifier now rejects bounded bond-only title forms such
as named bond/convertible resumptions when no stock or A-share subject is named.
Sixteen retained document occurrences move to NON_EQUITY. Accepted authority
stays at **8,716** exact resumptions, 58 terminal closures, zero conflicts and
**2,031** unresolved SZSE boundaries; 002477 keeps its date through a separate
official stock-resumption notice instead of the bond notice. Suspension
authority remains PARTIAL; the retained-bonus gate is unchanged. See
`../research/R5_SZSE_NON_EQUITY_EVIDENCE_SCREEN_V18.md`.

## R5 SZSE application-boundary revalidation v17 — 2026-09-19

Strict replay now distinguishes final `经/向交易所申请后自某日复牌` clauses
from plans or applications to resume, and prevents multi-digit days from being
truncated by time grammar. Against v16, 1,397 cached official boundaries are
recovered, 40 false/non-final rows reopen and four dates are corrected.
Authority now has **8,716** exact resumptions, 58 terminal closures, zero
conflicts and **2,031** unresolved SZSE boundaries. No source was downloaded or
symbol-specific rule added. Suspension authority remains PARTIAL; the retained-
bonus gate is unchanged. See
`../research/R5_SZSE_APPLICATION_BOUNDARY_REVALIDATION_V17.md`.

## R5 SZSE broad-subject date precedence v16 — 2026-09-19

The broad subject/date resumption form is now fallback-only when a narrower
effective-date form succeeds. Full retained replay closes 300316 with no loss
or date change among the prior 7,358 boundaries. Authority now has **7,359**
exact resumptions, 58 terminal closures, zero conflicts and **3,388**
unresolved SZSE boundaries. 000422 remains unresolved because one notice
describes two adjacent suspension episodes and the accepted one-date evidence
model cannot cross the intervening halt. Suspension authority remains PARTIAL;
the retained-bonus gate is unchanged. See
`../research/R5_SZSE_BROAD_SUBJECT_PRECEDENCE_V16.md`.

## R5 SZSE resumption-date precedence v15 — 2026-09-19

The broad resumption-date lookahead is now fallback-only when an anchored
effective trading-boundary pattern succeeds. Full retained-source replay closes
10 exact boundaries with no loss or date change among the prior 7,348.
Authority now has **7,358** exact resumptions, 58 terminal closures, zero
conflicts and **3,389** unresolved SZSE boundaries. Input-order replay, source
checksums and focused tests pass. True dual anchored dates remain unresolved.
Suspension authority remains PARTIAL; the retained-bonus gate is unchanged.
See `../research/R5_SZSE_RESUMPTION_DATE_PRECEDENCE_V15.md`.

## R5 all-retained SZSE delisting-boundary replay v14 — 2026-09-19

The v13 shared parser rule was replayed over every retained official source,
not only the 31 newly acquired notices. Fourteen additional cached official
documents close exact suspension boundaries without new downloads or
symbol-specific logic. Current authority has **7,348** exact resumptions, 58
terminal closures, zero conflicts and **3,399** unresolved SZSE boundaries.
Input-order replay and source checksums pass. Suspension authority remains
PARTIAL; the retained-bonus fractional methodology gate is unchanged. See
`../research/R5_SZSE_ALL_RETAINED_DELISTING_REPLAY_V14.md`.

## R5 SZSE delisting-consolidation recovery v13 — 2026-09-19

A bounded exact-title screen acquired 31 official CNINFO notices containing
`进入退市整理期`, with zero failures. Their shared final wording names a unique
effective trading start. A one-pattern shared-parser fix closes all 31 bound
halts, taking exact SZSE resumptions from 7,303 to **7,334** and unresolved
boundaries from 3,444 to **3,413**. The 58 terminal closures remain, conflicts
remain zero, and reversed supplement order reproduces byte-identical authority
outputs. Suspension authority stays PARTIAL. See
`../research/R5_SZSE_DELISTING_CONSOLIDATION_RECOVERY_V13.md`.

## R5 bounded SZSE implementation-title screen v12 — 2026-09-19

Two exact-title families supplied 40 official CNINFO PDFs with zero acquisition
failures. One document states an exact date, but 000509's 2014-01-09 resumption
cannot close its 2013-12-19 halt because a distinct official halt starts at
2014-01-09 09:30. The other 39 documents contain no exact bound resumption
date. No new boundary is accepted: authority remains 7,303 exact resumptions,
58 terminal closures, zero conflicts and 3,444 unresolved SZSE boundaries.
The implementation/listing-title route is exhausted; do not widen it into a
blind low-precision bulk retrieval. See
`../research/R5_SZSE_IMPLEMENTATION_TITLE_SCREEN_V12.md`.

## R5 targeted SZSE resumption recovery v11 — 2026-09-19

Reused 2,292 retained official documents and acquired 380 bounded official
CNINFO documents with zero failures. Strict content replay closes ten true
boundaries relative to v10. A cross-document precedence defect was also fixed:
000520's restoration-of-listing date is not a trading resumption because a
later official notice says it remained suspended that day. Current authority
has **7,303** exact resumptions, 58 terminal closures, zero conflicts and
**3,444** unresolved SZSE boundaries. Forward/reverse replay is byte-identical.
High-yield title families are exhausted; the current low-precision residual is
74,569 unprocessed leads across 1,923 facts, while 1,521 facts have no remaining
candidate in retained metadata. Authority stays PARTIAL. See
`../research/R5_SZSE_TARGETED_RESUMPTION_RECOVERY_V11.md`.

## R5 strict SZSE resumption revalidation v10 — 2026-09-19

All retained official resumption evidence was replayed under a fail-closed
parser after deadline/application language was found in historical accepted
supplements. The corrected authority has **7,293** exact resumptions, 58
terminal closures, zero conflicts and **3,454** unresolved SZSE boundaries.
Of 8,913 prior accepted rows, 7,276 retain the same date, 10 receive a corrected
date and 1,627 are reopened; seven additional exact final notices close. Reverse
supplement order produces byte-identical outputs. Earlier v1-v9 acceptance
counts are historical only. See
`../research/R5_SZSE_RESUMPTION_STRICT_REVALIDATION_V10.md`.

## R5 intraday and named resumptions v9 — 2026-09-19

Four retained official notices close under three narrow forms: an explicitly
named resumption date, same-date afternoon trading after a morning halt, and
same-date trading after a stated one-hour halt. No disclosure-dependent,
conditional, deadline-only or one-day inference is admitted. Full replay has
**8,913** true resumptions, 58 terminal closures, zero conflicts and **1,834**
unresolved SZSE boundaries. Authority remains PARTIAL. Manifest
`0c2678ac55fd0384e82d7c28601cf2f1e3e621c1d5d28e1067d92f606090fe42`.
See `../research/R5_SZSE_INTRADAY_AND_NAMED_RESUMPTION_V9.md`.

## R5 exact normal-trading boundaries v8 — 2026-09-19

Strict parsing now recognizes official `恢复正常交易` and prevents an earlier
disclosure/meeting date in the same sentence from masquerading as the trading
boundary. Conditional and application-only phrases remain rejected. Four
retained official notices close 000100, 300043, 000625 and 000423. Full replay
has **8,909** true resumptions, 58 terminal closures, zero conflicts and
**1,838** unresolved SZSE boundaries. Authority stays PARTIAL. Manifest
`aade1e18a17347dae231a6fbd3d834ea3cabf9c481a2a1322fe2e7649dffb6fb`.
See `../research/R5_SZSE_NORMAL_TRADING_BOUNDARY_V8.md`.

## R5 targeted resumption recovery v6 — 2026-09-19

A 13,515-page retained CNINFO metadata join was reduced from 75,579 interval
leads to a bounded 150-document official batch. All PDFs were acquired; exact
text accepted 13 delisting-consolidation resumptions and five separate
no-consolidation terminal closures. A second 126-document restoration screen
exposed the distinct `恢复上市` form; strict parser v5 rejects applications and
progress language and accepted eight effective trading restorations from
already retained official documents. Full replay now has **8,905** true
resumptions, **58** terminal closures, zero conflicts and **1,842** unresolved
SZSE boundaries. SSE remains 16,393/0. Authority stays PARTIAL. Full authority
manifest `9d1a6e9101d5ebdf95ac0511b8745d0dc2802aaa22f92f53e6fc96a4a218dcbe`.
See `../research/R5_SZSE_RESUMPTION_RECOVERY_V6.md`.

## R5 all-retained bound terminal scan v3 — 2026-09-19

The exact-event terminal rule has now run across every retained SZSE resumption
manifest carrying `affected_suspensions` bindings: 9,626 unique official
documents. SHA-identical repeat acquisitions merge bindings deterministically
while conflicting source metadata fail closed. Five merger suspensions
(000024, 000522, 000527, 000562, 300186) close through official
suspended-until-termination notices and master lifecycle ends. Full replay now
has 8,884 true resumptions, 53 terminal closures, zero conflicts and **1,868**
unresolved SZSE boundaries. Authority remains PARTIAL. V3 manifest
`f3ccdfcb9b53e83b1e688a7d8174c3874a5b68c6551a8e238b449b76151e9d72`;
full authority manifest
`0583bb29a1e7963f6f2fc247e096ba6486778d8a5338f8f1f4fad9ca5a0aecf7`.
See `../research/R5_SZSE_TERMINAL_SUSPENSION_CLOSURE_V3.md`.

## R5 bound terminal-suspension closure v2 — 2026-09-19

The terminal pass now uses each retained official document's immutable
`affected_suspensions` binding instead of choosing a nearby halt. Explicit
no-delisting-period or suspended-through-termination language plus the
official master lifecycle closes six additional events: 000418, 000671,
000748, 000780, 000916 and 002013. No resumption is invented. Full replay has
8,884 true resumptions, 48 terminal closures, zero conflicts and **1,873**
unresolved SZSE boundaries across 22,077 events; SSE remains 16,393/0.
Authority remains PARTIAL. V2 manifest
`0c4a55c663cac28b9457c5aec0a403d840f222baf8628b6c812b84399da8e573`;
full authority manifest
`8bc8cdd204f3a3be96eee8c92ebf8d4dc2e37e0368ed11d5bfdd848ac78e7cb9`.
See `../research/R5_SZSE_TERMINAL_SUSPENSION_CLOSURE_V2.md`. Full Dataset,
freeze and studies remain locked.

## R5 official terminal-suspension closure — 2026-09-19

The suspension audit now distinguishes a true official resumption from a
direct-to-delisting terminal boundary. Across 3,391 retained official CNINFO
documents, 42 unresolved SZSE events have an exact official halt date, an
explicit no-delisting-period statement, and one matching official-master
terminal lifecycle date. They are recorded as terminal closures; no synthetic
`resumed_at` is created. Full deterministic replay retains 8,884 official
resumption supplements, adds 42 terminal closures, has zero conflicts, and
reduces SZSE unresolved exact boundaries from 1,921 to **1,879**. SSE remains
16,393/0 unresolved. Authority is still PARTIAL. Report manifest
`70ef1ae3b94e908dcf84db8592606e7cd4051793b38f9b2620651b00930f0522`;
full authority manifest
`5cc9d7a86dd57342d2f8d0da8addb4ad5ab5b70ee1db949518891295701a21a0`.
See `../research/R5_SZSE_TERMINAL_SUSPENSION_CLOSURE_V1.md`. Full Dataset,
freeze and studies remain locked.

## R5 differentiated transfer zero-cash source closure — 2026-09-19

The 22 differentiated stock-transfer candidates now have official zero-cash
source terms: 20 explicit in the final implementation notices and two
corroborated by contemporary issuer plans plus the final notices. For 688368,
the 2024-05-08 issuer shareholder material explicitly says no cash and 0.4
transfer per share; the final 2024-06-06 notice records shareholder approval,
the same ratio and the adjusted repurchase exclusion. For 603703, the
original 2023-04-21 issuer-signed `中国证券报` disclosure explicitly says no
cash and 0.4 transfer per share; the official SSE announcement index uniquely
identifies its plan notice, and the final 2023-06-13 CNINFO notice records
shareholder approval, the same ratio/base and zero cash in the reference-price
formula. The SSE plan PDF URLs are preserved but their bytes were inaccessible;
the contemporaneous alternative official issuer disclosures are archived.
Neither proposed plan was used as a final event by itself.

Immutable report:
`/home/yuchen/data/research/staging/p1-differentiated-bonus-zero-cash-v1/official-zero-cash-corroboration-v2.json`,
file SHA-256 `1a681467fae8df49c1f774f374d1204f7d2e35508048db713b41a0afce2697d4`,
manifest `fb496eb138be22caad38c96c7959962c320b9c27382d61789f522e92eca1eab1`.
Reverse-order replay passes. Source-term cash uncertainty is zero for this
22-document subset, but **zero P1 requirements and zero economic events** were
closed here: all have fractional per-share entitlements and account-level
rounding/settlement remains a material human methodology gate. Cumulative P1
v58 stays 16,073/16,320 with 247 facts open. Full Dataset, freeze and studies
remain locked. The v4 baseline's two cash-source-unresolved labels are
superseded for source-term evidence only, not for accounting acceptance.

## R5 original SZSE exchange notices close 002075 — 2026-09-19

**Current corrected SZSE source-presence report is v5; v4 below is historical.**
The original 2010-04-30 `证券时报` page carries a SZSE-signed notice
setting 002075's listing suspension to 2010-05-07. The original
2011-03-30 page carries a SZSE-signed notice restoring the same issuer
(renamed 江苏沙钢股份有限公司) from 2011-04-08. Both exchange notices were
visually checked, and their original page PDFs have archived bytes, UTC
receipts and SHA-256. The official SZSE-hosted 2011 issuer report had
already independently corroborated the restoration date. The overlay
reclassifies only **216** 002075 dates strictly inside the suspension
interval. **239** dates across **239** ChiNext securities remain, all on
2011-07-25; 201 lack a matching halt source and 38 have unknown resumption.
All 15,655 absent active-master rows are conserved. The remaining one-day
block is not evidence of mass suspension or tradable bars. A separately
archived official SZSE 2011 statistical yearbook (PDF page 165, printed
page 149) reports **48.48 ten-thousand ChiNext deals** on 2011-07-25,
visually checked: the board traded that day, so the daily export's zero
300-series rows are an omission, not a board-wide trading halt. Yearbook
PDF SHA-256 `38289a861878de122015747d09ca3dc1f7e05de127c572ae2ac4792206460bd4`,
retrieved 2026-09-18T20:04:12.261327+00:00. The aggregate cannot
identify which individual securities traded or supply their OHLCV.

Current report:
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-corrected-v5.json`;
file SHA-256 `e34597c37fcfea2bfc193d165a40a8f56537b9bf247f809f8317ddbe6f3ac09d`,
manifest `36120ebb15c625e936bd77b8584230f7dc9c5d885af3a848ead5281c7e6f3127`.
Original notice PDF SHA-256 values are
`1f248ba308629a85ac6436bf0c83a1adfcfd81d7a2045d0bd6460e92ad083b02`
and `da36a8ecbd4a3e91ec2f46dc79a30600dc9176ef1d8c6abdb1fe43e7309bd8c2`.
Byte-identical replay, focused test and lint pass. This source-presence
classification does not promote full raw or execution authority. Full
Dataset, freeze and studies stay locked. A targeted `1815_stock_snapshot`
2011-07-25 alternate query returned "没有找到符合条件的数据！"; the current
per-symbol SZSE chart API returned only its recent 201 sessions even
with a 2011 date range, so neither is a replacement source.

## R5 official 000732 issuer-notice source closure — 2026-09-19

**Historical corrected SZSE source-presence report v4; v3 below is older.**
The original issuer-signed 2010-09-21 `证券时报` disclosure states that
000732 was suspended from listing on 2007-05-11 and trading would resume
2010-09-30 under SZSE decision `深证上[2010]310号`. The official CNINFO index
uniquely identifies that issuer notice; a SZSE-hosted issuer PDF names
`证券时报` as a designated disclosure paper. All three source surfaces have
archived bytes or index response, UTC receipt and SHA-256. The original
CNINFO PDF bytes remain unverified; no third-party mirror is substituted.
The checksum-bound overlay reclassifies only **177** 000732 absent rows
strictly within the interval. **455** dates across **240** securities remain:
002075 (216), and 239 ChiNext securities on 2011-07-25. Of those, 201 have
no matching halt source and 254 have unknown resumption. All 15,655 absent
rows are conserved. This is retrospective source-presence evidence, not
a 2007 signal or raw/execution authority.

Historical v4 report:
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-corrected-v4.json`;
file SHA-256 `85d19024f2781cdaa50a766ebbe1e6302938830005ec088a9b798dd22dc07a44`,
manifest `4b0b729fba816ece90a3a8c8f2c0fbc3e836530435fb936c1533773963b56826`.
The designated-paper PDF SHA-256 is
`50d68eb468aeb32a226d53ecc2057c510c945d4a35bb2d44a61601105b9eb23d`;
the SZSE issuer-designation PDF SHA-256 is
`351795ac6f8626a1891c6f099a2b22b33d7b809be356f22cd2208380ca8d1b33`.
Byte-identical replay, focused test and lint pass. Full Dataset, freeze and
studies remain locked.

## R5 official 000156 listing-suspension source closure — 2026-09-19

**Historical corrected SZSE source-presence report v3; v2 below is older.**
An archived SZSE-hosted issuer report (2020-11-04, PDF pages 93–94) quotes
the 2006-04-13 listing suspension and SZSE restoration decision
`深证上[2012]343`, with trading restored 2012-10-19 under unchanged code
000156. The report is retrospective historical evidence, never a 2010
signal input. All 665 unexplained 000156 dates (2010-01-04 through
2012-10-18) are strictly inside that interval. A checksum-bound overlay
reclassifies only those dates; it does not create bars or promote raw or
execution authority. **632** dates across **241** securities remain
unresolved: 002075 (216), 000732 (177), and 239 ChiNext securities on
2011-07-25. Of those, 378 have no matching halt source and 254 have
unknown resumption. The 15,655-row total is conserved.

Historical v3 report:
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-corrected-v3.json`;
file SHA-256 `c0612a6f95e0726c16caa42217a7e563eda876fd273f40c1b3f8de7f8d53fc8a`,
manifest `9fe0011dc16b7ac285eae3e6bc70c315bc6b079bedfa5987059d277ff65cfbca`.
Official PDF SHA-256
`807f2d79b15e88af65ea5ed0e0083704305795ea05f9b07a9606b4e8d6026110`,
retrieved 2026-09-18T19:30:29.477959+00:00. Byte-identical replay,
focused lint and all **763 backend tests** pass. The official SZSE-hosted
002075 half-year report confirms 2011-04-08 restoration but not the
2010 suspension start; 000732 remains without a complete source-bound
interval. Full Dataset, freeze and studies stay locked.

## Docker runtime recovered without data deletion — 2026-09-19

After Docker Desktop recurred on stale `sailor-ingest.sock` and then
`docker-secrets-engine/engine.sock`, only zero-byte socket runtime folders
were moved to timestamped, recoverable siblings with Docker processes
stopped. No image, volume, database or project file was removed. Ubuntu WSL
integration now exposes Docker 29.7.2 and Compose v5.5.0; the existing
PostgreSQL and Redis containers are healthy, backend is healthy,
`/api/health` and the frontend on port 5173 return HTTP 200. This closes
the current Docker startup issue only; final clean-rebuild and restart
durability checks remain release-gate work.

## R5 corrected SZSE daily source-presence audit — 2026-09-19

**Use this section, not the historical v1–v7 counts below.** The old audit
compared slash-formatted `resumed_at` values (for example
`2011/04/13 09:30`) lexically with `YYYY-MM-DD` session dates, so an
expired halt could be counted as still active. A regression test now
normalizes both endpoints to dates. All **3,886** immutable SZSE official
daily XLSX snapshots were SHA-checked and replayed against the same P0
master, calendar and suspension source. The **15,655** absent active-
master rows are unchanged, but the direct dated-halt category falls from
the invalid **10,606** to **227**. Corrected base file SHA-256
`45bd345c122d9ced5807be65ae427b61b6ef6fe63a6c9f1e7da2719126596aca`,
manifest `57eb21a6955b03d42a9d333d0783ace70683e35ac48c9f14da28f266df791b9b`.

Reapplying only the **24** previously PDF-verified official listing-
suspension/terminal intervals explains 9,628 pre-2010, 2,802 2010-plus
and 1,556 terminal-suspension absent rows. Another 145 are delisting
boundaries and 227 have a correctly bounded dated halt. **1,297** dates
across **242** symbols remain unresolved (1,043 no matching halt source;
254 unknown resumption). The three multi-day histories are 000156 (665),
002075 (216) and 000732 (177). The other **239** securities each lack
the same 2011-07-25 ChiNext row: that official export has **zero** 300-
series rows versus 245 on each adjacent session; only six of its 245
active ChiNext securities have a bounded halt covering the day. No mass
halt or tradable price is inferred. Corrected overlay file SHA-256
`23038aa4068abddaf475ba027c3afa78e0a0bd4e1424337f3ee045eea1f3982b`,
manifest `78634cdb2e076e0938f60ea130eaf0848fe7c67863c5cb0de3f20b57d64898bf`;
byte-identical overlay replay passes. Replay scripts:
`backend/scripts/audit_szse_official_row_gaps.py` and
`backend/scripts/reconcile_szse_corrected_row_gaps.py`.
An alternate official `tab1` export with an explicit end date yields
identical rows and still no 300-series code; official `tab2` is an empty
fund table, not a replacement stock source.

Official issuer leads for the three multi-day histories have been
identified, but their PDFs were **not** admitted without archived bytes:
the first targeted CNINFO fetch exhausted bounded transient-DNS retries,
and a direct-address check returned HTTP 403 bot denial. Do not bypass
the denial or promote raw/execution authority. The v1–v7 reports remain
immutable error-history artifacts only. Full Dataset, freeze and studies
remain locked; P0 and accepted official event facts are unchanged.

## R5 three terminal SZSE listing-suspension histories — 2026-09-19

Original CNINFO issuer PDFs for **000805** establish the 2006-05-15
suspended-listing start, the rejected proposal to enter delisting trading,
and 2013-03-27 delisting. Issuer PDFs for **000787** establish its
2007-05-24 suspension and 2013-02-08 delisting. For **000594**, issuer
PDFs establish 2014-07-17 suspension and a 2015-05-21 termination
decision; only 2014 missing rows are reclassified. Pages were visually
checked. The v7 report binds URL, UTC receipt and SHA-256 for each PDF,
explaining exactly **363** more absent official daily rows (212, 114, 37).

Historical superseded v7 report:
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-v7.json`;
file SHA-256 `b44fe8de96244136055a090c03f71644aed226b0c23f99643af1873b05d7ec89`,
manifest `e4da16bfa9d8ac2be3264bcfc6c9588be46c073662b441c37fa4c7cac62f11af`.
Repeat replay is byte-identical; focused test and lint pass. Of the fixed
**15,655** no-row sessions, **153** across **34** symbols remain unresolved
(48 unknown resumption, 105 no matching halt source). **000156** (53),
**002075** (47) and **000732** (22) have targeted official disclosure
leads. The first 000156 PDF hit its bounded transient-DNS retry limit;
the other PDFs were not fetched. A Windows-side targeted retry also failed
DNS resolution. None is accepted into the v7 ledger.
The remaining 31 symbols have one-day
gaps. No absent row becomes a tradable bar or exact execution authority.
Replay: `backend/scripts/close_szse_terminal_listing_row_gaps.py`.
Full Dataset, freeze and studies remain locked.

## R5 five 2010-plus official listing-suspension histories — 2026-09-19

Targeted CNINFO issuer/sponsor PDFs for **000545, 000722, 000751, 000831
and 002506** establish each suspension start and first trading day; their
checked pages, URLs, UTC receipts and SHA-256 hashes are bound in the v6
report. A deterministic checksum-bound overlay on immutable v5 explains
exactly **505** more absent SZSE official daily rows, only inside the
respective bounded intervals. The current report is
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-v6.json`;
file SHA-256 `e450c15f1ff3f3ddbc193106450f51b32bacb3975c0237633dc35b0984ef1b81`,
manifest `0ea44f9ed6fbe484cce9327f41470ddc551a24cd636baa04c0bc5fa0ccc2ce68`.
Byte-identical replay, focused test and lint pass. The fixed **15,655**
no-row total now includes 828 bounded 2010-plus suspended-listing dates;
**516** dates across **37** symbols remain unresolved (85 unknown
resumption, 431 no matching halt source). Replay:
`backend/scripts/close_szse_five_later_listing_row_gaps.py`. This is
source-presence classification only, not raw-bar or exact execution
authority. Full Dataset, freeze and studies remain locked.

## R5 six further official listing-suspension histories — 2026-09-19

Targeted CNINFO issuer/sponsor documents now bound **000620, 000657, 000681,
000820, 000863 and 000981**. PDF pages were visually checked at the
pause/restoration passages; URL, UTC receipt and SHA-256 evidence are in
the external v5 report. The checksum-bound overlay on immutable v4
explains exactly **1,012** more absent official SZSE daily rows. It keeps
the two post-2009 suspension starts (000657, 000820) in a distinct
`OFFICIAL_2010PLUS_LISTING_SUSPENSION` category, rather than misclassifying
them as pre-2010 histories. The current report is
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-v5.json`;
file SHA-256 `8b286641b05ab550b1e25b154b2f179d181c10c2718532435addee588dcbaea2`,
manifest `e9b6c6b0eee99535d6c012f07cbd12ddf155b2876c1f3a16f734706a4c6ee07f`.
Repeat replay is byte-identical. Among the fixed **15,655** no-row
sessions, 3,560 are now bounded official pre-2010 listing suspensions and
323 are bounded 2010-plus listing suspensions; **1,021** dates across
**42** symbols remain unresolved (590 unknown resumption, 431 no matching
halt source). Replay: `backend/scripts/close_szse_six_listing_row_gaps.py`.
This remains a source-presence report, **not** full raw or exact execution
authority. Dataset/freeze/study locks remain unchanged.

## R5 three more official suspended-listing histories — 2026-09-19

Archived CNINFO disclosures for **000038, 000670 and 000719** establish
pre-2010 suspension starts and actual first trading dates. The receipts,
PDF hashes, UTC retrieval times and checked page numbers are preserved in
the external v4 report. A checksum-bound overlay on immutable v3 explains
**683** more absent official SZSE daily rows (241, 217, 225), only inside
their individual suspended-listing intervals. Replay yields identical bytes.
The current report is
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-v4.json`;
file SHA-256 `86905153277c0ca28ef26347fd86ca702a814e1d9664317d1357fe236cb5b847`,
manifest `d60480a6ac37bdeda7e1630eb16f15ddb2e5a43b3b9ec24b0c834827bc07cb0b`.
Of the fixed **15,655** no-row sessions, **2,871** now have official
pre-2010 suspended-listing bounds; **2,033** dates across **48** symbols
remain unresolved (913 unknown resumption, 1,120 no matching halt source).
Replay: `backend/scripts/close_szse_three_listing_row_gaps.py`.

This is **source-absence classification, not an execution-status census**.
The monthly short-halt feed contains entries for some of these long-suspended
securities, including 000719; its short-term `resumed_at` cannot override
the issuer's actual restoration-of-listing date. Existing bounded-source
counts are untouched, and no absent row is inferred tradable or treated as
an OHLCV bar. `RAW:FULL_UNIVERSE`, exact trading-suspension authority,
Full Dataset, freeze and studies remain locked.

## R5 six-security official suspended-listing batch — 2026-09-19

Archived CNINFO issuer restoration announcements now bound the historical
suspended-listing intervals for **000403, 000498, 000622, 000672, 000688 and
000757**. Each announcement states its actual first trading day and its
original pause date; receipt URL, retrieval UTC and PDF SHA-256 are preserved
in the external report. A checksum-verified overlay on the immutable v2
report explains exactly **1,727** more absent official daily rows, including
273 previously marked unknown-resumption dates for 000688. No other security
or date is relabeled.

The current report is
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-v3.json`;
file SHA-256 `9f42a73d16e70d9665fd9966718c93a131aa0789cc81a7ad4d259a478232c1b1`,
manifest `0c456a64a54131b49b7a2d38c132b3d75a08832a9364d3793e4ccc5eac2bab78`.
The total official source-absence set remains **15,655** rows: 10,606
bounded dated halt-source intervals, 2,188 official pre-2010 suspended-
listing dates (including 000693), 145 delisting boundaries and **2,716**
unresolved dates across **51** symbols. Of those unresolved dates, 913 lack
accepted resumption and 1,803 have no matching halt source. No raw-price,
volume, auction-only transaction or exact execution authority is promoted;
Full Dataset, freeze and studies remain locked. Replay:
`backend/scripts/close_szse_pre2010_row_gaps.py`.

## R5 targeted 000693 official suspended-listing closure — 2026-09-19

The archived [2013-08-05 CNINFO issuer notice](https://static.cninfo.com.cn/finalpage/2013-08-05/62900545.PDF)
states that 000693 had been suspended since **2007-05-23**. Its
[2014-01-10 restoration notice](https://static.cninfo.com.cn/finalpage/2014-01-10/63471125.PDF)
sets the **first actual trading day to 2014-01-10**; the 2012-12-31
approval was not a trading resumption. Both PDFs are archived with original
URLs, UTC receipts and SHA-256 checks. A deterministic overlay on the
unchanged v1 row-gap report closes only its **461** 000693 no-row dates,
all within `[2007-05-23, 2014-01-10)`. It does not label unrelated dates
or infer a raw price/volume observation.

The v2 SZSE source-presence checkpoint was
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-v2.json`;
file SHA-256 `b9d8250bce1fa18362f7c81f78b302a14a5123907ee40499ccca973ef0940719`,
canonical manifest `1cef5be1bdc702dc9a21ed1e32ca46dc772a8162231dd446cc3c349ad2cf26b9`.
Of 15,655 absent rows, 10,606 have bounded source halt intervals, 461 have
this official pre-2010 suspended-listing chain, and 145 are delisting
boundaries. **4,443** dates across **57** other symbols remain unresolved:
1,186 unknown-resumption and 3,257 no-matching-halt-source dates. Raw and
exact daily execution authority remain partial; Full Dataset, freeze and
studies remain locked. Replay: `backend/scripts/close_szse_000693_row_gaps.py`.

## R5 SZSE official daily row-absence diagnostic — 2026-09-19

A receipt-verified replay of all 3,886 cached official SZSE daily files
reconciles the previously reported **15,655** absent active-master rows.
**10,606** fall in bounded, dated official halt-source intervals; **145**
are on accepted master delisting-effective dates. The remaining **4,904**
security-dates across **58** symbols are **not closed**: 1,186 have an
official halt source but no accepted resumption date, and 3,718 have no
matching halt source. All unresolved dates lie in 2010–2014 (1,141, 1,541,
1,070, 892 and 260 by year). The largest symbol, 000693, has 461; an
issuer official notice identifies a pre-2012 suspended listing, but the
effective-dated start/restoration chain has not yet been accepted.

The external per-date report is
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-row-gaps-v1.json`;
file SHA-256 `5c54e94fc10e35d16c37257aab22afdb47046f6a416418134eab42d17e9ae713`,
canonical manifest `7442324d22eb169599d8d04ab68b9a39205d812410487fdc8033153278b847b2`.
Replay script `backend/scripts/audit_szse_official_row_gaps.py`; focused
test and lint pass. This is source-presence triage only: unknown resumption
is never treated as a continuing accepted halt, and no absent row is
optimistically called tradable or suspended. SZSE raw transaction-method
scope and exact suspension authority remain partial; no Full Dataset or
strategy gate changes.

## R5 SSE official daily bar-presence closure — 2026-09-19

The checksum-bound 2,405-record SSE snapshot was replayed against the
accepted P0 master, 3,886-session calendar and normalized exchange halt
observations. Of **5,684,496** active master/security sessions, **5,550,031**
have an in-interval official bar. All **134,465** no-bar sessions are now
accounted for as: 133,771 inside SSE open-blocked source intervals; 646 for
600705's pre-2010 suspended listing through its official 2012-08-30
restoration; 19 in four issuer-dated halt windows (600053: 15, 600240: 1,
601360: 3); and 29 exactly on accepted delisting-effective dates. The 29
terminal dates retain their master identities but have no inferred trade or
suspension. **Unclassified source-presence gaps: 0.**

The 600705 bounds are visible in the archived [2009 SSE factbook](https://www.sse.com.cn/aboutus/publication/factbook/documents/c/10170573/files/073e042b8b87407b919e3d8e75ee91a5.pdf)
(PDF p. 86) and [2013 SSE factbook](https://www.sse.com.cn/aboutus/publication/factbook/documents/c/10170569/files/cdccf6c0b46a4c0cadc0a531ecc3aad7.pdf)
(PDF p. 130). Additional exact-dated CNINFO issuer PDFs and their original
URLs, UTC receipts and SHA-256s are listed in external report
`/home/yuchen/data/research/staging/full-raw-coverage-v1/sse-official-bar-gaps-v1.json`.
Report file SHA-256 `7ba780bf09e8e1f684247cf698d348c6ea2fb25ec24356aba792bbcd8ca14668`,
canonical manifest `f7e28d9e67c2a889e72c370e8919586cafef4c29b52b6cb0f4924b089f7f4d65`;
cached repeat yields identical bytes. Replay script:
`backend/scripts/audit_sse_official_bar_gaps.py`.

This closes **SSE bar-presence accounting only**. It does not establish exact
daily suspension/resumption for both exchanges, SZSE auction-only raw
volume/amount, corporate-action completeness, or `RAW:FULL_UNIVERSE`; no
Full Dataset or study is promoted. The focused tests and lint pass. A full
backend run reached 689 passed, 62 database-setup errors and one database-
dependent failure because PostgreSQL at `127.0.0.1:5432` refused connection;
Docker is not currently integrated into this WSL distro.

## R5 complete official daily source-scope checkpoint — 2026-09-19

Resumed the existing checksum caches; no official P0/ST/adjustment/benchmark
authority was rebuilt. Bounded same-request retries recovered six SSE and one
SZSE transient transport failures. The final collection reports cover all
**2,405/2,405** SSE master-symbol records and **3,886/3,886** SZSE sessions,
with zero transport failures. Their file SHA-256s are respectively
`d56d8abef4ff8a3f347d3f247feaf5ed8eb15367430eb3db91e36715048a5940`
and `3edca545dd7b4173c7c95381bb68dd2bb5fd20769faf0930e17da7640edf84ea`.
The separately accepted 600003 pre-2010 halt/exit has no target-period bar;
this is explicit, not silently classified as a failed source.

Independent full-range SSE source audit accepts **5,550,031** bars within
point-in-time symbol intervals and quarantines **2,306** old/new-code alias
labels (600849: 915; 601360: 1,368; 601607: 23). File SHA-256
`b3d8119f6c4b165fbcfc0303ca343a350e02d86b4c9edab85400a949d75d88db`,
canonical manifest `eb0517052f20e26603059a86da3a0fdaeb38d1fcea21bc7b3776ce42aefd391a`.
The frozen Pilot-v2 overlap covers all **2,289** SSE partitions and **852,354**
bars, with zero OHLC differences, zero volume/amount gaps beyond 100 shares /
CNY 100, no source symbol missing and no missing day in either direction;
file SHA-256 `7ce2ea461b21726897659f111e3efc0a88e546c36ddade577cd6940232fcf8d8`.

Independent full-range SZSE source audit covers **3,886** sessions and
**7,861,158** point-in-time ordinary-A rows: **7,589,490** traded and
**271,668** zero-turnover, with zero unmatched A-prefix candidates. The
**15,655** active-master/session pairs without a stock row are *not* inferred
as suspensions. File SHA-256
`71fec3fa0018162041b462a1e85f602a0b87147b733bac6de681a2a2b3a169de`,
canonical manifest `adbb7faa6ded6de13c1b795fdc4e408cb2592cd9e1eb1bcd0adfb95cb1aa567b`.
These are complete **source-snapshot scope** audits, not acceptance of
auction-only SZSE volume/amount, exact daily suspension, corporate-action
completeness, or `RAW:FULL_UNIVERSE`. No Full Dataset, freeze or study follows.
The older partial checkpoints below remain historical.

## R5 official-public raw collection checkpoint — 2026-09-19

The SSE and SZSE collectors were paused at the unresolved retained-bonus
fractional-share human methodology gate, preserving their existing
checksum-resumable source roots. Cached replay verifies **1,525/2,405** SSE
master-symbol records and **3,275/3,886** SZSE calendar sessions with zero
transport failures in the bounded checkpoints. SSE 600003 has no target-period
trade bar, consistent with its separately accepted halt/termination history;
it is not silently counted as a missing identity. Collection report SHA-256s
are SSE `be40f03027b4fe4440fb6fdace9b05c92960d08d1ebcea0ed1a8058da3dd0ba9`
and SZSE `bed2dae2ea08bb80677dba0a600d05fa8f31f99d261a7f5d636079addf799108`.

The source-bound SSE audit finds **4,438,675** in-interval target bars and
quarantines **2,306** cross-symbol-interval labels: 915 post-boundary 600849,
23 pre-boundary 601607, and 1,368 pre-boundary 601360. Every quarantined
set exactly duplicates its accepted counterpart code's same-date source bars
(601607, 600849, and 601313 respectively). File SHA-256
`5f777d573a4c2076d4d32872cf08e43b0ea33c81d7fc4e1f1bbcf5ce53c5ff91`,
manifest `216e0482b47058e41620791c5b9464c71a64afb425d9efdb118a787d21ffc48d`.
The SZSE audit finds **6,121,757** point-in-time ordinary-A stock rows,
including **5,854,424** traded and **267,333** zero-turnover rows, with zero
unmatched A-prefix candidates. The **15,582** active-master/session pairs
without a stock row are not inferred as suspensions. File SHA-256
`20acecc784f541d1bdb3c73f8ef4e1d140b2006fed9a8688e029527a9b5796e4`,
manifest `64fa65af9ef6c921eb9837418c7bb7bdd6e86812c869d37fcc53cf92d288448c`.
The older smaller checkpoints below are historical. Neither partial audit
proves full-range raw coverage, auction-only transaction scope, or exact
suspension/resumption. No raw authority or Full Dataset is promoted.

## R5 restructuring non-entitlement diagnostic — 2026-09-18

Forty-eight already cached CNINFO issuer PDFs explicitly state that the
restructuring capital-transfer shares are **not distributed to original
shareholders** and that these notices have **no cash dividend**. Source
PDF/text hashes, issuer, title, date, parser output and reverse input order
were checked. This is narrow negative-entitlement evidence only: some same
notices also determine issuer-specific opening reference prices and
resumption boundaries. The current P1 ledger cannot split one document's
candidate into those separate facts, so **zero P1 documents or facts were
closed**. Cumulative v58 remains authoritative at **16,073/16,320** facts,
with **247 facts / 242 documents** open. Diagnostic v2 file SHA-256
`60a787eecb596768abf1233ce34fb1d4d0e80f5601c0fccbb4eea9b92a6cb91a`,
manifest `429101ff2485174b834ecbebd97b2d80d2101e8c4cfaeb4350446a8df6584626`.
Draft v59 and queue v12/triage v21 generated during this audit are
**superseded and not accepted**; current queue v11/triage v20 remain in use.
No economic event, bonus policy or research gate changed.

## R5 SSE official day-bar temporal-scope control — 2026-09-18

A read-only replay of a 875/2,405-symbol acquisition checkpoint checks
original SSE JSON bytes and UTC/SHA-256 receipts against the accepted P0
symbol intervals and 3,886-session calendar. It found 3,067,830
in-interval 2010–2025 bars and quarantined **915** out-of-interval bars
under old code 600849. The accepted code transition makes 600849 end on
2010-03-04 and successor 601607 begin 2010-03-05; all 915 old-code
post-boundary bars exactly duplicate successor-code bars already available
from the official endpoint. Thus the SSE endpoint code label alone is not
a point-in-time identity and source normalization must filter by accepted
symbol interval. The one no-target-bar 600003 control remains explicit.
Replay script `backend/scripts/audit_sse_official_daily_scope.py`; partial
report SHA-256
`367ec87b51e73f6245657a4a35620bd721a55b4379f8fc992930a0d4adb21c16`,
canonical manifest SHA-256
`7f1af85a8c2fede82867875168e9b3097ef11d4e4e84c9a12a55db12041d3c4e`.
This does not promote full raw-data authority or assert full coverage.

## R5 SZSE daily transaction-scope control — 2026-09-18

The [official SZSE equity block-trade export](https://www.szse.cn/disclosure/deal/block/equity/index.html)
is available as XLSX even though its JSON report currently returns an error.
The 2023-04-10 checksum-archived exports contain 42 securities in the
summary, 57 agreement trades and zero block-trade fixed-price rows. Summary
and trade detail agree within CNY 100 of published rounding. For 000001,
the two official block trades total 1,000,000 shares / CNY 12,030,000,
matching the previously observed official-daily-minus-Pilot gap within
daily-export precision. Across 2,761 matched A-share Pilot bars, 2,504
daily totals already match within precision, 34 additional rows reconcile
after official block subtraction, and 223 ChiNext rows retain a residual
consistent with close-price transactions and 0/100-share display rounding.
This last pattern is **not** an official per-security after-hours transaction
record and therefore is not accepted as exact reconstructed volume/amount.
The [SZSE technical notice](https://www.szse.cn/marketServices/technicalservice/notice/t20200508_576947.html)
distinguishes ChiNext after-hours fixed-price trading from the auction feed;
the [SZSE investor explanation](https://investor.szse.cn/knowledge/stock/deal/t20191225_572858.html)
states that block trades enter daily totals. The replayable scope audit is
`backend/scripts/audit_szse_daily_transaction_scope.py`; source bytes,
UTC receipts and SHA-256s are under
`/home/yuchen/data/research/staging/full-raw-coverage-v1/szse-official-block-20230410-v1/`.
Its report SHA-256 is
`2a6251120f7ac80b371a5889653f61d2b5c44c4c6a41f0c995cbfd06b3aef78a`
and canonical manifest SHA-256 is
`762a0d3c4fd9f6b61586cb9498755bc8b146685b1ec60a12ba54320bbe08c47e`.
This is one-day source-scope evidence, not full-range raw-data authority.

## Current R5 official-public raw daily controls — 2026-09-18

Official exchange pages expose two public raw-data routes, now
partly checkpointed without authority promotion. The
[SSE company chart](https://www.sse.com.cn/assortment/stock/list/info/company/index.shtml?COMPANY_CODE=600000)
calls the SSE-hosted `yunhq.sse.com.cn:32042/v1/sh1/dayk` API; controls
600000, delisted 600553 and STAR 688001 return respectively 3,839, 212 and
1,566 bars within 2010–2025. The 600553 series stops on 2011-02-01; 600000
and 688001 overlap the frozen Pilot on 2023-04-10 with matching OHLC and
amount within feed precision (600000 volume differs by seven shares). The
[SZSE stock history](https://www.szse.cn/market/trend/archive/index.html)
exports complete daily XLSX snapshots: 872, 2,812, 2,913, 2,913 and 2,924
unique codes on 2010-01-04, 2023-04-10, 2025-08-29, 2025-09-01 and
2025-12-31. These are the report's stock-tab rows, not an audited ordinary-A
universe count; the 2010 export also includes `200...` codes. The last two
days use the official post-archive catalog. Its
export declares volume in 10,000 shares and amount in 10,000 yuan; on
2023-04-10, 000001's OHLC matches Pilot, but official all-trading-methods
volume/amount exceed Pilot by 999,900 shares / CNY 12,029,952.38. These
are differing source scopes, not an authorized overwrite. Source responses,
UTC receipts and SHA-256s are under
`/home/yuchen/data/research/staging/full-raw-coverage-v1/{sse,szse}-official-day-controls-v1/`;
report checksums are `f6c5a7f7d8f061d6be2b9244f26f57e3f87cadfbb71fe02a8d894d3bb69bd3f2`
and `f7e1af8b165e332c3648d261be0319c5263570927dce75e6a53cc4922d412de9`.
Neither route has passed full-universe, full-period completeness, source
parity, or transaction-scope acceptance. `RAW:FULL_UNIVERSE` remains open.

A read-only whole-day SZSE/Pilot-v2 overlap audit for 2023-04-10 uses the
accepted P0 point-in-time master, the checksum-verified official XLSX and the
frozen Pilot manifest. It identifies 2,765 official ordinary-A rows: 2,761
have matching Pilot bars and **zero OHLC mismatches**. After allowing 100
shares / CNY 100 for combined display precision, 211 volume and 257 amount
values still differ, always with the official all-methods total higher. The
other four official rows have zero volume/amount and no Pilot raw bar; they
are no-trade observations, not inferred suspension states. Audit SHA-256
`29401b9649ed77f3207871d85404cdc7cce4b88927000f5cf3d52841ec66e84a`.
The [SZSE's official trading FAQ](https://investor.szse.cn/knowledge/stock/deal/t20191225_572858.html)
states that block trades are excluded from the instantaneous quote but added
to the security's daily total after block trading ends. This is consistent
with the positive official-minus-Pilot volume gaps, but the exact gaps have
not been matched to official per-security block-trade records; no auction-only
volume/amount has been reconstructed or accepted.
Acquisition is safely paused at the existing fractional-bonus methodology
gate. The deterministic, checksum-resumable checkpoints contain 575/2,405
SSE master-symbol requests (574 target-bearing; 600003 has no 2010-2025
trade bar, consistent with its accepted pre-2010 halt/termination evidence)
and 825/3,886 SZSE calendar sessions, with no transport failures. Checkpoint
file SHA-256s are respectively
`72039f8fdc9a4755a0e479ef4c279943315be77b49cbb0958421aeb65a413d6c`
and `28dc9c5076be33750b46d7918c902938358ed46edefeba98cd438194f4f08f1c`.
The read-only SSE/Pilot-v2 cross-check covers 201,711 bars from available
partitions: zero OHLC mismatches, zero volume or amount gaps beyond 100
shares / CNY 100, and zero missing days within compared partitions. Its
partial report SHA-256 is
`a1ac7fed4ce5415a36873d49a89a3f0eefe1cafd342b863cd8c8f7314ba23455`;
1,752 Pilot SSE partitions still lack a snapshotted source, so this is not
a full-universe result. No raw source was promoted, no dataset was changed,
and `RAW:FULL_UNIVERSE` stays open.

## Current R5 five derivative notices scoped — 2026-09-18

Five already acquired official issuer PDFs are not independent ordinary-A
distributions: 002521 and 688065 adjust private-placement terms after the
distribution, while 300517, 601860 and 001283 announce temporary convertible
conversion halts before final implementation. Each matches exactly one
previously accepted official issuer implementation by security, distribution
year, chronology and, where present, record/ex-dates. Original PDF and text
hashes, accepted event checksums and reverse-order replay are bound in
derivative-scope report v6 (22 cumulative notices; manifest
`534de27e99a8075012a3242c5650350d71351d8e846e1f135e430b20bc4108f2`).
No new economic event was created. Cumulative P1 v58 establishes
**16,073/16,320** facts and leaves **247 facts / 242 documents** open (231
acquired distribution, 11 other); manifest
`0e5bb98ed6daf54ba29e48bef2b6ad6201ab4b1482dfdf96b277800067641e9c`.
The bounded bonus ledger remains 243/288, with the fractional-share human
methodology gate, full-census and research locks unchanged.

The 11 non-distribution P1 residual requests are exactly four merger/account
chains (000522, 000578, 002013, 600253), five mixed cash-plus-bonus chains
(600106, 600231, 601012, 603019, 603023), `RAW:FULL_UNIVERSE`, and
`SUSPENSION:FULL_DAILY`. This is a fact-request inventory, not a claim that
one purchased export or 11 new files will close them. Existing Tencent annual
window probes are coverage-only; the accepted failover policy is Pilot-only
and does not authorize full-range raw-data promotion.

## Previous R5 two nonfinal bank notices scoped — 2026-09-18

The original official 601009 issuer PDF is a shareholder proposal for a
possible 2024 midterm distribution, still subject to approval and with no
executable amount or entitlement dates. The 600919 issuer's convertible-halt
PDF explicitly promises its final ordinary-A implementation notice on
2023-07-11; exactly one accepted official cash event matches that issuer,
date and final title. Both PDFs mention preferred securities only in the
identification header, not in the entitlement body. Source bytes, extraction,
header/body distinction, final-event checksum and reverse order are audited
in nonfinal-scope report v8 (34 cumulative notices; manifest
`aff961accf0b3743c903f70b28a0c7064fdf48e283813e97be236e4004abc58c`).
Neither creates or changes an economic event. Cumulative P1 v57 establishes
**16,068/16,320** facts and leaves **252 facts / 247 documents** open (236
acquired distribution, 11 other); manifest
`7de0765893210ae796b24c1acd84edb7254051ca6f28f4d0b0a40c5485ba2896`.
The retained-bonus fractional methodology gate, full-census and research
locks are unchanged.

## Previous R5 official cash-correction source closure — 2026-09-18

Three already acquired issuer correction PDFs were independently reconciled
against their original official notices and accepted ordinary-A cash events:
002457 swaps the incorrect payment and liability-clause record dates while
the accepted entitlement record/ex and per-share cash remain unchanged;
603087 corrects only the virtual ex-price formula, not the 0.5 gross cash;
601678 updates repurchased/participating share counts and aggregate payout,
with exact 0.03 cash per participating share on both sides. PDF and text
bytes, original source identity, field-diff, event checksum and reversed input
order are bound in correction report v9 (10 cumulative corrections; manifest
`ba642def749d419361cde7d996e57da68b138b2799e83f126d279f18ba5e4571`).
No new economic event was created. Cumulative P1 v56 establishes
**16,066/16,320** facts, with **1,989** substitutions and **254 facts / 249
documents** open (238 acquired distribution, 11 other); manifest
`a0640f11699434ed644add3426f861b0244c29dd58e765c2a5167f625dbf2545`.
The bounded retained-bonus ledger remains 243/288 accepted; the human
fractional-bonus decision and Full Dataset/research locks remain unchanged.

## Previous R5 retained-bonus component-integrality correction — 2026-09-18

The approved retained-bonus policy has no convention for unobservable
registry-level fractional share allocation. Earlier bounded ledger v28 checked
only that the **sum** of stock-dividend and capital-transfer ratios was an
integer. Original official notices show 39 previously accepted events have
fractional **components** despite integer totals (for example 603023: 0.5 +
1.5). An integer total alone does not establish that both components credit
whole shares to every possible integer-holding account. These 39 events are
conservatively quarantined pending authoritative combined-allocation evidence
or the human fractional-bonus methodology decision; no actual registry award
is inferred. Immutable bounded ledger v30 supports **243/288**, leaves **45**
unresolved and still excludes 7,119 oracle rows from this subset. Manifest
`e5df58295be544873872d40b10dc82a591d921f8dd2108ac4144943afcd0e2e4`.

The dependent dual-source audit v7 now closes **11/16** notices (22 facts) and
leaves five mixed-component notices open, including 603023. Cumulative P1 v54
has **16,063/16,320** facts established, **1,986** official substitutions and
**257 facts / 252 documents** open (241 acquired distribution, 11 other).
Its manifest is `f87e6ac60c05397794891891651f3195cd11d92ed029bf938f825e07a2b63d25`.
The 603023 retrospective listing-date corroboration remains valid as an audit
fact, but no longer closes the two-leg source/accounting requirement. Full
Dataset, freeze and studies remain locked. See
`../research/R5_BONUS_SOURCE_ORACLE_V1.md`.

## Previous R5 603023 official retrospective listing-date corroboration — 2026-09-18

The retained issuer implementation PDF's new-share listing dates conflict:
2016-06-16 on its cover versus impossible 2016-04-16 in its body. The issuer's
official 2016 half-year report (revised, published 2016-09-02) retrospectively
states 2016-06-16 on pages 15, 21 and 61. Source bytes, CNINFO metadata,
retrieval receipt, both contradictory original dates and input order are
audited. This later report is **audit-only**, never a point-in-time signal.
The exact 603023 cash-plus-bonus P1 source request now closes; dual v6 has
16/16 documents and 32 facts, with prior 15 closures preserved. Cumulative
v53 has **16,073/16,320** handled, **1,991** official substitutions and
**247 facts / 247 documents** open (241 acquired distribution, 6 other).
The bounded bonus event still has its integer-holdings/next-session scope;
full census, Full Dataset, freeze and studies remain closed. See
`../research/R5_BONUS_SOURCE_ORACLE_V1.md`.

## Previous R5 603023 bounded bonus parser correction — 2026-09-18

Replaying the already retained official issuer PDF resolves a parser-only
false conflict: its 0.5 share dividend plus 1.5 capital-reserve shares total
2.0; later tax subcomponents 1.3 and 0.2 are not additional entitlements.
The 288-candidate bounded ledger v28 preserves all prior 281 accepted event
checksums and adds only 603023, for **282 supported / 6 unresolved**; 7,119
source-oracle rows remain outside scope. The 603023 dual-leg P1 request remains
open because the same notice gives conflicting new-share listing dates (cover
2016-06-16, body 2016-04-16). A next-session schedule does not certify actual
tradability. No Full Dataset, freeze or strategy run is authorized. See
`../research/R5_BONUS_SOURCE_ORACLE_V1.md`.

## Current R5 false 河北钢铁 parent-identity closure — 2026-09-18

The 000709 issuer implementation report names its acquired parents as 邯郸钢铁
and 承德钒钛. A contemporaneous official SSE notice assigns them codes 600001
and 600357; the audited SZSE master independently identifies 000761 本钢板材
and 000898 鞍钢股份 as separate continuing companies. The two P1 requests
`MERGER_NEW:000761:000709` and `MERGER_NEW:000898:000709` are therefore
source-identity false positives, not missing merger PDFs. Their rejection is
byte/receipt, official-term, master-checksum and input-order audited; no new
event or official substitution is claimed. Cumulative v50 is **16,071/16,320**
handled, including these two out-of-scope items, with **1,990** substitutions
and **249 facts / 248 documents** still open (241 acquired distribution, 7
other). The separate 600253 targeted notices confirm 1,122,431 effective
cash-choice shares, but no account-level fractional rule or compensation; that
chain remains open. Full Dataset and studies remain locked.

## Current R5 dual-parent 2010 official merger-chain audit — 2026-09-18

The bounded ordinary unrestricted, non-cash-electing 600607 and 600842 A-share
conversions into the same surviving company are now source-byte, page-term,
master-lifecycle, raw-boundary and input-order audited. The respective ratios
are 1:1.61 and 1:0.96. Both parents last traded 2010-02-03, halted from
2010-02-04 and terminated 2010-02-12; registration completed 2010-02-23.
New unrestricted shares were listed on 2010-03-01, the surviving company's
code changed 600849→601607 on 2010-03-05 without changing its stable ID, and
trading resumed only on 2010-03-09. An affiliated 600607 holder elected cash
for 160,440,885 shares and is expressly outside the non-electing audit; no
600842 holder elected. Individual registry fractional awards are not claimed.
The two exact P1 source requests close without adding an accepted economic
event or certifying a full merger census. Cumulative v49 is **16,069/16,320**
established, **1,990** official substitutions and **251 facts / 250 documents**
open (241 acquired distribution PDFs, 9 other). Full Dataset and studies stay
locked; the retained-bonus fractional methodology gate remains active. See
`../research/R5_MERGER_LEAD_CLOSURE_V1.md`.

## Current R5 600631 official merger-chain audit — 2026-09-18

The ordinary unrestricted A-share, non-cash-electing 600631→600827 chain is
now source-byte, page-term, master-lifecycle, targeted raw-boundary and
input-order audited from six official contemporaneous issuer PDFs. The ratio
is 1 old share to 0.861 new shares. The 2011-08-04 cash-choice record day is
also the last parent trading day; continuous suspension begins 2011-08-05,
parent termination is 2011-08-23, merger registration completed 2011-08-26,
and new unrestricted successor shares list 2011-08-31. The issuer reported
zero cash-choice elections. The approved merger research floor cannot recover
an individual's actual residual-share award. External immutable audit manifest
SHA-256 is `03e73decd34373a09f32e62d61561f5dc57ca40780011371a518b25cbc5a00e9`.
The exact P1 source request closes with no change to the 15-event accepted
inventory or full-merger census. Cumulative v48 is **16,067/16,320**
established, **1,988** official substitutions and **253 facts / 252 documents**
open (241 acquired distribution PDFs, 11 other). Full Dataset and studies
remain locked; the retained-bonus fractional methodology gate remains active.
See `../research/R5_MERGER_LEAD_CLOSURE_V1.md`.

## Current R5 600832 official merger-chain audit — 2026-09-18

The ordinary unrestricted A-share, non-cash-electing 600832→600637 chain is
now source-byte, page-term, master-lifecycle, raw-boundary and input-order
audited. The final ratio is 3.05 old shares to one new share; the last parent
trading day is 2015-04-29, continuous suspension begins 2015-04-30, record
and termination are 2015-05-20, registration is 2015-05-27, and new
unrestricted successor shares first trade 2015-06-03. The 2016 issuer
confirmation is audit-only and does not leak into the point-in-time event.
The approved merger-specific floor models unknowable individual registry
remainders; it is not a claim about the actual award. External immutable
event-audit manifest SHA-256 is
`4a539fd39a893150cbb24bac65efe4a207c55ce06f163f27013b5905a893a850`.
The matching P1 source request closes, but the 15-event accepted inventory
and full-merger census do not change. Cumulative v47 is **16,066/16,320**
established, **1,987** official substitutions and **254 facts / 253 documents**
open (241 acquired distribution PDFs, 12 other). Full Dataset and studies
remain locked; the retained-bonus fractional methodology gate remains active.
See `../research/R5_MERGER_LEAD_CLOSURE_V1.md`.

## Current R5 older SSE merger-report recovery — 2026-09-18

Recovered the exact official full issuer reports for the 600607/600842→600849
(stable 601607), 600631→600827 and 600832→600637 parent chains from retained
CNINFO metadata. Original PDF receipts and source SHA-256 are recorded in
`../research/R5_MERGER_LEAD_CLOSURE_V1.md`. Report, progress and result
notices establish ratios and several termination/registration/listing dates,
but not every actual tradability boundary, parent/holder scope or registry
fractional award. This historical checkpoint preceded the bounded audits
above; the four leads were incomplete at that time.
P0 public master remains PASS and no paid source was used.

## Current R5 000418 official merger-chain audit — 2026-09-18

Four issuer PDFs, including the final post-dividend ratio and listing notice,
are source-byte and page-term verified for the ordinary unrestricted A-share
non-electing path. The audited 000418→000333 ratio is 1:1.15144821, with last
parent trading 2019-05-07, record 2019-06-20 and first converted-share
listing 2019-06-21. Immutable external manifest SHA-256 is
`aa76da4feb7265b7e5376fd1388f7a0a7d86933fd219e8b663f824377af1a4f7`.
The matching `MERGER_NEW:000418:000333` P1 source request is now closed, making
cumulative v46 **16,065/16,320** established with **255 facts / 254 documents**
open (241 acquired distribution PDFs, 13 other). This **does not** claim actual
account-level registry fractional awards, B or restricted-share closure,
accepted-inventory revision, full merger census or Full Dataset readiness.
The existing retained-bonus fractional methodology approval gate remains the
immediate R5 stop.

## Current R5 600337 original designated-disclosure recovery — 2026-09-18

The 2011-06-08 official SSE publication index has exactly one 600337 entry
for the 2010 distribution implementation announcement. The issuer's
2010 annual report, published on CNINFO before that date, names
`《证券时报》` as its designated disclosure newspaper. Its original 2011-06-08
page carries the signed issuer notice (临2011-022): gross 0.05 CNY/share,
record 2011-06-13, ex 2011-06-14, payment 2011-06-20, with explicit direct
versus CSDC-disbursed holder classes. The announcement was isolated from
adjacent issuers before parsing and visually checked. This closes exactly one
non-queue P1 source fact against the already accepted cash event; it creates
no new event. SSE PDF bytes were bot-denied and remain marked unverified, not
silently substituted. Original designated-paper report v2 SHA-256
`7455aa578e57af8f230e396e5304d065efbf82feb80c83a6006244557f79aae6`,
manifest `2f04cc4e369e865d464b3ef2bd9defaf5b6713d267c8cd4f20e81635b3150876`.
Cumulative P1 v45 establishes **16,064/16,320**, including 1,985 official
substitutions, leaving **256 facts / 255 documents** (241 acquired distribution
PDFs, 14 other); manifest
`8c5df32f7ae0a6113ee946c8e917974d96d3152dcd6f741c588c5a8f8a7bdf1f`.
The fractional retained-bonus human methodology gate and full-census/safe-start
gates remain unchanged. Earlier P1 counts below are historical.

## Current Docker/WSL runtime recovery — 2026-09-18

Docker Desktop's engine had stopped after the same `sailor-ingest.sock`
runtime-socket rename error; WSL Ubuntu was running but its Docker CLI
integration was absent. After stopping the failed Desktop processes, the
two-entry runtime `run` directory was moved intact to a recoverable sibling
backup, then Docker Desktop was started normally. No image, volume, database,
project file or frozen dataset was deleted. Windows and WSL clients reach
Docker Engine 29.7.2 / Docker Desktop 4.89.0 and Compose v5.5.0. Existing
project containers were restarted without a rebuild: PostgreSQL and Redis
healthy, Redis PONG, backend healthy, `/api/health` HTTP 200 and frontend
HTTP 200 on its configured port 5173. This clears the separate local Docker
runtime blocker; it changes no data-authority or methodology decision.

## Current R5 convertible-halt notice closure — 2026-09-18

Two official 601998 convertible-bond conversion-halt notices are nonfinal
ordinary-A dividend references. Each expressly scheduled a later final issuer
A-share implementation notice, and exactly one accepted final event has that
publication date and title. Their indicative cash amounts (0.356 and 0.1847)
**differ** from final amounts (0.3261 and 0.1825), so no amount is sourced
from the hints. Nonfinal-scope v7 closes 32 documents total, SHA-256
`703d28b09c9c6b166ea65f98a05fcf6c6a5627d17cbd47ff92f8e253b18e600f`,
manifest `4fd9861ea5eb5524b5b89b7a8208c120d78117d94662e56081ef49e14dd7511c`.
Cumulative P1 v44 establishes **16,063/16,320** facts, with 1,984 official
substitutions and **257 facts / 256 documents** still open (241 acquired
distribution PDFs, 15 other). File SHA-256
`c2d91ce7c41b6a1c4d3c73e182ad88f73008b616ab76ab9b6984a0d0fe92a9fc`,
manifest `f62f73a38ed45060f55b9c641445b7465c77c8e65bc507672f1c45b06dfcb0b9`.
Current queue v6 SHA-256 is
`2469c4d53d7c9584137240285ca7aaf78e1d2c45fc6b396782a4cec7299a820a`;
source-bound triage v16 has 94 bonus-only, 1 both, 3 cash-only and 143 neither.
No new event, full census, safe-start or dataset acceptance is inferred.
The retained-bonus fractional methodology gate remains active.

## Current R5 P1 nonfinal A-share schedule closure — 2026-09-18

Seven checksum-verified official 601186/601390 A/H-share notices provide
preliminary A-share record/ex-date schedules and explicitly promise a later
final A-share implementation announcement. Each has exactly one later accepted
official issuer primary notice with the same security and exact A-share dates,
published before the record date. The H-share schedule is not substituted for
the A-share event; no new cash or bonus event is created. Nonfinal-scope v5
closes 30 documents total (23 prior + 7), file SHA-256
`fc0ca2c1901493dee85ecce10ab96d4611838e0944359e6239dc38ad52db43b0`,
manifest `65741fb57ca0394ed5d4fed49b389293a3736cad869d8216d62ea91c3fc19447`.
Cumulative P1 v42 establishes **16,061/16,320** facts, with 1,984 official
substitutions and **259 facts / 258 documents** still open (243 acquired
distribution PDFs, 15 other). Its file SHA-256 is
`37aed2cd4acaf9c0d54779c122e0bb7a4a2ba4b5655620f4cd11f59225c16592`,
manifest `e48e0a00c98bf66ef6f1a112fa2827a1c3ed1f47bbf2825ede4e9535c3d6e873`.
Queue v4 SHA-256 is
`7c7ef6c3f18e5cfaa6e91e190485141d3fa73385f11524e4a6bf4890655bc5ec`;
its source-bound triage v14 has 94 bonus-only, 1 both, 5 cash-only and 143
neither. Replay/input-order checks pass. The contemporaneous 301262 issuer
notice has a malformed ex-date; later official yearbook/annual-report data
corroborate the likely date only retrospectively, so it remains unaccepted
under point-in-time rules. P0 remains PASS; full cash/bonus census, verified
safe start and Full Dataset remain unresolved. The retained-bonus fractional
methodology gate remains active; no freeze or study was run.

## Current R5 P1 fact-level closure — 2026-09-18

P0 official-public reconstruction remains PASS for 2,403 SSE and 3,028 SZSE
securities, with zero unresolved core facts; no paid product was used. The 257
official CNINFO PDFs previously acquired remain checksum-bound and were not
downloaded again. Five non-primary/mixed distribution notices exactly match
accepted primary ordinary-A cash events (security, cash amount, record and
ex-date); their bonus components remain source terms only, pending accounting.
Two more derivative price-adjustment notices explicitly state that the same
accepted distribution completed on its ex-date. These are seven fact/scope
closures, not seven new economic events.

Immutable matched-cash v4 closes 45 documents (11 exact primary corroborations,
34 stronger-official substitutions); derivative v4 closes 17. Cumulative P1
v41 establishes **16,054/16,320** facts with 1,984 explicit official
substitutions; **266 facts / 265 documents** remain (250 distribution queue,
15 other). The v41 file SHA-256 is
`bc2e7ee19fbeb5d7e51a6720043a08e040103e684c5519f2f72c474669e2bd2c`,
canonical manifest `343efeadddbed6d381e4f0be5f2def2168ac56926e404d2f0b64652014571ed3`.
The remaining-queue v3 file SHA-256 is
`f64ac1d19bddbec85ccf111f0cb997efb11ecc1c0a4d29dd662e99a194092b62`.
Input-order and immutable replay checks pass. Full cash/bonus census and
verified safe start remain unresolved; no Full Dataset, freeze or study exists.
The separate retained-bonus fractional-share human methodology gate remains
active.

## Current R5 human methodology gate — 2026-09-18

Official 688339 implementation notices and the existing portfolio accounting
path expose a material retained-bonus fractional-share ambiguity: a reachable
100-share sequence becomes 140, 196, then 274.4 theoretical shares, while the
official registry allocates only whole residual shares using cross-account
ranking and random ties. Public issuer/exchange data cannot reproduce a single
account's allocation. Approved retained-bonus policy preserves basis but does
not specify this quantity convention; the merger-specific floor policy is not
silently extended. `R5_STATUS=BLOCKED_RETAINED_BONUS_FRACTION_POLICY_HUMAN_DECISION`;
`HUMAN_APPROVAL_GATE=R5_RETAINED_BONUS_FRACTION_POLICY`. See
`../research/R5_RETAINED_BONUS_FRACTION_GATE.md`. Earlier P1/source snapshots
below are retained as history; the current counts are in the section above.
Full Dataset, freeze and studies remain NO.

## Current R5 bonus-source term corroboration — 2026-09-18

The acquired 257-document official queue was re-triaged with an exact SSE
three-date bonus/listing-table parser and the issuer's `每10股转增股N股` form.
Source-bound triage v10 has 94 bonus-only, 7 cash-only, 6 both and 150 neither;
its parser dependencies and source hashes are pinned (manifest
`528c5aea4c5d94eeef216a9c10322f6a1ca3dfb41cd8a13ef18fc5e9a9222425`).
Official issuer PDF terms, point-in-time ordinary-A identity and exact exchange
record/ex-date ratio now corroborate 92/94 bonus-only notices: the previous
60 remain unchanged and 32 are newly corroborated. Bonus-source v4 file
SHA-256 is
`09fb6e2368b70e9275926588b5a66cc52ceb731c66ae470e24c5b8ba0eb10f29`;
manifest is `77c70f05b5aa7a14c48915b3bdeae8754c626fc431e797d2d389544c2ee58097`.
The other two are 002982 (issuer-only, no matching exchange oracle row) and
688692's secondary result/上市 notice (its primary implementation notice is
already among the 92). No new economic event or P1 fact was accepted from
this source-only corroboration; P1 remains 16,047/16,320, 273 facts open.
Corporate-action fractional/holder accounting and the remaining source classes
continue in R5. Full Dataset, freeze and studies remain NO.

## Current R5 targeted official-source recovery — 2026-09-18

The previously denied CNINFO PDF endpoint now returns official PDF bytes for
the exact remaining 257-document P1 distribution queue. Resumable acquisition
reused five prior PDFs and obtained the other 252; all 257 have verified PDF
receipts and page-addressable text caches, with zero retrieval failures. The
immutable source manifest SHA-256 is
`b5f786f7888e9828452e200a01e0d9cfee0abe7974f2717aabd5e2686fbde9be`.
This is source acquisition, **not** event/fact acceptance. Conservative triage
finds 7 cash-only, 93 bonus-only, 6 both and 151 neither under existing strict
parsers; differentiated/structural actions still need separate accounting.

Seven of eight prior retained-cash rejects are now closed: official issuer
corrections for 300207 and 600801, PDF page-number/date-boundary repair for
000776 and 002050, and exact source-bound issuer-internal timing plus SZSE
monthly corroboration for 000826, 300384 and 300852. The prior 263 accepted
economic identities, amounts and record/ex dates are unchanged. Retained-source
v22 closes 270/271; 600337 still lacks a final implementation source and its
payment/holder terms are not silently supplied by a shareholder resolution.
Cumulative P1 v39 establishes 16,047/16,320 facts with 1,979 explicit official
substitutions; 273 facts / 272 documents remain (257 distribution queue, 15
other). Full cash/bonus census, verified safe start and Full Dataset remain
PARTIAL/NO. No commercial source, dataset freeze or study was used/run.

## Current R5 official cash-source recovery — 2026-09-18

P0 SSE/SZSE public reconstruction remains PASS (2,403 / 3,028 securities,
zero P0 facts unresolved). A source-pinned extension of the existing 000022
A/B-share cash conflict reconciles four more 2012 notices (000028, 000530,
000570, 000581): each final issuer PDF states ordinary-A gross CNY cash and
the B-share HKD rate, while its exact SZSE monthly row reports the rounded
currency-converted figure but an A-share pre-close/ex-price delta equal to the
issuer's CNY amount. Both values and original source hashes remain explicit.
The retained 601818 ordinary-A final notice is distinguished from a preferred-
share companion for the same event. For 600378, the retained official issuer
correction explicitly replaces wrong 2014 entitlement years with 2015. Six
garbled/image PDF text layers are resolved using existing SHA-bound PyMuPDF/
OCR evidence; agreeing alternate extractions are recorded, and the 300041
scan was visually checked. No event is newly created or globally overridden.

Immutable retained-source v18 closes 263/271 candidates; eight remain (seven
issuer-date conflicts, one missing final source). All prior 257 v16 closures
remain byte-identical. File SHA-256
`3a326b2e2a65fee2a2806ed221226bf691cad529f8a76fd43fb0653c05e005b6`,
manifest `6c3504821626b2c9342528af51e2f5d6a50f67e3a0ac8d0d3ea9edb6983239b3`.
P1 cumulative v36 establishes 16,040/16,320 facts with 1,972 official
substitutions; 280 facts / 279 unique documents remain (257 cash-queue, 22
other). File SHA-256
`80e49f25fd99f3256406d81c1fcfdf3c3ff0037c020af86b83d29b2ff9755e06`,
manifest `2a02f9dcb6b0e3204321cb7957f8ca30780a4ae4b3744599218de220e8b9f72e`.
Both reports reproduced byte-identically. Full cash/bonus census, safe start,
Full Dataset and all research studies remain blocked; no paid source was used.

## Current R5 recovered historical-code A/B cash fact — 2026-09-18

The 000022 2012-07-12 CNINFO final implementation PDF was already retained in
an earlier official cash-gap batch; only a newer targeted redownload failed
DNS. Its original SHA-256 is
`5ee3949582e2c5c967b4a3059c2b8c7a8077d50b0067608af584542b5deabee6`.
The notice gives gross ordinary-A cash CNY 0.40/share, record 2012-07-19 and
ex 2012-07-20. P0 master maps historical 000022 to stable
`CN-A:SZSE:001872` with an official code-transition receipt; the already
accepted event has the same source SHA and facts. The SZSE monthly table's
A-row DPS `0.491` conflicts with the issuer, but its pre-close/ex-price delta
is CNY 0.400 and the issuer's B-share HKD conversion rate maps 0.40 to 0.491.
The one-event, source-pinned reconciliation records both values and hashes,
without creating a new event or globally overriding exchange data. Retained
source v12 closes 251/271 candidates, preserving all prior 250 rows; file
SHA-256 `019e59611c9aad04c07f056b7578cd3397a967b264519220497f117b6d524e69`,
manifest `fc8005c3097f95166dd448c9e2bcb940ed9e784b0f39fc282c0de0ef869a70be`.
P1 cumulative v30 establishes 16,028/16,320 facts and leaves 292 facts /
291 documents (257 cash-queue, 34 other), with 1,960 official substitutions;
file SHA-256 `9fe049e0c315d427f56a65d11ceefea62ff411e544baa67d08abc37cd1298918`,
manifest `2ab3a12fad49b846d7b6d59091fa47ed63be95648347ffc071541614a06251f6`.

## Current R5 official correction reconciliation — 2026-09-18

Two retained official CNINFO corrections now reconcile with already accepted
cash events and their original issuer PDFs. For 002866, the corrected 2023-05-15
record and 2023-05-16 ex dates replace an erroneous 2022 year in the original
notice. For 600586, corrected gross cash is CNY 0.03/share rather than the
original CNY 0.00298/share. The parser requires exact before/after-only edits,
source PDF/text checksums, original-source linkage and a unique matching
accepted event; all five prior correction rows remain unchanged. Correction
report v7 closes 7 documents, SHA-256
`c67b0ce0beb9ef5c09f0a75350ef6165b204f210b8c40dd68fec324549c34ebe`,
manifest `720c4032fecd0996be6d8514efb3a11d5c52172ff62f35f46100484f7d5a7e00`.
P1 cumulative v29 establishes 16,027/16,320 facts, leaving 293 facts /
292 documents (257 cash-queue, 35 other) and 1,959 official substitutions;
SHA-256 `9174b3461a28cf1a63be40c071c271e48d82a136a76da909bee29332d4ae38de`,
manifest `c4d4e0d7d842a74e1ddb92509670a407d4c52de1d3c118597730df7906f81f5d`.
This does not establish a complete cash or corporate-action census.

## Current R5 nonfinal official-notice scope — 2026-09-18

Four more SHA-verified retained CNINFO PDFs are non-executable notices:
301233 seeks authority to formulate a later interim plan, 002611 and 603363
explicitly announce no distribution, and 600157 defers implementation. None
has parsed cash/bonus terms or entitlement dates. The 601009 bank proposal is
not closed because its PDF has a preferred-instrument marker. Immutable scope
v4 preserves all 19 prior closures and adds four (23 total), file SHA-256
`c8fdbeeea3bab0bae92559d45cf15f14efb972b825bd266586983a84008f34ad`,
manifest `d93ff588b4c20abdd318a9aa8009d6aad6c3e633d1ec280b7279e136795f2e18`.
P1 cumulative v28 establishes 16,025/16,320 facts and leaves 295 facts /
294 documents (259 cash-queue, 35 other); 1,957 official substitutions are
unchanged. Cumulative file SHA-256
`446a732b0d78a90fd844f4c09acd850f2356861b64e6ea52b3ac0e0020291228`,
manifest `3ba4c92765883614c34ecd1877d8135cd7ca7a3796a3cde204c18f038aa659d5`.
No economic event or full cash census is inferred from these notices.

The later targeted 000022 redownload failed DNS after three bounded attempts;
an older checksum-verified original PDF was subsequently found and reconciled
above. The failed retrieval receipt remains in the archive, but is not the
source of accepted cash facts.

## Current R5 dual cash-and-bonus official source closure — 2026-09-18

Fifteen previously URL-less P1 dual-leg requests have one retained final
official CNINFO issuer PDF whose original SHA-256 is shared by accepted cash
and bounded bonus events. Re-reading each checksum-verified PDF/text confirms
issuer, ordinary-A identity, gross cash, retained share ratio and record/ex
dates against independent SSE cash/bonus rows. Fourteen issuer notices state
the exact dates; 600845 also lists a separate B-share record date, resolved
under the existing exchange-date disambiguation rule rather than borrowed as
the A-share date. The sixteenth request, 603023, remains open because its
bonus component/allocation conflict has no accepted bonus leg. Dual source
report v3 closes 15 documents / 30 facts, manifest
`aec400280226fcb64b4e8c99ff1aba36c8993b289a29984c0f621bc10a87891e`.
P1 cumulative v27 now establishes 16,021/16,320 facts, leaving 299 facts /
298 documents (263 cash-queue, 35 other, including one dual-leg request)
and records 1,957 official substitutions; manifest
`9924282d5b416b67b0f99b87fc77f03be0e06973cefa414966d975be0d2bf95e`.
All prior 2,265 P1 closures are unchanged. No new economic event, full
corporate-action census or Full Dataset is asserted.

## Current R5 retained bonus term reconciliation — 2026-09-18

Three previously unresolved bounded integer/next-session cases now reconcile
against retained official issuer implementation PDFs: 600056 and 601233 have
explicit post-implementation total-share/increase arithmetic corroborating the
one-for-one quantity despite conflicting earlier/component labels; 603686 has
an isolated `转赠股本` heading typo but an explicit `每10股转增10股` body. The
shared parser accepts only the exact generic evidence patterns and still
rejects unsupported restructuring and unresolved component conflicts. Official
exchange ratios, entitlement dates, ordinary-A identities and the approved
accounting policy remain separate checks. Bounded ledger v24 supports 281/288,
with seven unresolved and 7,119 oracle rows outside scope. All 278 previously
accepted event checksums are unchanged; reversed date-link order reproduced
identical base-ledger bytes. Ledger SHA-256
`08ae99961bfeb74d81d94144881db3a5faca1732993bbcc768a8b344dca5a107`,
manifest `8f3ebac218ae4f335cc305bbfd246031db73af2e13dc85b0cc394e3cdfb2ffed`.
This is not full bonus census or Full Dataset readiness.

## Current R5 bounded bonus official-source recovery — 2026-09-18

The two SSE implementation-PDF URLs previously denied by the SSE host are no
longer required for their facts: contemporaneous official CNINFO issuer PDFs
were already retained for 603315 and 603889. Each original PDF and text cache
is SHA-verified and states one transferred share per held share, exact
record/ex-dates and the next-session scheduled new-share listing. The official
exchange oracle, point-in-time ordinary-A identity and approved accounting
policy also reconcile. Bounded integer/next-session bonus v20 now supports
278/288 cases, with ten still unresolved and 7,119 oracle rows outside this
subset; 276 prior events remain unchanged. Ledger manifest
`82fcdf1d558adfa1e81f6486ab74f73fcfdf920bfdf7a13c1cff6e615db603f0`.
This does not establish full bonus census, actual new-share tradability or a
Full Dataset. No paid source was used or purchased.

## Current R5 issuer-body finality reconciliation — 2026-09-18

Thirteen more retained official CNINFO cash notices had abbreviated or generic
index titles, but their original PDF bodies contain implementation-method
terms. Every accepted notice has the exact issuer, ordinary-A gross cash,
record/ex-date and official exchange target; source PDF, extracted text and
manifest checksums are retained. A warning about a convertible-bond trading
pause, a shareholder resolution, and a generic notice without implementation
body evidence remain unaccepted. The last newly closed 002215 notice has an
explicit `分配方法` section and matching dates. Source v10 preserves all 237
v8 closures and closes 250/270 candidates, with 20 rejected explicitly;
manifest `134db8ba9c28f4a60f62c6f599aa94c4838f7ff9473e833d82bb3969004047bd`.
P1 cumulative v25 establishes 15,991/16,320 facts, leaving 329 facts / 313
documents (263 distribution, 50 other) and 1,942 official substitutions;
manifest `04cc6edc70787f8ec17f6877ce2db480147b62ee066fb9324d9a680276e995d3`.
Full Dataset, freeze and research gates remain closed.

## Current R5 SSE-composite issuer cash receipts — 2026-09-18

Eleven URL-less P1 cash requests with accepted SSE-table/CNINFO-composite
events now have unique retained final CNINFO issuer notices within 60 days of
their record dates. Original PDFs and text hashes, issuer identity, exact
ordinary-A gross cash, and official exchange amounts and dates all reconcile.
One 2020 special-dividend notice uses a slash-date table with a distinct
`特殊股息现金发放日` heading; the date parser now recognizes that exact official
table shape. Earlier 226 closures are unchanged. Source v8 closes 237/270
candidates, with 33 rejected explicitly; manifest
`1a3246c76ec777da95e91c4ebec4413a8fb4d10844373edf79a72e829c9f17a8`.
P1 cumulative v23 establishes 15,978/16,320 facts, leaving 342 facts / 326
documents (263 distribution, 63 other) and 1,929 official substitutions;
manifest `abc8888f39801cbe3fe47aae0d297e3869202bc7e510712e39b8bd5bf0c1da54`.
No new economic event, Full Dataset, freeze or study was accepted.

## Current R5 differentiated-public-A source closure — 2026-09-18

Six additional URL-less P1 cash requests have retained official CNINFO final
implementation PDFs and already accepted differentiated-public-A cash events.
The approved holder-specific parser, not the generic gross-cash parser,
reproduces each exact public-A amount and issuer record/ex-dates; official
exchange amounts/dates and original PDF/text hashes also reconcile. This
scope is gated by policy `DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1` and does not
create new economic events. Retained-source v7 closes 226/259 candidates;
33 remain explicit. Manifest
`8edb4a40f7c53aaebc83e346c7765ea60845221c913a75373c5753dc1063a8c7`.
P1 cumulative v22 establishes 15,967/16,320 facts, leaving 353 facts / 337
documents (263 distribution, 74 other) and 1,918 substitutions; manifest
`be12aaf8a9c6c5e038dc6e22740b8686bcb738b155159c4ea2e100ba56730cf1`.
Full Dataset and research gates remain closed.

## Current R5 historical-code cash reconciliation — 2026-09-18

The official point-in-time master maps historical SSE code 601313 to stable
security ID `CN-A:SSE:601360` until 2018-02-22, with an official code-change
receipt. Six previously unresolved final issuer PDFs use that historical code;
their original bytes, gross cash and record/ex-dates independently match the
accepted stable-ID events and official exchange targets. The retained-source
selector now permits this alias only with an effective-dated master transition
receipt; legacy selector callers retain their prior behavior. Source v6 closes
220/253 candidates, leaving 33 explicit; manifest
`d125a9d83737bf6251efbb3c82148a819378c7e0e89db9be374db46fce20d095`.
P1 cumulative v21 establishes 15,961/16,320 facts, leaving 359 facts / 343
documents (263 distribution, 80 other); 1,912 official substitutions are
recorded. Manifest `1a9987a52b879be1b6338e252e5d5cbc21d77cb7212152eb592b09fbf000e0c3`.
No new economic event, Full Dataset, freeze or study was accepted.

## Current R5 retained official full-cash source closure — 2026-09-17

Reused retained CNINFO source manifests, original issuer PDFs and text caches
against cash v43, point-in-time master and official SSE/SZSE exchange targets.
Of 253 previously URL-less P1 final cash candidates, a narrow additional
final-implementation/actual-payout title rule identifies 45 more than the
prior 169. Every acceptance still requires retained official issuer bytes,
identity, exact gross amount, and official exchange date/amount corroboration.
The 214 closed include 63 issuer-PDF year conflicts before publication whose
month-days match the authoritative exchange dates; both raw source dates are
preserved, and the effective dates come only from the exchange. Thirty-nine
remain explicit: 21 title/master unmatched, eight issuer-date conflicts, four
amount conflicts, six without a unique explicit gross amount. No new economic
events were created. Source report v4 manifest
`83551f6d84c11db717f88c134347b9dfc039b75d19d05e90889a0e263ba90e5e`.
P1 cumulative v19 establishes 15,955/16,320 facts, with 365 facts / 349
documents unresolved (263 distribution, 86 other) and 1,906 official
substitutions; manifest
`ab39ff3a3acdf8c61b2cb07651fcda472d37fdb363a8aaafeec1a29335ea8d97`.
Full issuer cash census, bonus census and SZSE resumption remain PARTIAL. No
Full Dataset, freeze or strategy study is accepted.

## Current R5 historical derivative-reference closure — 2026-09-17

Four further official notices are non-primary references, not new dividends:
two 600180 option-price notices cite the prior 2021/2022 annual implementation
plans, a 002543 employee-plan price notice cites its 2024 half-year
distribution, and a 603707 convertible-bond pause notice precedes the final
2024 annual cash implementation. Exact issuer/gross amounts, explicit
distribution-year labels where the original event is older, unique accepted
issuer events, PDF/text checksums and bounded chronology are verified.
Derivative scope v3 closes 15 notices in all, manifest
`832e9c7d9643ba231eeb7c51d9151c3039673f472607dcc80deb01593935abcd`.
P1 cumulative v15 establishes 15,741/16,320 facts, with 579 facts / 563
documents unresolved (263 distribution, 300 other). Substitutions remain
1,692; manifest `ea29e9ddc363f4f7a652487de22815b51f0e49d7d0439d3930a34e774501e931`.
No future final event is treated as known at an earlier proposal date, and no
new economic event is created. Full-period source gates remain PARTIAL.

## Earlier R5 non-primary buyback-notice closure — 2026-09-17

Three retained official repurchase-price notices use the phrase `回购股份价格上限`
previously missed by the narrow non-primary filter. Each has no independent
record/ex-date and matches a unique separately accepted official issuer cash
implementation event by ordinary-A symbol and exact gross amount within the
bounded publication window. PDFs, extracted text and accepted-event checksums
were verified. Derivative scope v2 closes 11 notices (up from 8), manifest
`f6be92067cd621017bb93441118e4bd1b4b763d1bd0007e23068b65283ac9fd7`.
Cumulative P1 v14 now establishes 15,737/16,320 facts; 583 facts / 567
documents remain (267 distribution, 300 other), with substitutions unchanged
at 1,692. Manifest `aaab2b753fe70f6b2aafdbfce6bb4e920e50e4397c422150fd06432630bf8b19`.
No new event, Full Dataset or research gate is accepted.

## Earlier R5 nonfinal cash-notice reconciliation — 2026-09-17

Seven additional retained official issuer notices state a tentative cash
amount but no record/ex-date; each contains an explicit approval/implementation
contingency and matches exactly one later separately sourced official issuer
implementation event (same ordinary-A issuer and gross amount, final notice
published before its ex-date and within 180 days). These proposal notices are
**not** used as effective-dated cash events. Original PDF and extraction SHA-256,
the final event checksum, and input-order checks are recorded in proposal
scope v3 (19 closed, up from 12), manifest
`8d259671fa7ec84ebf0e2de53451e3db5e989d456786082d07e7d1171f9820a9`.
Cumulative P1 v13 establishes 15,734/16,320 facts and leaves 586 facts /
570 documents (270 distribution, 300 other); official substitutions remain
1,692. Manifest `eeaa54e9616416d443705bb0184c7cb8ce445c702fb188516941936fe5b9835a`.
Cash/bonus/SZSE full-period gates remain PARTIAL; no Full Dataset is created.

## Current R5 retained-bonus PDF boundary correction — 2026-09-17

The retained official 601558 implementation PDFs exposed two extraction
artifacts: a page counter joining `10` into `102股`, and a quadrupled OCR
headline. The shared terms parser now preserves page boundaries, rejoins an
exact `每`/`股` page split, and ignores only the demonstrably quadrupled
headline when the implementation body is present. Replaying all 288 bounded
integer/next-session candidates supports 276 (up from 274); the two newly
supported 601558 events are dated 2011-06-07 and 2012-06-26. None of the
previous 274 accepted event keys or checksums was lost. Reverse date-link
ordering reproduced identical ledger bytes. Ledger v19 SHA-256
`acdfbc219cb826471769ea229482f8ada4eb9b728d50f0905cf8d66c69f29edb`,
manifest `edacba885961547fb484a20a82dd2e6e635e6df5e00c16f568ad9f77a3161788`.
Twelve remain unresolved: two missing official implementation PDFs, six
term/exchange conflicts, and four nonstandard entitlement cases. The other
7,119 oracle rows remain outside this narrow subset; no full bonus census,
Full Dataset, freeze or strategy study is accepted.

## Earlier R5 retained issuer cash precision — 2026-09-17

The 2010–2022 v7 date-link replay now uses the existing exchange amount only
to disambiguate **explicit** issuer gross-cash terms; it never manufactures a
term. It recognizes repeated PDF margin numbers, a non-economic appendix page
counter reset, separate A/H date-only tips, and date-only correction notices.
The accepted-prior guard preserves earlier ordinary and differentiated cash
events where their economics remain identical. The 2018 old guard correctly
rejected 300387's rounded 0.11/share against the primary issuer's exact
0.1100224/share, so that diagnostic was not published as a replacement.

An exact-precision cross-check found 1,162 single-notice issuer amounts that
round to an exchange cell: 1,139 were already exact in cash v41. The 23 still
rounded entries were rechecked against retained original official issuer PDF
bytes, linked extraction checksums, unique record/ex-dates, final implementation
titles and current gross-term parsing. Twenty-one supersede an accepted event
whose source PDF is **the same**; two replace SSE-table/CNINFO composite source
records with a corroborated primary CNINFO issuer notice. No security-specific
production rule or new economic event was introduced. Cash v43 contains
40,479 events, covers all 40,376 official exchange cash targets, and retains
103 issuer-only accepted events. Exactly 23 event checksums changed, with the
same event keys. Input-order and checksum checks pass; manifest
`e95886c38a38deca04f3d530f3a93a2e132156f670f5b6b17df8e3040b547cb8`,
file SHA-256
`ac2e996fcd8b9e20578e1b8ea08f6725e545bec8b6cb7152c0119b1bcbb3e191`.
The two source-bound precision receipts have manifests
`35fd52aa32953f0183b9d06cc50038f3247f3ce6cb088d944009e4b7d7bd2021`
and `37b1dd71e6bf8d023e420ad78daf3ebb0541d9dea2c6e3447327d4727faf3ebf`.
This closes the bounded precision gap, **not** the full issuer cash census:
P1 remains 593 facts / 577 documents, and bonus/SZSE resumption work remains
partial. Full Dataset, freeze and strategy studies remain locked.

## Earlier R5 retained-bonus integer subset — 2026-09-17

Replayed the existing 288 integer, next-session candidates against retained
SHA-verified official issuer notices, exchange ratios, lifecycle, and approved
basis-conservation policy. Explicit send/transfer and capital-reserve terms
add seven events; a compound ex-date / payment-date label links another 12;
the explicit stock-dividend leg supports one more. All 254 prior event checksums
remain identical. The ledger supports 274 / 288 and leaves 14 unresolved:
two lack a linked issuer implementation source, eight
have term/parser conflicts, and four are nonstandard/restructuring entitlements.
Reversed input order produces identical ledger bytes. File SHA-256
`f8bc4b47c0df4f13ed23ceefd2ed1d1666f0c9b726318d2e83a9d905a34ea76b`,
manifest `fec13a70ee44df54d2bbe714731af5fbfecff263c9a354df869874cf75dcffd2`.
The two absent cached issuer notices are 603315 (2016-06-07) and 603889
(2016-04-19). SSE official directory metadata identifies the implementation
PDFs published 2016-06-01 and 2016-04-12, respectively, but each PDF returned
`ACCESS_DENIED_STOP` at its official SSE URL; the one-attempt denial receipts
are under `bonus-targeted-source-recovery-v1`. Metadata is not event terms.
Replaying 2010–2022 date links found 849 new official matches and lost zero
old matches. These are date evidence only; full cash v41 is unchanged. Its
2016 diagnostic replay explicitly classifies three secondary A/H timing
notices as date-only, with separate final issuer cash notices for each. It
still leaves 32 earlier accepted events not independently recorroborated by
the current raw parser. The accepted-prior guard rejects replacement of the
cash ledger; diagnostic manifest
`66884f2dd84aab353462148424c6941b0fb183914ec4f7d3e88e27c091e14d39`.
This bounded subset is not a full-period bonus census; 7,119 oracle rows remain
outside the integer/next-session scope. Dataset freeze and research stay locked.

## Current R5 derivative-notice scope — 2026-09-17

Eight retained official convertible-bond, option-exercise or repurchase-price
notices are non-primary for ordinary-A cash entitlement. Each has no unique
record/ex-date in the derivative notice and an exact gross amount that maps
uniquely to an already accepted, separately sourced issuer implementation
event within a bounded publication window. Both source PDFs and cached
extractions are SHA-verified and reparsed. Four other derivative-like notices
with discordant amounts or no unique accepted match remain open. No derivative
was substituted for a final cash notice; no event was created. Report manifest
`0b807f1ae4529416b99589b20256801ae9142d474602bf6b2845f84b2a0fc848`.
Cumulative v12 leaves 593 facts / 577 documents (277 distribution, 300 other),
15,727/16,320 established or out of scope, 1,692 substitutions; manifest
`f69bf64aec243e9c91387e4b2b9913093eb5887d7d9f7dcc769a156347e21f91`.
Cash full census remains PARTIAL; Full Dataset and studies remain locked.

## Current R5 precise official issuer cash corrections — 2026-09-17

Four previously open SSE final implementation notices publish exact ordinary-A
tax-before cash terms finer than the accepted exchange table: 600459
2023-07-05 **0.16502** vs 0.165; 2024-07-04 **0.19006** vs 0.190;
2025-07-07 **0.24014** vs 0.240; and 603200 2023-04-27 **0.07471**
vs 0.075. Each issuer PDF was published before record, has matching
record/ex-dates, a unique A-share headline amount corroborated by the final
implementation body, no accepted bonus leg, and its precise amount rounds
to the old exchange-cell precision. Old proposal amounts in the same PDFs
were not accepted as final terms. Source report manifest
`de97170d183b81f349a99e8ed2a724d96d7ed6b49a5c447f5c90140fd6542737`.
Cash v41 atomically replaces these four accepted event amounts under the
existing checksum-linked supersession path: 40,479 events, 40,376/40,376
exchange targets, 103 issuer-only events, input order and checksum PASS;
manifest `8b35132432a3ca6400eb401ce9a7dc34a907ca0c3dfa9da7230b34608df33073`.
Cumulative P1 v11 leaves 601 facts / 585 documents (285 distribution,
300 other), 15,719/16,320 established/out of scope, 1,692 official
substitutions; manifest `3453857f0e7a1a85285720449ffc4991800349eaaa50100edc951158c8313e85`.
Full issuer cash census remains PARTIAL; no Full Dataset or study.

## Current R5 exact-date orphan cash replay — 2026-09-17

The common orphan cash classification now accepts **both** explicitly
printed issuer entitlement dates when they exactly match the same official
exchange row and accepted gross amount. This closes three previously
misclassified 600705 final implementation PDFs (2014-07-23, 2015-08-10,
2016-01-14). Replaying the already-retained source corpus also closed one
688388 notice (2022-05-06) using an exchange-disambiguated date set after
the earlier shared date parser improvement. All four were pre-record official
issuer publications and are existing-event source corroborations, not new
economic events. Orphan composite v10: 1,080 closed, 76 rejected; manifest
`23daf8481aeae8de4dba09986c7f22a7aea90e56ffeac1dfd475461110ffdba0`.
Cumulative v10: 15,715/16,320 established/out of scope; 1,688 official
substitutions; 605 facts / 589 documents unresolved (289 distribution,
300 other); manifest `b5ab47e0a99f4617a23dda4c798a620beb3332f3c9edfba2a4d9235b0773956a`.
Full cash census remains PARTIAL; no Full Dataset or study.

## Current R5 official nonfinal proposal scope — 2026-09-17

Twelve retained official issuer documents are proposals or authorizations,
not final distribution implementation notices. Each source PDF and cached
extraction is checksum-verified; each has no unique gross cash or bonus ratio,
no effective record/ex-date, and explicit conditional wording. Two further
proposal-like documents contain a cash amount and remain open; another has a
preferred instrument marker and remains open. No new event is created and no
existing event is altered. Proposal report v2 manifest
`33dc149fac61d102ae0820c3b33bf9739c63672e2bd74fd88173e48534dc66b6`;
disjoint cumulative v9 manifest
`f8044228720156d103e6e8f351d1751339c3abe5fad60d59dbeb0031a51164db`.
P1 now has 15,711/16,320 established or out of scope, with 1,684 official
substitutions; 609 facts / 593 documents remain (289 distribution, 304 other).
Full cash/corporate-action census remains PARTIAL. No Full Dataset or study.

## Current R5 301262 official annual corroboration — 2026-09-17

The official CNINFO 2023 annual report is now retained and SHA-verified
(`63c5b7258c4355c6219300d8dfc1a103519bc7bcfcf43c758f4bc8b4e4491144`),
with page 45 visually and textually confirming a 2023-10-30 record date and
2023-10-31 ex-date. It was published 2024-04-26, after the event. A complete
date-bounded CNINFO issuer announcement query (2023-10-24 through 2023-12-31;
six results, no further page) finds no corrected implementation notice; the
official 2023-10-27 Q3 report has no distribution date. The query snapshot,
Q3 PDF, annual PDF, retrieval times and SHA-256 receipts are retained under
`/home/yuchen/data/research/staging/p1-301262-annual-evidence-v1/`.
This retrospective corroboration does not make the malformed original ex-date
point-in-time authoritative. The event remains **UNACCEPTED** and full cash
census remains PARTIAL. No Full Dataset, freeze or study.

## Current R5 bonus-removal correction — 2026-09-17

The 003041 issuer's official 2024-05-30 pre-record correction removes only
the erroneously included 2-for-10 capital-reserve conversion clause from its
2024-05-29 implementation notice; the full normalized before/after cash terms
are identical. The original plan already stated no bonus, and cash v40 has the
same accepted 0.4/share event on 2024-06-05. This is an official correction of
a false bonus token, **not** a 0.2/share bonus event. The source-bound
correction report v5 closes one additional P1 document without changing an
economic event (manifest
`295259b4bd4e7e209dfd92c670484953f4b58ea27f46d29c549ed99413dcab9c`).
Cumulative v7 leaves 621 facts / 605 documents (301 distribution, 304 other),
15,699/16,320 established/out of scope, 1,684 substitutions; manifest
`8b166012a405f99c0f2da303000d0bc36a521a5feda216187e7356df95d17ec4`.
The separate 301106 correction **adds** an actual 4-for-10 conversion and
remains open for quantity, fraction and tradability accounting. No Full Dataset.

## Current R5 revised differentiated-cash notices — 2026-09-17

Two complete issuer implementation notices marked “修订版” (603506 and
600837) are now parsed as final revised sources, not dismissed as derivative
notices. Their public-A gross cash, record dates and ex-dates exactly match
the already accepted issuer events; neither has a bonus leg. Revision notices
without a matching accepted event or with a bonus leg remain fail-closed.
The 37-document differentiated replay v7 has ten exact accepted-event
corroborations, one prior notice superseded by an official correction, three
fully post-2025 chains, 22 missing final terms and one non-primary notice.
No new event was created. Its manifest is
`dc79e47128618c4c5e064ae5f9ab2d06bab8c8ff2ad67d41800916442783b3b3`.
Ten-report cumulative v6: 15,698/16,320 established/out of scope,
1,683 substitutions, 622 facts / 606 documents open (302 distribution,
304 other); manifest
`5042155dd92d723e67ff45f8f6543152391104e376241847dd30f0affd036469`.
Full cash census remains PARTIAL; the Full Dataset/study gates remain locked.

## Current R5 official correction fact closure — 2026-09-17

SHA-bound original/changed issuer PDFs establish that 002026's share-count
supplement leaves its 0.06/share cash, record and ex dates unchanged; three
other notices (300800, 002895, 002812) correct only payment dates and leave
their accepted cash facts unchanged. The strict before/after comparison closes
four distinct P1 documents, creates no event and does not normalize payment
dates into the accounting ledger. Correction report manifest
`b5d45da39b0874594b8871146b9fdaa90633b03baa5e4fefc1d37b62511b7aa0`;
cumulative ten-report v5 manifest
`6a18008cb6414714ce5201a9375ffe06c09a8716341a84830445c3a8222643d0`.
P1 now has 15,696/16,320 established/out of scope, 1,683 official
substitutions and 624 facts / 608 documents unresolved (304 retained
distribution PDFs, 304 other). Corrections that change bonus terms (301106,
003041) remain open. Cash full census is PARTIAL; 1,921 SZSE exact resumption
boundaries remain. No Full Dataset, freeze or study.

## Current R5 newly recovered issuer cash event — 2026-09-17

The shared date parser now also recognizes the explicit SZSE label
`股权登记日期`. Retained official CNINFO 002852 implementation PDF, published
2023-11-17, establishes ordinary-A gross cash 0.22/share, record 2023-11-24
and ex 2023-11-27; PDF SHA-256
`3e11fb3fefa0286876f71479b637c480f912530fd8b983d403a58e304978284f`.
The strict primary-notice replay adds exactly this one previously absent
event. Cash v40 has 40,479 accepted events, covers 40,376/40,376 official
exchange targets and holds 103 separately identified issuer-only events,
without duplicate dates (manifest
`187938f5ad214c9d8ad0e9620ed74a03df8171df505a7bda47febbec65897abb`,
file SHA-256 `1f2825b24594fe81d0b1b26589f6f77d741b396a46720393ba2afe9bce01eb8f`).
Full issuer cash census is still PARTIAL. Cumulative P1 fact replay v4
establishes/out-scopes 15,692/16,320, leaving 628 facts / 612 documents:
308 distribution PDFs and 304 other documents (manifest
`f1f66d06b7333b2a8e48a351536f7bd2f69336f7c3fb8beb58cc416010125b87`,
file SHA-256 `f6d0651c467aab833409f148daac8ac9d8a45cc3c6d80c358777e6a153259d20`).

Another official primary notice, 301262 on 2023-10-24 (PDF SHA-256
`af26edcd6277bc7212d9d43e9208650e119c33be27698f86a9457647b523d4c9`),
visibly prints `2023 年 10 年 31 日` for the ex-date. A later official
[CNINFO annual report](https://static.cninfo.com.cn/finalpage/2024-04-26/1219838683.PDF)
indicates 2023-10-31, but CNINFO returned HTTP 403 and the
[issuer-hosted annual PDF](https://www.ihicon.com/upload/portal/20240506/e32136fcee04ac4d0f7a4e175f486070.pdf)
timed out before source bytes/checksum could be retained. This event remains
UNACCEPTED pending independent official-byte verification; no date was
inferred from the misprint, payment date or missing bars. P0, ST and SZSE
resumption (1,921 unresolved boundaries) are unchanged. No Full Dataset,
freeze or study.

## Current R5 cash-table replay — 2026-09-17

The shared official notice date parser now reads unlabelled SSE cash schedules
with three or four date columns, without shifting B-share columns. Replaying
all 625 retained distribution PDFs changed dates for exactly ten notices: eight
already explained in differentiated-cash v5, plus 688533's exact accepted
0.45/share event on 2025-06-09 and 688059's record/ex chain on
2026-01-07/08, fully outside the dataset period. The latter is not the two
still-open cases with 2025-12-31 record dates. The 688533 official primary
notice is a same-event corroboration, not a new cash event. Full cash census
remains PARTIAL.

Cumulative disjoint-set replay v3 closes 1,965/2,578 baseline unresolved
documents/facts, leaving 629 facts / 613 documents: 309 retained distribution
PDFs and 304 other documents. P1 established/out-of-scope is 15,691/16,320;
official substitutions remain 1,679. Cumulative manifest
`487c2f52fbc55668892a5be4f7bbb25d00f9f2e4c0a182b5badb981b6e86759d`
(file SHA-256 `8df78d53961fa3ea4367b3ab186e9c705a0c0c0d2b08194a1d1e3df721a7b5cd`).
P0, ST and cash v39 events are unchanged; 1,921 exact SZSE resumption
boundaries still lack official closure. No full dataset, freeze or study.

## Latest R5 official differentiated notice cross-check — 2026-09-17

SHA-verified issuer PDFs and cash v39 were replayed against all 37 retained
differentiated-cash candidates. Eight notices exactly corroborate accepted
ordinary-A cash events (one is the already-counted 600157 v39 addition); seven
more P1 facts are now established. An earlier 688320 notice states 0.11/share,
but an official issuer **corrected version** published the next day, before the
record date, states 0.11038/share and is already the accepted v39 event. The
earlier notice is explicitly superseded, not accepted at 0.11, closing one
additional P1 request by official substitution. Three notices remain fully
post-2025, 22 lack accepted final cash terms and three are non-primary.
Original/correction PDF checksums, source URLs and dates are in cross-check
manifest `008648c4c7c55a0abc0eb775f19ac16b8683b88bc780006240a587ee6f00f620`
(file SHA-256 `294303d16f25534da4301e0f20447b3b1075ee26fe9c9b9ae53cc6d37d948e1c`).
Reverse input order and repeat checksum pass. A cumulative set-level recount
of all nine official closure reports found three post-2025 differentiated
notices missing from an earlier arithmetic update; no economic event changed.
The audited remainder is 15,689/16,320 established/out of scope, 1,679
official substitutions, 631 facts / 615 unique documents unresolved, including
311 retained distribution PDFs and 304 other documents. Cumulative manifest
`1f0f42e908b70ed71f059e0d22fa535aff0e20e3b914aa1279e3f8ebd85be59e`
(file SHA-256 `3a586dbe403cbba7f64e06340699b367802f85074a6363f43a7bfc965d9a9d26`). Cash v39
itself has no new event from this cross-check and full issuer census remains
PARTIAL; 1,921 SZSE exact resumption boundaries remain unresolved. No R5
dataset, freeze or study gate is unlocked.

## Latest R5 differentiated-cash correction — 2026-09-16

The already approved ordinary-public-A differentiated-cash policy was applied
to 37 previously unparsed retained issuer notices. Thirty-six remain outside
the strict new-event gate (three post-2025 entitlement chains, eight nonunique
dates, 22 without accepted final terms, three non-primary notices). One official
600157 final notice, published 2024-08-20 before its 2024-08-23 record date,
establishes a 2024-08-26 cash event of 0.00555/share to entitled holders;
0.00551/share in the same PDF is only a diluted ex-price reference. Source
PDF SHA-256 `896b402fe2a43bcd4398eee9ae1e0f8118c85aec817f0405a1c8a79e3c135b7f`;
strict classification manifest `2ff343d68a7edc5638fd1fa6a6ab7d7dfb95623911148f755ceb57254556c7bb`.
Cash v39 has 40,478 accepted events, 40,376/40,376 exchange targets covered,
102 separately identified issuer-only additions, zero target gaps and
checksum/input-order PASS (manifest `00e2780d2777904e4ebaf4c21667203e9e8cce397b93ebca6e2e71290b3ac2a8`).
Three other strict differentiated notices have both record and ex-dates in
January 2026, are disjoint from the earlier 23 out-of-period documents and
each carries one P1 fact. They are excluded only from the 2010–2025 window;
the two 2025-12-31 record-date cases remain open. Full cash census remains
PARTIAL. P1 is now 15,678/16,320 established or out of scope, with 1,678
official substitutions; 642 facts / 626 unique documents remain, including
322 retained distribution notices. No dataset or study gate
was unlocked.
Of the 22 notices that the differentiated-cash parser could not classify as
final cash terms, a separate source-bound bonus audit matches all 22 issuer
date/ratio pairs to official SSE bonus rows. Twenty explicitly say cash is
zero; two retain an unresolved cash leg. The 22 comprise 21 capital-reserve
conversions and one red-stock dividend with issuer tax terms. Manifest
`e3169ff82117534bfcaa03870966433c16261580c41a9409ce3941b54eed1f25`.
No bonus event or P1 fact was counted accepted; allocation, tax and accounting
remain to be resolved under the existing approved policy matrix.

## Authoritative 2026-09-16 R5 correction — official cash counterexamples

The retained P1 issuer PDFs falsify the prior *full-census* interpretation of
cash v35. An expanded conservative title/ordinary-A cross-check identified 142
primary, parseable official implementation notices: ten match v35, 25 have
2026 ex-dates outside the 2010–2025 target, **101 in-period SZSE notices have no
accepted event on their ex-date**, and **six in-period SSE notices contradict
the accepted cash amount**. Two examples are 601998 on 2024-07-10 (issuer 0.3261,
SSE table 0.326) and 2024-12-11 (issuer 0.1825, SSE table 0.183). The first
missing example, 001226 on 2023-11-30, is a final ordinary-A implementation
notice specifying record date 2023-11-29 and gross cash 0.40/share. The report
is immutable, source-hash-bound, and reverse-order reproducible: latest manifest
`d99465a98a534fd4449a6d89f0750bb7295ca2baf4781ca732fc585bc6f1c58f`.

Thus `CASH_DIVIDEND_FULL_CENSUS_STATUS=PARTIAL_OFFICIAL_COUNTEREXAMPLES_REQUIRE_RECONCILIATION`.
The v35 ledger and its 40,376 accepted entries remain unchanged as historical
audited inputs, but 40,376/40,376 was **not** a proven full census. Each of the
107 corrective notices was then revalidated against retained official PDF bytes,
text cache, exact terms and point-in-time ordinary-A identity. The immutable
primary-notice ledger contains 101 additional events and six precise replacements
(manifest `67ee85513cc2a83e2d4a1929ff03555b15b6ef71edf02b303abe19772d1fcb7c`).
Cash replay v37 contains 40,477 accepted events, covers all 40,376 old exchange
targets, and retains the 101 official issuer-only additions separately (manifest
`0928e86d1dd208f6796b31be98ede517ce9724a27eaf8f1df8f00cb421c5f6b3`).
An independent replay of the old SSE table-substitution path found 15 more
rounded-table values despite precise retained issuer PDFs. All 15 had exact
matching record/ex dates and were replaced by the issuer gross amount. Cash v38
still has 40,477 accepted events and 101 issuer-only additions, with 21 total
precise-issuer replacements and checksum/order PASS (manifest
`5ff94f3178d874abcb02017476adbe2f781ff48ebdcc7b78cad3e218b70e74a4`).
This repairs the **known** counterexamples but does not establish full-census
PASS. A separate official-document instrument check then classified 133
preferred-share dividend notices as outside ordinary-A scope, with zero A-share
events created (manifest `9d8b65e122f7bdce208605e7ef002be3b745c2dbffd3aa6123bd5dd53665c863`).
An additional exact official-source comparison closed 39 cash-only requests:
ten primary notices corroborate accepted events, and 29 derivative notices have
identical terms to stronger accepted official issuer implementation notices
(manifest `1b85bbeaca6dd59292348055e2e02ef652b4a800a003cbbe08b0f55e2305be40`).
Official PDF/date rechecks then established that 23 more primary cash notices
have both record and ex-dates after the 2025 dataset end (manifest
`0f6188b41f08160572c8542642282f9ab67e2fda626d59d3a0d360c6ca621a4d`).
Two notices with a 2025-12-31 record date remain open. Thus 326 of the original
625 P1 distribution-document requests remain to be classified. The cumulative
direct P1 cash matches are 13,079 documents and 14,025/16,320 facts are
established or excluded by scope, provisional for the full source gate; 2,295
facts / 2,279 unique documents remained at this step. A separate exact
official-source substitution pass then linked 512 URL-less P1 cash requests
to previously retained primary CNINFO issuer PDFs, requiring a unique
point-in-time identity, the same record/ex dates and gross amount parsed from
verified bytes (manifest
`b668a82fa6313ae92af873c0efd63750925f9e2b815204c8340c9b39060f3cb3`).
One of these uses an independent retained final issuer implementation notice
for 002859 where the accepted event cited a derivative bond-price adjustment
notice; exact issuer-PDF gross amount and record/ex dates were rechecked.
Another 917 of those URL-less requests have an exact gross amount re-parsed from
the official issuer PDF while one or both issuer-PDF dates are absent; the
accepted official exchange census supplies the exact record/ex dates, and no
conflicting issuer date was admitted (708 SSE, 209 SZSE).
Fifty more issuer PDFs contain the exact exchange-corroborated dates within a
multi-date set; the official exchange row uniquely disambiguates the target.
The previously approved ordinary-public-A differentiated-cash policy closed
96 more exact issuer notices: 52 with complete matching issuer dates and 44
with exchange-completed dates. The existing gross-cash parser, supplied with
exact exchange targets and then checked for exact equality, closed 13 further
multi-amount issuer notices. The resulting 1,076-document composite manifest
is `680fb5c58f672dcb24687247581bd482e0d215ee83d0093ac1d6393f496a9d31`.
Its source-checksummed rejected-candidate ledger retains 80 notices: 71
issuer/exchange date conflicts, three nonunique cash terms, four issuer-header
mismatches and two invalid page sequences. No new economic event, holder-class
policy or amount tolerance was created. The provisional P1 count is
15,612/16,320 established or explicitly out of scope, including 1,616 recorded
official substitutions at the cash stage. A separate fact-set replay against
the accepted official SSE ST authority closes 61 obsolete P1 ST-document
requests (59 former chain gaps and two unavailable legacy SSE PDF links),
with exact official event-corpus evidence for the latter two (manifest
`1b3cbf245ee1212499eec315a218cc1de182ee0a6514e3046653c7ad23d1ebc8`).
The current total is 15,674/16,320 established or out of scope, including
1,678 official substitutions; 646 facts / 630 unique documents remain. Three
additional mixed cash-plus-bonus notices
have their cash leg reconciled, but the bonus leg remains open and those source
requirements are not marked complete. The SSE composite substitution parser now
rejects a parseable issuer-notice amount that conflicts with the exchange table.
An independent checksum-bound replay corroborates the bonus ratio and both dates
of 60 retained issuer implementation PDFs against official SSE/SZSE tables
(manifest `dba59fcca0a03dddf19c6ab1744da3ab20affd356b917ccdc2a14ac19118426e`).
Three additional apparent date/ratio matches were withheld because their issuer
PDFs were published on or after the record date. This is a source-terms
cross-check, not complete corporate-action accounting or P1 closure; the
646-fact residual count is unchanged.
P0 and SSE/SZSE ST decisions are unaffected.

The independent SZSE resumption workflow also closed all 949 applicable day-91–180
official metadata windows through six bounded split-seven-day retries (18,129
records; zero unclosed; manifest
`d1c5cbc12b800334f948a0ae6c712d626287db8645833fb087cf8fc3d57ebc4f`).
The disjoint 895-document title-priority queue was fully acquired with zero
failures (894 PDFs, one supported JS attachment; source manifest
`5eb282502d6a4b90dd3b5e1014ea0847481fad8ff4c5a289a8a552ebc34f4abb`).
All 894 PDFs were text-indexed. Twelve documents yielded one exact official
resumption date, ten of which bound previously unresolved events; the combined
reverse-order authority replay now has SSE 16,393/0 unresolved and SZSE
22,077/1,922 unresolved, zero conflicts and 8,883 official supplements
(manifest `c88ce498b2c394023b2398282d944d087d508bea41d3a0f6cd71ebffbe021569`).
Authority remains PARTIAL. The next bounded official day-181–270 extension is
complete across all 659 applicable unresolved windows after the eight failed
first-pass windows were retried in 104 seven-day slices. The verified closure
has 12,523 official query records, zero unclosed windows and checksum/order PASS
(manifest `2a6b17bcf9d0b6f406d9d4fe35c05bcdd961f12671e2fe1276dfb929b318c887`).
A disjoint 360-document title-priority batch completed with zero retrieval
failures (359 PDFs, one supported JS attachment; source manifest
`4bc8aa040a19f3c4627884f51bba2e837e23b9471705e80c3920ab197aa04b5a`).
Exact-date review accepted only one new boundary; reverse-order full replay
leaves 1,921 SZSE events unresolved with zero conflicts (manifest
`f7cd758325d177e4c0a923938a90b193abaad18ef79cfab9bba2c8c16f67756a`).
Day-271–360 targeted official metadata then closed all 528 applicable windows
through bounded seven-day retries, with 9,280 records and checksum/order PASS
(manifest `fbbd59452682fd3480a0f6ac7ad44fd0250d2fdacfcd89b2bc87fab5aceeceac`).
A disjoint 217-document title-priority official batch completed with zero
retrieval failures (215 PDFs, two supported JS attachments; manifest
`74b11b9301c8d23ee214f390b19d14f0d185f9645d436d6f0d572a14bfbf2526`).
The exact-date review added zero boundaries; reverse-order full replay keeps
SZSE 1,921 unresolved, zero conflicts and PARTIAL authority (manifest
`81c8fab217945ffaf180560f4ad970790eff29382bd2a5cc9fb1ee57215fea33`).
Titles and query coverage are not accepted resumption facts.
Full Dataset created/audited/frozen = NO; studies NOT_RUN; PR #12 OPEN/unmerged.

## Authoritative 2026-09-16 R5 checkpoint — cash closed, SZSE resumptions active

Older sections below are historical checkpoints, not current blockers or counters.
The free official P0 master and SSE/SZSE ST authorities remain PASS; no paid
product was used. Full cash coverage v35 reconciles all 40,376 official ordinary-A
cash events to 40,376 accepted events with zero unresolved, zero accepted extras,
and checksum/input-order repeatability PASS (manifest
`679f003562068bbacbc7de884c522339d07313d77ed5c9df22c5e014f487b7fb`).
The P1 fact-level replay now directly matches 12,965 previously open CNINFO
implementation-document requests to the same official URLs in that accepted
cash ledger, with point-in-time identity (including symbol changes), issuer,
date and terms checks. This establishes 13,726/16,320 original P1 facts and
leaves 2,594 facts / 2,578 unique document requirements explicit; no new
official-source substitution was claimed. Immutable manifest:
`ff54f0e67bce7331f02d8d29fae926b7900f695a696d45bf4851c62ebf0f9eda`.
All 625 still-unestablished cash-queue documents have retained official bytes
with matching SHA-256 in the existing acquisition manifest
`ef5727f122b10b4ccba84d959cfaf178b951d0a7b64ea1316219dce4f185c28b`;
availability is not acceptance of their economic terms. Three redundant downloads
were identified against the older smoke cache and verified byte-identical.
Diagnostic-only PDF parsing of all 625 found 303 cash-only, 92 bonus-only, ten
mixed and 220 neither candidates, with 126 preferred-instrument markers. These
are not event classifications or substitutions; 40 amount/date matches were
specifically withheld because adjustment-after-distribution notices may omit
implementation terms. Triage manifest:
`6c6ce88078e760787e341669fa192e398e14e5094879ff02c95c0b026791f361`.

Full official suspension audit currently has SSE 16,393 target events / zero
unresolved and SZSE 22,077 target events / 1,932 unresolved official resumption
boundaries, zero conflicts, 8,873 official supplemental resumptions. Authority is
`PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES` (manifest
`a4bd5b71700d5182e583812f2e0a32a21e89d0f6a63610586c77ae38dde259ae`).
One newly verified example is 002665: the official CNINFO self-check result
announcement gives 2014-03-27 resumption after 2014-03-21 suspension. The original
14-day CNINFO metadata pass completed 2,686/2,696 windows; targeted retries closed
nine, and two nonoverlapping seven-day official queries closed the final unstable
pagination window. Its 34 announcement IDs are unique. An independent checksum-
verified closure audit proves all 2,696 original metadata query windows complete,
with 21,809 official records, zero unclosed windows and input-order PASS (manifest
`1e8cd5c9c7965620008466bf990cc2ca6bcf47f22fabadb9ea36796a6884f760`).
This proves query coverage only, not the missing resumption dates. Two disjoint prioritized
official PDF queues (2,011 direct suspension titles; 1,209 broader material titles)
were built from durable receipts. The first batch closed 315 exact new resumptions;
the second closed another 354. Its sole HTTP 502 was recovered in a separate
checksum-bound retry, but that document did not establish an exact resumption.
The day-15–44 official metadata extension closed all 2,022 applicable windows
after a page-size-30 correction to CNINFO pagination. It verified 17,062 official
query records, zero unclosed windows and checksum/input-order repeatability
(closure manifest `f489b7ce45a97cbfcec8f3f5980cd298cd3c41ee7edb90f8d5240970134747b1`).
Two disjoint title-priority PDF batches (1,389 + 127 documents) added 29 + 2
exactly bound resumptions. Their one transient HTTP 502 was separately recovered;
it was a continuing-suspension notice, not a resumption. The day-45–90 official
metadata extension closed all 1,278 applicable windows (15,071 records) after
three failed windows were retried in 21 bounded seven-day queries; query-closure
manifest `f5a4e5d43c0c2ee5a70cccf3722b461471ca3dc8cfff064a2115930f22152925`.
Separately, 87 hearing-result and five review-outcome official PDFs added 38 + 5
exact resumption boundaries, accepted by the combined reverse-order suspension
audit. A disjoint 1,313-document priority batch from the day-45–90 metadata
completed with zero download failures (1,311 PDFs, two supported JS attachments)
and added 20 more exact boundaries. Reconciliation manifest:
`b9b18a5fb44e2ef12d36d44c6c1483b433d2890bcc13c3e39f7a7289428a8f3a`.
Title routing and metadata coverage do not establish resumption facts; only exact
dated official text can do so. Many lower-priority document leads and longer
suspension intervals remain open.

Full dataset created/audited/frozen = NO; verified safe start remains unresolved.
Development, Validation and Official OOS are NOT_RUN. PR #12 remains open and
unmerged. Docker is deferred/nonblocking for current source work. No active
human-input blocker is established while official acquisition and reconciliation
continue.

## Current: full SSE/SZSE ST reconstruction passed; scoped P1 acquisition running

`OFFICIAL_PUBLIC_SOURCE_RECONSTRUCTION_V1` replaces the two assumed paid-export
file requirements with audited fact sets. SSE is 2,403/2,403 and SZSE is
3,028/3,028 reconstructed securities, with zero true unresolved P0 facts, zero
official-source conflicts, 269 delisted securities retained and deterministic
reverse-order replay. Both exchanges are
`PASS_PUBLIC_OFFICIAL_RECONSTRUCTION`; `SECURITY_MASTER_CORE_AUTHORITY=PASS`.
The 5,431 undated historical display-name boundaries remain explicit non-material
metadata gaps and do not supply ST state. No paid product was used. Evidence:
`../research/P0_PUBLIC_RECONSTRUCTION_REPORT_V1.md`.

Full SSE ST reconstruction is now `PASS_PUBLIC_OFFICIAL_RECONSTRUCTION`: all 2,403
P0 identities map, 1,242 official events replay with zero chain gaps, conflicts,
unmapped events or UNKNOWN intervals, and all 1,580 selected documents plus 6,724
title-routing leads have terminal classifications. Authority manifest:
`0b11bd3fcf4f62b530a551365dfa974b7db3cef63156d5a311e0f714ae0b012f`.

Full SZSE ST reconstruction is also `PASS_PUBLIC_OFFICIAL_RECONSTRUCTION`: all
3,028 P0 identities map to the official dated abbreviation history; all 836
prestart members have independent official corroboration; 1,276 risk transitions
replay across 7,876,813 security-sessions with zero gaps, lifecycle violations,
IPO conflicts, UNKNOWN states or future-event leakage. Authority manifest:
`8cb0c481cd8bd004dc689eee3370eb2fd9f592daec6ced717b40c45d1401c3a8`.

P1 fact-level scope reconciliation removes 757 official CNINFO notices for
non-ordinary-A instruments and directly resolves four SZSE yearbook facts. The
remaining counts are 15,559 fact requirements / 15,543 unique documents; 13,590
are in-scope public CNINFO PDFs and 1,953 are other targeted source gaps. The
correctly identity-bound, checksum-preserving public queue is running from durable
receipts. Acquired bytes are not accepted as event facts before parsing and
official exchange reconciliation. Docker remains deferred/non-blocking; full safe
start and the full dataset remain unestablished. No studies, freeze or PR merge.

## Current: official P0 export access is the sole acquisition blocker

The immutable V2 manifest revalidates at file SHA
`e9b7bb31868958c4bffd1dd9a31b26c33f0ad71c3b46c2e83adb7dd691b37559`
and canonical SHA
`96839c742cb12c9e0ea0c8301b990474554f64bfd2abf34579f8190b2e8017c7`.
P0 remains 0/2. SSEInfo historical/basic master delivery requires a business
application and agreement. CNINFO package 98 proves that historical stock/name/
listing-status data exist and previews normally, but data export requires login and
may charge. These are real user/organization access steps, not transport failures.

P1 is 16,320 event requirements / 16,304 unique documents. Five bulk collection
families cover the queue. Seven official CNINFO PDFs with prior HTTP-200 receipts
were found in existing archives, checksum-revalidated and placed in the exact V2
destinations; P1 net-new is 16,297. No generic intake exists, so no duplicate
framework was built before P0 arrives. Full unresolved material source documents
after all known local evidence are 16,303. Full safe start remains unestablished;
full dataset CREATED/AUDITED/FROZEN=NO. Docker is deferred/non-blocking for source
acquisition. No methodology approval, study, profitability inspection or PR merge.

## Current: differentiated cash closed; minimal official source input required

The approved `DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1` rule was replayed over all
664 cached differentiated final implementation documents. All 664 produce one
exact gross ordinary/public A-share cash term; no record is non-applicable,
ambiguous, missing-final or conflicting. Cash ledger v14 supports 24,306 events,
leaves 3,541 unresolved and retains 83 quarantines. The unresolved partition is
1,879 missing final sources, 844 exact-authority conflicts and 818 parser/policy
review groups. Prior accepted economic terms are unchanged. Canonical SHA:
`91e9ff1d6f064eb5ca0bc3d1dd97fb3b041b74e112fe95d7b78c6d4766da289a`.

The immutable `SOURCE_INPUT_REQUIREMENTS_V2_MINIMAL` manifest compresses 16,328
event-level requests into 16,312 unique official documents while preserving every
back-reference. Priorities are P0=2, P1=16,304, P2=5 and P3=1. Exactly 16,311 are
material; 16,310 currently require a user-provided official copy or restored
authorized access and one is already cached. The P3 metadata-only mirror is not a
readiness blocker. Canonical SHA:
`96839c742cb12c9e0ea0c8301b990474554f64bfd2abf34579f8190b2e8017c7`.

R5 is `BLOCKED_SOURCE_INPUT_V2_MINIMAL`, stop condition case 2. There is no pending
methodology approval. SSE still has 59 chain gaps; full security-master authority
and a verified safe start remain unestablished. Full dataset CREATED/AUDITED/FROZEN
= NO. Docker is tracked separately and does not change source evidence. No studies,
profitability inspection or PR merge.

A single safe Docker Desktop start was attempted without altering runtime files or
data. Windows processes started, but `docker-desktop` remained stopped and Ubuntu
had neither `/var/run/docker.sock` nor the Docker CLI. Recovery is still required;
no factory reset, runtime deletion or repeated retry was performed.

## Current: R5 final offline closure checkpoint

Cash ledger v12 supports 23,642 bounded events / 4,205 unresolved groups. The 83
historical quarantines remain excluded. The final unresolved partition is 1,879
missing implementation sources, 844 exact-authority conflicts and 1,482 parser or
policy-review groups. The shared strict issuer parser accepts additional official
OCR/header variants without accepting swapped identity fields, wrong documents or
title-only inference. No tolerance or differentiated-holder policy was introduced.
Combined canonical SHA
`cb9164039dfb21bc1a1ab38bb158bfb1f826b8063fbd9f193c26f2fa1668220c`.

The bounded integer retained-bonus ledger v8 supports 254 of 288 candidates and
leaves 34 explicit: 16 missing linked sources, 14 parser/exact-term conflicts and
four nonstandard-entitlement cases. Explicit `差异化分红送转:否` is no longer
misclassified as a differentiated event. Canonical SHA
`3815a14cc22c5a3a28291ce6ce6775aacfcdb6f8475be63ef3aaa2e2d31a7e6b`.

SSE parser v36: 787 provisional / 790 parser-or-restoration unresolved / three
metadata variants; 337 chains / 59 gaps / zero conflicts. All 771 main-parser
provisional events retain unchanged economic terms in checksum-bound current-parser
replay. Parser canonical SHA f8118dd2a6912067e40bf2d4158720c92efdeb036d5af2fdfdbe843d43cd3033;
chain canonical SHA 9006c5b9f99912ac45f5794c0329e66e2af11c875e4ce5a8370455ff1b2b977a;
integrity canonical SHA b9591e52257d076dffa4c0a60fa493e62f2a73ec4440d1a14d6b0e6aad27fd25.
Full authority remains PARTIAL.

All 69 cached merger implementation leads are closed deterministically: 34
supported-event evidence duplicates, 13 source-incomplete leads for three existing
chains, nine source-incomplete leads covering eight new ordinary-A parent events,
eight B-share-only parents and five unlisted absorbed targets without listed-parent
mutation. Closure canonical SHA
`d78f13e3a1cf817a9e8ea2aaa7773ea758e3bc0251674124f5d8039703dd2cfb`.
The supported identified merger count remains 15 and the full census remains
NOT_ESTABLISHED.

All independent safe offline work is exhausted. The detailed immutable
`SOURCE_INPUT_REQUIREMENTS_V1` manifest contains 16,328 source items and 664
methodology-decision items; canonical SHA
`e20492797f1249ecf2dc8dd5ef8b06f252199df2883425dca4c82a1045365edc`.
The only methodology class is
`ORDINARY_A_SHARE_HOLDER_CLASS_AND_PER_SHARE_CASH_POLICY_FOR_DIFFERENTIATED_DISTRIBUTIONS`.
R5 is `BLOCKED_HUMAN_METHODOLOGY_AND_SOURCE_INPUT`; safe start is not established
and the full dataset remains uncreated, unaudited and unfrozen.

The former PID 434 no longer exists after the WSL restart. Its denial manifest and
durable receipts remain preserved; no automatic resume, bypass or duplicate writer.
Docker Desktop now aborts before engine startup because the recreated
`sailor-ingest.sock` cannot be renamed to `.stale`; no reset or destructive recovery
was attempted. Local database-backed tests are pending, while 551 non-database tests
passed before the service-dependent failures. No full dataset, freeze or studies.
Older cash/ST counts below are superseded.

## Prior: offline cash implementation integrity closure

Full offline replay of existing 2010-2021 and partial-2022 source/date inputs now
supports 23,208 cash events: 376 new, all 22,832 revalidated identities preserved.
4,639 linked cash-term groups remain unresolved; no quarantined prior event is
readmitted. Canonical combined ledger SHA
0aea2a9f09b470f52169aebd420a34ddeb17ef96b23202d060d561f1fc075837.
Reverse input order, supported policy validation and event checksums PASS.
No source downloads or full-census acceptance were implied by this replay.

Prior 22,864 supported cash entries required integrity review after confirmed
proposal-versus-implementation selection defect in 000555 (2022). Revalidation
preserves 22,832 exact event identities; 32 quarantined, not admitted. Original
year-ledger counts below are historical and not current acceptance. New strict
implementation-section candidate ledgers are not replacements for the audited
revalidated subset. Current ledger canonical SHA
2c57b57f927a564d62e2dec206f33e2fe3d72194f2d77ef706a7a86d5addad02.
Remaining review includes genuine proposal/final discrepancies (000555 2022,
300002 2015, 300014 2017, 300034 2020, 002973 2022) and extraction/section gaps.
No rounding tolerance or synthetic ex-price cash accepted. 607 backend tests and
quality checks PASS. Frozen Pilot v2 unchanged; no strategy or dataset publication.
CNINFO PID 434 remains suspended for HTTP 403; source-access input requested.

## Current: CNINFO access denial; offline R5 continues

PID 434 is SIGSTOP-suspended, not terminated, following twenty consecutive HTTP
403 receipts. Do not automatically resume or route denied requests through another
host. Original receipts and in-memory worker preserved; no duplicate writer.
Runtime manifest e69890ebeaa22b46b5dc92ef73c9290d91e97e39293b83153b13bf2a6cc4652b.
21,029 original receipts; 2022 has 3,581/3,600 terminal receipts, including 2,704
PASS and 877 failures. Prior separate recovery adds 301 retained PDFs: partial
v3 contains 3,005 PASS / 576 unresolved. Final nineteen leads remain uncompleted.
Offline index/reconciliation continues; no year-completeness or full-readiness claim.

## Current: R5 600591 merger closure

Fifteen supported reviewed mergers / three reviewed unresolved chains; inventory V7
preserves fourteen accepted events and resolves 600591 with official global
fraction allocation evidence. Ratio 1.3, registration/exchange 2010-01-28,
ordinary new-share trading boundary 2010-02-02. Cash-option record 2010-01-11 is
not substituted for merger registration. Restricted shares separately identified.
607 backend tests / Ruff / format / mypy PASS. Original distribution downloader
still running; no full-census PASS, dataset publication, research study or merge.

## Prior: R5 cached transition and partial 2022 continuation

731 provisional SSE transitions / 846 parser unresolved / three metadata variants.
327 diagnostic chains / 83 gaps / zero conflicts; full authority remains PARTIAL.
Cached 600069 stock entry, 600130 and 600365 exits recovered by narrow header/verb
syntax support; bond notices and conflicting dates remain unaccepted. 606 backend
tests and quality checks PASS. CI 34818532899 for 17117c7 SUCCESS.
The 408-request recovery completed: 301 PDFs retained/indexed, 107 terminal DNS
failures preserved. Original worker PID 434 remains the only main-queue writer.
Partial 2022 snapshot v2: 2,318 retained PDFs, 1,698 supported cash events /
1,657 unresolved groups; not a complete year and not additive to prior snapshots.
R5 RUNNING_BATCH_CLOSURE; full dataset/studies/freeze/merge unchanged.

## Current: R5 merger and live-source continuation

Fourteen supported reviewed mergers; four reviewed unresolved chains; full census
unknown. New verified ordinary-holder boundaries: 600837/601211 2025-03-17,
601989/600150 2025-09-16, 000780/001289 2022-01-24. Controller/private-placement
lockups are not applied to the ordinary unrestricted holder class or ignored for
their actual holders. 002013 cross-market account conversion remains unresolved.
605 backend tests and quality checks PASS. PR12 OPEN; 94818c2 CI SUCCESS.
Original distribution worker continues. A separate recovery owns only 408 terminal
2022 DNS-failed requests, not the original worker's remaining queue. Partial 2022
snapshot indexed 2,017 successful PDFs; year not complete. Studies remain locked.

## Current: R5 bounded merger continuation

Eleven supported reviewed mergers; three further reviewed chains unresolved
(000578 additional pre-merger share transfer, 600591 referenced fraction rules,
000522 account-registration-dependent tradability). Full market count unknown.
600317 and 600723 source-byte, master and raw-boundary checks pass under the
existing first-post-event trading boundary, not an inferred registry timestamp.
602 backend tests and quality checks PASS. Existing event identities preserved;
review adapter passes through reciprocal ratios and activation evidence.
R5 remains RUNNING_BATCH_CLOSURE. No full publication, freeze, study or merge.

## Current: R5 bounded retained-bonus reconciliation

169 supported integer-ratio retained-bonus events under the approved
BASIS_CONSERVED_RETAINED_BONUS policy. 119 of 288 candidates unresolved;
7,119 oracle rows outside this bounded subset remain deferred, not excluded.
Ratios 1/2; integer holdings and next-session scheduled listing only. No assertion
of actual tradability or full corporate-action completeness. Reverse input-file
order reproduces the manifest. Cash/aggregate basis unchanged; no generated orders.
598 backend tests and quality checks PASS. Historical fee authority remains
PARTIAL: retained 2012 bulletin has a printed denominator discrepancy and does
not establish the full investor fee/minimum. Full dataset remains uncreated;
original distribution worker continues, all studies/freeze/merge remain locked.

## Current: R5 relisting evidence continuation

705 provisional SSE event records; 872 parser cases and three metadata variants
remain unresolved. Six further document records resolved using retained evidence,
including two coordinate-deduplicated PDFs. 325 diagnostic chains / 92 gaps,
zero same-day conflicts. Full authority remains PARTIAL, not daily-state PASS.
600057 header mismatch visually confirmed as printed in the PDF; original SSE
mirror denied access and is not retried. No identity guard waived.
596 backend tests PASS. Continue independent R5; no full publication or studies.

## Current: R5 2021 cash and restored SSE metadata

2021: 3,205 PDFs retained/indexed after 18 separate DNS recoveries; originals
preserved. 2,420 supported cash events / 688 unresolved groups; twelve-year
bounded cash total 20,683 / 3,809. Unchanged approved cash parser/policy.
SSE DNS recovered; all 20 restoration documents now exactly corroborated.
Ten provisional relisting transitions added, requiring dated restoration plus
first-day NST and later ST names. 699 provisional transitions overall; 878
parser cases and three metadata variants remain. 324 diagnostic chains / 95
gaps, zero same-day conflicts; full ST authority still PARTIAL.
596 backend tests and quality checks PASS. e4e5bbf CI 34812475961 SUCCESS.
Original distribution worker continues later years, no duplicate writer.
Full dataset not created/audited/frozen; all studies locked; PR12 open/unmerged.

## Current: R5 restoration coverage recovery

Retained annual fact books identify 17 restoration rows absent from the current
keyword-selected ledger. Targeted CNINFO queries recovered 38 metadata leads;
20 selected PDFs are retained and indexed. Separate SSE corroboration completed:
three cached exact matches, 16 issuer/day DNS failures preserved, no promotion.
The provisional chain diagnostic now covers 322 chains with 102 gaps and zero
same-day conflicts; this is not complete daily-state acceptance. 594 backend
tests and Ruff/format/mypy PASS. CI 34810743949 succeeded for 76d4851.
Original distribution worker remains active without duplication. Continue R5;
full dataset not created/audited/frozen, all strategy studies remain locked.

## Current: R5 independent source-oracle and bounded parser continuation

689 provisional SSE transitions / 868 parser cases / three metadata variants;
full authority remains PARTIAL. Three document-hash-bound title reviews preserve
ordinary issuer/date/name checks; no general fuzzy title rule. 593 backend tests
and quality checks PASS. Prior CI 34809275007 succeeded for 220d75c.
Bonus oracle: 7,407 source rows, 7,369 lifecycle-mapped candidates / 38 B-share
rows out of scope. Scheduled listing dates are not actual tradability evidence;
600817 is the existing accepted pass-through, not a new retained-bonus event.
Tencent long-range 640-row query truncates; 5,000 returns no daily history in
two controls. Retain year-bounded route; no bulk ingestion/source promotion.
Existing distribution worker continues. Full dataset remains not created/audited/
frozen, no studies or merge. See R5_BONUS_SOURCE_ORACLE_V1.md and ST report.

## Current: R5 2017 cash and deterministic bonus accounting

Completed 2017 source attempts: 2,564 PDFs, zero retrieval failures. Existing
cash parser adds 2,241 supported / 233 unresolved; eleven-year bounded total
18,263 / 3,121. Worker continues 2021 onward without duplication.
SSE metadata normalization preserves all 1,555 matches and adds two; 677
provisional transitions, 880 parser cases and three reviewed metadata differences
remain unaccepted. Bonus arithmetic now uses existing portfolio decimal context
and explicitly conserves aggregate basis; no fractional allocation policy chosen.
592 backend tests/quality PASS. Full dataset remains not created/audited/frozen.

## Current: R5 cached SSE evidence reconciliation continues

All selected 1,560 PDFs indexed; 1,555 exact metadata matches and five explicit
normalization/identity review gaps. Pagination recovery preserves original failed
receipts and validates grouped totals. Coordinate-based alternate extraction adds
16 provisional transitions; prior 644 unchanged, total 660. Another 895 parser
cases remain unresolved, not accepted NORMAL states. Nine retained fact books
provide dated name evidence, not contemporaneous publication timestamps.
590 backend tests and quality checks PASS. Distribution worker remains alive;
no duplicate writer. Full dataset CREATED/AUDITED/FROZEN=NO; no studies or merge.

## Current: R5 cash reconciliation extended through six retained years

2011–2016 adds 8,134 supported cash events using unchanged parsers/accounting.
Ten processed years now total 16,022 supported / 2,888 unresolved groups.
All 35 transient failures recovered; 128 JavaScript summaries remain non-PDF
source leads. Full census remains PARTIAL. Factor baseline checks cover 5,436
code intervals, not full adjustment authority. ST and distribution queues continue.

## Current: R5 missing-period ST metadata recovered

All 346 keyword/month queries now complete as queries only. One April 2022 HTTP
502 was recovered in a separate immutable attempt; the original failure remains.
6,724 unique leads are retained, including 2,911 SSE-code leads. A disjoint queue
of 1,560 transition-document leads reuses retained PDFs; 1,348 SSE warning or
application leads and three unexpected attachments remain explicit review work.
No event acceptance or full ST completeness is implied. Distribution worker
continues without duplication. CI 34804569207 passed for cc4b7b9.
External routing manifest: full-sse-st-v1/transition-routing-v1.json,
SHA 5abebf6499c32d740eed394fae1beaa1cfbeccfa84206993a380b42088e74059.
Full dataset remains CREATED/AUDITED/FROZEN=NO; no studies or merge.

## Current: R5 SSE starting-state evidence and missing-period metadata

860 starting SSE members: 778 NORMAL / 51 ST / 31 STAR_ST, zero missing/conflicting
anchor names. Retained 2009 company table and 857 trading-table names agree;
three paused members remain in the company table. This is not full ST coverage.
A separate two-thread metadata worker extends periods outside the accepted Pilot
window; original remaining-years PDF worker continues without duplicate writers.
Cash v2 extends only unresolved rows: 7,888 supported / 1,341 pending in four years;
all prior 7,702 event checksums preserved. Backend 586 and quality checks PASS.

## Current: R5 cash-dividend batch supported under existing policy

7,702 reconciled cash events across 2010/2018/2019/2020 have exact official gross
terms, exchange-date corroboration, stable lifecycle/instrument checks and
existing immutable event serialization. 1,527 groups remain unresolved in these
four years; full census remains PARTIAL. Existing ex-date cash accounting reused,
not a new tax/payment-date model. 584 backend / 78 frontend tests and quality PASS.
See ../research/R5_CASH_DIVIDEND_BATCH_V1.md. Independent R5 work continues.

## Current: R5 SZSE dated-state replay verified

7,876,813 security-sessions replayed; UNKNOWN=0 under the existing accepted Pilot
IPO initialization. Prestart corroboration, reversed input and future-event
truncation agree. Overall full ST acceptance remains PARTIAL, not a suspension
or full independent historical-name acceptance. Independent R5 queues continue.

## Current: R5 SZSE prestart risk-state corroboration

All 836 starting members independently corroborated: 820 yearbook trading-table
names and 16 paused issuers with 32 retained 2009 notice headers. Dated source
has 1,276 target risk transitions, zero detected risk-chain/lifecycle conflicts.
Full ST remains PARTIAL: IPO initialization and daily replay are not accepted.
See ../research/R5_SZSE_PRESTART_CORROBORATION_V1.md. R5 queues continue.

## Current: R5 2010 exchange-row notice coverage reconciled

1,056 date-linked notices, three existing supported rights entries, one separately
queued structural reform: all 1,060 exchange date groups have located evidence.
This is not dividend-term/accounting acceptance. 600728 requires holder-specific
retained-bonus and boundary reconciliation; no ordinary dividend was fabricated.
See ../research/R5_DISTRIBUTION_2010_DATE_CLOSURE_V1.md. Independent R5 work continues.

## Current: R5 candidate instrument classification closed

5,432 candidates: 5,431 ordinary A shares and one separately excluded CDR.
Reused 5,181 accepted facts, including the frozen v2 listing correction; only
251 missing candidates extended. Zero unresolved classifications. This does not
certify full master/ST/event coverage. See ../research/R5_INSTRUMENT_EXTENSION_V1.md.
R5 continues; full dataset CREATED/AUDITED/FROZEN=NO, no studies or merge.

## Current: R5 2009 membership cross-check reconciled

860 SSE and 836 SZSE active master entries covered; 18 SZSE annual-report identity
supplements verified. Yearbook temporal extras and B-only aliases stay explicit.
This is membership-only: full master/ST/tradability acceptance remains partial.
576 backend tests PASS. See ../research/R5_MASTER_BASELINE_CROSSCHECK_V1.md.
R5 continues; safe start NOT_ESTABLISHED, full dataset CREATED/AUDITED/FROZEN=NO.

## Current: R5 prior merger chronology gaps closed

Nine reviewed candidates now supported; zero unresolved within that bounded set.
Full-market merger census remains NOT_ESTABLISHED. 600553/600991/601299 use the
approved suspension-boundary policy; June 8 is the 601299 daily boundary, not
May 26 H-share conversion or June 4 new-share listing. No backdated disclosures.
See ../research/R5_MERGER_SUSPENSION_BATCH_V1.md. Acquisition continues; no studies.

## Current: R5 four retained merger implementations closed

Reviewed merger inventory: nine candidates, six supported, three unresolved;
full-market completeness remains NOT_ESTABLISHED. Four additions use existing
approved accounting, not new methodology. Two unknown cash-offer metadata fields
remain null and cannot authorize participation. Backend 571 / frontend 78 PASS.
See ../research/R5_MERGER_BATCH_CLOSURE_V1.md. Two distribution workers continue.
R5 RUNNING_BATCH_CLOSURE; full dataset CREATED/AUDITED/FROZEN=NO; no studies/merge.

## Current: 2026-09-14 durable worker recovery PASS

No old worker was alive. Queue identity, URL disjointness, receipts and retained
PDF hashes verified before resuming two disjoint batches. No duplicate writer.
At recovery: 2018–2020 processed 1,977/8,590; remaining-years 584/34,800.
Existing failures are retained, not silently retried or promoted.
44,504 metadata leads recovered across 2010–2025; 2022 unstable annual totals
remain documented alongside complete independent date partitions. No event promotion.
Runtime record: .research/reports/r5-worker-recovery-20260914.json.
R5 RUNNING_BATCH_CLOSURE. Full dataset CREATED/AUDITED/FROZEN=NO; no studies/merge.

## Current: R5 retained distribution notice recovery

2010: 1,113 PDFs indexed, one explicit HTTP 502 failure. 2018–2020: 8,590
document leads downloading with source/checkpoint reuse. Missing-date-range
recovery reuses retained pages; 2011/2012 reconcile to original annual totals.
See ../research/R5_DISTRIBUTION_NOTICE_RECOVERY_V1.md and external manifests.
R5 RUNNING_BATCH_CLOSURE; no new gate, dataset creation/audit/freeze or studies.

## Current: R5 exchange distribution census; batch closure continues

All 192 official SZSE monthly tables retrieved: 23,682 source rows; all 74
rights candidates match the existing official event ledger, no source-only or
ledger-only entries. SSE eight cash collisions resolved to exact issuer terms.
These are source/census checks, not full cash precision or dataset acceptance.
CNINFO API probe is supplementary only: average cash fields and missing delisted
history cannot replace official issuer evidence. 561 backend tests and quality
checks PASS. See ../research/R5_EXCHANGE_DISTRIBUTION_CENSUS_V1.md.
R5 RUNNING_BATCH_CLOSURE; no new human gate, no dataset creation/audit/freeze.
Remaining independent source and accounting queues continue; no studies/merge.

## Prior milestone: R5 full-range source extension

Calendar: 3,886 target sessions verified. Official CSI300 close history aligns
exactly, matches all 382 accepted Pilot closes and passes deterministic Parquet
replay. Accepted Pilot and raw stock authorities are unchanged.
SSE distribution source tables collected: 17,920 dividend rows / 2,500 bonus
rows including B-only records; source rows are NOT accepted accounting events.
Exact rational merger flooring implemented without changing accepted event IDs.
558 backend / 78 frontend tests and quality checks PASS.
See ../research/R5_FULL_RANGE_SOURCE_EXTENSION_V1.md.
R5 remains RUNNING_BATCH_CLOSURE, no human gate or new methodology blocker.
Full dataset CREATED/AUDITED/FROZEN=NO; remaining source queues continue.

## Prior milestone: R5 rights batch reconciled

153 identified rights events / 142 securities now reconcile to official direct-subscription
notices; material unresolved in this identified queue = 0, metadata-only incomplete = 149.
Full exchange census remains PARTIAL. Source documents and code-transition candidates
are not full-dataset acceptance. 554 backend tests and quality checks PASS.
See ../research/R5_BATCH_SOURCE_CLOSURE_V1.md and
.research/reports/r5-batch-source-closure-v1.json. R5 remains RUNNING_BATCH_CLOSURE;
no human gate, no full dataset creation/audit/freeze, no studies, merge or release.

## Prior milestone: consolidation decision resolved

The approved 15-class policy catalog is frozen (not the dataset):
`CORPORATE_ACTION_POLICY_MATRIX_V1`, file SHA-256
`3784d6817fb7ab30081e57d9693bc1ac7adbfbaccebe200e2903e7021d8a0352`.
600381 consolidation June 25 and separate surrender June 30, 2014 have source-byte,
Decimal accounting, replay and persistence checks. Source receipt:
`dcfa8e2a408629a0be0b8ab9b101ab08206642eaaae621cc5412b94f96a93383`.
Its prior human methodology blocker is RESOLVED. R5 remains RUNNING_BATCH_CLOSURE;
no new human approval requested. Rights, merger/restructuring, master and remaining
full-period authority queues remain independent. Document leads are not accepted events.
Full Dataset CREATED/AUDITED/FROZEN=NO; safe start NOT_ESTABLISHED. No studies,
profitability inspection, merge or release. Accepted Pilot v2 remains unchanged.
The retained merger/capital-adjustment source worker checkpoints under external
`full-merger-v1/batch-v1`; unavailable sources cannot silently pass.

## Historical checkpoint (superseded): 600817 PASS; former 600381 gate

600817 approved net pass-through accounting/source/replay/persistence PASS; old blocker RESOLVED.
R5 reviewed21 further retained-queue plan documents and two600381 implementation/reference PDFs.
600381 ordinary100 ->16 share consolidation occurred2014-06-25, distinct from later12% surrender.
Historical aggregate basis treatment of the consolidation is not covered by accepted policies.
SINGLE_SMALLEST_BLOCKER=RESTRUCTURING_SHARE_CONSOLIDATION_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600381.
HUMAN_APPROVAL_GATE=R5_RESTRUCTURING_SHARE_CONSOLIDATION_ACCOUNTING;
HUMAN_APPROVAL_REQUIRED=YES; HUMAN_SOURCE_INPUT_REQUIRED=NO.
544 backend/78 frontend tests; Ruff/format/mypy and migration checks PASS.
Full dataset CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No studies, profitability review, PR12 merge or release. No background worker.
Report: ../research/PASS_THROUGH_R5_CHECKPOINT.md. Resume preserved queues after decision.



## Current:600817 approved net pass-through PASS; R5 RUNNING

Human decision b42ec74db5f29f3a1434b96bdc04f9833dcb572a20198ee5b6fe69e3fe7293d6
approves CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1 /
NET_PASS_THROUGH_NO_BASIS_ALLOCATION. Five official PDF receipts verify25% bonus,
registration2012-07-31, transfer2012-08-01, unchanged originals and suspension.
Generic metadata-only accounting, persistence and raw-price separation checks PASS.
Old600817 methodology blocker RESOLVED; HUMAN_APPROVAL_REQUIRED=NO.
R5 resumes retained census/source queues; no prior acceptance is repeated or changed.
Full dataset CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No Development/Validation/OOS, profitability inspection, PR merge or release.
Evidence: ../research/RESTRUCTURING_PASS_THROUGH_V1.md.



## Current:600462 PASS; R5 new600817 pass-through methodology gate

600462 boundary and ceiling convention accepted/tested; original registry source
blocker RESOLVED. Historical timestamp/fraction facts remain NOT_PUBLICLY_EVIDENCED.
R5 resumed2010 merger leads and the preserved capital-adjustment queue.
600817 official notices establish temporary25% bonus credit then transfer to the
administrator, while original shares remain. Gross bonus/surrender versus net
issuer-level pass-through would allocate basis differently. Neither selected.
SINGLE_SMALLEST_BLOCKER=RESTRUCTURING_BONUS_PASS_THROUGH_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600817.
HUMAN_APPROVAL_GATE=R5_RESTRUCTURING_BONUS_PASS_THROUGH_ACCOUNTING;
HUMAN_APPROVAL_REQUIRED=YES; HUMAN_SOURCE_INPUT_REQUIRED=NO.
528 backend tests/Ruff/format/mypy PASS. Full dataset CREATED/AUDITED/FROZEN=NO;
safe start/full coverage NOT_ESTABLISHED. No studies, profitability review or merge.
Report: ../research/600462_CONVENTION_R5_CHECKPOINT.md.
No background worker. Resume preserved queues after this new methodology decision.

## Current:600462 approved boundary/fraction convention PASS; R5 RUNNING

Human decision6f14546633e87d4a3dfec3564d92e03de07b6778b0636e4f86193994772f03b1
approves FIRST_POST_EVENT_TRADING_BOUNDARY_V1 and CEIL_SURRENDER_FLOOR_RETAINED_V1.
Historical registry date and official fraction rule remain NOT_PUBLICLY_EVIDENCED.
Research application before2012-11-19 resumed tradable Bar; no future-price input
to quantity/basis. Generic ceiling and zero-retained accounting/replay/persistence PASS.
600462 source blocker RESOLVED_BY_APPROVED_CONVENTION, not by fabricated historical facts.
18 source PDF receipts verified; flat-start2010 quantity lattice remains100*n before
surrender, so reachable fractional/positive-zero-retained cases0, economic bound0.
Edge stress Q1/6/101 separately tests ceiling; not historical strategy holdings.
528 backend tests/Ruff/format/mypy PASS. No schema migration needed for JSON audit extension.
HUMAN_APPROVAL_REQUIRED=NO; HUMAN_SOURCE_INPUT_REQUIRED=NO; STATUS=RUNNING.
Resume preserved R5 queues. Full dataset CREATED/AUDITED/FROZEN=NO; coverage/safe start
not established. No studies/profitability inspection/merge/release.
Review/lineage: ../research/600462_APPROVED_CONVENTION_REVIEW_V1.json.
Evidence manifest a4d49ac37c9bff57485be7087122707ad0e03b788cfc39d776e509fdb00fd83a.

## Latest registry recovery: trading boundary and aggregate totals verified

Official first post-event trading boundary2012-11-19 established; exact registry
book-entry/daily valuation mutation date remains unverified. Actual aggregate
share-capital reconciliation PASS/difference0; plan-to-actual gap28163 and
non-exhaustive exception arithmetic residual116 remain distinct.
Fractional rule NOT_EVIDENCED; generic Portfolio odd quantities reachable,
actual600462 historical reachability NOT_ESTABLISHED (round-lot-only subset safe).
16 official PDF receipts/checksums reverified;3 targeted PDFs added, no restart.
Report: ../research/600462_REGISTRY_RECOVERY.md; manifest
231c167a765e79673cdb5517ec95e4b7a27eecdc53c4451d7014fe63ae3e0aa2.
Original source blocker remains. No new methodology approval; human source input YES.
Approved accounting and all prior acceptance decisions unchanged; no formal studies/freeze/merge.

## Current: partial-surrender policy implemented;600462 source evidence unresolved

CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1 APPROVED.
Generic exact-whole-quantity accounting/replay/persistence PASS; historical600462
admission PARTIAL. Ordinary nonexempt20% surrender and separate30% issuer issuance
verified; no direct holder compensation. Do not apply the issuance fractional rule.
Registry effective date and surrender-specific allocation remain unverified after
targeted plan/progress/court/annual-report review. No historical date is invented.
SINGLE_SMALLEST_BLOCKER=PARTIAL_SURRENDER_REGISTRY_EXECUTION_EVIDENCE_UNVERIFIED:CN-A:SSE:600462.
This is source recovery, NOT a repeated basis approval or established new fractional mechanism.
HUMAN_APPROVAL_GATE=NONE; HUMAN_APPROVAL_REQUIRED=NO; HUMAN_SOURCE_INPUT_REQUIRED=YES.
518 backend/78 frontend tests PASS; source replay/Ruff/mypy/schema checks PASS.
Prior Pilotv2/R4v2, rights/demerger/merger/source acceptances remain unchanged.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR12 merge or release.
Report: ../research/PARTIAL_SURRENDER_CHECKPOINT.md.
Resume preserved R5 source queues after registry evidence recovery; do not restart.
Next dataset gate remains GATE_FULL_RESEARCH_DATASET_FREEZE, not reached.

## Historical checkpoints below (superseded)

## Current: 600005 zero-whole PASS; R5 partial-surrender methodology STOP

Approved WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1 implemented in shared
Portfolio accounting. Official600005 ->600019 ratio0.56, conversion2017-02-17,
new-share activation2017-02-27 reverified. Zero parent basis is written off only
as corporate-action PnL; cash/trading PnL/orders/fills remain unchanged.
MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17 RESOLVED.
504 backend/78 frontend tests, source replay, lint/format/types and schema checks PASS.
R5 resumed:95 pages/2849 merger announcements,69 implementation-document leads;
five prior candidates updated,2 supported/3 source-unresolved. Full census unknown.
Broader review:6 pages/175 capital-adjustment notices; official600462 confirms20%
ordinary-holder compulsory surrender, with30% issuance diverted to bankruptcy account.
This is not a merger or zero-successor case; partial-surrender historical-basis treatment
requires a new explicit policy. No loss/full-basis retention, bonus credit or exclusion chosen.
SINGLE_SMALLEST_BLOCKER=MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600462.
HUMAN_APPROVAL_GATE=R5_MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY;
HUMAN_APPROVAL_REQUIRED=YES. Exact surrender transfer chronology remains separate source work.
Full dataset CREATED/AUDITED/FROZEN=NO; verified safe start/coverage NOT_ESTABLISHED.
Preserved Pilotv2, R4v2, rights/demerger/prior source decisions remain unchanged.
No Development/Validation/OOS, full freeze, PR12 merge or release.
Report: ../research/ZERO_WHOLE_SHARE_CHECKPOINT.md;
machine report: .research/reports/r5-zero-whole-policy-v1.json.
After human decision resume preserved R5 queues, not acquisition from zero.
No background worker remains. Full freeze gate has not been reached.

## Historical checkpoints below (superseded)

## Current: 000024 merger PASS; R5 zero-whole-share basis decision STOP

CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1 implemented; 000024 evidence/accounting/replay PASS.
Prior MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30 RESOLVED.
Official global allocation remains distinct from approved deterministic floor/no-cash accounting.
Full parent basis transfers to whole successor shares; remainder and CEIL bounds are audit-only.
R5 resumed the historical inventory; five candidates, two official reviews, one supported,
four unresolved including three retained source leads. Full census/materiality NOT_ESTABLISHED.
Official 600005 ratio0.56 exposes hypothetical Q=1 ->0 whole shares: positive B/0 is undefined.
No actual strategy holding is claimed; no loss, residual asset, cash, extra share or exclusion chosen.
SINGLE_SMALLEST_BLOCKER=MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17.
HUMAN_APPROVAL_GATE=R5_MERGER_ZERO_WHOLE_SHARE_BASIS_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
494 backend/78 frontend tests; source replay, lint/format/types and additive schema checks PASS.
Rights V2/600003/prior authorities/frozen Pilotv2/R4v2 unchanged. R4 actual fills remain0.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/verified coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR12 merge, release or background worker.
Report: ../research/MERGER_POLICY_V1_CHECKPOINT.md;
machine report: .research/reports/r5-merger-policy-v1.json.
Next after zero-whole basis decision: resume preserved R5 sources/materialization/audit;
stop at GATE_FULL_RESEARCH_DATASET_FREEZE without freezing.

## Historical checkpoints below (superseded)

## Current:600003 demerger PASS; R5 merger fractional-allocation decision STOP

CN_A_MANDATORY_DEMERGER_POLICY_V1 implemented;600003 accounting/replay/source audit PASS.
Prior DEMERGER_ACCOUNTING_POLICY_UNAPPROVED:CN-A:SSE:600003:2010-02-26 RESOLVED.
One identified demerger supported; full event census NOT_ESTABLISHED.
R5 resumed existing lifecycle/inventory evidence and verified000024 ->001979 merger.
Official1:1.6008 conversion requires all-holder remainder ranking with random ties.
SINGLE_SMALLEST_BLOCKER=MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30.
HUMAN_APPROVAL_GATE=R5_MERGER_FRACTIONAL_SHARE_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
No arbitrary rounding, cash-in-lieu, fractional trading or exclusion was chosen.
484 backend/78 frontend tests, Ruff/format/mypy, schema and source replay checks PASS.
Rights V2 queue/accepted authorities/frozen Pilotv2 unchanged; R4v2 remains PASS with0 fills.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/verified coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR merge, release or background worker.
Report: ../research/DEMERGER_POLICY_V1_CHECKPOINT.md;
machine report: .research/reports/r5-demerger-policy-v1.json.
Next after decision: resume preserved R5 source queues, materialize/audit, stop at full freeze gate.

## Historical checkpoints below (superseded)


## Current: rights entitlement V2 PASS; material demerger methodology STOP

Human V2 separates event structure, tradability evidence and portfolio policy.
CN_A_RIGHTS_ISSUE_POLICY_V1 / NO_SUBSCRIPTION_NO_MONETIZATION_V1 implemented.
000960/2010-01-27 verified STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE;
tradability NOT_EVIDENCED; prior exact rights blocker RESOLVED.
148 events reprocessed:4 STANDARD_COMPLETE,0 STANDARD_PARTIAL_BUT_ACCOUNTING_SAFE,
0 EXPLICIT_UNSUPPORTED_VARIANT,144 EVENT_IDENTITY_UNRESOLVED source-work queue.
20 independently identified occurrences match provider records; full census PARTIAL,
not zero unexplained differences. No source backlog is re-labelled a tradability decision.
R5 safety review confirms600003/2010-02-26 one-parent/two-successor demerger.
SINGLE_SMALLEST_BLOCKER=DEMERGER_ACCOUNTING_POLICY_UNAPPROVED:CN-A:SSE:600003:2010-02-26.
Required methodology: successor historical cost allocation and intervening valuation.
HUMAN_APPROVAL_GATE=R5_DEMERGER_ACCOUNTING_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
472 backend/78 frontend tests PASS; replay/Ruff/mypy PASS.
R4v2 PASS with0 actual fills; no rerun, strategy changes or profitability review.
Frozen Pilotv2/accepted authorities unchanged; full2010-2025 CREATED/AUDITED/FROZEN=NO.
Safe start NOT_ESTABLISHED; no formal studies, merge or release. No worker running.
Report: ../research/RIGHTS_ENTITLEMENT_V2_CHECKPOINT.md;
machine report: .research/reports/r5-rights-entitlement-v2.json.

## Historical checkpoints below (superseded)


## Current: rights policy engineering PASS; R5 exact event-evidence STOP

CN_A_RIGHTS_ISSUE_POLICY_V1 / DECLINE_SUBSCRIPTION approved and implemented.
Event model/accounting/reproducibility PASS; old participation-methodology blocker RESOLVED.
Inventory148 events/137 securities:2 supported,146 unresolved,0 positively confirmed
non-standard variants. No rights-based exclusion or full authority promotion.
User section8 STOP: RIGHTS_EVENT_UNSUPPORTED_VARIANT:CN-A:SZSE:000960:2010-01-27.
Its entitlement non-transferability remains unverified; this is not a finding of tradability.
HUMAN_APPROVAL_GATE=R5_RIGHTS_EVENT_VARIANT_REVIEW; HUMAN_APPROVAL_REQUIRED=YES.
R4_V2_STATUS=PASS, R4_REAL_DATA_FILL_COUNT=0; no R4 rerun or frozen Pilot modification.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; verified safe start NOT_ESTABLISHED.
No formal studies, strategy changes, profitability review, PR merge or release.
Current report: ../research/RIGHTS_ISSUE_POLICY_CHECKPOINT.md;
machine state: .research/reports/r5-rights-policy.json. No background worker remains.

## Historical checkpoints below (superseded)

## Current: Pilot v2 frozen; R4 v2 PASS; R5 methodology decision STOP

R1 COMPLETE; R2 v1 SUPERSEDED; R3 v1 INVALIDATED; R2/R3 v2 COMPLETE.
GATE_A_REVISED_DATASET_FREEZE APPROVED and executed, v2 current accepted/frozen.
R4 v2 PASS including fresh replay/no-look-ahead, persistence/API/actual UI.
R5 resumed source preflight, then STOP: FULL_HISTORY_RIGHTS_ISSUE_TREATMENT_REQUIRES_HUMAN_DECISION.
Official6000362010 paid rights issue is absent from the dividend-only response;
existing accounting policy rejects rights. No automatic subscription, forfeiture,
cash injection or exclusion decision. HUMAN_APPROVAL_REQUIRED=YES for this policy,
not full dataset freeze. Full2010-2025 dataset CREATED/AUDITED/FROZEN=NO;
verified research-safe start NOT_ESTABLISHED. No formal studies/merge/release.
Current BaoStock endpoint recovered;124 exited-security factor baselines verified.
Other full-history authorities remain unfinished, not inferred from Pilot PASS.
See `../research/PILOT_V2_FREEZE_R4_R5_CHECKPOINT.md` and
`.research/reports/r5-source-preflight.json`. All probes complete; no worker running.

## Historical checkpoints below (superseded)

## Current: revised Pilot v2 frozen; R4 v2 RUNNING

Latest human approval supersedes prior revised-freeze STOP. All eight approved
component hashes, partition bytes, counts,25 R3 checks and preserved v1 verify.
V2 freeze complete, canonical receipt f9add5f2...635bcb3. Unchanged R4 v2 running;
R1 COMPLETE; R2/R3 v2 COMPLETE; R2 v1 SUPERSEDED, R3 v1 INVALIDATED. On PASS, R5 full-history
materialization/audit. Next gate GATE_FULL_RESEARCH_DATASET_FREEZE, unfrozen.
No formal studies, PR merge or release. Previous acceptance decisions unchanged.

## Historical checkpoints below (superseded)

## Current: revised Pilot v2 audited; STOP at revised freeze gate

R3_REVISED_PILOT_AUDIT=PASS (25 checks); v2 CREATED=YES, AUDITED=YES,
FROZEN=NO, readiness READY. HUMAN_APPROVAL_REQUIRED=YES at
GATE_A_REVISED_DATASET_FREEZE. No freeze, R4 v2, R5 or formal study is authorized.
V1 remains frozen/superseded/acceptance INVALIDATED; bytes and visible warning preserved.
V2:5180 ordinary A shares,1922643 bars,382 sessions;15528 partitions reused,
12 rebuilt,9 new. Added688086,688287,688555;600190 listing date corrected;
no removed Pilot members or unexplained master differences. Independent exchange
year-end baselines reconcile with zero missing/extra A-share codes.
Manifest187b8c31d333fa33c5784d31bca60949e44a0c3a0c37a021235e49115bf92600.
See `../research/REVISED_PILOT_DATASET_REVIEW.md` and
`.research/reports/revised-pilot-v2.json` for exact lists, lineage and hashes.

## Historical checkpoints below (superseded)

## Current: revised Pilot rebuild approved, in progress

Human approval authorizes v2 rebuild and fresh R3 only. V1 remains frozen,
superseded and research-acceptance INVALIDATED (SECURITY_MASTER_COMPLETENESS_DEFECT);
its original files, manifest, freeze, R3 and R4 evidence remain unchanged.
R2_REVISED_PILOT_MASTER_REBUILD is RUNNING. All-board inventory discovered an
additional A/B listing-date conflation and a post-Pilot SZSE code transition;
neither provisional counts nor the old R3 verdict are v2 acceptance.
Stop unfrozen at GATE_A_REVISED_DATASET_FREEZE after all fresh audits pass.
R5=BLOCKED_PENDING_REVISED_PILOT_ACCEPTANCE. No R4 on v2 or formal studies.

## Historical checkpoints below (superseded)

## Current: R5 stopped on new frozen Pilot master counterexample

Pilot v1 was frozen exactly as approved; all bytes and freeze receipt remain
unchanged. R4 engineering/API/UI checks passed. R5 independently discovered
three omitted STAR exit securities:688086,688555,688287. Frozen candidate,
securities and exclusion Parquet tables contain none of them. Root query omitted
STOCK_TYPE=8; code and regression check are now fixed, but no dataset rewritten.
Current Pilot readiness and source-master completeness acceptance are INVALIDATED.
R4=ENGINEERING_PASS_DATASET_ACCEPTANCE_INVALIDATED. R5 full dataset not created.
STATUS=BLOCKED_REVISED_FREEZE_REVIEW; HUMAN_APPROVAL_REQUIRED=YES;
HUMAN_APPROVAL_GATE=GATE_A_REVISED_DATASET_REVIEW.
SINGLE_SMALLEST_BLOCKER=FROZEN_PILOT_MASTER_OMITS_STAR_EXIT_SECURITIES.
See `../research/PILOT_FREEZE_R4_R5_CHECKPOINT.md`. This is not approval to freeze
an unbuilt v2 or run formal studies. No Development/Validation/OOS, merge or release.

## Historical checkpoints below (superseded)

## Current: Gate A approved, Pilot frozen, R4 engineering smoke running

Human Gate A approval supersedes the stop below. Final read-only verification
PASS; Pilot v1 frozen with unchanged0696a5c7...manifest. Freeze record canonical
SHA74870e7d64a9197bd75a6ee32e7bf019aecaf5159d7ed9d1023078df7ce0ad31.
STATUS=RUNNING; CURRENT_STAGE=R4_PILOT_ENGINEERING_SMOKE_STUDY.
No formal Development/Validation/OOS is authorized. R4 only uses unchanged
predeclared strategy and fail-closed unknown execution states. Next R5 is full
2010-2025 historical materialization/audit, not formal strategy tuning; next gate
GATE_FULL_RESEARCH_DATASET_FREEZE. See PILOT_FREEZE_AND_SMOKE.md.

## Historical checkpoints below (superseded)

## Current: R3 complete; STOP at Gate A

2026-09-12 UTC: STATUS=AWAITING_HUMAN_APPROVAL; CURRENT_STAGE=R3;
last completed stage=R3. SOURCE_AUTHORITY_PREFLIGHT=PASS, all prior authorities
unchanged. PILOT_DATASET_CREATED=YES; PILOT_A_SHARE_DATA_READINESS=READY;
DATASET_AUDITED=YES; DATASET_FROZEN=NO.
HUMAN_APPROVAL_GATE=GATE_A_DATASET_FREEZE; HUMAN_APPROVAL_REQUIRED=YES.
No active engineering/source blocker; do not proceed without human freeze approval.

All5177 ordinary A shares complete:657 Eastmoney +4520 Tencent,1922088 raw bars,
382 sessions,12528 factor rows,4210 explicit missing observations; zero required
security failures/unresolved inputs/rejected rows. Candidate master5178 includes
one out-of-scope CDR689009; zero unclassified/non-A-share leakage. Original2580
partitions/951927 rows preserved. Atomic publication and no-refetch/no-rewrite
restart PASS; all22 R3 checks PASS, including5725 market-rule cases.
Manifest canonical SHA256:
`0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490`.

Important: official daily suspension/tradeability remains unknown for1926298
lifecycle security-sessions. Missing bars are not inferred suspensions. Independent
official evidence is still required for fills under the approved convention;
audit/readiness here does not assert execution readiness or complete suspension history.
No Development/Validation/OOS, freeze, merge or release was performed.
Full report: [R2/R3 ordinary A-share checkpoint](../research/R2_R3_ORDINARY_A_SHARE_REPORT.md).

## Historical checkpoints below (superseded)

## Current: approved ordinary-A-share scope implementation

Running recovery snapshot: 657 primary +3417 secondary inputs (4074 total),
1103 remaining, zero required failures. External secondary checkpoint advances
and supersedes these counters. Incremental Parquet:4020 securities/1498998 rows,
zero failures. All original2580 receipts reproduce the original `ff844abd...` hash.
Amount audit covers4032 securities/1503570 rows,26922 potentially reachable
decisions,zero ambiguous decisions/outliers; not yet the final full-universe audit.
R2 composer and R3 audit implementation/tests are based on8d6a835;419 tests
pass locally. No real Pilot publication or full R3 completion is claimed yet.

R2 RUNNING; HUMAN_APPROVAL_REQUIRED=NO. Scope decision APPROVED:
ORDINARY_A_SHARE_EQUITIES_ONLY. The former CDR methodology question is resolved.
689009 is AUTHORITATIVELY_OUT_OF_SCOPE_INSTRUMENT, not a required factor failure.
Generic scope gate and preserved out-of-scope failure ledger are implemented;
Full register/type/dated-IPO classification and the scope gate PASS:
5178 candidates, 5177 COMMON_A_SHARE, 1 CDR, 0 unclassified.
The only nonordinary instrument is CN-A:SSE:689009 (CDR).
Explicit original A-listing columns support nonmixed venues; STAR requires dated
original stock/CDR IPO metadata rather than backdating a current SEC_TYPE snapshot.
657 primary,1923 secondary,2580 partitions and951927 raw rows remain preserved.
Market-data worker has restarted from the accepted checkpoint for 2597 remaining
ordinary A-share securities. No successful input is re-fetched.
Approved scope manifest SHA-256:
`0b7fa3f26b99ffc19c179bc19a492693d6eb1c5249f4779251d8d9b03427334d`.
No dataset publication/audit/freeze, study or merge. Continue automatically to
R2/R3 and Gate A after this engineering gate, without another CDR scope question.

## Historical checkpoints below (superseded)


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


## Current running recovery milestone

R2 RUNNING. Primary657 preserved; secondary848 now materialized, total1,505
securities /554,152 raw rows /3,450 factor rows, zero partition failures.
3,673 inputs remained at this snapshot; live secondary-checkpoint.json is newer
as the worker continues. No dataset publication, full R3, freeze, studies or merge.
The original primary partition-report subset still hashes to
7c2916446fc867a39b41aa45a7062c44452be15fd2708a9b0e65882f5e573896.
Two-query/one-query normalized equality proved on260 recovered securities;
future requests omit the redundant second query without changing policy/coverage.
Delisting-period rule reachability is explicitly included: initial sample4335
potential checks (one more stable primary check than4334 previously reported).
The expanded current audit covered9891 checks with zero ambiguity (1544 available
securities /568116 rows, a later input snapshot than the materialized snapshot).
Observation inventory found3369 missing lifecycle-session observations across213
securities; no synthetic bars or suspension classifications. Zero-volume bars=0.
This inventory is not a final R3 pass or a newly established human-only blocker.
Old authority
artifacts retained; current audit writes separate amount-impact-current-* files.
405 backend tests and lint/type checks passed at acquisition milestone74f8c8c;
CI34612957718 SUCCESS. Latest refinements receive their own checks/CI.

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


## Current: focused Tencent amount acceptance completed

R2 BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; not Gate A.
PILOT_AMOUNT_REQUIREMENT = REQUIRED: existing 20-observation / 10M CNY liquidity screen.
TENCENT_AMOUNT_CLASSIFICATION = INSUFFICIENT_EVIDENCE; SECONDARY_ACCEPTANCE = FAIL.
Unit mapping is supported; provider rounding/aggregation error bound is not established.
1,719 preserved overlapping rows, maximum absolute difference51 CNY, maximum relative
0.0002227431347383828848417993403. No new market requests or tolerance changes.
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
657 successes/244,073 primary rows and4,521 pending members unchanged. R1 PASS intact.
No fallback promotion, publication, R3, freeze, studies or merge. Backend401 tests PASS.
See docs/research/TENCENT_AMOUNT_ACCEPTANCE.md and amount_audit_sha256 in state JSON.

## Previous candidate checkpoint (superseded)


## Latest checkpoint: systemic primary / secondary parity review

R2 BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; not Gate A.
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
Primary historical OHLCV authority remains PASS; operational availability is
PRIMARY_SYSTEMIC_TRANSPORT_FAILURE (6/6 newly authorized representative probes).
Tencent candidate: eight securities, 32 bounded requests, all normalized repeats
match; exited histories and Pilot IPO retained. 1,719 overlapping dates have no
OHLC/date disagreements. Four amount differences remain UNEXPLAINED after targeted
Sina corroboration; no new tolerance or production provider substitution is allowed.
CN_A_RAW_OHLCV_FAILOVER_V1 is CANDIDATE_NOT_ENABLED, secondary NOT_PROMOTED.
657 successful securities / 244,073 raw rows unchanged; 4,521 required gaps remain.
All original input and partition checksums verified unchanged. Candidate sample
rows are not production recoveries. No bulk primary retry, exclusion, R3, dataset
publication/freeze, study or PR merge. Backend 400 tests and lint/type checks PASS.
See docs/research/R2_RAW_FAILOVER_ACCEPTANCE.md and new hashes in project_state.json.
Next: supported vendor precision evidence or an explicit narrow amount-precision
decision, then re-evaluate secondary authority before resuming pending acquisition.

## Earlier checkpoint (superseded by current failover review)

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
