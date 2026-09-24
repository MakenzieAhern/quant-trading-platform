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
| U3-WIZARD | Four steps, advanced disclosure, summary, back/save/restore/exit; locale preserves inputs | /research/new four-step form | Chrome synthetic and actual historical submission/result PASS; draft/locale preserved. Real Chrome 153 on 2026-09-23 reproduced dirty Back silently leaving despite the sidebar guard. The shared router now runs the same guard before route updates: a native dialog on Back, dismiss retained the exact edited name and step, accept reached home, and Forward restored the exact draft and step without a second dialog. A regression also catches duplicate prompts from the App and shell location readers. Focused navigation 7/7, full frontend 208, lint/type/build PASS. Agent walkthrough, not a novice-user study | PASS |
| U3-JOB | Validated actual A-share job; stages/counts; persistent URL; refresh/reopen; idempotent duplicate | /api/experiments; independent durable manager | Live historical job `5f26f84f` remains SUCCEEDED 297/297 and a fresh Chrome context reopened its saved result URL. In a separate tmpfs test DB, the actual Chrome four-step synthetic wizard double-click sent one POST and persisted one job; resending the saved key/config from a fresh client returned the same ID with the DB still at one job. Existing backend concurrent-key/conflict test and frontend lock test cover the shared path. Synthetic result is labeled non-market; details below | PASS |
| U3-RECOVER | Real cancellation/retry/interruption; no partial results called success | cancel/retry and durable terminal states | Isolated cancellation, genuine FAILED terminal, controlled restart, and non-graceful SIGKILL recovery all verified. The crash left parent `77354e81` RUNNING 60/1212 with zero result rows; startup reconciled it to INTERRUPTED with HTTP409 result and a truthful Chrome warning. One linked child `52b76f45` completed 1212/1212, with 4108 rows only on the child and identical configuration SHA; two repeated parent retries reopened that child. The separate missing-partition FAILED path displayed specific bilingual integrity guidance and never yielded partial results. Details/screenshots below; this is not whole-machine power-loss or U7 forward-paper evidence | PASS |
| U3-ISOLATE | Independent exploration names/store; formal reports/OOS/freeze unchanged, dates labeled inspected | Separate product_research_jobs/rows, readonly archive | No .research diff; frozen hashes unchanged; formal 1 dataset/3 runs/310 trades before-after | IN_PROGRESS |
| U4-RESULT | Return/drawdown/cost/benchmark/limits, null semantics, true records and reasons | Personal result and date-linked holdings/trades, full-precision toggle | Chrome demo+historical results agree with exact APIs; real fill/snapshot2031-04-14 linked; source unavailable remains N/A; U4 tests/review PASS | PASS |
| U4-COMPARE | Reopen/compare 2–3; six config differences indicated | /experiments/compare?ids= | Chrome three actual runs, six conditions, exact fraction display and refresh preserving URL/results; comparison tests and independent review PASS; `u4/compare-three-results-en-dark-1024.png` | PASS |
| U4-EXPORT | Metadata report and formula-safe CSV | Server-streamed export, automatic download and persistent prepared-file link | Injection/precision/API tests PASS, including CSV formula-prefix escaping. On 2026-09-23 21:09 UTC isolated real Chrome 153 with `acceptDownloads` at the documented `http://localhost:5173` origin emitted successful download events for historical job `d9f27183`: trades CSV 29,316 bytes and metadata JSON 258,223 bytes, with expected filenames and `download.failure() = null`; JSON began with report metadata and exact job ID. Earlier in-app-browser download suppression remains an environment-specific observation, not a failed Chrome export. Agent walkthrough, not a real-user study | PASS |
| U5-MARKET | Search/watchlist/raw-adjusted/date/source view | /api/markets and /markets deployed0013 | 20 backend/14 frontend focused tests; independent review PASS; Chrome000001 raw22.45/HFQ874.904325432379995/suspension2010-03-01; watchlist persists fresh tab; dialog dates/locale/Esc;390+1280 no page overflow | PASS |
| U5-UPDATE | Incremental update/gaps/retry/history with source/license/rules/limits; no archive refetch | /data and /api/market-updates; separate product cache and migration0014/0016 | Real Chrome one-security/one-date job `3b729cf9` succeeded and survived restart/reload. Four-board job `164c947d` had 3 new + 1 cached candidates. Targeted control retry `ed796871` added two 2026-09-22 vendor candidates: 688622 isST=1; 603400 suspended with blank raw turnover normalized to zero, never executable. On 2026-09-24 real Chrome reopened the existing successful child from failed parent `0eecbddb`; live jobs/receipts/observations stayed 4/6/6, with one child. Separate candidate 2026 rules still authorize no fills. Cancellation browser matrix and full 2026 source authority remain | IN_PROGRESS |
| U6-PLAN | Real candidates/targets/quantities/cash/reasons/rejections; as-of/snapshot/version; insufficiency/staleness | Persisted result preview and independent audited historical paper account | Historical job `d9f27183` completed 293/293; preview 2011-03-22→23 had 32 candidates, 5 risk rejections. Independent account `d7044a3c` generated 20 risk decisions/orders and 6 fills through the paper runtime; future-data plan and actual forward receipt remain pending | IN_PROGRESS |
| U7-MODES | Three isolated account modes, start/pause/stop/risk/ledger | Synthetic demo + distinct audited historical replay with durable pause/resume; forward not implemented | Chrome previously verified account `4b64380f` with 20 orders/six fills, but that post-backup account is now absent after the 2026-09-23 database incident. The older uninterrupted account `d7044a3c` was restored from a verified backup. Forward mode remains unimplemented | FAIL |
| U7-RECOVER | Socket disconnect/reconnect + backend restart don't fake/duplicate fills | Persisted paused state, deterministic source replay to checked cursor, then append-only continuation | Prior Chrome restart/resume observations for `4b64380f` and interrupted `07d72259` are retained as historical QA evidence, not current persistence proof: both post-backup ledgers are absent from the live DB. No synthetic reconstruction is accepted. On 2026-09-23 actual Chrome 153 injected one snapshot HTTP503 for restored stopped historical account `d7044a3c`: the page recovered via one WebSocket reconnect and a second authoritative REST snapshot with no alert; HTTP403 stopped after one request with permission guidance; persistent503 stopped after four total requests. Live counts paper5/events417/jobs8 unchanged. Focused18/full215 frontend tests, lint/type/build and [CI35933791233](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35933791233) backend/frontend/compose PASS; bounded retry and no stale-event ledger mutation have unit coverage. Full restart/forward recovery matrix and lost ledgers remain | FAIL |
| U7-FORWARD | Lawful source + completed real session data arriving after user session start; receipt times/plan/simulation | Public-source candidate assessed, forward session not implemented | Historical probe is not forward evidence; real after-start arrival still required. Current SSE/SZSE Trading Rules §5.1.3 require permission for exchange trading-information use; BaoStock's public SDK and website access do not establish upstream/product execution rights (see SOURCE_READINESS). | NOT_RUN |
| U8-I18N | One tree; translated important UI/error/help/a11y; switching retains config/date | Shared i18n for legacy create/detail, paper ledger and typed shared load errors | Chrome real historical account shows translated signal, order, fill and risk labels; legacy create form is Chinese, and switching to English retained exact entered capital `123456.789`. Interrupted account has Chinese recovery help; nonexistent dataset has Chinese not-found guidance and preserves raw diagnostic under audit disclosure. The historical result warning explains inspected vs unseen data in both languages. On 2026-09-23, the in-app browser switched a persisted legacy success run EN→ZH→EN with exact Decimal strings unchanged. A later live result exposed raw `CORPORATE_ACTION_OPENING_UNCERTAINTY` as an unexplained reason; shared code mapping now explains it and the sibling non-orderable rejection in EN/ZH, with the original code still behind technical details. Chrome EN/ZH on two persisted synthetic jobs now shows a truthful synthetic equal-weight benchmark label in both result and comparison, without exposing `SYNTHETIC_EQUAL_WEIGHT` in the page; focused31/full213 frontend tests, lint/type/build and PR32 [CI35932877381](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35932877381) backend/frontend/compose PASS. Remaining pages, other server-supplied errors/help/a11y matrix pending | IN_PROGRESS |
| U8-SETTINGS | System/manual themes, language/motion/market colors/data preferences; explanatory help | Shared safe presentation storage and settings | Storage-denied/quota/locale tests PASS. Chrome dark/zh retained; motion-off, green-up and adjusted-view selections persisted after reload, and a real market detail opened in adjusted view. Original system-motion/red-up/raw preferences restored. Bilingual help explains four modes and key concepts | PASS |
| UX-DETAIL | Drawer keeps filters/scroll, Esc/Tab/back/trigger focus, URL | Shared navigation and native strategy/market dialogs with URL-fragment history; market fragment names exact dataset/security | Chrome strategy Back/Forward/direct URL and Tab/Esc PASS. Chrome market search page 21–40 with SSE filter: Back closed detail in place, Forward reopened, scrollY remained 295, trigger focus returned; direct URL reload resolved exact 600025, copied direct URL resolved watchlisted 000001 and closed in place; watchlist Back/Esc restored focus, Tab remained inside dialog; unavailable source showed actionable Chinese alert. Chrome 390×844 zh/en dark: document width375, modal width351, no page overflow; local table scroll hint visible; original locale/viewport restored. Frontend202/lint/types/build and PR30 backend/frontend/compose CI PASS. Broader mobile/filter-scroll matrix still open | IN_PROGRESS |
| UX-COMMAND | Safe Ctrl/Cmd+K + visible entry searches pages/strategy/studies/watchlist/help | Bounded server study/watchlist search, local pages/registered strategies/help | Chrome Ctrl+K, visible entry, server-filtered saved study, watchlist result, help search/navigation and one-Escape close with focus restoration PASS; Windows shortcut hint corrected. Frontend194, lint/type/build PASS; bounded search tests PASS | PASS |
| UX-VIEWS | Saved filters/chips/sort/columns/table-detail/task center | `/tasks` uses bounded saved research/update APIs; `/experiments` applies server-wide search/status/mode/sort before pagination, stores one optional local view, and retains temporary filters in the list history entry | Chrome zh/en task center linked to exact saved study/update receipt. Saved research view survived reload. On 2026-09-23 Chrome 390×844 task center and research list had document width 375, no page overflow, visible local table-scroll hint. A temporary `M1` search was lost after detail/Back; history-entry fix then retained the unsaved query and five matching results on the same path. Original filter and viewport were reset. Focused28/full frontend203, lint/type/build PASS. Broader matrix remains | IN_PROGRESS |
| UX-CHART | Exact hover/legend/benchmark/date range/equity-drawdown-trade link/table; bounded loading | SVG exact data + linked experiment collections | In-app browser 2026-09-23: historical 20-session run benchmark toggle/date 2011-03-23 linked to six fills and the exact account snapshot, while full-run return stayed −0.47%; 293-session result paged 100/100/93 with full-run return still +4.67%. A real synthetic run retained one plotted benchmark line and an enabled toggle. Actual Chrome153 on 2026-09-24 checked null-series behavior, keyboard date selection/live readout, exact hover, benchmark toggle, four-date range and 2011-03-23 date link to six fills/holdings; full-run metrics stayed fixed. Wider large-page, locale/theme and screen-reader matrix remain; details below | IN_PROGRESS |
| UX-ERROR | No data/permission/offline/timeout/no match/no trades have next step | Shared load panel distinguishes typed 401/403/404/408 and offline TypeError; raw diagnostic behind disclosure | Chrome real 404 dataset offered safe workbench exit. On 2026-09-23 isolated Chrome153, aborting only localhost:8000 API requests showed two actionable offline panels; after restoring transport, one retry refreshed both real data and recent studies, and the top service-status control independently returned to online. Injected HTTP403 initially exposed a misleading generic service-start message in ProductError; typed 401/403, 408 and TypeError now show distinct bilingual permission, timeout and offline guidance while retaining explicit retry. Isolated Chrome injected 403/408 and restored the real cached date after retry; frontend211/lint/type/build PASS. These are fault-injection UI checks, not real permission grants. Chrome `/experiments` no-match search showed a remove-filter/reset next step; reset restored the saved result. A real persisted 293-session result filtered to 2010-01-04 showed zero trades with clear-or-widen guidance; clearing dates restored 18 trade rows without changing full-run metrics. Clean-install no-data path was checked separately in U1; wider failure and screen-reader matrix remain | IN_PROGRESS |
| QA-VISUAL | 1440×900,1280×800,1024×768,390×844; two themes/locales; key 200% zoom | Neutral shell and product pages | Home1440 and mobile390 basic checks. On 2026-09-23 the actual historical result page in the in-app browser had document widths 1425/1265/1009/375 at viewports 1440/1280/1024/390 respectively, with no page-level overflow; Chinese light at 390 and English system-dark at the other widths were visually inspected. A separate real-Chrome 720×450 CSS-viewport proxy for a 1440×900 window at 200% found the Workbench primary action below the first screen (507–549px); compact styling moved it to 387–429px, with no page overflow at 720, 390 or 1440. [Before](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/workbench-css-720x450.png) / [after](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/workbench-css-720x450-fixed.png) are agent screenshots outside Git. The proxy is not actual browser zoom; bounded native 200% checks are detailed below, while the full cross-page/theme/locale matrix remains | IN_PROGRESS |
| QA-A11Y | Keyboard/focus/semantic dialogs/live status/reduced motion/AA contrast+targets | Shared semantic controls and responsive shell | In-app browser 2026-09-23 at 390×844 measured the top data-status link at 343×20px; a shared CSS target change made it 343×40px without page overflow (document375px). A repeat wizard DOM geometry pass found 35 visible controls and none below 24px. A separate mobile paper-session list audit found its shared `.monoLink` target only 86×14px; table-scoped CSS raised it to 86×40px, also fixing the legacy backtest list. Both pages retained document width375/client width375 at 390×844; desktop paper row is 53px high at1440. On 2026-09-23 isolated Chrome153 AX trees of nine primary routes had no unnamed exposed button/link/textbox/combobox/checkbox/switch/menuitem. Home text links were measured at 20–21px high, then raised to 40px in shared styles; Chrome at 390×844, 720×450 and 1440×900 confirmed all four links at 40px, no page overflow, and the 720px primary CTA still inside the first viewport. [Narrow screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/workbench-links-720x450.png) stays outside Git. Direct-load focus was found on main/step heading, bypassing the first-Tab skip link; shared route focus and wizard-step focus now skip the initial mount only. Chrome at 390×844 confirmed first Tab reaches the skip link on both direct URLs, while in-app navigation focuses main and a step change focuses its heading. Focused35 and full frontend210, lint/type/build PASS. A separate Chrome153 1280×800 computed-color check found the old search-field border at 1.17–1.48:1 against adjacent light/dark colors; the form-only `--field-border` token raised sampled ratios to 3.41–4.03:1 without document overflow. [Before](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/field-border-before.png) / [after](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/field-border-after.png) screenshots stay outside Git. Four-route light/dark text samples had no sub-threshold computed-color result using nearest opaque ancestor, but this is not a complete contrast audit. This is not a full WCAG 2.2 AA or screen-reader audit | IN_PROGRESS |
| QA-PERF | Immediate feedback; measured local interaction p95 target≤200ms; bounded charts/tables | Research archive and result/compare routes loaded on demand; initial JS entry chunk 549.12→409.17 kB minified (169.44→129.31 kB gzip) | On DESKTOP-3EOROGR, actual isolated Chrome 153 at 1440×900 with local populated database: 30 warm Workbench↔Strategies route clicks from Playwright click start to visible h1 had p50 15.6ms/p95 32ms/max 48.2ms, including automation overhead. A separate persisted 293-session result page (138 currently rendered table rows) took cold 560ms and 10 warm full reloads p50 883ms/p95 923ms to show Total return; this is document/data-load latency, not the same interaction metric. API requests themselves took ≤12ms in a warm trace. Bounded native-200% chart/page interaction timings are detailed below; production build, larger-data and wider interaction diagnosis remain | IN_PROGRESS |
| QA-ENGINE | Decimal/server validation/idempotency/task isolation; same financial path | Existing financial path + independent queue | 862 backend tests; actual 2011 exploratory run completed; synthetic clearly separated | IN_PROGRESS |
| QA-REVIEW | Implement→browser review→fix→recheck; independent read-only review resolved | Independent backend+frontend code/test review | Reported races/idempotency/format/routing defects corrected; final browser repeat pending | IN_PROGRESS |
| M4-DATA-INTEGRITY | Application and formal-history persistence, isolated tests, recoverable backup | Suite-wide test-DB guard and verified additive restore | Live DB was found missing formal 1/3/310 ledger and later paper accounts. Formal ledger and four pre-backup accounts were restored atomically; `4b64380f` and `07d72259` remain absent. Live-config pytest was rejected; isolated backend969 PASS/one optional skip with live counts stable. The post-recovery dump restored into a new database, with 44/44 public tables matching live by row count and sorted-row hash. This same-disk dump is not independent disaster recovery and missing-history disposition remains open | FAIL |
| QA-RELEASE | Full backend/frontend/lint/types/build/migrations/durability/CI/compatibility | Incremental suites and reversible migrations | Earlier isolated migration and frontend checks remain valid. 2026-09-23 isolated backend969 PASS/one optional archive skip and PR32 `b060e9f` CI35915906461 backend/frontend/compose PASS; however the live DB data-loss incident makes the current release/durability gate FAIL. Frozen research files were not changed; formal DB rows were restored from backup | FAIL |
| M5-DELIVERY | New/old screenshots + key recordings, bilingual manual/demo/start/recovery/rollback, mode freshness/limits | Draft [Chinese](USER_GUIDE.zh-CN.md) and [English](USER_GUIDE.en-US.md) guides | Both draft guides cover current UI, mode/date boundaries, recovery and rollback. Docker Desktop 4.92.0 login autostart is enabled; four project containers have `unless-stopped` in Compose and runtime. A non-destructive Docker Desktop restart recovered all four services with API/frontend HTTP200, Redis PONG, persistent volumes/images and unchanged live ledger counts 1/3/310 research, 5/417 paper, 8 personal jobs and 4 update jobs. The two idle test-DB containers were returned to their original healthy state. This is engine-restart evidence, not full Windows reboot/login acceptance. PR32 CI35915906461 backend/frontend/compose PASS; screenshots/recordings and operator review remain incomplete | IN_PROGRESS |
| M5-PUBLISH | Small feature PRs reviewed+CI+browser→merge; v1.2.0 only after all required rows pass | feature/product-experience-v1.2 | v1.1 remains immutable | NOT_RUN |

