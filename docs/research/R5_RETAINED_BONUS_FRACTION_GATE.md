# R5 retained-bonus fractional-share methodology gate

Status: **RESOLVED_BY_GENERIC_POLICY_V1**. This resolves only the retained-bonus
fractional accounting choice; it does not authorize a Full Dataset or strategy run.

The 2026-09-18 component-integrality replay extends this same gate to 39
formerly accepted integer-total bonus events with fractional stock-dividend
or capital-transfer components. The bounded current ledger is v30: 243/288
supported, 45 unresolved. Cumulative P1 v58 has 247 facts / 242 documents
open. See `R5_BONUS_SOURCE_ORACLE_V1.md`; the older v48 count below is a
historical checkpoint.

## Official evidence and concrete reachable case

- 688339's three ordinary-A implementation notices specify 0.4 new shares per
  held share: [2022](https://static.cninfo.com.cn/finalpage/2022-05-27/1213517606.PDF)
  (`f00c410bb2ffb77049be544e354d51d20e6658ea58355fea160bbbd94cb3f7ed`),
  [2023](https://static.cninfo.com.cn/finalpage/2023-06-29/1217155733.PDF)
  (`292ae3448798caaec95f63748f1e1f999c67d1db40d644e2dabbcb20df156a97`),
  and [2024](https://static.cninfo.com.cn/finalpage/2024-07-12/1220614824.PDF)
  (`9fec1196a420a44bcf9fa90cc2f0d2009de4c0db610d166c39e241fddc6b8d46`).
  Official exchange rows corroborate record/ex dates and ratios in the immutable
  `p1-official-bonus-source-terms-v4.json` report.
- For an illustrative continuously held 100-share position, exact multiplication
  gives 140 after 2022, 196 after 2023, and **274.4** after 2024. This is a
  reachability example, not a strategy run or claim about any actual account.
- The 2024 issuer PDF says sub-share remainders are allocated in rank order
  across all registry accounts, with random tie order. The individual 274/275
  whole-share outcome cannot be reconstructed from public issuer/exchange data.
  The 2023 notice describes the same mechanism. The 002873 2022 and 002982
  2023 SZSE notices likewise describe registry-wide remainder allocation.

## Current policy gap

The approved `BASIS_CONSERVED_RETAINED_BONUS` policy preserves aggregate basis,
but does not prescribe a research convention for an unknowable registry-level
fractional allocation. `PortfolioEngine.apply_corporate_action` currently
multiplies quantity by `1 + share_ratio`, so it can carry a fractional A-share
position. The approved floor/no-fabricated-cash convention is specific to
stock mergers and share consolidations, not retained bonuses. Extending it
silently would be a new material methodology decision affecting quantity,
basis per share, valuation and subsequent sell eligibility.

## Approved decision

The human completion mandate SHA-256
`26bf7dafd15bf2eca4476b2dfeaa09b5fc95ee90dbe2769637ae9a21bfa603e5`
explicitly preserves retained-bonus and fractional-share conventions and directs
mapped events to continue without another approval. The deterministic generic
policy is therefore `CN_A_RETAINED_BONUS_FRACTIONAL_SHARE_POLICY_V1`: use exact
official whole shares when individually evidenced; otherwise floor the
theoretical post-event quantity, book no synthetic cash or tradable fraction,
preserve aggregate basis on the remaining whole shares, and audit the discarded
fractional bound. This is pre-performance, applies to every ordinary-A retained
bonus event, and is not a symbol-specific rule.

This gate does not close the **253 remaining P1 facts in cumulative v48**, the
corporate-action census, or the verified safe-start date. The 600337 original
designated-disclosure notice and two bounded merger source requests have since
closed independently, without promoting any fractional retained-bonus source
term to an accepted economic event.
