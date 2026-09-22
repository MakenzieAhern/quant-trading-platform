# v1.2 Product Experience Edition

Authoritative product objective, accepted 2026-09-22. Baseline: published v1.1.0,
main `f88b5c60d29fc1a928b59daf1c2e7818395b7702`, merged PR #12.
This file and [state](../../.product/state.json) govern product work; historical
`.research` records describe frozen research and are not the product work queue.

## Outcome and scope

A non-financial personal user can, entirely in the local bilingual UI: understand
the platform → inspect data → choose/configure a strategy → run an exploratory
A-share backtest → understand/compare results → create a dated risk-aware simulated
rebalance plan → track a deliberately started simulated account. All U1–U8 and
the acceptance matrix are required; a fixture or mock is not a substitute.

Keep the modular monolith, React/TypeScript/i18n, data, APIs, PostgreSQL, RiskEngine,
OMS, Portfolio and paper runtime. Add missing application APIs incrementally.
No live brokerage/money, HK/US expansion, ML/GPU, automatic strategy optimization,
commercial purchases, security-policy changes or public multi-user deployment.
Preserve repo visibility, v1.1 tag, frozen datasets/evidence/methodology/reports and
consumed Official OOS lock. New experiments use independent identity/storage and
explicitly inspected historical periods, never new unseen/OOS claims. If old
research is defective, retain originals and record impact; validate fixes separately.

## Required user capabilities

| ID | Required behavior |
|---|---|
| U1 | Useful first page with one primary guided-backtest action and existing-research secondary action. Skippable/reopenable orientation explains historical research, historical replay, synthetic demo, and new-market forward simulation. Clean installs have a labeled demo. Returning users see drafts, recent studies and data state, without repeated onboarding. |
| U2 | Only registered executable strategies, explained in plain Chinese/English: buy/sell rules, rebalance cycle, risks, supported parameters, data needs and existing evidence. Config drafts and saved versions; no implied profitability recommendations. |
| U3 | Four steps: strategy → cash/dates/universe → costs/risk → confirm. Server validates all parameters, data bounds and strategy support. Durable independent real jobs reuse financial engines; real phase/work-count or phase/elapsed time; idempotency, leave/refresh/reopen, backend cancellation/retry/recovery. Persistent summary, back/save/restore/exit confirmation. Formal reports read-only. |
| U4 | Reopen and compare 2–3 studies; flag differences in dataset/version, dates, costs, cash, risk and strategy version. Show return/drawdown/cost/benchmark/limitations before expandable fills/audit; null stays unknown. Explain non-fills and costs. Export metadata-bearing reports and formula-safe CSV. |
| U5 | Security search/watchlist, raw/adjusted research view, update/as-of timestamps, incremental updates, gap diagnosis, retry and task history over existing cache. Preserve provider/rule-effective-date/rate/license/provenance records. Never refetch full 2010–2025 archive for UI. |
| U6 | Simulated plan from selected strategy/config, actual data and account: candidates, weights, proposed buy/sell quantities, cash required, reasons and risk rejections. Every plan has as-of, snapshot and config version. Stale data never labeled today's advice; insufficient data cannot yield fake executable plans. Simulation only. |
| U7 | Separate synthetic demo, historical replay and genuinely new-market forward sessions/results. Start/pause/stop, risk limits, holdings/cash/orders/fills/logs and explicit disconnect/restart recovery. New-market mode can be delayed/EOD, never falsely tick realtime. No continuous worker without user start. Forward acceptance requires lawful available source, an actual completed trading day's data arriving AFTER session start with receipt time, plan and constrained simulated processing. Historical backfill and synthetic 2030 only count as integration/demo. Long-run evidence must wait for time. |
| U8 | Same component tree in Chinese/English, all important copy/status/errors/help/accessible names translated. Locale change preserves form and financial dates. Settings: system/manual persisted theme, language, motion, explicit market up/down colors, data preferences. Help explains backtests, drawdown, win rate vs return, benchmark. |

## Experience contract

- Neutral warm-white/cool-gray light and graphite dark; indigo primary actions;
  system theme default, persisted manual choice; system fonts, 14–16px body,
  Chinese line-height and tabular numerals. No remote-font dependency.
- Fixed sidebar + compact topbar + workspace + contextual panel. Workbench,
  markets/watchlist, strategies, research, simulated accounts, data; secondary
  help/settings. Preserve old routes/deep links. Audit data belong in advanced
  research archives, not the novice landing page.
- Topbar: location, global search, data mode/date, locale, theme. Distinguish
  service online, data freshness and audit status. Signed textual market values;
  market colors separate from success/error and never switch implicitly by locale.