PRODUCT_GOAL_COMPLETE = NO. Remaining required work is the full non-PASS set above.

## 2026-09-24 02:55 UTC manual update refresh feedback

In actual Google Chrome 153 at 1280×800, delaying only the saved update
detail GET after the visible Refresh click left the old completed status,
2/2 requests and candidate summary on screen until the response finished.
That was ambiguous feedback for a user and a stale success during a pending
read, although the prior error path already hid old details. The detail
refresh now immediately clears the old job/error and presents the existing
polite `role=status` loading message. Chrome with the same held GET showed
zero old-completion copy and exactly `Loading saved state…`; releasing the
unmodified request restored the genuine completed detail. No update POST or
provider request was made in this fault-injection check. The
[loading-state screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u5-refresh-loading-20260924.png)
is outside Git, SHA-256
`504BA0EA3A8A68EACF74DB15E274EA583E43329A931E8C632CCF99251F881DB0`.
The focused update suite passed 12/12, full frontend 220/220, ESLint,
TypeScript, Prettier and production build passed. PR32
[CI35949299927](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35949299927)
passed backend/frontend/compose. This is a bounded
UX-ERROR/QA-A11Y status-feedback improvement, not an actual screen-reader
study or full U5/AA/release acceptance.

## 2026-09-24 02:48 UTC durable retry identity and actual Chrome check

