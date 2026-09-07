# v1.0.0 — Quant Trading Platform MVP

**Local Single-User Paper-Trading MVP**

> **PAPER TRADING ONLY. NO LIVE BROKER CONNECTIVITY. NO REAL-MONEY ORDER EXECUTION.**

## Highlights

- Deterministic backtesting and finite Paper replay through a shared typed financial core.
- Auditable Signal → Risk → OMS → simulated Execution → Fill → Portfolio pipeline.
- PostgreSQL persistence, stable REST contracts, bounded WebSocket updates and React dashboard.
- Docker-first Windows/WSL2 workflow with complete backend/frontend CI.

## Architecture

The modular monolith keeps market data, indicators, strategies, risk, execution, portfolio and
analytics independent of FastAPI, SQLAlchemy and React. Financial values retain Decimal semantics;
authoritative time is aware UTC; next-Bar OPEN execution prevents same-Bar lookahead.

## Backtesting

Registered fixture/strategy inputs, deterministic identifiers and ordering, transaction-cost
models, idempotent API submission, durable lifecycle, exact results and paginated audit history.

## Portfolio and Analytics

Centralized cash/position/cost-basis/PnL/equity accounting with immutable snapshots, drawdown,
return, CAGR, Sharpe, Sortino, exposure and Fill statistics.

## Risk and OMS

Pre-trade notional, position, exposure, leverage, buying-power and drawdown policies; sequential
reservations; retry-safe proposals; distinct risk and broker rejections; explicit Order states.

## Persistence and API

Alembic-managed PostgreSQL persistence for runs, signals, proposals, decisions, Orders, Fills,
snapshots, metrics, reservations, Paper sessions and event journals. REST remains authoritative;
WebSocket delivery is incremental and bounded.

## Dashboard

Typed React/Vite pages for creation, history, results, equity, audit tables and Paper lifecycle.
Financial text stays exact, timestamps are labeled UTC, and charts have accessible text data.

## Paper Trading

Local registered Bar replay reuses the reviewed strategy/risk/OMS/accounting path. Session
creation/start/stop is retry-safe; multiple subscribers recover from REST; process restart marks
active execution `INTERRUPTED` and never silently resumes it.

## Testing

- 257 backend and 70 frontend tests, no skips.
- Ruff lint/format, strict mypy, ESLint, TypeScript and production build passed.
- npm and Python dependency audits found no known vulnerabilities at release validation.
- PostgreSQL, Redis, Alembic, Docker rebuild/restart, deterministic backtest/Paper smoke, Chrome,
  PR CI and main CI passed.

## Security

Loopback-only published ports, restricted browser/WebSocket origins, bounded request bodies and
pagination, registry-constrained identifiers, exact Decimal validation, sanitized errors, locked
dependencies, isolated disposable test database, and tracked-file secret/artifact review.

## Known Limitations

- Unauthenticated local single-user application; not approved for public-internet deployment or
  production HA.
- A process crash during synchronous execution may leave a stale `RUNNING` backtest record;
  automatic recovery is future work, and no result is fabricated.
- Active Paper execution is interrupted—not resumed—after backend process loss.
- Finite fixtures only; no live market data, broker margin/borrow model, options, futures, HFT, or
  distributed workers.
- No live brokerage, real-money execution, ML, or GPU functionality.

## Future Work

Future work may consider authenticated deployment, asynchronous job leases/recovery, additional
data/asset classes and visualization. Live broker or ML/GPU work requires a new, explicitly scoped
safety and architecture phase and is not part of this release.
