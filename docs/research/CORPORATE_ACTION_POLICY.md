# Corporate Action Policy

## Separate price and accounting paths

Adjusted close (`adjustflag=2`) is used only for factor features. Raw, unadjusted OHLC
(`adjustflag=3`) remains the execution and mark source. Adjustment factors never imply a cash flow.

BaoStock dividend rows are hashed and normalized into immutable events. Supported fields are
announcement date when present, record date, ex/operation date, cash payment date, stock-listing
date, pre-tax cash per share, stock-distribution ratio and capital-reserve-to-stock ratio. Missing
source fields remain null.

| Normalized event | Portfolio treatment |
|---|---|
| `CASH_DIVIDEND` | Apply cash per share only when the economic amount and ex-date are complete. |
| `STOCK_DIVIDEND` | Increase long quantity and reduce per-share cost basis by the exact supplied ratio. |
| `BONUS_SHARE` | Same share/cost-basis transformation, preserving its distinct source type. |
| `RIGHTS_RELATED_EVENT` | `CN_A_RIGHTS_ISSUE_POLICY_V1`: decline subscription only for a verified ordinary non-tradable entitlement. |
| `SPLIT_OR_SHARE_CHANGE` | Unsupported unless explicit source terms are later available. |
| `MERGER_REORGANIZATION` | Unsupported; preserve successor/election evidence, never map to a no-effect rights event. |
| `UNKNOWN_UNSUPPORTED` | Persist provenance; block accounting and eligibility. |

Incomplete or unsupported events raise a portfolio error rather than silently altering holdings.
Short-position corporate-action accounting is outside this long-only study. The current BaoStock
endpoint recovered in the preceding checkpoint; dividend-only responses still do not establish
rights or full corporate-action coverage. Corporate-action readiness remains PARTIAL.

## Human-approved rights convention

`CN_A_RIGHTS_ISSUE_POLICY_V1` / `DECLINE_SUBSCRIPTION` is a predeclared research assumption,
not a profitability choice. It applies to later Development/Validation/OOS only after separate
stage authorization. No study is authorized by this policy.

The immutable `CorporateAction` captures the event independently of portfolio participation.
Rights fields retain announcement, record, ex/effective dates, subscription window, payment
deadline (date precision, no invented intraday time), positive subscription price and ratio,
eligible share basis, optional new-share listing, source document/URL/version/document hash,
UTC retrieval time and a derived event checksum. Unknown fields remain null. Source total
company capital must not substitute for the eligible A-share base. Later listing facts belong
to their later source availability, not an earlier ex-date record. The rights inventory is
explicitly not admitted as a full point-in-time event ledger.

For a supported event, holdings Q, cash C and historical acquisition basis B remain unchanged
through subscription and lapse. No entitlement asset, borrowing, capital injection, cash
reservation, subscription Order/Fill, additional shares or compensation is created. Actual
raw/unadjusted marks reflect price impact; the engine does not restore a theoretical ex-rights
value. Adjustment factors/adjusted prices remain feature-only and never enter portfolio cash
or share accounting. Rights do not remove the underlying security from the historical universe.

Standard status is explicit, never the default for a missing variant. Tradable rights, automatic
compensation, mandatory conversion, unusual instruments, incomplete or contradictory terms
fail with `RIGHTS_EVENT_UNSUPPORTED_VARIANT`, including when no position is held. A missing
listing date alone is not a fabricated listing or a subscription accounting requirement.

## Deterministic session precedence

The point-in-time master/lifecycle and accepted calendar/status/rules supply the session.
All session actions are validated before any corporate-action mutation, including unsupported
structural events. Pre-open accounting order is: cash dividend on existing shares, stock
dividend, bonus shares, then declined rights; exact event content breaks same-type ties.
Structural split/merger/unknown events fail closed, not an invented ordering-dependent payout.
Then pending ordinary orders face the existing independent execution/suspension gate, raw
OPEN execution if eligible, raw CLOSE marks, and completed-session strategy observation.
The existing corporate-action opening-uncertainty guard remains unchanged; it is not a
whole-security universe exclusion. Subscription and lapse schedule no portfolio transactions.
No future listing date changes eligibility before the accepted lifecycle says it can.

## Acceptance boundary

Event model/accounting/replay engineering PASS does not certify the full historical inventory.
See `RIGHTS_ISSUE_POLICY_CHECKPOINT.md` and `RIGHTS_ISSUE_SOURCE_REVIEW.json` for the current
148-event inventory, four-source sample, unresolved evidence and the exact Section 8 stop.
R4 v2 remains PASS with **R4_REAL_DATA_FILL_COUNT = 0**: it proves orchestration, replay,
no-look-ahead and API/UI parity, not real historical filled-trade corporate-action accounting.
The focused synthetic execution/portfolio tests are the current fill-path engineering evidence.
No strategy was changed to generate fills; no R4 replay or profitability inspection was performed.

Readiness is measured using four explicit counts: securities queried over the declared period,
source rows returned, complete economically actionable events, and unsupported/incomplete events.
It also records the number of independently reconciled ex-dates. Coverage remains PARTIAL until the
2010–2025 provider range is reachable and these denominators are frozen; adjusted-price availability
does not raise the corporate-action score.
