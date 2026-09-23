# Product daily-source readiness

Verified 2026-09-22 for U5/U7. This is a new product-source check, not a change to
v1.1 frozen data, provider acceptance, methodology, or Official OOS.
Machine evidence: [bounded probe report](../../.product/evidence/baostock-public-probe-20260922.json).

## Result

**PARTIAL: free public single-security EOD access works; forward acceptance has
not run.** No source permission/payment action is currently required from the user.

Official BaoStock 0.9.4, loaded from its checksum-verified PyPI wheel without
installing into project dependencies, successfully logged into its documented
`public-api.baostock.com:10030` node anonymously. A raw daily query for `sh.600000`
over 2026-09-18 through 2026-09-22 returned two records: 2026-09-18 and 2026-09-21.
OHLC bounds, finite positive prices, nonnegative volume/amount, unadjusted flag 3,
trading-status and ST flag domains passed. Both returned rows were non-ST and
trading normally; suspended/ST securities and other boards were **not tested**.

The response completed at `2026-09-22T07:51:53.022481+00:00`, before the provider's
documented 17:30 daily-bar publication time in the Chinese-market schedule.
Thus September 21 was the latest returned date for this probe security. This
does not prove market-wide completeness or an independent trading-calendar audit.

The first, documented all-A daily endpoint query for 2026-09-21 failed to deliver
a complete SDK response within the 45-second total guard and returned `10002007`
(network receive error). Public login succeeded in both attempts. The second
attempt changed to the smaller per-security endpoint and succeeded. Exactly two
data requests were made; no further retries, denial bypass, VIP key, account
creation, data purchase or continuous worker was used. The SDK receive loop has
no EOF guard; the precise upstream cause of the bulk failure is unestablished.

## Source and use boundaries

- [Official platform/API introduction](https://www.baostock.com/mainContent?file=home.md)
  explicitly describes free access without registration and local storage for
  analysis. It lists daily K-line publication at 17:30 and factors at 18:00.
- [Official daily-update API](https://www.baostock.com/mainContent?file=DailyUpdates.md)
  specifies OHLC, volume in shares, amount in CNY, adjustment flag, trading status
  and isST. Suspension rows are vendor-carried prices with zero volume/amount,
  not executable transactions.
- [Official per-security API](https://www.baostock.com/mainContent?file=stockKData.md)
  supports explicit date bounds and `adjustflag=3` for raw prices.
- [Official package](https://pypi.org/project/baostock/0.9.4/) was released on
  2026-09-21. BSD is the **software** license; it is not a blanket data license.
- [Website disclaimer](https://www.baostock.com/disclaimer), contract V1.0.0,
  disclaims accuracy/availability and reserves website-content rights. The API
  documentation supports the scoped private local-analysis trial; redistribution
  and commercial data rights have not been established. No market rows go to Git,
  a public deployment or published release attachments.

The rendered site retrieves its public documentation with POST `{}` to
`/helpdocs/api/markdown/<document>` and its disclaimer with GET
`/articleMall/api/contract?contract_status=1&contract_type=5`. Exact document bytes,
terms and package metadata are archived privately, with checksums in the report.

[Eastmoney's current legal notice](https://about.eastmoney.com/home/legal) restricts
copying/distribution without written exchange permission; public readability alone
must not qualify it as a new product feed. Historical Tencent/Sina acceptance also
does not establish new-market coverage or redistribution rights. Their previously
accepted frozen histories remain untouched.

## 2026-09-23 product updater checkpoint

Step 1 below is implemented for an explicitly requested, bounded, per-security
raw EOD update. Chrome submitted one `CN-A:SSE:600000` / 2026-09-22 request;
one candidate observation and immutable receipt were written to the separate
product volume. The same job and receipt survived backend restart and browser
reload. Migration 0014 was reversible on the disposable database and additive
on the main database after an off-repo backup. The frozen research archive was
mounted read-only and its checksums and formal study counts did not change.
The browser evidence is stored outside Git under
`product-evidence/v1.2/u5/incremental-raw-receipt-zh-20260923.png`.

This historical catch-up proves ingestion durability, **not** authority for
execution or U7 forward acceptance. Current master, calendar, ST, market rules,
corporate actions and adjustment factors remain unverified for the new date.
Cross-board controls, failure/retry/cancel browser paths, and an after-session
forward receipt remain open. No raw market rows belong in Git.

## Implementation and remaining gates

### Four-board bounded candidate check (2026-09-23)

After Docker Desktop 4.92.0 recovery, persisted job
`164c947d-b8bc-47ab-8c99-193bc0eeddf6` was re-read from the running API.
It requested only 2026-09-22 for `CN-A:SSE:600000` (Main),
`CN-A:SSE:688001` (STAR), `CN-A:SZSE:000001` (Main), and
`CN-A:SZSE:300750` (ChiNext). The job `SUCCEEDED`: three provider requests,
three new observations, one cached observation, four available observations,
and zero unresolved dates. Its configuration SHA-256 is
`0e46b4479471ae5c86da1a694506262d2a52e215b3e1991c7240ae6e1b0b05b2`.
The original receipt/manifests remain on the product volume, not in Git.

All four remain `RAW_CANDIDATE`, **not executable authority**. Current security
master, calendar, ST history, rules and corporate actions are `UNVERIFIED` for
2026; adjustment factors were not requested. The fixed sample does not yet
include current ST or suspension controls. This is historical catch-up, not an
after-user-start forward receipt; no U7 session or simulated fill is inferred.

1. **DONE for the bounded raw candidate path.** A product-owned, user-triggered
   per-security EOD update job uses
   existing BaoStock integration/Decimal records and a supervised timeout. Fetch
   only missing completed dates for the selected securities. The full archive is
   not a prerequisite for this product updater. Keep bulk API disabled until a
   separately bounded diagnosis succeeds.
2. Before promotion, run a small fixed sample spanning SSE Main/STAR and SZSE
   Main/ChiNext plus known current ST and suspension controls. Reconcile current
   master, calendar, status and effective market rules for intended execution.
   Unknown metadata blocks affected execution; missing rows never imply suspension.
3. **DONE for raw candidate receipts; authority promotion remains separate.** Preserve requested-at, response-completed/received-at and immutable first-seen
   timestamps in UTC, exchange trading date separately, SDK/parser/source version,
   request parameters, original fields, response/logical SHA-256 and terms snapshot.
   Append corrected vintages and atomic manifests outside the frozen archive.
   Persist job history/checkpoints/idempotency and access-denial stop state.
4. Start a forward session explicitly, before a genuinely subsequent trading
   session. Wait for its completed EOD data to arrive, create a receipt-bound plan,
   and process only later eligible observations through risk/OMS/accounting.
   The present two historical rows are **integration/backfill evidence only**.

Reuse traps: `scripts/probe_raw_failover.py:tencent_url` and
`scripts/audit_raw_failover.py:normalized` are Pilot-year/date-bound. The old
`scripts/reconcile_sse_cninfo.py:fetch` records `retrieved_at_utc` **before** reading
the response, so it cannot serve as U7 receipt evidence. BaoStockAdapter.daily_bars
currently queries raw and adjusted data separately; preserve raw execution and
separate adjustment lineage rather than silently adding adjusted fills.

Human action becomes necessary only if an intended route returns access denial,
requires unavailable credentials/payment, or no lawful workable source remains
after the bounded alternatives. None was observed in this probe. Cross-board
coverage, incremental durability, new-event receipt and actual forward processing
are still engineering/elapsed-time acceptance work, not completed capabilities.
