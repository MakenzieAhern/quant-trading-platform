# Phase 10 local MVP validation

Validation date: 2026-09-06. Scope: Windows 11 / Ubuntu WSL2 / Docker Desktop,
single-process, single-user simulated trading. No live broker, credentials, ML or GPU.

## Automated evidence

- Complete PostgreSQL-backed backend suite: 257 passed, no skips.
- Complete frontend suite: 70 passed across 11 files, no skips.
- Focused coverage within those totals: release golden path 1; release security 6;
  backtest API 27; paper API 23; paper runtime 11; paper frontend pages 10.
- Ruff lint and format, strict mypy, ESLint, TypeScript and production build passed.
- npm audit: zero known vulnerabilities. pip-audit against requirements.lock: none found;
  the scanner ran in a disposable environment, not as a runtime dependency.
- Alembic upgrade, downgrade to base, re-upgrade, and schema check passed in a disposable
  PostgreSQL database; exactly one head, 20260906_0004. No shared migration was changed.

The suites include exact high-precision Decimal round trips, UTC/naive-time rejection,
idempotency/concurrent runs, independent sessions, start/stop races, repeated cleanup,
bounded slow subscribers, malformed/duplicate events, failed-result rollback, database
constraints and injected provider/strategy/risk/OMS/broker/portfolio/persistence failures.
WebSocket transport failure and cancellation release subscribers and child tasks.

## Operational evidence

- Fresh remote feature-branch clone with no host virtualenv/node_modules: configuration,
  make setup/test/lint/build succeeded. A separately named Compose project started the
  cloned application with a fresh database and migrations; internal frontend HTTP and
  backend/PostgreSQL/Redis health passed. Published ports were disabled for that parallel
  check to avoid collision with the existing application. Only its temporary volumes
  were removed afterward.
- No-cache local release image build succeeded. Installed backend without source mounts
  and nginx production frontend started; backend health and frontend returned HTTP 200.
- Real backtest and real WebSocket paper replay produced equity 100012.2, one fill at
  183.92 and six portfolio snapshots from the documented fixture.
- Backend restart interrupted an active replay without resuming it. PostgreSQL and full
  Compose restarts preserved exact backtest result and paper snapshot JSON.
- Chrome exercised creation/history/details, signals/risk/orders/fills/equity, risk
  rejection, failed backtest, direct URLs, refresh and navigation, multiple sessions/tabs,
  realtime replay and manual stop. Failed-run display used an intentionally injected
  application-service failure, not a forged success/result. Application console errors: 0.

## Focused review fixes

- Coherent paper lifecycle/event REST snapshot under a shared session-row lock.
- Cancel the pending WebSocket queue task when its handler is cancelled.
- Invalidate old API data during rapid A-to-B-to-A navigation.
- Rehydrate paper lifecycle metadata on status events: started/stopped UTC timestamps
  and sanitized errors now appear without a browser refresh. Terminal events received
  during the initial REST request no longer leave hydration stuck. Buffering during
  REST synchronization is bounded to 256 events; overflow reconnects to authoritative REST.
- Bound HTTP bodies before JSON parsing, Decimal lengths/periods/offsets; omit reflected
  validation inputs; opaque unexpected errors; reject hostile browser mutation origins.
- Isolate destructive test fixtures from application PostgreSQL; loopback ports and
  production static build; correct documentation that previously implied future features.

Core dependency/import and financial-number audit found no infrastructure imports in
domain engines or authoritative financial JavaScript arithmetic. Financial text stays
exact; chart coordinates are approximate. Existing RESTRICT foreign keys, unique event
sequences/idempotency keys and per-run/session indexes support audit history; no speculative
indexes or new schema were added. Tracked-file review found no secrets, .env, dependency
directories, database dumps, generated build artifacts or personal machine paths.

## Limits and integration gate

See PERFORMANCE.md for measured engine/persistence/API and React-render baselines.
Indicator recomputation and retained finite-run collections are known scaling limits.
This is not an endless-feed, multi-worker or public-network service. A process crash can
leave a synchronous backtest RUNNING without results; automatic job recovery is not
implemented. Paper sessions instead become INTERRUPTED. A total database outage cannot
guarantee an immediate terminal-state write; recovery must await database availability.

Release evidence does not replace the integration gate: the feature PR must have green
backend/frontend/Compose checks before squash merge, followed by clean synchronized main,
main CI, repeated tests, Docker startup, backtest/paper smoke and browser verification.
