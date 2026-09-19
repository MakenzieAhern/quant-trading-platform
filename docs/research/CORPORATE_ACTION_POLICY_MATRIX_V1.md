# Corporate-action policy matrix V1

Frozen **policy catalog**, not a frozen Full Dataset. Authority: human mandate SHA-256
`9362f32566013841a3a45fd5946abbc9c128fd4f66b5ea20e23c902180a8a4ad`.
The machine-readable catalog is `.research/corporate_action_policy_matrix_v1.json`.
Policy approval does not imply that an implementation, event source or full-period census passes.
Revision 2 preserves revision 1 file SHA-256
`3784d6817fb7ab30081e57d9693bc1ac7adbfbaccebe200e2903e7021d8a0352` and adds
human-approved differentiated-cash decision SHA-256
`869cdc3159ee770d06c29ecca4965d9b554382bb73c0fdd7e9c64724525d05c5`.
Revision 3 preserves revision 2 file SHA-256
`8e4269e5b62a7a738e4e46a0f0caada47fe07af98b482ae3f81fd946cf759c79`
and applies the human mandate SHA-256
`26bf7dafd15bf2eca4476b2dfeaa09b5fc95ee90dbe2769637ae9a21bfa603e5`
to the existing retained-bonus and fractional-share classes.

| Event class | Approved accounting |
| --- | --- |
| Cash dividend | Existing authoritative cash entitlement; no adjusted-price double count. |
| Differentiated cash | `DIFFERENTIATED_CASH_ORDINARY_PUBLIC_A_V1`: exact gross final-implementation term for the ordinary exchange-tradable public A-share holder; public/unrestricted A over restricted or special classes; no averages, tolerance, tax-net values or synthetic ex-price inference. |
| Retained bonus | Official quantity increase, unchanged aggregate basis unless official basis/tax terms require otherwise. |
| Retained-bonus fraction | Exact official whole-share allocation when individually evidenced; otherwise floor the theoretical post-event quantity, no synthetic cash or tradable fraction, preserve aggregate basis, audit the discarded fractional bound. |
| Restructuring pass-through | Net pass-through, no basis allocation; original holdings unchanged. |
| Rights | No subscription, no monetization, no injected cash; metadata preserved. |
| Split/consolidation | Official ratio, basis conserved; official fractions first, otherwise floor/no cash; zero whole shares write off basis. |
| Partial surrender | Remove proportional historical basis; corporate-action loss; approved conservative fractional convention. |
| Full/zero-whole extinguishment | No orphan basis; corporate-action loss, not a sale. |
| Stock merger | Basis to successor; approved floor/no cash and zero-whole policy. |
| Demerger | Official tax/reference/valuation allocation, never an invented multi-asset split. |
| Mandatory cash-only | Nonelective exact cash per share times quantity; corporate-action PnL = proceeds minus removed basis. |
| Mandatory mixed consideration | Exact official consideration and basis allocation required. |
| Voluntary election | Do not participate absent a predeclared policy. |
| Temporary entitlement | Accounting continuity only; no orders, execution or factor ranking. |
| Event inside verified halt | Verified terms and nontradable interval, apply before authoritative first tradable Bar; no invented registry timestamp. |
| Unknown material structure | Consolidated human gate only under all four materiality conditions below. |

Every accounting action creates no synthetic Order/Fill. Trading PnL is not used to hide
corporate-action gains or losses. Raw execution prices stay separate from adjustment data.
Event identity, source bytes/checksums, applicable holder class and effective boundary remain mandatory.
Source retries, known variants and implementation defects do not require another human decision.

## Human-stop rule

All four must hold: material quantity/cash/basis/eligibility effect; no safe mapping above;
official evidence cannot determine treatment; alternative choices materially affect research.
Finish independent safe work before presenting one consolidated report. A source lead is not
an accepted event, and a missing census count is not zero.

## 600381 chronological regression

Ordinary non-responsible holders: June 25, 2014 consolidation 100 old to 16 new shares,
then June 30, 2014 separate surrender of 12% of consolidated shares. The later confirmation
documents are audit evidence, never strategy inputs. No separate surrender record date is
invented from its completion date. Per-holder global fractional ranking is not reproducible;
the approved research floor applies, explicitly distinct from an actual registry allocation.

For 10,000 old shares with basis 100,000: consolidation yields 1,600 shares, basis 100,000;
surrender removes 192 shares and basis 12,000, leaving 1,408 shares and basis 88,000.
These are accounting regression quantities, not a strategy or profitability result.
During missing raw-price observations the carrying amount is not an executable quote;
new orders/fills remain blocked until an actual raw Bar is observed.

The frozen Pilot v2 bytes remain untouched. Full Dataset freeze, Development, Validation,
Official OOS, merging PR #12 and release creation remain unauthorized.
