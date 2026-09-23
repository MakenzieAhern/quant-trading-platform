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
| U3-JOB | Validated actual A-share job; stages/counts; persistent URL; refresh/reopen; idempotent duplicate | /api/experiments; independent durable manager | Chrome job5f26f84f: actual297/297, leave/reopen/reload same ID, historical result; API idempotency and UI lock tests PASS | IN_PROGRESS |
| U3-RECOVER | Real cancellation/retry/interruption; no partial results called success | cancel/retry and durable terminal states | Running cancellation; restart INTERRUPTED; linked retry SUCCEEDED. On 2026-09-23 the in-app browser opened interrupted job `5861fbb5`, showed no partial result and explained the linked retry, then its retry control reopened existing completed job `3db4b679` rather than overwriting the original. Cancelled job `b78965ad` also showed no partial result and a recovery explanation. In a separate disposable `quant_test` database, actual Chrome 153 opened cancelled synthetic job `45b220b1`, showed no partial result, clicked linked retry, and reopened the same child `a54768bb` on a second click. The parent remained CANCELLED; the child SUCCEEDED as attempt 2 with one linked row and an identical configuration SHA. [Cancelled](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-isolated-cancelled-en-1280.png) and [linked retry](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u3-isolated-linked-retry-en-1280.png) screenshots are outside Git. This proves one synthetic cancellation/retry path, not the broader historical/failure/restart matrix | IN_PROGRESS |
| U3-ISOLATE | Independent exploration names/store; formal reports/OOS/freeze unchanged, dates labeled inspected | Separate product_research_jobs/rows, readonly archive | No .research diff; frozen hashes unchanged; formal 1 dataset/3 runs/310 trades before-after | IN_PROGRESS |
| U4-RESULT | Return/drawdown/cost/benchmark/limits, null semantics, true records and reasons | Personal result and date-linked holdings/trades, full-precision toggle | Chrome demo+historical results agree with exact APIs; real fill/snapshot2031-04-14 linked; source unavailable remains N/A; U4 tests/review PASS | PASS |
| U4-COMPARE | Reopen/compare 2–3; six config differences indicated | /experiments/compare?ids= | Chrome three actual runs, six conditions, exact fraction display and refresh preserving URL/results; comparison tests and independent review PASS; `u4/compare-three-results-en-dark-1024.png` | PASS |
| U4-EXPORT | Metadata report and formula-safe CSV | Server-streamed export, automatic download and persistent prepared-file link | Injection/precision/API tests PASS, including CSV formula-prefix escaping. On 2026-09-23 21:09 UTC isolated real Chrome 153 with `acceptDownloads` at the documented `http://localhost:5173` origin emitted successful download events for historical job `d9f27183`: trades CSV 29,316 bytes and metadata JSON 258,223 bytes, with expected filenames and `download.failure() = null`; JSON began with report metadata and exact job ID. Earlier in-app-browser download suppression remains an environment-specific observation, not a failed Chrome export. Agent walkthrough, not a real-user study | PASS |
| U5-MARKET | Search/watchlist/raw-adjusted/date/source view | /api/markets and /markets deployed0013 | 20 backend/14 frontend focused tests; independent review PASS; Chrome000001 raw22.45/HFQ874.904325432379995/suspension2010-03-01; watchlist persists fresh tab; dialog dates/locale/Esc;390+1280 no page overflow | PASS |
| U5-UPDATE | Incremental update/gaps/retry/history with source/license/rules/limits; no archive refetch | /data and /api/market-updates; separate product cache and migration0014 | Real Chrome one-security/one-date job `3b729cf9` succeeded and survived restart/reload. Four-board job `164c947d` had 3 new + 1 cached candidates. Targeted control retry `ed796871` added two 2026-09-22 vendor candidates: 688622 isST=1; 603400 suspended with blank raw turnover normalized to zero, never executable. Chrome visually confirmed official SSE 603400 suspension notice; binary checksum unavailable. Official 2026 exchange rule transition is mapped in a separate candidate model with no fills and focused tests; execution authority remains false. Failure/retry browser and full 2026 authority remain | IN_PROGRESS |
| U6-PLAN | Real candidates/targets/quantities/cash/reasons/rejections; as-of/snapshot/version; insufficiency/staleness | Persisted result preview and independent audited historical paper account | Historical job `d9f27183` completed 293/293; preview 2011-03-22→23 had 32 candidates, 5 risk rejections. Independent account `d7044a3c` generated 20 risk decisions/orders and 6 fills through the paper runtime; future-data plan and actual forward receipt remain pending | IN_PROGRESS |
| U7-MODES | Three isolated account modes, start/pause/stop/risk/ledger | Synthetic demo + distinct audited historical replay with durable pause/resume; forward not implemented | Chrome previously verified account `4b64380f` with 20 orders/six fills, but that post-backup account is now absent after the 2026-09-23 database incident. The older uninterrupted account `d7044a3c` was restored from a verified backup. Forward mode remains unimplemented | FAIL |
| U7-RECOVER | Socket disconnect/reconnect + backend restart don't fake/duplicate fills | Persisted paused state, deterministic source replay to checked cursor, then append-only continuation | Prior Chrome restart/resume observations for `4b64380f` and interrupted `07d72259` are retained as historical QA evidence, not current persistence proof: both post-backup ledgers are absent from the live DB. No synthetic reconstruction is accepted. Full recovery matrix remains | FAIL |
| U7-FORWARD | Lawful source + completed real session data arriving after user session start; receipt times/plan/simulation | Public-source candidate assessed, forward session not implemented | Historical probe is not forward evidence; real after-start arrival still required. Current SSE/SZSE Trading Rules §5.1.3 require permission for exchange trading-information use; BaoStock's public SDK and website access do not establish upstream/product execution rights (see SOURCE_READINESS). | NOT_RUN |
| U8-I18N | One tree; translated important UI/error/help/a11y; switching retains config/date | Shared i18n for legacy create/detail, paper ledger and typed shared load errors | Chrome real historical account shows translated signal, order, fill and risk labels; legacy create form is Chinese, and switching to English retained exact entered capital `123456.789`. Interrupted account has Chinese recovery help; nonexistent dataset has Chinese not-found guidance and preserves raw diagnostic under audit disclosure. The historical result warning explains inspected vs unseen data in both languages. On 2026-09-23, the in-app browser switched a persisted legacy success run EN→ZH→EN with exact Decimal strings unchanged. A later live result exposed raw `CORPORATE_ACTION_OPENING_UNCERTAINTY` as an unexplained reason; shared code mapping now explains it and the sibling non-orderable rejection in EN/ZH, with the original code still behind technical details. Browser EN/ZH and frontend206/lint/type/build PASS. Remaining pages, other server-supplied errors/help/a11y matrix pending | IN_PROGRESS |
| U8-SETTINGS | System/manual themes, language/motion/market colors/data preferences; explanatory help | Shared safe presentation storage and settings | Storage-denied/quota/locale tests PASS. Chrome dark/zh retained; motion-off, green-up and adjusted-view selections persisted after reload, and a real market detail opened in adjusted view. Original system-motion/red-up/raw preferences restored. Bilingual help explains four modes and key concepts | PASS |
| UX-DETAIL | Drawer keeps filters/scroll, Esc/Tab/back/trigger focus, URL | Shared navigation and native strategy/market dialogs with URL-fragment history; market fragment names exact dataset/security | Chrome strategy Back/Forward/direct URL and Tab/Esc PASS. Chrome market search page 21–40 with SSE filter: Back closed detail in place, Forward reopened, scrollY remained 295, trigger focus returned; direct URL reload resolved exact 600025, copied direct URL resolved watchlisted 000001 and closed in place; watchlist Back/Esc restored focus, Tab remained inside dialog; unavailable source showed actionable Chinese alert. Chrome 390×844 zh/en dark: document width375, modal width351, no page overflow; local table scroll hint visible; original locale/viewport restored. Frontend202/lint/types/build and PR30 backend/frontend/compose CI PASS. Broader mobile/filter-scroll matrix still open | IN_PROGRESS |
| UX-COMMAND | Safe Ctrl/Cmd+K + visible entry searches pages/strategy/studies/watchlist/help | Bounded server study/watchlist search, local pages/registered strategies/help | Chrome Ctrl+K, visible entry, server-filtered saved study, watchlist result, help search/navigation and one-Escape close with focus restoration PASS; Windows shortcut hint corrected. Frontend194, lint/type/build PASS; bounded search tests PASS | PASS |
| UX-VIEWS | Saved filters/chips/sort/columns/table-detail/task center | `/tasks` uses bounded saved research/update APIs; `/experiments` applies server-wide search/status/mode/sort before pagination, stores one optional local view, and retains temporary filters in the list history entry | Chrome zh/en task center linked to exact saved study/update receipt. Saved research view survived reload. On 2026-09-23 Chrome 390×844 task center and research list had document width 375, no page overflow, visible local table-scroll hint. A temporary `M1` search was lost after detail/Back; history-entry fix then retained the unsaved query and five matching results on the same path. Original filter and viewport were reset. Focused28/full frontend203, lint/type/build PASS. Broader matrix remains | IN_PROGRESS |
| UX-CHART | Exact hover/legend/benchmark/date range/equity-drawdown-trade link/table; bounded loading | SVG exact data + linked experiment collections | In-app browser 2026-09-23: historical 20-session run benchmark toggle/date 2011-03-23 linked to six fills and the exact account snapshot, while full-run return stayed −0.47%; 293-session result paged 100/100/93 with full-run return still +4.67%. A real synthetic run retained one plotted benchmark line and an enabled toggle. A gap-page component test now verifies no phantom benchmark/drawdown legend or benchmark scale contribution, with bilingual unavailable notices; frontend205/lint/type/build PASS. Real browser missing-series state, keyboard/hover and wider large-page matrix remain | IN_PROGRESS |
| UX-ERROR | No data/permission/offline/timeout/no match/no trades have next step | Shared load panel distinguishes typed 401/403/404/408 and offline TypeError; raw diagnostic behind disclosure | Chrome real 404 dataset offered safe workbench exit. On 2026-09-23 isolated Chrome153, aborting only localhost:8000 API requests showed two actionable offline panels; after restoring transport, one retry refreshed both real data and recent studies, and the top service-status control independently returned to online. Injected HTTP403 initially exposed a misleading generic service-start message in ProductError; typed 401/403, 408 and TypeError now show distinct bilingual permission, timeout and offline guidance while retaining explicit retry. Isolated Chrome injected 403/408 and restored the real cached date after retry; frontend211/lint/type/build PASS. These are fault-injection UI checks, not real permission grants. Chrome `/experiments` no-match search showed a remove-filter/reset next step; reset restored the saved result. A real persisted 293-session result filtered to 2010-01-04 showed zero trades with clear-or-widen guidance; clearing dates restored 18 trade rows without changing full-run metrics. Clean-install no-data path was checked separately in U1; wider failure and screen-reader matrix remain | IN_PROGRESS |
| QA-VISUAL | 1440×900,1280×800,1024×768,390×844; two themes/locales; key 200% zoom | Neutral shell and product pages | Home1440 and mobile390 basic checks. On 2026-09-23 the actual historical result page in the in-app browser had document widths 1425/1265/1009/375 at viewports 1440/1280/1024/390 respectively, with no page-level overflow; Chinese light at 390 and English system-dark at the other widths were visually inspected. A separate real-Chrome 720×450 CSS-viewport proxy for a 1440×900 window at 200% found the Workbench primary action below the first screen (507–549px); compact styling moved it to 387–429px, with no page overflow at 720, 390 or 1440. [Before](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/workbench-css-720x450.png) / [after](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/workbench-css-720x450-fixed.png) are agent screenshots outside Git. The proxy is not actual browser zoom; full zoom and cross-page/theme/locale checks remain | IN_PROGRESS |
| QA-A11Y | Keyboard/focus/semantic dialogs/live status/reduced motion/AA contrast+targets | Shared semantic controls and responsive shell | In-app browser 2026-09-23 at 390×844 measured the top data-status link at 343×20px; a shared CSS target change made it 343×40px without page overflow (document375px). A repeat wizard DOM geometry pass found 35 visible controls and none below 24px. A separate mobile paper-session list audit found its shared `.monoLink` target only 86×14px; table-scoped CSS raised it to 86×40px, also fixing the legacy backtest list. Both pages retained document width375/client width375 at 390×844; desktop paper row is 53px high at1440. On 2026-09-23 isolated Chrome153 AX trees of nine primary routes had no unnamed exposed button/link/textbox/combobox/checkbox/switch/menuitem. Home text links were measured at 20–21px high, then raised to 40px in shared styles; Chrome at 390×844, 720×450 and 1440×900 confirmed all four links at 40px, no page overflow, and the 720px primary CTA still inside the first viewport. [Narrow screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/workbench-links-720x450.png) stays outside Git. Direct-load focus was found on main/step heading, bypassing the first-Tab skip link; shared route focus and wizard-step focus now skip the initial mount only. Chrome at 390×844 confirmed first Tab reaches the skip link on both direct URLs, while in-app navigation focuses main and a step change focuses its heading. Focused35 and full frontend210, lint/type/build PASS. A separate Chrome153 1280×800 computed-color check found the old search-field border at 1.17–1.48:1 against adjacent light/dark colors; the form-only `--field-border` token raised sampled ratios to 3.41–4.03:1 without document overflow. [Before](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/field-border-before.png) / [after](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/field-border-after.png) screenshots stay outside Git. Four-route light/dark text samples had no sub-threshold computed-color result using nearest opaque ancestor, but this is not a complete contrast audit. This is not a full WCAG 2.2 AA or screen-reader audit | IN_PROGRESS |
| QA-PERF | Immediate feedback; measured local interaction p95 target≤200ms; bounded charts/tables | Research archive and result/compare routes loaded on demand; initial JS entry chunk 549.12→409.17 kB minified (169.44→129.31 kB gzip) | On DESKTOP-3EOROGR, actual isolated Chrome 153 at 1440×900 with local populated database: 30 warm Workbench↔Strategies route clicks from Playwright click start to visible h1 had p50 15.6ms/p95 32ms/max 48.2ms, including automation overhead. A separate persisted 293-session result page (138 currently rendered table rows) took cold 560ms and 10 warm full reloads p50 883ms/p95 923ms to show Total return; this is document/data-load latency, not the same interaction metric. API requests themselves took ≤12ms in a warm trace; wider interaction sample, production build, 200% zoom and large-data diagnosis remain | IN_PROGRESS |
| QA-ENGINE | Decimal/server validation/idempotency/task isolation; same financial path | Existing financial path + independent queue | 862 backend tests; actual 2011 exploratory run completed; synthetic clearly separated | IN_PROGRESS |
| QA-REVIEW | Implement→browser review→fix→recheck; independent read-only review resolved | Independent backend+frontend code/test review | Reported races/idempotency/format/routing defects corrected; final browser repeat pending | IN_PROGRESS |
| M4-DATA-INTEGRITY | Application and formal-history persistence, isolated tests, recoverable backup | Suite-wide test-DB guard and verified additive restore | Live DB was found missing formal 1/3/310 ledger and later paper accounts. Formal ledger and four pre-backup accounts were restored atomically; `4b64380f` and `07d72259` remain absent. Live-config pytest was rejected; isolated backend969 PASS/one optional skip with live counts stable. The post-recovery dump restored into a new database, with 44/44 public tables matching live by row count and sorted-row hash. This same-disk dump is not independent disaster recovery and missing-history disposition remains open | FAIL |
| QA-RELEASE | Full backend/frontend/lint/types/build/migrations/durability/CI/compatibility | Incremental suites and reversible migrations | Earlier isolated migration and frontend checks remain valid. 2026-09-23 isolated backend969 PASS/one optional archive skip and PR32 `b060e9f` CI35915906461 backend/frontend/compose PASS; however the live DB data-loss incident makes the current release/durability gate FAIL. Frozen research files were not changed; formal DB rows were restored from backup | FAIL |
| M5-DELIVERY | New/old screenshots + key recordings, bilingual manual/demo/start/recovery/rollback, mode freshness/limits | Draft [Chinese](USER_GUIDE.zh-CN.md) and [English](USER_GUIDE.en-US.md) guides | Both draft guides cover current UI, mode/date boundaries, recovery and rollback. Docker Desktop 4.92.0 login autostart is enabled; four project containers have `unless-stopped` in Compose and runtime. A non-destructive Docker Desktop restart recovered all four services with API/frontend HTTP200, Redis PONG, persistent volumes/images and unchanged live ledger counts 1/3/310 research, 5/417 paper, 8 personal jobs and 4 update jobs. The two idle test-DB containers were returned to their original healthy state. This is engine-restart evidence, not full Windows reboot/login acceptance. PR32 CI35915906461 backend/frontend/compose PASS; screenshots/recordings and operator review remain incomplete | IN_PROGRESS |
| M5-PUBLISH | Small feature PRs reviewed+CI+browser→merge; v1.2.0 only after all required rows pass | feature/product-experience-v1.2 | v1.1 remains immutable | NOT_RUN |

PRODUCT_GOAL_COMPLETE = NO. Remaining required work is the full non-PASS set above.

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
