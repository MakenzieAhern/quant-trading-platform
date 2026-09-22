# BaoStock Capability Audit

Assessment date: 2026-09-09. SDK inspected: PyPI package 0.8.9, reported SDK `00.8.90`.
The repeatable probe is `backend/scripts/audit_baostock.py`.

## Empirical record

| Capability | Result | Evidence |
|---|---|---|
| `query_all_stock(day=...)` | NOT COMPLETED | Historical snapshot audit was attempted twice on 2026-09-09; the BaoStock TCP service timed out before login. |
| `query_stock_basic` | PARTIAL | SDK exposes `ipoDate`, `outDate`, type and status. Completeness for exited securities is not empirically established. |
| `query_trade_dates` | PARTIAL | API exists and is normalized; complete 2010–2025 response could not be refreshed during this pass. |
| `query_history_k_data_plus` | CONFIRMED | Earlier 2026-09-07 probes returned raw OHLCV/status/ST for 2010 and a 2018 comparison sample. Earliest confirmed date is 2010-01-04; latest confirmed date is in 2018, not a claimed provider maximum. |
| `query_adjust_factor` | PARTIAL | SDK exposes `dividOperateDate`, forward, backward and adjustment factors; the adapter normalizes them, but the live range audit did not complete. |
| `query_dividend_data` | CONFIRMED/PARTIAL | Earlier probes returned dividend fields. Cash, stock and capital-reserve share distributions are normalized; completeness across 2010–2025 is unverified. |
| CSI300 constituents | CONFIRMED | A 2010 historical query returned 300 members on 2026-09-07. |
| CSI500/SSE50 constituents | PARTIAL | APIs exist and are included in the repeatable probe; the full historical range audit did not complete. |
| Index daily data | PARTIAL | Supported through daily-history queries; end-to-end pilot ingestion was blocked by service availability. |

## Historical behavior still unknown

The audit did not establish whether inactive securities reliably appear in every historical
`query_all_stock` snapshot, whether all delisted codes remain queryable, whether renamed symbols
retain complete history, or the coverage endpoints for daily ST/tradeStatus, adjustment factors and
dividends. These are unknown—not assumed absent and not assumed complete.

On 2026-09-09, DNS resolved `www.baostock.com` to `114.94.20.92`, but TCP port 10030 timed out and
both the capability audit and pilot ingestion ended with `BAOSTOCK_LOGIN_FAILED`. Earlier successful
results remain valid evidence, but cannot substitute for the required comprehensive audit.
