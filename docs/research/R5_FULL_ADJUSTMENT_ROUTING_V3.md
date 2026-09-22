# R5 full adjustment unmatched routing v3 — 2026-09-19

The 2,328 retained factor-change dates without a currently supported official
event were joined, by accepted security identity and exact date, to the
checksum-bound official bonus source oracle. Reverse input order reproduced the
same report.

## Result

- retained official bonus source-date routes: **912**
- no retained official bonus date: **1,416**
- integer displayed bonus ratio: **209**
- fractional displayed bonus ratio: **703**
- actual new-share tradability not evidenced: **713**
- separate scheduled date still requiring entitlement review: **199**

For 628 SZSE routes with displayed pre-close and ex-price values, the factor
step was checked against the full interval permitted by the accepted A-share
`0.01` price tick. **621 pass** and **7 conflict**. The other **284** routes are
SSE source rows without comparable displayed prices in this oracle.

For those same 628 zero-cash SZSE source rows, the factor step was separately
checked against `1 + displayed bonus ratio` using the source ratio's displayed
precision. **616 pass** and **12 conflict**. The row-level report shows that the
seven price conflicts all pass the bonus-ratio check, while twelve price passes
conflict with the displayed bonus ratio. Neither check overrides the other.

This is routing and diagnostic evidence only. It does not turn the summary
table into an accepted event, infer registry allocation, replace exact issuer
terms, or promote adjustment authority. The seven conflicts and 1,416 unrouted
changes remain explicit; no row is called normal.

Immutable report:
`/home/yuchen/data/research/staging/full-adjustment-audit-v1/unmatched-routing-v3.json`

- file SHA-256:
  `52f947fd14291caa39496d2771ab061ac03b02857f1cc1e66391ff4cf04966f6`
- canonical manifest SHA-256:
  `f36461f55bdc9e8a4dce26bf4ed6c6de9fae5406ffb693a27ef2d958d912be9d`
- checksum repeatability: **PASS**
- input-order reproducibility: **PASS**
- adjustment authority: **PARTIAL**
- Full Dataset created/audited/frozen: **NO / NO / NO**
- Development / Validation / Official OOS: **NOT RUN**

## Follow-on retained-source recovery

The 1,416 unrouted dates were not sent directly to the network. Retained
official CNINFO metadata supplies candidate documents for 1,383 dates, and all
1,421 selected documents already exist as checksum-bound bytes. Strict parsing
finds a unique exact official term signature for 1,311 factor changes and none
for 72. See `R5_FULL_ADJUSTMENT_SOURCE_RECOVERY_V1.md`; authority remains
PARTIAL.
