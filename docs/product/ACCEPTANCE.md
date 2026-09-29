# v1.2 acceptance ledger

## 2026-09-29 13:29 UTC exact-head Chrome receipt recovery and local runtime

At `b328ae8`, a separate tmpfs Compose stack and real Chrome tested the
paper-create ambiguity: the first backend 201 was deliberately lost; retrying
the saved identical-key request received a test-injected 422; the new read-only
receipt endpoint returned 200 for the original committed account. The proxy
recorded identical request/key hashes, and scratch session list stayed at
`total=1`, `CREATED`. After removing the HTTP-only fault proxy and switching
only the scratch frontend to direct scratch API access, Chrome showed the
same account `已连接 已创建`, and the creation page retained its confirmed link.
No replay was started. The detailed harness, IDs and SHA-256 values are outside
Git in `product-evidence/v1.2/m5/20260929-paper-receipt-422-browser.md`.

The original backend process had predated the new route. All original jobs
were terminal, no pending product receipt journal was present, and the DB was
already at Alembic head, so a backend-only Compose restart loaded current
bind-mounted code. Original PostgreSQL/Redis/backend are healthy, Redis PONG;
frontend and API health are HTTP 200; live OpenAPI now exposes the receipt
route. Original paper sessions/events remain `5/417`, research jobs `8`,
market jobs `4`. This makes the local app usable while GitHub account CI is
held, but not release-ready. No original account/data or frozen/OOS asset was
used for scratch QA; no push, hosted CI, merge, tag or release occurred.
October 1 remains an unverified restoration estimate. Lawful new-market
forward receipt, genuine missing-ledger restore, independent physical backup,
valid cold matched p95, native screen-reader/200% zoom, CSV landing and
independent novice QA remain open. This is one same-profile fault path, not a
full U7/M4/M5 or arbitrary-race proof.

## 2026-09-29 13:13 UTC local committed-receipt recovery — bounded U7 check

When an earlier paper-create response is uncertain, a later identical-key
POST can fail request validation before the server's idempotency lookup.
The new read-only `GET /api/paper-trading/sessions/receipt` checks only for a
committed account under that exact key, returns it with `Cache-Control:
no-store`, and is called after a prior-attempt POST receives 400/404/422.
The browser confirms that receipt and opens the existing account if found;
otherwise it retains the original key and blocks a different new account.
Neither a 404 nor a timeout means the original POST can no longer commit.
No schema migration, deletion or cancellation was added.

Against an isolated tmpfs `quant_test` PostgreSQL, the full backend suite
passed 1029 tests with one optional unmounted-archive skip. The final full
frontend suite passed 461 tests across 38 files, including recovery after
400/404/422 and retaining an uncertain key when receipt lookup returns 404.
Ruff, format, mypy, ESLint, TypeScript, Prettier and production frontend build
passed. Independent read-only review found no remaining actionable defect
after the 404 source-outage edge was added. This remains local code/test evidence, not an
actual-browser proof of the new endpoint or hosted CI. The earlier actual-
Chrome lost-201 proof is in the following entry. The original Compose services
and financial database remained untouched; no GitHub action occurred.

## 2026-09-29 13:02 UTC browser lost-201 recovery — bounded local U7 check

In a separate tmpfs `qtp-v12-paper-loss-qa` Compose project at code head
`504b95a`, real Chrome created a synthetic 2030 demo account through a
loopback one-shot proxy. The backend committed HTTP 201, but the proxy closed
the first browser response. After a reload, the page retained the uncertain
saved request; its same-key retry returned the same account ID
`7eaea074-9cdf-43c9-aff9-9c1c8b5a3da3`. The proxy recorded identical key
and body hashes for both POSTs; scratch session list reported `total=1` and
`CREATED`. The form subsequently showed a saved confirmed receipt. After the
test-only frontend was rebuilt on the same origin to use the scratch backend
directly, Chrome opened that account detail and showed `已连接 已创建` with no
console errors. The intermediate detail error was caused by the deliberately
HTTP-only fault proxy not tunnelling WebSocket. No replay was started.

Harness, checksums and exact observations are outside Git at
`product-evidence/v1.2/m5/20260929-paper-create-lost201-browser.md`.
This proves one same-profile browser fault path, not every timing race,
cross-profile/device exactly-once, full U7/M4/M5, or release readiness.
Original database/accounts, frozen research/OOS and GitHub were unchanged.
Hosted exact-head CI remains unavailable; October 1 restoration is an
unverified estimate. Lawful forward-market receipt, genuine lost-ledger
recovery, independent physical backup, valid cold matched p95, native
screen-reader/200% zoom, CSV landing and independent novice QA remain open.

## 2026-09-29 12:46 UTC two-tab paper creation — bounded local U7 check

The paper-create page now holds one same-origin browser Web Lock from reading
saved intents through POST and receipt persistence. A successful response
retains its exact request, key and confirmed session ID, so an ordinary later
submit cannot silently create a new account; a separate explicit button is
required. If the first result was uncertain, a later 400/422 retry does not
erase the original reconciliation key. An independent read-only review found
this last bug before the patch, and two new regressions cover both form and
saved-request retries. Storage failure or unavailable Web Locks stops a fresh
POST rather than choosing an unsafe key.

The isolated `qtp-local-paper-0929` tmpfs test project passed 1027 backend
tests with one optional unmounted-archive skip and 456 frontend tests across
38 files. Ruff, format, mypy, ESLint and TypeScript passed. A separate
`qtp-v12-paper-lock-qa` current-source production build used its own tmpfs
`quant_test` PostgreSQL, Redis and product data, with read-only research/data
mounts; Alembic was applied only to that scratch database. Its API and
frontend were healthy at `localhost:18014` and `localhost:15175`. In real
Chrome, two tabs at that same origin were open before a synthetic 2030 demo
account was created. The second tab received the saved confirmed receipt and
“Open saved paper account” link without reload; its ordinary Create action
stayed on the form with duplicate-prevention guidance. Scratch read-only
`GET /api/paper-trading/sessions` returned `total: 1`, the same account ID
shown in the first tab. No replay was started. The original Compose stack,
database and accounts were not modified.

This proves only one local Chrome two-tab success path plus mocked-lock
concurrency/fault regressions, not every browser interleaving, cross-profile
or cross-device exactly-once behavior, an actual-browser lost-201 fault, full
U7/M4/M5 or release readiness. The scratch stack is disposable and remains
separate from the original app. GitHub exact-head CI, lawful after-start
forward-market receipt, genuine pre-incident lost-ledger recovery,
independent physical backup, valid cold matched interaction p95, native
screen-reader/200% zoom, CSV landing and independent novice QA remain open.
October 1 is only an unverified estimate of GitHub account restoration; no
push, hosted CI retry/poll, merge, tag or release occurred.

## 2026-09-29 12:22 UTC local paper-create recovery during GitHub CI hold

The original WSL Compose PostgreSQL, Redis and backend were healthy, the
frontend was up, and `/` plus `/api/health` returned HTTP 200. These running
containers predate the working-tree change. An isolated `qtp-local-paper-0929`
Compose test project used its own tmpfs `quant_test` PostgreSQL and did not
touch the original database. Its full backend suite passed 1027/1028 with one
optional unmounted-archive skip; the frontend passed 449/449. Ruff, mypy,
ESLint, TypeScript, changed-file Prettier and the production frontend build
passed locally. None of these results sets a GitHub CI status.

Paper creation now saves the exact request and idempotency key before POST,
allows an explicit same-key retry after a lost response or reload, blocks a
different request while the earlier outcome is uncertain, and exposes saved
recovery even if its originating experiment stops loading. A definite
400/401/403/404/422 rejection removes the rejected intent so the form can be
corrected. The backend looks up an already accepted matching key before
checking mutable dataset/strategy availability, so a replay survives a later
source outage. Focused page tests passed 65/65, including a changed default
form after reload, oversized storage and a definite 422 correction. The
saved-retry panel is visible on the same page after an uncertain response.

This is a bounded single-tab/browser-profile recovery improvement, **not**
cross-tab exactly-once, full U7 or release acceptance. `localStorage`
read/choose/write is not atomic across tabs, and removing a confirmed intent
can strand another tab whose response was lost; Web Locks plus retained
confirmed receipts and explicit new-account action are still required before
claiming that stronger guarantee. No actual-browser fault injection for this
new flow was run. The original runtime was not rebuilt, and no original
account, provider, frozen data, Official OOS or GitHub state was changed.
GitHub's October 1 recovery remains an unverified estimate; remote exact-head
CI, lawful current-market forward receipt, genuine lost-ledger recovery,
independent physical backup, novice QA and release gates remain open.

## 2026-09-29 local operation during GitHub Actions hold — bounded U7 correction

WSL2 and Docker remained available without hosted CI. The original Compose
PostgreSQL, Redis and backend were healthy, the frontend was up, and both
`http://localhost:5173/` and `/api/health` returned HTTP 200 from Windows.
This proves local reachability, not v1.2 release readiness; GitHub's October 1
recovery is the user's estimate, not a verified service date.

Two creation pages allowed a late successful POST to redirect after the user
had selected Cancel. New isolated tests first failed for paper-account and
legacy-backtest creation. Both now follow the existing research-wizard pattern:
only the still-mounted page at its submission URL may navigate on completion.
The tests cover an unmounted paper form and a still-mounted legacy form after
Cancel changed the URL. Focused tests passed 86/86; `make test` passed in the
separate tmpfs test Compose project (frontend 441/441), and `make lint` and
`make build` passed. An independent read-only review found no source defect.
No original database, running account, provider, frozen study, OOS or GitHub
state was changed. The running original frontend was not rebuilt with this
working-tree fix, and no actual-browser delayed-POST proof was claimed.

This is a bounded route-consistency fix, not full U7/M4/M5 acceptance. A
separate audit found that paper-create idempotency is only component-memory
durable: a lost 201 followed by refresh may generate a new key and a second
account. That requires its own exact-request recovery correction. Lawful
new-market forward receipt, genuine lost-ledger recovery, independent physical
backup, novice acceptance and exact-head hosted CI remain open. No push,
merge or release occurred.

## 2026-09-29 configuration restore at the 20-row boundary — bounded U2/U3/M4 correction

When the oldest saved configuration was restored from a full 20-row page,
the required pre-restore backup became row 1 and moved the original Restore
trigger to page 2. Closing the confirmation dialog tried to focus that now
disconnected button, leaving keyboard focus on `body`. The new regression
reproduced this failure (7 pass, 1 fail). The shared dialog now returns focus
to its connected trigger as before; only when the trigger has disappeared
and focus has fallen to `body` does it focus the persistent main workspace.
The focused suite passed 8/8, the full frontend passed 439/439, and `make
lint`, changed-file Prettier and `make build` passed. A read-only review found
no blocking regression in the six dialog callers.

Actual Chrome 153 on DESKTOP-3EOROGR loaded current-source Vite at temporary
`localhost:15175/research/new`. Through the UI on that isolated origin, it
saved 20 versions, opened the oldest with Return, and confirmed restoration
with Return. The page then showed 21 versions and the step-1 restore notice;
the old button was absent from page 1, focus was on `main-content`, and the
old version remained on page 2. A GET-only proxy on `:18014` forwarded reads
to the isolated scratch backend `:18012`, so this browser exercise made no
backend write. The screenshot was visually inspected but not saved as M5
media. The temporary tab, proxy and dev container were stopped; the original
four Compose services stayed healthy. Exact harness and proxy checksum are
outside Git in `product-evidence/v1.2/m4/20260929-config-restore-focus/README.md`.

This is one configuration keyboard-fallback case, not native screen-reader
speech, 200% zoom, full U2/U3/M4/M5, independent novice acceptance, lawful
new-market forward data, genuine lost-ledger recovery, independent backup or
hosted exact-head CI. The 21 browser-only QA versions remain under the
inactive temporary `localhost:15175` origin; no original account, database,
frozen research, OOS or GitHub state was changed.

## 2026-09-29 global search keyboard Retry — bounded U8/M4 correction

The global command search lost keyboard focus when a failed studies read was
retried successfully: the focused Retry button disappeared and focus fell to
the document body. The existing regression failed before the change. Retry
now focuses the persistent search field before reloading, preserving the
query; the focused test passed 7/7 and the full frontend passed 438/438.
`make lint`, changed-file Prettier and `make build` passed.

Actual Chrome loaded a current-source production preview through a GET-only
proxy to the isolated scratch backend. The proxy returned one studies search
HTTP 503 for `q=FocusProbe`, then HTTP 200 on Retry. The browser exposed
the Chinese error, keyboard Tab focused Retry, Return cleared the error with
the unchanged query and search field focused, and Escape restored focus to
the topbar Search trigger. The recovery screenshot was visually inspected
but not saved as M5 media. Proxy checksum, exact endpoints and cleanup are
outside Git in `product-evidence/v1.2/m4/20260929-command-palette-retry-focus/README.md`.
The preview/proxy/tabs were stopped; original Compose services stayed up.

The same Chrome session did **not** establish native 200% zoom: two browser
zoom shortcut forms left the measured zoom/viewport unchanged. Neither the
automatic CSV action nor its prepared fallback link yielded a captured
download event, so file landing remains unverified, not an established app
defect. Native screen-reader speech, full U8/M4/M5, independent novice,
lawful forward data, genuine lost-ledger recovery, independent backup and
hosted exact-head CI remain open. No push, merge or release occurred.

## 2026-09-29 local market readout live-region and update focus check

On the working tree based on `4fdcd26`, the market detail announced its full
OHLCV/factor fact sheet whenever a selected chart point changed. A regression
failed against that broad `role=status`. The live region now contains only the
selected date and observation status; exact price/factor values remain visible
and available in the ordinary definition list. Actual Chrome opened the saved
historical 600000 detail, changed the date from 2011-06-30 to 2011-06-29,
and exposed `2011-06-29 · 完整 OHLCV 记录` as the status while the precise
2011-06-29 close remained `9.7600` outside it. The accessibility tree and DOM
agreed; a visually inspected screenshot and SHA-256 are outside Git in
`product-evidence/v1.2/m4/20260929-4fdcd26-market-live-status/README.md`.

The first complete frontend run also had one read-error focus failure in the
market-update detail (437 passed, one failed), while its focused file passed.
The parent schedules a later focus request; the disappearing-command handoff
now runs during layout rather than a passive effect. Its existing regression,
the combined targeted files (62/62), and two subsequent complete frontend
runs (438/438 each) passed. A final local `make test` also passed 1025 backend
tests (one optional unmounted-archive skip) and 438 frontend tests in the
separate test Compose project. This is a bounded likely timing-race correction,
not proof of every browser interleaving. `make lint`, changed-file Prettier,
`make build` and `git diff --check` passed. Original Compose data and services
were not changed; no push, merge or release occurred. Native screen-reader
speech, 200% zoom, independent novice, full M4/M5, lawful after-start forward
data, original lost-ledger recovery, independent backup and exact-head GitHub
CI remain open. The user's October 1 recovery date is an estimate.

## 2026-09-29 actual browser U4 export recovery and current-source Workbench media

The isolated production preview of current frontend source displayed an
already-saved historical result. In the in-app browser, keyboard CSV export
returned HTTP 200 and prepared a named fallback; a GET-only local proxy then
injected one exact export HTTP 503. The error was visible but the fallback
kept the same blob URL, filename, route and button focus. A third browser
retry returned HTTP 200, cleared the error and replaced the blob URL while
retaining route and focus. The proxy recorded export 200/503/200. Screenshots
of the failure and recovery were visually checked and saved outside Git with
SHA-256s in `product-evidence/v1.2/m4/20260929-export-retry-browser.md`.
The browser did not prove that an automatic file landed in Downloads; old
blob revocation on replacement is covered by the focused component test,
not this browser observation. The preview/proxy/tab were stopped; original
Compose services remained up and frontend/API health returned HTTP 200.

At local checkout `7965170`, the running bind-mounted frontend also produced
real in-app-browser full-page Workbench captures in EN/system-dark with a
requested 1440×900 CSS viewport and ZH/light with a requested 390×844 CSS
viewport. The mobile document had no page-wide overflow (scroll width =
client width 375). The saved PNGs are 1425×1337 and 375×1912 respectively,
because the capture surface reserves browser chrome/scrollbar space; cropped
diagnostics were rejected. Hashes and limits are in outside-Git
`product-evidence/v1.2/m5/20260929-7965170-iab/README.md`. These are two
bounded exact-source images, not the complete before/after six-route media,
native Chrome/zoom/speech, valid cold p95, independent novice, full U4/M4/M5,
hosted CI or release. EN/Follow system and the default viewport were restored.

## 2026-09-29 local Workbench retry browser proof — M4 remains open

`b963abf` keeps keyboard focus on the persistent Workbench heading when an
error Retry button disappears during capability or recent-study loading, but
does not move focus if the user already left the error. A red/green component
regression covers capability retry success and repeat failure; independent
read-only review found no obvious regression and noted the recent-study branch
is not separately tested. In an isolated production preview with a GET-only
proxy, the in-app browser saw a real displayed 503 error, keyboard Retry to
success with heading focus, and 503-to-503-to-success with heading focus.
The earlier development-server attempt was rejected because StrictMode masked
the injected failure. The proxy, owned preview container and QA tab were
stopped after validation; the original four Compose services stayed up.

Actual in-app browser Workbench and Help tabs also synchronized Chinese and
English without reload; English was restored. At committed `b963abf`, full
frontend tests passed 424/424, `make lint` and `make build` passed. The last
backend run passed 1025 tests with one optional unmounted-archive skip before
this frontend-only change. Details and the GET-only proxy checksum are in
outside-Git `product-evidence/v1.2/m4/20260929-workbench-retry-browser.md`.
No screenshot was saved as exact-head M5 media. Native screen-reader/zoom,
OS reduced motion, independent novice, lawful forward data, lost-ledger
recovery, independent backup and hosted CI remain open; no release gate is
promoted by this bounded check.

## 2026-09-29 local operation while GitHub Actions is unavailable

GitHub Actions is not needed to run the platform on this PC. From the WSL
repository, the existing four-service Compose application was up: PostgreSQL,
Redis and backend reported healthy, and the frontend and `/api/health` each
returned HTTP 200. A URL-confirmed in-app browser opened the local Workbench
and a saved historical research result by GET; the result showed its metrics,
historical date and non-advice warnings. This is actual local browser access,
not native Windows Chrome accessibility or full M5 evidence.

Two red/green corrections were committed locally. `9874e09` synchronizes
language across open tabs through the existing i18n setup. `126f811` labels
an older historical paper portfolio with its last verified trading date when
the latest accepted session has no new valuation; it handles REST hydration
and WebSocket updates without changing immutable paper events. On committed
`126f811`, `make test` passed 1025 backend tests with one optional
unmounted-archive skip and 422 frontend tests. `make lint` and `make build`
passed. Tests used the separate `quant-mvp-tests` PostgreSQL project, and the
original four services remained running afterward. No original account,
database, provider, frozen research, push, merge or release was changed.

These are local gates only. The user's October 1 GitHub Actions recovery is an
estimate, not a verified account state. Exact pushed-head hosted CI, native
zoom/screen-reader and independent novice QA, current lawful A-share forward
data, genuine lost-ledger recovery and independent physical backup remain
open. The platform can be used locally, but these checks do not authorize a
v1.2 merge, tag or release.

## 2026-09-29 local U3/U4 recovery defects — M4 remains open

Two red regressions exposed independent failures. A historical freeze marker
containing valid JSON `null` crashed the capabilities registry, blocking even
the independent synthetic-demo entry. The registry now treats a non-object
marker as `DATASET_INTEGRITY_FAILED`: historical data is unavailable, while
demo capabilities remain available and historical resolution still fails
closed (`c487042`). A failed replacement CSV download previously revoked the
already prepared report URL. The existing fallback now survives that failure
and is revoked only after successful replacement or unmount (`e5329d0`). The
result route keys its detail by job ID, so navigation unmounts the old link.

Both regressions failed before the fixes and passed afterward. An independent
read-only diff review found no concrete blocker. On committed code, local
`make test` passed 1025 backend tests with one optional unmounted-archive skip
and 418 frontend tests. `make lint`, changed-file Prettier, `make build` and
`git diff --check` passed. Tests used the separate disposable `quant_test`
PostgreSQL; original PostgreSQL, Redis, backend and frontend stayed running,
with frontend and `/api/health` HTTP 200. Before a targeted backend restart,
the original API showed no active research, paper, market-update or backtest
task. Only the backend was restarted to load the committed code; it returned
healthy, capabilities HTTP 200 with both mounted historical and independent
demo available, and all four task-status distributions were unchanged. The
corrupt-marker case was tested only against an isolated temporary fixture,
not by altering the original archive. No original account/database, frozen
research, provider or GitHub state was written.

Browser interaction with the failed-download/recovery state and native
accessibility remain unverified: the Windows browser helper stopped before
input on URL-confidence policy, and that method was not retried or bypassed.
This local check is not hosted CI, full U3/U4/M4/M5 acceptance or v1.2 release.

## 2026-09-29 delivery provenance correction — M5 remains open

The outside-Git delivery index now identifies clean local `fe0712b`, 100
commits ahead of its cached remote. The accepted five PNGs and 26.12-second
WebM were captured at earlier frontend code `ffaa023`, before the service
status accessibility fix; they are not exact-HEAD media. Their six SHA-256
values match the saved manifest, and all 60 local file links in the index
resolve. HTTP and WSL UNC links were not browser-click verified. The original
four Compose services stayed up; the frontend and `/api/health` returned 200.

Windows Computer Use twice stopped before input because it could not
confidently identify the Chrome URL. No zoom or native screen-reader claim is
made and no alternate automation was used to bypass that safety stop. The
index still marks full account-lifecycle recording, exact-HEAD six-route
media, independent novice, real login startup, backup/lost-ledger, lawful
forward receipt and hosted CI/release gates incomplete.

## 2026-09-29 GitHub-independent local operation and service-status accessibility

The original four Compose services remained up; PostgreSQL, Redis and backend
reported healthy, and the frontend and `/api/health` each returned HTTP 200.
On the working tree based on `91e4cfb`, Chrome 153's pre-fix accessibility
tree exposed the refresh button but suppressed its nested service `status`.
The status is now a sibling live region and describes the refresh button.
A focused regression was red before the fix and green after it. Exact-source
local `make test` passed 1024 backend tests (one optional historical-archive
skip) and 417 frontend tests; `make lint` and `make build` passed.
The existing Vite frontend serves the bind-mounted changed AppShell source;
its fetched module contains `service-health-status` without a container restart.

This permits local use and development during the GitHub Actions hold, but
does not establish a pushed-head hosted CI result or v1.2 release approval.
The post-fix native Chrome accessibility tree and screen-reader speech remain
unverified because the Windows browser helper could not safely establish its
current URL and stopped. No original database, frozen research, paper account,
provider, push, merge or release was changed.

## 2026-09-29 local continuation during GitHub Actions hold — bounded M4 correction

The shared paper-ledger table now exposes its first body cell as a semantic
row header in all five positions, signals, risk-decision, order and fill tables.
The existing bilingual populated-ledger test failed before the change and
passed afterward. In the isolated production-image Chrome account, all five
Chinese tables exposed row headers (7/62/62/62/19 on the persisted historical
account); the page was visually inspected. This is not native screen-reader
speech or the full accessibility matrix.

