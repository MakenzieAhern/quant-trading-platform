# v1.2 acceptance ledger

Status vocabulary: PASS (direct evidence), FAIL (observed defect), IN_PROGRESS,
NOT_RUN, EXTERNAL_BLOCKED. Code existence/test count alone never proves a user flow.
This ledger is cumulative; no required row may disappear to manufacture completion.

Baseline 2026-09-22: DESKTOP-3EOROGR, Ubuntu WSL2, Docker 4.92, Chrome (existing
profile), v1.1.0 `f88b5c6`, populated local PostgreSQL. Agent walkthrough only.
Screenshots are local, outside Git:
[before home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/home.png),
[create](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/create-backtest.png),
[research](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/research-loaded.png),
[strategy](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/strategy.png),
[mobile](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/strategy-mobile.png).
Canonical Windows evidence root: `C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2`.

| ID | Required observable acceptance | Implementation/API/page | Tests/evidence | Status |
|---|---|---|---|---|
| M0-ENV | Correct host, clean baseline, published v1.1/main, no competing writer, healthy services | Git/GitHub/Compose | Live commands 2026-09-22; main/tag f88b5c6, PR12 merged | PASS |
| M0-UI | Real populated pages, new-user/empty-DB/service-failure baseline | `/`, legacy create, research, strategy | Before screenshots; fresh origin5174/disposable product_v12_baseline DB; isolated stopped backend reveals untranslated Failed to fetch | PASS |
| M0-REF | Official references and ≤2 layout directions | DESIGN_SYSTEM.md | Six official sources read; Apple rendered Chrome; one chosen layout | PASS |
| U1-START | Clean user → one primary guided action → strategy; skip/reopen guide; returning draft/recent/status | Workbench / | 2026-09-23 real Chrome fresh origin5174 + isolated `product_v12_baseline` (0 initial product jobs, no private archive): primary CTA opened registered strategy; four-mode guide closed with Esc and reopened; named draft `Clean install demo QA` saved, appeared on home and resumed at step 2; after completion home showed exact recent study and dated synthetic data state. Agent walkthrough, not a novice-user study | PASS |
| U1-DEMO | No-private-data install can run clearly marked synthetic demo; all four modes explained | Registry + standalone synthetic experiment | Isolated API exposed historical archive unavailable (`DATASET_NOT_MOUNTED`) and demo available. Chrome completed all four guided steps, created job `fb620f96-591b-48b3-b238-e92be1b41d02` in isolated DB and opened result (+0.39%, −0.04% drawdown, CNY25 costs); synthetic/non-market warning persisted on home, wizard and result, and no executable next-day plan was fabricated. Main DB remained 8 personal jobs and `.research` clean. Temp 8001/5174 servers stopped after QA | PASS |
| U2-STRATEGY | Registered strategies, plain rules/cycle/risk/data/evidence; drafts and saved versions | /strategies, URL-backed detail drawer and named local configuration versions | Chrome exact-string save/restore/reload/Chinese switch and pre-restore backup; drawer direct URL, Back/Forward and return from full strategy detail verified; independent review closed cross-tab overwrite; full frontend suite PASS | PASS |
| U3-WIZARD | Four steps, advanced disclosure, summary, back/save/restore/exit; locale preserves inputs | /research/new four-step form | Chrome synthetic and actual historical submission/result PASS; draft/locale preserved. In-app browser: edited draft triggered the native sidebar exit confirmation, dismiss kept the form and latest value. The shared guard now keeps one listener across edits (focused regression + frontend204/lint/types/build PASS). Browser-tool Back still left the wizard without an observable dialog or guarded `popstate`; genuine Back/Forward cancel/accept proof remains unverified | IN_PROGRESS |
| U3-JOB | Validated actual A-share job; stages/counts; persistent URL; refresh/reopen; idempotent duplicate | /api/experiments; independent durable manager | Chrome job5f26f84f: actual297/297, leave/reopen/reload same ID, historical result; API idempotency and UI lock tests PASS | IN_PROGRESS |
| U3-RECOVER | Real cancellation/retry/interruption; no partial results called success | cancel/retry and durable terminal states | Running cancellation; restart INTERRUPTED; linked retry SUCCEEDED; UI lifecycle pending | IN_PROGRESS |
| U3-ISOLATE | Independent exploration names/store; formal reports/OOS/freeze unchanged, dates labeled inspected | Separate product_research_jobs/rows, readonly archive | No .research diff; frozen hashes unchanged; formal 1 dataset/3 runs/310 trades before-after | IN_PROGRESS |
| U4-RESULT | Return/drawdown/cost/benchmark/limits, null semantics, true records and reasons | Personal result and date-linked holdings/trades, full-precision toggle | Chrome demo+historical results agree with exact APIs; real fill/snapshot2031-04-14 linked; source unavailable remains N/A; U4 tests/review PASS | PASS |
| U4-COMPARE | Reopen/compare 2–3; six config differences indicated | /experiments/compare?ids= | Chrome three actual runs, six conditions, exact fraction display and refresh preserving URL/results; comparison tests and independent review PASS; `u4/compare-three-results-en-dark-1024.png` | PASS |
| U4-EXPORT | Metadata report and formula-safe CSV | Server-streamed export, automatic download and persistent prepared-file link | Injection/precision/API tests PASS; actual30021-byte historical JSON HTTP200. Chrome and in-app browser prepared the expected report blob and fallback link, but neither auto-click nor user-activated fallback produced a browser download event; no file appeared in Windows Downloads. A 2026-09-23 direct-attachment control was blocked by the browser security check (`net::ERR_BLOCKED_BY_CLIENT`); no bypass attempted. Artifact completion remains unverified | IN_PROGRESS |
| U5-MARKET | Search/watchlist/raw-adjusted/date/source view | /api/markets and /markets deployed0013 | 20 backend/14 frontend focused tests; independent review PASS; Chrome000001 raw22.45/HFQ874.904325432379995/suspension2010-03-01; watchlist persists fresh tab; dialog dates/locale/Esc;390+1280 no page overflow | PASS |
| U5-UPDATE | Incremental update/gaps/retry/history with source/license/rules/limits; no archive refetch | /data and /api/market-updates; separate product cache and migration0014 | Real Chrome one-security/one-date job `3b729cf9` succeeded and survived restart/reload. Four-board job `164c947d` had 3 new + 1 cached candidates. Targeted control retry `ed796871` added two 2026-09-22 vendor candidates: 688622 isST=1; 603400 suspended with blank raw turnover normalized to zero, never executable. Chrome visually confirmed official SSE 603400 suspension notice; binary checksum unavailable. Official 2026 exchange rule transition is mapped in a separate candidate model with no fills and focused tests; execution authority remains false. Failure/retry browser and full 2026 authority remain | IN_PROGRESS |
| U6-PLAN | Real candidates/targets/quantities/cash/reasons/rejections; as-of/snapshot/version; insufficiency/staleness | Persisted result preview and independent audited historical paper account | Historical job `d9f27183` completed 293/293; preview 2011-03-22→23 had 32 candidates, 5 risk rejections. Independent account `d7044a3c` generated 20 risk decisions/orders and 6 fills through the paper runtime; future-data plan and actual forward receipt remain pending | IN_PROGRESS |
| U7-MODES | Three isolated account modes, start/pause/stop/risk/ledger | Synthetic demo + distinct audited historical replay with durable pause/resume; forward not implemented | Chrome historical account `4b64380f` started, paused on 2011-03-09, resumed and stopped 2011-03-23; 20 orders, 6 fills, equity99964.8134. Full isolated backend956/frontend188 tests PASS. Forward mode remains | IN_PROGRESS |
| U7-RECOVER | Socket disconnect/reconnect + backend restart don't fake/duplicate fills | Persisted paused state, deterministic source replay to checked cursor, then append-only continuation | Chrome `4b64380f` stayed PAUSED with 19 events after actual backend restart and WebSocket reconnection; resumed account had 134 non-status events identical to uninterrupted `d7044a3c` (142 vs 138 total, four pause/resume status events). Separate actual mid-run restart left `07d72259` INTERRUPTED at sequence 22 with zero orders/fills and no auto-resume; browser explains retry. Full recovery matrix remains | IN_PROGRESS |
| U7-FORWARD | Lawful source + completed real session data arriving after user session start; receipt times/plan/simulation | Public-source candidate assessed, forward session not implemented | Historical probe is not forward evidence; real after-start arrival still required. Current SSE/SZSE Trading Rules §5.1.3 require permission for exchange trading-information use; BaoStock's public SDK and website access do not establish upstream/product execution rights (see SOURCE_READINESS). | NOT_RUN |
| U8-I18N | One tree; translated important UI/error/help/a11y; switching retains config/date | Shared i18n for legacy create, paper ledger and typed shared load errors | Chrome real historical account shows translated signal, order, fill and risk labels; legacy create form is Chinese, and switching to English retained exact entered capital `123456.789`. Interrupted account has Chinese recovery help; nonexistent dataset has Chinese not-found guidance and preserves raw diagnostic under audit disclosure. The historical result warning now explains inspected vs unseen data in plain Chinese/English; both rendered in the in-app browser on 2026-09-23, with frontend204/lint/type/build PASS. Remaining pages, other server-supplied errors/help/a11y matrix pending | IN_PROGRESS |
| U8-SETTINGS | System/manual themes, language/motion/market colors/data preferences; explanatory help | Shared safe presentation storage and settings | Storage-denied/quota/locale tests PASS. Chrome dark/zh retained; motion-off, green-up and adjusted-view selections persisted after reload, and a real market detail opened in adjusted view. Original system-motion/red-up/raw preferences restored. Bilingual help explains four modes and key concepts | PASS |
| UX-DETAIL | Drawer keeps filters/scroll, Esc/Tab/back/trigger focus, URL | Shared navigation and native strategy/market dialogs with URL-fragment history; market fragment names exact dataset/security | Chrome strategy Back/Forward/direct URL and Tab/Esc PASS. Chrome market search page 21–40 with SSE filter: Back closed detail in place, Forward reopened, scrollY remained 295, trigger focus returned; direct URL reload resolved exact 600025, copied direct URL resolved watchlisted 000001 and closed in place; watchlist Back/Esc restored focus, Tab remained inside dialog; unavailable source showed actionable Chinese alert. Chrome 390×844 zh/en dark: document width375, modal width351, no page overflow; local table scroll hint visible; original locale/viewport restored. Frontend202/lint/types/build and PR30 backend/frontend/compose CI PASS. Broader mobile/filter-scroll matrix still open | IN_PROGRESS |
| UX-COMMAND | Safe Ctrl/Cmd+K + visible entry searches pages/strategy/studies/watchlist/help | Bounded server study/watchlist search, local pages/registered strategies/help | Chrome Ctrl+K, visible entry, server-filtered saved study, watchlist result, help search/navigation and one-Escape close with focus restoration PASS; Windows shortcut hint corrected. Frontend194, lint/type/build PASS; bounded search tests PASS | PASS |
| UX-VIEWS | Saved filters/chips/sort/columns/table-detail/task center | `/tasks` uses bounded saved research/update APIs; `/experiments` applies server-wide search/status/mode/sort before pagination, stores one optional local view, and retains temporary filters in the list history entry | Chrome zh/en task center linked to exact saved study/update receipt. Saved research view survived reload. On 2026-09-23 Chrome 390×844 task center and research list had document width 375, no page overflow, visible local table-scroll hint. A temporary `M1` search was lost after detail/Back; history-entry fix then retained the unsaved query and five matching results on the same path. Original filter and viewport were reset. Focused28/full frontend203, lint/type/build PASS. Broader matrix remains | IN_PROGRESS |
| UX-CHART | Exact hover/legend/benchmark/date range/equity-drawdown-trade link/table; bounded loading | SVG exact data + linked experiment collections | Chrome selected-date trade/holdings agrees; full summary unaffected; keyboard/hover/large-page matrix pending | IN_PROGRESS |
| UX-ERROR | No data/permission/offline/timeout/no match/no trades have next step | Shared load panel distinguishes typed 401/403/404/408 and offline TypeError; raw diagnostic behind disclosure | Chrome real 404 dataset offered safe workbench exit; timeout Chinese component test PASS. Offline, permission and remaining empty-state browser matrix not run | IN_PROGRESS |
| QA-VISUAL | 1440×900,1280×800,1024×768,390×844; two themes/locales; key 200% zoom | Neutral shell and product pages | Home1440 and mobile390 basic checks. On 2026-09-23 the actual historical result page in the in-app browser had document widths 1425/1265/1009/375 at viewports 1440/1280/1024/390 respectively, with no page-level overflow; Chinese light at 390 and English system-dark at the other widths were visually inspected. The browser did not apply Ctrl+plus zoom, so 200% and the cross-page/theme/locale matrix remain unverified. Agent walkthrough, not a user test | IN_PROGRESS |
| QA-A11Y | Keyboard/focus/semantic dialogs/live status/reduced motion/AA contrast+targets | Pending | Measured audits + agent keyboard walk | NOT_RUN |
| QA-PERF | Immediate feedback; measured local interaction p95 target≤200ms; bounded charts/tables | Research archive and result/compare routes loaded on demand; initial JS entry chunk 549.12→409.17 kB minified (169.44→129.31 kB gzip) | Vite build and real Chrome direct reload of historical result/data lineage PASS; cold/warm interaction p95 and large-table audit not yet measured | IN_PROGRESS |
| QA-ENGINE | Decimal/server validation/idempotency/task isolation; same financial path | Existing financial path + independent queue | 862 backend tests; actual 2011 exploratory run completed; synthetic clearly separated | IN_PROGRESS |
| QA-REVIEW | Implement→browser review→fix→recheck; independent read-only review resolved | Independent backend+frontend code/test review | Reported races/idempotency/format/routing defects corrected; final browser repeat pending | IN_PROGRESS |
| QA-RELEASE | Full backend/frontend/lint/types/build/migrations/durability/CI/compatibility | Incremental suites and reversible migrations | 2026-09-23 isolated `quant_test_v12_u5` upgraded 0014→0015 only; full backend959 PASS/one optional unmounted-archive skip, frontend198 PASS, Ruff/mypy/ESLint/TS/build PASS. PR26 backend/frontend/compose CI PASS. Formal DB and `.research` not modified by these tests. Remaining full product gates pending | IN_PROGRESS |
| M5-DELIVERY | New/old screenshots + key recordings, bilingual manual/demo/start/recovery/rollback, mode freshness/limits | Pending | All links validated before release | NOT_RUN |
| M5-PUBLISH | Small feature PRs reviewed+CI+browser→merge; v1.2.0 only after all required rows pass | feature/product-experience-v1.2 | v1.1 remains immutable | NOT_RUN |