An existing failed raw-update parent `0eecbddb-4960-4a63-bf9a-505e9a5af884`
already had successful child `ed796871-4ce4-4cf3-b7f0-2223e636bb75`, but the
child used a manually supplied request key. The UI retry key differed, so the
old backend could create a second child. Migration 0016 adds one unique
`retry_of` child per parent to both personal-research and market-update jobs;
service create/retry returns the existing child for a different key or a
concurrent call, while retaining configuration-fingerprint conflict checks.

The change passed 975 isolated backend tests (one optional archive skip),
Ruff/format/mypy, migration downgrade/re-upgrade on disposable `quant_test`,
and [PR32 CI35948252640](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35948252640)
backend/frontend/compose. A pre-0016 logical dump outside Git has SHA-256
`c823582ed08f5e5e3e43aa6e697cda667ff4ec75babd2badb33fda48131f6eb4`;
it restored transactionally into a disposable clone containing 8 research and
4 update jobs, then upgraded 0015→0016 with both constraints present. This is
a same-disk migration safety check, not independent disaster recovery.

The live migration reached 0016, only the backend restarted, API health
returned HTTP 200, and the 8 research / 4 update / 5 paper session counts
stayed unchanged. In an independent headless Google Chrome 153 session at
1280×800, clicking the visible failed-task retry once sent one
`POST /api/market-updates/{parent}/retry` and navigated to the already
successful child URL. The child displayed 2/2 completed requests and the
candidate-only/non-executable warning. Live update jobs/receipts/observations
remained 4/6/6 and the parent had exactly one child; this is not evidence of
a newly authorized provider feed. The [Chrome screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u5-retry-existing-child-20260924.png)
is outside Git, SHA-256
`8F91D19CCB3D7E40D37C2CF1AFD0A5C1D55C4187BCD46E54912080CF40DF6932`.
U5-UPDATE remains IN_PROGRESS, QA-RELEASE remains FAIL, and no forward account
was started.

## 2026-09-24 02:21 UTC task-center research error recovery