On the working tree based on `5f0cd15`, local `make test` passed backend
1024 tests with one optional unmounted-archive skip and frontend 413/413.
`make lint`, changed-file Prettier, the frontend TypeScript/production build,
three Compose configuration checks, and Alembic upgrade/downgrade-to-baseline/
re-upgrade/check on a separate tmpfs `quant_test` PostgreSQL all passed.
Both original and isolated frontend URLs and `/api/health` returned HTTP 200;
the original four Compose services remained running. The local scratch
database was stopped without deleting volumes or touching the original data.

These checks let development and historical/synthetic local QA continue while
GitHub Actions is unavailable. They do **not** create a pushed-head hosted CI
result, approve PR #32, justify merge or release, establish lawful 2026
forward-market data, restore the genuine missing paper ledgers, or complete
M4/M5. The user's October 1 recovery date is an estimate, not a verified
GitHub account state. No push, merge, release, Official OOS rerun or original
database/frozen research write occurred.

## 2026-09-29 current-head isolated production-browser rehearsal — bounded M5 integration

At `cb9367c` a separate Compose project built current production backend and
frontend images, migrated only a tmpfs `quant_test` PostgreSQL, and ran with
tmpfs Redis/product state plus read-only accepted historical archive mounts.
All four scratch services were running, PostgreSQL/Redis/backend healthy, and
scratch frontend and `/api/health` returned HTTP 200. The original four
services stayed up and the original frontend and `/api/health` still returned
HTTP 200 after the walkthrough.

Actual Chrome completed the Chinese Workbench → guided 2011 historical study
→ saved result, then switched the result to English. It created a **separate**
2011-04-01–2011-06-30 paper account only after explicitly shortening the
replay range to the 93-day cap. That account reached 2011-06-30, stopped
normally, and exposed its historical plan, risk decisions, orders, cancelled
orders and fills in both languages. A second same-period study with a
different initial capital completed; the comparison page marked that
difference and warned the results were **not a controlled comparison**.
Detailed IDs, observed values and isolation limits are outside Git in
`product-evidence/v1.2/m5/20260929-cb9367c-current-head-integrated-browser.md`.
At 390×844 CSS pixels, actual Chrome showed no page-wide horizontal overflow
on the Chinese comparison or stopped paper-account pages. The English dark
comparison at 1024×768 and English dark stopped paper-account page at
1280×800 also had no page-wide overflow; each viewport was visually inspected.
Language, theme and viewport were then reset. This is not the full
viewport/theme/locale or native 200% zoom matrix.
Seven screenshots were visually inspected in the browser tool but **no
screenshot or recording was saved** in this slice.

This is a bounded local current-head integration check, not full M5 media or
delivery acceptance. Independent novice, native accessibility/zoom,
performance matrix, next genuine login/startup, lost-ledger/independent-backup
resolution, lawful new-market forward receipt and exact-head GitHub CI remain
open. No original database, frozen research/OOS, provider, push, merge or
release was changed.

## 2026-09-29 observation pagination focus — bounded M4 correction

Progress refetches cleared the Data Center observation response and unmounted
its focused pager. A red component regression reproduced that defect. The
pager remains mounted and reports loading. An actual-Chrome check then found
the focused last-page pager jumped behind the sticky topbar when 50 rows
collapsed to one. Shared pagination now keeps a user-activated pager visible
through layout changes, using the measured topbar clearance. A subsequent
manual scroll away cancels that intent, so later polling does not pull the
user back. Independent read-only diff review found no concrete regression.

Focused tests passed 48/48. Exact-code `make test` passed backend 1024 with one
optional unmounted-archive skip and frontend 413/413; `make lint` and
`make build` passed. Installed Chrome 153 confirmed focus-visible,
unobscured pager behavior at 1440 and 400 CSS-pixel widths with keyboard
Enter; 1100 width checked the wrapped topbar. The backend saw GETs only.
Script, geometry, manually-scrolled-away check and three visually inspected
screenshot hashes are outside Git in
`product-evidence/v1.2/m4/20260929-observation-pager-focus.md`.

This browser-injected 51-row QA fixture is not actual provider data. Native
200% zoom, screen reader, physical mobile/soft keyboard, independent novice,
full M4/M5 and GitHub CI/release gates remain open. No original database,
frozen research/OOS, provider, paper account, push or release was changed.

## 2026-09-29 successful task-poll focus — bounded M4 correction

Actual Chrome 153 reproduced a keyboard focus defect in three task lists:
when a successful five-second poll prepended a newer task and displaced the
focused twentieth Open control, focus fell to `BODY`. The test changed only
the browser's GET responses, not backend jobs. Three focused regressions
were red before the fix. Task Center's research/raw lists and Data Center's
history now hand off focus to their persistent named headings on successful
replacement, while the existing failed-GET path still targets its alert and
deliberately moved focus is not stolen. Chrome recheck focused H2/H2/H3,
respectively, with only backend GET requests. Three screenshots were visually
inspected and SHA-256 recorded outside Git in
`product-evidence/v1.2/m4/20260929-task-success-poll-focus.md`.

Focused tests passed 47/47. Exact-code `make test` passed backend 1024 with
one optional unmounted-archive skip and frontend 411/411; `make lint` and
`make build` passed. An independent read-only post-fix review found no
actionable regression. This is not a real concurrent task-creation event,
native screen-reader, mobile/zoom matrix, full M4 or GitHub CI acceptance.
The separate Data observation-pager correction is recorded above.

## 2026-09-29 strategy first-click timing — bounded M4 Chrome study

Installed Chrome 153 opened the strategy drawer in 120/120 first-click trials
over four sets of 30 fresh browser contexts/documents with network cache
disabled. The host click-start-to-rendered-screenshot p95 values were 196.5,
234.4, 203.9 and 205.6 ms. That stopwatch includes automation and screenshot
overhead; three sets exceeded the 200 ms target, so it is neither an app
PASS nor an app FAIL. After independent method review, the final set recorded
native click event and dialog-open timestamps: all 30 dialog openings fell
within the click's recorded rendering window with an 8 ms event-timing
quantization allowance. Native event-duration p95 was 24 ms, and trusted
pointerdown to the second frame callback after opening p95 was 18.5 ms.

The script, method limits and visually checked screenshot checksum are
recorded outside Git in
`product-evidence/v1.2/m4/20260929-strategy-first-click-measure.md`. This
proves only a local headless development-page interaction, not production
visible-pixel latency, native assistive technology, whole-site p95,
independent novice QA, GitHub CI or full `QA-PERF`/M4 acceptance.

## 2026-09-29 task-list polling focus — bounded M4 correction

Task Center research/raw-task lists and Data Center update history unmounted a
focused Open link/button when a five-second polling GET failed. Focus fell to
`body`, leaving keyboard users without a useful recovery point. Two new
regressions reproduced that failure before the fix. Each list now moves focus
to its named, programmatically focusable error alert only when the focused
list item disappears; moving focus elsewhere before the poll does not steal it.
The shared resource hook still clears failed data, so stale task state is not
presented as current. Focused TaskCenter/MarketUpdates tests passed 43/43;
full frontend 407/407.

Actual Chrome 153 then exercised all three lists with browser-only status
overrides to trigger polling and injected 503 responses. In every case, the
Open control disappeared and the visible alert received focus. Only backend
GET requests occurred; no saved job was changed. Three visually checked
viewport screenshots, SHA-256 values and the reproducible script are recorded
outside Git in `product-evidence/v1.2/m4/20260929-task-poll-focus-chrome.md`.
Exact-code `make test` passed backend 1024 with one optional unmounted-archive
skip and frontend 407; `make lint` and `make build` passed. This is not a real
outage, native screen-reader proof, idle-pagination test or full M4 acceptance.

## 2026-09-29 market read-error recovery — bounded Chrome check

Installed Chrome 153 received browser-injected 403 on English market-search
GETs and 408 on Chinese market-search GETs. Both pages displayed the correct
localized next step and historical-source warning. One visible Retry read the
cached search again, removed the alert and restored a 20-row table. All logged
backend API methods were GET; no provider or watchlist mutation occurred. The
two screenshots were visually checked, and the script, request counts and
SHA-256 values are saved outside Git in
`product-evidence/v1.2/m4/20260929-market-read-error-chrome.md`.
This closes a browser-evidence gap for the earlier typed-error repair, not the
full U5/U8/M4 matrix, a real permission/timeout failure, or legal authority
for new-market forward simulation.

## 2026-09-29 result-chart guide — bounded M5 improvement

Both user guides now document the existing result chart's 100-point pages,
benchmark checkbox, selected-date precise available values, linked trades and
holdings, and exact-data table/keyboard route. They state that the controls
change only the display, not full-period metrics, and that missing values are
not zero. Labels and behavior were checked against the current component and
number formatter. This is documentation completeness, not a new browser,
novice, accessibility or full M5 acceptance result.

## 2026-09-29 exact-head local verification during GitHub hold

After commit `7c96ee5`, `make test` exited zero: backend 1024 passed, one
optional read-only historical-archive test skipped because that archive was
not mounted, and frontend 404/404 passed across 38 files. The test Compose
project used a separate tmpfs `quant_test` PostgreSQL and read-only `./data`
mount; no test services remained running afterward. `make lint` passed Ruff
check/format, mypy, ESLint and TypeScript. `make build` passed the Vite
production build (130 modules). The original Compose PostgreSQL, Redis and
backend remained healthy; the frontend and `/api/health` returned HTTP 200.
The worktree was clean after the commit.

These are local developer checks, **not** GitHub-hosted CI or release
acceptance. GitHub recovery remains unverified; no push, merge or release
occurred. Current licensed forward-market data, the two lost paper ledgers,
independent physical backup, native accessibility/performance, genuine novice
acceptance and full U1–U8/M0–M5 remain open. The original database,
accounts, frozen research and Official OOS were not changed.

## 2026-09-29 saved-market read errors — bounded U5/U8 correction

The market catalog, security search, watchlist and saved-price detail used
one generic archive/service warning even when the API returned a typed 403 or
408. A new search regression first failed on an actual `ApiError(403)` with
the old archive warning. All four read surfaces now reuse the existing
bilingual `ProductError` classification while preserving their market-specific
fallback and Retry label. Focused Markets tests passed 21/21, covering the
four surfaces, EN/ZH permission text and no request on locale switch.

The full frontend passed 404/404 tests, ESLint, TypeScript and Vite build.
Actual Chrome reopened the local historical market list and a saved price
detail: 5431 registered securities, the source/date warnings and exact-price
record rendered; closing the dialog returned focus to its trigger. That
browser check was a successful GET path, **not** a browser-injected 403/408.
An independent read-only code review found no concrete blocker in this slice.
No provider request, watchlist change, original database/account/frozen asset
write, GitHub action or release occurred. Full U5/U8/M4 and external gates
remain open.

## 2026-09-29 research read-error focus — bounded U3/M4 correction

When a running research task's polling GET failed, its focused Cancel button
and status both unmounted, leaving keyboard focus on the page body. A focused
regression reproduced this before the fix. The read-error alert is now a
programmatic focus fallback, using the existing status-focus path; the
regression and the full Experiments file passed 46/46. The full frontend
passed 404/404 tests, ESLint, TypeScript and Vite build. This is a component-
level polling-failure check; no real-browser GET fault was injected, and no
study was cancelled or created. Full U3/M4 remains open.

## 2026-09-29 data-update cancel response — bounded U5 correction

The update-task detail shared one error state for GET reads and cancel/retry
actions. If a cancel POST returned 503 **after** a task GET had already
confirmed `cancel_requested` or `CANCELLED`, the late response reintroduced a
misleading alert. Conversely, a definitive cancel 403 disappeared after a
successful status refresh. Red tests reproduced both defects; the
failure-first 503 order was already safe and is retained as a regression.

Read and action errors now have separate state. A shared small classifier
marks only network errors, timeout 408 and server 5xx as uncertain; a
confirmed cancel hides only such an obsolete action warning. Permission 403
and a subsequent Retry 503 remain visible. A denied Cancel POST followed by
a failed GET keeps the denial visible alongside a distinct read error;
the inverse (uncertain Cancel 503, denied GET 403) also keeps both errors.
Identical 403 alerts are deduplicated for assistive technology. The first
two interleavings failed before the fix; the inverse is also covered.
Focused MarketUpdates 36/36 and
Experiments 45/45, full frontend 399/399, ESLint, TypeScript, changed-file
Prettier and Vite build passed. This also tightens the preceding research-
cancel fix so a separate actor's cancellation cannot swallow a definitive
permission denial.

Actual Chrome opened the local data center and an existing completed raw-
candidate update task by GET, displaying its persisted status, observations,
receipts and warning that candidate data cannot be used for forward
acceptance. The temporary tab closed. No browser-injected lost response or
live cancellation was run. This bounded error-path repair does not establish
source/use rights, full U5/U3/M4/M5, independent novice, GitHub CI or release.
No provider acquisition, original database/account/frozen research/OOS write,
push, merge or release occurred.

## 2026-09-29 lost research-cancel response — bounded U3 correction

Two red component regressions reproduced a cancellation accepted by the
server but followed by a lost/503 POST response. Whether the POST failed
before or after an authoritative task GET confirmed `cancel_requested` on a
running job or terminal `CANCELLED`, the old view retained a misleading
request-error alert. The detail view now records which command failed and
hides only the obsolete **cancel** error after authoritative confirmation.
An unconfirmed cancel failure still appears; a subsequent Retry 503 on the
cancelled parent still appears independently. This matches the backend's
durable cancel transaction and does not create another task or touch results.

Focused `Experiments.test.tsx` passed 44/44 after the fix, full frontend
392/392; ESLint, TypeScript, changed-file Prettier and Vite build passed.
Actual Chrome reopened an existing saved historical result by GET with its
stored metrics and no page error, then the temporary tab closed. The browser
did not inject a lost cancel response or cancel a live task. This is a bounded
code/error-path correction, not full U3/M4/M5, independent novice or GitHub
CI/release acceptance. Original studies, accounts, providers, frozen research
and Official OOS were not changed.

## 2026-09-29 current-head Workbench screenshot — bounded media

Installed Chrome 153 headless loaded the local Workbench at the configured
`localhost:5173` origin. The saved PNG is 1440×900, 86,856 bytes, SHA-256
`1211D135D1372591801971AD5E8EC17703E63AC743F35ED5100F1BC0BC6DD87E`.
It was visually inspected after capture: a settled Chinese/light returning-user
home showed the guided-backtest primary action, existing-research secondary
action, online service, historical data cutoff 2025-12-31 with no current-
advice claim, and recent saved studies. HEAD was `a9d2298`, frontend tree
`1a4b7d3d6ea92838da5345a886a9ae4f9d6f3449`. The PNG and bounded capture
record are outside Git in
`product-evidence/v1.2/m5/20260929-a9d2298-workbench-capture.md`.

This supplies a current-code opening-page image, not a fresh-user walkthrough,
interaction recording, two-locale/theme/viewport matrix, native 200% zoom,
screen-reader speech, cold-click p95, independent novice test, complete M4/M5,
GitHub CI or release acceptance. The capture navigated only to the local home
page; no account, study, provider, market-data or GitHub action was initiated.

## 2026-09-29 saved comparison screenshot — bounded current-code media

An installed Chrome 153 headless process loaded the existing two-study
comparison from the configured `localhost:5173` origin, without submitting
anything. The saved 1440×900 PNG shows the online indicator, the two saved
historical studies, the explicit differing-conditions warning, rounded metrics
and the scrollable result table. PNG SHA-256 is
`B1A06A67950B5D288BE0091C76F2695CD77B10185963E72B509BE63B2E9EBECA`;
the frontend tree at capture was `87a710d1827d69877c176aea2c2f2080b2d6ea24`
on `249c327`. The local artifact and rejected capture trials are documented in
`product-evidence/v1.2/m5/20260929-249c327-comparison-capture.md` outside Git.

The first trials used `127.0.0.1`, which mismatched the configured `localhost`
frontend origin and displayed a spurious service error despite HTTP 200 study
GETs. They are not delivery evidence. A requested 390-pixel screenshot did not
verify the effective CSS viewport and is not mobile acceptance. One settled
desktop screenshot is M5 media progress, not an interaction recording,
bilingual/theme matrix, native zoom/speech, independent novice test, full
M4/M5, GitHub CI or release pass. This capture sent no mutation request to
the original database, frozen research or OOS; no before/after fingerprint
was taken.

## 2026-09-29 monthly-return heatmap — bounded accessibility repair

Actual Chrome exposed a saved formal research heatmap's heading but none of
its 48 visible month/value cells: the wrapper's `role="img"` made its child
data presentational. It now uses a named native section, preserving every
month and exact displayed percentage in the accessibility tree. Hover titles
use the same percent units instead of the raw return fraction. The focused
regression failed before each corresponding fix, then passed; final frontend
369/369 tests, ESLint, changed-file Prettier and TypeScript/Vite build passed.
Chrome on the saved validation run confirmed first and last month values in
Chinese and English; the original Chinese/dark preference was restored.

Local evidence: `product-evidence/v1.2/m4/20260929-heatmap-accessibility.md`
(outside Git). This is one repaired M4 accessibility defect, not verified
native screen-reader speech, full WCAG/visual matrix, saved current-head
media, GitHub CI or release acceptance. No study or data was changed.

## 2026-09-29 saved-study comparison — bounded current-head Chrome

On local HEAD `25b0fa4`, actual Chrome opened two saved historical studies in
the comparison view. Chinese/dark and English/light both showed the same
study identities, dataset checksum, differing date windows and explicit
warning that this is **not a controlled comparison**. The full-precision
toggle showed stored values, and reloading the comparison URL restored the
two studies and rounded values. A fresh first mouse click also opened the
strategy detail and focused Close. Chrome's queried warning/error log was
empty. The original Chinese/dark preference was restored; no provider,
research, paper-account or market-data POST was initiated.

The bounded observation is recorded in the local, untracked evidence file
`product-evidence/v1.2/m4/20260929-25b0fa4-comparison-chrome.md`. No
current-head screenshot/recording was saved. One successful strategy click
does not resolve the intermittent cold-click or p95 question; the browser
tool did not expose native Event Timing. This is not full M4/M5, new-market
forward evidence, GitHub CI or release acceptance.

## 2026-09-29 missing data-update task recovery — bounded local Chrome

A valid-looking but absent `/data?updateJob=` deep link returned the correct 404,
yet offered only Refresh and left the invalid selection in the URL. The detail
now explains where to go in Chinese and English and offers an explicit return
to requests and task history. Recovery replaces the invalid URL instead of
pushing it onto browser history, and focuses the stable panel heading after
the detail is removed. It never starts provider acquisition.

One new component regression was red before the change and now passes for
empty history, both languages, keyboard Return, unchanged history length and
heading focus. The current frontend passed 368/368 tests, ESLint, TypeScript,
Prettier and a 129-module production build. The isolated repository test run
passed backend 1024 with one optional archive skip and frontend 368; its
frontend image was built before the later focus refinement, which was covered
by the subsequent current-code frontend run. Actual Chrome opened an absent
task by GET and confirmed the Chinese recovery button clears `updateJob`,
restores form/history, and focuses the panel heading. No task, provider,
paper account, original database or frozen research was changed.

This is bounded local UX evidence, not full U5/U8/M4/M5, native screen-reader
speech, independent novice acceptance, GitHub CI or release approval. The
October 1 GitHub recovery date is a user estimate and remains unverified.

## 2026-09-29 application motion-off setting — bounded actual Chrome

On the existing `/settings` page in actual Chrome, the saved motion preference
started at Follow system with OS `prefers-reduced-motion=false`. The page's
computed entry animation was 0.22s. Selecting the visible Close nonessential
motion option set `data-motion=off` and computed `.productPage` animation to
0s. Restoring Follow system returned the value and 0.22s animation. This
proves the explicit application switch suppresses that animation without
changing the original preference; it does **not** verify a Windows OS
reduced-motion transition, every interactive motion, screen-reader speech,
200% native Chrome zoom or full M4 accessibility.

The browser zoom shortcut in the agent Chrome tab did not change
`devicePixelRatio` or `innerWidth`. The tab was not present as a uniquely
selectable native Windows Chrome window; no unrelated user window was used
and no viewport proxy was promoted to native 200% evidence. Five existing
stopped paper sessions had at most 20 rows in any signals/risk/orders/fills
table and a largest REST snapshot of about 21.5 KB. No speculative local
pagination was added; a genuinely long-running feed would need bounded
server transfer as well. No code, account, study, provider or dataset was
changed, and no screenshot/recording artifact was saved. M4/M5 remain open.

## 2026-09-29 foreground service-status recovery — local gate

The topbar rechecked service health on initial load, manual refresh and tab
return, but could continue saying "Service online" indefinitely if the user
kept the tab visible while the backend failed. The existing return-check path
now runs every 30 seconds while visible; hidden tabs make no requests, and
unmount clears the timer. Its refresh still checks both health and available
data, so the status and catalog are not silently equated with data freshness.

An isolated fake-time regression covered online → HTTP 503 → recovery without
focus/visibility events, no hidden-tab requests and timer cleanup. Focused
App tests passed 14/14; full frontend 367/367, local Ruff/format/mypy,
ESLint/TypeScript and production build passed. Before this change, the full
isolated `make test` passed (frontend 366/366); the backend was unchanged.
The original Compose PostgreSQL/Redis/backend remained healthy, Redis returned
PONG, and `/api/health` and the frontend both returned HTTP 200. Actual Chrome
opened the saved U6 historical result by GET: the undated-account warning,
five cash rejections and source checksums remained visible; expanding source
details kept keyboard focus, and Tab reached the independent-account link.

This is local unit/build and bounded Chrome GET-only evidence, not a real
browser backend-outage trial, native assistive-technology/zoom proof, saved
current-head media, full M4/M5 acceptance or GitHub CI. GitHub recovery on
October 1 is a user estimate, not a verified clearance to push or release.

## 2026-09-29 global search to saved-security detail — bounded Chrome

From `/markets`, keyboard Return on the existing saved 平安银行 result in global
search formerly closed the palette and filtered the table, but did not open the
selected security's detail; focus returned to the topbar search button. The
link now includes the already-supported effective-dated dataset/security
detail hash while retaining the dataset and exact-ID list filter. The market
page's existing resolver still requires a registered available dataset and a
valid exact CN-A security ID, failing visibly when it cannot resolve one.
Review also found that closing a managed hash detail could leave its saved
navigation URL stale; the shared replace helper now updates that marker only
when it matched the URL being replaced. Markets and strategy drawers reuse it,
without blessing an unknown native hash change.

An extended command-search regression failed before the link change and passed
7/7 afterward. A managed-return regression also failed before the helper and
passed afterward; the unknown-URL guard and direct-detail/fail-closed tests
remained green. Full frontend tests passed 366/366, ESLint, TypeScript/Vite 129-module build
and changed-file Prettier passed. In actual Chrome on the same `/markets`
route, Enter opened the named 平安银行 · 000001 detail, focused its visible Close
button, and Escape returned to the exact-ID filtered list. The historical
archive cutoff remained 2025-12-31; no market acquisition or user-data POST
was sent. A separate first pointer click on the strategy card opened its
drawer and focused Close in one fresh Chrome trial, but the earlier intermittent
cold-click/p95 question is not resolved by that single pass. The browser
tool did not expose `history.state` for direct inspection; the focused test
covers the managed marker and return behavior.

This is agent-operated GET-only keyboard/visual evidence, not saved current-head
media, native screen-reader speech, 200% zoom, statistical click latency,
independent novice acceptance, complete U5/M4/M5 or GitHub CI/release.

## 2026-09-29 data-center saved task keyboard focus — bounded Chrome