PRODUCT_GOAL_COMPLETE = NO. Remaining required work is the full non-PASS set above.

## 2026-09-23 15:16 UTC unplanned backend interruption and localized recovery

The agent started historical account `07d72259-4491-4ad6-8ebc-4c8a2a8ae156`
and restarted the real backend while it was RUNNING. After the restart the
server reported `INTERRUPTED`, completed market date 2011-03-11, last sequence
22, zero orders and zero fills; a later read returned the same sequence and
counts. It did not auto-resume. Real Chrome showed the interruption in Chinese,
an explicit new-session action, and a collapsed raw English diagnostic retained
for audit. This is a fail-closed historical replay check, not proof of complete
crash recovery or a forward market session. The frontend suite passed 191 tests,
lint, typecheck and production build. Agent walkthrough only.

## 2026-09-23 15:21 UTC shared load-error review

The shared resource hook now preserves typed `ApiError` information instead of
discarding it into a raw English string. One shared panel distinguishes
offline, timeout, denied and missing-record states in both locales, retains
the original diagnostic behind a disclosure, and offers reload or workbench
navigation. Chrome opened a genuinely nonexistent research dataset and showed
Chinese not-found guidance and a working `/` exit. A focused timeout test and
the complete 193-test frontend suite, lint, typecheck and build passed. This
does not validate the remaining offline/permission/empty-state browser matrix.

