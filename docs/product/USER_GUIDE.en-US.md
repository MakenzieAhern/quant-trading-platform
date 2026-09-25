# A-share workstation guide (v1.2 development build)

This guide describes the local work-in-progress UI, not a released v1.2.0. The app is for local research and simulation only: it has no live broker connection and sends no real-money orders. Historical performance cannot guarantee future returns.

## Open the app and check the data

When the services are already running, open the [workbench](http://localhost:5173/) in a browser on this PC. Check “Service online” separately from the data mode and date. An online service does **not** mean prices are current or that their source has passed audit. Use the [data center](http://localhost:5173/data) to inspect available data, dates and provenance. Language and theme are in [Settings](http://localhost:5173/settings); changing language does not change trading dates or calculations.

Project containers are configured to recover with the Docker Desktop engine. Desktop was not observed to auto-start after either the 2026-09-24 or 2026-09-25 Windows sign-in. A maintainer replaced the old login entry with one current-user scheduled login task, but a subsequent real sign-in has not tested it. Direct post-login opening is therefore **not** guaranteed. If the page is unavailable, open the already-installed Docker Desktop from the Windows Start menu and wait until its engine is running, then refresh the original page. If it still fails, ask the maintainer to check the project services. Do not reinstall Docker, remove volumes or reacquire the archive. Reopen the same task link after recovery and verify saved tasks and results. This is a terminal-free manual recovery step, not proof that sign-in autostart works.

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
5. Select 2–3 completed studies to compare, checking data version, date range, capital, costs, risk and strategy version first. A saved simulated rebalance preview, where present, must be read with its as-of date, data snapshot and risk rejections; older results may have no preview. The result page can download a metadata JSON report and CSV records; both completed in actual Chrome on this PC. If the report is prepared but your browser does not start the download, use “Save prepared report” and check browser downloads. If preparation fails, check service status before clicking the download button again; a click alone does not prove the file was saved.

## Simulated accounts and recovery

In [Simulated accounts](http://localhost:5173/paper), the creation form defaults to a clearly labeled 2030 synthetic A-share demo; the legacy AAPL fixture remains an explicit non-A-share choice. You can also choose audited historical replay. Start the account explicitly; the page supports pause, resume and stop, with cash, holdings, orders, fills and logs. None are real trades. New-market forward mode is not yet usable; a historical catch-up is not a new-market receipt.

On a completed A-share historical research result, “Review these settings in a separate historical paper account” opens a new-account form with capital, strategy, universe, cost and risk settings copied for review. It does not copy the study's returns or rebalance preview, create or start an account, or submit an order. Each historical replay is limited to 93 calendar days; a longer study leaves the new start date blank for you to choose explicitly. The new account has its own data snapshot, plan and ledger. Create and start it only after reviewing the settings.

For a cancelled or interrupted research task, open its detail page and read the explanation. “Start or reopen linked retry” uses the saved configuration without overwriting the original record; repeated requests reopen the linked attempt. An account interrupted by a service failure may remain “Interrupted” instead of automatically continuing. Read its recovery guidance before starting a new session; do not assume fills occurred while disconnected. For offline, timeout or missing-data errors, try the page's retry or return action. If it persists, give the task link and displayed technical reason to the maintainer; never clear PostgreSQL, Redis or Docker volumes as a troubleshooting shortcut.

This development database had a recovery incident: two paper sessions created after the usable backup (short IDs `4b64380f` and `07d72259`) could not be recovered. Do not treat them as queryable durable records. A backup on the same physical disk is not independent disaster recovery. Until this gap is resolved, do not rely on this build as a long-term account ledger.

## Release and rollback

This development build is unreleased. The published stable baseline is v1.1.0; formal research reports and frozen data remain read-only. A maintainer may roll application code back through the repository's release process, but must not overwrite the old tag, rerun Official OOS or delete database volumes. Current gaps include lawful forward-market authority, full accessibility/performance acceptance and reboot-tested terminal-free startup. This is not a v1.2.0 final delivery.
