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
2026; adjustment factors were not requested. At this checkpoint the fixed
sample did not include current ST or suspension controls. This is historical catch-up, not an
after-user-start forward receipt; no U7 session or simulated fill is inferred.

### Targeted ST and suspension controls (2026-09-23)

Two additional securities from the existing 2025 archive master were requested
only for 2026-09-22: `CN-A:SSE:688622` (STAR, source-observed `*ST禾信`) and
`CN-A:SSE:603400` (Main Board, `华之杰`). The [official SSE announcement
catalog](https://www.sse.com.cn/disclosure/listedinfo/announcement/index.shtml)
indexed the former with the `*ST` name and a 603400 suspension-progress notice
on that date. Direct access to the candidate 603400 SSE PDF timed out from this
machine; its effective suspension dates have **not** been accepted from search
snippets. The frozen master names are coverage clues, not 2026 effective-dated
authority.

Initial job `0eecbddb-4960-4a63-bf9a-505e9a5af884` failed closed with
`INVALID_PROVIDER_RESPONSE`. A single targeted BaoStock SDK inspection found
`sh.603400` returned `tradestatus=0`, carried price `54.6700`, and empty
`volume`/`amount` strings. Parser v2 normalizes **only both empty fields on an
explicit suspended row** to numeric zero; active rows, half-empty rows and
nonzero suspended transactions still fail. Raw provider fields remain in the
immutable receipt and `execution_eligible=false`. Focused isolated tests: 50
PASS, Ruff and formatting PASS.

Retry job `ed796871-4ce4-4cf3-b7f0-2223e636bb75` succeeded with two new
observations and zero unresolved dates. 603400 is `VENDOR_SUSPENDED`, zero
normalized volume/amount, vendor `isST=0`; 688622 is `RAW_CANDIDATE`, vendor
`isST=1`, trading status 1. Their manifest SHA-256 values are respectively
`e117d2f313ea1579351c235e44af81c99bb5ef46a3a627a0329505c4c4d1a893`
and `c12aa42bb94898921f64f4eba687687f17dc374cc06299c13965da2ad1cd82b4`.
The raw receipt timestamps are UTC in the API payload; some local PowerShell
JSON views convert them to Australia/Sydney time for display.

Provenance caveat: these two append-only retry receipts carry the original
`product-baostock-raw-v1` parser label because the live normalization fix ran
before its version token was advanced. Do not relabel or rewrite those receipts.
The v2 token applies to subsequent receipts; these two are identified by their
job, manifest hashes and exact raw/normalized checksums. This bounded control
check does **not** promote vendor ST/status fields to official effective-dated
authority, establish current universe/calendar/rules/actions, or satisfy a
post-session-start forward receipt.

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