- List/card opens accessible light detail panel retaining filter/scroll; independent
  URL for complex detail; Esc/Tab/back and trigger-focus restoration.
- Ctrl/Cmd+K uses registered safe actions: pages, strategies, studies, watchlist,
  help. Visible alternative entry. Saved views, filter chips, sorting, columns,
  table-to-detail and task center.
- Charts: exact hover values, clear legend, benchmark toggle, displayed-date range,
  linked equity/drawdown/trade dates, accessible tables and bounded data loading.
  Display ranges never change the stored full-run metrics.
- Feedback 120–160ms, panels 180–260ms, steps 220–320ms, optional module stagger
  30–50ms are measured design targets. Prefer opacity/transform, no fake progress,
  no result delays/profit celebrations/animated money recalculation or replayed
  entrance on each socket event. Reduced-motion and explicit motion-off preserve
  all functionality.

## Engineering and safety contract

Financial authority stays backend Decimal/exact strings: cash, quantities, costs,
returns and risk. Preserve validation, durable idempotency, isolation, cancellation
and persistence. Distinguish UTC server time and Asia/Shanghai trading dates.
Existing audited archives connect through optional `RESEARCH_DATA_ROOT` in local
`.env` (the parent of `cn-a-research-20100101-20251231-v1`). Compose mounts it
read-only at `/workspace/research`; host execution uses `RESEARCH_DATA_PATH`.
The default `./data/research` supports clean installs with the explicit synthetic
demo. Missing archives never trigger download or pretend historical availability.
Reuse components/libs first; at most one accessible component/motion/chart solution
per purpose after official API/license/compatibility/size/maintenance checks and pinning.

Check current PID, command, start time and checkpoint before any process action;
repository/queue/DB have explicit owners. No Docker factory reset, volume/image/DB
or WSL deletion. Stop a route on 401/403/CAPTCHA/payment; lawful independent sources
and existing caches remain available. Bounded retry/backoff/circuit breaking only.
Three identical failures require a new falsifiable hypothesis and recorded decision.

## Milestones and acceptance

M0: live host/Git/release/process/API/data audit; before screenshots and four states
(new user, existing data, empty DB, service error); reference comparison and matrix.
M1: visible AppShell/home/theme/onboarding, strategy detail and a real guided
strategy → configuration → result path; browser review/fix/recheck.
M2: apply system across markets/watchlist, strategies, archives/comparison/tasks,
accounts/data/help/settings; compatible legacy links.
M3: finish drafts/jobs/cancel/recovery/comparison/update/plans/real data chain.
M4: full visual/interaction/financial/API/accessibility/performance/error/restart
loop and read-only independent review with fixes.
M5: screenshots/interaction recordings, bilingual manual/demo, complete tests,
limitations, rollback and releasable v1.2.0 after all mandatory gates.

Test 1440×900, 1280×800, 1024×768 and 390×844, both themes/locales and key 200%
zoom cases. No page-level mobile overflow; local table scroll clearly labeled.
Keyboard, semantic dialogs/buttons, focus, live status, reduced motion and relevant
WCAG 2.2 AA; target controls 40–44px with valid compact target spacing. Measure
click feedback and local p95 ≤200ms target with machine/browser/data/cache/method;
diagnose misses, do not erase targets. Distinguish agent walkthrough from real
novice user testing. Test milestones with full backend/frontend/lint/types/build,
reversible migration, durability and CI, without rerunning formal studies.

## Delivery and recovery

Use `feature/product-experience-v1.2` from verified main; small coherent feature
slices and PRs, correct identity, normal push. PR #12 is historical. Merge only
after independent review/separate recheck, CI, browser evidence and compatibility;
never bypass protection/force-push main/overwrite tags. Release v1.2.0 only when
every mandatory flow passes. Repo stays local single-user and visibility unchanged.

Update `.product/state.json` at each checkpoint/milestone with owner/processes,
last actual success, failures/not-run/external blocks, next exact action. Read this
master and state after recovery. Keep raw/private data, secrets and large/sensitive
evidence outside Git. Decisions go in existing orchestration DECISIONS, prefixed
v1.2; frozen research records stay unchanged. After two iterations without a new
passing flow or reduced defect, change execution approach, not product scope.

Final delivery must link usable app/start/recovery, before/after screenshots and
recordings, per-flow evidence/tests/CI, actual mode/data freshness/limitations,
branch/PR/release/rollback and Chinese/English nontechnical manuals. Only all U1–U8
verified means PRODUCT_GOAL_COMPLETE; otherwise report PARTIAL/BLOCKED explicitly.
