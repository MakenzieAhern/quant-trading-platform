# R5 full-history transaction-cost evidence inventory V2

Status: **PARTIAL_SOURCE_CLAIMS_ONLY**. No executable fee schedule is accepted
or changed by this review. The requested coverage remains 2010-01-01 through
2025-12-31. Review baseline: `e5383d7209f3a6e983bb9e0d7410181bb72a50d5`.

This bounded offline review reuses the retained 2009/2012/2013 SSE factbooks,
all sixteen official SZSE yearbooks from 2010 through 2025, the August 2012
CSRC press compilation, July 2015 SSE announcement and prior visual-review/
failure receipts. Original bytes were SHA-256 checked against their retrieval
records. The transition pages were rendered and read again; the CSRC PDF's
unmapped text glyphs were not accepted as extracted evidence.
Machine-readable source hashes, locators and unresolved claims are in
`.research/reports/r5-full-transaction-cost-gaps-v2.json`.

## Claims established by the selected retained sources

Rates below are fractions of the explicitly named base. A snapshot is not
evidence for a continuous effective interval. Both-side rates mean the rate
applies on each side, not twice to one modeled fill.

| Source and locator | Directly supported claim | Limit of the evidence |
| --- | --- | --- |
| SSE 2009 factbook, PDF 19 / printed 28 | Ordinary SSE A-share transfer fee: 0.1% (`0.001`) of traded face value, minimum CNY 1. Commission ceiling 0.3% (`0.003`) of notional, minimum CNY 5. Stamp duty 0.1% (`0.001`) of notional, seller only. | No exact commencement/end date for this table; no proof that these values span all 2010-2012 dates. Ceiling is not the actual broker commission. |
| SSE 2009 factbook, PDF 20 / printed 31; SSE 2012 factbook, PDF 27 / printed 21 | SSE A-share exchange handling fee 0.011% (`0.00011`) of notional both sides; regulator fee 0.004% (`0.00004`) both sides; stamp duty 0.1% (`0.001`) one side. | Exchange/member charges cannot automatically be added to customer commission. 2012 PDF 30 / printed 24 explicitly excludes broker commission and registration/clearing charges from that table. |
| SSE 2013 factbook, PDF 14 / printed 6 | On 2012-06-01 SSE handling fee changes from 0.11 per mille (`0.00011`) to 0.087 per mille (`0.000087`) of traded amount. | Establishes the SSE handling boundary; does not establish transfer fee, its minimum or SZSE's preceding rate. |
| SSE 2013 factbook, PDF 15 / printed 7; CSRC August 2012 compilation, PDF 127 / printed 114 | Handling rate 0.0696 per mille (`0.0000696`) of notional from 2012-09-01. CSRC text specifies both exchanges and both sides. | This is a handling component, not a complete investor charge. |
| SSE 2013 factbook, PDF 29 / printed 21 | Snapshot confirms handling 0.00696% (`0.0000696`), regulator fee 0.002% (`0.00002`) both sides and stamp duty 0.1% (`0.001`) one side. | Exact effective date of the regulator-fee reduction is not supplied by this page. |
| CSRC August 2012 compilation, PDF 127 / printed 114, dated 2012-08-02 | Says SSE transfer charge becomes 0.3 per mille (`0.0003`) both sides from September 1; the printed denominator is **traded amount**. | Denominator contradicts the later SSE source's description of the preceding face-value-based charge. No minimum or investor/broker retained split established. |
| SSE announcement, body dated 2015-07-01 | At 2015-08-01, SSE/SZSE handling changes from 0.0696 to 0.0487 per mille (`0.0000696` to `0.0000487`) of notional both sides. Within the latter: 0.00974 per mille investor-protection fund and 0.03896 per mille exchange. | These are subcomponents of 0.0487 per mille, not extra charges. No broker commission relationship established. |
| Same 2015 announcement | Preceding SSE transfer charge is 0.3 per mille (`0.0003`) of **traded face value** both sides; preceding SZSE charge is 0.0255 per mille (`0.0000255`) of **traded amount** both sides. Both change to 0.02 per mille (`0.00002`) of notional from 2015-08-01. | Direct evidence of a basis/rate transition. No transfer minimum, rounding, broker-retained part, preceding start dates, or post-2015 end date given. |
| SZSE yearbooks 2010-2025 | Deterministic annual snapshots cover handling rates from 2010 through 2025. Full A-share fee tables are present for 2010-2021; later books retain exchange-fee snapshots. | Annual snapshots corroborate values but do not by themselves create daily effective dates. |
| SZSE 2025 yearbook, PDF 1903 / printed 1886 | Explicitly states the 2023-08-28 A/B-share handling-fee transition from `0.0000487` to `0.0000341`, both sides. | This closes the handling boundary only; it does not establish transfer, stamp-duty or broker-contract terms. |
| SZSE 2015 yearbook, PDFs 660-661 / printed 644-645 | The A-share table lists handling, transfer and regulator fees and its footnote states that all three are included in commission. | This is authoritative table/component evidence, but it does not identify whether the research account's approved `0.0003` assumption is net or all-in. The executable model must not be changed without that methodology decision. |

