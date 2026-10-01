# Product daily-source readiness

Verified 2026-09-22 for U5/U7. This is a new product-source check, not a change to
v1.1 frozen data, provider acceptance, methodology, or Official OOS.
Machine evidence: [bounded probe report](../../.product/evidence/baostock-public-probe-20260922.json).

## Result

**PARTIAL: free public single-security EOD access works; forward acceptance has
not run.** Explicit data-use rights evidence is still needed before an executable
forward feed can be accepted. No permission request, payment or credential action
has been initiated.

On 2026-09-24, the shared rule resolver was tightened to require an explicit
`is_tradeable=True` as well as `is_suspended=False` before returning
`executable=True`. Unknown or false tradeability now fails closed. This is a
software guard, **not** confirmation of a 2026 status authority, licensed feed,
or forward execution. The separate 2026 candidate rules remain
`conservative_no_fill=True`; `RULE_AUTHORITY_2026 = PARTIAL`.

### Written rights clarification needed (unsent)

The [SSE 2026 rule, §5.1.3](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml)
and [SZSE 2026 rule, §5.1.3](https://docs.static.szse.cn/www/lawrules/rule/trade/current/W020260424690713155663.pdf)
do not themselves grant this product a feed-use license. The official
[SSE service page](https://www.sse.com.cn/transparency/services/) lists
`marketservice@sse.com.cn` for market-data licensing questions; the official
[SZSE contact page](https://www.szse.cn/English/about/contactus/index.html)
lists `infoservices@cninfo.com.cn` for market-data authorization. BaoStock's
[official home](https://www.baostock.com/) lists `baostock@163.com` for support.
No inquiry has been sent, no permission inferred, and no commercial purchase
authorized. The exact question for a rights holder/provider is whether its
2026 A-share delayed/EOD feed, including both exchanges, may be stored and
used in a **private single-user local application** to create dated simulated
plans and persistent paper fills, without redistribution or real orders; ask
for the applicable written terms and any upstream exchange authorization.
Until that is documented, candidate receipts remain non-executable.

The [SZSE website legal notice](https://www.szse.cn/application/laws/)
describes noncommercial browsing and downloading of **that website's** content.
The [2026 SZSE Trading Rules, §5.1.3](https://docs.static.szse.cn/www/lawrules/rule/trade/current/W020260424690713155663.pdf)
separately require permission to use exchange trading information. The
website notice does not identify BaoStock's upstream feed or explicitly grant
this application's persistent EOD-plan and simulated-fill use. This is a
scope inference, not a legal determination; keep the rights gate unresolved
until written terms cover the actual source and use. A bounded recheck on
2026-09-24 found no such authorization.

The historical paper-account form and guided research cost hint now explicitly
identify user-entered broker commission as a simulation assumption, not a
verified broker quote. This product-copy correction does not resolve current
broker pricing or the new-market source-rights gap above.

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

The [SSE 2026 Trading Rules, §5.1.3](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/10816482/files/959da0158c65434daa8a43a6e32be7ba.docx)
and [SZSE 2026 Trading Rules, §5.1.3](https://docs.static.szse.cn/www/lawrules/rule/trade/current/W020260424690713155663.pdf)
reserve exchange trading-information use and dissemination to permitted users.
The SZSE rule expressly says that trading information belongs to the exchange
and may not be used or disseminated without permission. The [SZSE website
notice](https://www.szse.cn/application/laws/) permits noncommercial browsing
and downloading of website content, but that does not itself resolve the more
specific trading-information permission or BaoStock's upstream rights. This is
a source-rights gap, **not** a finding that the existing private, bounded trial
was unlawful. Do not substitute an exchange webpage scrape for the candidate
provider or promote BaoStock observations to executable forward authority on
the basis of public readability, SDK licensing, or this website notice alone.

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
on that date. Chrome rendered the [official 603400 SSE PDF](https://static.sse.com.cn/disclosure/listedinfo/announcement/c/new/2026-09-22/603400_20260922_QPNV.pdf)
(announcement 2026-048): it states trading stopped from 2026-09-15 and would
continue suspended at the announcement. WSL retrieval timed out; a scripted
Windows fetch saved only an HTML JavaScript challenge, which was identified and
removed, **not** mislabelled as a PDF checksum. The actual PDF binary has not
been archived/checksummed. The frozen master names are coverage clues, not
2026 effective-dated ST authority.

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
job, manifest hashes and exact raw/normalized checksums. The official 603400
notice corroborates this one suspension control but does **not** promote vendor
ST/status fields generally to official effective-dated authority, establish
current universe/calendar/rules/actions, or satisfy a
post-session-start forward receipt.

### Current exchange trading-rule evidence (2026-09-23)

The [SSE 2026 Trading Rules notice](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/c_20260424_10816482.shtml)
is 上证发〔2026〕41号, published 2026-04-24 and effective **2026-07-06**;
it repeals the 2023 revision on that date. The [SZSE 2026 Trading Rules](https://docs.static.szse.cn/www/lawrules/rule/trade/current/W020260424690713155663.pdf)
(深证上〔2026〕551号, published 2026-04-24) likewise take effect
**2026-07-06** and repeal the 2023 revision. Publication is not the
effective trading date. [SSE's implementation explanation](https://www.sse.com.cn/aboutus/mediacenter/hotandd/c/c_20260424_10816474.shtml)
explicitly changes Main Board risk-warning share price limits from 5% to 10%;
SZSE rule 3.3.13 sets Main Board 10% and ChiNext 20%, with its risk-warning
section no longer specifying a 5% exception. The [SZSE risk-warning guide](https://www.szse.cn/lawrules/service/member/t20260630_621404.html)
also describes the Main Board limit change. SSE STAR and SZSE ChiNext remain
20% in their respective rule text. This is source discovery, **not** accepted
2026 execution authority.

Original official attachments are stored outside Git under
`/home/yuchen/data/product_source_evidence/2026_rules/`. Local save times
below are UTC filesystem timestamps, not independently measured HTTP receipt
times; SHA-256 was rechecked on 2026-09-23 at 17:48 UTC.

| Official attachment | Saved UTC | SHA-256 |
|---|---|---|
| [SSE rules DOCX](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/10816482/files/959da0158c65434daa8a43a6e32be7ba.docx) | 2026-09-23 17:45:31 | `fc922c433438b2636cb631eab25cca405209712acbb6aaded768c45456ff8888` |
| [SSE deferred clauses DOCX](https://www.sse.com.cn/lawandrules/sselawsrules2025/stocks/exchange/c/10816482/files/f6bd756cdd8248f49b7795f62e73237f.docx) | 2026-09-23 17:45:31 | `f4a0d0976a01e3e95f82460170900993824b70d91183e42d09e13ba10a9958c5` |
| [SZSE rules PDF](https://docs.static.szse.cn/www/lawrules/rule/trade/current/W020260424690713155663.pdf) | 2026-09-23 17:45:29 | `9b66f8b0db70f84a25ef1ccb4ee2351001724e408117552d75f6d8993483c586` |

The SSE deferred-clause attachment concerns specified block-trade VWAP and
16:00–17:00 provisions, not an extension of the old 5% Main Board limit.
The historical `cn-a-2010-2025.6` rule version has open-ended 2023 periods
and Main Board ST limit 5%; it is frozen historical input, **not** a valid
2026 product-forward rule version. A read-only diagnostic in the running
backend resolved a hypothetical 2026-09-22 SSE Main ST status to
`cn-a-2010-2025.6:SSE_MAIN-2023-04-10`, limit `0.05`; this is proof of the
gap, not an actual security classification or simulated order. Do not change
its serialized content or silently resolve 2026 sessions with it. A separately
versioned, effective-dated candidate mapping now covers the four boards from
2026-07-06 and requires an injected cost schedule. It deliberately sets
`conservative_no_fill=true` for every rule; it cannot authorize even a normal
paper fill. Historical rule values and frozen files were not edited. Their
`frozenset` order-type JSON serialization was nondeterministic across processes; the shared
serializer now sorts order types, and four independent process checks produced
the same historical model checksum
`28a0123ce3d9ebf522f59f0bf69de8e24d1fb0a7cb9da0a795a8404c535a250b`.
The exact official 2026 rule source and transition have focused tests, but
current master/calendar/ST/suspension/actions/cost authority and executable
status/order constraints still require audit and implementation before any
candidate bar can be promoted. `RULE_AUTHORITY_2026 = PARTIAL`; all existing
candidate receipts remain `execution_eligible=false`.

### Current A-share cost components (2026-09-23)

The [ChinaClear fee catalog](https://www.chinaclear.cn/zdjs/fbzyls/service_tlist.shtml)
currently lists separate Shanghai and Shenzhen schedules updated on
2026-01-01. Both official tables specify ordinary A-share transfer fees of
**0.01‰ on each side** (`0.00001` of turnover), securities stamp duty of
**1‰ on the seller, halved** (`0.0005`), exchange handling fees of
**0.0341‰ on each side**, and regulatory fees of **0.02‰ on each side**.
The [SSE investor fee guide](https://one.sse.com.cn/onething/gptz/) states
the handling and regulatory fees are included in broker commission; adding
them again to the existing commission model would double-count them. The
[SZSE 2026-01 schedule](https://www.szse.cn/marketServices/deal/payFees/)
independently lists the same handling and regulatory rates. The
[tax authority's 2023 notice](https://shanghai.chinatax.gov.cn/zcfw/zcfgk/yhs/202308/t468451.html)
is marked effective and confirms the halving from 2023-08-28.

The two ChinaClear originals are stored outside Git under
`/home/yuchen/data/product_source_evidence/2026_costs/`. These are local save
times in UTC, not independent HTTP receipt timestamps. The archive was
verified as 10-page PDF files and checksummed after download:

| Official schedule | Saved UTC | SHA-256 |
|---|---|---|
| [Shanghai 2026 fee PDF](https://www.chinaclear.cn/zdjs/fbzyls/202512/922adc26c2ff4865930c7fb77688bb8a/files/%E4%B8%8A%E6%B5%B7%E5%B8%82%E5%9C%BA%E8%AF%81%E5%88%B8%E7%99%BB%E8%AE%B0%E7%BB%93%E7%AE%97%E4%B8%9A%E5%8A%A1%E6%94%B6%E8%B4%B9%E5%8F%8A%E4%BB%A3%E6%94%B6%E7%A8%8E%E8%B4%B9%E4%B8%80%E8%A7%88%E8%A1%A8.pdf) | 2026-09-23 18:08:30 | `84a99e563cb8e84e264c88e3bea2df5f4ac50b1e95330417ec30e2b2566d862f` |
| [Shenzhen 2026 fee PDF](https://www.chinaclear.cn/zdjs/fbzyls/202512/a59388fbfa714c5fa546784891a42e30/files/%E6%B7%B1%E5%9C%B3%E5%B8%82%E5%9C%BA%E8%AF%81%E5%88%B8%E7%99%BB%E8%AE%B0%E7%BB%93%E7%AE%97%E4%B8%9A%E5%8A%A1%E6%94%B6%E8%B4%B9%E5%8F%8A%E4%BB%A3%E6%94%B6%E7%A8%8E%E8%B4%B9%E4%B8%80%E8%A7%88%E8%A1%A8.pdf) | 2026-09-23 18:08:22 | `dff4a06ce20e180f4a85ddae138211dcf7dd3246fb84775453cfd21cbaec6573` |

This verifies the current **statutory components for ordinary A-share
auction trades**, not a universal broker commission. The existing `0.0003`
commission and CNY 5 minimum are configurable simulation assumptions, not
rates certified by ChinaClear. `candidate_2026_cn_a_costs` now takes those
assumptions explicitly and returns a separately labeled 2026 candidate cost
schedule; exchange handling and regulatory fees are not charged again on top
of the assumed inclusive brokerage commission. Product-facing brokerage
assumption disclosure and full current execution authority remain `PARTIAL`;
all candidate rules still forbid fills. This does not retroactively certify
or edit the frozen v1.1 historical transfer-fee allowance.

### Bounded current security-master sample (2026-09-23)

The official [SSE stock list](https://www.sse.com.cn/assortment/stock/list/share/)
uses its public `https://query.sse.com.cn/sseQuery/commonQuery.do` endpoint.
Four exact-code requests used `sqlId=COMMON_SSE_CP_GPJCTPZ_GPLB_GP_L`,
`STOCK_CODE` below, `STOCK_TYPE=1` (Main) or `8` (STAR),
`COMPANY_STATUS=2,4,5,7,8`, pagination and the page referer. Each response
contained exactly one matching A-share row with no delisting date. The
[SZSE official stock-list XLSX](https://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=1110&TABKEY=tab1)
contained 2,902 A-share rows (1,494 Main, 1,408 ChiNext) and exactly one row
each for `000001` and `300750`. All originals are outside Git under
`/home/yuchen/data/product_source_evidence/2026_master/`:

| Snapshot | Listed identity / board / listing date | Saved UTC | SHA-256 |
|---|---|---|---|
| `SSE_600000_QUERY_20260923.json` | 浦发银行 / Main / 1999-11-10 | 18:12:09 | `bd2e4c7c9255ce516ab36cf148320419977aaae00e75a207f449dd910b88ab05` |
| `SSE_688001_QUERY_20260923.json` | 华兴源创 / STAR / 2019-07-22 | 18:13:57 | `c58d3146bec9591fd6476a8f04208396c138b9aac95dd8ce5587c55e4e0a92c3` |
| `SSE_688622_QUERY_20260923.json` | *ST禾信 / STAR / 2021-09-13 | 18:14:12 | `11afd2ba67ddf84fc8539f2a32f717d9733d001d2aaa2b9e3519c11b334e75bd` |
| `SSE_603400_QUERY_20260923.json` | 华之杰 / Main / 2025-06-20 | 18:14:22 | `41087920a69b34499b8f5b8adf2124030109ad8a18c15b6aae6ba1bca1202878` |
| `SZSE_CURRENT_LIST_20260923.xlsx` | 000001 平安银行 / Main / 1991-04-03; 300750 宁德时代 / ChiNext / 2018-06-11 | 18:12:20 | `8354521bc2a166d47c0411c6f88ab733b76a90a31d4a45aef61765415cac5110` |
| `SSE_MAIN_CURRENT_20260923.json` | Current Main list: 1,702/1,702 rows, one page | 18:16:37 | `472cb64bd91e598300904f753e1ca17f8a06e331733230256689396911b8293d` |
| `SSE_STAR_CURRENT_20260923.json` | Current STAR list: 618/618 rows, one page | 18:16:48 | `d7057d578631766a47f9a05ea028cf41d7533d9683190c68e26ce6385a251dc1` |

The two SSE current-list responses had no duplicate codes across 2,320 rows;
the four targeted SSE identities agreed with that broader snapshot. Together
with the SZSE XLSX, these sources expose 5,222 listed A-share rows at retrieval.
This is a **current inventory**, not a complete 2026 effective-dated universe:
the exchange requests were separate, no historical delisting/renaming chain
was collected, and current counts must not be projected backward.

The [SSE's 2026-04-29 notice](https://www.sse.com.cn/disclosure/magin/announcement/ssereport/c/c_20260429_10817106.shtml)
explicitly says `688622` became subject to delisting risk warning on
**2026-04-30**. Its archived HTML SHA-256 is
`03e75103555a6211599702c2b261d76bada0bc8655d4a3715ee8ba10dc551a54`
(saved 2026-09-23 18:15:06 UTC). The current list's `*ST` name corroborates
the present label, not a complete effective-dated history. Likewise, `603400`
remains listed in the master while its separate official suspension notice and
vendor row say it was not trading on 2026-09-22. Listing and trading status
must not be conflated.

**Sample identity 6/6 is verified at retrieval, not a complete 2026 point-in-time
master or an as-of-2026-09-22 lifecycle proof.** Targeted changes, delistings,
ST exits/entries and suspensions still require dated evidence for the intended
execution interval. `CURRENT_MASTER_AUTHORITY = PARTIAL`; the raw candidates
remain non-executable. The historical pilot master was not refetched or edited.

### Current exchange calendar schedule (2026-09-23)

The [SSE 2026 closure notice](https://www.sse.com.cn/disclosure/announcement/general/c/c_20251222_10802507.shtml)
(上证公告〔2025〕45号) and [SZSE 2026 closure notice](https://www.szse.cn/disclosure/notice/t20251222_618087.html)
(深证会〔2025〕481号), both dated 2025-12-22, independently list
2026-09-25 through 2026-09-27 as Mid-Autumn closure and 2026-09-28 as
reopening. As of this checkpoint, 2026-09-24 is only a **scheduled** session;
it has not completed or produced an after-start receipt. The old accepted
calendar ends 2025-12-31 and does not prove a complete 2026 session list.
Later exceptional closures or exchange notices still require checking before
the product calendar can become execution authority.

The exchanges' later, dated [SSE notice of 2026-09-17](https://www.sse.com.cn/disclosure/announcement/general/c/c_20260915_10832273.shtml)
(上证公告〔2026〕22号) and [SZSE notice of 2026-09-17](https://www.szse.cn/www/disclosure/notice/general/t20260917_622911.html)
repeat that closure and also list the 2026-10-01 through 2026-10-07 National
Day closure with 2026-10-08 reopening. Their original HTML was saved off Git
at `/home/yuchen/data/product_source_evidence/2026_calendar/`: SSE SHA-256
`779cbf7cc7ab2c4b34db17ceee29e266bc483e075860d8313b85c1d5d0f307bc`
(2026-09-23 18:32:44 UTC); SZSE SHA-256
`7b0c4264d27f4ba14a1904ab31cb3b2b870e4e68d6b8d8c0f6cf4254c1a045a4`
(18:32:45 UTC). These are local save times, not live session receipts.

At 2026-09-24 18:27 UTC, the official SSE notice and SZSE notice were checked
again: both still specify 2026-09-25 through 09-27 as closed and 09-28 as
the scheduled reopening. The next possible after-start completed-session
receipt is therefore no earlier than the 09-28 session's data publication,
and only if lawful source rights and all execution authorities are accepted
first. A scheduled opening is not itself a receipt or forward acceptance.

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

## 2026-10-02 holiday and rights checkpoint

The official [SSE September 17 notice](https://www.sse.com.cn/disclosure/announcement/general/c/c_20260915_10832273.shtml)
and [SZSE annual notice](https://www.szse.cn/disclosure/notice/t20251222_618087.html)
were rechecked on October 2 (Australia/Sydney). Both schedule the A-share
market closed October 1–7, reopening October 8. This is a scheduled reopening,
not an observed session or provider receipt. With no accepted, deliberately
started forward session, a new after-start completed-session EOD receipt cannot
be established during this closure; the next scheduled opportunity is no
earlier than the October 8 session and its later data publication. There was
no new provider request, authority promotion or simulated fill. The written
source-use rights, current master/calendar/ST/actions/rules and durable
post-start receipt gates remain unresolved.
