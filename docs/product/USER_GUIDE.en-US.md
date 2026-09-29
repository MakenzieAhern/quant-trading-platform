# A-share workstation guide (v1.2 development build)

This guide describes the local work-in-progress UI, not a released v1.2.0. The app is for local research and simulation only: it has no live broker connection and sends no real-money orders. Historical performance cannot guarantee future returns.

## Open the app and check the data

When the services are already running, open the [workbench](http://localhost:5173/) in a browser on this PC. Check “Service online” separately from the data mode and date. An online service does **not** mean prices are current or that their source has passed audit. Use the [data center](http://localhost:5173/data) to inspect available data, dates and provenance. Language and theme are in [Settings](http://localhost:5173/settings); changing language does not change trading dates or calculations.

Project containers are configured to recover with the Docker Desktop engine. The existing Windows sign-in task did run at 23:41 Sydney time on 2026-09-28, but the Docker backend exited twice soon afterward. The cause is unproven; the currently stable services followed a later manual launch. Direct post-login opening is therefore **not** guaranteed. If the page is unavailable, open the already-installed Docker Desktop from the Windows Start menu and wait until its engine is running, then refresh the original page. If it still fails, ask the maintainer to check the project services. Do not reinstall Docker, remove volumes or reacquire the archive. Reopen the same task link after recovery and verify saved tasks and results. This is a terminal-free manual recovery step, not proof that sign-in autostart works.

Use the exact `http://localhost:5173/` address above rather than replacing its hostname. This PC's browser cross-origin configuration currently allows only that frontend origin to access the API; `127.0.0.1:5173` can render the page while reporting an unconfirmed service response. Return to the workbench link first; do not change browser security settings.

## Keep the four modes separate

| Mode | Appropriate use | Not evidence of |
|---|---|---|
| Historical research | Personal exploration on stored A-share data | An unseen test or a forecast of future returns |
| Historical replay | Walk a simulated account through stored trading sessions | Newly arriving live or end-of-day data |
| Synthetic demo | Learn controls and pages without private historical data | Market behavior or investment returns |
| New-market forward simulation | Target mode: process newly completed sessions received after user start | **Not yet available**; data rights, current rules and actual-arrival acceptance remain open |

## From strategy to result

1. On the [workbench](http://localhost:5173/), select “Start guided backtest.” Read the registered strategy's rules, risks and data needs. A strategy description is not a return recommendation.
2. Complete the four steps: strategy; capital, dates and stock universe; costs and risk; confirmation. Expand advanced settings only when needed. Save a draft to continue from home. Broker commission and its minimum are simulation assumptions, not verified quotes; check the result's actual cost breakdown. Check the data-mode and date labels before submitting.
3. Find the same durable task in [Experiments](http://localhost:5173/experiments) or the [Task center](http://localhost:5173/tasks). Leaving or refreshing its page does not itself create another task. Only a “Complete” task has a complete result; cancelled, interrupted and failed records are never shown as successful.
4. Read return, maximum drawdown, costs, benchmark and limitations first; then expand trades, holdings, risk decisions and fill reasons. “Show full precision” changes display only. Filtering shown trading dates does not recompute full-period metrics. Expand technical details for the original reason code.

   The chart shows up to 100 trading-session points per page. Use “Show benchmark” to toggle its curve; hover a point or use “Inspect a trading date” to read available full-precision equity, benchmark and drawdown values for that date. “Show trades and holdings for this date” filters and opens those records; clear the focused date to restore the previous range. Open “Exact chart data” for the table and use the page controls for other points; both support keyboard use. Benchmark toggling, date selection and paging change only the display, not the full-period metrics above. Missing values are not zero.
5. Select 2–3 completed studies to compare, checking data version, date range, capital, costs, risk and strategy version first. The page checks only six saved configuration conditions; it does not verify implementation fingerprints, execution-model versions or effective statutory costs. Inspect exported metadata before calling a comparison controlled. A saved simulated rebalance preview, where present, must be read with its as-of date, data snapshot and risk rejections; older results may have no preview. The result page can download a metadata JSON report and CSV for the selected record type; date filters limit exported records while JSON summary metrics remain full-period. Both downloads completed in actual Chrome on this PC. If the report is prepared but your browser does not start the download, use “Save prepared report” and check browser downloads. If preparation fails, check service status before clicking the download button again; a click alone does not prove the file was saved.

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

## Simulated accounts and recovery

In [Simulated accounts](http://localhost:5173/paper), the creation form defaults to a clearly labeled 2030 synthetic A-share demo; the legacy AAPL fixture remains an explicit non-A-share choice. Audited historical replay can be created only when Data center shows that archive is available. Start the account explicitly; the page supports pause, resume and stop, with cash, holdings, orders, fills and logs. None are real trades. New-market forward mode is not yet usable; a historical catch-up is not a new-market receipt.

On a completed A-share historical research result, “Review these settings in a separate historical paper account” opens a new-account form with capital, strategy, universe, cost and risk settings copied for review. It does not copy the study's returns or rebalance preview, create or start an account, or submit an order. Each historical replay is limited to 93 calendar days; a longer study leaves the new start date blank for you to choose explicitly. The new account has its own data snapshot and ledger, with a rebalance plan only when conditions allow. Create and start it only after reviewing the settings.

If creation times out, disconnects or returns an uncertain error, check the [session list](http://localhost:5173/paper) first; a temporarily missing entry does not prove that creation failed. Reopen [Create paper session](http://localhost:5173/paper/new) in the same browser profile at the `http://localhost:5173` origin, review the exact settings under “Saved paper-account creation requests,” then choose “Retry saved request.” This reuses the request and ID saved before the first POST; if the server already accepted it, the same account opens. A confirmed receipt offers “Open saved paper account.” A different request is blocked until every unconfirmed creation is resolved. Only explicitly choosing “Create another paper account” and submitting after that generates a new request ID. If a retry is rejected after an uncertain earlier attempt, its key remains saved for reconciliation; do not clear it or assume the first attempt failed. Another browser, device or origin, or cleared browser data, may not have the locally saved request; if it cannot be read, ask the maintainer to reconcile it before creating another account.

For a cancelled or interrupted research task, open its detail page and read the explanation. “Start or reopen linked retry” uses the saved configuration without overwriting the original record; repeated requests reopen the linked attempt.

During a paper-account disconnection, displayed cash and holdings may be only the last verified snapshot, not a current balance. After reconnection, check session status, trading date and records before acting. A failed start, pause or stop response does not prove that the command was not applied. A paused account can be explicitly resumed when the page offers “Resume replay”; backend restart does not start it automatically. An “Interrupted” session keeps read-only records and does not backfill fills automatically; follow its guidance before deciding to create another session. Normal process restart after pausing was verified in isolated historical replay, not sudden power loss, database-loss recovery or independent disaster recovery.

For offline, timeout or missing-data errors, try the page's retry or return action. If it persists, give the task link and displayed technical reason to the maintainer; never clear PostgreSQL, Redis or Docker volumes as a troubleshooting shortcut.

This development database had a recovery incident: two paper sessions created after the usable backup (short IDs `4b64380f` and `07d72259`) could not be recovered. Do not treat them as queryable durable records. A backup on the same physical disk is not independent disaster recovery. Until this gap is resolved, do not rely on this build as a long-term account ledger.

## Release and rollback

This development build is unreleased. The published stable baseline is v1.1.0; formal research reports and frozen data remain read-only. There is **no verified in-place v1.2→v1.1 rollback**: v1.1.0 does not know the current database's newer Alembic revisions. Do not check out the old tag and run `make up` against the current volume. A maintainer must first follow the [deployment and rollback gate](../DEPLOYMENT.md) using an independent pre-upgrade backup in an isolated rehearsal; without that backup and rehearsal, safe rollback cannot be claimed. Do not overwrite the old tag, rerun Official OOS or delete database volumes. Current gaps include lawful forward-market authority, full accessibility/performance acceptance and reboot-tested terminal-free startup. This is not a v1.2.0 final delivery.
