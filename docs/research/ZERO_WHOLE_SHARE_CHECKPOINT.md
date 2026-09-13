# Autonomous Quant Project Checkpoint

## Approved policy delivered

MERGER_POLICY = CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1

ZERO_WHOLE_SHARE_POLICY = WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1

600005_EVENT_CLASS = MANDATORY_STOCK_FOR_STOCK_MERGER

600005_CONVERSION_RATIO = 0.56

600005_ZERO_WHOLE_CASE = PASS

600005_ACCOUNTING = PASS

MERGER_FRACTIONAL_REPRODUCIBILITY = PASS

The previous zero-whole basis approval blocker is RESOLVED. Shared Portfolio
accounting, persisted snapshots, source manifests, research result lineage and replay
include the policy. No production600005 special case or dependency was added.
Cash/trading PnL/orders/fills remain unchanged. Parent basis is realized only in the
corporate-action component; parent market value is removed once. No zero-quantity
successor or orphaned basis is retained. Closed-trade metrics are not contaminated.

| Synthetic Q | Exact T | Whole W | Fraction F | Accounting |
|---|---|---|---|---|
| 1 | 0.56 | 0 | 0.56 | Corporate-action loss=-B; no pending asset |
| 2 | 1.12 | 1 | 0.12 | Full B transferred to1 whole share |
| 100 | 56 | 56 | 0 | Full B transferred to56 shares |
| 3 | 1.68 | 1 | 0.68 | Full B transferred to1 whole share |

These are synthetic accounting cases, not strategy holdings or profitability results.
The exact synthetic B=3Q/last raw mark=4/commission0.5 test reconciles total PnL
before conversion, while pending and after activation under reduced ambient precision.
Repeated/reversed-source replay, JSON/database roundtrip, no-bar session and existing
acquirer holdings pass. Official compensation variants cannot fall through to writeoff.

## Official evidence and timing

Retained600005 issuer notices confirm actual successor600019, ratio0.56 and global
remainder ranking/random ties. The January16 notice has a2016 last-trade year typo;
the January24 official notice confirms2017-01-23. Termination/record2017-02-14,
conversion2017-02-17, converted shares eligible2017-02-27. Acquirer original listing
2000-12-12 is distinct. February22 completion disclosure remains separately dated,
not backdated as a pre-conversion signal. Full PIT dataset acceptance is not implied.

Source review: MERGER_600005_SOURCE_REVIEW.json. External source root:
/home/yuchen/data/research/staging/full-merger-v1. Three source documents rehash and
replay identically. Event SHA256:
456fc000cf23e493384bb0857deeffde046a21977d0ce4c90454bed3e232aa30.
Canonical source-manifest SHA256:
a83c54b5a6e25e641eed8941a47b7d83d54da99e2b2f63765d45c129822718a2.
Approval receipt: .research/approvals/zero-whole-share-policy-v1.json.

## R5 resumed, not restarted

Updated the existing five-candidate inventory in MERGER_INVENTORY_V2.json;
V1 and accepted000024 manifest are preserved. Supported reviewed events=2;
the remaining3 have targeted official evidence retained, not fabricated dates:
600553 ->601992 ratio1.2;600991 ->601238 ratio1.6;601299 ->601766 ratio1.10.
Their exact source chronology/activation reconciliation remains unfinished.

The full-period merger-title query now has all95 pages/2849 unique announcements;
69 implementation/listing document leads are retained separately. Query manifest:
66c774ead5744c8a72597a8f9dc58591c84b32a652c1a771ef85215e6d186eaf.
This is NOT a full market-wide event census: proposals, cancellations, unlisted
subsidiaries, B-share parents and duplicate event documents require classification.
TOTAL_MERGER_EVENTS = NOT_ESTABLISHED (5 prior candidates updated).
SUPPORTED_MERGER_EVENTS = 2 (reviewed subset).
UNRESOLVED_MERGER_EVENTS = NOT_ESTABLISHED (at least3 prior candidates plus new leads).