Actual Chrome 153 intercepted only `GET /api/experiments` on `/tasks` with a
test HTTP 403. Before the fix, the research section incorrectly told a Chinese
user to start the local service; the four raw-data request links still loaded.
The task center now reuses the same typed experiment-error explanation as the
research list/detail. With the same injected 403, Chinese and English rendered
explicit access-denied guidance in an alert; after removing the interception
and using the visible Refresh button, eight genuine saved research links
returned, the four raw-data links remained, and the browser sent no POST.
The test was a local fault injection, not an actual permission grant or bypass.
[Before](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/task-center-403-before-20260924.png)
(SHA-256 `C4A448CF18F457E11D9D5EE04F1DFCCF755917AFC68E40ADD4C8DA6194A3388A`)
and [after English](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/task-center-403-after-en-20260924.png)
(`88B2D08AFBB77F3F8AE6ED5D4A4BA8F9B4A27946B88FC129DC23A3D0945809A5`)
are actual browser captures outside Git. The existing dual-stream test now
covers 403 → offline → explicit refresh recovery; full frontend 219 tests,
ESLint, TypeScript, production build and Prettier passed. This closes one
`UX-ERROR`/`U8-I18N` defect, not either full acceptance row.
PR #32 code head `58e64a1` passed
[CI 35946927203](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35946927203)
for backend, frontend and Compose.

## 2026-09-24 02:11 UTC experiment comparison selection target

Actual Chrome 153 on the populated `/experiments` page found eight row-level
comparison checkboxes with only an 18×18 CSS-pixel pointer target. The column
visibility options already had larger label targets. A label around each row
checkbox now provides a 40×40 target while retaining its bilingual accessible
name and the original selection/three-study limit. At native 200% zoom in a
physical 1280×800 window (CSS 640px, DPR 2), clicking the new outer edge
selected a study, and keyboard Space removed it; the selected count changed
from 0 to 1 and back. The document/client widths were both 640px. English
`Select for comparison` remained correctly named. In a separate fresh Chrome
profile at standard 390×844/DPR 1, the label measured 40×40 and page width
equaled the 390px viewport; only the data table scrolled horizontally.
[Mobile capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/experiment-select-mobile-after-20260924.png)
is outside Git (SHA-256
`B852B32DFC92851A73AEDCE878912E152843FBBBE982685F4C2F369E4AFC3325`).
Frontend 219 tests, ESLint, TypeScript and production build passed. This closes
one `QA-A11Y` target defect, not the full WCAG/AT/visual matrix; its status
remains IN_PROGRESS. PR #32 code head `f02dbf5` passed
[CI 35946268129](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35946268129)
for backend, frontend and Compose. No research task or paper account was started.

## 2026-09-24 01:31 UTC native 200% narrow/short first-action visibility

Actual local Chrome 153 at 200% page zoom in a physical 1024×768 window
reported a 504×336 CSS viewport, DPR 2 and document/client width 504/504.
On a clean home, the guided-backtest action was below the first screen in
Chinese and English. The shared short-height/narrow-width CSS now places it
fully within the viewport in both languages. In a returning-user profile,
the Continue your draft button initially ended at CSS y=340.9, below the
336px viewport; after reducing only the draft banner spacing, it ends at
y=326.7. Clicking it opened the saved guided-backtest route with no page-level
overflow. [English light clean home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/zoom200-1024-en-light-home-fixed-20260924.png)
(SHA-256 `7BE4A0A483E422755599D7F543FCB4EC9C4BFFFE6F0B1C3807FACD76933309BF`),
[Chinese light clean home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/zoom200-1024-zh-light-home-fixed-20260924.png)
(`0CB462E01924342DB711B2BB432A08B6FB5FA2544EE246FE2E8F639A106A81F8`),
and [English dark returning home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/zoom200-1024-en-dark-draft-fixed-20260924.png)
(`4217B6DD05285686C7F9832A5E206E8972CFB8109D5E354761CE4038B667773A`)
are real-browser captures outside Git. Frontend 219 tests, ESLint, TypeScript,
production build and Prettier passed. This closes only the observed first-action
clipping; QA-VISUAL and QA-A11Y remain IN_PROGRESS.

At physical 1280×800 with the same native zoom, a returning Chinese/dark
profile reported CSS 632×352/DPR 2. Its draft action ended at CSS y=295.2.
Workbench, strategies, guided backtest, experiments, markets, paper, data,
tasks, help and settings all had document/client width 632/632; Chrome's
accessibility tree exposed no unnamed button, link or form control on those
ten routes. [Home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/zoom200-1280-zh-dark-draft-20260924.png)
(SHA-256 `BDDB3F7DA2C43D6F710ADC12FFCEA39A24253E9D43F37953F29E04EDB111F7B1`)
and [markets](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/zoom200-1280-zh-dark-markets-target-20260924.png)
(`694E5052AED2F7BEBAB9A1B15A28D1E6D4CA08E1305A8AF4BA941657C1A08E23`)
are outside Git. The markets notice contains a 20px-high link inline in a
sentence; this bounded geometry/AX pass is not a full target-spacing, contrast,
screen-reader or WCAG audit. PR #32 code head `08c75e9` passed
[CI 35943421735](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35943421735)
for backend, frontend and Compose; release gates remain open.

## 2026-09-24 01:41 UTC mobile route breadth

An isolated Chrome 153 profile at 390×844 (DPR 1) checked the same ten main
routes in Chinese/system-light and English/dark. Every route reported document
width equal to its 390px client viewport; Chrome's accessibility tree exposed
no unnamed button, link or form control. The [Chinese home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/mobile390-zh-system-clean-home-20260924.png)
(SHA-256 `F89B354EEE56F3DF29AFFA5CE86A691E102D2F3BE6C9D412C646F55F63800162`),
[English wizard](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/mobile390-en-dark-wizard-20260924.png)
(`4A62884967A3D8AF292EF42832E75990F4ED8376FD0DA10AABC14F9AF69F9781`)
and [English paper page](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/mobile390-en-dark-paper-20260924.png)
(`C32B24CFEB759AF173D0D3F9FDD40F300E791EDD6D931BEF4E8147142C1D0ED0`)
are real-browser captures outside Git. The profile was new, but the backend
database was populated; this is **not** clean-install or novice-user proof.
Only route width/names and the shown views were inspected, not the full
interaction, contrast, screen-reader or 200%-on-mobile matrix. PR #32 docs
head `b7b1a62` passed
[CI 35943815149](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35943815149).

## 2026-09-24 01:49 UTC large saved-result interaction latency at native 200%

On DESKTOP-3EOROGR, the PC's actual Chrome 153 at native 200% page zoom in a
physical 1440×900 window reported CSS 712×402/DPR 2. The populated local
development Compose app loaded the **existing** 293-session historical job
`d9f27183-a9a1-4f34-aef4-eba439f53374` with a bounded 100-point equity
page; no research or paper job was submitted. After warm loading, 20 alternating
page-1/page-2 clicks measured from Playwright click start until the visible
pagination label changed had p50 36ms, p95 51ms, max 53ms; the corresponding
equity GET resource durations were 8–12ms. Twenty benchmark-line toggles had
p50 28ms, p95/max 46ms. Twenty exact-precision toggles had p50 35ms,
p95 58ms, max 61ms. The saved full-period return, drawdown, cost and benchmark
summary stayed `+4.67%`, `-2.48%`, `96.05`, `-8.83%` through pagination and
benchmark toggling; precision changed only the displayed digits.

The [real chart capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/perf-zoom200-293session-chart-20260924.png)
has SHA-256 `2982847B18A8EE97488467A9EC4602EF9E73F283DAD31C7A309EE561299E9DAB`
and stays outside Git. Timings include local browser-automation overhead and
wait for visible DOM state; they are **not** low-level input-to-paint traces.
They pass the 200ms target for only these warm interactions, not full reload,
production build, cold cache, larger datasets or the entire QA-PERF gate.

## 2026-09-24 01:56 UTC shared experiment checkbox target

