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
| U1-START | Clean user → one primary guided action → strategy; skip/reopen guide; returning draft/recent/status | Workbench / | Chrome primary CTA, four-mode guide/Esc, restored draft, real as-of; recent-run recheck pending | IN_PROGRESS |
| U1-DEMO | No-private-data install can run clearly marked synthetic demo; all four modes explained | Registry + standalone synthetic experiment | Actual API demo c4a46658 succeeded; clean-install UI still pending | IN_PROGRESS |
| U2-STRATEGY | Registered strategies, plain rules/cycle/risk/data/evidence; drafts and saved versions | /strategies and detail drawer | Real registered strategy plain-language Chrome evidence; saved versions pending | IN_PROGRESS |
| U3-WIZARD | Four steps, advanced disclosure, summary, back/save/restore/exit; locale preserves inputs | /research/new four-step form | Draft/locale/summary live checks; full submit/exit browser proof pending native-dialog interruption | IN_PROGRESS |
| U3-JOB | Validated actual A-share job; stages/counts; persistent URL; refresh/reopen; idempotent duplicate | /api/experiments; independent durable manager | Actual synthetic+historical jobs; duplicate same key returns same ID; UI result pending | IN_PROGRESS |
| U3-RECOVER | Real cancellation/retry/interruption; no partial results called success | cancel/retry and durable terminal states | Running cancellation; restart INTERRUPTED; linked retry SUCCEEDED; UI lifecycle pending | IN_PROGRESS |
| U3-ISOLATE | Independent exploration names/store; formal reports/OOS/freeze unchanged, dates labeled inspected | Separate product_research_jobs/rows, readonly archive | No .research diff; frozen hashes unchanged; formal 1 dataset/3 runs/310 trades before-after | IN_PROGRESS |
| U4-RESULT | Return/drawdown/cost/benchmark/limits, null semantics, true records and reasons | Personal summary + paginated exact result APIs/UI | Actual API results include limits/reasons/null; UI render pending | IN_PROGRESS |
| U4-COMPARE | Reopen/compare 2–3; six config differences indicated | Pending | API + browser tests | NOT_RUN |
| U4-EXPORT | Metadata report and formula-safe CSV | Pending | Injection/precision tests + downloaded artifact | NOT_RUN |
| U5-MARKET | Search/watchlist/raw-adjusted/date/source view | Pending | Cached dataset read only | NOT_RUN |
| U5-UPDATE | Incremental update/gaps/retry/history with source/license/rules/limits; no archive refetch | SOURCE_READINESS.md candidate audit | BaoStock anonymous public per-security path probed; bulk EOF fails boundedly; ingestion pending | IN_PROGRESS |
| U6-PLAN | Real candidates/targets/quantities/cash/reasons/rejections; as-of/snapshot/version; insufficiency/staleness | Pending | API invariants + result→plan browser | NOT_RUN |
| U7-MODES | Three isolated account modes, start/pause/stop/risk/ledger | Existing synthetic paper retained | Mode isolation/lifecycle tests | NOT_RUN |
| U7-RECOVER | Socket disconnect/reconnect + backend restart don't fake/duplicate fills | Existing runtime interruption | Product retry/resume integration | NOT_RUN |
| U7-FORWARD | Lawful source + completed real session data arriving after user session start; receipt times/plan/simulation | Public-source candidate assessed, forward session not implemented | Historical probe is not forward evidence; real after-start arrival still required | NOT_RUN |
| U8-I18N | One tree; translated important UI/error/help/a11y; switching retains config/date | Existing i18n | Legacy create remains English in Chinese | FAIL |
| U8-SETTINGS | System/manual themes, language/motion/market colors/data preferences; explanatory help | Pending | Persistence, OS preference and browser | NOT_RUN |
| UX-DETAIL | Drawer keeps filters/scroll, Esc/Tab/back/trigger focus, URL | Pending | Keyboard browser | NOT_RUN |
| UX-COMMAND | Safe Ctrl/Cmd+K + visible entry searches pages/strategy/studies/watchlist/help | Pending | No eval/dynamic operations | NOT_RUN |
| UX-VIEWS | Saved filters/chips/sort/columns/table-detail/task center | Pending | Reload/reopen | NOT_RUN |
| UX-CHART | Exact hover/legend/benchmark/date range/equity-drawdown-trade link/table; bounded loading | Existing SVG charts | New range does not rewrite full metrics | NOT_RUN |
| UX-ERROR | No data/permission/offline/timeout/no match/no trades have next step | Pending | Isolated service/DB failure browser tests | NOT_RUN |
| QA-VISUAL | 1440×900,1280×800,1024×768,390×844; two themes/locales; key 200% zoom | Neutral shell and product pages | Home1440 and mobile390 basic checks; full matrix/zoom not complete | IN_PROGRESS |
| QA-A11Y | Keyboard/focus/semantic dialogs/live status/reduced motion/AA contrast+targets | Pending | Measured audits + agent keyboard walk | NOT_RUN |
| QA-PERF | Immediate feedback; measured local interaction p95 target≤200ms; bounded charts/tables | Pending | Machine/data/browser/cache/method to record | NOT_RUN |
| QA-ENGINE | Decimal/server validation/idempotency/task isolation; same financial path | Existing financial path + independent queue | 862 backend tests; actual 2011 exploratory run completed; synthetic clearly separated | IN_PROGRESS |
| QA-REVIEW | Implement→browser review→fix→recheck; independent read-only review resolved | Independent backend+frontend code/test review | Reported races/idempotency/format/routing defects corrected; final browser repeat pending | IN_PROGRESS |
| QA-RELEASE | Full backend/frontend/lint/types/build/migrations/durability/CI/compatibility | M1 local suite and reversible migration | 862 backend/108 frontend tests and lint/type/build PASS; CI and full product gates pending | IN_PROGRESS |
| M5-DELIVERY | New/old screenshots + key recordings, bilingual manual/demo/start/recovery/rollback, mode freshness/limits | Pending | All links validated before release | NOT_RUN |
| M5-PUBLISH | Small feature PRs reviewed+CI+browser→merge; v1.2.0 only after all required rows pass | feature/product-experience-v1.2 | v1.1 remains immutable | NOT_RUN |

PRODUCT_GOAL_COMPLETE = NO. Remaining required work is the full non-PASS set above.