The history `Open task` button bypassed the existing focus handoff. A keyboard
selection first left focus on the page body; after handing focus to the detail,
the reloading history list shifted that detail below the 911px Chrome viewport
(top 1137px). The button now reuses `openAndFocusTask`, and the selected detail
renders before history so a list refill cannot move it out of view. No task,
provider, financial or API behavior changed.

Focused component checks passed 29/29, including Enter, history refill and
no focus theft when another control is chosen. Full frontend tests passed
364/364; ESLint, TypeScript/Vite 129-module build and changed-file Prettier
passed. In actual Chrome, keyboard Return opened an existing saved task via
GET, focused its named detail, and kept it visible at top 398px while history
refilled below it (top 1730px). The temporary agent tab was closed; original
Chinese/dark preferences were not changed. Independent read-only review found
no blocking defect. A long detail now places history farther down the page.

This is a bounded keyboard/visual U5 check, not native screen-reader speech,
200% zoom, full U5/U8/M4, independent novice acceptance, GitHub CI or release.
No original database write or saved screenshot artifact is claimed.

## 2026-09-29 terminal-free login startup — read-only causal narrowing

The enabled current-user `QuantTrading-DockerDesktop-AtLogon` task ran at
2026-09-28 23:41:00 AEST after the 23:40:45 boot and returned task result 0.
Docker Desktop's backend launched at 23:41:01, exited at 23:41:25, launched
again at 23:41:43 and exited at 23:41:51. The currently healthy Docker
backend processes started only at 2026-09-29 04:50:06 AEST after manual
recovery. Thus the scheduled trigger worked, but task result 0 is **not**
evidence that Engine, Compose or the UI stayed available after login.

A bounded Application Error/WER check found no matching event in the startup
window; Task Scheduler Operational logging was disabled and old backend logs
had rotated. The exact backend exit cause remains unproven. Existing at-logon
task and Docker Run entry already coexist; no third launcher, task execution,
reboot or system change was made. M5 terminal-free startup remains NOT_PROVEN.
At the next genuine login, inspect timestamped Engine/Compose/API/frontend
availability before any manual intervention, then diagnose the captured exit
if it recurs. No simulated login or read-only check now can close that gate.

## 2026-09-29 saved historical plan bilingual keyboard audit — bounded Chrome

At unchanged executable code head `b9089b2`, actual Chrome opened the existing
saved U6 historical result `d9f27183-a9a1-4f34-aef4-eba439f53374` by GET.
Chinese/dark displayed the 2011-03-22 plan, missing account-snapshot date,
2011-03-23 next accepted trading day and explicit historical/not-today and
no-order warnings. The recorded cash `45539.94836`, equity `104666.94836`
and risk-approved buy estimate `44221.44166` were visible. Its five cash
rejections were reachable through the risk-decision pagination; Shift+Tab
from its pager reached a named technical-detail button. Enter expanded the
`INSUFFICIENT_BUYING_POWER` trace and kept visible keyboard focus.

After a temporary EN/light switch, the same plan retained its dates, figures
and warnings in English. ArrowRight on the focused horizontal table region
exposed the complete rightmost Risk/OMS decision text, including all five
`Rejected: Insufficient available cash` rows; ten further ArrowRight presses
did not visibly move the table or truncate the text. Tab reached the named
Data and configuration provenance button; Enter collapsed it without losing
focus. The original Chinese/dark preferences were restored and the agent tab
closed. Main database read-only counts remained paper5/events417/research8.

This is an agent-operated, GET-only Chrome visual/keyboard check, not an
independent novice study, native screen-reader announcement, exact numeric
scroll-bound measurement, full U6/U8/M4, or a persisted screenshot/recording.
The browser tool showed images for visual inspection but did not save an image
artifact in this run. GitHub CI and release remain held.

## 2026-09-29 historical filled-plus-pending crash — bounded isolated proof

The pinned `3e621a1` backend replayed the accepted 2011 historical archive
read-only against uniquely owned tmpfs `quant_test` PostgreSQL/Redis. While the
scratch account was `RUNNING` with six persisted historical fills and six
positions, the API was paused and one `ACCEPTED` order was **QA-injected via
the repository into that same scratch journal**. This order was not generated
by the running broker. The 124-event SQL prefix was recorded before scratch
API `SIGKILL` and retained its SHA-256 after both starts.

The first start appended exactly one `CANCELLED` update for the injected order
and one `INTERRUPTED` status event (126 total). The second start appended
nothing. Both restored HTTP snapshots retained six fills, six positions,
cash `81309.8134` and equity `99964.8134`, with the order cancelled; both
attempts to restart the interrupted account returned 409 without journal
changes. The adjacent outside-Git result
`product-evidence/v1.2/m4/20260929-3e621a1-historical-six-fill-injected-pending-crash.json`
records IDs, prefix checksum, script checksum and exact scope.

Only owned scratch containers/network were removed; no original image, volume,
database or account was mounted or changed. Original services remained healthy,
API/frontend returned HTTP 200, main database read-only counts stayed 5/417/8,
and frozen archive marker/manifest hashes matched the prior checkpoint. This
narrows U7 restart integrity but does not prove a broker-generated pending
order beside fills, lawful current-data forward trading, genuine lost-ledger
restoration, independent backup, full U7/M4/M5, GitHub CI or release.

## 2026-09-29 saved-result report export keyboard focus

On an existing saved 2011 historical result, actual Chrome keyboard Return
prepared the CSV report but the focused download button became natively
disabled and focus fell to `BODY`. A deferred-download regression was red
before repair. Both JSON and CSV buttons now use `aria-disabled` during the
existing synchronous duplicate-GET guard; the collection select remains
natively disabled so the requested report cannot change mid-flight.

After repair, the focused regression passed 12/12 and the full frontend suite
passed 361/361. ESLint, TypeScript, changed-file Prettier and the 129-module
production build passed. In the same Chrome result, keyboard Return prepared
the report with focus still on the CSV button; the next Tab reached the
prepared-report fallback link with the expected filename. A separate read-only
review found no actionable issue. The local evidence is indexed outside Git
under `product-evidence/v1.2/m4/20260929-32a6a04-export-keyboard-focus.json`.
The export was GET-only; main database read-only counts stayed at 5/417/8.
This is a bounded U4/M4 keyboard repair, not native screen-reader speech or
complete export, accessibility, product or release acceptance.

## 2026-09-29 historical paper crash after persisted fills — bounded local check

At executable head `3e621a1`, a uniquely owned backend used scratch tmpfs
`quant_test` PostgreSQL/Redis and the accepted historical archive read-only.
Its 2011-03-23 replay account was still `RUNNING` with six committed fills and
six positions when only the scratch backend received `SIGKILL`. The original
123 SQL events retained the same SHA-256 after two actual starts. Startup
appended one `INTERRUPTED` event (124 total); the second start added none.
Both post-restart HTTP snapshots matched the pre-crash SQL ledger's seven
listed portfolio values, six listed fields per position and the multiset of
eight listed fill attributes, including order IDs. The final event sequence
was 124. Starting the interrupted account returned 409 twice and appended no
event. This does not establish a distinct fill-level ID or entire object
identity. Earlier zero-fill pending-order restart evidence is separate; this
run had no pending order at the freeze.

The outside-Git result in `product-evidence/v1.2/m4/20260929-3e621a1-historical-fill-crash-rest-snapshot.json`
and its adjacent repeatable script record the exact prefix checksum and limits.
The scratch containers/network were removed; images and original volumes
remained. The four original Compose
services stayed up, main database read-only counts remained 5/417/8, and
frozen archive marker/manifest hashes matched the prior checkpoint. This is
not genuine pre-loss ledger restoration, lawful new-market forward evidence,
independent backup, full U7/M4/M5, GitHub CI or release acceptance.

## 2026-09-29 current-code local release and chart checks during GitHub CI hold

At executable code head `3e621a1`, all three Compose configurations passed
validation. A uniquely tagged production frontend image built 129 modules and
served `/`, `/help` and `/markets` through isolated Nginx with HTTP 200. A
uniquely tagged backend image ran on a private scratch network with tmpfs
PostgreSQL `quant_test` and Redis; Alembic upgraded to `20260924_0016`,
downgraded to baseline `20260904_0001`, upgraded again and reported no pending
schema operation. Its production paper-mode `/api/health` returned HTTP 200;
capabilities exposed the synthetic demo and correctly marked the deliberately
unmounted historical archive unavailable. The release frontend was **not**
opened against that backend: its baked API origin points to the live local
port 8000, so the Nginx checks prove static delivery only.

Only the newly owned scratch containers and network were stopped; the local
images remain. The original four Compose services remained running and the
main database's read-only counts were five paper sessions, 417 paper events
and eight product research jobs, unchanged from the previous checkpoint.
The full local backend/frontend/lint/type/build suite at this same executable
code head is recorded below, not rerun merely for this documentation entry.
This local smoke is **not** GitHub CI, integrated production-browser coverage,
independent disaster recovery, U7 forward acceptance or a release PASS.

Separately, Chrome read-only keyboard paging on the existing 293-session
historical result advanced the equity/drawdown chart from 1–100 to 101–200 and
201–293. The last-page Next button disabled, Tab focused Previous, and the
pager exposed `aria-live=polite`; the browser error log was empty. The actual
JPEG and SHA-256 are indexed outside Git in the local delivery evidence. This
does not prove native screen-reader speech, full WCAG 2.2 AA, native 200% zoom
or the complete chart/device matrix.

## 2026-09-29 local paper event integrity during the GitHub CI hold

Two paper-ledger defects were reproduced before repair. The live frontend
replaced signals with the same strategy, timestamp and type, silently hiding
distinct security or repeated same-security events. The reducer now appends
each new-sequence `signal.created` event, matching the REST event projection;
the existing sequence guard still discards replay duplicates. A regression
failed before the change and covers both different and repeated symbols.

The A-share runtime's terminal cleanup also reported cumulative expired
orders, repeating earlier `CANCELLED` events. It now returns only cancellations
caused by `finish()`, including when an earlier order expired before a new
pending order. The shared paper manager retains that cancellation batch across
a failed terminal database transition, so a concurrent STOPPING retry or
FAILED fallback does not lose the order update. Offline replay fault-injection
tests failed before this shared fix and passed afterward. The isolation tests
did not write to the original paper database or call a market provider.

The final local `make test` run used the disposable tmpfs `quant_test` database:
backend 1024 passed, one optional unmounted historical-archive case skipped,
frontend 361 passed. Local Ruff, format check, mypy, ESLint, TypeScript and
production frontend build passed; an independent read-only diff review found
no blocking issue. The four original Compose services and health endpoint
remained available. This is bounded local event-integrity evidence, **not**
GitHub CI, a genuine lost-ledger restore, lawful forward-feed acceptance,
full U7/M4/M5, or approval to merge/release. Current-head screenshots, if
captured, are indexed outside Git in the local delivery evidence directory.

## 2026-09-29 local gates during the GitHub CI hold

The isolated `make test` target previously ended with `down --volumes`.
Its PostgreSQL data is already tmpfs, so the target now stops only its
disposable Compose services; the development and performance instructions
match this no-volume-deletion policy. Before running, the test Compose config
was checked for `quant_test`, `APP_ENV=test`, an unpublished PostgreSQL port
and tmpfs storage. The local full run migrated that database to
`20260924_0016`: backend 1019 passed, one optional unmounted-archive case
skipped, and frontend 358 passed. Local Ruff/format/mypy, ESLint, TypeScript
and production build also passed. These are local checks, not GitHub Actions.

An additional paper-stream regression then reproduced a distinct fault:
when the opening WebSocket was blocked, REST returned a saved `STOPPED`
account with cash and fills, but the page stayed on Loading. The shared hook
now accepts that authoritative terminal REST snapshot and cancels its pending
reconnect. A `RUNNING` REST snapshot still cannot masquerade as live state
without a WebSocket. The stopped-account test failed before the fix; after it,
paper-page 43/43 and full frontend 360/360 passed, with ESLint, TypeScript,
changed-file Prettier and the 129-module production build. This is bounded
component proof, not an injected real-browser socket outage or full U7/M4/M5.
The original services, accounts, frozen research and Official OOS were not
used for the test writes. No push, remote CI, merge or release was attempted.

## 2026-09-29 isolated backend process restart with pending orders

An owned `quant-mvp-tests` PostgreSQL with tmpfs storage was migrated to
`20260924_0016`; its backend used only the test project and read-only fixture
data. A fresh replay account `e620d5b4-30b1-4db7-b21f-deb5af1cc9e5` was
created through HTTP, then four distinct `CREATED`, `SUBMITTED`, `ACCEPTED`
and `PARTIALLY_FILLED` order states were seeded through the existing repository.
Before failure, HTTP showed `RUNNING`, seven continuous events and zero fills.
Only that labeled scratch backend was killed with SIGKILL; test PostgreSQL
stayed healthy. On the real application startup path, HTTP showed
`INTERRUPTED`, each order `CANCELLED` once, and events 1–12 (four cancellation
events followed by the interruption). A second kill/start left the event count
at 12 and added no duplicate cancellation or fill. The test backend and tmpfs
PostgreSQL were then stopped without deleting any image or volume. The original
four services stayed up; the main database's read-only counts remained five
paper accounts, 417 paper events and eight research jobs. `.research` was
unchanged. This operational gate uses injected simulated orders and zero fills;
it is not genuine pre-loss ledger recovery or full U7 acceptance.

A separate cold-click performance pilot opened only an existing saved-results
page in verified Chrome, then stopped before input: the available browser
scope exposed neither `performance` nor `PerformanceObserver` and could not
prove foreground focus. No native Event Timing sample or p95 is claimed.
The temporary tab was closed without application writes. Prior delayed and
unmatched clicks remain unresolved; M4 performance and accessibility stay open.

## 2026-09-29 isolated current-head historical flow during GitHub hold

At code head `f75dd95`, production backend/frontend images ran against an
owned private test network, tmpfs PostgreSQL/Redis/product state, and read-only
repository data and audited historical archive. Fresh Alembic upgrade reached
`20260924_0016`; the test API and frontend returned HTTP 200. The original
Compose services, accounts, volumes and frozen research were not used for
these writes.

In the actual in-app browser, guided historical study A
`dd3ab840-fc90-4885-98e1-3484e5e18c1a` completed 293/293 including
warmup for 2011-03-01 through 2011-03-22. It had zero fills because 20
approved proposals had no in-window next session; its preview was dated
2011-03-22 for 2011-03-23 and was not submitted to an account. Studies B
`47d883ec-f650-45fd-aa91-8962405f524f` and C
`e742b89e-6bc2-45cb-b6f4-8165e9a91255` each completed 294/294 for
2011-03-01 through 2011-03-23 with six historical fills. Their saved
comparison agreed on data SHA, scope, dates, capital, risk and strategy;
only the simulated commission rate differed (`0.0003` versus `0.002`).
B cost CNY 30.1866 and ended at CNY 99964.8134; C cost CNY 37.5066
and ended at CNY 99957.4934. The comparison page flagged the cost mismatch
and did not rank or recommend either study. Reload preserved the comparison.

The result-to-paper handoff from A copied settings but did not create an
account or order. After explicitly extending the independent replay through
2011-03-23, account `311ed27f-ec9e-43ef-94db-5a1c214892ed` was created
with no orders, then deliberately started. It stopped after 17 market
sessions: 20 distinct simulated orders, six fills, final cash CNY
81309.8134 and equity CNY 99964.8134, matching B's financial result.
Its persisted 2011-03-22 plan named 2011-03-23 as the next accepted
session, `submitted_to_account=true` and the same account ID. A page reload
restored the stopped status, plan dates and final balances.

After recording these results, the three agent-created browser tabs were
closed and only the four exact `qtp-v12-e2e-20260929-*` containers were
stopped. Their scratch PostgreSQL/Redis used tmpfs, so that disposable test
state ended with them; the stopped containers and images were retained.
The original four Compose services remained up and the main API health
check still passed. No Docker volume, image or original database was removed.

This is bounded historical/local integration evidence on an isolated
disposable database, not native Chrome, saved current-head media, a genuine
after-start market-data receipt, forward paper trading, full U7/M4/M5,
GitHub CI or v1.2 release acceptance. No Official OOS was rerun.

## 2026-09-29 terminal paper-stream recovery after transient snapshot failure

The paper detail previously treated a WebSocket terminal-status notification
as final before the authoritative REST snapshot succeeded. If that GET briefly
returned HTTP 503, the socket closed with retries disabled and the final
account status and ledger remained unavailable until manual reload. The shared
stream hook now treats the notification as a reason to hydrate; only a
successful terminal REST snapshot (or an explicit 401/403/404 denial) stops
reconnection. A server close before the GET finishes aborts that read and
uses the existing bounded reconnect path. Financial values are cleared on a
failed read, not presented as an authoritative final balance.

The new terminal-notification/503 regression failed before the change and
passed after it. A second test covers the server-close-before-snapshot race;
the existing successful-terminal, initial-failure, stale-money and retry-limit
tests remain passing. Paper page: 41/41; full frontend: 358/358 across 37
files; ESLint, TypeScript, changed-file Prettier and 129-module production
build passed. Independent read-only review found no actionable race. These
are component and code-review checks, not a real-browser injected outage or
full U7/M4/M5 acceptance. No original account, database, provider, frozen
research, Official OOS or GitHub action was changed.

## 2026-09-29 shared pagination range announcement

The shared pager moves keyboard focus to its named group before an asynchronous
page change, but the settled range text was not a live region. Its existing
range span now has `aria-live="polite"`; focus behavior and button states are
unchanged. A focused test confirms the same span updates from loading to the
new range and preserves deliberately moved focus. Adding `role="status"`
initially caused three unrelated status queries to become ambiguous, so the
smaller live-only markup was retained. Focused 9/9 and full frontend 356/356
passed, along with ESLint, TypeScript and the 129-module production build.
This proves DOM semantics, not native screen-reader speech, 200% zoom or full
U6/M4/M5 acceptance. No provider, database, frozen research or remote action
occurred.

## 2026-09-29 local operation and orphaned paper-order recovery

GitHub Actions remains unavailable pending actual account recovery, but the
original local Compose services are running: PostgreSQL accepts connections,
Redis returns `PONG`, and the frontend and `/api/health` both return HTTP 200.
This permits local use and testing, not pushed-head CI, review or release.

An orphaned paper session was marked `INTERRUPTED` on backend restart, but its
persisted `CREATED`, `SUBMITTED` and `PARTIALLY_FILLED` orders were left open;
only `ACCEPTED` was cancelled. The restart path now cancels the same four
pending states as normal stop/failure, leaving `FILLED`, `CANCELLED` and
`REJECTED` untouched. In isolated tmpfs `quant_test`, the seven-case restart
regression first failed 3/7 and then passed 7/7. Full backend: 1019 passed,
one optional historical-archive case skipped because that archive was not
mounted. Ruff check/format and mypy passed. The original database, paper
accounts, frozen research and Official OOS were not used or changed. This is
a bounded recovery fix, not genuine pre-loss ledger restoration or full
U7/M4/M5 acceptance.

## 2026-09-29 U5 and task-center active-list consistency

The Data Center's saved update detail already polled active tasks, but its
adjacent history and both task-center lists made only one request. They could
continue to show queued/running after the server had completed a task. The
existing resource hook now optionally polls only while the returned page has
queued/running items. A response replaces the visible page without a loading
flash; a failed read clears the unconfirmed prior status and requires the
visible Refresh action before another attempt. Dependency changes or unmounts
abort the old request and timer. Research and raw-candidate task lists use the
same bounded five-second behavior. Only each row's changing status has polite
live-region semantics, not the entire list. No polling starts jobs or promotes
candidate data to execution authority.

The update-history regression failed before the fix (one list request after
five seconds), then passed with running-to-completed convergence, retained
list during an in-flight read and no further terminal polling. A second
regression confirmed a 503 hides stale running status, stops automatic reads
and recovers only after explicit Refresh. Task-center research/update tests
also passed. Full frontend: 356/356 across 37 files;
ESLint, TypeScript, changed-file Prettier and 129-module production build
passed. Actual Chrome GET-only reopened `/tasks` and `/data` against the
original local app and displayed persisted terminal rows. No active task was
created for QA, so live-browser status transitions and actual screen-reader
speech are not claimed. The
original database, providers, frozen research and Official OOS were not
modified. This narrows U5/task recovery, not lawful current-data authority,
full M3/M4/M5, screen-reader/native zoom, GitHub CI or release acceptance.

## 2026-09-29 U5 update-task command focus and Chrome read-only check

The saved update-task Cancel/Retry buttons were natively disabled during a
request, which could drop keyboard focus. A completed cancellation or failed
task read could then remove the focused button; successful Retry opened a
linked task on the same pathname without handing focus to that new detail.
Regression tests first failed on the pending controls. The existing request
lock remains authoritative, Cancel is additionally guarded after the server
records `cancel_requested`, and source-denied/receipt-blocked Retry remains
natively disabled. Pending controls use `aria-disabled`; focus moves to the
terminal status, read error or linked task only when the command still owned
focus. Moving focus to Refresh or another outer control is respected.

The focused suite passed 24/24 and the full frontend passed 353/353 across
37 files. ESLint, TypeScript, changed-file Prettier and the 129-module
production build passed. Independent read-only review found no actionable
regression after the linked-task and read-error cases were added. In actual
Chrome, a saved failed update task was reopened by GET only: its status
heading was focusable, Retry had the expected enabled state, and the browser
reported no warning/error. No Retry/Cancel POST or provider acquisition was
made against the original application.

The dynamic pending/terminal and linked-Retry focus transitions are proven by
component tests, **not** by a live browser command or screen-reader speech.
This does not establish U5/M4/M5 acceptance or source rights. Original
services, volumes, ledgers, frozen `.research` and Official OOS were not
changed; GitHub CI, review, merge and release remain on hold.

## 2026-09-29 native Chrome zoom tooling boundary

The Chrome browser extension opened the local workbench at 1728×911 CSS
pixels with device-pixel ratio 1. Sending a page-level Ctrl+Equal left both
width and ratio unchanged, so it did **not** produce native 200% zoom.
The separate Windows computer-control path stopped before input because it
could not verify the current Chrome URL for policy enforcement. This is a
tooling boundary, not evidence that the app passed or failed 200% zoom.
No shortcut repetition, viewport-proxy promotion or safety bypass followed.

## 2026-09-29 experiment command focus and local operation during GitHub hold

Experiment Cancel/Retry used native-disabled pending buttons, so keyboard focus
could fall to the document body when a request began or the focused Cancel
button disappeared after a terminal status update. The controls now remain
focusable with `aria-disabled`; the existing synchronous lock and a
`cancel_requested` guard prevent duplicate commands. If a status change
removes the still-focused action, focus moves to the stable status text.
Deliberate movement to Refresh is respected. The status has a visible focus
ring. A red regression demonstrated the prior failure.

The focused experiment suite passed 39/39 and the full frontend passed
346/346 across 37 files. ESLint, TypeScript, changed-file Prettier and the
129-module production build passed. Independent read-only diff review found
no blocking regression. A GET-only in-app browser recheck of an existing
completed historical task found the named status element in the rendered DOM
and no browser warning/error. No Cancel/Retry POST or provider acquisition
was made in the original application. PostgreSQL accepted connections, Redis
returned PONG, and the original frontend and `/api/health` returned HTTP 200.

The pending-to-terminal focus transition is component-tested, not verified
in a running browser; native Chrome, 200% zoom, screen-reader speech and full
U3/M4/M5 acceptance remain open. Local operation and checks may continue
during the user-estimated GitHub hold, but they do not replace pushed-head CI,
review, merge or release. Original volumes, ledgers, frozen `.research` and
Official OOS were unchanged.

