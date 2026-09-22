# Rights entitlement V2 / R5 checkpoint

## Decision and implementation

Human decision f939025a-7742-41e5-b6e7-1e19b06df3ed is recorded in
`.research/approvals/rights-entitlement-classification-v2.json`.
CN_A_RIGHTS_ISSUE_POLICY_V1 remains approved. Portfolio policy is
NO_SUBSCRIPTION_NO_MONETIZATION_V1, participation DECLINE_SUBSCRIPTION.
Structure, tradability and portfolio policy are separate. No missing tradability
is converted into a historical non-tradability claim. Existing centralized
accounting and session ordering are reused; no dependency or strategy change.

000960/2010-01-27 is STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE,
ENTITLEMENT_TRADABILITY=NOT_EVIDENCED,
PORTFOLIO_TREATMENT=DECLINE_SUBSCRIPTION_NO_MONETIZATION.
The former exact tradability blocker is RESOLVED.

Reverified retained prospectus PDF pages12-14, issuance pages1,3-5, result pages1-3,
listing pages2-3: ordinary A shares; approval[2009]1474; original shareholders;
ratio0.24; price8.98; record2010-01-18; payment2010-01-19..25;
suspension19..26; successful ex-right date27. Result confirms150,664,585 issued;
later listing confirms capital651,086,660 ->801,751,245 and listing2010-02-04.
Later outcomes corroborate history, not retroactive point-in-time availability.
All original PDF bytes/URLs/retrieval times/checksums remain preserved.

## Inventory reclassification

Every one of148 provider events has exactly one terminal current classification:

| Classification | Count |
|---|---:|
| STANDARD_COMPLETE | 4 |
| STANDARD_PARTIAL_BUT_ACCOUNTING_SAFE | 0 |
| EXPLICIT_UNSUPPORTED_VARIANT | 0 |
| EVENT_IDENTITY_UNRESOLVED | 144 |

Complete terms4; incomplete nonessential terms0; missing material terms144.
137 securities. Four complete events:600036/2010,000960/2010,300147/2015,
000049/2023. Only600036 and000049 have confirmed non-tradability. The other two
remain NOT_EVIDENCED, with standard accounting accepted under the approved policy.
Missing listing at ex-date is not treated as missing subscribed holdings.

The144 unresolved events are not144 requests for a tradability decision.
128 lack independent occurrence/structure reconciliation;16 have annual-table
occurrence support but not independently accepted material ex-date/structure.
They remain the preserved source-work queue, not admitted or excluded securities.

## Census, not a provider-count completeness claim

PROVIDER_RIGHTS_EVENTS=148; AUTHORITATIVE_RIGHTS_EVENTS=20 identified occurrences;
MATCHED_EVENTS=20; PROVIDER_MISSING_EVENTS=0 within the reviewed authoritative set;
AUTHORITATIVE_EVENT_MISSING_PROVIDER_RECORD=0 within that set; DUPLICATE_EVENTS=0;
CONFLICTING_EVENTS=1 known provider chronology conflict (600066/2012).
PROVIDER_EVENTS_AWAITING_AUTHORITATIVE_RECONCILIATION=128.
UNEXPLAINED_CENSUS_DIFFERENCES=NOT_ESTABLISHED, not zero.

The explicit authoritative union contains the retained SSE2011 factbook page103
(17 record-year2010 events) plus the three distinct SZSE issuer events. No new
network acquisition was needed. This persists and expands the reconciliation ledger,
not the number of previously retrieved documents. Remaining exchange-years are
not certified; absence of2024/2025 or STAR rows is not proof of zero events.
The table's later publication cannot supply earlier strategy features or ex-dates.

External immutable output:
`full-rights-inventory-v1/inventory-reviewed-v2.json` under the existing staging root.
Parser RIGHTS_INVENTORY_V2; reverse-page/reverse-row replay and identical-byte
repeat publication PASS. V1 outputs are preserved, not overwritten.
Canonical manifest SHA256:
`97e709090751f515a5a4da7ecd47fa7bbb1f563566731c8025c1103dc2deee07`.
Review SHA256:
`c8b3eeba17db8c469d53d395a89b4afb116dcf11a6831d4e3733ffb882ce9035`.

