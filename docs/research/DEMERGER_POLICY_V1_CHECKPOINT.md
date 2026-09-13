# Mandatory demerger V1 / R5 checkpoint

## Result and current stop

`CN_A_MANDATORY_DEMERGER_POLICY_V1` implemented and tested. The600003 demerger
accounting blocker is RESOLVED. R5 resumed targeted corporate-action inventory
using retained lifecycle evidence, then identified a genuinely different fractional
allocation methodology issue in000024's mandatory merger. No source backlog is
being reclassified as a new rights or600003 approval request.

Single smallest blocker:
`MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30`.
Human gate: `R5_MERGER_FRACTIONAL_SHARE_POLICY`; approval required YES.
This is not the Full Dataset freeze gate. No background worker remains active.

## Verified600003 evidence

Parent600003 last raw close3.87 CNY; termination2010-02-26; legal completion2010-03-01.
Each parent share converts into one601188 and one601518. Both list2010-03-19.
Their pre-listing references2.08 and1.79 sum to3.87. These are official reference
values, not observed opening prices. Original PDFs and retrieval receipts remain
outside Git; source URL, publication date, UTC retrieval, checksum and reviewed
physical PDF page numbers are pinned in `DEMERGER_SOURCE_REVIEW.json`.

- [Pre-effective termination notice](https://static.cninfo.com.cn/finalpage/2010-02-24/57619981.PDF),
  publishedFeb24, pages1-2: effective termination and mandatory conversion.
- [Full plan](https://static.cninfo.com.cn/finalpage/2010-02-11/57604018.PDF),
  pages6/192: conditional dissenting election and suspension from2009-03-16.
  Last trading session2009-03-13 is derived from that suspension boundary, not from
  undated historical names. The raw last-close value is independently in both listings.
- [601188 listing](https://static.cninfo.com.cn/finalpage/2010-03-18/57700807.PDF),
  pages3-4/11: conversion, listing, incorporation and2.08 reference.
- [601518 listing](https://static.cninfo.com.cn/finalpage/2010-03-18/57700809.PDF),
  pages3-4/11: matching lifecycle and1.79 reference. Issuer-hosted equivalent retained
  separately; canonical event uses the dated CNINFO disclosure.
- [Implementation report](https://static.cninfo.com.cn/finalpage/2010-03-18/57700808.PDF),
  pages5-8: later corroboration, not pre-effective disclosure availability.

The invalid-org-ID601518 query returned zero and is retained as a failed locator,
not evidence of absence. The successful targeted title query independently located
the exact dated CNINFO listing. No failed locator was promoted to evidence.

## Accounting, timing and scope

The generic immutable event has parent/successor stable IDs, ratios, lifecycle,
allocation enum, source-specific availability, cash-election metadata and canonical
checksum.600003 occurs only in evidence/regression data, not production branching.
No master/security exclusion, raw history backfill or parent-factor transfer occurs.

Pending accounting stores Q, aggregate cost B and carrying value Q*3.87, labelled
`CORPORATE_ACTION_PENDING_CARRY_VALUE`. It is non-tradable/non-orderable/non-executable.
No cash, external capital, proposal, order or fill is created. Parent realized PnL
is retained; conversion realizes zero. Pending carry contributes to equity/risk
exposure but not cash buying power. It never becomes a market quote or factor input.

The reference documents became availableMar18, after termination. Aggregate basis
remains intact while pending; future reference allocations are not exposed in the
pending snapshot or strategy session. On the accepted listing session, before
trading logic, successor cost is allocated from the now-available official references:
B*2.08/3.87 and B minus that amount, conserving B under fixed28-digit Decimal
precision. Raw opens are valuation inputs only, never allocation weights.

Actual raw successor marks affect unrealized PnL without suppression. Later ordinary
sales realize PnL against the exact remaining aggregate cost basis; partial-sale
rounding cannot lose the final residual. No election is exercised:
`NO_ELECTION_UNLESS_EXPLICITLY_PREDECLARED_AND_ELIGIBLE`.

Only OFFICIAL_REFERENCE_VALUE is implemented. Other enum values, unavailable
pre-listing evidence, asynchronous activation, fractional successor quantities,
existing-successor collisions and missing actual raw opens fail closed. These are
explicit support limits, not assumptions for unreviewed events. Pending/allocated
snapshots survive PostgreSQL round-trip using additive migration20260913_0006;
existing rows receive an empty pending list, without rewriting historical data.

## Reproducibility and checks

484 backend tests,78 frontend tests PASS. Ruff check/format, strict mypy117 modules,
Alembic schema check and git diff whitespace check PASS. The12 added regression
cases cover quantity1/100/137, pending chronology, all conservation invariants,
raw marks, later/partial sales, preserved parent realization, risk exposure,
source-byte tampering, unsupported allocation, exact storage, engine ownership
ordering, no event-derived orders/fills, input reversal and repeated replay.
Engineering synthetic fixtures are not a historical strategy study.

Eight original documents verified; offline audit repeated with identical output
bytes and reversed source/successor order. Reproduce from backend:

```sh
python -m scripts.audit_demerger_evidence \
  --review ../docs/research/DEMERGER_SOURCE_REVIEW.json \
  --event tests/fixtures/600003_demerger.json \
  --staging /home/yuchen/data/research/staging \
  --output /home/yuchen/data/research/staging/full-demerger-v1/accepted-event-manifest.json
```

Event SHA256: `7937ae6c3ed5c97c648b5f6a601390267e38a1a20d62b5b8b128ffc2115314a1`.
Canonical manifest SHA256: `8b75852bb5f716e87a97e408903eb978aff02318168486a4c31bbabd712a45ad`.
Manifest file SHA256: `e1c726bc6c34304599197c09f9c30e71718ad8cf68be291269fcbd1372af1f25`.
Checksum verification validates retained bytes; the semantic source review is
explicitly recorded, not falsely described as an automatic PDF authority parser.

## R5 inventory continuation and new material decision

Retained full candidate lifecycles contain both000024 and001979 with the2015-12-30
boundary. Targeted official retrieval verifies the merger, not a no-effect delisting:

- [SZSE termination](https://static.cninfo.com.cn/finalpage/2015-12-28/1201867754.PDF):
  decisionDec25, publicationDec28, A-share terminationDec30.
- [Final conversion implementation](https://static.cninfo.com.cn/finalpage/2015-12-28/1201863627.PDF),
  CMPD2015-177, pages1/4/5/7: A-share ratio1.6008; conversion afterDec29 close.
  Page5 requires integer share allocation using all holders' fractional remainders;
  ties beyond remaining shares are resolved by the registration system randomly.
- [Successor listing notice](https://static.cninfo.com.cn/finalpage/2015-12-29/1201871229.PDF),
  page1:001979 listingDec30 and the same A-share ratio.

The implementation PDF SHA256 is
`82b4aad17e1a7305e4987a714933d974ed349a84c8eae99149d0cc00fe8f0648`,
retrieved2026-09-12T23:50:30.460089+00:00. Original page5 was also visually checked.
100 hypothetical parent shares give160.0800 unrounded successor shares. Actual
integer allocation is160 or161 depending on the full register/tie outcome, not
determinable from this account's Q alone. No floor, ceiling, random sampling,
fractional tradable share, cash-in-lieu, zero-value default or exclusion is approved.

Smallest required decision: approve a deterministic simulated-account fractional
share convention for this mandatory merger when official register-dependent
allocation cannot be reproduced. This is an accounting methodology decision,
not a broken URL, missing tradability assertion, or choice based on performance.

| Primary category | Total observed | Supported | Unresolved | Unsupported variants |
|---|---:|---:|---:|---:|
| CASH_DIVIDEND | Not established | Not established | Not established | Not established |
| STOCK_DIVIDEND | Not established | Not established | Not established | Not established |
| BONUS_SHARE | Not established | Not established | Not established | Not established |
| RIGHTS_ISSUE | 148 | 4 | 144 | 0 |
| DEMERGER | 1 | 1 | 0 | 0 |
| MERGER | 1 | 0 | 1 | 1 |
| SPLIT_OR_SHARE_CHANGE | Not established | Not established | Not established | Not established |
| MANDATORY_CONVERSION | Not established | Not established | Not established | Not established |
| UNKNOWN_VARIANT | Not established | Not established | Not established | Not established |

Counts apply only to identified/provider-observed sets, never full-market census.
Unknown counts are null in the machine report, not zero. Supported dividend/bonus
code does not certify a complete event count. Merger variant1 is included in
unresolved1. The demerger/merger have mandatory-conversion subtypes and are not
double-counted as standalone conversion events. Remaining rights inventory is
unchanged:148/137 securities,4 accepted structures,144 source-work items,20
authoritative occurrences; canonical manifest97e70909...ee07 preserved. No unknown
material event is admitted or defaults to no effect.

## Final checkpoint and locks

R5_FULL_DATASET_STATUS=BLOCKED_MATERIAL_CORPORATE_ACTION_METHODOLOGY.
REQUESTED_FULL_COVERAGE=2010-01-01..2025-12-31.
VERIFIED_SAFE_START_DATE=NOT_ESTABLISHED; VERIFIED_FULL_COVERAGE=NOT_ESTABLISHED.
FULL_DATASET_CREATED=NO; FULL_DATASET_AUDITED=NO; FULL_DATASET_FROZEN=NO.
HUMAN_APPROVAL_GATE=R5_MERGER_FRACTIONAL_SHARE_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
DEVELOPMENT_STUDY=NOT_RUN; VALIDATION_STUDY=NOT_RUN; OFFICIAL_OOS=NOT_RUN;
OOS_AUTHORIZED=NO; PR12 OPEN/unmerged; no release or strategy-profitability review.

Frozen accepted Pilotv2 and all accepted source authorities remain unchanged.
R4v2 remains PASS with0 real-data fills, not rerun. Unfinished R5 master/ST/raw/
factor/rule/calendar/benchmark/census work remains explicit and cannot inherit
full-history PASS from the Pilot. After the new decision, resume that existing
queue and eventual full materialization/audit, stopping unfrozen at the full-data gate.
