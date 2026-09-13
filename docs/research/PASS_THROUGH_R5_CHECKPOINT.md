# AUTONOMOUS QUANT PROJECT CHECKPOINT

600817 is accepted under the approved net pass-through convention. The old blocker is resolved.
R5 resumed the retained175-document capital-adjustment queue, reviewed21 additional plan
documents plus two600381 execution/reference notices, and reached a new material accounting gate.
Source PDFs remain outside Git. No prior accepted source or frozen Pilot bytes were changed.

```text
RESTRUCTURING_BONUS_PASS_THROUGH_POLICY = CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1
600817_EVENT_CLASS = RESTRUCTURING_BONUS_PASS_THROUGH
600817_BONUS_RATIO = 0.25
600817_TEMPORARY_REGISTRATION = VERIFIED_2012-07-31
600817_TRANSFER_TO_ADMINISTRATOR = VERIFIED_2012-08-01
600817_ORIGINAL_QUANTITY_PRESERVED = PASS
600817_BASIS_POLICY = NET_PASS_THROUGH_NO_BASIS_ALLOCATION
600817_ACCOUNTING = PASS
600817_REPRODUCIBILITY = PASS
PASS_THROUGH_EVENTS_TOTAL = NOT_ESTABLISHED_FULL_CENSUS
SUPPORTED_PASS_THROUGH_EVENTS = 1
UNRESOLVED_PASS_THROUGH_EVENTS = NOT_ESTABLISHED_FULL_CENSUS
ANALOGOUS_UNRESOLVED_SOURCE_LEADS = 7
TEMPORARY_SHARES_TOTAL = NOT_ESTABLISHED_FULL_CENSUS
600817_OFFICIAL_TEMPORARY_ISSUER_SHARES = 32182016
EVENTS_WITH_TEMPORARY_TRADABILITY = 0_OF_1_ACCEPTED; FULL_CENSUS_NOT_ESTABLISHED
EVENTS_WITH_HOLDER_COMPENSATION = 0_OF_1_ACCEPTED; FULL_CENSUS_NOT_ESTABLISHED
R5_FULL_DATASET_STATUS = BLOCKED_NEW_MATERIAL_METHODOLOGY
REQUESTED_FULL_COVERAGE = 2010-01-01 THROUGH 2025-12-31
VERIFIED_SAFE_START_DATE = NOT_ESTABLISHED
VERIFIED_FULL_COVERAGE = NOT_ESTABLISHED
FULL_DATASET_CREATED = NO
FULL_DATASET_AUDITED = NO
FULL_DATASET_FROZEN = NO
HUMAN_APPROVAL_GATE = R5_RESTRUCTURING_SHARE_CONSOLIDATION_ACCOUNTING
HUMAN_APPROVAL_REQUIRED = YES
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
OOS_AUTHORIZED = NO
PR_MERGED = NO
SINGLE_SMALLEST_BLOCKER = RESTRUCTURING_SHARE_CONSOLIDATION_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600381
```

## Why this is a new decision

Official600381 notice2014-083 confirms an implemented2014-06-25 share consolidation:
ordinary holders100 ->16; specified responsible holders100 ->2 or10. Issuer total shrank
from1,601,845,390 to198,925,752. A separate subsequent12% surrender follows consolidation.
The notice says trading remains suspended. June27 is the ex-reference date, not the legal
implementation date. Notice2014-084 confirms reference16.75 versus prior close2.08; neither
reference is a synthetic Fill. Subsequent surrender execution date is not yet established.

The approved600817 policy preserves original Q and does not apply to this shrinking-Q leg.
The approved original-share-surrender policy writes off proportional basis, but applying it
to a consolidation would select a materially different convention. Current SPLIT_OR_SHARE_CHANGE
remains unsupported and there is no approved consolidation basis policy. No implementation,
exclusion or basis write-off has been selected for600381.

Diagnostic only, not a strategy or observed holding: Q10,000/B100,000 becomesQ1,600 at
consolidation. PreservingB gives average62.5 and zero realized PnL; treating84% as a surrender
givesB16,000/average10 and corporate-action loss84,000. This difference exists even with exact
integer quantities, independently of fractional allocation or future strategy performance.

Smallest decision: approve how aggregate historical basis is treated in the restructuring
share-consolidation leg, separately from the subsequent12% surrender. A basis-preserving
consolidation would retainB and recomputeB/Q without realizing a consolidation loss; this is
a proposal for approval, not an implemented policy or a legal tax conclusion.

## Verification and preserved continuation

544 backend tests and78 frontend tests PASS; Ruff/format and strict mypy120 files PASS.
Migration0010 downgrade/upgrade verified in isolated test DB; application upgrade applied.
Docker services healthy; no application database used for tests.
600817 evidence checksum0e100b6ec0a586daa97b7bd599ce2669ab88cae22a83da72365dd5396b3ff2f2.
R5 census receipt8838106a1a876d155374cd9bac671552eea12d8201d6acc43ed1f6deeeddfa9f.
Full inventories/materiality are not inferred from reviewed document counts. Seven analogous
leads are not seven established pass-through events. All pending queues remain preserved in
RESTRUCTURING_CENSUS_CONTINUATION_V1.json and original external staging.
No background worker remains. Stop at this new decision, then resume R5 without restarting.
