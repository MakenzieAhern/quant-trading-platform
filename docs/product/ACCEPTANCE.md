# v1.2 acceptance ledger

## 2026-09-26 03:38 UTC nested comparison/detail return and incomplete comparison

Actual Chrome found the still-open nested defect: list selection 2 -> compare
-> detail -> visible Back to list produced selection 0. A new navigation
regression failed before repair. Replace the one-hop origin with the existing
history entry's bounded managed ancestor metadata (URL and index only). Return
to the nearest exact requested URL via native history traversal, retaining its
list context and Forward entries. Validate consecutive safe indices and the
current URL marker; direct, malformed or unknown/native-hash history navigates
internally. Retain only 32 managed ancestors; beyond that bounded context the
safe internal fallback applies. No router/cache dependency or financial change.

Focused navigation/comparison 29 PASS; full frontend 260 PASS, lint, TypeScript,
production build, changed-file Prettier and diff check PASS. Regressions include
three nested routes, nearest newer list, unknown hash, malformed metadata and
cancel/accept of the existing dirty-draft guard on a multi-entry return.
Chrome ZH/dark: M1 search + completed/historical/name-ascending filters, two
existing completed studies -> comparison -> original detail -> reload -> Back
retained both selections and filter chips. Native Forward still reached compare
then detail; switching EN before returning retained the same selection/dates.

A separate direct comparison of one real completed study and the existing real
INTERRUPTED study showed the explicit incomplete alert in EN/ZH, named both
studies without omission and exposed retry/loading and detail/return controls;
it did not fabricate a partial metric table. The internal Back link worked.
No retry command, study/account/order/provider creation, main service restart,
DB write or frozen-research mutation occurred. Temporary tab closed; main tab
restored to default view, selection 0 and Chinese/dark Workbench. Main services
remain running, PG/Redis/backend healthy, Redis PONG/API 200; formal 1/3/310,
jobs 8, paper 5/events 417 and updates 4/receipts 6 unchanged.

Bounded evidence is outside Git at product-evidence/v1.2/m4/
20260926-nested-study-return.json. Scroll restoration, missing/stale result
browser branches, native zoom, novice review, lawful forward data and genuine
missing-ledger/independent-backup gates remain separate. Full views/U4/U5/U7/
M4/M5 acceptance is not claimed.

## 2026-09-26 03:28 UTC saved study view and comparison return context

Actual Chrome reproduced two list-context defects: selecting two completed
studies, opening a detail and using browser Back reset selection to zero;
after that fix, the visible comparison Back link still created a fresh list
entry and lost selection. Reuse the existing list history state for at most
three validated selections; do not put IDs into the durable saved-view setting.
The existing Link/navigation helper now optionally traverses back only when
the current entry records that its immediate origin is the requested list;
direct details use the internal list fallback. Modifier-click behavior and
existing unsaved-draft traversal guard remain unchanged.

The failing component regression now passes. Focused navigation/comparison/
experiments 53 PASS; full frontend 253 PASS, ESLint, TypeScript and production
build PASS. Changed shared/test files pass Prettier; the original compact
ExperimentsPage style is retained instead of unrelated whole-file reformatting.
In Chrome, completed/historical/name-ascending filters and hidden creation
column survived save/reload; two selected real historical studies survived
detail/comparison visible Back links, browser Back/Forward and reload. EN/light
390x844 comparison retained dated results and no page overflow; remove-one
disabled comparison. A direct detail in a fresh tab safely returned internally
with zero selection. Default filters, empty selection, ZH/dark and original
viewport/Workbench were restored; the temporary direct-detail tab was closed.

This covers the direct list->detail/compare->list path, not every nested
comparison->detail return, missing/stale study branch, native zoom or novice
workflow. No study, account, order, provider request or database write occurred.
Four services remain running, Redis PONG/API 200, formal counts 1/3/310,
jobs 8, paper 5/events 417, updates 4/receipts 6 and frozen .research unchanged.
Evidence is outside Git at product-evidence/v1.2/m4/
20260926-study-return-context.json. Full U5/views/U7/M4/M5 remain incomplete;
unknown backup/pre-loss/forward-rights answers are not approval.

## 2026-09-26 03:10 UTC checkpoint write safety and isolated real crash

Two new regressions (Bar replay and synthetic A-share sessions) failed before
the fix: if a paused account's persisted market checkpoint disappeared from
the input, subsequent non-status events were appended before terminal failure.
The existing shared persistence callback now refuses writes until replay has
exactly matched the saved checkpoint. Failure, cancellation and concurrent-stop
cleanup of an unmatched runtime cancel only pending orders from the persisted
history, not orders invented by the unverified replay. No lifecycle permission,
automatic recovery, financial policy, schema, worker or dependency was added.
Both regressions pass with the non-status journal unchanged and terminal restart
HTTP 409. Fresh isolated `quant_test` tmpfs full backend: 989 PASS, one optional
unmounted historical-archive skip; Ruff, format and mypy PASS.

A real Uvicorn process in an owned, isolated API container was frozen to capture
an exact committed two-account prefix, then SIGKILLed and restarted against its
unchanged scratch PostgreSQL. The paused synthetic account `192d42bc` stayed
PAUSED; active `cc001164` became INTERRUPTED, no automatic processing occurred,
explicit start returned HTTP 409, and the saved non-status journal was identical.
Startup logged exactly one orphan interruption. This is genuine process-crash
evidence on a synthetic fixture, **not** new-market forward, full historical
recovery, host/database-loss recovery or reconstruction of the missing accounts.
The first harness attempt stopped before the crash due to PowerShell REST-array
enumeration; that harness issue was corrected, and only its scratch account was
stopped before the successful attempt. Do not count it as a product failure.

Evidence and the bounded check script are outside Git at
`product-evidence/v1.2/m4/20260926-paper-recovery.json` and
`20260926-paper-crash-check.ps1`. Owned scratch API/Redis and tmpfs PostgreSQL
containers/network were removed; no image, named volume or application data
was removed. Main services were not restarted or hot-reloaded for this patch;
all four remain running, Redis PONG/API HTTP 200, with read-only formal counts
`1/3/310`, jobs `8`, paper `5/417`, updates `4/6` and `.research` unchanged.
Full U7/M4/M5, genuine lost-ledger recovery, independent backup and lawful
forward-source gates remain open; the three unknown user answers grant nothing.

## 2026-09-26 02:57 UTC command-search focus and explicit motion-off

Actual Chrome 153 at 390x844 EN/dark/motion-off reproduced a command-panel
keyboard defect: Ctrl+K focused its Close button, so direct typing `Help`
left the search input empty. A new regression failed before the fix.
The command component now focuses its existing input after the shared Dialog
opens; the Dialog's trigger capture/cleanup and other dialog types are unchanged.
The regression also covers StrictMode and restoration to the original trigger.
Focused search 7/7, full frontend 245/245, ESLint, TypeScript/build and changed-file
Prettier passed. In actual Chrome, both the shortcut and visible button focused
search; EN `Help`/ZH `帮助` entered directly, first Escape closed with text and
returned to the search-button trigger, and Tab/Enter on the Help command reached
`/help` with main-content focus. No input was programmatically filled for this
focus verification.

The explicit motion-off setting survived reload. Nine primary routes' initial
mounted content and ::before/::after styles had no non-none animation, nonzero
transition duration or smooth scrolling. This samples content after a visible h1,
not every asynchronously loaded row/error/result branch. At 390x844 the mobile
navigation had a 0s transition, modal semantics, inert background and a real
Shift+Tab/Tab focus wrap; Escape released isolation and returned to Open navigation.
The command panel also stayed animation-free and fully keyboard-operable.
The OS `prefers-reduced-motion` branch was inspected in CSS, **not** tested with
a changed actual system setting. Full AA/AT/visual/motion acceptance is not claimed.

Bounded evidence is outside Git at
`product-evidence/v1.2/m4/20260926-motion-command-focus.json`.
Original system-motion, Chinese/dark preferences and default viewport were
restored, with Workbench left open. Four Compose services remained running,
API HTTP 200; read-only counts remained formal `1/3/310`, personal jobs `8`,
paper sessions/events `5/417` and update jobs/receipts `4/6`. No container
restart, provider acquisition, study, account/order submission or database write
was requested; `.research` remains unchanged. U7/M4 integrity/M5 remain open.

## 2026-09-26 02:46 UTC native Chrome chart interaction timing