Other corporate-action review captured6 pages/175 capital-adjustment announcements.
Source provenance is preserved under capital-adjustment-query-audit-v1.json;
canonical SHA2561da654fbb1b42ca94df1afe7c311e3f9441655893ab9a48aec6848a2d3d4aa7e.
The source queries are complete; the corporate-action census is not.

Cash/stock dividends and genuine holder bonus shares remain supported only with
complete terms. Rights148 identified/4 supported/144 source-unresolved and600003
demerger acceptance remain unchanged. Other split/share-change, mandatory conversion,
reorganization and unknown variants remain explicitly fail-closed. The machine report
records each support state; no unsupported event was dropped or labeled normal.

## New material methodology gate

Official600462 notice2012-71, published2012-10-31 and signed2012-10-30, confirms
ordinary shareholders outside four named largest holders surrendered20% of holdings.
The30% capital-reserve issuance went directly to a bankruptcy property-disposal
account, NOT ordinary shareholders. Both relevant pages were read and visually checked.
Source: https://static.cninfo.com.cn/finalpage/2012-10-31/61741320.PDF
SHA2569d53f1ea78030b5ee3581af4316f37d6511c4af853623c6b7ea07e42e00cad9a;
retrieved2026-09-13T01:55:17.903619+00:00.

This is compulsory partial surrender in the SAME continuing security, not conversion
to a successor and not the approved zero-successor boundary. With hypotheticalQ100,
B1000 and80 retained shares, retaining B1000 versus retaining B800 and realizing200
as corporate-action loss selects a different basis/PnL policy. Existing approvals do
not select either. No treatment, synthetic bonus, compensation or exclusion was applied.
The precise earlier surrender transfer date still needs targeted chronology evidence:
the notice's2012-11-02 capital-reserve ex-date is NOT assumed to be the surrender date.
That source task is separate from the required basis-methodology decision.

SINGLE_SMALLEST_BLOCKER =
MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600462

HUMAN_APPROVAL_GATE = R5_MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY

HUMAN_APPROVAL_REQUIRED = YES

Human decision needed: specify historical-cost-basis treatment for compulsory
uncompensated partial share surrender in a continuing security. Do not reinterpret
this as a request to redo already approved merger/rights/demerger policies.

## Full-account materiality and final state

ZERO_WHOLE_SHARE_EVENTS = NOT_ESTABLISHED

ZERO_WHOLE_SHARE_POSITION_OCCURRENCES = NOT_ESTABLISHED

TOTAL_BASIS_WRITTEN_OFF = NOT_ESTABLISHED

MAX_SINGLE_WRITE_OFF = NOT_ESTABLISHED

TOTAL_MARKET_VALUE_REMOVED_AT_EVENTS = NOT_ESTABLISHED

No full historical account path was generated; these are unknown, not zero.

R5_FULL_DATASET_STATUS = BLOCKED_MATERIAL_CORPORATE_ACTION_METHODOLOGY

REQUESTED_FULL_COVERAGE = 2010-01-01 through2025-12-31

VERIFIED_SAFE_START_DATE = NOT_ESTABLISHED

VERIFIED_FULL_COVERAGE = NOT_ESTABLISHED

FULL_DATASET_CREATED = NO

FULL_DATASET_AUDITED = NO

FULL_DATASET_FROZEN = NO

DEVELOPMENT_STUDY = NOT_RUN

VALIDATION_STUDY = NOT_RUN

OFFICIAL_OOS = NOT_RUN

OOS_AUTHORIZED = NO; PR_MERGED = NO; V1.1.0_CREATED = NO.
Full freeze gate not reached. Accepted frozen Pilotv2 and R4v2 remain unchanged.
No background ingestion/strategy worker remains.

## Verification

504 backend and78 frontend tests PASS. Ruff/format/mypy118 source files PASS.
Isolated test schema downgrade/upgrade and additive application migration0008 PASS;
no schema drift. API health HTTP200; frontend HTTP200 on configured5173.
MakenzieAhern Git/GitHub identity verified unchanged. Existing feature branch/PR12
workflow retained. Source data/PDFs stay external, not committed to Git.