The July 2015 publication date comes from the retained page body. Its URL contains
`20150912`; that archive path is not the publication or effective date. Likewise,
2025 HTTP Last-Modified headers on factbooks do not date their historical rules.

## Exact remaining evidence gaps

| Gap | Missing proof | Can the selected retained material resolve it? |
| --- | --- | --- |
| `TRANSFER_2012_BASE_CONTRADICTION` | Effective 2012 SSE transfer charging base, relevant clearing versus investor/broker components and their relationship. An original operative ChinaClear/exchange notice or authoritative correction is needed to reconcile the CSRC amount wording with the SSE face-value wording. | **No.** Both incompatible passages remain explicit; do not choose one or infer a typographical correction. |
| `TRANSFER_MINIMUM_AFTER_REDUCTIONS` | Per-side minimum, any per-fill/order aggregation rule and monetary rounding across the 2012 reductions and 2015-08-01 transition. | **No.** CNY 1 is directly evidenced only in the 2009 snapshot. Do not carry it forward, halve it, or replace an omitted minimum with zero. |
| `TRANSFER_PRE_2015_INTERVALS` | Exact 2010 opening regime and all 2012 transfer transitions for both exchanges, including preceding SZSE rates/charge incidence; face-value input authority where applicable. | **No.** The 2015 notice proves the immediate preceding rates but does not retrospectively date their whole intervals. Do not assume every security has face value CNY 1. |
| `CUSTOMER_COMMISSION_COMPONENT_SCOPE` | Whether the research commission assumption is net or all-in, and any retained broker share of historical transfer charges. | **No.** The official 2015 table proves that its listed handling, transfer and regulator components are included in commission, making a separate addition potentially duplicative. It still cannot define the research account contract. Preserve the approved assumption and do not change the model without a human choice. |
| `REGULATOR_FEE_EFFECTIVE_BOUNDARY` | Exact boundary changing the documented `0.00004` snapshot to `0.00002`, with applicability. | **No.** The yearbook sequence narrows the transition from the 2011 to 2012 tables but does not establish an exact trading date. |
| `FULL_PERIOD_INTERVAL_COMPLETENESS` | Continuous source coverage for all applicable cost regimes through 2025-12-31, including transfer and stamp-duty boundaries, with commission assumptions distinguished from statutory evidence. | **Partial.** The SZSE handling-rate path is now evidenced through 2025 and its 2023-08-28 boundary is exact. Non-handling intervals remain incomplete. |

The SSE handling boundaries at 2012-06-01 and 2012-09-01, the explicit
2015-08-01 handling/transfer transition and the SZSE 2023-08-28 handling
transition are now reviewable source claims.
They do not resolve the separate transfer-base/minimum/component gaps above.
No mathematical back-solving from advertised percentage reductions is used.

## Retained acquisition failures and executable model boundary

The existing 2012 acquisition manifest records DNS failure for the April 30 CSRC
page and HTTP 403 for the Guangdong August 24 page. The annual-report recovery
manifest records `NOT_PDF` and `FAILED_NO_FURTHER_RETRY`. They are negative
retrieval receipts, not supporting rule sources. This review made no network
request and did not repeat those failed routes.

At the reviewed commit, `TransactionCostSchedule` has a single transfer rate,
and `EffectiveDatedAShareCommission._calculate` always applies it to notional.
The shared schedule is split at the 2023 stamp-duty boundary but uses
`0.00001` for transfer charges even in its 2008-start interval. It cannot
represent the evidenced pre-2015 SSE face-value base or an exchange-specific
transfer minimum. Its commission `0.0003` / minimum CNY 5 remains an explicit
research assumption. This report neither changes that assumption nor promotes
the provisional model into full-history authority.

`FULL_TRANSACTION_COST_AUTHORITY = PARTIAL`

`NEW_EXECUTABLE_RULES_ACCEPTED = 0`

`DATASET_OR_STRATEGY_RUN = NO`

The existing retained-bonus human gate is independent. This inventory is
authorized source review and identifies no new methodology selected here.