On the same saved result in actual Chrome 153 at native 200% zoom, the
`显示完整精度` and `显示基准` labels were each only 25.5 CSS px high. The shared
`.experimentCheck` style now centers its checkbox and gives the clickable
label a 40px minimum height. Browser recheck measured both labels at exactly
40px with document/client width 712/712. A click at the bottom of the expanded
benchmark label toggled it off and back on; keyboard Space did the same and
retained the visible 2px focus ring with 3px offset. A 390×844 Chrome result
page measured both labels at 40px and document/client width 390/390. The
saved result summary and backend data were unchanged. At physical 1024×768 /
native 200% zoom, the real two-study comparison precision label measured 40px;
the guided wizard reached its confirmation step without submitting and its
multiline acknowledgment label measured 45.6px. Both routes had document/client
width 504/504. No configuration was run.

[Before](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/zoom200-experiment-check-target-before-20260924.png)
SHA-256 `ADF558828CE72AE315C1F86033C82928AD19A691A5598054ACFBF0E8378B0137`;
[after](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/zoom200-experiment-check-target-after-20260924.png)
SHA-256 `AB543C7351E11D79DD0EF4B308759BEE1A79C976686EC8D5511418FEE2EE2804`.
Both captures remain outside Git. Frontend 219 tests, ESLint, TypeScript,
production build and Prettier passed. PR #32 code head `07fe3a1` passed
[CI 35945124726](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35945124726)
for backend, frontend and Compose. This closes one target-size defect, not
the full WCAG 2.2 AA or screen-reader audit.

## 2026-09-24 01:09 UTC unplanned historical worker crash and linked completion

An owned `quant-v12-u3crash-20260924` tmpfs PostgreSQL and backend on 8001
used the existing historical archive mounted read-only. Its explicitly
inspected 2010-01-04→2014-12-31 exploratory parent `77354e81` was observed
RUNNING before `docker kill --signal KILL` targeted **only** that isolated
backend. Exit code was 137. Before restart, the durable DB still showed
RUNNING 60/1212, null summary and zero result rows; no background worker was
alive. Starting the same test backend reconciled it to `INTERRUPTED` with
`WORKER_RESTARTED_RETRY_AVAILABLE`, preserved 60/1212, null summary,
`result_available=false`, zero result rows and HTTP 409 on `/result`.

Actual Chrome 153 showed the [interrupted guidance](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-historical-isolated-sigkill-interrupted-zh-20260924.png)
(SHA-256 `F4B7DA5CA03CFB8F0FB8F03A38D9D564D6D2803227F8CD09738A70E0F450AE79`)
and clicked the linked retry. Child `52b76f45` finished 1212/1212 with
4108 persisted result rows, attempt 2, `retry_of` the unchanged parent and
identical configuration SHA-256. The [reopened child](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-historical-isolated-sigkill-retry-result-zh-20260924.png)
(SHA-256 `1444728E5575FF30AEBDB7EDBA7BB3645E574C75C43DF6A44A002E4A74FA199B`)
kept the inspected-history/non-guarantee warning. Two later parent retry
clicks opened that same child; the test DB held two jobs, one retry link and
4108 rows only for the child. This is execution/recovery QA, **not** return
evidence or Official OOS. The owned backend, tmpfs PostgreSQL and network
were removed without `-v`; main DB counts stayed paper 5/417, research 8,
updates 4, four existing Docker volumes remained and `.research` was not
modified. This verifies abrupt worker-process exit, not physical power loss,
Windows reboot or the independent U7 paper/forward paths.

## 2026-09-24 01:00 UTC isolated historical FAILED terminal and honest data availability

An owned `quant-v12-u3fail-20260924` tmpfs PostgreSQL and backend on port 8001
used a test-only shadow dataset containing copies of the genuine frozen
manifest and marker but **no** partitions. The real archive and code mount
were read-only; the main database was untouched. Before correction, the registry advertised
this incomplete dataset as available and the worker failed with generic
`EXPERIMENT_EXECUTION_FAILED`. Parent `d5105a82` was genuinely `FAILED`, with
`result_available=false`, HTTP 409 on `/result`, and zero result rows.

The shared dataset boundary now classifies missing/changed frozen partitions
as `DATASET_INTEGRITY_FAILED`, without masking unrelated calculation errors.
It also marks a manifest with absent partition files unavailable before a
new job is submitted; actual archive availability remains true, and a live
read-only registry check took 11.1 ms. This is a file-presence check at
discovery, **not** a substitute for execution-time SHA-256 verification.

After restarting only the isolated test backend with the correction, actual
Chrome 153 clicked the parent's retry button and opened child `5b8db429`.
The child was genuinely `FAILED` with the same configuration SHA-256,
`retry_of` the parent, `DATASET_INTEGRITY_FAILED`, and no result. The browser
showed an actionable data-source warning in [Chinese](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-historical-isolated-failed-retry-zh-20260924.png)
(SHA-256 `E40242E0A9ECA7F46272D301529DF116ADB3E7014397CA402BBC03733D864EF3`)
and [English](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-historical-isolated-failed-retry-en-20260924.png)
(SHA-256 `266BBEAD83369519200A87CD0C714C9AD9D97781E847886F78831246BC76D00D`).
Repeating retry on the unchanged parent reopened that exact child; the test
database held two jobs, one link and zero result rows. Focused experiment API
18/18 and market-reader 18/18 tests, Ruff check/format and mypy passed.
Only the two owned test containers/network, tmpfs data and two-file shadow
directory were removed. Main DB counts stayed paper 5/417, research 8,
update jobs 4; `.research` and all four original Docker volumes were unchanged.
This covers a real FAILED-terminal browser path, not unexpected crash/power
loss or forward-market acceptance; `U3-RECOVER` remains IN_PROGRESS.

## 2026-09-24 00:46 UTC isolated historical restart and linked retry

An owned `quant-v12-u3restart-20260924` PostgreSQL ran on disposable tmpfs,
with an isolated backend on `127.0.0.1:8001`. Backend code, ordinary fixtures
and the already-audited historical archive were mounted read-only; no formal
study or Official OOS was run. The exploratory request used the existing
registered strategy and an explicitly inspected 2010-01-04→2014-12-31 range.
Its first task `8fa4b318` was observed RUNNING at 90/1212 sessions before
restarting only that test backend. It became `INTERRUPTED` at 190/1212 with
`WORKER_STOPPED_RETRY_AVAILABLE`, `result_available=false`, zero result rows
and HTTP 409 on `/result`; it was not called a completed study.

Actual Chrome 153 opened this interrupted task using only the isolated API,
showed localized recovery guidance and no financial result, then clicked
**创建或打开关联重试**. Child `557f6885` completed 1212/1212 with 4108 persisted
result rows, attempt 2, `retry_of` pointing to the unchanged parent and the
same configuration SHA-256. Clicking the parent's retry control twice after
completion returned that identical child; the test DB still held exactly two
tasks. Chrome displayed the completed child with an inspected-history warning,
not forward-market or Official OOS evidence. [Interrupted state](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-historical-isolated-interrupted-zh-20260924.png)
(SHA-256 `0F5A51E740C780D3FF89F9F1524BC9562CC7B61FC3443B6A05E1C5DFF0AEFFBB`)
and [linked result](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-historical-isolated-retry-result-zh-20260924.png)
(SHA-256 `352E7766F36567F8F21FA25429F1F778B27CFD82DAFD2A414BA894A61D30BFE8`)
are actual Chrome screenshots outside Git. Main DB counts remained paper
5/417, personal research 8 and update jobs 4; `.research` stayed unchanged.
Only this owned test backend, tmpfs database container and test network were
removed; all four existing Docker volumes and main services remained.
Controlled restart is not proof of unexpected process crash/power loss, and
an actual FAILED-terminal browser flow is still unverified. `U3-RECOVER`
remains IN_PROGRESS.

