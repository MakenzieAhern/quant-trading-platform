# Tencent amount focused acceptance audit

## Decision

PILOT_AMOUNT_REQUIREMENT = REQUIRED.
TENCENT_AMOUNT_CLASSIFICATION = INSUFFICIENT_EVIDENCE.
SECONDARY_ACCEPTANCE = FAIL (not a finding that Tencent prices are invalid).
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.

This audit implements the latest human instruction without changing the existing
methodology, widening a tolerance or promoting the candidate. The controller was
RUNNING with no approval required during review; it stops BLOCKED on this evidence
gap, not Gate A. All 657 primary securities/244,073 rows and 4,521 pending members
are retained. No new market-data request was needed; candidate data are not production
recoveries. No R1 re-audit, publication, R3, freeze, study, release or merge occurred.

## Existing contract and consumers

`DATASET_MANIFEST.md` requires Decimal normalization, distinct nulls and lineage;
it does not declare amount dispensable for the Pilot. `DailyBarRecord.amount`
allows None for general provider interchange, not research eligibility.
The existing `backend/app/research/strategy.py` (last changed in commit
0f0ab762a0f53cb7417d498633c2320ddd9a8f5d, before this audit) requires 20 amount
observations and mean >= 10,000,000 CNY before factor selection (lines24,45,63–68).
NULL would withhold those observations and change the eligible population.
No frozen, published Pilot dataset exists yet; the pre-existing research design,
not the generic schema's nullability, determines this REQUIRED classification.

| Use | Existing amount dependency |
| --- | --- |
| Static master universe | None; identity and lifecycle authorities |
| Research eligibility / liquidity screening | Required 20-observation mean threshold |
| MOM_12_1 / TREND_120 / LOW_VOL formulas | Adjusted closes, not amount |
| Portfolio construction | Indirect via liquidity-screened candidate population |
| Risk | No direct daily-market-amount use found |
| Execution | Raw prices and volume cap; no direct daily amount use |
| Transaction costs | Order/fill notional, not daily traded amount |
| Benchmark | Accepted index closes, not constituent daily amount |

Only code and contracts were inspected. No strategy or study was run. No threshold,
cost, factor, universe, exclusion or null policy was altered to help acceptance.

## Schema, units and limitations

TENCENT_AMOUNT_PRESENT = YES for all 1,719 overlap observations.
TENCENT_AMOUNT_DTYPE = raw JSON string; Decimal in this audit. The pinned SDK uses
`pd.to_numeric(errors="coerce")`, which can lose decimal precision and converts
invalid values to NaN; this audit does neither.
TENCENT_AMOUNT_UNIT = 10,000 CNY per raw field-8 unit.
TENCENT_AMOUNT_DECIMAL_PRECISION = observed 2 places (100 CNY output quantum).
TENCENT_AMOUNT_ROUNDING_BEHAVIOR = UNDOCUMENTED / NOT ESTABLISHED.
TENCENT_AMOUNT_SOURCE_SEMANTICS = SDK maps raw day field8 to daily traded monetary
amount and multiplies by 10,000 to CNY; exact vendor aggregation/rounding not established.
TENCENT_AMOUNT_NULL_BEHAVIOR = no null/empty observed; provider missing-value behavior
unknown. This audit fails closed on null, nonfinite or negative amounts.

