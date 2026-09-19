# R5 retained-scan SZSE resumption recovery v24 — 2026-09-19

Twenty-nine retained official CNINFO PDFs covering 24 current gaps had fewer
than 60 non-whitespace characters in the prior text cache. The original PDF
bytes were checksum-verified and processed as one bounded offline OCR batch;
no document was downloaded again.

Only two documents produced one strict resumption date. Both original first
pages were rendered and visually checked against the OCR result:

| Security | Suspended at | Resumed at | Official page wording |
|---|---|---|---|
| 000545 | 2011/07/20 09:30 | 2011-09-15 | 公司股票将于2011年9月15日恢复交易 |
| 002033 | 2011/09/09 09:30 | 2011-09-15 | 公司股票将于2011年9月15日开市起复牌 |

The other 27 OCR outputs supplied no unique strict date and remain unaccepted.
OCR alone is not authority; the two accepted facts are bound to the original
official bytes, OCR cache hash and direct page review.

## Intraday execution scope

Resumption date closure is now distinct from opening-session eligibility.
Revalidation preserves explicit `开市` timing as not blocked at the open,
explicit afternoon/13:00 timing as blocked at the open, and leaves unstated
times unknown. A same-date pair of notices for 300399 contains both an opening
resumption and a new half-day halt; the conservative event result is blocked at
the open and the timing conflict is retained rather than erased.

Current retained supplement timing states are 8,184 confirmed open, 59 blocked
at open and 492 unknown, with one conservative same-date conflict. In the full
22,077-event normalized SZSE ledger, including native and unresolved rows, the
counts are 8,185 / 59 / 13,833. The approved daily-opening convention requires
affirmative tradeability, so unknown timing is not executable.

## Result

- exact resumption supplements: **8,737**
- terminal closures: **58**
- unresolved SZSE boundaries: **2,010**
- date conflicts: **0**
- source checksum repeatability: **PASS**
- input-order reproducibility: **PASS**
- authority status: **PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES**

## Immutable artifacts

- OCR scan manifest file SHA-256:
  `3630b80c39ab3e709725597a1fd9a099890e82bb0cff987d9d35f3fbe844263c`
- reviewed acceptance file SHA-256:
  `1c429a6be369006e52004871c7d6d3566556ce2feeceb0508d12a2ca743a6867`
- retained revalidation v36 file SHA-256:
  `812f440f41fa64dc8118932923369afd5d92598f23634aad2c90a0e8d97cc66e`
- v32 authority file SHA-256:
  `275c94706bf60ab6b402c658e27bf2e7cd0921932204d5a44d0a478342e79dcb`
- v32 authority manifest SHA-256:
  `da9be561718a0783112c5ce083d5183e411d5c535407c7c3217da86b89ee8d67`
- normalized events file SHA-256:
  `492bc7fbf574d4c8af5eeadc7f423d75a7be844c12598a9c2a17909090913638`
- unresolved facts file SHA-256:
  `1b75ddd71f72ae9158acce9bec450c6d2d13c997770b0fcc522e5f7683e324bf`

No Full Dataset was created, audited or frozen. Development, Validation and
Official OOS remain unrun. PR #12 remains open and unmerged. The retained-bonus
fractional methodology gate is unchanged.