## 2026-09-24 00:33 UTC stale research list after refresh failure

Actual Chrome 153 refreshed the populated personal-research list with an
intercepted GET 503. Before correction, an offline-sounding error appeared
above previously fetched “已完成” rows. The list now removes old rows after a
failed read and passes the actual typed error to the existing explanation
function: HTTP 503 shows server-request guidance, while HTTP 403 shows
permission guidance. After restoring the read and manually retrying, the
server's saved rows returned. The [503 list screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-list-read-error-zh-20260924.png)
is outside Git (SHA-256
`CB6147AED09B4DFF1375131516D0554B2121105577AAA8769F03800F7F56D59D`).
No POST or database mutation occurred (paper 5/417, research 8, updates 4).
Focused research 28/28 and full frontend suite, lint, TypeScript and build
PASS. The list's existing in-flight refresh behavior is unchanged; this only
prevents a failed refresh from presenting stale rows as current. Wider U3
recovery and U8 error/accessibility matrices remain incomplete.

## 2026-09-24 00:28 UTC stale research result after task-read failure

The same stale-success presentation existed in the research-detail status
reader: actual Chrome 153 opened persisted historical job `5f26f84f`, then a
read-only HTTP 503 interception on its task GET plus **刷新** left the previous
−0.47% return visible below the error. The hook now clears the last job on a
failed task read. Chrome subsequently showed only the actionable error and
manual refresh restored the authoritative saved result. The [error-state
screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-no-stale-result-zh-20260924.png)
is outside Git (SHA-256
`43F3D9E7C106A4561C1CF41FF622068FDD869306A98D96DE4B396B6F9185ED38`).
The existing shared resource hook already discards data on read errors;
these two bespoke task readers now do likewise. No POST, job mutation or
formal research run occurred; live counts remained paper 5/417, research 8,
updates 4. Focused research 27/27, full frontend 218/218, lint, typecheck,
build and Prettier PASS. This repairs one misleading error state, not the
broader U3 restart or release acceptance.

## 2026-09-24 00:24 UTC stale update-task status after read failure

Actual Chrome 153 opened the saved candidate-only update task `ed796871`.
After intercepting only its detail GET with HTTP 503, **刷新** previously
showed an error above an obsolete “请求已完成” state, counts and observations.
The detail component now clears its last-known job on a failed read; it does
not present cached completion as current. Removing the interception and
manually refreshing restored the server's saved state. The [task-error panel](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u5-task-read-error-zh-20260924.png)
is an actual Chrome screenshot outside Git (SHA-256
`E7579544B00ADFF687D0E2B1A0A13472ABEC2AD65FDAAC2776602F7199CB51D6`).
No update POST occurred; main counts stayed paper 5/417, research jobs 8,
update jobs 4. The focused task test is 11/11, full frontend 217/217,
ESLint, TypeScript, build and Prettier PASS. This closes one stale-status
failure path, not U5 source/rule authority or its whole failure matrix.

Chrome also read the existing historical exploration chain `b78965ad`
CANCELLED → `5861fbb5` INTERRUPTED → `3db4b679` SUCCEEDED. The first two
had truthful recovery guidance, a linked-retry control and no result body;
the third displayed saved -0.91% return and costs. This was read-only
observation of persisted states, not a new cancellation/restart trial; no POST
occurred and `U3-RECOVER` remains IN_PROGRESS.

## 2026-09-24 00:15 UTC chart date-link and keyboard browser check

Actual Chrome 153 on the saved historical exploration `5f26f84f` (20 March
2011 sessions) used the native date selector with Home then ArrowDown. The
selected date became 2011-03-02, and the polite live-region readout updated
to the server's exact equity, benchmark and drawdown strings. Disabling the
benchmark removed both its SVG line and legend. A display-only range of
2011-03-10 through 2011-03-15 showed four session options, while the saved
full-run return remained −0.47% and no POST was issued.

Separately, selecting 2011-03-23 and activating **查看该日交易与持仓** narrowed the
chart to one date and opened six actual fills plus its account/holdings
snapshot. The [real Chrome screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/chart-linked-trade-20110323-zh-20260924.png)
is outside Git (SHA-256
`7B3E76BC5EFE6A708458A86C312A75B2EE2CD155E1FAF652412E89A80429C02B`).
The main database remained at five paper sessions/417 paper events/eight
personal research jobs/four update jobs, and `.research` was unchanged. This
is agent-operated browser/DOM evidence, not a screen-reader study or complete
large-data and cross-theme/locale chart acceptance.

An additional actual Chrome 390×844 EN/dark/motion-off check of this saved
result showed document width 390/390 and no page-level horizontal overflow.
The [mobile chart screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/chart-mobile-en-dark-390-20260924.png)
is outside Git (SHA-256
`8723D435FCF7D12B579D95B31A1AB856B7533298AE42096D70495051B286941D`).
This is one theme/locale/size combination, not the full visual matrix.

## 2026-09-24 00:08 UTC U3 job identity browser check

The main database's audited historical exploration job
`5f26f84f-b6da-4eac-805a-fbc28fd27af4` remains SUCCEEDED at 297/297
processed sessions. Fresh Chrome 153 reopened its same persistent URL and
showed the completed 2011 result, actual return/cost/benchmark, and warning
that the interval is already inspected historical data.

Separately, an empty `quant-v12-u3double-20260924` tmpfs PostgreSQL stack ran
the registered four-step synthetic wizard in actual Chrome. Double-clicking
the final Run button produced one POST `/api/experiments`, HTTP 202, job
`45c986a5-4eb8-49c4-9418-91697808406e`, and exactly one persisted task.
The job finished 340/340 sessions; a fresh Chrome context reopened its result
with the non-market synthetic label. Replaying the stored configuration and
idempotency key from a new client returned that same job ID and left the
database at one task. The [isolated result screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-double-submit-isolated-zh-20260924.png)
is outside Git (SHA-256 `56F00ED3A038797E1EF19D424932EDE923BBE681CEE5532065926C831BFE51D7`).
The test containers/network and intentionally disposable tmpfs database were
removed without volumes. Main DB counts remained paper 5/417, personal jobs
8 and update jobs 4. This composite historical/synthetic evidence accepts
U3-JOB's shared create/identity path, but not U3-RECOVER's full failure
matrix, genuine forward data, or a real novice-user test.

## 2026-09-24 00:02 UTC chart missing-series browser check and backup media

The persisted historical result `d9f27183` has complete benchmark values on
all three pages (293 observations). To test the missing-data display without
altering that result or its database, actual Chrome 153 intercepted only its
read-only equity response and set one displayed benchmark and drawdown value
to `null`. The page showed incomplete-series guidance in Chinese and English,
disabled the benchmark switch, rendered neither incomplete SVG line nor legend,
and kept the exact-data table accessible with both null cells shown as unknown
(`暂无`), not zero. No experiment POST occurred. The [Chinese fault-injection
screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/chart-null-series-fault-zh-20260924.png)
is outside Git (SHA-256 `600D20313726D2DCBFB02703135C6C28336480180BB0D4117A68D45D42EC8C30`).
This is browser fault-injection evidence, not a naturally incomplete historical
result or formal research rerun; UX-CHART and QA-A11Y remain IN_PROGRESS.

Windows `Get-Partition` and `Get-Disk` showed both C: and D: on Disk0, the
machine's sole exposed 2 TB NVMe disk. No independently mounted filesystem
backup destination was verified. The existing same-disk dump/restore drill
does not close independent disaster recovery or the two missing post-backup
paper ledgers; M4-DATA-INTEGRITY remains FAIL.

## 2026-09-23 23:54 UTC Data Center permission recovery