## 2026-09-29 local execution and U5 market-update submit focus

GitHub CI/CD remains on hold until actual account recovery; October 1 is a user
estimate, not a verified runner date. Local Compose remained available with
PostgreSQL/Redis/backend healthy, Redis `PONG`, and both the frontend and
`/api/health` returning HTTP 200. This supports local use and checks, not a
substitute for pushed-head CI, review, merge or release.

The market-update form had a native-disabled pending Submit inside a disabled
fieldset, which could drop keyboard focus even though its existing synchronous
lock already prevented duplicate requests. Submit now remains focusable with
`aria-disabled` while fields stay disabled and the lock still blocks keyboard
and pointer repeats. On successful creation, focus moves to the named task
detail only when Submit still owned focus; an already-open same-identity task
is handled without relying on a URL change. Deliberate focus movement to
another control is respected. A red same-ID regression confirmed the old gap.
The focused suite passed 17/17; full frontend passed 342/342 across 37 files,
with ESLint, TypeScript, changed-file Prettier and a 129-module release build.
Independent read-only review identified and verified the same-ID boundary.

No real market-update POST or provider acquisition was made because local
product-use rights for current A-share data remain unverified. This is a
bounded component-level focus check, not an actual-browser submission,
native Chrome/200%/screen-reader proof, full U5/M4/M5 acceptance, current
forward-data authority or GitHub CI. Original services, volumes, ledgers,
frozen `.research` and Official OOS were not changed.

## 2026-09-29 paper command keyboard focus through request and status changes

Start, Pause and Stop previously used native `disabled` while their POST was
pending, which could remove keyboard focus. A later WebSocket status could also
remove the focused action and leave focus on the document body. A red regression
demonstrated both gaps. The controls now remain focusable with `aria-disabled`;
one synchronous lock blocks repeated keyboard/pointer POSTs. When a focused
action disappears after an authoritative status change, focus moves to its
stable status text. Moving focus elsewhere first is respected. The existing
shared disabled-state and focus-ring styles are reused.

The paper-page suite passed 39/39, the full frontend passed 339/339 across 37
files, and ESLint, TypeScript, changed-file Prettier and a 129-module release
build passed. Independent read-only diff review found no actionable blocker.
In an actual in-app browser against a new release frontend and **isolated,
mount-free** API/PostgreSQL/Redis, two disposable synthetic 2030 accounts were
created. Mouse Start/Pause/Stop on the first and keyboard Start followed by
pointer Stop on the second reached authoritative
status updates; after each removed focused action, the active element was the
status span. Keyboard Start left a visible 2px focus outline. Browser warning/
error logs were empty. Both accounts were explicitly stopped before QA cleanup.
The scratch database was migrated from empty to Alembic head `20260924_0016`
and lived only in tmpfs; the exact labeled test services were stopped. Original
services, volumes, accounts, frozen `.research` and Official OOS were not
modified. No live order, market acquisition or GitHub action occurred.

The deferred 503/double-activation case was component-tested, not forced in a
live browser. This is bounded in-app browser and synthetic-mode evidence, not
native Chrome, screen-reader speech, a genuine new-market forward session,
saved release media, full U7/M4/M5 acceptance or GitHub CI.

## 2026-09-29 watchlist keyboard focus during save and remove

A new regression failed against the old native-disabled Save button. The
existing synchronous watchlist lock already blocked repeat writes; Save and
Remove now use focusable `aria-disabled` during an in-flight change. On a
successful Remove, focus moves to the stable, named watchlist section only if
the removed button still owns focus; moving elsewhere during the request is
not overridden. The shared disabled-state CSS already covers this attribute.
The focused markets suite passed 16/16, full frontend 336/336 across 37 files,
ESLint, TypeScript, changed-file Prettier and the 129-module build passed.
An independent read-only diff review found no actionable blocker.

For an actual in-app browser check, a new release frontend image used a
private scratch API and tmpfs PostgreSQL containing a local, short-lived copy
of the existing database. Historical/product/data mounts on the scratch API
were **read-only**; the original database and application endpoints were not
used for writes. In the Chinese market page, mouse and keyboard each saved and
removed `CN-A:SSE:600000` through the isolated API. Save retained the button
focus; Remove moved it to the named watchlist section. Keyboard removal showed
a visible 2px focus outline. The isolated API returned PUT 200 and DELETE 204;
the scratch and original watchlists each had one record afterward, and the
browser reported no warning/error. The owned browser tab closed; exact labeled
scratch API/web/PostgreSQL/Redis containers were stopped after checking IDs and
mount modes. Stopping the tmpfs PostgreSQL discarded **only the test copy**;
the original volumes/images and four running services were preserved.

This is a bounded local keyboard/pointer and DB-copy browser proof, not native
Chrome or screen-reader speech, saved release media, real novice testing, a
full U5/M4 matrix, GitHub CI or v1.2 release acceptance. No provider, formal
research, frozen asset, OOS, live order or remote GitHub action occurred.

## 2026-09-29 local CI-equivalent checks while GitHub is unavailable

The current code tree (unchanged since `8e5b9eb`; `ad740cf` only recorded the
preceding rehearsal) passed the frontend CI commands in the running local
container: 335 tests in 37 files, ESLint, TypeScript and the 129-module
production build. A separate, broader Prettier check is **not** in CI and
reported style drift in eight tracked files at this head (`index.html`,
`scripts/benchmark.mjs`, `src/App.tsx`, `src/components/EquityChart.tsx`,
`src/i18n/i18n.test.tsx`, `src/product/experiments/api.test.ts`,
`src/product/experiments/ExperimentsPage.tsx`,
`src/product/experiments/fixtures.test-data.ts`). No formatting rewrite was
made merely to mask that distinction.

Against the owned, mount-free, tmpfs `quant_test` PostgreSQL—not the original
application database—the backend image passed Alembic upgrade, downgrade to
`20260904_0001`, re-upgrade and `alembic check`; 1,013 tests passed, with one
optional read-only historical-archive test skipped because that archive was
not mounted. Ruff check, Ruff format check (544 files) and mypy (144 files)
passed. All four Compose configuration/override checks in CI passed. The
temporary database/cache containers were stopped again after exact ownership
checks; no `down -v`, prune, original-volume or frozen-research operation was
used. Original four project services remained healthy.

These are local equivalents of the code/test checks, **not** a GitHub runner,
pushed-head PR check, review, merge or release. The user-estimated October 1
GitHub recovery has not been verified. Full product and external gates remain
open.

## 2026-09-29 exact-head local integrated release rehearsal

Docker Desktop 4.92.0 was launched normally after login, without reinstall or
reset. The existing PostgreSQL, Redis, backend and frontend Compose containers
were started in place: database, cache and API are healthy; Redis returned
PONG; `/api/health` and the frontend returned HTTP 200. This proves manual
recovery today, not automatic startup after a future login.

At clean local head `8e5b9eb`, production backend and frontend images were
built. A separate labeled, mount-free network used temporary PostgreSQL and
Redis filesystems and no original project volume. Its fresh database migrated
to Alembic head `20260924_0016`; scratch production API and frontend served on
loopback 18000 and 15174. In an actual in-app browser, the guided research
wizard created one **synthetic demo** job, which completed 340/340 sessions.
The saved result survived page reload; the scratch database contained exactly
that one successful job. Both English and Chinese views labeled it non-market
evidence and withheld an executable rebalance plan because there was no
accepted next session. The result showed 7 proposals, 5 simulated fills and
2 open-outside-limit rejections. No browser error/warning was observed.

The owned browser tab and four scratch containers were closed/stopped after
checking exact IDs, labels and zero mounts. Their temporary database/cache
contents were disposable; their stopped containers and images were retained.
The original Compose services, volumes, account records and frozen research
were not altered. This closes the prior **exact-head integrated image/browser
rehearsal** gap only. It does not establish native Chrome, saved release media,
200% zoom/screen-reader, uninvolved novice, lawful current-market feed,
genuine pre-loss paper ledgers, independent backup, full U1–U8/M0–M5, GitHub
CI or release readiness. The user-estimated October 1 GitHub recovery remains
unverified; no push, merge or release occurred.

## 2026-09-28 local execution without GitHub CI and pending-submit recovery

The original PostgreSQL, Redis, backend and frontend Compose services remained
running; both `/api/health` and the local frontend returned HTTP 200. GitHub
availability on October 1 is only a user estimate, not a verified recovery.
Local Compose, tests and production-image checks can continue, but they do not
replace exact pushed-head CI, review or release gates.

Before this UI fix, an isolated production frontend/backend stack at local head
`e7aba94` used a private network and tmpfs PostgreSQL/Redis. Its fresh schema
migrated to head, and an actual in-app browser completed one synthetic-demo
study (340/340 sessions), reopened its result, and showed the synthetic-not-
market-evidence warning in both languages. Those owned scratch services were
stopped; their test data were transient, and the original project services,
volumes, account records and frozen research were untouched. This is a bounded
integrated release rehearsal, not the post-fix image or formal study evidence.

The subsequent pending-submit fix keeps the legacy backtest, paper-account and
guided-study submit controls focusable while the existing request locks prevent
duplicate writes. A failing-then-passing regression covers each path. The
paper-account error now treats an uncertain response conservatively: check the
session list and service status in another tab, keep the form open, then retry
unchanged settings with the same request ID. The test verifies the same
Idempotency-Key on retry and the Chinese/English recovery copy. Definite
401/403 denials instead show the permission error; bilingual regressions guard
against an uncertain-retry instruction on those responses. Full frontend
335/335 across 37 files, lint, typecheck, Prettier and production build (129
modules) passed locally. In an isolated release frontend with its API
intentionally unavailable, actual in-app browser checks showed the English and
Chinese recovery message and retained submit focus; no paper account was
created. The labeled mount-free test container was stopped. Native Chrome,
screen-reader, independent novice, exact-head GitHub CI and full U1–U8/M0–M5
acceptance remain open; no push, merge, release, OOS or live trading occurred.

## 2026-09-28 local operation and submission/focus safety while GitHub is held

The original four Compose services remain running locally. A production
frontend image built from `caa6953` (129 modules) served `/`, `/help`,
`/markets` and a direct comparison URL with HTTP 200 in an isolated,
mount-free loopback Nginx container. Its exact identity and label were checked
before stopping it; the image was retained. This is static route smoke, not an
integrated production browser run or GitHub CI.

A failing U3 regression showed that the study wizard could POST even when
browser storage rejected the draft and idempotency request ID. Submission now
stops before the API call unless that identity is saved. Once storage recovers,
the same page can submit once; the bilingual warning names the unsaved request
ID. The test proves zero create calls on failure and one on recovery. It does
not simulate a native browser storage outage or claim the full U3 journey.

A second failing regression exposed a refresh-focus defect: after health
completed but capabilities remained pending, the topbar button unlocked and
could restart the latter request. It now remains focusable with
`aria-disabled` and refuses repeat activation until both checks finish. A
bounded live in-app browser click kept focus on the button after the ordinary
fast refresh; the pending split is component-tested, not a live throttled
browser or screen-reader proof.

After both fixes, 330 frontend tests across 37 files, lint, typecheck,
Prettier and the 129-module production build passed locally. No backend,
financial, provider, paper account, frozen research, or official OOS path was
changed. Original services/data were not stopped or deleted. GitHub push,
exact-head CI, merge and release remain held until actual recovery; the
reported October 1 date is an estimate, not observed availability. Full
U1–U8/M0–M5 acceptance and external gates remain open.

## 2026-09-28 same-name comparison identity

The saved-study list already distinguished duplicate names, but the comparison
page dropped that identity in both result/condition column headers and the
limitations cards. A failing regression used two successful jobs with the same
name **and same displayed creation second**. The page now repeats one shared
ordinal, name and UTC creation label across the incomplete-state list, both
tables and limitations, including distinct accessible Open links. The focused
comparison suite passed 21/21; the full frontend suite passed 328/328, with
lint, typecheck, Prettier and production build (129 modules) passing locally.

One temporary in-app browser opened two existing completed historical studies
through the live local frontend and confirmed matching numbered/dated headers,
result columns, limitation cards and target links. Its screenshot showed no
obvious desktop layout overflow; the tab was closed. This browser check used
distinct real study names, while the exact duplicate-name collision is covered
by the isolated regression. No experiment, paper account, provider request,
database, frozen research or GitHub state was changed. U4 and full product
acceptance remain IN_PROGRESS; local checks do not replace exact-head GitHub CI
after actual account recovery.

## 2026-09-28 current-head local release-image smoke

At local head `816c738`, the release Compose frontend image rebuilt from source
(129 modules). In an isolated labeled, mount-free Nginx container on loopback
15174, `/`, `/help` and `/markets` returned HTTP 200. A separately built backend
image started with its own tmpfs `quant_test` PostgreSQL and Redis on a private
network; migrations reached head, production `/api/health` returned `ok` with
paper broker mode, and capabilities truthfully offered synthetic demo while
historical exploration was unavailable without the private archive. The
temporary frontend, API, PostgreSQL, Redis and network were stopped/removed
after exact identity and ownership checks. Images were retained; no main
service, persistent volume, dataset or account was touched.

This matches the CI Compose job's bounded image/HTTP smoke, not an integrated
release-browser flow: the default release frontend API URL points to the live
port 8000, so no scratch frontend-to-scratch backend browser claim is made.
GitHub exact-head CI, full M5 release and external gates remain open.

On the live development frontend, one fresh hidden in-app browser tab loaded
`/strategies`; its first visible Explore strategy click opened the registered
drawer and exact `#strategy=` URL, focused Close, and closing restored the
trigger and base URL. The temporary tab was closed. This bounded in-app result
does not explain or erase the earlier one-off native Chrome first-click
anomaly, nor prove cold native pointer/p95 acceptance. Main eight retained
table count/MD5 fingerprints still equal the saved reference; `.research`
remains untouched.

The apparent synthetic-demo pre-start execution concern was rejected after
tracing the caller: earlier sessions provide the declared 253-session warmup,
while `active_from=request.start_date` prevents a target before the requested
start. Existing result tests assert initial cash and fill dates. No financial
path was changed based on the misleading loaded-session count.

## 2026-09-28 local execution while GitHub Actions is unavailable

The four original Compose services remain running; PostgreSQL, Redis and backend
report healthy, and `/api/health` and `/markets` each return HTTP 200. Local
execution is independent of GitHub Actions. This is not an exact pushed-head CI
result or permission to merge/release; the user-reported 2026-10-01 recovery is
an estimate, not observed recovery.

A U5 source-version defect was reproduced in isolated backend/frontend tests:
a saved watchlist row with the same dataset ID but a different dataset SHA was
still marked readable. The backend now checks the saved SHA against the current
registered source, returning `DATASET_VERSION_CHANGED` when they differ. The
frontend independently disables Inspect if the current dataset response has a
different SHA, while Remove remains available. The English/Chinese notice now
mentions changed sources. No real archive, saved record, frozen research, paper
account or provider input was modified.

On this working-tree snapshot, isolated `quant_test` PostgreSQL gave 1013 backend
tests PASS, one optional unmounted-archive skip; 327 frontend tests/37 files PASS.
Full Ruff/format/mypy, frontend lint/typecheck/build (129 modules), three Compose
config checks and Alembic downgrade to `20260904_0001`, re-upgrade to head and
`check` on the test DB all PASS. Main API/frontend returned 200. This is bounded
local verification. An actual in-app browser opened the existing unchanged
watchlist history on the matching source SHA; its temporary tab was closed.
The mismatch case was proved only in isolated tests, not by changing a real
archive. Eight main data-table count/MD5 fingerprints equal the saved reference;
`.research` is unchanged. The owned, labeled, mount-free `quant_test` tmpfs
PostgreSQL was stopped after checks; only its disposable test state ended, with
no image/volume/object deletion and no main service stop. Release-image smoke,
native browser/new-user/forward/
data rights/backup and GitHub exact-head CI remain separate open gates.

## 2026-09-28 benchmark visibility survives saved-chart pagination

The saved equity chart reset its Show benchmark preference on every page change:
`EquityDisplay` remounted for the new offset with a fresh `true` state. A new
regression first failed on page 2's checked box. The preference now belongs to
the stable experiment collections container, while the keyed display still
resets its selected trading date for each page. No financial calculations,
records, API, source authority or frozen research changed.

Focused collections/keyboard tests 16 PASS; full frontend 326/37 PASS, lint,
typecheck, changed-file Prettier and production build129 PASS. Actual in-app
browser at documented localhost opened the existing 293-session historical run
`d9f27183`: hide benchmark on page 1, advance to 101–200/293, then observe the
box still off, zero benchmark curve/legend and no benchmark readout. Re-enable
on page 2 restored one curve, one legend and the exact server-supplied readout.
The temporary tab was closed; no study, account, provider or order command ran.
This closes only the chart-pagination preference defect, not full UX-CHART,
native Chrome/200%/screen-reader/performance/novice/forward or release gates.
GitHub CI remains on the user-reported recovery hold.

## 2026-09-28 market-detail filtered page return matrix

Current5f4ee64 actual in-app localhost services, historical000025 only: UI query000,
SZSE filter, second page21–40/573. Four requested DOMsizes1440x900/1280x800/
1024x768/390x844 times ENZH/lightdark:16 cases. Back and Escape close the detail
and restore exact trigger/query/source/exchange/page/scroll; Forward reopens.
ReverseTab stays in modal; additional12forwardTabs and visible Close tested on
390ZHdark, not a complete cyclic/speech/AA audit. Exact2011-01-04..06-30 window,
118OHLCV/1official suspension/0missing factors retained. All page document widths
equal client widths, modal horizontally contained; native modal internal scroll.

Four actual JPEGs/checksums outsideGit; root and independent readonly reviewer
inspected390ZHdark/1440ZHlight, no observable blocker. Screenshot375x812 and
1425x891 differ from requested DOM heights, cause unproven; no physical-size or
native200zoom claim. Method/matrix/limits:
`product-evidence/v1.2/m4/20260928-market-detail-context-matrix.json`.
Review did not independently execute matrix/SQL/Tab. No production change/new
tests/dependency/financial/provider/study operation. Own tabclosed/ENsystem
restored/viewportreset; originalfourservices running/eight main fingerprints equal/
.research unchanged. FullUXDETAIL/visual/AA/novice/performance/forward/backup/login/
media/CIrelease remain incomplete; GitHubhold retained.

## 2026-09-28 bilingual recovery instructions aligned to current evidence

Both user guides corrected stale never-tested-login wording: current real09-27
sign-in/task12:41:15/result0 and later menuQuit are recorded, not complete startup
acceptance or proof of initiator. Added uncertain create lookup/unchanged draft
key/new acknowledgement versus a linked new attempt for explicit failure;
PAUSED explicit Resume replay/继续回放 versus INTERRUPTED read-only/no backfill;
last verified snapshot is not current balance. Normal paused process recovery is
not abrupt crash/database-loss/independent backup. No new runtime mechanism.

Actual in-app documentedlocalhost5173 task center loaded8research/4candidate
tasks; existing5861fbb5 Interrupted detail matched EN/ZH linked-retry/no-result
copy. No retry clicked or new task. Initial127origin failed; documentedlocalhost
worked, matching exact CORS source config. Guides name this browser-origin
boundary without suggesting security changes. Eight guide routes HTTP200, not
eight full UI flows. Independent readonly review no blocker; corrected exact
resume labels. Docs-only diff check PASS, no unnecessary suite/OOS rerun.
Two native JPEGs/checksums and limits:
`product-evidence/v1.2/m5/20260928-guide-recovery-refresh.json`.

Own tabclosed/ENsystem restored/no new process. Eight main fingerprints equal,
.research unchanged. Real novice trial availability asked once, no signoff;
M5 and full native/forward/backup/login/performance/GitHub/release gates remain.

## 2026-09-28 accepted create response uncertainty and original task recovery

Current f1e4046, owned quant_test/synthetic fixture only: guarded outside-Git
middleware let actual create return202, concealed its first response with503.
Real worker completed340/340 while wizard retained exact cash
123456.789000000000001/configuration. EN/ZH switch, task-center lookup, Back and
reload caused no second POST. Reload required a fresh acknowledgement; unchanged
explicit retry returned the same request key/config SHA/job17307fe3. SQL stayed
one task with unchanged completion timestamp, not a rerun. Native task-center Link
and neutral bilingual uncertainty guidance replace misleading noncompletion and
unreachable-service claims. Validation/permission handling remains specialized;
no automatic retry, financial/API/backend/provider/dependency change.

503/408/TypeError component regressions retain draft/key/remount/ack/edit semantics;
final325 frontend/37files, lint/type/changed-file format/build129 PASS. Shared-copy
TaskCenter and comparison assertions updated without weakening refresh/isolation.
Readonly final diff review no blocker, not independent execution. Actual browser
fault is202 concealed by503, not native disconnect/timeout. Four JPEGs/checksums
and exact identity/timestamps outside Git:
`product-evidence/v1.2/m4/20260928-create-response-recovery.json`.
Corrected-alert screenshots have the alert below fold; DOM observed guidance and
link, final result screenshot shows recovered task. No full visual/Chrome/AA claim.

Own tab closed/ZHsystem preserved; fresh PID/cwd/args checked before TERM; API
graceful shutdown/tool exit1 recorded, own listeners absent. Fresh exact owned
tmpfs container/labels/no mounts verified then stopped: only disposable test data
gone, container/image retained. Main eight fingerprints equal; original four
services running/APIfrontend200/.research unchanged. Full scope, GitHub hold,
native/novice/forward/current authorities/original missing ledgers/independent
backup/login/performance/release gates remain incomplete.

## 2026-09-28 actual paper command rejection and recovery

Current2c0077d frontend/actual API+SQL in owned tmpfs quant_test, synthetic account
0f982c1f only. UI create did not auto-start. Injected selected POST503 before
application command: CREATED/start sequence1->1, RUNNING/pause5->5,
PAUSED/stop7->7. EN/ZH alerts persisted/translated, buttons remained available;
locale change added no command request. After disarm, explicit UI clicks start,
pause, stop returned200 and reached RUNNING, PAUSED, STOPPED8. Cash/equity100000000,
date2030-01-02/10securities unchanged; zero orders/fills, not a nonempty-ledger
duplication check or forward evidence. Outside-Git harness uses existing supported
30s pacing only for UI QA, current lifecycle/SQL/runtime and own-origin CORS.

Observed defect: failure lacked a concrete next step. Existing two locale resources
now ask to check current status/connection before retry; no claim that an ambiguous
request never executed. Added guidance assertions first3failed/30passed; fixed33,
fullfrontend323/37files/lint/type/format/build129 PASS. Financial/provider/backend
code unchanged; backend suite not rerun. Four actual JPEGs/checksums and method in
outside-Git `product-evidence/v1.2/m4/20260928-paper-command-recovery.json`.
Independent readonly diff/two-image review found no release-critical issue; not
independent SQL/tests/native accessibility or Chrome proof.

Own tab closed/original ZHsystem preserved. Fresh PID/start/cwd/args verified before
TERM, graceful API shutdown logged (tool exit1, no exit0 claim); own listeners gone.
Fresh containerID/labels/tmpfs/no mounts verified then disposable DB stopped,
test data gone as designed; container/image retained. Main eight fingerprints equal,
four original services running/APIfrontend200/.research unchanged. GitHub hold,
full U1-U8/M0-M5, nativezoom/speech/novice/performance/login, genuine lost ledgers,
independent backup and lawful real after-start feed/authority/release gates remain.