## 2026-09-23 15:29 UTC bounded current ST/suspension control

The first two-security job failed closed on a real BaoStock suspended row with
empty volume/amount strings. A targeted direct provider inspection established
the exact shape. Parser v2 accepts only the explicit suspended/both-empty
case and leaves raw fields immutable; active or half-empty rows still fail.
Focused isolated tests passed 50/50; full isolated backend 958 PASS with one
optional archive test skipped, Ruff/format/mypy PASS. After restarting only the idle backend,
retry job `ed796871-4ce4-4cf3-b7f0-2223e636bb75` completed two requests,
two candidate observations and zero unresolved dates. `CN-A:SSE:603400` is
vendor-suspended with zero normalized turnover; `CN-A:SSE:688622` has vendor
ST flag 1. Neither is execution-eligible. The parser-label caveat, immutable
manifest checksums and remaining official-source gaps are in SOURCE_READINESS.
The Chrome report export produced a prepared blob/link but no verified file
download event or artifact; U4-EXPORT remains IN_PROGRESS.

## 2026-09-23 14:57 UTC paper pause/restart/resume checkpoint

Chrome created audited historical account `4b64380f-85ff-4696-a710-a8d92725bc0b`
with an explicitly edited 2011-03-23 end date; the server persisted that date.
The agent started it, paused after completed session 2011-03-09 (19 ledger
events, no fills), restarted the real backend, and observed the same PAUSED
state, cursor, ledger count and connected browser. Resume completed on
2011-03-23. Against uninterrupted account `d7044a3c-7ef3-46ba-accd-197a6d40505e`,
all 134 non-status event type/payload pairs match in order; both have 20 orders,
six fills and equity `99964.8134`. The resumed ledger adds exactly four
pause/resume status events. This is historical replay, not a forward market
receipt. The Chrome review also found untranslated order enum values; U8 remains
FAIL. Native date inputs in paper, guided research, market updates, collections
and market detail now handle `input` events; related frontend tests and the
actual Chrome paper form submission passed.