## Actual remaining human methodology blocker

R5 safety review reverified a retained, materially different corporate action:
`DEMERGER_ACCOUNTING_POLICY_UNAPPROVED:CN-A:SSE:600003:2010-02-26`.
This is not a rights event and is not counted among the148 rights rows.
Official implementation report PDF pages5-8 establishes parent termination and
mandatory conversion: one600003 share -> one601188 share plus one601518 share.
The existing engine rejects MERGER_REORGANIZATION; a no-effect rights policy cannot
preserve these holdings. Source facts do not choose the research convention for
allocation of historical acquisition cost between successors or valuation before
independently executable successor prices are available. No equal-cost allocation,
future-price allocation, optional cash election, forced sale or exclusion is assumed.

Smallest required decision: approve a deterministic demerger accounting convention
for successor cost allocation and intervening valuation, subject to source verification.
This is a genuine material methodology stop under the new full-history safety rule,
not a stop over unknown entitlement tradability or ordinary acquisition backlog.
Rights census/material source work remains unfinished; it is not promoted to PASS.

Evidence: `official/600003-demerger.pdf` in the retained rights staging root;
https://static.cninfo.com.cn/finalpage/2010-03-18/57700808.PDF
SHA256 `e1caeeb68562ca5efc1f7d469df5026adf85d8ae1fa7d98cd2c59079b72a5c0e`;
retrieved2026-09-12T15:54:28.311964+00:00. This later report is corroboration,
not permission to backdate disclosure availability. Before implementation, earlier
dated plans and actual listing/registration availability must be reconciled.

| Category | Support state |
|---|---|
| CASH_DIVIDEND | Existing complete-event accounting supported; full census unfinished |
| STOCK_DIVIDEND | Existing complete-event accounting supported; full census unfinished |
| BONUS_SHARE | Existing complete-event accounting supported; full census unfinished |
| RIGHTS_ISSUE | Standard V2 decline/no-monetization supported; full census PARTIAL |
| SPLIT_OR_SHARE_CHANGE | Unsupported material event fails closed |
| MERGER | Unsupported material event fails closed |
| REORGANIZATION | Unsupported; exact600003 demerger requires methodology |
| UNKNOWN_VARIANT | Unsupported material event fails closed |

## Validation and locks

472 backend tests PASS, including48 focused rights/inventory/portfolio tests.
Ruff check/format and strict mypy116 modules PASS. Tests cover all three tradability
states, all seven explicit instrument classes, missing material versus nonessential
fields,000960, raw marks, unchanged cash/shares/basis, no synthetic assets/cash,
no Order/Fill invention and deterministic mixed-action replay.
R4v2 remains PASS with R4_REAL_DATA_FILL_COUNT=0; no R4 rerun or profitability review.
The frozen accepted Pilotv2 and all previously accepted authorities are unchanged.

R5_FULL_DATASET_STATUS=BLOCKED_MATERIAL_CORPORATE_ACTION_METHODOLOGY.
REQUESTED_FULL_COVERAGE=2010-01-01..2025-12-31.
VERIFIED_SAFE_START_DATE=NOT_ESTABLISHED; VERIFIED_FULL_COVERAGE=NOT_ESTABLISHED.
FULL_DATASET_CREATED=NO; FULL_DATASET_AUDITED=NO; FULL_DATASET_FROZEN=NO.
HUMAN_APPROVAL_GATE=R5_DEMERGER_ACCOUNTING_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
DEVELOPMENT_STUDY=NOT_RUN; VALIDATION_STUDY=NOT_RUN; OFFICIAL_OOS=NOT_RUN;
OOS_AUTHORIZED=NO; PR12 remains open/unmerged; no release. No worker remains active.
Next after resolution: preserve V2 classifications, resume source queue/census and
remaining R5 authorities, then materialize/audit; STOP unfrozen at the full-data gate.