Unit evidence is the actual AKShare1.18.94 implementation, not magnitude alone:
`akshare/stock_feature/stock_hist_tx.py` selects column8 as amount, declares output
CNY and multiplies it by10,000. Pinned source SHA256:
aa9199665d356ba3a054297004e349d3926fa83026abfd2d50c4b7f832226d84.
The [AKShare documentation](https://akshare.akfamily.xyz/data/stock/stock.html)
has an older six-column Tencent example; its generic/other-endpoint unit labels
are not evidence for this field's rounding. Focused searches of Tencent finance/
quote surfaces and AKShare material did not locate a provider rounding guarantee.
Unrelated QMT precision discussions and community posts were not used as authority.

Therefore no frozen production amount-normalization acceptance rule is introduced.
Decimal(raw_string)*Decimal(10000) remains an evidence-backed **candidate unit
conversion**, not a claim of additional precision or full semantic parity. Raw
strings remain in snapshots and the new per-observation audit.

## Deterministic representative sample

Reuse the intersection of the prior fixed eight-member candidate set and the 657
successful primary inputs, with every overlapping Pilot date, not selected residuals.
This yields six securities/1,719 sessions and all four boards. Sample roles refer
to this observed sample, not full-universe quantile claims; no return/performance
criterion was used and no new request was needed.

| Symbol | Coverage role | Rows | Raw close range CNY | Volume range shares |
| --- | --- | ---: | ---: | ---: |
| 600000 | SSE Main | 382 | 6.50–9.04 | 10,896,000–143,117,900 |
| 000001 | SZSE Main / high volume | 382 | 9.03–15.15 | 36,539,600–505,528,500 |
| 688008 | STAR | 382 | 43.15–76.46 | 4,882,600–54,561,200 |
| 300750 | ChiNext / high price / adjustment dates | 382 | 140.75–476.80 | 7,211,200–76,335,000 |
| 300336 | ChiNext / low price / *ST / delisting | 91 | 0.21–2.08 | 3,617,000–115,336,200 |
| 000732 | SZSE Main / low volume / ST / delisting | 100 | 0.43–1.43 | 325,100–163,581,300 |

Accepted SZSE timeline anchors explicitly show ST for000732 and STAR_ST for300336;
timeline SHA256 127f4cec8c32277057f6cf35f502a6efd2d54051607d5df32241d99859bed6f1.
The retained 300750 factor curve includes2023-04-26 and2024-04-30 (both within
the full compared span); factor source SHA256
e671b88fd79901931bfe44cb0c3a3fd0bf9b7eee96a5e93e0d788e3d5cdaf3d7.
These are accepted adjustment-event periods, not a newly asserted cash-action ledger.

All rows retain raw primary amount, raw secondary amount, multiplier, normalized
candidate CNY, absolute difference and relative difference = abs(delta)/primary.
Zero denominators are explicitly handled; no undefined relative value occurred.
Candidate multipliers1 and100 explain zero exact rows;10000 explains20 exact rows.
Direct ROUND_HALF_UP to0.01 source units matches1,715 rows; truncation matches843.
Neither is a universal transformation. Four exceptions are unchanged from the
prior report; preserved Sina corroboration suggests a precision chain but proves
neither the provider algorithm nor a future error guarantee.

Maximum absolute difference = 51.00 CNY.
Maximum relative difference = 0.0002227431347383828848417993403
(0.02227431347383828848417993403%), at000732/2023-05-25:
Eastmoney188558.00 CNY, Tencent18.86 raw ->188600.00 CNY, difference42.00 CNY.
The absolute maximum and relative maximum occur on different rows.
Observed extrema do not establish a bound over the4,521 unobserved securities.
No acceptance threshold was selected from strategy performance or modified to fit51.

## Authority and reproducibility

SECONDARY_RAW_OHLC_AUTHORITY = PASS (tested candidate route scope).
SECONDARY_VOLUME_AUTHORITY = PASS (previous explicit board normalization).
SECONDARY_AMOUNT_AUTHORITY = PARTIAL (unit mapped; rounding/semantic bound missing).
SECONDARY_SECURITY_LIFECYCLE_SUPPORT = PASS (representative retained sample).
SECONDARY_REQUEST_REPEATABILITY = PASS (preserved normalized two-repeat evidence).
SECONDARY_CHECKSUM_REPEATABILITY = PASS (canonical content, not volatile quote metadata).
SECONDARY_SOURCE_LINEAGE = PASS.
CROSS_SOURCE_OHLC_PARITY = PASS (1,719 dates;6,876 price comparisons).
SECONDARY_ACCEPTANCE = FAIL. No production secondary route or policy promotion.

External `raw-failover-v1/amount-observations.json` SHA256:
b7efbaa5571a63ed4a73e7e4f0adc1d908c9c8517079b234cc6702b6af9d7e96.
External `raw-failover-v1/amount-audit.json` SHA256:
3807e6cc28f043b3cdff4d2bca22d0ddea8d99b918d09771171b5467e9da3c93.
Existing candidate audit and every raw/meta source checksum verified before review;
the original files were not rewritten. Individual primary hashes, date-level
comparisons, sample ranges and tested scalings are in these external artifacts.
Replay: `python -m scripts.audit_tencent_amount --staging /external/staging`.
Focused Decimal checks cover retained50.02 difference, zero denominator, nonfinite
and negative input. Full backend401 tests, Ruff/format/strict mypy PASS.

Smallest remaining blocker: evidence establishing the required amount field's
rounding/aggregation semantics and a reproducible error bound sufficient for the
existing liquidity screen. No new provider, optional-field workaround or bulk retry.