Main database migration0015 followed a verified off-Git pre-migration backup
`/home/yuchen/data/backups/quant_platform_pre0015_20260923T1443Z.dump`
(SHA-256 `0f751cb54be0d939fdd76d4ed01b5f6c75591fd9f59d634ca10cbcebd3effd57`).
A separate disposable PostgreSQL instance passed upgrade0014→0015,
downgrade0015→0014, re-upgrade and `alembic check`. Do not downgrade the live
database while it contains PAUSED/PAUSING rows. No frozen research files changed.

## 2026-09-23 15:08 UTC focused Chinese/English closure

The Chrome review of the completed historical paper account exposed raw
`BUY / LIMIT`, `CANCELLED` and `proposal approved` values in Chinese. Paper
signal/order/fill directions, order types/statuses and known risk reasons and
diagnostics now use the current locale while persisted event payloads remain
unchanged. Chrome reloaded the same 20-order/six-fill account and showed
`买入 / 限价单`, `已成交`/`已取消`, `风控通过` and Chinese diagnostic text. The legacy
`/backtests/new` form, previously wholly English, now renders Chinese labels,
validation and help. Chrome language switching retained the exact typed
capital `123456.789`. This is an agent walkthrough, not a real new-user test;
untranslated server-supplied errors and the wider U8 matrix are still open.