The earlier tool-inclusive click times did not isolate application latency.
A temporary local `PerformanceObserver` on the production build now measured
native Event Timing in actual Chrome 153 on DESKTOP-3EOROGR (Ryzen 7 9800X3D),
1440x900, Chinese/dark, warm saved 293-session result `d9f27183`, with a
100-point chart page and 138 rendered table rows. All 30 trusted benchmark
toggle clicks had a matched nonzero `interactionId`; related entries were
grouped by maximum duration rather than counted as separate gestures.
Each click changed both checkbox and benchmark SVG, and the final state was
checked. Native p50/p95/max were **16/16/16 ms**, with 8 ms quantization and
a 16 ms reporting threshold; no missing/censored interaction was substituted
with zero. Click processing was 9.1-12 ms; this is a bounded warm-case PASS
against the 200 ms target, not whole-site INP or full `QA-PERF` acceptance.
The [W3C Event Timing draft](https://www.w3.org/TR/event-timing/) documents
the grouping, threshold and native input-to-presentation semantics.

Per-interaction evidence is outside Git at
`product-evidence/v1.2/m4/20260926-chrome-native-chart-timing.json`, SHA-256
`b40ec23d93d03c0a5785e32e0e408ccff2b588d578e7bf33928e288315d29bdd`.
Temporary measurement code was removed, the original production build rebuilt,
and no frontend source diff remains. Chrome reload verified the diagnostic
output absent, restored the original viewport and Chinese/dark Workbench.
Frontend 244/244, ESLint, TypeScript and build passed.

**Operational deviation:** the preview used only the frontend port, but
`docker compose up -d frontend` during restoration unexpectedly recreated
PostgreSQL, Redis and backend dependencies. Their named data volumes were
retained, all services recovered, Redis PONG/API and frontend HTTP 200, and
Alembic remained at `20260924_0016`. Read-only counts stayed formal `1/3/310`,
personal jobs `8`, paper sessions/events `5/417`, updates/receipts `4/6`.
Do not describe those dependencies as continuously running throughout the
restore. Future frontend-only restoration must use `docker compose start
frontend` for the existing stopped container, or explicit `--no-deps` if an
update is needed. No volume cleanup, data restore, study or provider request
was performed. `.research` remains unchanged. This incident/check does not
establish mid-run recovery, lost-ledger repair or full persistence acceptance.

The user's three unknown answers do not establish an independent backup
destination, genuine pre-loss ledger evidence or lawful new-market data rights.
Those gates remain open; U7/M4/M5 and product completion remain incomplete.

## 2026-09-26 02:35 UTC tab-return status refresh

A failing App regression reproduced stale topbar service/data status when a
document became visible without a window-focus event. The shared shell now
listens to `visibilitychange` through its existing return/focus handler, skips
hidden documents, reserves the existing ten-second throttle before updating,
and removes both listeners on unmount. It introduces no timer, provider request,
worker or financial behavior. The regression checks service failure after return,
data-capability refresh, hidden/duplicate-event suppression and cleanup.
Focused App 11/11, full frontend 244/244, ESLint, TypeScript, production build,
Prettier and diff checks passed.

Actual Chrome on the retained Chinese/dark Workbench showed the new code and
a normal manual status refresh advanced its UTC check time to 02:34:59. The
attempted real-tab background/return test is **NOT VERIFIED**: the temporary
blank tab and one Ctrl+Tab action did not change the product document's observed
visibility from `visible`. The temporary tab was closed; no alternate native
automation or forged DOM visibility event was used. The unit test isolates this
event path; the browser result proves only ordinary refresh compatibility,
not a genuine visibility transition. Wider M4/U8 acceptance remains incomplete.
Read-only application counts remained formal `1/3/310`, personal jobs `8`, paper
sessions/events `5/417` and market receipts `6`; no study, account, order or
source-acquisition request was submitted.

## 2026-09-26 02:26 UTC shared test-mode database protection

The suite-level pytest guard did not protect independent test-mode scripts or
Alembic: their shared Settings previously accepted `APP_ENV=test` with an
application database URL. Settings now rejects every target outside the existing
`quant_test` / `quant_test_*` namespace before engine creation, and pytest reuses
the same URL/name check. Configuration error strings hide input values, including
database credentials. Development/production behavior is unchanged.

Focused configuration/guard tests passed 15/15, including unsafe names, malformed
URLs, permitted test targets and credential-redaction. The full backend suite
on fresh `quant-v12-settings-guard-20260926` tmpfs PostgreSQL passed 985 tests
with one optional unmounted-archive skip before the final malformed-URL and
production-mode cases were added; Ruff, format and mypy passed. Frontend 243/243, ESLint and TypeScript
passed. A standalone `APP_ENV=test` Alembic `current` probe against a deliberately
unreachable application-named target failed at Settings before any engine or
database connection, with no URL/password in the error string. The scratch
container/network were removed without volumes or main-service changes.

Read-only live counts remained formal datasets/runs/trades `1/3/310`, personal
jobs `8`, paper sessions/events `5/417`, update jobs/receipts `4/6`; API health
returned HTTP 200 and `.research` had no diff. This closes an additional
test-entry-point protection gap, **not** recovery of the two lost genuine
paper ledgers, independent disaster backup, forward-source authority or U7/M5.
No formal study, source acquisition, schema migration or release was run on
application history.

## 2026-09-25 18:10 UTC Chrome production-chart timing method rejected

On DESKTOP-3EOROGR, the current production frontend build was served in actual
Chrome 153 on the project-owned `localhost:5173` origin against the saved
293-session historical result `d9f27183`. Only the project's frontend was
briefly stopped; a named temporary preview container served the build. The
first two benchmark-toggle clicks took 278/269 ms at the browser-control API,
then the next 18 took about 2.75–2.99 seconds each. Every click changed both
the checkbox and benchmark SVG line, and 20 toggles returned the control to
checked. A separate full-precision checkbox took 274 ms on its first click
and 2749 ms on its second. The same jump in a non-chart control leaves
browser-control delay and page-wide work unseparated: these tool-inclusive
times cannot establish chart render latency or the <=200 ms interaction
target. No performance PASS or product regression is inferred;
use a supported in-browser event/paint trace rather than repeating this method.

The temporary preview tab/container were closed. The original Compose frontend
was restored (Compose recreated only that frontend container); PostgreSQL,
Redis and backend remained running. Frontend and `/api/health` returned HTTP
200, Redis PONG, and read-only live counts remained research jobs 8, paper
sessions 5, paper events 417 and market-update jobs 4. No study, order,
provider acquisition, database restore, formal report or frozen data was
changed. `QA-PERF` and the release gate remain IN_PROGRESS/FAIL respectively.

## 2026-09-25 17:53 UTC same-route Back repair

Actual Chrome opened the saved historical study `d9f27183` and followed its
paper-account handoff without creating an account. The form retained the
historical provider, CNY 100000, dataset and 2011-03-22 end date; because the
study spans more than the 93-calendar-day replay limit, the start date stayed
required and empty. EN switching preserved these values and the explicit
replay-only warning. No account was submitted.

While returning to the research list, clicking its already-active sidebar
link and pressing Back once left Chrome on the same list: the shared `navigate`
helper added a redundant browser-history entry for an **identical** URL.
After checking its callers and hash-detail navigation, the helper now returns
without pushing only when the complete destination URL already equals the
current URL. A regression checks both no duplicate entry and a distinct hash
entry. Focused navigation 8/8, full frontend 243/243, ESLint, TypeScript/Vite
build, Prettier and diff check passed. Fresh real Chrome verified Workbench →
Research → Research again → one Back returns to Workbench. Chinese/dark and
the original Workbench tab were restored; live product jobs/paper sessions/
paper events/market receipts stayed `8/5/417/6`. This repairs Back behavior,
not the remaining U7 forward, M4 data-integrity or M5 release gates.
[PR #32 CI 36170000918](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36170000918)
at head `067bf01` passed backend, frontend and Compose; the PR remains draft.

## 2026-09-25 17:39 UTC bounded English Chrome read-only walkthrough

The existing Chrome profile was reopened after its previous window disappeared.
At the live local frontend, English Data Center and strategy detail from the
earlier attempt were continued into saved historical study `d9f27183`:
complete-run return `+4.67%`, drawdown `-2.48%`, costs `CNY 96.05`, CSI 300
benchmark `-8.83%`, historical-only 2011-03-22 rebalance preview, and
plain-language non-fill reasons were visible. Comparing that run to synthetic
demo `dccc74b3` showed a prominent uncontrolled-comparison warning, distinct
historical/synthetic data provenance, and different periods/capital; the page
did not rank or recommend a strategy. The stopped historical paper account
`d7044a3c` showed its 2011-03-23 session, CNY cash/equity, retained positions,
and an explicit notice that its older account-native plan is unavailable.
Chrome showed the safety boundary: simulated execution only, no broker or
real-money orders, and no new-market forward simulation. Chinese/dark and the
Workbench route were restored. This was agent-operated read-only QA: no new
study, paper session, provider request or order was requested, and no
English recording, novice-user study, native 200% zoom or full M4/M5 PASS.
[PR #32 CI 36168702768](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36168702768)
at head `4396a53` passed backend, frontend and Compose. A bounded check for a
local recorder found no installed Snipping Tool; pre-existing Clipchamp opened
only to a Microsoft sign-in failure screen. It was closed without login,
screen permission, upload or recording. No **new English** video is claimed;
the earlier Chinese demo and walkthrough recordings remain valid bounded
evidence, not full delivery acceptance.

## 2026-09-25 17:29 UTC Docker login-recovery and startup replacement

Windows last booted at 2026-09-25 12:04:54 AEST and this user logged in at
12:05:07, after the Docker Run path had been quoted. Docker Desktop 4.92.0 was
not running when checked at 2026-09-26 03:24 AEST; `docker-desktop` WSL was
stopped and Ubuntu had no Docker CLI integration. The user setting still said
`AutoStart=true`, StartupApproved began `02`, and the quoted per-user Run value
was present. Host logs had no post-login Docker launch before the agent's
manual start, and the bounded Application crash-log check found no Docker
event. The exact reason Windows skipped the Run entry remains unknown.

Starting only the already-installed Desktop recovered WSL Engine 29.8.0,
Compose 5.5.1, four original project volumes and four project services.
PostgreSQL, Redis and backend became healthy; `/api/health` and the frontend
returned HTTP 200. Read-only database counts remained formal datasets/runs/
trades `1/3/310`, personal research jobs `8`, paper sessions/events `5/417`,
market receipts `6`. No reset, prune, reinstall, data deletion or study ran.

Because the previous startup hypothesis failed, one limited-privilege
current-user `AtLogOn` scheduled task now replaces the Docker-only HKCU Run
entry, which was removed after verifying the task and recording its rollback
value. The task has **not** passed a real next-login test. M5 terminal-free
startup and release remain FAIL. Chrome was closed during the attempted
English read-only walkthrough; Data Center and strategy detail were observed,
but the historical result had reached only Loading when the browser binding
disappeared. No English video or completed result walkthrough is claimed.
[PR #32 CI 36167737133](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36167737133)
at head `8ec405d` passed backend, frontend and Compose. That CI did not run a
Windows login or restore the missing paper ledgers.

## 2026-09-25 01:57 UTC optional orientation under denied storage

The Workbench's optional mode guide wrote a `guide-seen` browser-storage key
that no code read. Denied storage could therefore throw while the user pressed
**Got it, continue exploring**. The dead write was removed; the guide still
closes and remains reopenable. A regression simulates a storage `SecurityError`;
the focused 3/3 and full frontend 242/242 tests, ESLint, TypeScript/production
build and diff check passed. No account, provider, database or frozen research
data was changed. PR #32 head `abdc56b` [CI 36084273692](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36084273692)
passed backend, frontend and Compose; the local worktree was clean and the
running API/frontend returned HTTP 200. This closes one U1 error-path defect,
not M4/U7/M5 or native 200% zoom. The user still cannot confirm an independent backup destination,
genuine pre-loss paper ledgers or lawful 2026 forward-data rights.

## 2026-09-25 01:50 UTC result chart date/locale and review checkpoint

Actual Chrome reopened saved 293-session historical job `d9f27183` without a
new run. Filtering displayed records to 2011-03-01–2011-03-22 changed the
chart selection from 2010-06-01 to the in-range 2011-03-22 and showed 16/16
equity rows. Full-run return/drawdown/cost/benchmark remained +4.67%/-2.48%/
CNY96.05/-8.83%. Switching Chinese to English kept both date inputs, the
selected trading date and exact chart readout; full interval and Chinese/dark
were restored. No study/account/provider/database write occurred. An
independent read-only review of the current result/plan/chart code and tests
found no reproducible new U4/U6/U8 defect; it was not an assistive-technology
or novice-user acceptance test.

Chrome browser control explicitly blocked `chrome://settings/appearance` by
security policy. No alternate route or bypass was attempted. Therefore a
native 200% browser-zoom check remains **NOT RUN** by the agent and requires a
user-operated browser session or an approved testing interface; the earlier
720px CSS-viewport proxy is not equivalent. `UX-CHART`, `QA-VISUAL`, `QA-A11Y`
and M4 remain IN_PROGRESS.

## 2026-09-25 01:34 UTC five-route responsive and language spot check

Actual Chrome inspected `/data`, `/tasks`, `/experiments`, `/paper` and `/help`
without submitting any request or changing a saved record. At 390×844,
Chinese/dark and English/light each had document width equal to scroll width
(`375/375`) on all five routes. At 1024×768 English/light the five pages were
`1009/1009`; at 1280×800 and 1440×900 Chinese/dark they were respectively
`1265/1265` and `1425/1425`. The help page was visually inspected at English
light desktop and mobile sizes. On the research list, the 18px native
comparison and column checkboxes were inside 40px or taller labels; its wider
table remained in a local scroll region rather than widening the page.
The data-request acknowledgment's 18px input had a 307×64px label target.
On a fresh mobile research-list load, first Tab focused the skip link and
Enter moved focus to `main#main-content`.
The same 390×844 two-locale/two-theme spot check covered `/`, `/strategies`,
`/markets`, `/research/a-share` and `/settings` after their headings appeared;
all five also measured `375/375`. The fully loaded formal archive retained
two locally scrollable tables (1237px and 777px inside 337px containers).
The English/light settings page was visually inspected at mobile size.
Language/theme were returned to Chinese/dark and the temporary viewport
override was reset. This is a bounded layout and target check, not native
200% zoom, a complete contrast/keyboard/screen-reader audit, or novice-user
acceptance. `QA-VISUAL`, `QA-A11Y`, M4 and M5 remain incomplete.

## 2026-09-25 01:25 UTC release-image CI regression gate

PR #32 head `f5d4f8d` [CI 36081787335](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36081787335)
passed backend, frontend and Compose. The Compose job's new release-backend
smoke step passed on GitHub's isolated runner: it built the backend image,
migrated a tmpfs PostgreSQL database, started production-mode Uvicorn with
scratch Redis on a private Docker network, and checked `/api/health` plus the
clean-install capability boundary (synthetic demo available; unmounted
historical archive unavailable). It uses no application data mount or named
database volume and cleans up its scratch containers/network. The prior
agent-operated Chrome end-to-end rehearsal remains separate evidence; CI does
not run a browser or establish data durability, lawful forward authority or
v1.2 release readiness. `QA-RELEASE` and `M5-DELIVERY` remain FAIL.

## 2026-09-25 01:15 UTC isolated release-image end-to-end rehearsal

At product head `955c23a`, the backend release image and Nginx frontend image
were built from the current worktree; the frontend API base was compiled for
the isolated loopback port `18000`. Four explicitly named scratch containers
used their own Docker network and ports `18000`/`15173`, with PostgreSQL and
Redis on tmpfs and **no mounts or volumes** from the main application. The
backend ran `APP_ENV=production`, `BROKER_MODE=paper` and its plain image CMD,
not the development startup command. On the scratch database, Alembic
`upgrade head`, `downgrade 20260904_0001`, `upgrade head`, and `check` passed.
Redis returned PONG; backend `/api/health` and Nginx `/` and `/help` returned
HTTP 200 with the expected static security headers.

Actual Chrome 153 opened the release frontend, saw the separate backend as
online, and completed all four guided steps using the explicitly labeled
synthetic demo because no private historical archive was mounted. The
isolated API accepted one POST and the saved job
`b3b0a2cc-7e8a-4ca2-89d8-87004c0aee3f` completed; its result remained
available after page reload and after restarting only the scratch backend.
The page warned that +0.39% synthetic return was not market evidence and
withheld an executable next-day plan. Scratch PostgreSQL held one personal
job; the main database still read formal 1/3/310, personal jobs 8, paper
sessions 5/events 417. Main Compose and frozen research were untouched.
The four named scratch containers were stopped and auto-removed, and their
now-empty scratch network was removed; no application volume or image was
deleted. Main Compose remained four services up, with the same database
counts after cleanup.

This is a bounded clean-database release-image/API/browser and process-restart
rehearsal, **not** the actual release Compose switchover, independent backup,
restoration of two missing genuine ledgers, lawful 2026 forward-mode evidence,
native-login startup, novice-user review or v1.2 acceptance. M4 data integrity,
U7 forward mode, QA-RELEASE and M5 delivery remain blocked/incomplete.

## 2026-09-25 01:06 UTC historical paper monetary units

Actual Chrome 153 showed the stopped, audited A-share paper account with
unqualified portfolio balances and position/fill prices. The existing detail
page now marks historical A-share cash, equity, market value, PnL, commissions
and position/fill prices as 人民币/CNY in Chinese/English, without changing exact
values, exports or backend accounting. Synthetic/legacy accounts do not gain an
unverified CNY claim. Chrome reloaded the retained historical account and
confirmed both locales' labels, then restored the original Chinese/dark
preference. Focused paper tests 26/26, full frontend 241/241, ESLint and
TypeScript/production build passed; changed files were formatted. No account,
order, provider, database or frozen research write occurred. This is a bounded
U8/QA-A11Y clarity fix, not full U8 or release acceptance. Two lost genuine
paper ledgers, independent disaster-recovery destination, lawful 2026 feed
rights and Docker post-login startup remain unverified.

## 2026-09-25 00:48 UTC guided Save & exit browser closure

The explicit wizard **Save & exit** route no longer uses the browser-native
confirmation that repeatedly left its outcome unobservable. It reuses the
existing accessible product dialog; the dirty sidebar/Back navigation guard
is unchanged. Actual Chrome 153 opened the restored historical step-2 draft,
cancelled the Chinese dialog without leaving, then confirmed and reached the
workbench. **Continue last draft** restored the same name, 2011-01-04 through
2011-06-30 dates and exact CNY `123456.789000000000001`. In English, the
dialog text translated without resetting the draft; Escape returned focus to
the trigger and left the wizard intact. Chinese/dark was restored. The dialog
was visually inspected in Chrome. Focused wizard 31/31 and full frontend
241/241 tests, ESLint and TypeScript/production build passed; changed-file
Prettier was applied and rechecked. PR #32 code head `e84a5b3`
[CI 36079549453](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36079549453)
passed backend, frontend and Compose. No research task, account or order was
submitted and no live database or frozen research file was changed. An
independent read-only review found no release-critical defect in this change.

Together with the already recorded four-step, historical/synthetic submission,
draft/locale and guarded navigation evidence, this closes the agent-operated
`U3-WIZARD` interaction row. It is not an independent novice-user study and
does not close `U3-ISOLATE`, M4 data integrity, U7 forward mode or M5 delivery.

## 2026-09-25 00:40 UTC market watchlist action names

Actual Chrome showed twenty identical **Save to watchlist** accessibility
names in the market results and generic **Inspect history**/**Remove from
watchlist** names for saved securities. The existing buttons now identify the
security; saved-row actions also identify the dataset, so the same security
in historical and synthetic sources has distinct names. Visible labels and
watchlist behavior are unchanged. A regression test checks both sources and
English/Chinese names. Actual Chrome's EN/ZH accessibility trees confirmed
the names and the original Chinese/dark preference was restored. Focused
13/13 and full frontend 240/240 tests, ESLint, TypeScript/production build,
changed-file Prettier and `git diff --check` passed. No live watchlist,
account, provider or research write was made. An independent read-only PR32
review found no additional release-critical defect beyond recorded acceptance
gaps. This closes only the repeated-action-name defect; `QA-A11Y` remains
**IN_PROGRESS** and M4/M5 remain blocked by the unverified genuine pre-loss
ledgers, independent backup and lawful forward-data rights. The user does
not know whether any of those three external prerequisites exists; none is
treated as approved.

## 2026-09-25 00:30 UTC raw-task history accessibility

Actual Chrome opened the existing failed raw-candidate task from the task
center without retrying it. The Data Center history's four **Open task**
buttons exposed only UUIDs to assistive technology, unlike the contextual
task-center links. Each button now names the securities, requested date range
and UTC creation time in the selected language; the visible label, target and
audit ID are unchanged. Actual Chrome's Chinese and English accessibility
trees distinguished all four buttons, including the failed and successful
requests for the same securities and dates. Chinese/dark was restored. The
focused 13/13 and full frontend 239/239 tests, ESLint, TypeScript/production
build and changed-file Prettier passed. No provider request, retry, account or
research task was started. This is bounded QA-A11Y progress, not full WCAG or
U5 source-authority acceptance.

A second fresh Chrome tab also reopened the saved step-2 wizard draft, but
the explicit Save & exit native confirmation again left the browser controller
timed out with the tab still on `/research/new`. No second click or research
submission was made; U3-WIZARD remains **IN_PROGRESS**.

## 2026-09-25 00:20 UTC explicit save-and-exit browser gate corrected

A fresh actual-Chrome tab reopened the existing local step-2 draft with its
exact name, capital and dates. Clicking **Save & exit** raised the expected
native confirmation. The browser controller identified a `confirm` dialog,
but its accept operation then timed out; the dialog disappeared while the
browser's authoritative tab listing still showed `/research/new`. Later
state/screenshot attempts also timed out. The action was not retried, no
research task was submitted, and no navigation or restored-draft outcome is
claimed. The existing focused unit test proves the component's intended
confirm-and-navigate path, while the separate actual-Chrome Back guard passed;
neither proves this explicit browser path. U3-WIZARD is therefore
**IN_PROGRESS**, pending a different reliable real-browser confirmation path.

## 2026-09-25 00:13 UTC mobile ledger/result and dependency audit

Actual Chrome 153 at 390×844 opened the retained stopped historical A-share
paper account `d7044a3c` and the saved 293-session A-share study `d9f27183`.
Both had document width 375px against client width 375px: no page-level
horizontal overflow. The paper page's five wide tables each had a named,
focusable local scroll region; keyboard Right moved the first table. Visible
paper controls were at least 24px in both dimensions. The result page's
three wide tables were locally scrollable and focusable; its two 18px native
checkboxes were inside 40px-high clickable labels. The browser viewport was
reset afterward. This is a two-route mobile/keyboard sample, not full
QA-VISUAL or WCAG 2.2 AA acceptance; no session or research action was sent.

At PR #32 head `0e0bc30`, [CI 36075909646](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36075909646)
passed backend, frontend and Compose. `npm audit --audit-level=moderate`
reported zero known vulnerabilities in the locked frontend dependency tree,
including development dependencies. `pip-audit 2.10.1 -r requirements.lock`
reported no known vulnerabilities for the locked backend tree from a one-off
test-only container; no audit package was added to the live backend or repo.
The main stack was not rebuilt or restarted. These checks do not resolve the
missing genuine paper ledgers, independent backup, lawful forward-feed rights,
or the remaining product/release acceptance matrix.

## 2026-09-25 00:04 UTC paper startup ownership fence

An independent read-only review found a conditional overlap hazard: a second
backend could mark a live paper account `INTERRUPTED` before failing to acquire
the existing experiment-worker singleton lock. The original worker could then
append events after that terminal status. Startup now acquires ownership and
starts local managers before reconciling orphaned paper accounts; shutdown
stops paper tasks before releasing ownership. Repository event appends reject
terminal paper sessions under the same row lock. This was a code-inspection
finding, not an observed live-account incident.

The focused isolated `quant_test` suite passed 34 tests with one optional
historical-archive skip; the complete backend suite passed 979 with that same
skip. Ruff, formatting and mypy passed. No main Compose service was restarted,
no formal study/OOS was rerun, and no live database or frozen dataset was
written. The repair does not restore missing paper ledgers, establish an
independent backup, license a forward data feed, or complete M4/M5 acceptance.

## 2026-09-24 23:51 UTC backup-location follow-up and PR CI

The user could not identify an independent backup destination, pre-loss ledger
backup or lawful 2026 A-share data-use authorization; all remain unknown. A
read-only host check found only C: and D: fixed logical drives (previously
verified as partitions of the same NVMe), no currently attached removable or
network drive, and only `desktop.ini` in the local OneDrive sync root. The
empty local sync root does **not** prove that no cloud backup exists. The five
known WSL PostgreSQL dumps remain the earlier `pre0014`, `pre0015`, after-loss,
post-recovery and `pre0016` files; the first two predate paper accounts
`4b64380f` and `07d72259`, and the later three cannot recover their original
rows. No candidate source, database, volume or backup setting was changed.

Non-elevated `Get-ComputerRestorePoint` returned Access Denied and
`Win32_ShadowCopy` returned initialization failure, consistent with the
earlier privileged `vssadmin`/`wbadmin` gate. Shadow copies and Windows Backup
versions remain **unassessed**, not absent. The 2026-09-24 22:29 AEST Windows
boot time is unchanged after the Docker Run-path correction, so post-login
autostart still has not been retested. PR #32 head `06d1b01` passed
[CI36074387311](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36074387311)
backend, frontend and Compose. M4-DATA-INTEGRITY, U7-FORWARD and M5-DELIVERY
remain unaccepted.

The release-rehearsal command and the clean-install bootstrap command in
`docs/DEPLOYMENT.md` previously appeared before their current-workbench backup
warnings. Both warnings now precede the respective commands. No Compose,
migration, service or database command was executed by this documentation fix.

## 2026-09-24 23:45 UTC task-center link purpose (QA-A11Y)

Actual Chrome `/tasks` exposed eight identical "Open experiment" and four
identical "Open task" link names, so a links-only screen-reader view could not
identify the target. The existing list rows now give each link a localized
accessible name with its study name or security/date window and UTC creation
time; visible text and destinations are unchanged. Chrome EN and ZH accessibility
trees distinguish all 12 links, including repeated study names and repeated
security/date windows. Chinese/dark preferences were restored. Focused 3/3 and
full frontend 238/238, ESLint, TypeScript/production build, and changed-file
Prettier passed. No research, provider or paper request was sent. This closes
one QA-A11Y defect, not the full WCAG/screen-reader/release gate. A temporary
Chrome viewport override did not change the measured CSS viewport in this
session, so no new mobile-size claim is made.

## 2026-09-24 23:35 UTC forward-data rights disclosure and backup inventory

Actual Chrome on `/data` showed that the raw-candidate notice already blocks
execution, but the expanded BaoStock terms said "private local analysis trial"
without explicitly separating that trial from unverified exchange-data rights
for this app. The shared EN/ZH terms and request acknowledgment now say the
rights remain unverified, including forward simulation; SDK access and a
software license do not grant data rights. Chrome exposed both corrected
language variants in the terms disclosure and checkbox name, then restored
Chinese/dark. No request was submitted, receipt changed or authority promoted.
The focused update suite passed 12/12; ESLint, TypeScript and production build
passed. This reduces a U5/U8 permission ambiguity; U7-FORWARD remains NOT_RUN.

Read-only Windows inventory found only stopped File History, block-backup and
cloud-restore services, ready built-in backup tasks, and a running OneDrive
process. None proves that WSL/Docker/PostgreSQL data were backed up to an
independent destination. `wbadmin get versions` required elevation, as the
earlier VSS query did; neither shadow copies nor Windows Backup versions were
assessed. No files, volumes, settings or data were changed. M4 independent
backup and the two genuine missing ledgers remain open.

## 2026-09-24 23:24 UTC release backend migration safety

Read-only review of the merged release Compose configuration found that the
backend still inherited development's `alembic upgrade head && uvicorn` startup
command. The release overlay now resets that command to the backend image's
plain Uvicorn default; CI checks both release backend and frontend commands.
Local Compose JSON checks confirm both release commands are null while the
development command remains unchanged. No release stack, migration, account,
market source or live database write was run. A schema change still requires a
controlled one-off migration after a verified independent backup. This removes
one accidental startup-migration risk, not the missing pre-loss paper ledgers,
independent backup gap or M4/M5 release blockers.

## 2026-09-24 22:34 UTC paper-session entry and lifecycle copy

Actual Chrome on `/paper` showed five retained sessions whose first-column
links exposed shortened UUIDs, including two indistinguishable-looking
historical strategy rows. The visible action now reads `查看会话` / `Open session`;
its accessible name includes the translated strategy, data mode, lifecycle
status, UTC creation time and short audit ID. The full ID remains available in
the account detail's audit disclosure. Chrome's Chinese and English trees
distinguished the two historical accounts; selecting one opened its exact
persisted ledger, and Back returned to the list. The original Chinese/dark
preference was restored. The shared English lifecycle dictionary now renders
human-readable `Created`, `Running`, `Stopped`, etc. instead of raw uppercase
backend enums, without changing their API values or financial processing.
Two affected-page suites passed 31/31, full frontend 235/235, ESLint,
TypeScript and production build passed. This is agent-operated U8/QA-A11Y
progress, not a novice-user study, full screen-reader/WCAG audit, recovery of
the two absent ledgers, lawful forward simulation or release acceptance.
`QA-A11Y` remains IN_PROGRESS; `M4-DATA-INTEGRITY` and `M5-DELIVERY` remain
FAIL.

## 2026-09-24 22:24 UTC same-name research accessibility check

Actual Chrome on the populated `/experiments` list exposed three distinct
`M1 lifecycle recovery` records whose comparison controls previously had the
same accessible name. The row checkbox now includes translated status and UTC
creation time; both result links include the saved record's creation time,
and selected-removal chips show it visibly. Actual Chrome's Chinese and English
accessibility trees distinguished the complete, interrupted and cancelled
records and their links; the original Chinese/dark preference was restored.
One same-name/two-timestamp regression covers row links, checkbox selection,
removal and locale change. Full frontend 234/234, ESLint, TypeScript, production
build, changed-test Prettier and diff check passed. This is a bounded list
accessibility repair, **not** screen-reader/WCAG certification, independent
backup, recovered paper ledgers, licensed forward market data or release
acceptance. `QA-A11Y` stays IN_PROGRESS; `M4-DATA-INTEGRITY` and
`M5-DELIVERY` remain FAIL.

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

## 2026-09-24 21:54 UTC paper-handoff eligibility and performance-method check

Review found that the historical result page previously offered the paper
handoff for any successful historical job, although the form accepts only the
audited archive and registered strategy. A shared eligibility check now governs
both entry and destination; an incompatible historical dataset no longer gets
a dead-end link. A focused negative regression and the compatible real Chrome
result-page recheck passed. No account or order was created. Full frontend
232/232, ESLint, TypeScript and production build passed locally; PR #32 code
head `5e10757` passed [CI36064371291](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36064371291)
backend/frontend/Compose. Both draft nontechnical user guides now describe the
new handoff, its 93-day limit and separate ledger; this is documentation
progress, not an operator or novice-user review.

An attempted actual-Chrome chart performance check could not establish the
≤200 ms page-response target. The available read-only page evaluator does not
expose `performance`/`PerformanceObserver`, and one browser-control click
round trip took 2,062 ms; that number includes automation transport and is
**not** the app's response time. No performance PASS/FAIL is inferred, and the
existing target remains. A temporary in-app two-frame diagnostic produced
38–59 ms on some toggles but grouped ~1,996 ms delayed-frame callbacks while
the Chrome tab was background/being observed. That timing is also invalid for
the app's visible response. The diagnostic code was removed. A foreground
browser-native trace or equivalent measurement that separates page work,
background frame throttling and automation overhead is still required.

## 2026-09-24 21:41 UTC historical result to paper-account handoff

The completed audited-historical research result now links to a separate
historical paper-account form. The form retrieves the saved study, accepts only
the completed registered historical configuration, and copies exact capital,
strategy, universe, cost and risk inputs for review. It never copies result
metrics or creates/submits an account on navigation. When the study's range
exceeds the existing 93-calendar-day paper replay limit, the start date stays
empty and must be chosen explicitly; the saved end date remains visible.
Synthetic/ineligible studies fail closed. The account will have its own
snapshot, plan and ledger, not a continuation of the research preview.

Actual Chrome 153 on saved 293-session study `d9f27183` showed the Chinese
handoff link, then the independent form with historical provider locked,
2010-01-04→2011-03-22 source range explained, blank start, 2011-03-22 end,
CNY100000 capital, 20-session/20-holding strategy, 0.1 position cap,
-0.2 drawdown limit and 0.0003/5 cost assumptions. No form was submitted.
English Chrome displayed the same independent-account and date-limit warnings;
the original Chinese/dark preference was restored. PR #32 code head `e938b67`
passed [CI36063147686](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36063147686)
backend/frontend/Compose.
Unit regression covers the result link, long-range guard, exact-string inputs
and synthetic rejection. Full frontend 231/231, ESLint, TypeScript, production
build and changed-file formatting passed locally. Read-only live DB counts
remained datasets1/runs3/trades310/product jobs8/paper sessions5/events417.
This is bounded U6/U7 navigation progress, not proof of a common executable
plan, forward feed, missing-ledger recovery or release acceptance.

## 2026-09-24 21:01 UTC data-center confirmation target and open evidence

Actual Chrome on the running local Data Center measured the raw-update
consent checkbox's enclosing label at 663×26px on desktop. The existing label
now has a 40px minimum height; Chrome remeasured 663×40px. At a temporary
390×844 viewport it measured 307×42.875px and document width 375px, without
page-level overflow. The viewport was reset. No checkbox was selected and no
supplier request was sent. Frontend 228/228 tests, ESLint, TypeScript/build,
CSS Prettier and `git diff --check` passed. This closes one bounded pointer
target, not the full accessibility gate.

The user answered **unknown**, not yes or no, for an independent physical or
approved private backup location, a genuine pre-incident copy of paper
accounts `4b64380f` and `07d72259`, and lawful 2026 A-share feed rights.
None is inferred. Windows Docker's own launch log has no entry between the
2026-09-24 22:29 AEST reboot and the 2026-09-25 03:46 AEST manual launch.
The quoted HKCU Run path was changed after that failed login and awaits a
genuine subsequent login test; no duplicate startup mechanism or reset was
added. M4 data integrity, U7 forward and M5 delivery remain unaccepted.

## 2026-09-24 20:52 UTC Chrome missing-record recovery layout

Actual Chrome on the running local application exposed that the shared 404
panel squeezed its message, button and diagnostic into one horizontal row;
the paper-account button also sent the user to Workbench rather than the
persisted-account list. The shared error panel now stacks those elements,
while paper-account 404 alone supplies a localized `/paper` return link.
Chrome showed the corrected Chinese and English copy and the link opened the
five retained accounts. At a temporary 390×844 Chrome viewport, the document
had client/scroll width 375/375 and the return button height was 42px; the
default viewport and original Chinese/dark preference were restored.
Focused error/paper tests passed 25/25 with ESLint, TypeScript, Prettier and
production build. This is agent-operated viewport QA, not native 200% zoom,
screen-reader acceptance, recovery of two absent ledgers, or U7/M4/M5 PASS.

## 2026-09-24 20:43 UTC missing paper-account handshake recovery

The local in-app Chromium browser confirmed that a missing persisted paper
account (`4b64380f`) received HTTP 404 from its REST snapshot, but the
WebSocket was rejected before `onopen`, so the page previously retried and
ended with generic reload advice. The shared paper-stream hook now makes one
read-only REST classification after a failed initial socket handshake; a
typed 401/403/404 stops the retry timer and shows the existing bilingual
permission/not-found guidance. No saved balance or fill is synthesized.
The added rejected-handshake regression and all 23 paper-page tests passed;
the full frontend suite passed 228/228, with ESLint, TypeScript, Prettier and
production build passing. Browser recheck showed EN/ZH not-found guidance;
the separate retained account `d7044a3c` still displayed its saved cash
`81309.8134`, equity `99964.8134` and six fills. This fixes one truthful
missing-record path, **not** the two absent ledgers or U7/M4/M5 acceptance.

## 2026-09-24 20:06 UTC paper accessibility and startup recovery recheck

The local in-app Chromium browser reopened the persisted stopped historical
paper account without changing its cash `81309.8134`, equity `99964.8134`, or
six fills. A read-only computed-style scan of 406 visible leaf-text elements
on that page found zero below 4.5:1 for normal or 3:1 for large text in both
light and dark themes; English and Chinese were exercised. The scan composites
CSS ancestor backgrounds but is not a complete contrast/WCAG or screen-reader
audit. At 390×844 in Chinese/dark, document and client widths were 375/375,
the visible interactive targets measured at least 40px on both axes, and the
paper safety notice and replay label remained visible. Language, system theme
and default viewport were restored.

A read-only Windows check found the current Docker Desktop Run entry quoted,
Docker Engine reachable from WSL, and the four project services running (the
backend/PostgreSQL/Redis health checks healthy). The quoted entry has **not**
been tested by a subsequent genuine Windows login. Both draft user guides now
give the observed manual, terminal-free Docker Desktop recovery path without
claiming autostart acceptance. `QA-A11Y` and `M5-DELIVERY` remain incomplete.

## 2026-09-24 19:56 UTC explicit tradeability guard

The shared A-share rule resolver previously returned `executable=True` when
`is_suspended=False` even if the same dated security status had
`is_tradeable=None` or `False`. A new regression first failed on the unknown
case; the resolver now requires `is_tradeable is True`. Targeted market,
candidate-rule, smoke, execution-engine and dataset tests passed 62/62; Ruff
check/format and strict mypy passed. A normal reload of the existing stopped
historical paper account in the in-app browser showed the saved six fills,
cash `81309.8134` and equity `99964.8134` without browser warnings/errors;
that browser read did **not** exercise the new unknown-status branch. No account,
data-source, methodology or frozen research write occurred. The candidate
2026 rules remain conservative no-fill; `U7-FORWARD`, M4 and release are not
accepted. The user could not confirm legal 2026 feed rights, a genuine pre-loss
copy of two absent paper ledgers, or an independent physical backup destination.

## 2026-09-24 19:47 UTC bounded responsive and locale recheck

On the running local app in the Codex in-app Chromium browser, a 1024×768
viewport showed no document-level horizontal overflow on Workbench, Strategies,
Research, Task center, Paper sessions, Data center, Help and Settings in
Chinese/dark; the saved historical result also fit. Seven of those routes
were checked in English/system theme at the same width. The saved result and
restored stopped historical paper account were visually checked at 390×844 in
Chinese/dark; both had document/client width 375/375 CSS pixels. The paper
account retained cash `81309.8134` and equity `99964.8134`, with explicit
historical-replay and simulated-execution labels. Browser warning/error logs
were empty. An 18px research-list checkbox input was inside a 53px-high
clickable label; input dimensions alone are not a target-size failure.
English/system preferences and default viewport were restored afterward.
This is a bounded agent check, not actual Chrome, 200% zoom, screen-reader,
complete contrast, novice-user or full visual-matrix acceptance.

## 2026-09-24 19:38 UTC paper reconnect state labels and exhaustion

An independent paper-stream code review found that four consecutive WebSocket
closures after a successful REST snapshot exhausted the bounded reconnects
but left the old account and "authoritative portfolio" on screen beside a
reload error. A focused test failed on the still-visible portfolio. The shared
stream hook now clears the snapshot at final reconnect exhaustion, so the
page shows only the actionable reload error until a fresh authoritative REST
read. During bounded reconnect attempts, the still-visible snapshot is now
explicitly labelled "last verified" with an EN/ZH warning that it is not a
current balance; a successful REST rehydration restores the authoritative
label. The focused tests cover both branches and passed with the other
paper-page tests; all 227 frontend tests, ESLint, TypeScript and formatting
passed. The default local build could not clear a pre-existing root-owned
`frontend/dist/assets` directory; a production build to a fresh temporary
output directory passed without changing that directory. A live
in-app Chromium reload of the existing STOPPED historical account still showed
cash `81309.8134`, equity `99964.8134`, six saved fills and no browser errors.
The reconnect and four-close faults were exercised in component tests,
**not** injected into the live browser. No account, market, formal research or frozen data was
written. Full U7 recovery, M4 data integrity and release remain unaccepted.

## 2026-09-24 19:24 UTC production chart timing cross-check

On the same saved 293-session result in the production preview, 20 alternating
page-1/page-2 clicks to the changed visible pagination label measured p50
270ms/p95 275ms (264–277ms). Twenty benchmark-checkbox toggles plus checked
state readback measured p50 277ms/p95 284ms (269–287ms). The equivalent
20-toggle check against the restored development server also measured p50
277ms/p95 284ms (269–284ms). A direct Windows `curl.exe` read of the page-2
equity endpoint returned HTTP 200 in 10ms. Full-run return remained +4.67%,
the benchmark checkbox returned to checked, and the browser logged no errors.
The project dev frontend was restored afterward; frontend/API returned HTTP
200 and research/paper/event counts remained 8/5/417.

These UI timings include the in-app browser action/readback overhead, which
appears to dominate the ~270ms result on both builds. They are **not** evidence
of a production-only regression, nor a valid pass against the ≤200ms
interaction target. Re-measure this interaction in actual Chrome with an
instrumented click-to-visible-change method before closing `QA-PERF`; do not
change chart code from this ambiguous measurement alone.

## 2026-09-24 19:18 UTC bounded production-build performance check

The existing `frontend/dist` was served briefly with `vite preview` on the
project-owned `localhost:5173` origin while only the project's dev frontend
was stopped. The original frontend was restarted afterward; frontend and
`/api/health` both returned HTTP 200, and live counts remained 8 research
jobs, 5 paper sessions and 417 paper events. No study or order was submitted.

In the Codex in-app Chromium browser (1265 CSS-pixel viewport, populated local
database), 30 warm Workbench↔Strategies clicks reached the visible destination
heading at p50 21ms, p95 25ms and max 28ms. Ten full reloads of saved
293-session historical result `d9f27183` reached its saved +4.67% return at
p95 439ms (samples 367–439ms). This reload is not a click-response measure.
English and Chinese strategy pages rendered, English preference was restored,
and the browser reported no console warning/error. Timing includes browser
automation overhead. This is a bounded production-preview check, not actual
Chrome, cold-cache, larger-data, native-zoom or full `QA-PERF` acceptance;
that gate remains IN_PROGRESS.

## 2026-09-24 19:07 UTC failed paper rehydration hides stale balances

The paper detail kept its last cash/positions under an error after a failed
authoritative REST rehydration, even though the header called that portfolio
authoritative. The shared stream hook now clears the old snapshot and buffered
events on hydration failure, and clears it on a malformed stream event; only a
subsequent valid REST snapshot restores values. A focused 503-after-success
reconnect test and malformed-event test prove the fail-closed transition and
successful recovery (paper suite 21/21; frontend 226/226, lint, typecheck,
build and Prettier passed). A real local browser still rendered the
unchanged stopped account after successful hydration: cash `81309.8134` and
equity `99964.8134` matched the read-only API, with no account action. The
fault transition has unit evidence, not a new live-browser injected 503 claim.
No ledger, market receipt or formal research was changed. Full U7 recovery,
missing ledgers, independent backup and forward authority remain open.
[PR #32 CI 36046097765](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36046097765)
passed backend, frontend and Compose for code head `f7888a0`.

## 2026-09-24 18:58 UTC paper-session live-status semantics

The stopped historical paper-session detail rendered connection and session
state as plain text in the browser accessibility tree. The detail page now
marks these two changing labels as status regions without changing the shared
badge or any account transition. A real local browser reload confirmed DOM
`role="status"` on `Session connection: closed` and `STOPPED`; the browser's
accessibility-tree provider still coalesced that area into a text node, so
this is **not** a screen-reader announcement proof. Focused paper tests 20/20,
full frontend 225/225, ESLint, TypeScript, production build and diff check
PASS. No session was started and no market/ledger state was changed. `QA-A11Y`
remains IN_PROGRESS; U7 forward, M4 integrity and M5 delivery remain open.

## 2026-09-24 18:50 UTC A-share paper-entry default

Actual local browser `/paper/new` initially defaulted to the legacy AAPL
fixture despite the A-share-only shell. The form now defaults to the existing
2030 synthetic A-share demo and labels its 100,000,000 balance as a scenario
input, not an account-size recommendation. Legacy AAPL remains selectable but
is explicitly marked non-A-share in EN/ZH. The live browser verified default
after reload, manual legacy selection, Chinese label, and restored English
preference; no session was created or started. Focused paper tests 20/20,
full frontend 225/225, ESLint, TypeScript, production build, Prettier and
diff check PASS. PR #32 head `b67222f` passed
[CI 36043708809](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36043708809)
for backend, frontend and Compose. This closes a bounded novice-entry mode
ambiguity, not U7 forward, missing paper-ledger recovery or M4 data integrity.

## 2026-09-24 18:39 UTC prepared-report fallback check

In the live in-app browser, the persisted historical job `d9f27183` prepared
its JSON metadata report and displayed the English "Save prepared report"
link. Switching to Chinese showed "保存已准备的报告" with the same prepared blob;
switching back to English retained the link. This confirms the recovery text
in both guides matches the current UI. It does not establish that this browser
saved a file; the earlier real-Chrome CSV/JSON download proof remains the
file-transfer evidence. No new study, paper account or order was created.

## 2026-09-24 18:33 UTC bilingual guide correction

The draft Chinese and English guides incorrectly told users to find a retry
control when a prepared report did not automatically download. The actual
export component exposes a **Save prepared report** link after successful
preparation; failed preparation instead leaves the download buttons available.
Both guides now distinguish those cases and identify broker commission as a
simulation assumption, not a verified quote. The route names and exact
EN/ZH control text were checked against the current frontend; prior real
Chrome CSV/JSON download evidence remains the browser evidence. No new
download or app transaction was attempted. Operator/novice review and M5
delivery remain incomplete.

## 2026-09-24 18:19 UTC backup-location and exit-dialog check

Read-only Windows inventory again shows just Disk0 (2 TB NVMe), C:/D: on
that disk, and no mapped SMB drive. The Temp PowerShell drive is under C:.
This rules out an already mounted independent destination; it does not rule
out an unplugged device, private backup service or VSS snapshot. The current
process token is medium integrity with Administrators deny-only, so the
previous VSS access failure cannot be interpreted as no snapshots. A
privileged **read-only** shadow-copy listing remains the next bounded
recovery check, without restoring or deleting anything.

The in-app browser restored the agent's saved `U3 final diagnostic` step-2
draft. Clicking Save & exit raised the expected native confirmation, but
browser control could not inspect or dismiss it and the URL stayed on
`/research/new`; no exit outcome is claimed and the action was not repeated.
The existing focused unit test accepts the positive branch, not a live-browser
navigation proof. No study was submitted; read-only live counts stayed at
eight product research jobs, five paper sessions and 417 paper events. PR #32
head `f72d258` passed [CI 36039521609](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36039521609)
for frontend, backend and Compose. All release gates remain unchanged.

## 2026-09-24 18:10 UTC historical commission disclosure checkpoint

The historical paper-account advanced form now labels its commission rate and
minimum as simulation assumptions, not a verified broker quote. The guided
research cost hint says the same in English and Chinese. This changes no
fee calculation, accepted date-specific cost model, source authority or frozen
research. The local browser showed the English and Chinese form text; at
390x844 the English hint wrapped within the card with document width 375px
and client width 375px. No account was submitted. Frontend 225/225 tests,
TypeScript, ESLint, production build, Prettier and diff check passed. This
closes a bounded disclosure ambiguity, not U7 forward, M4 or release.

| ID | Required observable acceptance | Implementation/API/page | Tests/evidence | Status |
|---|---|---|---|---|
| M0-ENV | Correct host, clean baseline, published v1.1/main, no competing writer, healthy services | Git/GitHub/Compose | Live commands 2026-09-22; main/tag f88b5c6, PR12 merged | PASS |
| M0-UI | Real populated pages, new-user/empty-DB/service-failure baseline | `/`, legacy create, research, strategy | Before screenshots; fresh origin5174/disposable product_v12_baseline DB; isolated stopped backend reveals untranslated Failed to fetch | PASS |
| M0-REF | Official references and ≤2 layout directions | DESIGN_SYSTEM.md | Six official sources read; Apple rendered Chrome; one chosen layout | PASS |
| U1-START | Clean user → one primary guided action → strategy; skip/reopen guide; returning draft/recent/status | Workbench / | 2026-09-23 real Chrome fresh origin5174 + isolated `product_v12_baseline` (0 initial product jobs, no private archive): primary CTA opened registered strategy; four-mode guide closed with Esc and reopened; named draft `Clean install demo QA` saved, appeared on home and resumed at step 2; after completion home showed exact recent study and dated synthetic data state. Agent walkthrough, not a novice-user study | PASS |
| U1-DEMO | No-private-data install can run clearly marked synthetic demo; all four modes explained | Registry + standalone synthetic experiment | Isolated API exposed historical archive unavailable (`DATASET_NOT_MOUNTED`) and demo available. Chrome completed all four guided steps, created job `fb620f96-591b-48b3-b238-e92be1b41d02` in isolated DB and opened result (+0.39%, −0.04% drawdown, CNY25 costs); synthetic/non-market warning persisted on home, wizard and result, and no executable next-day plan was fabricated. Main DB remained 8 personal jobs and `.research` clean. Temp 8001/5174 servers stopped after QA | PASS |
| U2-STRATEGY | Registered strategies, plain rules/cycle/risk/data/evidence; drafts and saved versions | /strategies, URL-backed detail drawer and named local configuration versions | Chrome exact-string save/restore/reload/Chinese switch and pre-restore backup; drawer direct URL, Back/Forward and return from full strategy detail verified; independent review closed cross-tab overwrite; full frontend suite PASS | PASS |
| U3-WIZARD | Four steps, advanced disclosure, summary, back/save/restore/exit; locale preserves inputs | /research/new four-step form | Chrome synthetic and actual historical submission/result PASS; draft/locale preserved. The shared router guards dirty Back: actual Chrome dismiss retained the edit and step, accept reached home, and Forward restored them. Explicit Save & exit now uses the existing accessible dialog: actual Chrome EN/ZH cancel/Escape stayed on the wizard, confirm reached home, and Continue last draft restored the exact step, name, dates and capital. Failed local storage keeps the page open. Focused31/full241 frontend tests, lint/type/build PASS. Agent walkthrough, not a novice-user study | PASS |
| U3-JOB | Validated actual A-share job; stages/counts; persistent URL; refresh/reopen; idempotent duplicate | /api/experiments; independent durable manager | Live historical job `5f26f84f` remains SUCCEEDED 297/297 and a fresh Chrome context reopened its saved result URL. In a separate tmpfs test DB, the actual Chrome four-step synthetic wizard double-click sent one POST and persisted one job; resending the saved key/config from a fresh client returned the same ID with the DB still at one job. Existing backend concurrent-key/conflict test and frontend lock test cover the shared path. Synthetic result is labeled non-market; details below | PASS |
| U3-RECOVER | Real cancellation/retry/interruption; no partial results called success | cancel/retry and durable terminal states | Isolated cancellation, genuine FAILED terminal, controlled restart, and non-graceful SIGKILL recovery all verified. The crash left parent `77354e81` RUNNING 60/1212 with zero result rows; startup reconciled it to INTERRUPTED with HTTP409 result and a truthful Chrome warning. One linked child `52b76f45` completed 1212/1212, with 4108 rows only on the child and identical configuration SHA; two repeated parent retries reopened that child. The separate missing-partition FAILED path displayed specific bilingual integrity guidance and never yielded partial results. Details/screenshots below; this is not whole-machine power-loss or U7 forward-paper evidence | PASS |
| U3-ISOLATE | Independent exploration names/store; formal reports/OOS/freeze unchanged, dates labeled inspected | Separate product_research_jobs/rows, readonly archive | No .research diff; frozen hashes unchanged; formal 1 dataset/3 runs/310 trades before-after | IN_PROGRESS |
| U4-RESULT | Return/drawdown/cost/benchmark/limits, null semantics, true records and reasons | Personal result and date-linked holdings/trades, full-precision toggle | Chrome demo+historical results agree with exact APIs; real fill/snapshot2031-04-14 linked; source unavailable remains N/A; U4 tests/review PASS | PASS |
| U4-COMPARE | Reopen/compare 2–3; six config differences indicated | /experiments/compare?ids= | Chrome three actual runs, six conditions, exact fraction display and refresh preserving URL/results; comparison tests and independent review PASS; `u4/compare-three-results-en-dark-1024.png` | PASS |
| U4-EXPORT | Metadata report and formula-safe CSV | Server-streamed export, automatic download and persistent prepared-file link | Injection/precision/API tests PASS, including CSV formula-prefix escaping. On 2026-09-23 21:09 UTC isolated real Chrome 153 with `acceptDownloads` at the documented `http://localhost:5173` origin emitted successful download events for historical job `d9f27183`: trades CSV 29,316 bytes and metadata JSON 258,223 bytes, with expected filenames and `download.failure() = null`; JSON began with report metadata and exact job ID. Earlier in-app-browser download suppression remains an environment-specific observation, not a failed Chrome export. Agent walkthrough, not a real-user study | PASS |
| U5-MARKET | Search/watchlist/raw-adjusted/date/source view | /api/markets and /markets deployed0013 | 20 backend/14 frontend focused tests; independent review PASS; Chrome000001 raw22.45/HFQ874.904325432379995/suspension2010-03-01; watchlist persists fresh tab; dialog dates/locale/Esc;390+1280 no page overflow | PASS |
| U5-UPDATE | Incremental update/gaps/retry/history with source/license/rules/limits; no archive refetch | /data and /api/market-updates; separate product cache and migration0014/0016 | Real Chrome one-security/one-date job `3b729cf9` succeeded and survived restart/reload. Four-board job `164c947d` had 3 new + 1 cached candidates. Targeted control retry `ed796871` added two 2026-09-22 vendor candidates: 688622 isST=1; 603400 suspended with blank raw turnover normalized to zero, never executable. On 2026-09-24 real Chrome reopened the existing successful child from failed parent `0eecbddb`; live jobs/receipts/observations stayed 4/6/6, with one child. A separate provider-free fixture browser run cancelled a RUNNING task, reopened it, and proved two parent retries resolve to one child, with zero receipts; details below. Separate candidate 2026 rules still authorize no fills. Full 2026 source authority remains | IN_PROGRESS |
| U6-PLAN | Real candidates/targets/quantities/cash/reasons/rejections; as-of/snapshot/version; insufficiency/staleness | Persisted result preview and account-native plan in the audited historical paper event journal | Historical job `d9f27183` completed 293/293; its independent preview had 32 candidates and 5 risk rejections. A new isolated historical account `2f005ae8` saved its own 2011-03-22 plan with 20 candidates, submitted simulated proposals, and six later fills; the 2011-03-23 snapshot exposes the last actual rebalance plan separately from the latest balance. Real Chrome ZH/EN/mobile evidence below. New-market plan/receipt and forward-source authority remain pending | IN_PROGRESS |
| U7-MODES | Three isolated account modes, start/pause/stop/risk/ledger | Synthetic demo + distinct audited historical replay with durable pause/resume; forward not implemented | Chrome previously verified account `4b64380f` with 20 orders/six fills, but that post-backup account is now absent after the 2026-09-23 database incident. The older uninterrupted account `d7044a3c` was restored from a verified backup. Retained legacy AAPL fixtures are now explicitly labeled non-A-share in both languages; this does not supply forward mode or recover the missing ledger | FAIL |
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
| QA-PERF | Immediate feedback; measured local interaction p95 target≤200ms; bounded charts/tables | Research archive and result/compare routes loaded on demand; initial JS entry chunk 549.12→409.17 kB minified (169.44→129.31 kB gzip) | On DESKTOP-3EOROGR, actual isolated Chrome 153 at 1440×900 with local populated database: 30 warm Workbench↔Strategies route clicks from Playwright click start to visible h1 had p50 15.6ms/p95 32ms/max 48.2ms, including automation overhead. A separate persisted 293-session result page (138 currently rendered table rows) took cold 560ms and 10 warm full reloads p50 883ms/p95 923ms to show Total return; this is document/data-load latency, not the same interaction metric. API requests themselves took ≤12ms in a warm trace. Bounded native-200% and production-preview timings are detailed above and below; actual Chrome production interaction, cold cache, larger data and wider diagnosis remain | IN_PROGRESS |
| QA-ENGINE | Decimal/server validation/idempotency/task isolation; same financial path | Existing financial path + independent queue | 862 backend tests; actual 2011 exploratory run completed; synthetic clearly separated | IN_PROGRESS |
| QA-REVIEW | Implement→browser review→fix→recheck; independent read-only review resolved | Independent backend+frontend code/test review | Reported races/idempotency/format/routing defects corrected; final browser repeat pending | IN_PROGRESS |
| M4-DATA-INTEGRITY | Application and formal-history persistence, isolated tests, recoverable backup | Suite-wide test-DB guard and verified additive restore | Live DB was found missing formal 1/3/310 ledger and later paper accounts. Formal ledger and four pre-backup accounts were restored atomically; `4b64380f` and `07d72259` remain absent. Live-config pytest was rejected; isolated backend969 PASS/one optional skip with live counts stable. The post-recovery dump restored into a new database, with 44/44 public tables matching live by row count and sorted-row hash. This same-disk dump is not independent disaster recovery and missing-history disposition remains open | FAIL |
| QA-RELEASE | Full backend/frontend/lint/types/build/migrations/durability/CI/compatibility | Incremental suites and reversible migrations | Isolated release-image/browser rehearsal and [CI 36081787335](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36081787335) backend/frontend/Compose plus production-backend/tmpfs smoke PASS. The live DB data-loss incident, missing independent disaster-recovery proof, forward authority and remaining M4/M5 acceptance keep the release gate FAIL; frozen research files were not changed | FAIL |
| M5-DELIVERY | New/old screenshots + key recordings, bilingual manual/demo/start/recovery/rollback, mode freshness/limits | Draft [Chinese](USER_GUIDE.zh-CN.md) and [English](USER_GUIDE.en-US.md) guides | Both draft guides cover current UI, mode/date boundaries, recovery and rollback; bounded Chinese demo/walkthrough videos and screenshots exist. A second real 2026-09-25 12:05 AEST login did not launch Desktop under the quoted Run path, despite AutoStart and enabled StartupApproved. One limited current-user AtLogOn task replaced that Run entry; the next genuine login has not tested it. Manual launch recovered Engine, four services/volumes and original database counts without loss. Full key-interaction coverage, novice-user/operator review and terminal-free startup remain incomplete; no English video is claimed or treated as a separate requirement | FAIL |
| M5-PUBLISH | Small feature PRs reviewed+CI+browser→merge; v1.2.0 only after all required rows pass | feature/product-experience-v1.2 | v1.1 remains immutable | NOT_RUN |

PRODUCT_GOAL_COMPLETE = NO. Remaining required work is the full non-PASS set above.

## 2026-09-24 17:57 UTC retained fixture mode clarity

The actual local `/paper` page contained two preserved AAPL fixture sessions
beside A-share historical and synthetic accounts, while the product shell
called itself A-share-only. The shared provider label now explicitly says
"Legacy local AAPL fixture · not A-share data" in English and
"保留的 AAPL 本地测试回放 · 非 A 股数据" in Chinese. Existing sessions and links
were not filtered, edited or deleted. The same live browser page displayed
both translations; the original English preference was restored. Its desktop
table showed the longer label without clipping. The focused paper page suite
passed 20/20, full frontend 225/225, TypeScript, ESLint, production build,
Prettier and `git diff --check` passed.
This is a narrow labeling fix, not U7 mode or data-integrity acceptance.

The prior Save & exit tab was absent from the browser inventory. A fresh
local tab restored the saved step-2 draft. Clicking its Save & exit button
raised the expected native confirmation, but browser control then could not
inspect or resolve that dialog; the URL inventory remained `/research/new`.
The action was not repeated, no research POST was made, and an exit outcome
is **not** claimed. A separate QA tab remained usable. An initial
`127.0.0.1:5173` tab showed an apparent API error because its origin differed
from the configured `localhost:8000` API; opening the documented
`localhost:5173` origin showed service online and the persisted studies.
This was a QA-entry mismatch, not a new Docker or database outage.

## 2026-09-24 17:48 UTC actual next-login startup failure

Windows booted at 2026-09-24 22:29:20 AEST; Explorer started at 22:29:36.
At 2026-09-25 03:44 AEST there was no Docker Desktop/backend process, and
both Ubuntu and `docker-desktop` WSL distributions were stopped. Docker's
Desktop log had not advanced past the previous pre-reboot launch, and no
Docker-related Application event appeared in the bounded 22:28–22:40 log.
`AutoStart=true`, the Docker-only `StartupApproved\\Run` value still began
`02`, and the HKCU Run entry remained present. Thus the earlier approval
correction failed an actual login test; whether Windows skipped the entry or
the app exited before logging is not established.

The exact Run value was the unquoted existing executable path
`C:\Program Files\Docker\Docker\Docker Desktop.exe`. After verifying that
value and executable, only this one Run value was changed to the quoted
`"C:\Program Files\Docker\Docker\Docker Desktop.exe"`; readback and the
enabled approval value matched. The old unquoted string is the rollback
value. This is a hypothesis-driven, reversible startup correction, **not**
proof of root cause or M5 acceptance. No additional startup mechanism,
installer, reset, cleanup or reboot was invoked.

The already-installed Desktop app was launched once manually. Ubuntu then
reached Engine 29.8.0 / Compose 5.5.1; the four original project volumes were
listed, PostgreSQL/Redis/backend became healthy, Redis returned PONG,
`/api/health` and frontend returned HTTP 200. Read-only live counts remained
research runs 3, research trades 310, paper sessions 5, paper events 417,
product research jobs 8 and market-update jobs 4, matching the recorded
post-recovery baseline. This is service recovery, not restoration of the two
missing pre-loss paper ledgers or an independent backup. The user could not
confirm independent backup media, pre-loss snapshot/WAL or lawful 2026 feed
rights; all three stay unverified. The next genuine login still must prove
terminal-free auto-start before M5 can pass.

## 2026-09-24 12:25 UTC shared pagination target in actual Chrome

A fresh Chrome tab on the running local app, Chinese/dark at an explicit
390×844 viewport, showed no page-level horizontal overflow across nine routes:
strategies, markets, experiments, tasks, paper, data, help, settings and a
persisted historical result. Document/client widths were 375/375 CSS pixels
on all nine. This is one locale/theme/viewport slice, not the whole matrix.

The common pagination buttons on experiments, tasks, paper and data were
36px tall. Their callers all use the same `Pagination` component and one
`.pagination button` rule, whose minimum height was raised to 40px. Chrome
then measured respectively 2, 4, 2 and 2 buttons at 40px; all four pages
still had document/client widths 375/375. The research-list pagination row
was visually inspected in Chrome after scrolling. Its disabled Prev/Next
state reflected the actual 8-item saved list, so this did not exercise an
enabled edge click. The existing component test covers exact page offsets.

The same scan also found 18px checkbox inputs, but their actual clickable
labels were at least 40×40px in the research table, 52×53px or larger in its
column controls, and 307×43px for the data-center consent. No extra checkbox
CSS was added. Frontend 225/225 tests, ESLint, TypeScript, production build,
CSS Prettier and `git diff --check` passed. The temporary browser viewport
override was reset. `QA-A11Y` and `QA-VISUAL` stay **IN_PROGRESS**; these
measurements are not a full target-spacing, native-zoom or screen-reader audit.

## 2026-09-24 12:15 UTC test isolation and Windows login-startup correction

The backend suite's shared `pytest_sessionstart` guard requires `APP_ENV=test`
and a `quant_test`-named database. In the running backend container, a
collection-only invocation with `APP_ENV=development` and an intentionally
unreachable `quant_platform` URL exited 1 with the guard message before any
test was collected. The isolated test Compose specifies `quant_test` on a
tmpfs PostgreSQL data directory. This is a bounded fail-closed check, not a
re-run of the suite or proof that missing live paper history was restored.

Windows login-startup inspection found Docker Desktop's own AutoStart setting
true and its exact `HKCU\\...\\Run` executable still present, while the
`StartupApproved\\Run` value for Docker Desktop was twelve zero bytes. Four
other enabled per-user entries began `02`. After checking that the Docker
executable existed and the value had not changed, only that one approval value
was set to `020000000000000000000000`; readback matched. The old value was
`000000000000000000000000`, so the one-value change is reversible. This
matches the enabled pattern described in [Microsoft Q&A](https://learn.microsoft.com/en-us/answers/questions/2843923/enforce-startup-apps-through-gpos),
but is an inference about this machine, **not** a proven root cause. Docker's
[official startup setting](https://docs.docker.com/desktop/settings-and-maintenance/settings/)
alone had not delivered a running Engine after the observed reboot. Current
Compose still has the same four running services; PostgreSQL, Redis and backend
are healthy, Redis returned PONG, and API/frontend returned HTTP 200. Do not
promote M5 until the next real login starts Docker and the app without terminal
assistance. No second startup task, reset, volume deletion or service restart
was performed.

Chrome's existing guided-research page did display the native Save & exit
confirmation. The browser control timed out during dismiss/refresh, so the
dialog outcome and post-click route were **not** verified. There was no new
research submission. Inspect the live dialog/page state before repeating any
navigation action; this observation does not change U3-WIZARD status.

## 2026-09-24 11:45 UTC Help FAQ pointer target

Actual Chrome on the running local app, Chinese/dark: the first Help FAQ row
looked about 70px high, but clicking its lower blank area at `(500, 615)`
left the native `<details>` collapsed. The shared `.helpQuestion` CSS had 20px
vertical padding on the non-interactive parent and only a 30px minimum on
`summary`. Moving that padding to the native `summary` and giving it a 70px
minimum retained the disclosure marker and row layout. The same lower-edge
click then expanded the Chinese answer; in English, `(500, 635)` expanded
the translated answer. Chrome's accessibility tree reported the native
button as expanded and focused in both languages. The original Chinese
preference was restored. This is a bounded `QA-A11Y` pointer-target fix, not
a native-200%-zoom, mobile, assistive-technology or full WCAG audit. Frontend
225 tests, ESLint, TypeScript typecheck, production build and CSS Prettier
all passed in the existing frontend container; no backend or research test was
rerun for a CSS-only change. `QA-A11Y` remains IN_PROGRESS.

## 2026-09-24 11:25 UTC Docker recovery and U3 isolation read-only audit

Docker Desktop 4.92.0 was unexpectedly stopped: the `docker-desktop` WSL2
instance was stopped, its backend process absent, and both Windows Engine pipe
and Ubuntu CLI integration unavailable. Launching only the already-installed
Desktop app restored Engine 29.8.0 and Ubuntu integration without reinstall,
reset or cleanup. The existing four project containers restarted; PostgreSQL,
Redis (`PONG`) and backend health became healthy, and API/frontend returned
HTTP 200. The four named project volumes persisted. This is another bounded
engine-restart check, not a full Windows reboot or independent backup proof.
Windows still reports only one physical NVMe disk.

Read-only live SQL now shows formal research 1 dataset / 3 runs (Development,
Validation, OOS) / 310 trades, versus 8 personal jobs / 1110 personal result
rows. The product and formal jobs have distinct tables and zero shared run IDs.
The formal dataset remains `PASSED` and frozen, with canonical SHA-256
`1d7b6134e2c6a7026aa124bed57ab101ea910847e10e3d799c45f6c6a1e17f9e`.
The current archive manifest file SHA-256
`693c0b81d942d9532c6ec6c6455fbafab76921a40c8093bace32f1fac9cf2cd0`
and freeze file SHA-256
`228569f1dcbb099e8b7225ef72f6960660f5741bb7298c051809bbb1ab3739bd`
match the 2026-09-22 M1 evidence. The OOS lock still records consumption.
These checks strengthen U3-ISOLATE evidence but do not prove every pre-loss
formal DB row matches its original state; the data-loss and independent-backup
gates remain FAIL/blocked and U3-ISOLATE remains IN_PROGRESS.

## 2026-09-24 11:33 UTC Windows startup observation

Windows reports last boot at 2026-09-24 18:33:33 AEST and the console user
signed in around 18:33. Docker backend logs continue until 18:32:43 before
that reboot, then have no later entry until the agent's manual launch at
21:22:14. At that check the Desktop/backend process, Engine pipe and
`docker-desktop` WSL instance were absent/stopped. The installed app's
`AutoStart` setting is true, an HKCU Run entry exists and Ubuntu integration
is enabled; these settings alone did not make Docker available after this
login. No matching Docker application-crash event was found in the bounded
18:30–21:25 Application log check; neither the reason for non-start nor an
intentional intervening exit is established. Starting the existing app by
hand restored the original services and volumes without reset or cleanup.
Thus M5's terminal-free post-reboot startup acceptance is **not met** by this
observation. This is not evidence of another data loss.

## 2026-09-24 06:00 UTC shared status-time accessibility check

The live in-app browser at `localhost:5173` exposed the Workbench service
status's screen-reader-only check time as raw
`2026-09-24T05:40:12.769Z UTC`. The shared AppShell now uses the existing
`formatUtc` presentation helper; the same browser accessibility tree reads
`2026-09-24 05:40:12Z (UTC)` in English and
`2026/09/24 05:40:12 (UTC)` in Chinese. Language was restored to English.
No market date, data status, or API value changed. AppShell regression covers
both locales and rejects a raw ISO timestamp. Frontend 225/225 tests, ESLint,
Prettier, TypeScript and production build passed. This is an agent browser
accessibility-tree check, not a screen-reader user study; U8-I18N and QA-A11Y
remain IN_PROGRESS, and the release/data-integrity blockers remain open.

## 2026-09-24 04:12 UTC account-native historical plan

The U6 gap was not a missing button: the saved research-result preview belonged
to its exploratory run, while the paper account independently generated orders
without saving an account-specific plan. New historical accounts now version their
plan contract as `PAPER_ACCOUNT_PLAN_V1` and store the completed-date plan in the
same durable `portfolio.snapshot` event batch as their simulated risk/OMS/portfolio
updates. Earlier accounts without that marker replay their original journal
without a retroactive plan. The shared preview builder and existing display
component were reused; no broker or new market feed was introduced.

In an owned tmpfs PostgreSQL test stack with the audited historical archive mounted
read-only, actual Chrome 153 at 1280×800 created account
`2f005ae8-75d4-46e4-812b-051c59381009` and the user deliberately clicked
Start. Instrumentation saw exactly one create POST and one start POST; subsequent
reload, language and viewport checks added no POST. The stopped account's final
session was 2011-03-23: latest cash CNY81,309.8134, equity CNY99,964.8134 and
six fills. The API's latest-day plan correctly said `NOT_REBALANCE_SESSION`, while
`last_rebalance_plan` selected the persisted 2011-03-22 plan (20 candidates,
`submitted_to_account=true`, estimated approved-buy cash CNY75,191.75091) with
the same account ID. This is not today's advice; the displayed next accepted
session is the historical 2011-03-23, and cash at plan time was CNY100,000,
distinct from the latest balance. Both languages visibly explain that distinction.
At 390×844, Chrome measured document/client width 390/390 and showed a local
horizontal-table scroll hint. The test-account data are disposable, not a live
paper ledger or a forward-market receipt.

The actual browser [Chinese plan](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-plan-zh-20260924.png),
[English plan](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-plan-en-20260924.png), and
[English mobile plan](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-plan-en-mobile-detail-20260924.png)
are outside Git; SHA-256 values are respectively
`91764EBCB93CB0E91DE09C57606B8204C2F52F3E73BB4D7F4C1DEB4E3DA59E0E`,
`321EACCABF9623BA4015EFA216DE1CB41611D68216A2595D07B45024054D4C7B`,
and `C47FB9AF76534E43306B80479124F938453D77EC27D02DD79E2BF614C2A0EA0D`.
Focused frontend 33/33 and final full frontend 224/224, ESLint, TypeScript and
production build passed. The first isolated full-backend run failed 28 queue
ownership checks because the still-running owned QA backend held advisory locks
on that same disposable database; no financial assertion failed. After stopping
only that QA backend, the identical full suite passed 976/976; Ruff, formatting
and strict mypy also passed. An independent read-only review found that the
initial configuration checksum omitted account order/exposure risk limits;
the hash now includes full effective risk and the account-native plan test
proves it changes with `max_order_notional`. A legacy-account test proves no
plan is silently backfilled, and a WebSocket test covers incremental plan
state. The final isolated backend suite passed 977/977 and the final frontend
suite 224/224 after these fixes. The three real Chrome captures preceded the
checksum-only backend correction; the separate post-correction in-app browser
recheck below is not mislabeled as another Chrome run.
U6/U7 and the release remain open:
neither a lawful post-start forward data receipt nor the two missing genuine
paper ledgers or independent physical backup exists in this evidence.

## 2026-09-24 04:43 UTC post-correction account-plan browser recheck

PR #32 commit `84fc718` passed [CI 35956311105](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35956311105)
(backend, frontend, Compose). In the owned `quant-v12-u6plan` test stack, a
new account `f30dc3b9-d2a2-42d1-8991-de3d6ae449d7` completed its historical
2011-03-01..31 replay with six simulated fills. Its API returned a latest
2011-03-31 non-rebalance snapshot and the last genuine 2011-03-22 rebalance
plan: 20 candidates, `submitted_to_account=true`, next accepted session
2011-03-23 and configuration SHA-256
`316ddc3a39ce4211d073782af49108cdd4ad1245241f3b0cf39750b7e37c30bb`.
The account used this same post-correction code, not a recreated old screenshot.

The Codex in-app browser on `http://localhost:5174` loaded the stopped account
after the replay. Chinese and English both displayed the dated account-native
plan, plan-time CNY100,000 cash versus latest CNY81,309.8134, the
CNY75,191.75091 estimated approved-buy cash, and explicit historical-only /
no-broker-order wording. Opening provenance visibly showed configuration
`316ddc3a…30bb`, matching the API. At its 1280×720 viewport, the plan copy
measured 15px/25.5px line height, document width 1265px, and the plan table
scrolled locally (1043px content within 938px), not at page level.
At an explicit 390×844 viewport, Chinese plan text and the historical-only
warning remained visible without page overflow (document width 375px), while
the same 1043px table scrolled within 307px; the temporary viewport override
was reset after QA. The
[mobile capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-plan-postfix-zh-mobile-20260924.png)
has SHA-256 `BDDB754F4D2C89423651B1122128A02423CC1DC60FE0BEE543FB6EAD10EFCCA6`.
[English](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-plan-postfix-en-20260924.png)
SHA-256 `4DEED0DDB5174F5E4CB34D22D016A61D7F79C013E28450246642531230729740` and
[Chinese](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-plan-postfix-zh-20260924.png)
SHA-256 `91F75B94A84A99ACBE2B14771F50D6737B61343B676954F56D1A4D06ADE73A62`
are actual browser captures outside Git. No account command was sent through
the browser recheck; account creation/start occurred separately on the
disposable API. The first attempt at `127.0.0.1:5174` showed a service error
because the development CORS/API origin was configured for `localhost:5174`;
switching to that exact origin resolved it without changing security settings.
This closes only the bounded post-correction historical-plan visual check, not
the broader U6/U7 forward-data or release gates.

An independently created account `35e2bd86-3590-4014-8665-9c5a88800313`
used the same historical dates and strategy with a stricter CNY3,000
`max_order_notional`. Its persisted 2011-03-22 plan had 20 candidates, six
approved and 14 `ORDER_NOTIONAL_LIMIT` rejections; the plan's configuration
SHA-256 changed to
`fdb3a6a3bdb5d39b508f76b9355571d15bc6c32559d42acde4221e87f80eb53e`.
Three later fills belonged only to approved securities: the intersection of
14 rejected symbols with three filled symbols was empty. The same browser
rendered all 20 rows with six Chinese approval explanations and 14 explicit
`已拒绝: 订单金额超出配置上限` explanations; the
[risk-decision capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-plan-risk-reject-zh-20260924.png)
is outside Git, SHA-256
`09E6F9A9492F19B939A349D110329DD16F24DE909096C8EAB666EBE217532063`.
Both accounts were created and started only in the owned disposable test DB;
the live paper-session count remained five. This proves a bounded historical
risk-rejection path, not lawful new-market execution.

## 2026-09-24 05:08 UTC mobile topbar target follow-up

At 390×844 on the live `/paper` list, the menu and search controls were
36×37px and 36×38px; the English language target was only 27.9×40px. Shared
mobile CSS gives menu, search and both language buttons at least 40×40px.
The first spacing attempt wrapped the tool group to a new row, so the final
mobile gap is 8px; the final measured first row contains all five controls,
while the dated data-context link remains on its own second row. Document
width was 375px within a 390px viewport. Lower-edge clicks on the expanded
menu and search targets opened their intended panels; closing restored the
page and search focus. The
[mobile capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/topbar-targets-en-mobile-20260924.png)
is outside Git, SHA-256
`69208CD0CE02FA8E2F6D9C7EFEBC7E73E4848400DBF3C1ADCF79B510BCDED341`.
The viewport override was reset. Full frontend 225/225, ESLint, TypeScript
build and CSS Prettier passed. PR #32 commit `506f2c2` passed
[CI 35958686226](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/35958686226)
(backend, frontend, Compose). This closes one bounded pointer-target defect,
not a full WCAG 2.2 AA or native-zoom signoff.

## 2026-09-24 05:02 UTC draft autosave and mobile Back target

An unchanged wizard autosave had been rewriting only `savedAt`, making a
cancelled recovery preview appear to alter the shared draft. The shared
`saveExperimentDraft` path now retains the exact stored JSON when form, step
and request identity are unchanged; a real form edit still receives a new
timestamp. The focused configuration/recovery tests passed 17/17 and the
full frontend suite passed 225/225, with ESLint, TypeScript, production build,
Prettier and `git diff --check` passing. In the live in-app browser, an
alternate recovery draft was previewed and **Keep current draft** returned to
the unchanged `U3 final diagnostic` name/step. Reopening the wizard in a new
tab again showed that saved name and step 2. The
[reopen capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/draft-cancel-reopen-en-20260924.png)
is outside Git, SHA-256
`9446EABC95695687C9838B7DBA191F1799DE44D52ADF2DC628BEB00669D0D627`.
The browser-control interface stalled on the native **Save & exit** confirm;
that confirm's subsequent navigation was **not** verified and is not claimed
as passed. No research job was submitted.

The shared `.backLink` target on five detail pages was 21px high; its CSS now
gives a 40px minimum target without a page-level mobile overflow. At an
explicit 390×844 viewport, the real restored historical account's link
measured 116.8×40px, document width 375px against viewport 390px. A click
at `(40,313)` near its lower edge navigated to `/paper`; the original 21px
target would not have included that point. The
[mobile capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/paper-back-target-mobile-20260924.png)
is outside Git, SHA-256
`CE649E1B1401586665BF390EF32B4E45BA4A468B5E7BCE5AC7543B6D6DEEE4BD`.
The viewport override was reset. This closes two bounded defects, not full
U3 recovery, WCAG 2.2 AA, data-integrity or release acceptance.

## 2026-09-24 03:35 UTC paper-list error guidance

Actual isolated Chrome 153 at 1280×800 intercepted only the saved paper-list
GET with HTTP 403. Before the fix, `/paper` replaced the typed API error with
a generic service message. Passing the original error to the existing shared
`ErrorPanel` now shows explicit permission guidance and a visible reload link.
The [before](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/paper-list-403-before-20260924.png)
and [after](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/paper-list-403-after-20260924.png)
captures are outside Git, SHA-256
`ED53B644F29C707609CC2E86F75C972772B123183B62284783A533074FB168CB` and
`01674A581DD336C3F9EA82772902B624F3A4C6A9EC908C197E38ADA8945B65EB`.
After removing interception, the visible reload restored all five persisted
accounts. In Chinese, an intercepted HTTP 408 showed timeout guidance and the
same next step; its [capture](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/paper-list-408-zh-20260924.png)
has SHA-256 `C5736603C0BCDCBD76BEA0FE4226B6171BA684632587B171724E5A73D9F67578`.
The instrumented checks sent zero POST requests. A focused regression passed
19/19 paper-page tests; full frontend 221/221, ESLint, TypeScript, Prettier and
production build passed. This closes one `UX-ERROR`/`U8-I18N` defect, not the
full fault, accessibility or release matrix. A 403 injection is not a real
permission grant, and no account execution or forward-market receipt occurred.

## 2026-09-24 03:24 UTC Data Center detail targets

Actual Chrome 153 exposed a bounded `QA-A11Y` pointer-target defect on the
populated Data Center. At a 504×336 CSS viewport (a narrow-layout proxy,
**not** native 200% browser zoom), its two technical-lineage summaries were
32px high, source/policy summaries about 25px, and expanded source/archive
links only 16–20px. The existing shared technical-detail and market-update
CSS now gives those summaries and links a 40px minimum click height, without
changing destination URLs, provider permissions, data or update behavior.

After hot reload, the same route measured all eight relevant summaries/links
at 40px and document/client width 504/504. Clicking the lower edge of both
summary types toggled the intended `<details>`; keyboard Space closed the
focused provider summary with a visible solid focus outline. In a separate
390×844 Chinese/system-dark Chrome view, the page stayed 390/390 wide,
all eight targets remained 40px, and the expanded provider/terms links
remained visible at 40px. The [collapsed mobile view](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/data-center-targets-zh-dark-mobile-20260924.png)
has SHA-256 `FDC2CD0145E65347ABEA3314C1200E2D30EA52A173D97DF6BC8C55603D23A76D`;
the [expanded source view](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/data-center-source-links-zh-dark-mobile-20260924.png)
has SHA-256 `A40B1EB6A97555614330A650C10A750709B9183244B35D0932EC2ECD6B701FFE`.
Both are actual browser captures outside Git. Frontend 220/220 tests,
ESLint, TypeScript, production build and CSS Prettier passed. This fixes one
target-size defect; it is not a full WCAG 2.2 AA/screen-reader, native-zoom,
forward-source or release signoff.

## 2026-09-24 03:14 UTC U6 result-to-account browser chain

Actual Google Chrome 153 at 1280×800 reopened saved historical exploration
`d9f27183-a9a1-4f34-aef4-eba439f53374`. Its result showed the saved
2011-03-22 simulation preview: next accepted session 2011-03-23, replayed
cash 45,539.94836 CNY, estimated approved-buy cash 44,221.44166 CNY, 32
candidates and five cash-risk rejections. The result separately explained
70 proposed orders, 65 risk-approved proposals and 18 fills, including
non-fill reasons. It explicitly said the preview sent no order to a separate
simulated account and was not current trading advice.

Using only visible UI, the tester returned to the research list, selected
that study and saved historical study `5f26f84f-b6da-4eac-805a-fbc28fd27af4`,
and opened their comparison. The comparison flagged different trading
periods, despite matching dataset, costs, capital, risk and strategy settings;
it did not rank or recommend a strategy. The tester then used the persistent
sidebar to open independent paper account
`d7044a3c-7ef3-46ba-accd-197a6d40505e`, visibly labeled audited
A-share **historical replay**, STOPPED, with 2011-03-23 session, portfolio,
positions, 20 orders and six fills. This account was not created or funded by
the experiment preview. A second instrumented pass through the same browser
route sequence recorded zero POST requests. No market provider was contacted.

The [comparison screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-comparison-chain-20260924.png)
has SHA-256 `503E7C66E3EE242554664125FC1F532A1A0D1AB3A5018549C06279BAA47D0DBE`;
the [account screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u6-account-chain-20260924.png)
has SHA-256 `5DFD5EB3D110F23284287E7C3C20C0CEE92FA75CAD9874F1C51D94D624FADCCD`.
Both are outside Git. This is a bounded terminal-free historical-navigation
check; U6/U7 remain IN_PROGRESS because the preview is not an executable
forward plan, no new-market receipt was accepted, and paper-ledger recovery
remains incomplete.

## 2026-09-24 03:07 UTC U5 cancellation/retry in isolated real Chrome

An owned `quant-v12-u5cancel` Compose test project used PostgreSQL
`quant_test` on tmpfs, a read-only mount of the existing historical archive,
backend port 8001, and frontend port 5174. A temporary launch fixture replaced
the market-data transport **before worker startup** with a coroutine that
waited only for cancellation; it never contacted the named provider. The
fixture file was removed after QA. Main services and data volumes were not
stopped or written.

In isolated Google Chrome 153 at 1280×800, the user submitted one existing
archive security for 2026-09-22. One create POST produced durable task
`76314ee4-91f6-41c7-aa72-80f3d350fd38`, visibly RUNNING at 0/1. One
cancel POST showed immediate sending feedback, then persistent CANCELLED at
0/1 with no success summary. Leaving for Task Center and opening its direct
URL returned the same terminal state. Clicking its Retry created child
`bdf49c26-988d-4b1a-9aec-f34a2044eef8` (attempt 2); that child was
explicitly cancelled. A second Retry click on the parent returned the same
child URL, not a third task. The isolated DB held exactly two CANCELLED jobs,
one parent-child link, zero receipts and zero observations. The main DB
remained four update jobs, six receipts and five paper sessions. No real
market data was acquired and no forward execution was authorized.

The [reopened-cancel screenshot](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/u5-cancel-fixture-20260924.png)
is outside Git, SHA-256
`3C005DF8136D3529018BB647CEB4E31D0030562D74A8C1C70A1DD3FDB622A372`.
Only the three owned test containers and their network were removed after QA;
the database was disposable tmpfs, and no Docker image or volume was deleted.
The test frontend left one unreferenced anonymous `node_modules` volume
created at 03:03:53 UTC; it was not pruned or treated as project data.
This closes the bounded U5 cancel/retry browser path, not source authority or
the overall U5/QA-RELEASE gate.

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

## 2026-09-24 11:54 UTC shared technical-disclosure target checkpoint

Actual Chrome on the registered strategy detail (Chinese/dark) showed the
`technicalDetails` row's upper blank area did not toggle the native disclosure,
while its text line did. The shared CSS had 20px vertical padding on the
noninteractive `<details>` parent and only a 40px `<summary>` target. Moving
that spacing onto `<summary>` made the same upper-edge coordinate toggle the
expanded state; the English "Technical lineage" upper edge also expanded and
exposed the correct strategy ID/method link. Chinese/dark was restored.
This shared class also serves strategy recent details and market lineage.
Frontend 225 Vitest, ESLint, TypeScript/production build, and CSS Prettier PASS.
This closes a bounded pointer-target defect, **not** the full WCAG 2.2 AA,
screen-reader, native-zoom, data-integrity, forward-market, or delivery gates.

## 2026-09-24 12:02 UTC bounded recovery inventory and user-path recheck

Read-only Windows/WSL inventory found the existing `pre0014` and `pre0015`
PostgreSQL dumps plus the after-loss and post-recovery dumps already recorded
above; none is a newly discovered pre-loss copy of the two absent paper
sessions. The standard Windows File History configuration path is absent.
Windows VSS shadow-copy enumeration returned `initialization failed`, and
`vssadmin list shadows` explicitly required elevated privileges. Thus shadow
copies are **not assessed**, not proven absent. Two anonymous Docker volumes
were created at 2026-09-24 03:03Z and 03:55Z, after the 2026-09-23 loss;
their contents were not altered. Docker Desktop's official login-autostart
setting, HKCU Run entry and current processes exist, but its
`StartupApproved` bytes are all zero; that undocumented value is a hypothesis,
not a diagnosed cause, and no registry/startup setting was changed.

Actual Chrome (existing Chinese/dark profile) followed Workbench → Data
Center → registered strategy explanation → guided research entry → saved
historical result → two-study comparison → restored stopped historical paper
account. The Data Center distinguished historical coverage through
2025-12-31, synthetic 2030 demo and unapproved raw-update candidates. The
wizard restored its existing local draft with the exact
`123456.789000000000001` cash string; no new job was submitted. The saved
293-session result showed +4.67% return, -2.48% drawdown, CNY96.05 costs,
-8.83% CSI300 and a dated 2011-03-22 preview explicitly not executable.
Comparison warned that the two historical periods differ. The restored paper
account displayed a stopped 2011-03-23 session, six fills and a truthful
"older account has no account-specific saved plan" message. This is an agent
read-only recheck of a **partial** path: it neither repairs the absent ledgers
nor proves a newly generated account plan, novice usability, restart safety,
independent disaster recovery or real forward-market acceptance. M4 and M5
remain incomplete; PR #32 stays unmerged.

## 2026-09-24 20:22 UTC bounded responsive matrix

The local Codex in-app Chromium rendered ten known primary routes at 390×844,
720×450, 1024×768, 1280×800 and 1440×900 in each of EN/system-dark,
EN/light, ZH/light and ZH/dark: 200 route/size/language/theme observations.
Every page had an `h1` and document `scrollWidth == clientWidth`; browser
warning/error log was empty. A saved 293-session historical result and the
Chinese/dark Workbench and Chinese/light wizard were visually inspected at
390×844. The result kept +4.67% return, −2.48% drawdown and its dated,
non-executable historical preview. The original EN/system/default viewport
was restored. This proves only the measured layout, not native 200% zoom,
actual Chrome behavior, complete contrast/keyboard/screen-reader accessibility,
or a new user completing the flow. `QA-VISUAL` remains IN_PROGRESS; no study,
paper account, formal research, market receipt or frozen asset was changed.

## 2026-09-24 21:18 UTC bounded Chrome table-scroll repair

Actual Chrome rendered ten primary routes at 390×844, 1024×768, 1280×800,
and 1440×900 in Chinese/dark, plus 390×844 and 1440×900 in English/light,
1024×768 and 1280×800 in English/dark, and 390×844 and 1440×900 in
Chinese/light: 100 route/size/locale/theme observations with no document-level
horizontal overflow. Four representative states were visually inspected.
At 1024×768 English/dark, the paper-account table overflowed locally
(984px content in a 759px container) but had no visible scroll cue. The
existing shared cue is now visible at desktop widths, and legacy paper and
backtest tables have localized, focusable scroll regions. Chrome showed the
cue on paper, backtest and formal archive tables in both locales; focusing
the paper region and pressing ArrowRight changed its scrollLeft. The 390px
Chinese/dark paper page retained no document-level overflow. Browser
presentation was restored to Chinese/dark and the default viewport.
Frontend 228 tests, ESLint, TypeScript, production build, changed-file
Prettier and diff check passed. Read-only database counts remained one formal
dataset/three runs/310 trades, eight product jobs, five paper sessions and
417 events. This is a bounded keyboard/layout improvement, not native 200%
zoom, screen-reader/WCAG certification, novice-user, missing-ledger recovery,
independent backup, lawful forward-source or v1.2 release acceptance.
`QA-VISUAL` and `QA-A11Y` remain IN_PROGRESS; `M4-DATA-INTEGRITY` and
`M5-DELIVERY` remain FAIL.

## 2026-09-24 21:26 UTC formal-archive status accessibility

Actual Chrome's Chinese accessibility tree exposed `PASSED` and `SUCCEEDED`
as the names of formal-archive status cells even though their visible child
text was translated. The raw `title` attributes on two list cells and the
dataset-detail status caused this mismatch. Removing those three redundant
titles retains the translated visible statuses and leaves the original codes
in the formal API/manifest evidence. Chrome's archive tree now contains
`审计通过 · 已冻结` and `已成功` as child text without the raw status names;
dataset detail reads `审计通过 · 已冻结` in Chinese and `Audit passed · Frozen`
in English. The original Chinese/dark preference was restored. Existing
direct-route regression, all 228 frontend tests, ESLint, TypeScript/build and
changed-file Prettier passed. This is one bounded U8/QA-A11Y fix, not a full
screen-reader study or completion of the bilingual/accessibility matrix.

## 2026-09-24 22:07 UTC historical-paper handoff keyboard order

Actual Chrome opened the saved 293-session historical result's independent
paper-account setup. Before the fix, Tab after the source-switch link focused
the immutable archive ID, then other read-only fields. Those three display-only
inputs now remain readable but are omitted from sequential keyboard focus.
Chrome recheck: Tab from the source-switch link reaches editable initial cash;
the next Tab reaches the historical start-date control. No account, order or
study was created. The same inert-symbol Tab stop was removed from the
retained legacy backtest form, while the comparison share URL remains
keyboard-focusable so users can select and copy it. Actual Chrome confirmed
Tab from legacy Cancel reaches initial cash without visiting the immutable
AAPL field. Final combined frontend 233/233, ESLint, TypeScript, production
build and changed-file Prettier passed. This closes only wasted form Tab stops;
`QA-A11Y` and full U7 acceptance remain IN_PROGRESS/FAIL respectively.
PR #32 code head `5002eea` passed [CI36065880987](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36065880987)
backend/frontend/Compose; the PR remains draft and unmerged.

## 2026-09-24 22:38 UTC risk decision wording

Actual Chrome on retained historical paper account `d7044a3c` showed that a
risk-approved proposal may end as either a filled or cancelled order. The
decision column previously displayed raw `APPROVED` in English. Paper and
backtest decisions now read `Risk check passed` / `风控检查通过`, distinct from the
order-execution status; English rejection reads `Rejected by risk controls`.
Chrome verified both locales on the saved account and restored Chinese/dark.
Focused paper/backtest tests passed 32/32; full frontend 235/235, ESLint,
TypeScript, production build and changed-file Prettier passed. This changes presentation only,
not a risk decision, order or ledger. Full U8 accessibility/translation and
M4/U7/M5 gates remain open. The user could not confirm an independent backup
location, genuine pre-loss ledger backup, or lawful 2026 forward-data rights;
none is treated as accepted.

## 2026-09-24 22:47 UTC research-detail disclosure names

Actual Chrome on saved 293-session result `d9f27183` exposed multiple
indistinguishable `技术详情` controls in the execution-reason table and risk
decision table. Each repeated disclosure now has a distinct accessible name:
the execution reason code, or the security identifier plus decision sequence.
The visible label stays short. Chrome's Chinese and English accessibility trees
distinguished the controls, and the original Chinese/dark preference was
restored. Focused collection/detail tests passed 39/39; full frontend 236/236,
ESLint, TypeScript, production build and changed-file Prettier passed. This is a bounded
agent-operated accessibility repair, not a screen-reader user study or a full
WCAG 2.2 AA pass. Chrome browser-control zoom shortcuts did not visibly alter
the viewport, so no new native-200% result is claimed. Separate U3 isolation
review cannot prove every pre-loss formal DB row matches its original state;
M4 data integrity and independent backup remain unaccepted.

## 2026-09-24 22:58 UTC release frontend and bounded guide walkthrough

Independent read-only review found that the release Compose overlay selected
the Nginx frontend image but inherited the development `npm ci && npm run dev`
command. The merged release configuration therefore could not start its
frontend. The overlay now resets the command to the image default; CI asserts
the merged frontend command is null. Local release-image build passed, and an
isolated Nginx container served HTTP 200 on 127.0.0.1:15173 with the expected
security headers. That disposable container was stopped; the main Compose
stack, database and volumes were not changed. This is a release-config smoke
check, not a complete release rehearsal or M5 PASS.

Actual Chrome cross-checked the draft Chinese/English operator guides against
the home/data/paper mode labels, a saved historical result, and its separate
paper-account handoff. The historical source was locked, the 293-session
study left the 93-day-limited replay start blank, and capital, universe,
strategy, cost and risk settings were visible for review. No study, account,
order, provider request or market receipt was created. This is an agent
walkthrough of key guide paths, not an independent novice-user review or a
complete bilingual demo. The user still cannot confirm an independent backup
destination, genuine pre-loss ledgers, or licensed 2026 forward data; none is
accepted. `M4-DATA-INTEGRITY`, `U7-FORWARD` and `M5-DELIVERY` remain FAIL.

## 2026-09-24 23:07 UTC help language-switch context

Actual Chrome on `/help` showed all four English explanations and the four
distinct data-mode descriptions. Switching the locale after expanding a help
answer collapsed it: the translated question was being used as the React key.
The fixed four-question list now uses stable identifiers. A regression test
checks that the open answer stays open when its label changes from English to
Chinese. Chrome confirmed the expanded answer remained visible across
Chinese → English → Chinese, and the original Chinese/dark preference was
restored. Full frontend 237/237, ESLint, TypeScript, production build and
changed-file Prettier passed. No research, account, order or data was changed.
This closes only this U8 reading-context defect, not the full bilingual,
screen-reader, performance or novice-user acceptance; M4/M5 remain open.

## 2026-09-24 23:15 UTC isolated release frontend runtime gate

The release CI now builds the actual Compose-selected frontend image, runs that
image without starting backend/PostgreSQL/Redis, and checks HTTP 200 for `/`
and the `/help` deep link. The merged Compose command-null assertion remains.
Local rehearsal built the isolated image; both routes returned HTTP 200 with
Nginx and the expected headers. Actual Chrome on the isolated 15173 origin
rendered the Chinese help page and expanded a help answer, proving the bundle
ran beyond a bare HTTP response. Its top bar correctly showed service
unavailable: the running backend only accepts the normal 5173 origin, so this
does **not** prove end-to-end release API operation. The disposable frontend
containers were stopped without touching the main four services or DB.

One local `docker compose run --no-deps` experiment unexpectedly pre-created
three `qtp-release-smoke_*` named volumes although no database service ran.
They were left intact under the no-volume-deletion policy. CI uses `docker run`
for the image smoke instead, avoiding that side effect. Windows currently
shows Docker AutoStart enabled and a quoted HKCU Run path, but no subsequent
real login has tested it. `QA-RELEASE` and `M5-DELIVERY` remain FAIL.