## 2026-09-28 saved historical ledger responsive and keyboard matrix

Current58bcc98 live frontend bind, existing localhost5173/8000 services, stopped
historical accountd7044a3c only. Four requested DOM viewports1440x900/1280x800/
1024x768/390x844 times EN/ZH and light/dark:16 cases without page overflow.
Cash81309.8134/equity99964.8134/trading date2011-03-23 unchanged, five tables
retain6/20/20/20/6 rows, translated named focusable local-scroll regions. Older
account has no native saved plan; both locales truthfully retain that absence.
Back link40px, compact audit disclosure24.75px min; not universal40px/fullAA.

Phone table337px/content733px: real ArrowRight focus and later scrollLeft40/80,
2px visible outline, page375/375. Immediate0 preceded native scroll completion,
not failure. Mobile header intentionally omits Theme, so select via desktop UI
then remeasure phone; no hidden-DOM settings mutation or product patch. Initial
ZH notice matcher corrected to actual visible copy, not changed product copy.

Six real representative JPEGs/checksums saved; decoder corrected mistaken PNG
filename/header assumption. Own new filenames renamed jpg without changing bytes;
older screenshot links retained and MIME note added. Delivered image dimensions
differ from requested DOM dimensions; height difference cause unproven, not exact
pixel proof for16 cases. Independent readonly review of three key images found
no observable blocker, but cannot independently validate SQL/matrix/amounts or
fullAA/Chrome/nativezoom/speech/forward. No fabricated visual/financial evidence.

Original EN/system restored, temporary viewport reset/own tab closed. No new
process/account/provider/study command. All eight main fingerprints match reference,
four original services remain healthy/reachable and `.research` unchanged. No
code change, so earlier323 frontend tests/static/build remain timestamped, not
rerun. All mandatory product/release gates and GitHub hold preserved.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260928-paper-ledger-matrix.json>)
is outside Git.

## 2026-09-28 new V3 historical UI account and provider empty-state fix

Owned tmpfs quant_test/API18036/frontend15173 only: create a new historical
account through the in-app UI, dates2011-03-01..23/cash100000. EN switch preserves
form values; creation stays CREATED with no automatic start/data/orders/fills.
Actual walkthrough exposed incorrect Bar empty-state labels on A-share accounts:
shared detail page chose labels by data availability rather than provider type.
Fix only provider-specific headings/translated empty states; preserve legacy
AAPL copy and all financial code. New regression failed2/passed31 before fix,
then33 passed across both locales/all three providers; full frontend323/37files,
lint/typecheck passed. Vite129-module build passed in fresh cache output. Default
root-owned dist/cache permissions were not changed; no old files deleted.

Explicit UI start completed STOPPED/138events/20orders/six distinct-order fills.
EN/ZH show latest2011-03-23 cash81309.8134/equity99964.8134 versus plan-time
2011-03-22 cash100000/estimated requirement75191.75091 and next2011-03-23.
V3, historical-only warnings and snapshot distinction verified. Four real key
screenshots/checksums retained outside Git. Native Chrome unavailable in current
browser inventory; no bypass/retry. This is agent historical walkthrough, not
genuine novice, native zoom/speech, full visual matrix or lawful forward PASS.

Own tab closed/original ZH/system restored; freshly identified owned API/Vite
stopped/listeners absent, tmpfs test container stopped (disposable test data only).
Original main four services remain healthy/reachable; eight fingerprints match
reference and `.research` unchanged. GitHub five-day hold preserved until actual
recovery, not estimated date. Full goal/release remains incomplete.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260928-paper-provider-empty-state.json>)
is outside Git.

## 2026-09-28 V3 SQL persistence and actual graceful process restart

Previously optional real-archive test now ran in owned tmpfs quant_test: baseline
passed, strengthened paper API/plan compatibility41 tests passed with no skips.
Only existing test changed: V3/date guards, fresh manager via actual HTTP route,
saved-prefix equality and unchanged full financial-event comparison. Readonly
independent review found no blocking issue; final Ruff/format passed after an
equivalent response-assignment style fix. Production calculations unchanged.

Separate current-source backend18036 in test mode: new historical V3 account
paused at2011-03-22 with20 orders/zero fills/97 events. Verified own process
gracefully exited; a new process/lifespan reopened the same SQL DB. It stayed
PAUSED with the exact97-event checksum preserved, until explicit HTTP start.
Resume added only2011-03-23, produced six distinct-order fills and17 dated V3
plans; saved prefix/start time unchanged. Repeated start409 appended no event.
Owned API/test DB stopped after fresh identity checks; main eight fingerprints
still match reference, services HTTP200, `.research` unchanged. No formal/OOS run.

This closes a bounded V3 historical normal-process restart check, not abrupt
crash/power/database-loss/terminal-free login, real Chrome/novice or U7 forward.
All original product and external gates remain required; GitHub stays held.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260928-v3-sql-process-recovery.json>)
is outside Git.

## 2026-09-28 local runtime recovery and isolated backend verification

One supported normal Desktop start succeeded; original four Compose services
started without recreation/reset. PostgreSQL/backend healthy, Redis PONG,
API/frontend HTTP200 on configured8000/5173; Engine29.8.0/Compose5.5.1.
Original volumes and read-only research mount retained. Five paper sessions
remain STOPPED; all eight critical table count/sorted-row fingerprints match
the09-26 reference. Equality is not recovery of missing ledgers or a backup.

Owned tmpfs quant_test only:1012 passed/one optional historical archive skipped,
Ruff/544-format/mypy144 passed, upgrade/downgrade/upgrade/check passed. Three
Compose configs passed. Test container freshly verified then stopped; main
services remain running, no project data/image/volume deletion. No formal/OOS run.
In-app browser EN/ZH/EN saved historical result displays the snapshot-date
warning and preserves exact amounts; AX only, not actual Chrome visual/zoom
acceptance. Initial mouse no-effect remains unproven; keyboard opened the result.
Own tab closed/original locale restored/draft untouched. GitHub five-day hold
continues; actual recovery and exact-head CI still required. Full goal incomplete.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260928-runtime-sql-recovery.json>)
is outside Git.

## 2026-09-28 local login-trigger evidence, not full startup PASS

Windows reboot12:41local and current-user AtLogOn task12:41:15/result0 confirmed.
Existing action launched Docker backend02:41:16Z; menu-quit request02:41:50Z.
Second launch02:42:15Z later received actionMenuQuit12:53:21Z, followed by
ExitHealthyState12:53:26Z and backend exit. This establishes graceful menu exit,
not who initiated it or why. Earlier09-26 EOF-only case remains unexplained.
Current Docker absent and Compose unavailable; no current service/SQL/data
fingerprints or full M5 startup PASS. Readonly diagnosis only, no launcher,
task/setting change, reset or data deletion. Ask whether to restart and keep
Desktop running; preserve GitHub hold and all required U1-U8/M0-M5 gates.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260928-docker-login-quit-diagnosis.json>)
is outside Git.

## 2026-09-26 17:16 UTC current-head local frontend release checks

At e9e175e, all321 tests/37 files, ESLint, TypeScript and production Vite129-module
build passed. Official npm registry audit reported0 vulnerabilities; dependencies
unchanged. Build retained outside Git in /home/yuchen/.cache/qtp-release-check-fKelHx.
Initial shell PATH expansion failed before tests; corrected explicit Linux PATH
and actual terminal exit0 recorded, no claim from failed command.

Docker absent, Ubuntu running/docker-desktop stopped. No native PostgreSQL/Redis
available. Bounded Application crash-event query returned no matching Docker
events; latest host EOF/canceled streams still do not prove cause. User intentional
exit question pending; no launch loop or data deletion. Full backend SQL/runtime,
native accessibility/performance, forward and CI/release remain NOT_PROVEN.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-local-release-preflight.json>)
is outside Git; GitHub hold continues and full goal remains active.

## 2026-09-26 17:13 UTC bounded offline home responsive checkpoint

Actual Chrome home: four requested viewports1440x900/1280x800/1024x768/390x844
times EN/ZH and light/dark produced16 DOM geometry checks, no page horizontal
overflow, two truthful offline alerts, main controls>=40CSSpx. Five real JPEG
screenshots saved outside Git; initial PNG names corrected after magic-byte
verification, without reencoding. One delivered desktop image1188x891 rather
than1425x891 is a retained unproven scaling confound, not exact-width proof.
Extension overlays remain; no clean-profile or novice claim. Independent readonly
review of JSON and two actual screenshots found readable actions/errors and no
blocking overflow or fabricated online/results state; no live interaction review.

[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-offline-home-responsive.json>)
and [Chinese desktop screenshot](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/offline-home-zh-light-1440-20260926.jpg>)
are outside Git. Own tab closed, locale/theme/default viewport restored; freshly
verified own preview439 stopped, process/listener absent, persistent build retained.
Native200% zoom/speech/fullAA/p95/novice/SQL/runtime/forward NOT_PROVEN.
Docker absent17:13UTC; bounded log tails show canceled streams/EOF, not proven
fatal cause. User five-day GitHub estimate is not recovery proof: no push, remote
CI polling/retries, merge or release. Full U1-U8/M0-M5 remains incomplete.

## 2026-09-26 16:58 UTC historical paper integer request boundary

Six failing regressions proved the actual request union coerced true,20.0 and
string20 into integers for rebalance_sessions/maximum_holdings. The two existing
fields now require strict integers, matching the exploratory request. Valid
lower/upper/default counts and exact cash100000.123456789123456789 remain unchanged.
No accounting, runtime, saved account, plan version or ledger rewrite. Final126
pure backend tests, Ruff check/format320 and mypy144 passed. Independent readonly
review found no P0/P1: valid UI JSON and normalized saved-account recovery remain
compatible; it did not execute tests/DB/browser/network. Actual HTTP POST/SQL
persistence/browser submission NOT_RUN; frontend not rerun because unchanged.

Previous turn normally launched actual installed Chrome and inspected current
281e25b isolated frontend at15173: home explicitly reported service/data unavailable
in Chinese; semantic EN button switched the same real page to English. Native
window inspection was stopped by URL-confidence policy; no bypass, native200%
NOT_RUN, no screenshot obtained. This is not service or forward acceptance.
Fresh PID/start/command/cwd inspection identified only the owned preview489,
which was stopped with TERM; process/listener absence verified16:58UTC. Build
retained, no files/data deleted. Chrome remains open; Docker absent, main health
unverified. GitHub hold/full U1-U8 goal and external gates remain intact.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-paper-count-boundary.json>)
is outside Git.

## 2026-09-26 16:49 UTC saved plan date confidence and V3 metadata

Old saved plans do not prove their own account snapshot date. The shared research
and paper plan view now gives a bilingual unverified-history warning for missing
or mismatched dates; cash/equity become recorded values, not claimed plan-time
values. Original amounts, candidates and risk decisions remain visible and intact.
No executable action is added. New plans carry their guarded Shanghai snapshot
date; missing accounts carry null. Latest portfolio date cannot validate an older
rebalance plan.

New paper events use V3. V1/V2 saved checkpoints retain their exact old payloads
without the new field; V2 golden hashes were captured from unmodified ddc1f24.
Strict whole-event comparison, mixed-version resume, duplicate prevention and
cash-tamper rejection remain. Earlier V2-only entries below are timestamped history,
not the current new-event contract. No saved record or accounting is rewritten.

Seven baseline warning tests failed before repair. Final117 offline backend and
321 full frontend tests/37 files, Ruff check/format320, mypy144, ESLint, types,
changed-file Prettier and fresh Vite129-module build passed. An intermediate page
selector ambiguity was corrected to require both visible matching dates. Readonly
independent review found no P0/P1. SQL persistence/new V3 API creation and actual
Chrome NOT_RUN; current services/DB NOT_VERIFIED. GitHub remains held. This is
bounded offline evidence, not full U6/U7 or release acceptance.
[Evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-plan-date-warning.json>)
is outside Git. Full original goal remains active with all external gates intact.

## 2026-09-26 16:36 UTC current plan snapshot and legacy checkpoint compatibility

An empty session can retain the prior portfolio snapshot. The shared plan builder
now requires snapshot date = as-of date in Asia/Shanghai; otherwise it returns
ACCOUNT_SNAPSHOT_UNAVAILABLE with no account/candidates/cash requirement, without
mutating the delta, engine or financial ledger. The failing baseline and UTC
cross-midnight positive control are preserved in the regression test.

Readonly review identified a compatibility risk before commit: recalculating an
old V1 paused account would change its saved projection and break strict replay.
Saved cursor-side events now rebuild their own V1/V2 versions; new events always
use V2, including never-started V1 accounts. Original pre-plan accounts remain
without plans. Entire event-payload equality remains mandatory; altered cash
fails without new market events. Mixed-version second resume produces no duplicate
events. Old V1 projections match the unmodified e2a3aa9 builder field-for-field,
with a golden SHA anchor for its stale-date case. Old records are not rewritten;
their prior-date account may be affected by this known defect, not accepted as a
current executable plan. Frontend accepts strict V1/V2 strings and rejects unknown
or array versions while preserving exact money strings.

115 offline backend tests, full frontend312/36 files, Ruff check/format320,
mypy144, ESLint, types, changed-file Prettier and fresh Vite129-module build passed.
Actual _run and fixture runtime were exercised with SQL boundaries mocked, not
database persistence acceptance. Independent final readonly review found no P0/P1;
its suggested unstarted-V1 test was added and passed. Docker/Chrome processes are
absent; browser inventory has only an empty in-app browser. Actual Chrome and full
backend SQL suite NOT_RUN; current retained DB/service health NOT_VERIFIED.
No runtime/account/provider/formal study/OOS or GitHub action. GitHub hold and all
U1–U8/M0–M5 requirements remain; this is not full U6/U7 or release acceptance.
[Offline evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-plan-snapshot-checkpoint.json>)
is outside Git. First scratch build failed shell argument transport; explicit
observed scratch path corrected it without changing original assets/permissions.

## 2026-09-26 16:16 UTC legacy submission keeps locale, draft and retry identity

Eight baseline regressions exposed stale translated local/API errors and missing
typed permission/unavailable/timeout/offline guidance. Translate keys/typed errors
at render without changing request construction, financial strings or submit locks.
Independent review rejected an intermediate use of GET ErrorPanel: its reload
action would erase the POST draft and retry key. Two new timeout/offline regressions
first failed on that action. Keep the existing form and Run button, explain the
unknown outcome and checking history in another tab; no destructive reload action.

Final focused27/full311 frontend tests, ESLint, types, changed-file Prettier and
fresh scratch production build129 modules passed; independent four-file readonly
review found no blocker. Same settings resend identical body/key after500/408/
offline; editing creates a new key. No backend change/suite or GitHub CI run.

Chrome connection is currently absent: **actual Chrome NOT_RUN**. In-app browser
keyboard-only local invalid-period check passed ZH→EN→ZH with exact fractional
cash retained. Native full-page English image inspected inline, not a saved media
deliverable. Mouse locator clicks had no observed effect; cause unproven, not mouse
acceptance. Only deterministic invalid inputs submitted, no valid run/account/API
mutation. Own tab closed and owned preview processes stopped, port15173 clear.
Docker remains absent and current service/DB health unverified. GitHub five-day
user hold, full U1–U8/M0–M5 and all existing gates remain unchanged/incomplete.
[Bounded evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-legacy-submission-errors.json>)
is outside Git; component fixtures are not operational or forward acceptance.

## 2026-09-26 16:02 UTC failed account commands keep their context and locale

With Docker unavailable, existing WSL Node24.20 and matching locked frontend
dependencies enabled offline validation, no install. Three API503 fixture cases
first failed: start/pause/stop errors retained English after Chinese switch and
were hidden inside a generic data-load diagnostic. At their shared command
boundary store the existing key, render a visible native alert with the specific
failure. Stream errors retain independent typed ErrorPanel; neither snapshot,
financial/API behavior nor pending/finally/retry semantics changed.

Focused31/full305 frontend tests passed, ESLint/types/Prettier passed. First npm
invocation failed inherited PATH quoting; used observed absolute Node executable.
Default build failed EACCES on root-owned dist/assets. Same Vite production build
passed129 modules in a freshly created scratch output, no chown/manual deletion or
original asset overwrite. Readonly independent final two-file review found no
bounded blocker. Backend unchanged/not rerun; CI held. Actual Chrome command-error
recheck **NOT_RUN** while Docker absent; mock commands do not act on retained
accounts or prove U7 runtime/forward acceptance. No account/provider/DB/OOS work.

Bounded Windows event reads found no matching Docker/WSL fault/shutdown event in
the observed interval, not proof of cause. Docker ownership question unanswered;
no second launch/reset/deletion. Full product acceptance/release remains incomplete.
[Offline regression/build/review evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-paper-command-errors.json>)
is outside Git. Subsequent healthy runtime must supply real browser evidence.

## 2026-09-26 historical account configuration and live error locale

Disposable API regression proved historical create accepted exact cash above the
existing research engine limit and only failed on startup. Reuse the shared
request model before persistence; invalid create now422 with sanitized text,
exactly1e12 remains CREATED (never started). Synthetic/idempotent paths preserved.
Frontend uses the existing exact comparator with trim, not Number. Independent
readonly review found the whitespace bypass; its regression first failed then
passed. Chrome found error text retained the prior locale; all create errors now
store translation keys and translate at render. Immediate locale regression first
failed; final28 paper frontend cases passed. Actual Chrome English→Chinese alert
changed without resubmitting, exact fractional input preserved; native full-page
image inspected inline, restoredZH/dark and closed own tab. No account created.

Full backend995 passed/1 optional unmounted archive skipped; Ruff543 format and
mypy144 passed. Full final frontend test/lint/type/build returned0; compact output
did not retain final total, not inferred. Preceding frontend301 passed. Eight DB
fingerprints matched at08:05UTC, `.research` unchanged. No formal study or feed.

Runtime changed during continuation: normal installed Docker4.92.0 launch briefly
restored29.8.0/Compose5.5.1 with original12 containers/9 volumes and PostgreSQL mount.
Main Compose startup then lost its handle; at15:54UTC Docker processes absent again
and Ubuntu reported docker unavailable. Latest backend log15:53:31Z ends in event
stream EOF, cause unproven. No reset/deletion/repeated launch. Final service/data
recheck and owned tmpfs-test cleanup **not verified**, not healthy recovery PASS.
GitHub remains held; no push/CI/merge/release. All full product gates remain open.

[Bounded repair and runtime evidence](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-paper-configuration-boundary.json>)
is outside Git. Local tests do not establish forward source rights, lost-ledger
recovery, independent backup, Windows login persistence or release acceptance.

## 2026-09-26 07:51 UTC observation payload must match its immutable receipt

U5's read path verified bundle checksums but trusted the separate PostgreSQL
observation index. A new disposable-DB regression proved that an INSERT could
reference a valid receipt yet introduce an observation absent from that receipt;
the existing append-only UPDATE/DELETE triggers did not prevent this. Preserve
those triggers and test-DB guard. Reuse the same verified Parquet read plus
existing canonical SHA256, binding receipt/security/date and exact JSON payload.
Receipt metadata also matches its original manifest identity/provider/UTC time.
No schema, authority promotion, price calculation or frozen asset modification.

Five negative variants cover date, price, executable flag, security identity and
numeric0 versus booleanfalse (Python dictionary equality alone was insufficient,
found by independent read-only review). API returns422 with the stable integrity
code; subsequent incremental acquisition stops before another provider call.
Final focused56/full backend994 passed,1 optional archive skip; Ruff/all543 format
and mypy144 passed. Initial long-line/type-check failures were corrected, not
ignored. Frontend unchanged, suite not rerun; remote CI not run during human hold.

New source loaded in a read-only audit verified all6 retained receipts/observations,
all non-executable. Main backend normal restart; all5 accounts were STOPPED and
queues terminal first. Immediate health curl reset was startup transient; later
health200. Actual Chrome153 ZH/EN reopened existing four-board task, exact cached
rows and receipt IDs plus non-execution/rights warnings. Final-code restart/reload
returned the original Chinese candidate row, no console errors. Native English
table image inspected inline, no local image artifact claimed. Locale restored,
own tab closed. Eight critical DB fingerprints unchanged; frozen research clean.
Explicit owned quant_test PostgreSQL stopped, no volume/data/image deletion.

[Reproduction/test/browser/safety summary](<C:/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m4/20260926-receipt-observation-integrity.json>)
is outside Git. Actual U7 request union/manager still has only replay, simulated
A-share and historical A-share providers: licensed new-market adapter and its
after-start real receipt/plan/constrained processing remain **NOT_IMPLEMENTED /
NOT_ACCEPTED**, not just an unrun UI test. No placeholder adapter or feed right
inferred. This fix reduces a real U5 defect, not a full product/release PASS.

## 2026-09-26 07:36 UTC native event delivery diagnosis, not a p95 pass

Three fresh main-app strategy documents at actual958×903 each opened the native
drawer on the first mouse activation. The prior isolated anomaly was not reproduced;
cause unproven, no speculative code patch or unconditional activation promotion.

Reused existing localhost-only GET-forward harness in owned/tmp/qtp-native-qa-cGGYmp.
Copied default build still called localhost8000 and failed from5182 due the configured
origin boundary; isolated VITE_API_BASE_URL=/ build restored same-origin proxy.
Main backend CORS/settings and main dev app were not changed. tsc/Vite build and
native recorder JS syntax passed; full suites not rerun for QA-only instrumentation.

New protocol has no MutationObserver or DOM publication during the measured click;
collection is an explicit button activated only after saved result+4.67% appears.
Actual Chrome153, ZH/dark1440×900, no-store resources200 with positive transfer
bytes (main451445/lazy25029), not cold backend/OS/data. Primary1 matched trusted
pointerdown/up/click interaction157, all24ms. Primary2 native absent, including
same-page recollection: unknown, not zero. Stop incomplete sampling, no p95.