## 2026-09-22 09:27 UTC cached-market browser closure

`u5/markets-zh-light-390-context-fixed.png` and `u5/markets-zh-dark-1280.png`
under the evidence root show the actual Chrome UI. Parent and detail both wrote
the topbar data context: opening showed an experiment-style requested date and
closing erased the selected archive. A regression failed on this mismatch;
the page now owns the context alone, retaining archive2025-12-31 (or explicitly
synthetic2031-12-31) through open/close. Requested dates remain in the detail.
Board/exchange names are translated without changing their API identifiers.

The prior U2 cross-tab draft overwrite is resolved with independently retained
per-page recovery slots. Exact saved version and restore behavior was checked in
Chrome; the three-way comparison was also refreshed in Chrome. These checks are
agent walkthroughs, not real new-user research.

## 2026-09-23 00:52 UTC incremental candidate checkpoint

Migration0014 was checked with upgrade/downgrade/upgrade and Alembic check on the
isolated test DB. The main database received the additive migration after a
validated off-repo backup. Backend949/frontend182 tests, Ruff, strict mypy,
ESLint, TypeScript and build passed. Chrome submitted exactly one explicit
BaoStock request for `CN-A:SSE:600000` on 2026-09-22. Job
`3b729cf9-32e2-4945-9a81-05b08685fc6e` completed one provider request with
one raw candidate observation and receipt `4eb082e8-4b06-4a63-8197-acfa0f6073d1`.
Manifest SHA-256 `5db56749ffe589cc34184ea741739cddce57eaec0b8ea150a770b46f28924dff`
matches the independent product volume file. The browser reopened that same
task after backend restart with unchanged counts; the screenshot is
`u5/incremental-raw-receipt-zh-20260923.png` outside Git. Formal ledger counts
remain 1 dataset/3 runs/310 trades and frozen manifest/freeze hashes unchanged.
This is a historical candidate update, not trading authority or a forward
simulation receipt after user-session start. U6/U7 and the full matrix remain.

## 2026-09-23 U6 historical preview checkpoint

The actual historical exploratory job `d9f27183-a9a1-4f34-aef4-eba439f53374`
finished 293/293 accepted sessions through 2011-03-22. Its saved preview uses
only completed-session raw closes and the accepted calendar's next date,
2011-03-23. Replayed cash `45539.94836`, equity `104666.94836`, and 16 holdings
exactly match the persisted final holdings endpoint. The preview records 32
candidates and five risk rejections; approved-buy cash `44221.44166` is an
estimate at the completed close, not an executable next-open amount. No paper
order was submitted. An insufficient-warmup test produces no usable plan.

Chrome rendered the real result and plan in Chinese and English. At 390×844,
the whole page has no horizontal overflow; the candidate table scrolls locally
with an explicit bilingual hint. Agent screenshots (not real-user evidence) are
outside Git at `u6/plan-zh-dark-desktop.png` and
`u6/plan-en-dark-mobile-390.png`. This is U6 replay preview evidence, **not**
completion of the independent U7 account, genuinely new-market forward mode,
or U6 submission to a simulated account.
