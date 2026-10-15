# A-share workstation guide (v1.2 development build)

When Data center shows “View only · new execution blocked,” use “What can I do now?” to browse that same cached dataset, inspect saved research, or open the focused recovery help. These links do not start tasks. Repeated submissions, changed dates or raw-price updates cannot repair the same version; preserve original records and ask the maintainer to verify a corrected version. Existing returns remain subject to the displayed quality warnings.

This guide describes the local work-in-progress UI, not a released v1.2.0. The app is for local research and simulation only: it has no live broker connection and sends no real-money orders. Historical performance cannot guarantee future returns.

## Open the app and check the data

When the services are already running, open the [workbench](http://localhost:5173/) in a browser on this PC. Check “Service online” separately from the data mode and date. An online service does **not** mean prices are current or that their source has passed audit. Use the [data center](http://localhost:5173/data) to inspect available data, dates and provenance. Language and theme are in [Settings](http://localhost:5173/settings); changing language does not change trading dates or calculations.

Checked October 14, 2026: the local page and health endpoint work, and GitHub CI has recovered with successful runs. Opening this local program does not require waiting for CI; code checks do not grant data-execution approval. “Cached data available” means readable, not execution-approved. “View only · new execution blocked” means that version cannot start a new study or historical replay. The current historical archive still has source and economic-completeness gaps. Old reports and account records remain inspectable; waiting for GitHub, repeatedly restarting Docker or choosing different dates cannot repair those data issues.

Current check (October 14, 2026): the frontend responds, PostgreSQL, Redis and the backend are healthy, and the backend's project-code mount is readable. A loopback-only static container still serves the frontend, not the original Vite development container; you can use the address above to view it. This check does not guarantee arbitrary new mounts, sudden-power-loss recovery or unattended Windows-login startup. If the page is unavailable, open the already-installed Docker Desktop from the Windows Start menu and wait until its engine is running, then refresh the original page. If it still fails, ask the maintainer to check services and mounts; do not recreate project containers, reinstall Docker, remove volumes or reacquire the archive. Reopen the same task link after recovery and verify saved tasks and results. This is a terminal-free manual recovery step, not disaster-recovery or unattended-startup acceptance.

Keep using `http://localhost:5173/` to recover drafts and uncertain requests saved under that browser origin. `http://127.0.0.1:5173/` can now reach the local API too, but it is a **different browser origin** and does not share those saved local records. Do not switch between the two addresses while reconciling an uncertain study or account-creation request. If the page reports the service unavailable, check Docker using the recovery steps above; do not change browser security settings.

## Keep the four modes separate

| Mode | Appropriate use | Not evidence of |
|---|---|---|
| Historical research | Personal exploration on stored A-share data once that version is approved for execution | An unseen test or a forecast of future returns |
| Historical replay | Walk a simulated account through stored trading sessions once that version is approved for execution | Newly arriving live or end-of-day data |
| Synthetic demo | Learn controls and pages without private historical data | Market behavior or investment returns |
| New-market forward simulation | Target mode: process newly completed sessions received after user start | **Not yet available**; data rights, current rules and actual-arrival acceptance remain open |

## From strategy to result

1. On the [workbench](http://localhost:5173/), select “Start guided backtest.” If a draft already exists, choose “Continue saved draft” to keep its step and request ID, or “Back up draft and start new” to retain it as a browser version before opening a fresh step-1 form with a new request ID. Neither choice submits a study. Read the registered strategy's rules, risks and data needs. A strategy description is not a return recommendation.
2. Complete the four steps: strategy; capital, dates and stock universe; costs and risk; confirmation. Expand advanced settings only when needed. Save a draft to continue from home. Broker commission and its minimum are simulation assumptions, not verified quotes; check the result's actual cost breakdown. Check the data mode, dates and current execution admission before submitting. A failed or unverified source, or an explicit execution denial, also blocks submission from an old draft: the wizard returns to data selection while retaining cash and dates for inspection. Acknowledgment does not remove the restriction. Quality notices explain known economic-coverage gaps or unknown completeness; they neither repair data nor financially validate returns or quantities.
3. Find the same durable task in [Experiments](http://localhost:5173/experiments) or the [Task center](http://localhost:5173/tasks). Leaving or refreshing its page does not itself create another task. Only a “Complete” task has a complete result; cancelled, interrupted and failed records are never shown as successful.
4. Read return, maximum drawdown, costs, benchmark and limitations first; then expand trades, holdings, risk decisions and fill reasons. “Show full precision” changes display only. Filtering shown trading dates does not recompute full-period metrics. Expand technical details for the original reason code.

   The chart shows up to 100 trading-session points per page. Use “Show benchmark” to toggle its curve; hover a point or use “Inspect a trading date” to read available full-precision equity, benchmark and drawdown values for that date. “Show trades and holdings for this date” filters and opens those records; clear the focused date to restore the previous range. Open “Exact chart data” for the table and use the page controls for other points; both support keyboard use. Benchmark toggling, date selection and paging change only the display, not the full-period metrics above. Missing values are not zero.
5. Select 2–3 completed studies to compare, checking data version, date range, capital, costs, risk and strategy version first. Requested interval is what you selected when creating the study; actual result interval is the saved result coverage, and these may differ. The six checks include both date-boundary pairs, not every observation within them. They do not verify implementation fingerprints, execution-model versions or effective statutory costs. Inspect exported metadata before calling a comparison controlled. If a simulated rebalance preview is present, read it with its date, data snapshot and risk rejections; older results may have none. On a result page, use “Download metadata report (JSON)” for a report with saved configuration and provenance, or choose a record type and use “Download records (CSV)” for its details. Displayed-date filters limit exported records only; JSON summary metrics still describe the full interval. On 2026-10-14, the installed local page was checked in the in-app browser: JSON, equity CSV and the fallback save link produced actual files, and filtering preserved full-period metrics. This does not verify every browser or export edge case. If the report is prepared but your browser does not start the download, use “Save prepared report”; check the browser download record and actual file before treating it as saved. If preparation fails, check service status before clicking the download button again.

### Recover a list view or task

Filter studies by name, status and data mode, choose a sort order, and hide optional columns under “Columns.” A filter chip's × removes only that condition. Use Tab to reach it, then Enter; focus returns to “Study view settings.” Choose “Save this view” to reuse the configuration in a newly opened list. It is saved for this device, browser and origin, not synchronized to an account in the cloud.

Unsaved changes also stay with the current list entry, including refresh and returning from a detail; a saved view does not overwrite them. “Reset view” clears current settings and the saved view, not study results. Open a study's name or “Open experiment,” then use browser Back to return to that link and the list's scroll position. Task center also returns to the original research or raw-request link. If that entry is no longer listed or reading fails, focus moves to visible guidance rather than an obsolete blank position. Opening lists, details or Task center does not run research or fetch market data.

### Formal research archives (read-only)

Another confirmed loader defect (2026-10-07): the old loader blocked only the
suspension start day, potentially missing continuing halts and timestamps.
The fix is included in the current local backend (checked October 14, 2026): it
interprets the whole interval; uncertain opens prohibit execution rather than
imply a normal trading day. This neither establishes illegal past fills nor
removes the current historical-data execution restriction.
Original reports remain; their individual impact is not quantified and their
returns have not been revalidated.

Known engine defect (2026-10-03): the old historical loader could reuse the first
security's single-price non-executable flag for another security in the same
cache group, incorrectly rejecting a normal security. The new version separates
these states. An independent single-price veto remains, so illegal fills are not
established. Prior executed personal/formal candidate results may be affected;
impact on particular saved reports is not quantified. Original reports, frozen
data and the consumed OOS lock remain unchanged. This fix does not revalidate old
returns, and formal research is not rerun to replace its original evidence.

Open an existing report in the [formal A-share archive](http://localhost:5173/research/a-share) and check its Development, Validation or OOS label first. Click “Show benchmark” or press Space to toggle its equity-chart overlay. Paging and language changes on this page retain the display choice without recomputing official metrics or rerunning research. Equity and benchmark each load at most 200 points per page; expand “Show plotted data” for an exact table with at most 100 records per page. Hiding the curve does not remove benchmark values from that table. Long monthly-return values wrap in full on mobile rather than being truncated.

Enter first/last trading dates under “Displayed trading dates,” then choose “Apply dates.” Leave either end blank for an open bound; “Show full interval” resets both. The server filters before pagination, not just the current 200 points. Equity and drawdown date pickers stay linked; hover, click or use Home/arrow keys for exact values. Previewing a date does not query activity. Choose “Show trades and holdings for this date” to query holdings, rebalances and trades for that Asia/Shanghai trading day and move to the linked-date region. Later chart preview/paging does not silently change the confirmed records' date: check “Linked trading date.” “Clear linked date” restores the prior range. The rolling chart retains its independent readout. These actions do not recompute official full-run metrics or monthly returns. Missing values are not zero; no matching holdings does not imply liquidation.

### No confirmation after clicking Run

A timeout, disconnection or server-response error does not prove that no task was created. Use “Check task center” in the error guidance, or the task-center link above, to find the original task by its name, configuration and creation time. If returning to the wizard, restore the original draft without editing its configuration. After refreshing, acknowledge it again before explicitly clicking Run. An unchanged retry retains the same request ID and reopens an already accepted task; editing creates a new request ID and may create another experiment. Do not change parameters and run again just to check whether the first submission succeeded.

This differs from “Start or reopen linked retry” on an explicitly failed, cancelled or interrupted task: a linked retry is a new attempt that preserves the original record, not recovery of an unconfirmed create request.

## Inspect prices, cache and update history

Search for a security in [Markets and watchlist](http://localhost:5173/markets), then inspect its historical dates and source. Raw prices are unadjusted prices for that date. Research-adjusted prices support historical comparisons, not a claim about executable prices. A watchlist saves interest, not orders. The top bar's labeled data-as-of, requested or observed-through date depends on the page; it differs from an observation's trading date and the UTC service-check time.

In [Data center](http://localhost:5173/data), inspect the saved update history under “Incremental raw-data requests.” Open a task to read receipts, observations and unexplained dates. “Refresh” reads saved state; it does not reacquire the entire archive. A linked retry retains the original failed task. Failure or cancellation is not evidence of complete data.

This area is currently a **candidate raw cache, not approved for trading**. “Request complete” only means the bounded vendor request ended, not that usage rights, the current security master, calendar, ST history, rules or corporate actions passed acceptance. New requests need a separate acknowledgment of source-evaluation use. Until those rights and source gates are resolved, do not use candidate observations for research, forward simulation or trading. Allowed dates are request bounds, not proof of a trading session or available data; this does not refetch the whole historical archive.

## Understand the result

- Return describes asset change during that simulated period, not a promise about the future. Check capital, costs and whether the data are synthetic first.
- Maximum drawdown is the largest drop from a previous asset peak to a later low. A profitable final result can still contain a large drawdown.
- Win rate is the fraction of profitable trades. A few large losses can outweigh many small wins; win rate is not return.
- A benchmark is a same-period comparison, not a risk-free return. Check matching dates and data modes.
- Orders can remain unfilled because of suspension, price limits, cash constraints or risk rejection. Read the reason; a signal is not a fill. Unknown values are not zero.

Open [Help](http://localhost:5173/help) for further explanations.

You can also open the top-bar search (or press Ctrl/Cmd+K), type “backtest”,
“drawdown”, “win rate” or “benchmark”, and select the question. Its answer opens
with keyboard focus. Changing language preserves answers you opened or closed.

## Simulated accounts and recovery

Each simulated account represents an independent simulated investor with separate
cash, holdings and records. Daily purchase limits are not pooled across different
accounts; copying the same strategy configuration does not merge them. This is
local simulation isolation, not permission to split real brokerage accounts to
evade limits or evidence that current market data is approved for execution.

The development creation page checks current source availability first; see the current checkpoint for deployment and browser-validation status. Unavailable modes remain visible with reasons. New creation is blocked while the check is pending or has failed. Use “Check data readiness” or “Recheck availability”; rechecking keeps entered cash and dates and never changes a historical selection into a demo. Saved-request recovery above remains independent. If you leave while old receipts are being verified, a late response will not create another account. A request already sent still needs reconciliation as described below; leaving is not cancellation.

Development PnL fields (deployed locally October 13; real-browser recheck pending): trading realized PnL excludes corporate-action PnL such as dividends. New complete snapshots show these separately, together with unrealized PnL, transaction costs and total PnL after costs. Transaction costs include applicable brokerage commission, transfer fees and stamp duty. Older snapshots that did not record corporate-action or total PnL show “—” (unknown), not zero; original ledgers are not rewritten. The new fields do not establish economic completeness of historical source data.

In [Simulated accounts](http://localhost:5173/paper), the creation form defaults to a clearly labeled 2030 synthetic A-share demo; the legacy AAPL fixture remains an explicit non-A-share choice. Creating or starting historical replay requires current data-execution approval: a frozen archive, readable cache or saved account is not approval. New execution on the current historical archive is blocked; saved records remain inspectable. Start an eligible account explicitly; the page supports pause, resume and stop, with cash, holdings, orders, fills and logs. None are real trades. New-market forward mode is not yet usable; a historical catch-up is not a new-market receipt.

For a historical account, read the data-quality notice above cash and equity first; the plan retains the same explanation. “Authoritative portfolio” means the backend's saved ledger state, not verified economic coverage of corporate actions, quantities or returns. If coverage has a known gap or unknown completeness, old amounts, results and plans remain for inspection; that does not mean the gap is repaired or returns are reliable. The current notice is not retrospective proof of coverage on a past day. An absent quality marker is not a quality pass. Opening a detail link with `#simulation-plan` locates the plan once it loads; this navigation does not run the account or submit orders.

On an account detail page, choose “View saved events” below Fills to inspect its persisted event log. It shows at most 50 records at once, newest first; “Older” and “Newer” page through history. “Refresh” returns to the latest saved records. This log does not update live on its own, and it does not recreate missing records.

If a “Calendar control” record appears, it records the trading dates known to that account at that point, not new market data, an order or a fill. Its UTC record time can differ from the replay's trading date; synthetic 2030 dates are not real future observations. “Newer saved events are available” means the journal has new records; choose “Refresh” to read them.

On a completed A-share historical research result, “Review these settings in a separate historical paper account” opens a new-account form with capital, strategy, universe, cost and risk settings copied for review. It does not copy the study's returns or rebalance preview, create or start an account, or submit an order. Each historical replay is limited to 93 calendar days; a longer study leaves the new start date blank for you to choose explicitly. The new account has its own data snapshot and ledger, with a rebalance plan only when conditions allow. Create and start it only after reviewing the settings.

When reading this account's own historical rebalance plan, check the completed trading day, account snapshot date, next accepted session, plan-time cash, estimated cash requirement and risk decisions, and expand “Data and configuration provenance” when needed. The latest balance above is not the plan-time balance, and a historical plan is not today's trading advice.

If creation times out, disconnects or returns an uncertain error, check the [session list](http://localhost:5173/paper) first; a temporarily missing entry does not prove that creation failed. Reopen [Create paper session](http://localhost:5173/paper/new) in the same browser profile at the `http://localhost:5173` origin, review the exact settings under “Saved paper-account creation requests,” then choose “Retry saved request.” This reuses the request and ID saved before the first POST; if the server already accepted it, the same account opens. A browser-saved confirmed receipt must be verified against the current server before opening. A different request is blocked until saved creations are reconciled; “Create another paper account” verifies all saved receipts before assigning a new request ID or posting. If verification fails, keep the original key, inspect the session list and data-recovery status, and try verification later. If a retry is rejected after an uncertain earlier attempt, its key remains saved for reconciliation; do not clear it or assume the first attempt failed. Another browser, device or origin, or cleared browser data, may not have the locally saved request; if it cannot be read, ask the maintainer to reconcile it before creating another account.

For a cancelled or interrupted research task, open its detail page and read the explanation. “Start or reopen linked retry” uses the saved configuration without overwriting the original record; repeated requests reopen the linked attempt.

During a paper-account disconnection, displayed cash and holdings may be only the last verified snapshot, not a current balance. After reconnection, check session status, trading date and records before acting. A failed start, pause or stop response does not prove that the command was not applied. A paused account can be explicitly resumed when the page offers “Resume replay”; backend restart does not start it automatically. An “Interrupted” session keeps read-only records and does not backfill fills automatically; follow its guidance before deciding to create another session. Normal process restart after pausing was verified in isolated historical replay, not sudden power loss, database-loss recovery or independent disaster recovery.

For offline, timeout or missing-data errors, try the page's retry or return action. If it persists, give the task link and displayed technical reason to the maintainer; never clear PostgreSQL, Redis or Docker volumes as a troubleshooting shortcut.

This development database had a recovery incident: two paper sessions created after the usable backup (short IDs `4b64380f` and `07d72259`) could not be recovered. Do not treat them as queryable durable records. A backup on the same physical disk is not independent disaster recovery. Until this gap is resolved, do not rely on this build as a long-term account ledger.

## Release and rollback

This development build is unreleased. The published stable baseline is v1.1.0; formal research reports and frozen data remain read-only. There is **no verified in-place v1.2→v1.1 rollback**: v1.1.0 does not know the current database's newer Alembic revisions. Do not check out the old tag and run `make up` against the current volume. A maintainer must first follow the [deployment and rollback gate](../DEPLOYMENT.md) using a compatible pre-upgrade backup separate from the current database in an isolated rehearsal; restoring the current development baseline does not substitute for it. Without that backup and rehearsal, safe downgrade cannot be claimed. Do not overwrite the old tag, rerun Official OOS or delete database volumes.

You can manually open Docker Desktop, wait for services, then open the local platform; this normal startup and recovery path does not require a terminal command. Corrected unattended Windows-login startup remains untested, as do independent physical disaster recovery and real novice satisfaction; these are additional assurance, not newly mandatory gates. Actual gaps are the lawful genuine forward-market chain, missing-ledger disposition, and consolidated required interaction, accessibility, visual, performance and delivery acceptance. This is not a v1.2.0 final delivery.
