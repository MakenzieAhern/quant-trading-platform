# Differentiated cash policy v1

Status: `PASS_FOR_CACHED_R5_BATCH`; this is not full-dataset acceptance.

The human-approved `CN_A_DIFFERENTIATED_CASH_DISTRIBUTION_POLICY_V1` is implemented
as rule `DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1`. The modeled portfolio is an
ordinary exchange-traded public A-share holder. Only exact gross final
implementation terms for that holder class are admitted as `Decimal` cash per
share. Public/unrestricted ordinary A terms take precedence over restricted,
controller, employee, H-share and B-share terms. Multiple reachable public-A
terms, net-tax-only amounts, proposal terms, synthetic ex-price values and missing
final terms fail closed.

All 664 cached differentiated final implementation documents were replayed:

- supported ordinary/public A term: 664
- non-applicable: 0
- ambiguous: 0
- missing final terms: 0
- conflicting: 0

The combined cash ledger now supports 24,306 events, leaves 3,541 unresolved and
retains 83 quarantines. The prior 23,642 accepted economic terms are unchanged;
664 events were added under the new policy. Reverse evidence order and repeated
replay produce identical events and checksums.

Immutable evidence:

- ledger: `/home/yuchen/data/research/staging/full-distribution-notices-v1/cash-current-implementation-ledger-v15.json`
- canonical SHA-256: `91e9ff1d6f064eb5ca0bc3d1dd97fb3b041b74e112fe95d7b78c6d4766da289a`
- file SHA-256: `4db2a892e5bfaf603a44beb99f65ac0f47d48e094ca0cd10cac801ec555feaf2`
- policy catalog SHA-256: `8e4269e5b62a7a738e4e46a0f0caada47fe07af98b482ae3f81fd946cf759c79`

The remaining cash partition is 1,879 missing final implementation sources, 844
exact-authority conflicts and 818 parser/policy-review groups. No tolerance,
averaging, future performance or unofficial source was used.