Changed input to documented AX click, added full native-event/event-count diagnostics.
Control interaction3679 had trusted input6985.8ms/click6987.6ms, result ready and
native/allNative empty before capture, despite pointerdown/up count1 and click count2
(second click belongs to collector). After a native screenshot and recollection,
the SAME interaction appeared: pointerdown13312ms, pointerup/click13304ms;
click processing6991.6−6988.0=3.6ms. The capture/collection happened after the
original input; this is evidence of late presentation/delivery, not causal proof
that screenshot, occlusion or app code is its source. [W3C Event Timing](https://www.w3.org/TR/event-timing/)
distinguishes native rendering duration from synchronous event processing.
Earlier3040ms remains. Empty native output cannot be classified under16 from DOM
readiness. Immediate output publication is not the sole explanation. No app
performance PASS/FAIL, complete protocol, native p95 or all-product promotion.

Collector first mouse activation also produced no output; Enter collected it.
Visible raw JSON initially caused QA-only page overflow; retained recorder wraps
it for future use. Do not patch app styles for this measurement artifact. Initial
cross-shell variable copy resolved to/./ and failed permission checks; used explicit
mktemp result/separate literal copies instead, no broad deletion. A mistakenly
targeted TSX node-check failed on extension; corrected JS syntax check passed.

Evidence outside Git: `product-evidence/v1.2/m4/20260926-native-delivery-diagnostic.json`
and recorder20260926-native-route-deferred.js, SHA256
8235d331bda03f72c4f50164ee41079d0fddbe181242655bc814c7bf9d2e300a.
Owned PID40976/start17:28:48/path verified before TERM; session71597 terminal,
5182 listener absent; build/evidence retained, temporary viewport/tab cleaned.
Four main services and eight critical DB fingerprints unchanged; frozen research
clean; no provider acquisition/financial write/GitHub operation. User asked to
confirm actual Chrome foreground/unoccluded; not yet verified. Full goal/gates remain.

## 2026-09-26 07:22 UTC strategy layout evidence, activation anomaly retained

Actual Chrome checked16 combinations of ZH/EN, dark/light and the four required
dimensions, each with list and native drawer open (32 geometry states). The
single registered strategy retained six plain-language sections covering rules,
cycle, risks, configuration, data and weak existing evidence. List document
client/scroll widths matched1425/1265/1009/375; drawer widths matched523 desktop
and358 mobile, no measured paragraph/heading overflow. Card trigger42px;
drawer Close/Open40px and Configure42px. Sampled drawer text contrast minimum
dark7.653/light6.058. Mobile EN/light native Tab reached Configure with2px outline,
Escape returned Explore strategy. Independent detail URL loaded all six sections.

Do not hide the first activation anomaly: initial native locator mouse click left
no drawer/hash and main focused, confirmed by a later read. No console error.
Enter then opened it, and a later stable mouse click plus sixteen matrix Enter
opens succeeded. Cause remains unproven; no speculative shared Dialog/router fix
was made. Strategy quality remains PARTIAL, not unconditional activation PASS.
The attempted browser history read was unavailable in the DOM-only scope; no
fallback to hidden state/CDP or mutation. Missing guessed file paths were corrected
through rg discovery; those read-command failures were not failed app tests.

Representative actual desktop ZH/dark and mobile EN/light drawer and independent
detail images inspected inline, not saved local PNGs or all32 pixel-reviewed images.
Original ZH/dark restored; owned viewport/tab cleaned. Eight critical DB counts/
fingerprints and frozen research unchanged. No code, suites, provider, financial,
runtime or GitHub operations. Evidence outside Git:
`product-evidence/v1.2/m4/20260926-strategy-quality.json`.

Two recent units added bounded proof but no new completed full user flow or code
defect reduction. Change priority now to first-activation/cold-response diagnosis,
not another generic matrix. Keep native3040ms cold anomaly and p95 unknown; DOM/
rAF availability cannot prove presentation. Full U1–U8/M0–M5 and all gates remain.

## 2026-09-26 07:16 UTC bounded Task Center whole-page quality

Actual Chrome checked Task Center in ZH/EN × dark/light ×
1440×900/1280×800/1024×768/390×844, using the existing eight research
tasks and four raw-data request tasks. All16 cases retained twelve task rows,
two translated named regions and descriptive task links. Document client/scroll
widths matched1425/1265/1009/375; measured paragraphs/headings/list rows had no
horizontal overflow. All twelve task links were42px high. Sampled main body,
status and timestamp text contrast minimum7.653 dark /5.652 light; timestamps
12.5px. No actual defect found; no code, dependencies or financial behavior changed.

Native EN/light390 Tab from Refresh reached the first descriptive research-task
link with2px outline. Full-page EN/light390 and ZH/dark1440 images inspected
inline, not saved local PNGs or all16 pixel-reviewed images. Original ZH/dark
restored, temporary viewport reset and owned tab closed. Eight critical retained
DB counts/fingerprints still match; no provider request/retry, new research,
paper lifecycle, runtime change or GitHub access. Suites not rerun for proof-only
documentation. This is not full speech/native200%/AA/novice/performance acceptance.

Evidence outside Git: `product-evidence/v1.2/m4/20260926-task-center-matrix.json`.
User-reported GitHub recovery remains estimated2026-10-01, unverified; no push/CI
polling/release. All original U1–U8/M0–M5 and external gates remain required.

## 2026-09-26 07:06 UTC truthful shared modes and Help/Settings matrix

Actual Help described forward processing as if it were an available capability,
without its current unavailability, unlike Paper and the manuals. Both callers
use ModeGuide: Help and the optional Workbench dialog. Two bilingual regressions
failed first; the shared copy now says “Not available yet” / “尚未开放” and retains
lawful verified source, deliberate start and genuinely new completed sessions
after start. Historical backfill/2030 remains explicitly insufficient. No forward
capability was removed or promoted, no execution/financial calculation changed.

Actual Chrome checked 32 geometry cases: Help/Settings × ZH/EN × dark/light ×
1440×900/1280×800/1024×768/390×844. Document client/scroll widths both
1425/1265/1009/375; no measured visible main paragraph/heading/label/summary
overflow. All four Help answers were expanded; new forward warning present in
all16 Help cases. Help main controls min42px; Settings min40px. Motion/colors/
price remained system/red-up/raw across language/theme changes, saved-state copy
translated. Representative full-page images inspected: EN/light390 and ZH/dark
desktop on both pages, plus ZH/light390 home dialog. They are inline native tool
images, not claimed saved local PNGs or complete six-surface media delivery.

Mobile native ArrowDown changed Motion to off, root flag off and select focus
ring2px; Tab reached market-color select with2px ring. Workbench dialog remained
native open/modal,349px client/scroll, animation none/transition0s; shared warning
visible in EN/ZH. Tab reached the acknowledgment button; Escape closed and restored
trigger focus. Original ZH/dark/system/red-up/raw restored, viewport reset and
owned tab closed. This is bounded explicit-motion-off behavior, not OS-motion,
screen-reader, all business paths, native200%, full visual/AA or novice acceptance.

Evidence: `product-evidence/v1.2/m4/20260926-help-settings-matrix.json` outside Git.
Tooling failures retained: filtered mutable disclosure selectors lost their nth
target; switched to stable summaries + observed parent state. Dialog-role evaluate
timed out despite visible snapshot; native DOM diagnosed open/modal without
restarting or duplicating the action. No workaround of blocked file-video policy.

Focused8 and full frontend300/36files, lint/typecheck/build PASS; final changed-file
Prettier/diff PASS (one existing tasksIntro wrapping-only formatting repair).
Independent read-only review approved, without independently rerunning tests.
Backend not rerun for copy-only change; eight critical DB fingerprints unchanged,
`.research` clean. No provider/request/job/account/runtime/GitHub mutation. All
broader integrity, forward, backup, login, media, performance and CI/release gates
remain; U8-I18N/QA-VISUAL/QA-A11Y stay IN_PROGRESS, PRODUCT_GOAL_COMPLETE=false.

## 2026-09-26 06:52 UTC delivery completion-gap audit

Read the complete original objective, PRODUCT_MASTER, both guides, state and
the requirement matrix. This is a gap audit, not a new full runtime acceptance.
Code baseline `a3b679e`, clean at entry, ahead12 of cached origin; no remote
query during the user-reported five-day GitHub hold. Four Compose services
running; PostgreSQL/backend/Redis healthy. No competing writer/test/restore seen.

All 73 distinct local media targets in this ledger exist as native Windows files.
Windows reads through their WSL `/mnt/c` UNC aliases returned AccessDenied;
WSL can read the sampled file. Existence therefore does not prove cross-client
link usability. Outside-Git `product-evidence/v1.2/DELIVERY_INDEX.md` now has
18 checked native-path file links, app/manual links and explicit scope/gaps.
It is a local delivery aid, not another authoritative project-state file.

Both principal WebM SHA-256 hashes match the original records:
historical walkthrough `B85F5595830D884BBC88D6C34AD1B824575DAFA199953DD42D7EA18F51695C1F`;
isolated synthetic flow `947B3233284E55C45BF2D515B81779BFA3D261C538344D1BFB48BB0F8102FFC8`.
Durations/playability remain prior evidence: Browser Use URL policy blocked local
`file:` video navigation; no hosting/alternate browser/CDP workaround attempted.
Direct image inspection found the M5 home still loading/fading. The index marks
this limitation and distinguishes the inspected, loaded earlier M1 home; neither
is promoted to current full visual proof. Original files remain unchanged.

| Requirement | Existing evidence and remaining gap |
|---|---|
| U1/U2 | START/DEMO/STRATEGY bounded prior evidence retained. Live strategy drawer/full page matched manual names; no current novice/full visual claim. |
| U3 | WIZARD/JOB/RECOVER prior historical and isolated synthetic evidence includes idempotency/cancel/failure/crash retry. ISOLATE remains incomplete with missing original ledgers. No new tasks/formal studies. |
| U4 | RESULT/COMPARE/EXPORT prior acceptance retained. Three-study geometry is bounded; do not reopen accepted Chrome downloads from an older suppression observation. |
| U5/U6 | Cached history/historical plans have bounded evidence; current source authority, lawful new data and new-market plans remain incomplete. Manuals now cover cache/history/refresh/candidate limits/date distinctions, matching live ZH/EN data-center headings. No provider request. |
| U7 | Synthetic/history are not genuine forward. Missing original paper ledgers, rights and after-start arrival/processing prevent completion. Stopped-account image is not lifecycle recording. |
| U8, UX-DETAIL/VIEWS/CHART/ERROR | Prior cases retained; full cross-page translation/focus/scroll/error/accessibility coverage not collectively proven. Manuals now explain return/drawdown/win rate/benchmark/non-fills without profitability claims. |
| Design and QA-VISUAL/A11Y/PERF | Four sizes/two themes/two locales have bounded cases, not whole-product proof. Native200%/OS motion/speech/novice and genuine cold visible-response p95 remain unproven; proxies cannot promote gates. |
| QA-ENGINE/REVIEW/RELEASE and safety | Prior frontend298/lint/types/build belong to prior code unit, not rerun now. Exact-head full suites/migrations/restart/compatibility/CI still required for release. Eight critical DB fingerprints match prior checkpoint; `.research` unchanged; no new dependencies/calculation, destructive action, live order or authority redo. |
| M0–M5 | M0 baseline exists. M1/M2 real visible flows need broader acceptance; M3 lacks required forward mode; M4 integrity/quality and M5 delivery/publication remain open. No milestone promoted. |

Six mandatory walkthroughs: (1) clean synthetic and actual historical strategy→job→
result have prior bounded proof, not a novice test; (2) navigation/refresh/duplicate/
cancel/failure have isolated evidence; (3) result→reason→comparison→historical plan
has bounded proof, new-market chain incomplete; (4) mode/date samples are not a
full-page matrix; (5) isolated synthetic restart/WebSocket checks do not recover
missing original accounts or prove forward processing; (6) offline/permission/
timeout/no-match/no-trade faults exist, broader coverage remains. No mock substitute.

Final deliverables: (1) app/manual recovery available, next genuine login NOT_RUN;
(2) before/after and two recordings PARTIAL: missing standalone old orientation/
comparison/paper evidence must be reconciled with actual baseline, not fabricated;
comparison/account-lifecycle recordings remain; (3) per-flow local proof exists,
exact-head CI blocked; (4) modes/dates/limits in guides/index; (5) branch/PR32 exist,
no v1.2.0 merge/release/rehearsed rollback completion; (6) ZH/EN manuals expanded,
novice/operator review remains. M5 FAIL; PRODUCT_GOAL_COMPLETE=false.

Next safe work: settled current six-surface screenshots/key interactions using
supported artifact capture only, then missing whole-page visual/accessibility
cases. If durable recording capture is unavailable, state that tooling gap and
advance independent quality work. Do not repeat accepted tables/export/recovery,
trigger held GitHub jobs, fake forward data or stop solely on the GitHub hold.

## 2026-09-26 06:40 UTC market/data table keyboard context repaired

Actual Chrome confirmed three remaining unnamed tables: cached security search,
historical exact observations and raw candidate observations. Search/exact
focusable containers had labels but no region role; candidate had only a scroll
hint. Reused existing translated titles for native table names, added two region
roles, and distinguished nested search/candidate regions with the existing hint.
No component, dependency, layout, request, price formatting or finance change.
Prettier also expanded two existing date callback objects without semantic change.

Two new regressions fail before repair for missing named tables. Final focused28
and full frontend298/36files, lint/types/build, changed-filePrettier/diff PASS.
Tests cover EN/ZH names/containment/tabindex and preserved precise strings/no new
acquisition. Initial host WSL npm was unavailable; switched to the existing
Compose frontend Node24.21.0 runtime, no installation. Independent read-only
review approved the final diff without claiming complete AA.

Real Chrome ZH/dark and EN/light:20 cached search rows and50 exact rows remain;
Tab enters inspect600000/first date2011-01-04; Escape returns dialog focus to
its exact trigger. At390×844, document375/375 and dialog334/334 have no overflow;
named local search/exact scroll regions are312/727 and263/1075. Native ArrowRight
settles at40px (immediate read0),3px focus; visible exact-table segment inspected.
This is not a whole-page screenshot or actual screen-reader speech.

Existing four-board update164c947d remains3/3 requests, cache1/new3/available4/gaps0.
Its candidate region/table names translate; mobile307/1215 locally scrolls40px
with2px focus and document375/375. Native Tab reaches receipt summary. Selecting
already-cached300750 and switching EN→ZH retains2026-09-22 raw OHLC298/308.69/
297.74/304.63, volume47381066, amount14476584269.96 and exact receipt identity.
Candidate/unverified/non-executable warnings remain; no provider request.

Eight critical DB mutation fingerprints and .research unchanged; API/frontend200,
RedisPONG. RestoredZH/dark, resetviewport, closed owned tab; no runtime restart,
new financial/session/study/provider write or GitHub action. Evidence outside Git:
product-evidence/v1.2/m4/20260926-market-table-keyboard.json. Full U1–U8/M0–M5,
nativezoom/speech/novice/performance/startup/data-rights/backup/ledger/CI/release
gates remain open. Next audit the whole objective against evidence before selecting
another missing case, rather than repeating accepted table checks.

## 2026-09-26 06:31 UTC three-study responsive comparison closure

Actual Chrome selected three existing successful historical studies from the
list: U6 plan preview, U4 March 2011 and M1 lifecycle recovery. Four required
viewport sizes × two languages × two themes produced16 geometry checks: no
document overflow, four columns, seven metric rows/six condition rows and no
cell-content overflow. Document clients1425/1265/1009/375 equal scroll widths;
both table regions are1074/938/714/307 wide, with680px local scroll on mobile.
Table and scroll-region names translate together.

Actual screenshot segments covered ZH dark desktop/header and mobile conditions,
ZH light mobile third-study header/all seven metric rows, EN dark1024 long
condition values and EN light1280 all three condition headers. Native mobile
Tab/Shift+Tab reaches the next region/third header and reveals it at373px local
scroll; ArrowRight settles at40px. Both focus outlines are3px. Fresh state and
separate capture avoided accepting stale frames. These segments are not all16
full visual screenshots or full AA/native200pct/speech evidence.

All seven full-precision metrics match the three read-only result APIs, including
equities104666.94836/99528.8134/99092.83177 and costs96.05164/30.1866/20.16823;
EN→ZH retains precision state and values. Different periods visibly warn this
is not a controlled comparison; actual execution/fee fingerprints still require
metadata review. No ranking, new run or financial recomputation.

Eight critical DB mutation fingerprints match the prior checkpoint and .research
has no diff. RestoredZH/dark, resetviewport and closed owned QA tab. No product
code change or test rerun; preceding296 frontend tests are historical evidence,
not newly run. No provider/runtime/GitHub/financial writes. Evidence outside Git:
product-evidence/v1.2/m4/20260926-three-study-responsive-matrix.json. Full U1–U8,
M4/M5 and external/release gates remain incomplete; goal remains active.

## 2026-09-26 06:21 UTC research control-boundary override repaired

Actual Chrome found that the grouped research input/select rule overrode the
global --field-border with --border. Light boundaries measured1.314:1 against
the white input and1.173:1 against its raised panel. Changed only that shared
rule to the existing field token; no new CSS system, dimensions, focus,
disabled behavior, data or calculation changes. Selector callers include the
wizard, displayed-date filters, chart date, CSV selection and comparison URL.

Eight computed field samples now measure light4.032/3.597 and dark3.992/3.412
against inner/outer backgrounds, with heights44–48.5px. Actual result-page
date/chart/export selectors inherit the token; comparison URL was reviewed,
not browser-rechecked this turn. The existing32-row plan has sampled text
minima light5.405/dark6.541 and3px focus ratios5.946/6.600; native Tab moves
to provenance summary. Independent read-only reviewer approved the shared fix.
Full frontend296/36files, lint/types/build/Prettier/diff checks pass.

Draft name, exact cash123456.789000000000001 and dates2011-01-04/2011-06-30
were not edited and survived theme switches. The page's existing autosave may
refresh timestamps on mount/unload; storage is not claimed byte-identical.
390px viewport measured375px client/scroll, no document overflow; the returned
mobile screenshot showed prior desktop composition and is not mobile visual
proof. An immediate light-plan screenshot similarly showed a stale dark frame;
discarded it, then fresh DOM/separate capture verified actual light rendering.

Eight critical DB fingerprints and frozen .research remain unchanged. No
runtime restart, new study/account/order/provider acquisition or GitHub action.
ZH/dark restored, viewport reset and two owned tabs closed. This is a bounded
computed contrast/keyboard check, not full AA, speech, zoom or all-page visual
acceptance. Evidence: product-evidence/v1.2/m4/20260926-research-control-contrast.json.
Full product and external gates remain open.

## 2026-09-26 06:14 UTC two-study comparison responsive matrix

Real Chrome on approved localhost:5173 compared two existing saved historical
studies (d9f27183,5f26f84f), without creating studies or requests to vendors.
Checked 1440x900,1280x800,1024x768,390x844 in both languages and both themes:
16 geometry cases had document scroll width equal to client width. Desktop
clients were1425/1265/1009px; mobile375px. Named tables remained7 metric and6
condition rows; desktop regions1074/938/714px, mobile307px with680px local
table width. Screenshots of visible top/table/limits segments were reviewed.
This is not every scroll position, three-study responsiveness, actual200pct
zoom, screen-reader speech, full AA or all-page QA-VISUAL completion.

On mobile the native ArrowRight moved the precise metric table from0 to40px
(max373px), retained named-region focus and3px outline, without moving the
whole document horizontally. Full-precision final equities104666.94836 and
99528.8134 and costs96.05164/30.1866 match the current authoritative result
API; language change retains the checked precision setting and exact values.
Trading-period differences and non-recommendation warnings remain present.

Retained tool failures: full-page and clipped screenshot calls each timed out.
Normal screenshots succeeded; one immediate ENdark1440 capture showed the
prior light/mobile frame and was not accepted as dark evidence. Fresh DOM
Dark-selected/rootTheme dark/width1440, then a separate screenshot, confirmed
the correct desktop view. Mobile does not expose the topbar theme selector;
after a no-match, fresh DOM was inspected and the actual desktop selector used
before resizing. No hidden-state writes, browser reset or app restart.

The later U4-EXPORT row already contains successful real-Chrome download
evidence, so older in-app-browser failures were not repeated or reclassified.
No implementation changed; previous frontend296/lint/type/build results are
previous-turn evidence, not a new test run. Eight critical table fingerprints
remain unchanged; frozen .research has no diff. Restored ZH/dark, reset viewport,
closed owned tab; user main tab/draft unchanged. No GitHub push/CI retry.
Evidence: product-evidence/v1.2/m4/20260926-comparison-responsive-matrix.json.
Full product and external gates remain open.

## 2026-09-26 06:06 UTC research table context and repeated date linkage

Eight research scroll regions and tables now reuse the existing translated
visible titles; the plan inner scroll region remains distinct from its outer
section. Native table headers, bounded pagination and exact server strings
remain unchanged. Actual Chrome on approved localhost:5173 verified EN/light
and ZH/dark context, keyboard focus (3px outline), comparison native Tab into
study links and horizontal ArrowRight scrolling (0 to 32px). Comparison uses
two existing saved historical results and still warns that trading periods
differ; no new research run was created.

A real existing-data defect was reproduced: an already-applied single-date
range did not reopen trades/holdings on Show; repeated Show after manual
collapse also did not reopen them. A local explicit-action counter now resets
only bounded detail collections on each Show action. The persistent filter
section keeps focus, manual collapse still works, and language changes do not
remount the collections. Chrome verified 2011-03-22 holdings with 16 positions
and unchanged full-period metrics. Regression assertions failed before fixes;
all 296 frontend tests across 36 files plus lint/typecheck/build/Prettier pass.

Initial browser blank-page evidence showed a served empty BacktestHistoryPage
module despite its intact on-disk export. Restarted only the frontend once;
the frontend then served the module and worked. A transient formatter/cache
interaction is a hypothesis, not established root cause. A test-only invalid
Testing Library exact option caused tsc failure and was removed; strict string
name assertions were retained. No backend, PostgreSQL or Redis restart.

Eight critical table counts and sorted-row MD5 fingerprints are unchanged;
this is a mutation check, not a backup or proof of historical completeness.
API health 200, Redis PONG, PostgreSQL/backend healthy. Frozen .research
unchanged; no account/order/study/provider write, push, CI retry or merge.
Restored Chinese/dark and closed the temporary Chrome tab. Read-only reviewer
approved the final semantic and repeated-action changes.

Evidence: product-evidence/v1.2/m4/20260926-research-table-keyboard.json.
Bounded verification only: actual screen-reader speech, native 200% zoom,
OS reduced motion, novice acceptance, full performance/release gates remain
open. GitHub recovery remains user-estimated 2026-10-01, unverified.

## 2026-09-26 05:46 UTC stable asynchronous pagination and date-link focus

Closed the previously observed BODY-focus defect with the existing shared
Pagination component: synchronous user-action focus on a named native group,
retained through pending/error/success, guarded busy/unknown controls, and no
delayed autofocus or stale financial data. All 17 asynchronous sites moved
outside resource-content branches; four client-side sites reuse the same contract.
Date activity and clear actions focus the persistent parent filter before the
keyed collections reset. Existing request identity isolation is unchanged.

The original two regressions failed before the repair. Added checks cover pending
and disabled last-page Next, error/retry, a moved focus not being stolen, locale,
unmount, independent pagers, actual stateful client boundaries and obsolete job
completion after replacement. Full frontend: 294/294 across 36 files; lint,
TypeScript and production build PASS. Independent read-only all-caller review
found no release-critical defect; its two missing regressions were added and passed.

Actual Chrome on original approved 5173, saved 293-session result: Chinese/dark
and English/light Next retains DIV group focus both while busy and after loading;
101–200 and 201–293 ranges correct, last Next disabled, Tab reaches Previous.
Date activity/clear retains named SECTION focus, then Tab reaches native first
date input. Both focus outlines are 2px. Market search similarly retains focus
through loading and 21–40 of 5431; independent watchlist stays 1–1 of 1.
This is bounded agent-operated keyboard evidence, not screen-reader speech or
full WCAG AA. Research exact-table landmarks, native zoom/motion and full matrix
remain open. Evidence: external product-evidence/v1.2/m4/20260926-pagination-focus.json.

Chinese/dark restored; only owned tab closed. No service restart, new study,
account, financial/provider request or research change. Eight retained table
fingerprints match; API200, Redis PONG and main Compose healthy. GitHub remains
user-reported unavailable for five days; the estimate is not verified recovery.
Local commits only; no push/CI retry, merge or release. Full product gates remain open.

## 2026-09-26 05:27 UTC bounded chart contrast/keyboard; async focus defect found

Actual Chrome on approved5173, existing historical result a2770b6, native958x903
viewport (no override), ZH/dark and EN/light. Computed essential SVG colors against
the first opaque plot panel, with all ancestor opacity1/background-image none,
meet unrounded3:1: dark minimum6.540636911463896, light5.405261175460344.
This covers equity/benchmark/drawdown/selected vertical/point versus plot
background only, not crossings, native checkbox tick/menu arrow, every control,
full text contrast or complete AA. Decorative axes were not required graphics.
Method: [W3C non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html).

Native Home/ArrowDown/End date selection updates exact strings and vertical
marker; benchmark Space removes/restores curve/legend/readout without changing
date. Tab date→activity→exact-data summary→scroll container→first date button;
Enter disclosure/date selection retains focus, aria-pressed and matching select.
Date focus2px, activity/summary/table/date-button3px. Locale/theme preserves
selected date and disclosure. Readout polite/atomic roles verified, not speech.
Table has headers/buttons but unnamed table/generic scroll DIV remains a
separate semantic-navigation gap, not full table-landmark acceptance.

Actual pages100/100/93 and last Next disabled; inspect2010-11-05 links one point,
opens Trades/holdings with genuine dated all-cash snapshot and explanatory empty
trades. Full-run metric text remains unchanged through page/date display changes.
However Next loading unmounts its focused button; after both loads activeElement
BODY. Inspect-date's keyed subtree also remounts and loses activity focus. This
is REPRODUCED_NOT_FIXED, not keyboard PASS. Root cause is intentional resource
identity reset plus conditionally mounted controls. Read-only review inspected
all21 Pagination sites (17 async/server,4 local/client) and recommends a stable
native pager anchor/busy contract, not retaining stale rows or global focus state.
Keyed date-link requires separate persistent-parent focus while keeping resets.

Two guessed English locator names timed out; fresh DOM supplied actual names,
no application change or retries on stale selectors. Original ZH/dark restored,
temp tab closed, no viewport/QA process/service restart/financial/provider/study
mutation. Eight critical count/sorted-row fingerprints and .research unchanged;
services healthy/API/frontend200/PONG. No code change/new suite run claimed;
previous287 frontend remains prior evidence. Evidence outside Git:
product-evidence/v1.2/m4/20260926-chart-keyboard-contrast.json.
GitHub hold unchanged/no polling/push/CI/merge/release. Next repair must retain
loading/error/lastpage/isolation and not steal focus after the user moves away;
deferred tests and actual browser recheck required. Full M4/M5 remains open.

## 2026-09-26 05:15 UTC distinct paper-ledger landmarks and keyboard traversal

Actual Chrome on5173 showed five populated ledger regions sharing the generic
scroll instruction and five unnamed tables. Shared PaperTable now prefixes the
translated section title on each region and names its table with that title;
tabindex, headers, empty states and all monetary/stream/API logic stay unchanged.
New ZH region assertion failed before repair. Initial English fixture expected
Simulated orders/fills rather than the existing Paper orders/fills: corrected
explicit expectations after inspecting translations, not weakened assertions.
Focused26/full frontend287/35files, lint/type/build/Prettier/diff PASS. Independent
read-only reviewer approved the bounded change; no full WCAG/speech claim.

QA-only HTTP forwarder lacked WebSocket upgrade, so snapshotGET200 did not hydrate
the UI. Existing installed Vite preview proxy then reached the backend, which
rejected temporary5182 Origin with WebSocket403. Stopped this access path; no
Origin rewrite, CORS/security change or product connection fix to satisfy QA.
POST on a nonexistent QA-only path returned405. Both owned processes verified
by PID/start/command/listener before TERM (26120/start15:10:56 Python,26254/
start15:12:59 Vite); sessions8838/29277 terminal, listener5182 gone, files retained.
Compose inspection established source bind mount: fresh page on approved5173
served the repair without image build or any container restart.

Actual Chrome ZH/dark stopped historical account: all five region/table names
distinct, Tab positions→signals→risk→orders→fills,2px visible outline. EN names
and positions→signals verified; rows6/20/20/20/6 unchanged, historical date
2011-03-23 retained, cash81309.8134/equity99964.8134/commission30.1866 unchanged.
Closed/Stopped status roles localized; actual screen-reader speech not tested.
Audit native Enter opens/closes with focus retained. Locale restoredZH, dark
unchanged, temp tabs closed; main draft not interacted with. Eight critical
fingerprints and .research unchanged, services healthy/API+frontend200/PONG.
No session start/pause/stop, job/provider/order/financial POST or research run.
Evidence outside Git: product-evidence/v1.2/m4/20260926-paper-landmark-keyboard.json.
Local coherent commit only; GitHub hold unchanged, no CI retry/push/merge/release.

## 2026-09-26 05:04 UTC cold HTTP-cache route measurement is partial

Disposable production build42f2025, Chrome153, ZH/dark1440x900, no-store
responses and fresh document per sample. Reused GET-only localhost5182 QA
forwarder; no financial POST or new study. Seven trusted pointer clicks loaded
the same saved historical result: loading DOM4.8–11.7ms, result DOM337.2–346.2ms.
Asset/main/lazy JS responses200 with positive transfer bytes, not cold backend,
OS or archive data. These measure DOM availability, not visible presentation.

Preserve native3040ms pointerup/click in sample1 (same interaction, not two
samples). Sample7 native click16ms; five samples have pointerdown-only0 and
incomplete click evidence, not zero-duration clicks. Event observer threshold16
censors entries; asynchronous delivery was observed after the result became
available. No native/visible-feedback p95 or cold performance PASS is claimed.
Two bridge timeouts occurred before input, root sample remained null; do not
count them as product interactions or silently remove failures. Changed action
method rather than repeating a third identical failed action.

Bounded QA-only publication control with AX clicks: deferred184ms interaction
versus immediate384ms pointerdown/376ms click, DOM results341.2/327ms. Two
observations cannot establish causality or dismiss3040ms; different input method
is not pooled into the seven-sample series. Independent read-only review agrees
DOM-only progress is valid but native paint evidence incomplete. Stop this
measurement series before multiplying an unresolved measurement design.

Owned QA PID24290/start14:55:50 WSL, command and5182 listener verified before
TERM; session16430 terminal/listener gone. Temp tab closed, viewport reset,
instrumentation removed from disposable index, build/evidence retained. Main
services healthy; eight critical count/row fingerprints unchanged and .research
diff empty. No product code/runtime/data/provider changes. Evidence outside Git:
product-evidence/v1.2/m4/20260926-cold-route-diagnostic.json. No push/CI retry,
merge or release during user-estimated five-day GitHub hold. Remaining native
paint collection needs a valid bounded protocol; paper keyboard/live-announcement
and nontext focus checks remain safe independent work. Goal remains incomplete.

## 2026-09-26 04:50 UTC actionable wizard validation and keyboard recovery

Actual Chrome on an isolated localhost production build reproduced negative
capital: generic alert only, no invalid/description association, focus left on
Continue. The wizard's existing validation now identifies the first invalid
field using the same exact monetary predicates. Bilingual explanations attach
through aria-invalid/describedby; restored-review errors return to the proper
step, open a closed advanced section and focus its field. Async API errors focus
the summary without inventing a field. Repeated unchanged invalid submission
refocuses the field. No new dependency or financial/backend calculation.

noValidate deliberately funnels native/custom failures through this one path;
required/bounded integer and Decimal checks remain, with name<=120 and canonical
Gregorian ISO dates covering former native safeguards. Server stays authoritative.
Baseline capital-focus regression failed before repair. Initial batch13fail/1pass
included one malformed fractional-integer draft fixture: draft shape rejects that
fixture, so corrected it to a valid-shape out-of-range integer and separately
tested fractional UI input. No weakened assertion. Focused wizard16 and existing
guided tests31 PASS; full frontend287/35files, lint/type/production build and
changed Prettier PASS. Independent read-only reviewer found no bounded regression.

Actual Chrome EN/dark negative capital focused correctly, ZH retained -1 and
translated its description; correction retained exact100000.000000000000000001
and focused next-step heading. ZH/dark commission0.02, repeated Enter, EN/light
translated error/focus PASS. Closed advanced maximum-holdings0 automatically
opened/focused with1–100 guidance; correction20 continued without residual errors.
An installed browser writing-assistant extension appended its label to the input;
selector timeout was resolved from fresh DOM with the observed name prefix,
not a product defect or extension/security change. Screenshot emitted inline,
not a saved-image claim. Actual screen-reader speech not verified; broader AA
and product acceptance remain incomplete. Async-error and invalid restored-review
paths above are unit evidence, not a financial browser submission.

Reused readonly GET-only harness, separate5181 storage; no job/account/order/
provider POST, main draft or frozen-research change. Owned PID21982/start14:40:05
and listener verified before TERM; session70717 terminal,5181 closed/temp tab
closed/build retained. Main PG/Redis/backend healthy, PONG/API+frontend200, eight
critical count/row fingerprints unchanged. Evidence outside Git:
product-evidence/v1.2/m4/20260926-wizard-validation.json. Commit stays local during
user-estimated GitHub hold; CI not run for this repair, no merge/release.

## 2026-09-26 04:37 UTC local plan keyboard check and CI hold

User reports GitHub recovery requires five days: estimated 2026-10-01, not
verified recovery or authorization to pay/increase limits. No CI retry or push
while the account gate is unchanged; local work continues, release gates intact.

Actual Chrome opened the existing U6 historical plan using Enter. Chinese/dark
table focus had a visible 3px outline; ArrowRight reached its horizontal end
(436px). Tab reached native provenance summary; Enter opened/closed it and
retained focus. English/light retained 32 candidates, five cash rejections,
2011-03-22/23 boundary, cash45539.94836/equity104666.94836/estimated44221.44166,
historical-only/no-order warnings and semantic status. English summary also
opened/closed with Enter. English table is wider (max664px); Chinese end-scroll
evidence does not establish English end-scroll or full screen-reader coverage.
No new study, account, order, provider request, code change or service restart.
Chinese/dark Workbench and existing U3 draft restored. Eight critical table
counts/row hashes unchanged; `.research` unchanged. Evidence outside Git:
product-evidence/v1.2/m4/20260926-plan-keyboard-ci-hold.json.
This bounded case passes, not full accessibility, M4/M5 or release acceptance.

## 2026-09-26 04:30 UTC GitHub Actions account gate

Comparison repair pushed as f91e1e5 to existing draft/open PR32. Exact-head
[CI36217962698](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36217962698)
terminated before any frontend/backend/Compose step started. GitHub annotations
state recent account payments failed or the spending limit needs increasing.
This is NOT_STARTED_ACCOUNT_BILLING, not a failed product test and not CI PASS.
No repeated rerun, payment, limit change, alternative identity, self-hosted
workaround or protection bypass attempted. User informed once to check Billing
& plans. Local frontend271/lint/type/build and bounded Chrome/review evidence
remain valid; safe independent M4 work remains. Release stays incomplete. This
external gate is saved locally without another pointless CI-triggering push.

## 2026-09-26 04:27 UTC saved comparison result failure and identity-safe retry

Actual Chrome over a disposable localhost-only production build and read-only
API forwarder loaded two existing successful historical studies, then reloaded
with one delayed result GET503. It reproduced two defects: already parsed study
name discarded on result failure, and an unknown transport code directing the
user to nonexistent technical details. The shared code-explanation helper now
accepts HTTP guidance as an unknown-code fallback; registered business/risk
explanations remain unchanged and permission/timeout precedence is retained.
The comparison catch retains only that same request's verified job metadata,
never partial financial results. No router, dependency or domain change.

New regression failed before repair. Focused22/full frontend271, lint/type,
production build and changed-file Prettier PASS. Deferred query-only failure and
retry assert no stale/partial metric tables; unknown and registered code behavior
has focused coverage. A mistaken fixture-value test expectation was corrected
after inspecting its actual precise return, not by weakening assertions.
Independent read-only source review found no actionable regression.

Chrome ZH/light and EN/dark showed both actual saved study names and actionable
server guidance, zero metric tables while incomplete. Mouse retry and keyboard
Enter retry restored the same pair, two tables/zero alerts, returns4.67%/-0.47%
and original2010-01-04→2011-03-22 /2011-03-01→2011-03-28 periods. Locale switch
retained the pair/error. Before/after screenshots emitted inline, not saved-file
claims. Browser retry completed too quickly to capture pending feedback; that
specific deferred branch is unit evidence, not browser timing evidence. Injection
is not a real outage, permission grant, strategy rerun or forward-market evidence.

QA forwards GET only to fixed localhost8000, never financial POST. Owned process
and listener verified before stopping; port5181 and temporary tab closed. Main
services untouched/healthy/API200/PONG; eight critical table counts/sorted row
hashes equal prior verified04:09 values. Original main browser untouched, no
viewport override, study/account/order/provider or frozen `.research` mutation.
Evidence outside Git: product-evidence/v1.2/m4/
20260926-comparison-result-error.json and comparison-readonly-qa.py.
Base61170ca CI36217283329 PASS (backend989/1skip, frontend269, Compose).
This repair's exact-head CI did not start due to the account gate above. Broader accessibility/performance and genuine
backup/ledger/forward/startup/user gates remain open; M4/M5 not promoted.

## 2026-09-26 04:15 UTC alias review, text contrast and idle guard deployment

Independent read-only review identified an accepted `/experiments/` alias
bypassing the exact list/history identity. Actual Chrome reproduced M1 query
and two selections disappearing after detail/native Back. Two new regressions
failed before repair. Normalize only this accepted alias in the existing shared
pathname reader, before mount and after allowed traversal; retain query/hash,
history length and state, rewriting only a matching managed URL marker. Existing
dirty-navigation guards remain intact. The same reviewer accepted the bounded
repair. Focused49/full frontend269, lint/type/build/changed-file Prettier PASS.
Actual EN/light Chrome detail/visible Back retained M1, selection2 and loaded
scrollY631. Native Forward/Back and guard compatibility have unit coverage;
no broader alias, router, response cache or financial-state change was added.

Actual saved-result rendered text contrast: 884 nodes each in ZH/dark and
EN/light, zero failures against normal4.5/large3 ratios, disabled Previous
opacity skipped. Computed RGB/background alpha composition is bounded evidence,
not full WCAG or chart/nontext/focus/native-control/screen-reader acceptance.

Main jobs/accounts were idle; only `docker compose restart backend` deployed
the previously tested checkpoint guard. Backend healthy/API200, Redis PONG,
Alembic0016. Other service IDs/start times unchanged; no container/volume/image
recreated or deleted. Eight critical table counts and sorted JSON-row MD5s were
identical before/after (an equality check, not a backup). Guard host/container
SHA256 matched. Chrome reloaded eight saved studies and the Chinese/dark
Workbench; default view/selection0, original draft and viewport preserved.
No study/account/order/provider creation or `.research` write. This idle restart
does not prove mid-run recovery or restore the two missing genuine ledgers.

Evidence outside Git: product-evidence/v1.2/m4/
20260926-alias-review-idle-restart.json. Base92e760b passed CI36216328525;
this alias repair awaits its own exact-head CI. Three human answers remain
unknown; full M4/M5, forward authority and release gates remain incomplete.

### Concrete remaining independent checks, without reopening accepted cases

- Saved comparison result503 after success and identity-safe manual retry now
  passed as bounded evidence above; deferred pending/query transitions have
  unit coverage. Do not repeat this or the prior completed+INTERRUPTED case.
- Broader keyboard/announcement and chart/nontext/focus contrast across
  configuration, plan and paper pages; bounded result text checks above do not
  replace these, genuine screen-reader or OS reduced-motion evidence.
- Cold production-route/data feedback measurements beyond accepted warm
  30-route and 30-chart measurements; record case and method, not proxy timings.
- Genuine next Windows login, native200pct user-operated zoom, novice workflow,
  independent backup medium, authentic pre-loss ledgers and lawful forward-feed
  rights remain separate user/external gates. Agent QA cannot substitute them.

## 2026-09-26 03:55 UTC asynchronous study-list scroll and missing-link recovery

Actual Chrome ZH/dark reproduced a stable loaded-list position of `scrollY=693`
becoming `55` after opening the existing last-row result and returning. The
loading placeholder is shorter than the loaded list, so native restoration
clamps too early. Reuse the existing list history entry for validated vertical
position; restore once in layout after rows load, then record real scrolling.
Do not overwrite it during loading or on another route. Query changes discard
the old position, including a filter change before the first request completes.
No response cache, polling restore loop, router or dependency was added.

The new regression failed before repair. Focused comparison/list checks 19 PASS;
full frontend 267 PASS, ESLint, TypeScript, production build, changed-test
Prettier and diff check PASS. Invalid/null/negative/nonfinite/string positions,
loading clamp, subsequent scrolling, rerender and pending-filter change are
covered. The original compact page style is retained. Actual Chrome returned
to `693`, reloaded at `693`, and preserved `693` after native Forward/Back;
before/after screenshots were emitted inline, not claimed as saved files.

A read-only DB query established zero records for the fixture-shaped unknown
study ID. Its actual deep link showed actionable Chinese and English not-found
alerts; the visible Back link returned to the loaded list without an alert or
invented result. This is one missing-link branch, not all stale/offline/timeout
cases. Restored Chinese/dark Workbench and original view/empty selection; no
temporary viewport was set. Services remain healthy, Redis PONG/API+frontend
HTTP200, formal 1/3/310, jobs 8, paper 5/events 417, updates 4/receipts 6 unchanged.
No study/account/order/provider/DB/service restart or `.research` mutation.

Evidence stays outside Git at product-evidence/v1.2/m4/
20260926-study-scroll-recovery.json. The user's three `不清楚` answers remain
unknown, not backup existence, pre-loss recovery evidence or feed authorization.
UX-VIEWS/UX-ERROR/full M4/M5 remain incomplete; no merge or release gate promoted.
Base `fb5888a` passed [CI36215518814](https://github.com/MakenzieAhern/quant-trading-platform/actions/runs/36215518814)
backend/frontend/Compose; that run predates this scroll repair.

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

## 2026-09-29 01:46 UTC local formal-chart integrity and keyboard paging

The formal research detail's exact strategy/benchmark table previously put
all strategy rows before benchmark rows, separating matching trading dates
across local table pages. It now orders rows by trading date before paging,
and both visual traces use the same ordered date domain even if source series
have independent dates.
Rolling metrics previously dropped a date's valid drawdown when its Sharpe
value was null; both exact rows are now shown, with the Sharpe value explicitly
unavailable and no line drawn through its missing observation. The curve,
rolling and research-table pagers remain mounted while a page loads or errors,
so keyboard focus survives Next and Previous. Each has a distinct section
name; after a failed later page, Previous remains available without guessing
an unknown total.

Local full frontend tests 378/378, ESLint, changed-file Prettier and
TypeScript/Vite build passed. Main Compose PostgreSQL, Redis and backend were
healthy, frontend and `/api/health` returned HTTP 200. Actual Chrome on the
saved Development run `b38081a7` showed same-date strategy/benchmark rows,
2011-01-18 null Sharpe alongside exact drawdown 0, and curve page 201–400
with focus retained on the named pager. The read-only source response for the
first rolling page had 200 rows: 21 null Sharpe and 100 valid drawdowns.
This is bounded local/GET-only evidence, not full U4 interaction, native
screen-reader/200% zoom, independent novice testing, GitHub CI or M4/M5 PASS.
No research, account, provider or dataset write occurred. The user-estimated
October 1 GitHub recovery is not treated as verified clearance.

## 2026-09-29 02:01 UTC local operation while GitHub CI/CD is unavailable

The existing main Compose stack remained available on this PC: PostgreSQL and
backend were healthy, Redis and frontend were running, and both `/` on port
5173 and `/api/health` on port 8000 returned HTTP 200. Actual Chrome opened
the local workbench, data center and an existing saved historical result via
read-only navigation. The data center explicitly labeled the available archive
as historical through 2025-12-31, not current market data.

At local head `c0ab74e`, `make test` used the separate `compose.test.yml`
tmpfs PostgreSQL and passed 1024 backend tests (one optional unmounted-archive
skip) plus 378 frontend tests. `make lint` passed Ruff, format, mypy, ESLint
and TypeScript; `make build` passed the Vite production build. Actual Chrome
confirmed no document-width overflow on the workbench at 390×844 and
1024×768 in Chinese/dark and English/light, and at 1280×800 and 1440×900
in English/light. The exact 390px CSS viewport was verified, then the browser
override and original Chinese/dark preference were restored.

This is a bounded local-runtime and developer-check checkpoint. It does not
replace GitHub CI, the full M4 browser/accessibility/performance matrix,
saved M5 media, independent novice acceptance, lawful current-data forward
evidence, genuine recovery of the two lost paper ledgers, or independent
physical disaster recovery. No new study, market acquisition, paper order,
formal/OOS run, push, merge or release occurred; no screenshot file or
recording was saved for this check. The user-estimated October 1 GitHub
recovery is not itself clearance to resume remote operations.

## 2026-09-29 02:12 UTC current-head release images without GitHub CI

At local head `9ff0ff1`, the merged release Compose configuration passed and
reset both backend and frontend commands to their release-image defaults. The
current-source frontend release image served `/`, `/help` and `/markets` with
HTTP 200 on an isolated localhost port. Actual Chrome rendered `/help`, showed
the unavailable-service state honestly, and expanded the “What is a backtest?”
help item. This was not an integrated release-browser run: the standalone
frontend was not wired to the isolated backend.

The current-source backend release image migrated a fresh private-network,
tmpfs `quant_test` PostgreSQL from empty to Alembic head `20260924_0016`.
The last revision downgraded to `20260923_0015` and upgraded to head again.
With separate tmpfs PostgreSQL and Redis, production/paper-mode
`/api/health` returned HTTP 200 and Redis returned PONG. The isolated API
log showed startup complete. Exact scratch containers had auto-remove,
no host/named-volume mounts, and were stopped; their empty dedicated network
was removed. The original four Compose services remained running, and their
frontend and `/api/health` returned HTTP 200 afterward.

This closes only a local current-head image, migration and runtime smoke gap.
It is not GitHub CI, an integrated release-browser run, a genuine backup or
lost-ledger recovery, licensed current-market forward evidence, native
accessibility/performance/novice acceptance, or M4/M5 release approval.
No original database, frozen research, dataset, account, provider or Official
OOS change, push, merge or release occurred. The October 1 GitHub recovery
date remains a user estimate, not verified clearance.

## 2026-09-29 02:20 UTC isolated frontend-to-backend release demo

At local head `5776d76`, an isolated release frontend was rebuilt with
`VITE_API_BASE_URL=http://localhost:18002`, paired with the current production
backend image using `FRONTEND_ORIGIN=http://localhost:15176`, and served on
localhost-only temporary ports. Scratch PostgreSQL and Redis used tmpfs and a
private network; none of the four containers had host or named-volume mounts.
This avoided the release Compose overlay's original host ports and data mounts.

In the Codex in-app browser, the first page showed an online service, the
registered A-share strategy, a disabled unmounted historical archive, and an
explicitly labeled 2031 synthetic demo. The main action opened the four-step
wizard. Submitting default demo settings returned HTTP 202 to the isolated API;
job `4fdf5f74-e18e-495d-b0f0-e2b7cc82bbe6` finished `SUCCEEDED` with
340/340 sessions. The saved result showed +0.39% return, -0.04% drawdown,
CNY 25 cost and +4.15% **synthetic** benchmark; these are workflow fixture
outputs, not market or investment evidence. A browser reload reopened the same
result. Switching to English retained the numbers and translated the synthetic
and risk warnings; Chinese was restored. The plan correctly withheld an
executable action because this demo has no accepted next trading day. API logs
confirmed browser GET/OPTIONS/POST/result requests reached the isolated API.

The browser tab was closed, the four exact auto-remove scratch containers were
stopped, and the verified-empty dedicated network was removed. The QA task and
tmpfs database were disposable; original PostgreSQL, Redis, backend and
frontend remained running, with their API/frontend still HTTP 200. No original
database, frozen research, provider, account, Official OOS or GitHub action
was taken. This is one agent-operated synthetic release-flow proof, **not**
independent Chrome/novice, real A-share or forward-data acceptance, current-head
interaction media, full M4/M5, GitHub CI, or v1.2 release approval. No screenshot
file or recording was saved. October 1 remains a user estimate, not a verified
GitHub recovery event.

## 2026-09-29 02:33 UTC local continuation while GitHub CI is held

The running Compose PostgreSQL, Redis, backend and frontend remained available
on their configured localhost ports; PostgreSQL accepted connections, Redis
returned PONG, `/api/health` reported HTTP 200 and the frontend returned HTTP
200. This permits local use and verification without GitHub Actions. The
repository's `make test` uses a separate disposable PostgreSQL; `make test`,
`make lint` and `make build` all exited zero. Frontend tests passed 381/381;
backend tests, Ruff, format, mypy, ESLint, TypeScript and Vite build passed.

One U1/U3 defect was corrected: before any experiment submission, a failed
strategy-capabilities read showed the message for an uncertain *submission*.
The wizard now reuses the existing typed load-error panel. Red-before/green-
after cases covered HTTP 403, HTTP 408 and offline TypeError in English and
Chinese, successful read retry, and no experiment-create request. An
independent read-only review found no required change or import cycle.

These checks are bounded local evidence, not the exact-head GitHub CI or a
full U1–U8/M0–M5, native browser fault-injection, novice, accessibility,
performance, forward-data or disaster-recovery pass. No original database,
paper account, frozen research, provider, Official OOS, push, merge or release
was changed. The user-estimated October 1 GitHub recovery is not yet verified.

## 2026-09-29 02:45 UTC saved-result read-error correction

Four read-only result panes (equity, trades, risk decisions and holdings)
previously reused the uncertain-*submission* message when their GET failed.
Four red tests reproduced HTTP 403, HTTP 408 and offline cases. The existing
typed load-error panel now supplies distinct bilingual guidance. Retry issues
only the failed GET, not an experiment-create request; all four recovered in
the focused test. `Collections.test.tsx` passed 16/16; TypeScript, changed-file
ESLint/Prettier and diff checks passed. An independent read-only reviewer found
no blocking issue in this slice.

Actual Chrome opened a saved historical result and expanded the trades and
holdings panes after the fix; their saved rows loaded without a browser error.
The temporary QA tab was closed. This is a successful-read browser check, not
browser fault injection of 403/408/offline; no screenshot file or recording
was saved. Full M4, U1–U8/M5, genuine forward-data/backup/ledger gates and
exact-head GitHub CI remain open. No original study/account/provider/frozen
research, Official OOS, push, merge or release was changed.

## 2026-09-29 02:53 UTC local continuation without GitHub CI

GitHub recovery is still unverified; October 1 is only the user's estimate.
The running local Compose PostgreSQL, Redis and backend were healthy, with
`/api/health` and the frontend returning HTTP 200. The services need no
restart. `make test` passed using its separate disposable PostgreSQL, with
390/390 frontend tests; `make lint` and `make build` exited zero. This is a
usable local verification path while GitHub Actions is unavailable, but it
cannot replace exact-head remote CI, PR review, merge or release gates.

A paper-session race was reproduced and corrected locally. A start, pause or
stop HTTP command could report an error after the authoritative session state
had already confirmed the command, leaving a misleading alert as subsequent
statuses arrived. The view now records confirmation during a pending command
and suppresses its late failure. Regression tests also cover a failed POST
before confirmation, later status changes, an unconfirmed failure and a new
command failing independently; `PaperTradingPages.test.tsx` passed 48/48.
The saved-result keyboard regression was aligned to the new read-error retry
label and remains 4/4. These are bounded component tests, not real browser
fault injection, full U7/M4/M5 or release acceptance. No original database,
paper account, provider, frozen research, Official OOS, push, merge or
release was changed.

## 2026-09-29 05:52 UTC experiment-list polling and retry focus

The Research experiment list had two M4 keyboard defects. When an active-row
poll failed, the table unmounted and its focused link fell to `BODY`; after
an error was retried successfully, the disappearing Retry button likewise
left focus on `BODY`. Red component regressions reproduced both. The list
now moves focus to its visible error alert only when the focused list control
disappears, and moves focus to its stable heading after a successful retry or
row replacement. Focus deliberately moved elsewhere is not stolen. A
read-only independent review identified additional keyed-row and pending-
retry focus gaps; both are covered by the final tests.

An isolated production frontend and GET-only QA proxy over the existing
scratch backend reproduced one five-second poll with a browser-response-only
`RUNNING` row and an injected HTTP 503. Actual Chrome focus moved from that
row link to the visible alert, with no stale row; the first Retry check exposed
the second defect. After the fix and a rebuilt frontend, Chrome again focused
the alert on failure and the H1 after Retry restored the list. The screenshot
was inspected in-tool but **not saved**. Reproducible proxy and bounded method
log are outside Git in
`product-evidence/v1.2/m4/20260929-experiment-poll-focus-*`.

Final local checks: `make test` passed backend 1024/1025 (one optional
unmounted-archive skip) and frontend 416/416; the later test-only pending-
retry guard passed in the focused 50/50 and final full frontend 417/417.
`make lint`, `make build` and `git diff --check` passed. The exact QA tab,
mount-free container and proxy were stopped; original four Compose services
remained running and original frontend/API both returned HTTP 200. This is
bounded Chrome/component evidence, not native screen-reader speech, full
M4/M5, independent novice, licensed current-market forward simulation,
genuine lost-ledger/independent-backup recovery or exact-head GitHub CI.
No original database/account/provider/frozen research/Official OOS write,
push, merge or release occurred; October 1 remains an unverified estimate.

## 2026-09-29 06:08 UTC narrow-browser check, not native 200% zoom

At clean code head `3db3a32`, the existing isolated production-image scratch
project remained healthy. Actual Chrome 153 used only saved historical reads:

- English 390×844 saved result: document/client width 375/375. Keyboard Next
  advanced the chart to 101–119 of 119 and left focus on the named Pagination
  group. No page-level horizontal overflow or alert was observed.
- Chinese dark 1024×768 stopped historical paper ledger: document/client width
  1009/1009. The named plan table was 714px wide with 1051px content;
  ArrowRight reached its 337px maximum horizontal scroll, exposing the risk
  decision column.
- A separate 720×450 **CSS viewport surrogate**: saved-result and stopped-
  ledger document/client width 705/705. Result chart Next reached 101–119 of
  119 with focus on the named group in view. The ledger plan table was 627px
  wide with 1051px content; keyboard scrolling reached 424/424px and the
  rightmost decision text was visible. No page-level horizontal overflow.

Native 200% zoom was **not** proven: at a 1440×900 base viewport, Chrome
extension `Control+plus` and `Control+equal` did not change devicePixelRatio,
visualViewport scale or the CSS viewport. The 720px surrogate cannot replace
real page zoom, font scaling or screen-reader speech. Screenshots were viewed
in-tool but not saved as release media. An independent read-only static audit
found no clearly evidenced release-critical defect in these target layouts;
it did not run a browser and cannot certify geometry or WCAG AA.

The temporary Chrome tab and viewport were reset/closed. The original four
services stayed running; there were no account/database/provider, frozen
research, Official OOS or GitHub writes. Full M4/M5, actual native zoom,
licensed new-market forward receipt, genuine lost-ledger restore, independent
backup, hosted CI and release approval remain open.

## 2026-09-29 06:20 UTC deployment and guide safety correction

Read-only Alembic inspection found the original development database at
`20260924_0016 (head)`. The published `v1.1.0` tag lacks product migrations
`20260922_0012` through `20260924_0016`. Its code must not be started against
the current PostgreSQL volume as an assumed rollback. `docs/DEPLOYMENT.md`
now states the independent pre-upgrade backup and isolated restore-rehearsal
gate; both user guides link to it. No such backup/rehearsal or cutover has
been verified, so rollback remains unavailable, not PASS.

The guides also qualify optional historical archive availability, uncertain
paper-session creation retries, conditional rebalance plans, comparison
metadata limits, date-filtered export records versus full-period metrics and
contextual data dates. These were checked against existing product behavior;
they are documentation corrections, not a new M5 browser or release pass.
No original service data, frozen research, Official OOS or GitHub state changed.

## 2026-09-29 06:55 UTC bounded Chrome paper race and saved historical media

On a scratch-only synthetic A-share paper account, the current-head frontend
made exactly one Start POST. The scratch backend accepted it once (HTTP 200,
one `STARTING` event); an isolated response proxy held that reply until Chrome
showed `Running`, then delivered HTTP 503. Both browser response and CDP
network events recorded that 503. The UI stayed `Running` with zero visible
error alerts and no duplicate Start POST. The account was stopped afterward.
The preliminary attempt did not prove 503 delivery and is excluded. The
reproducible harness, report and post-response screenshot are outside Git at
`product-evidence/v1.2/m4/20260929-paper-late503-chrome.md`. This passes one
controlled browser-response case, not a real outage or full M4/U7 matrix.

Installed Chrome 153 saved and visually checked current-head scratch PNGs of
the Workbench, historical result, differing-condition comparison and stopped
historical paper account at 1440×900. A separate Playwright capture measured
CSS viewport/client/scroll widths of 390/390/390 and saved a 390×844 Chinese
Workbench PNG without page-level horizontal overflow. A native Chrome CLI
390px PNG cropped a wider layout and is **rejected**; the initial 127.0.0.1
origin PNG is also rejected because scratch CORS expected `localhost`.
Screenshots and SHA-256 values are outside Git in
`product-evidence/v1.2/m5/20260929-chrome-media/README.md`.

A 26.12-second, 1440×900 VP8 WebM records scripted GET-only navigation from
Workbench through selecting two saved studies, the non-controlled-comparison
warning, both historical results, then a stopped paper account and its dated
plan. Decoded frames at 1, 7, 13, 15, 21 and 25.9 seconds were inspected; the
first frame is white while Chrome starts. WebM SHA-256 is
`A8BC68808698B59D8A84E4AB390EFF424182B95B47486EB4A17F630A32BF7D70`.
The post-close `saveAs` step errored, but the raw recording had finalized and
decoded; see `20260929-readonly-interaction.md` in the same outside-Git folder.
This is saved historical scripted media, not independent novice, native 200%
zoom/screen-reader, physical-mobile, full M4/M5, or lawful new-market forward
evidence. No original account/database/provider/frozen research/OOS or GitHub
write occurred. GitHub October 1 recovery remains unverified.

## 2026-09-29 08:51 UTC comparison Retry keyboard-focus recovery

At local code head `c291fdc`, a red regression showed that keyboard Enter on
the comparison error's Retry removed the focused button and stranded focus on
`BODY` during the replacement GET. The page now moves focus synchronously to
its persistent, programmatically focusable H1 before invalidating the read.
The deferred 503-result component case asserts H1 focus during loading and
after successful metrics return. Its 21 targeted tests, all 424 frontend tests,
lint, TypeScript check, production build and changed-file Prettier check pass.
An independent read-only diff review found no concrete regression.

Actual in-app browser on the bind-mounted current source loaded a deliberately
nonexistent two-ID comparison. Both reads returned not found; keyboard Enter
on Retry left the visible focus ring and accessibility focus on “Compare
experiments” while the incomplete state remained actionable. Screenshot saved
outside Git at `product-evidence/v1.2/m4/20260929-compare-retry-focus.png`,
SHA-256 `1306AB3C0F55B48A64BE87E5F44ACBA5D98A6872D38396B4E5AA1C94FA05711D`.
The temporary tab was closed; original Compose services and financial data
were not changed. This is one bounded keyboard recovery case, not an actual
browser 503→success run, native Chrome/screen-reader speech, whole U4/M4/M5,
independent novice acceptance or hosted CI. The October 1 recovery estimate
has not been verified; no push, merge or release was attempted.

## 2026-09-29 09:14 UTC local continuation during GitHub hold

The original Compose PostgreSQL, Redis, backend and frontend remained up;
PostgreSQL, Redis and backend were healthy, and the frontend and `/api/health`
returned HTTP 200. The isolated `quant-mvp-tests` test stack used temporary
PostgreSQL storage. `make test` passed 1025 backend tests with one optional
unmounted-archive skip and all 424 frontend tests. `make lint`, frontend
typecheck and `make build` passed. These are local checks, not pushed-head
GitHub CI or release approval.

Actual in-app-browser GET-only navigation at 1265×712 showed the running
Workbench, Strategies, strategy detail, restored guided-research draft,
Research list and saved historical result in English/dark. Six baseline
screenshots and a post-change success-page screenshot are stored and hashed
outside Git in `product-evidence/v1.2/m5/20260929-cfd9fe5-iab/README.md`.
The two result screenshots are pixel-identical. This is returning-user,
clipped-viewport evidence, not exact requested media, native Chrome, a
clean-user walkthrough, independent novice test or full M5.

A red keyboard regression showed that saved-result Retry removed its focused
error button and left focus on `BODY`. Commit `3ca7676` moves focus to the
persistent result heading before reloading. A deferred-response test asserts
heading focus both while the replacement GET is pending and after successful
metrics return; all 424 frontend tests, lint, typecheck and build pass.
Independent read-only review found no concrete defect. The browser screenshot
shows only the success page, **not** an error→Retry browser proof; that path
is verified by the component regression only. Whole U4/M4/M5 remains open.

Read-only backup inventory found one physical NVMe; its C/D partitions are
not independent backup destinations. Known pre-accident dumps predate the
lost account creation, and later dumps postdate the loss; none is verified
to contain original account ledgers `4b64380f` and `07d72259`. Windows
backup/VSS inventory could not be completed without elevation, so its
existence is unknown, not disproven. No lawful 2026 two-exchange market-data
use grant or genuine after-start forward receipt was established. Original
database/accounts, Docker volumes, frozen research, Official OOS and GitHub
were not changed. GitHub recovery on October 1 is an unverified estimate;
no push, merge or release was attempted.

## 2026-09-29 09:33 UTC shared Retry and raw-task deep-link recovery

Red keyboard tests reproduced lost focus when the shared error Retry removed
its button on Strategies and Data Center. Another red test showed that simply
focusing the page H1 is wrong inside the market-detail dialog; a
section-level error likewise should retain its local heading. Commit
`d07990b` now hands focus to the persistent modal H2, otherwise the nearest
section/aside H2/H3, otherwise the page H1/main. The Workbench's existing
explicit H2 handoff is not overridden. Deferred-response tests cover focus
while the replacement GET is pending and after it resolves. The modal test
uses jsdom's `showModal` stub, so native dialog focus remains a browser gate.

Task Center's existing raw-update task link previously focused a detail that
was pushed offscreen when data cards and the request form loaded afterward.
The first actual in-app-browser attempt is rejected: the focused task top was
y=1396 in a 720px viewport. The corrected landing waits for parent and
request-capability layout, then checks URL and user focus before scrolling.
At 1280×720, the Task Center link placed the focused task top at y=125.7,
below the 119px topbar; direct URL reload placed it at y=126.5. Both reads
used an existing completed **candidate-only** task and started no source
request. Screenshot and SHA-256 are outside Git in
`product-evidence/v1.2/m4/20260929-u5-deep-link-iab/README.md`.

Final local frontend: 429/429 tests across 38 files, ESLint, TypeScript,
changed-file Prettier and production build PASS; independent read-only diff
review found no actionable issue. The first standard build failed only
because ignored generated `frontend/dist/assets` was root-owned. Its exact
resolved path/ignore rule were checked, owner restored to `yuchen`, and the
standard build passed; no original service data or Docker volume was touched.
Post-check Compose PostgreSQL/Redis/backend remained healthy, frontend up,
and frontend plus `/api/health` returned HTTP 200. Browser evidence is one
bounded IAB 1280×720 case, not native Chrome, required 1280×800 or other
viewports, screen-reader speech, 200% zoom, independent novice or full M4/M5.
No original account/provider/frozen research/OOS or GitHub write occurred;
October 1 recovery remains unverified.

## 2026-09-29 09:57 UTC local execution during GitHub CI hold

The existing WSL Compose PostgreSQL, Redis and backend were healthy; the frontend
was running, and `/` plus `/api/health` returned HTTP 200. PostgreSQL accepted
connections, Redis returned PONG, and `docker compose config --quiet` passed.
The application is usable locally at `http://localhost:5173`; this does not
require GitHub Actions. The repository's existing `make test`, `make lint` and
`make build` provide local development checks using the isolated test Compose
project. They are not pushed-head CI or a release gate substitute. No `act`,
self-hosted runner, new dependency or payment workaround was introduced.

At `d99c325`, a red/green EN/ZH Workbench regression corrected the EN intro's
claim that a guided backtest uses a simulated account. The actual wizard creates
a research job, not a paper account; the intro now says “guided backtest”.
At `70bd3d6`, paper start/pause/stop commands acknowledge the parsed same-account
server response and reconcile with the existing REST snapshot. A socket loss or
superseding status event cannot reopen the old command while a read is aborted;
newer stream state wins. A successful POST followed by failed GET is not reported
as a failed command. A mismatched account response fails closed with persistent
bilingual reload guidance. Red/green component tests cover these paths; an
independent read-only review found no actionable diff regression.

Final local `make test` exited zero: backend 1025 passed, one optional unmounted
historical-archive test skipped, frontend 435 passed across 38 files. `make lint`
(Ruff, format, mypy, ESLint, TypeScript), changed-file Prettier and `make build`
passed. Original Compose services and frontend/API HTTP 200 remained available
after checks. This is local component/container evidence, not native-browser
injected socket-fault QA, full U1–U8/M4/M5, independent novice, lawful after-start
forward data, genuine lost-ledger recovery, independent physical backup or
exact-head GitHub CI. The October 1 date is the user's estimate, not verified
recovery; no push, merge or release was attempted, and original accounts,
provider data, frozen research and Official OOS were not modified.

## 2026-09-29 10:13 UTC local mobile navigation and offline validation

At `9ffd880`, a red regression reproduced the mobile sidebar remaining modal
with the main content inert after its current-page Help link was clicked.
The sidebar now closes only for an unmodified click whose URL exactly matches
the current URL, using its existing focus-return path. A second regression
keeps the sidebar open when a dirty research wizard refuses a different route.
An independent read-only diff review found no actionable issue. In the actual
in-app browser at 390×844, selecting Help from the open sidebar closed it and
returned focus to Open navigation; the temporary viewport was reset.

Original Compose PostgreSQL/Redis/backend stayed healthy, frontend remained up,
and `/` and `/api/health` returned HTTP 200. The second complete `make test`
passed backend 1025 (one optional unmounted archive skip) and frontend 437/437;
`make lint` and `make build` passed. The first complete run had one unrelated
Market Updates read-error focus assertion fail with the alert mounted but not
focused within one second. That test passed six targeted repeats, its 40-test
file and later full runs; no root cause was confirmed and no speculative fix
was made. Local execution is available without GitHub Actions, but these checks
are neither native Chrome/screen-reader/full M4/M5 acceptance nor exact pushed-
head hosted CI. October 1 is only an estimated recovery date. No original
account, database, provider, frozen research, Official OOS or GitHub state was
changed; no push, merge or release occurred.

## 2026-09-29 10:30 UTC isolated historical account restart and Chrome export check

At source `f16460c`, the existing scratch release Compose images were rebuilt
without touching the original project. Its PostgreSQL/Redis/product data were
tmpfs and the accepted archive was read-only. In the actual in-app browser, a
new scratch-only audited historical A-share account was started, paused after
2011-04-19, reloaded after restarting only the scratch backend, resumed from
2011-04-20, then stopped on 2011-05-11. A separate native Chrome read showed
the persisted STOPPED state, last market date and final cash/equity. Scratch
PostgreSQL had 282 continuous, unique journal sequences, 49 strictly increasing
unique market dates and 11 fills with distinct order IDs. These checks establish
bounded local persistence/replay continuity, not independent economics or full
U7/M4/M5 acceptance. Original PostgreSQL/Redis/backend remained healthy and
frontend plus `/api/health` returned HTTP 200.

Chrome CSV export for an existing scratch historical research result produced
the page's prepared blob link, but neither the primary button nor fallback
link yielded a captured download event; the exact expected filename was not
found in Windows Downloads. Automatic file landing remains **UNVERIFIED**.
The browser policy blocked its internal Downloads page, and no alternate route
was attempted. Screenshots, SHA-256 values, image IDs and query details are
outside Git at
`product-evidence/v1.2/m5/20260929-f16460c-historical-restart/README.md`.
No original financial account, formal/frozen research, OOS, provider authority,
GitHub push/CI, PR merge or release was changed. GitHub October 1 recovery is
still an unverified user estimate; full U1–U8/M4/M5 and external gates remain
open.

## 2026-09-29 10:40 UTC native Chrome service-health outage and recovery

At `7be85cf` (no AppShell source change since the current-head scratch image),
installed Chrome opened the isolated release Workbench. Before process action,
its QA backend was healthy and all scratch paper/research jobs were terminal.
Only that scratch backend was stopped. The visible tab changed to `服务不可用`
without a manual refresh click; its topbar data link separately said
`不可用`. The Chrome accessibility tree showed independent service-state text
after the refresh button. The DOM confirmed that the sibling
`role="status"` element was outside the button and matched its
`aria-describedby` target. Switching to English showed `Service unavailable`
with the same relationship. After restarting only the scratch backend, a
visible Refresh click restored `Service online` and kept focus on the button;
switching back to Chinese restored `服务在线`. The backend returned HTTP 200 and
Docker healthy; original Compose services and `/` plus `/api/health` remained
healthy/HTTP 200 throughout.

Four actual Chrome screenshots, SHA-256 values, exact process checks and scope
are outside Git in
`product-evidence/v1.2/m4/20260929-7be85cf-service-health/README.md`.
This closes one bounded real-browser service-status/label/recovery check, **not**
screen-reader speech, native 200% zoom, the full viewport/theme/locale matrix,
novice testing, full M4/M5 or GitHub CI. No original financial data, frozen
research, OOS, GitHub PR or release was changed.

## 2026-09-29 10:45 UTC native Chrome market-dialog read failure and Retry focus

At `17dbebc`, installed Chrome opened `600000` from the scratch historical
market list in a native dialog. Only the isolated backend was stopped after
confirming its PID/Compose ownership and terminal scratch jobs. Changing the
visible end date from 2011-06-30 to 2011-06-29 and reading the new window
produced a localized, actionable `服务暂时无法连接` alert with `重试读取缓存` inside the
still-open dialog. That intermediate failure was observed in the Chrome AX/DOM
state; no failure PNG was saved. After restarting that same scratch backend,
Enter on Retry moved focus to the persistent dialog H2 while loading. The
successful historical-bars GET returned HTTP 200, displayed the exact
2011-01-04–2011-06-29 diagnostics, removed the alert and kept H2 focus.
Escape closed the dialog, cleared its URL hash and returned focus to the
original security button. The scratch backend finished healthy; original
Compose and API remained healthy/HTTP 200.

Two Chrome PNGs, SHA-256 values, request path and process facts are outside Git
at `product-evidence/v1.2/m4/20260929-17dbebc-market-modal-retry/README.md`.
This closes one real-dialog keyboard/error/retry/focus case beyond the jsdom
`showModal` stub. It does not establish screen-reader speech, every error
class, native zoom, full U5/U8/M4/M5, independent novice or hosted CI. No
original financial data, frozen research/OOS, GitHub push/merge or release was
changed.
