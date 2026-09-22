# Mandatory partial share surrender checkpoint

Policy CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1 is APPROVED and implemented.
Approval receipt: PARTIAL_SURRENDER_APPROVAL_V1.json. No symbol-specific production branch.

## Accounting acceptance versus historical admission

Generic exact-whole-quantity accounting PASS: Q100/B1000 -> surrendered20/B200,
retained80/B800, average10; Q1000/B12345.67 -> surrendered200/B2469.134,
retained800/B9876.536, average12.34567. Corporate-action PnL alone receives the
basis loss; cash, fees, external capital, orders, fills and trading PnL do not change.
Snapshots persist immutable audit records and expose the separate loss category.
Strategy observations omit event evidence. Chronology, holder applicability,
duplicate processing, unsupported compensation, fractional allocation and
unrepresentable Decimal average-cost invariants fail closed before event mutation.
No nearest/floor/ceiling allocation is invented for surrender.

600462 historical event admission remains PARTIAL, not PASS:
- Ordinary nonexempt holders surrender20%; top four have40%/30% treatment.
- Record date2012-02-08 includes qualifying nontrade successors.
- Shares are transferred to bankruptcy property disposal account, not cancelled.
- No direct compensation is allocated to surrendering ordinary holders.
- Separate30% capital-reserve issuance is NOT holder consideration.
- October29 is receipt of the registry notice, not an explicitly stated registry
  effective transfer date. Issuance dates must not substitute for surrender dates.
- Issuance-specific global fractional ranking is not evidence of the surrender rule.
- November2 disclosure identifies unexecuted holder categories; applicability is
  explicit, never assumed from a security code alone.
- Actual issuer-wide surrendered shares96,997,075 are NOT a simulated Portfolio
  quantity or a full-universe materiality statistic.

## Source recovery and reproducibility

Reused all prior snapshots. Targeted stock-specific2012 metadata104 announcements/
4 pages; restructuring query28 announcements; reviewed June28 plan, July10
explanation, August8 court-approved plan, October20/27/30/31 implementation/progress,
November2/6/8 progress, December14 completion and original/revised2012 annual reports.
The final court plan confirms the two legal legs but does not specify the missing
registry execution date or surrender fractional algorithm. Annual report dates are
receipt/completion statements, not a substitute registry transaction record.
No repeated failed acquisition or new provider authority was introduced.

Seven core source PDF bytes, URLs, SHA256s and retrieval receipts were reverified.
Evidence receipt: external staging/full-merger-v1/partial-surrender-evidence-v1.json.
Event SHA256:3fbaed5a18bb3163390dfbb3ba97b4d76ed246d3d7527308bd8e6d4ea912ef69.
Canonical manifest SHA256:1619c597b7703c1b39aae080ce1a45ff88d719dae0442614fb4541e58cf2b883.
Reverse document/source order produces the identical receipt.
Source review V1 is preserved; V2 retains the unresolved effective date as null.
Synthetic engineering dates are not historical evidence.

## Materiality and full corporate-action coverage

One identified partial-surrender event/security; full census NOT_ESTABLISHED.
Reviewed event compensation=0; reviewed event unresolved consideration=0.
Full-market event counts, shares surrendered, total/max historical account basis
written off, compensation and unresolved-consideration totals are NOT_ESTABLISHED.
No account path was generated; do not replace those unknown totals with zero.

| Type | Support state |
| --- | --- |
| CASH_DIVIDEND | Existing supported accounting; full census incomplete |
| STOCK_DIVIDEND | Existing supported accounting; full census incomplete |
| BONUS_SHARE | Existing supported accounting; full census incomplete |
| RIGHTS_ISSUE | Preserved V2:4 supported/144 source-unresolved of148 events |
| DEMERGER | Preserved600003 supported; full census incomplete |
| MERGER | Preserved000024/600005 supported;3 prior candidates unresolved |
| MANDATORY_PARTIAL_SHARE_SURRENDER | Generic accounting PASS;600462 historical admission PARTIAL |
| SPLIT_OR_SHARE_CHANGE | Source-specific ratio/provenance required; full census incomplete |
| MANDATORY_CONVERSION | Accepted specific merger/demerger structures only; no generic no-op |
| REORGANIZATION | Separate legal legs required; unknown material legs fail closed |
| UNKNOWN_VARIANT | Unresolved, not admitted as no-op |

Prior95-page/2849 merger announcement inventory,69 document leads and6-page/175
capital-adjustment notice inventory remain resumable; they are not certified event counts.
Rights/demerger/merger acceptances and frozen Pilotv2/R4v2 are unchanged.

## Validation and stop

518 backend tests and78 frontend tests PASS; Ruff/format/mypy PASS.
Migration0009 upgrade/downgrade/upgrade passed in isolated test database.
No application database downgrade. No profitability inspection or formal study.

R5_FULL_DATASET_STATUS=BLOCKED_SOURCE_EVIDENCE.
SINGLE_SMALLEST_BLOCKER=PARTIAL_SURRENDER_REGISTRY_EXECUTION_EVIDENCE_UNVERIFIED:CN-A:SSE:600462.
Needed: official registry execution evidence establishing the effective transfer
date and surrender-specific allocation. Human source assistance requested.
The basis approval is recorded; the previous unapproved-basis condition no longer
describes the decision state, but complete historical600462 acceptance is not declared.
No new compensation or fractional mechanism was positively established.
This is a source recovery stop, not a new invented methodology choice or freeze gate.
Resume from the preserved event/source queues when evidence is supplied.

Requested full coverage2010-01-01..2025-12-31; verified safe start/full coverage
NOT_ESTABLISHED; full dataset CREATED/AUDITED/FROZEN=NO.
HUMAN_APPROVAL_GATE=NONE; HUMAN_APPROVAL_REQUIRED=NO; HUMAN_SOURCE_INPUT_REQUIRED=YES.
Next authorized terminal freeze gate remains GATE_FULL_RESEARCH_DATASET_FREEZE.
Development/Validation/OOS=NOT_RUN; PR12 unmerged; release not created.
