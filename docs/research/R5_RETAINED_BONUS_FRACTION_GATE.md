# R5 retained-bonus fractional-share methodology gate

Status: **HUMAN_DECISION_REQUIRED**. No Full Dataset or strategy run is authorized.

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

## Decision requested

Approve one deterministic, pre-performance convention for genuine retained
bonus/share-dividend fractions when exact per-account registry evidence is
unavailable. A conservative candidate is: apply official whole shares if
individually evidenced; otherwise floor the theoretical post-event quantity,
book no synthetic cash or fractional tradable share, preserve aggregate basis
on remaining whole shares, and record the discarded fractional bound.
Alternatively, exclude affected security-date
holdings until exact allocation is evidenced. Neither choice is approved here.

This gate does not close the 273 remaining P1 facts, the 150 other triage
documents, the 600337 final-implementation source gap, the corporate-action
census, or the verified safe-start date. No source term was promoted to an
accepted economic event by this report.
