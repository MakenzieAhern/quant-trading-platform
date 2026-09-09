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
| `RIGHTS_RELATED_EVENT` | Unsupported; no inferred subscription or cash flow. |
| `SPLIT_OR_SHARE_CHANGE` | Unsupported unless explicit source terms are later available. |
| `UNKNOWN_UNSUPPORTED` | Persist provenance; block accounting and eligibility. |

Incomplete or unsupported events raise a portfolio error rather than silently altering holdings.
Short-position corporate-action accounting is outside this long-only study. Reconciliation fixtures
cover cash and share distributions, but a live known ex-dividend record could not be refreshed during
the 2026-09-09 BaoStock outage. Corporate-action readiness therefore remains PARTIAL.