Actual Chrome 153 at 1280×800 intercepted only the read-only
`/api/market-updates/capabilities` response with HTTP 403. Before the fix,
the Data Center said only to refresh. The existing update-error path now
distinguishes denied access, timeout and offline transport for capabilities,
history, receipt/observation records and the Task Center, while preserving
source-specific denial text and explicit refresh. On the live page, Chinese
permission guidance appeared; after removing the interception, one manual
refresh restored the real request form. No market-update POST occurred and
main database counts remained paper 5/417, personal jobs 8, update jobs 4.
The [full-page Chrome screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/data-permission-403-page-zh-20260924.png)
is outside Git (SHA-256 `181DBE4D7873DB6C5A70BD572779001DD00773C59DECAF15D60D63CDDBEC5FE2`).
Focused update/task-center tests 12/12, full frontend 216/216, ESLint,
TypeScript and production build passed. This is fault injection, not a real
provider permission grant; U5-UPDATE and UX-ERROR remain IN_PROGRESS.

## 2026-09-23 23:45 UTC isolated paper reconnect and restart check

In a disposable `quant-v12-paperqa-20260924` tmpfs PostgreSQL stack with backend
on port 8001 and frontend on 5174, actual Chrome 153 created synthetic account
`cccc6b44-dc05-4a57-a9ca-b524adfb3ad0` through the UI. While RUNNING, its
active WebSocket was closed and reconnected; the authoritative REST sequence
advanced from 9 to 11 without duplicate fills. After UI pause at sequence 13,
a second disconnect/reconnect left the REST event count and sequence at 13.
The session then resumed and naturally STOPPED at sequence 521. All 521
persisted event sequences were unique and continuous from 1 through 521;
the final account had one order, one fill, cash `1223.5` and equity `100000000`.

Only the isolated backend was restarted. The same API account still showed
STOPPED, 521 events, one order, one fill, and identical cash/equity. A fresh
Chrome context reopened the same page and visibly showed the 2030 synthetic
label, stopped state, order, fill and portfolio values. The [post-restart
screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/paper-isolated-stopped-restart-20260924.png)
is outside Git (SHA-256 `BA998178FBE6067D4D19C63F17709560838CD4A04BB2874712FB0C27E8515FB4`).
Main DB counts stayed at five paper sessions, 417 paper events and eight
personal jobs. The three owned test containers and network were removed
without volumes; their intentionally disposable tmpfs DB was discarded.

This is bounded agent-operated synthetic integration evidence for U7-RECOVER,
not restoration of the two lost historical ledgers, a full restart matrix,
genuine forward-market data, or a real-user acceptance test. U7-RECOVER,
U7-MODES and M4-DATA-INTEGRITY remain FAIL; U7-FORWARD remains NOT_RUN.

## 2026-09-23 23:07 UTC isolated clean-user demo recording

An empty disposable PostgreSQL `quant_test` and read-only-mounted backend were
bound to `127.0.0.1:8001`; actual Chrome 153 served the existing frontend but
rerouted every `localhost:8000/api/` request to that isolated backend. The
Chinese 1280×800 browser flow opened the clean Workbench, completed the four
guided steps, acknowledged the synthetic warning, created exactly one registered
server job (`2813dc8f`) and read its completed result. The only POST was
`/api/experiments`; the job was `synthetic_demo`, not market evidence. The
9.60-second VP8 recording (SHA-256
`947B3233284E55C45BF2D515B81779BFA3D261C538344D1BFB48BB0F8102FFC8`)
was opened in Chrome and a running-stage frame inspected. A separate fresh
Chrome context reopened the same result after only this isolated backend was
restarted: +0.39% displayed return, CNY 25 cost, synthetic warning intact.
The main database stayed at eight personal jobs and five paper sessions. The
disposable tmpfs database/container/network were removed without volumes.
Evidence remains outside Git:
[full demo](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-full-flow-zh-1280.webm),
[clean home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-home-zh-1280.png),
[configuration](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-config-zh-1280.png),
[confirmation](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-confirm-zh-1280.png),
[result](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-result-zh-1280.png),
[reopened result](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-reopened-after-backend-restart-zh-1280.png).
This is an agent-operated synthetic path, not genuine A-share forward market
receipt, actual novice-user satisfaction, full Windows reboot durability or
product release acceptance. `M5-DELIVERY` remains IN_PROGRESS.

## 2026-09-23 23:00 UTC local delivery walk-through evidence

Actual local Chrome 153 at 1280×800 recorded a 13.44-second Chinese walkthrough:
Workbench → guided-backtest entry → strategy detail → saved historical result
and keyboard date selection → stopped audited-historical paper account. The
session used an isolated browser profile; only its local draft was saved, no
new backend task or paper session was started. Live database counts after the
recording remained eight personal research jobs and five paper sessions.
The WebM is SHA-256
`B85F5595830D884BBC88D6C34AD1B824575DAFA199953DD42D7EA18F51695C1F`.
The video and screenshots are local evidence outside Git, not generated mockups:
[walkthrough](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/product-walkthrough-zh-1280-v2.webm),
[home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/workbench-zh-1280.png),
[guide](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/guided-start-zh-1280.png),
[strategy](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/strategy-detail-zh-1280.png),
[result](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/historical-result-summary-zh-1280.png),
[chart](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/historical-result-chart-zh-1280.png),
[comparison](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/historical-comparison-zh-1280.png),
[paper](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/historical-paper-zh-1280.png).
This is an agent-controlled read-only demonstration, not a novice-user test,
fresh forward-data proof, complete start-to-finish run, or release approval.
`M5-DELIVERY` remains IN_PROGRESS.

## 2026-09-23 22:48 UTC chart keyboard announcement

Actual Chrome 153 on saved historical study `d9f27183` showed that ArrowUp on
the trading-date selector changed the date and exact equity/benchmark/drawdown
readout, but the readout had no live-region semantics. The existing readout now
uses polite, atomic announcement; the same Chrome keyboard step confirmed the
updated date and financial strings without changing the study or full-period
metrics. The existing collection test checks the announcement attributes and
date update. Frontend 213 tests, ESLint, TypeScript, build and Prettier passed.
This is a bounded keyboard/DOM accessibility check, not a screen-reader user
study or full WCAG 2.2 AA audit. `QA-A11Y` and `UX-CHART` remain IN_PROGRESS.

## 2026-09-23 22:32 UTC experiment result-load error recovery

On a persisted successful historical experiment, isolated Chrome 153 intercepted
only its result GET with HTTP 403 plus an unfamiliar backend code. Before the
fix, the result panel incorrectly said the server could not finish the
request. The shared experiment error interpreter now gives permission and
timeout responses precedence over unknown codes, and the result panel uses
that same interpreter. Chrome showed Chinese permission guidance, an explicit
retry after removing the interception loaded the actual result, and an
injected HTTP 408 showed timeout guidance. No new task or live database write
was made. The frontend regression covers denied access and retry; broader
U3 failure/cancellation and U8 error matrices remain IN_PROGRESS.

The native Chrome 200% follow-up also checked seven routes at physical
1280×800 in EN/dark/motion-off (CSS632×352, DPR2), without document-level
horizontal overflow. CDP screenshots are outside Git under
`product-evidence/v1.2/m4/zoom200-en-dark-*-1280.png`. This remains a bounded
visual check, not full accessibility or product acceptance.

## 2026-09-23 22:25 UTC native Chrome 200% zoom check

An ephemeral Chrome 153 profile used Chromium's native default-page-zoom
preference (factor 2, not a CSS viewport proxy): a physical 1440×900 window
reported CSS viewport 712×402, `devicePixelRatio=2` and
`visualViewport.scale=1`. Workbench, guided wizard, experiment list, markets,
paper accounts, data center and research archive each had document width
712/712 with no page-level horizontal overflow. The clean-profile Workbench
primary action was clipped by 3 CSS pixels below the first screen. A
short-height/narrow-width heading-spacing adjustment moved its bottom from
405 to 395 against the 402px viewport; a physical 1424×805 Chrome CDP
screenshot shows the entire button. Before/after screenshots are outside Git
under `product-evidence/v1.2/m4/zoom200-clean-home-{cdp,fixed-cdp}.png`.
Regular Playwright screenshots were cropped at native zoom, so these captures
used Chrome's screenshot protocol directly. This is a bounded Chinese/light
route pass, not the complete language/theme/route zoom matrix.

## 2026-09-23 22:17 UTC research-archive status and mobile-table review

Real Chrome 153 on the persisted formal research archive found raw `PASSED`,
`SUCCEEDED` and research split codes in the Chinese list/detail. The shared split
badge and two archive pages now show translated, non-promissory labels while the
original status remains available as the element title for audit. The 390px
archive screenshot also showed that important columns were offscreen with no
scroll cue. Both research-list tables and run-detail tables now announce the
horizontal scroll region and expose a visible narrow-screen hint; the focused
container moved 40px with ArrowRight in Chrome. Document width remained 390px.
EN 1280px and ZH 390px screenshots are outside Git under
`product-evidence/v1.2/m4/research-status-{en-1280,zh-390-scrollhint}.png`.
Frontend 212 tests, ESLint, TypeScript, build and Prettier passed. This closes
one archive slice, not the overall U8, visual or accessibility gates.

## 2026-09-23 21:09 UTC real Chrome export closure

An isolated headless installation of the PC's actual Chrome 153, with its own
temporary profile and downloads enabled, opened the persisted historical job at
the documented `localhost:5173` origin. It emitted successful download events
for both CSV and JSON; the CSV contained 29,316 bytes and the metadata JSON
258,223 bytes. Neither download reported failure. The earlier in-app-browser
artifact limitation is retained as environment-specific evidence, not a reason
to leave the Chrome product export unverified. This does not close the other U4
or release gates. A control at `127.0.0.1:5173` showed the existing exact-origin
CORS policy (`FRONTEND_ORIGIN=localhost:5173`) denying API access; the documented
local URL works, and no security policy was broadened.

## 2026-09-23 21:18 UTC dirty browser traversal repair

Real Chrome Back from an edited guided wizard reached home without calling its
registered confirmation, while a sidebar link did call it. The route listener
was consuming the browser `popstate` before the page guard could act. The
shared route now asks the active guard synchronously before changing pages;
cancelled traversal restores the original history entry. Chrome showed one
native confirmation on dismiss and one on accept; dismiss kept the edited name
and step, accept reached home, and Forward restored both without another
dialog. This repairs one shared navigation boundary, not every U3 job/recovery
case.

## 2026-09-23 21:27 UTC bounded Chrome performance measurement

The PC's actual Chrome 153 ran in an isolated headless profile against the
populated local Compose services. Thirty warm Workbench↔Strategies clicks at
1440×900 reached their destination heading at p95 32ms. A different measure,
full document reload of the persisted 293-session historical result until its
saved return label appeared, was p95 923ms over ten warm attempts (cold 560ms).
The former supports immediate local navigation feedback only; the latter is not
a click-response p95 and does not pass or fail the broader interaction target.
The live development server and a 138-row rendered result were used. A warm
resource trace showed individual result API responses ≤12ms, so the page-load
gap needs further browser/render analysis; no speculative optimization was made.

## 2026-09-23 21:31 UTC narrow desktop first-action visibility

At a 720×450 CSS viewport, the primary Workbench action was initially below
the first screen (top/bottom 507/549px). A compact 601–800px Workbench layout
now puts the whole action at 387–429px without changing its 390px mobile or
1440px desktop layout. Chrome showed no document overflow at any of those three
widths. These are CSS-viewport and screenshot checks, **not** a claim that the
browser's true 200% zoom control was exercised.

## 2026-09-23 20:55 UTC unavailable-market explanation

The unavailable historical-source notice in Markets had exposed
`DATASET_NOT_MOUNTED` directly. It now reuses the registered bilingual plain
explanation and retains the raw code only in a closed source-lineage disclosure.
The focused Markets tests passed 12/12 in EN/ZH, with lint, typecheck and build
passing; the actual available-cache Markets page still loaded 20 rows in the
in-app browser. An unavailable-source browser run was not possible against
the mounted live archive, so this change does not close the wider U5/U8 gate.

## 2026-09-23 20:51 UTC topbar locale review

The actual Chinese result page exposed the backend-only `development · paper`
value in the service-status hover title. The topbar already has a localized
online/offline label, a refresh control and a UTC check time, so the redundant
raw title was removed. The existing routing regression now rejects its return;
focused App tests 9/9, lint, typecheck and build passed in the frontend
container. The in-app browser confirmed no title in either Chinese or English
while the localized status and accessible refresh name remained. Original EN
locale was restored. This narrows U8; it is not a full translation audit.

## 2026-09-23 20:32 UTC post-restart in-app browser check

The workbench reopened persisted historical job `d9f27183` after the Docker
engine restart. Its saved 2010-01-04→2011-03-22 range, return +4.67%, drawdown
-2.48%, cost CNY96.05, 32-row simulated plan and risk refusals rendered; the
page continued to label the period inspected and the plan non-executable.
This is a post-restart read check, not a fresh experiment or formal study.

On that actual result page, JSON export produced a prepared blob and a fallback
save link. Neither automatic click nor user-activated fallback raised a browser
download event within 10 seconds; the named report was absent from the default
Windows Downloads directory. U4-EXPORT remains IN_PROGRESS. Browser logs showed
no error, so the app-versus-browser cause is not established; no security check
was bypassed. On the guided wizard, a temporary name edit followed by browser
Back stayed on the wizard but exposed no observable native dialog; the original
`U3 final diagnostic` name was restored and saved in this in-app browser.
Dirty Back/Forward cancel/accept remains unverified. EN→ZH→EN preserved the
exact name, CNY100000, 2011-01-04→2011-06-30 dates and parameters; this narrows
U8 but does not close the complete bilingual matrix or prove the separate
Chrome-profile draft was restored.

At 20:39 UTC, the in-app browser checked the actual guided wizard at
390×844, 1024×768, 1280×800 and 1440×900. In the 390×844 viewport,
Workbench, Strategies, Experiments, Markets, Paper, Data Center and Settings
were inspected in English and their main document did not overflow the
viewport; the same primary routes were checked in Chinese. Workbench was also
visually inspected at 390×844 in system-dark and light themes. Original EN,
system theme and default viewport were restored. This is a bounded responsive
pass, not 200% zoom, keyboard, screen-reader or complete visual-matrix signoff.

## 2026-09-23 19:59 UTC restored paper-page language check

The in-app browser opened restored historical account `d7044a3c` from the
five-session live list and showed its 20 orders, six fills and simulated
equity `99964.8134`. Its Chinese view initially exposed an English paper
safety marker, the transport label `WebSocket`, and the internal strategy ID
in every signal row. Existing bilingual paper copy and strategy-name keys now
render plain safety/connection labels and a translated strategy name without
changing persisted financial events. Browser Chinese visible text no longer
contains those three raw tokens; English was rechecked and the original locale
restored. Full frontend206/lint/type/build and focused paper16 tests pass.
This agent check narrows U8 but does not close the full bilingual/a11y matrix.

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
