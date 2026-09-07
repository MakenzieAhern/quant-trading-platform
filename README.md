# Quant Trading Platform

**v1.0.0 — Local Single-User Paper-Trading MVP**

A deterministic quantitative-research platform that turns registered historical Bars into
auditable strategy signals, risk decisions, simulated Orders and Fills, portfolio accounting,
analytics, durable PostgreSQL history, and a React dashboard. It demonstrates correct execution
sequencing and inspectable financial state without a market-data vendor or brokerage account.

> **PAPER TRADING ONLY. NO LIVE BROKER CONNECTIVITY. NO REAL-MONEY ORDER EXECUTION.**

## Overview

The project is a typed modular monolith. A shared Python engine powers historical backtests and
finite paper replay; FastAPI exposes REST/WebSocket contracts; PostgreSQL stores authoritative
audit history; React presents results without recalculating financial state.

**Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL 16, Redis 7,
React 19, TypeScript 6, Vite 8, Node 24, pytest, Vitest, Docker Compose, and GitHub Actions.
Redis is provisioned for future cache use but is not the current event transport.

## Features

- Registered daily OHLCV CSV fixtures and strict market-data validation.
- Decimal SMA, EMA, RSI, MACD and Bollinger Band indicators.
- Moving-average crossover and RSI mean-reversion strategies.
- Deterministic next-Bar OPEN simulated execution with configurable engine cost models.
- Pre-trade exposure, leverage, notional, drawdown and optional buying-power controls.
- Explicit OMS lifecycle, reservations, risk/broker rejection separation and idempotency.
- Long/short portfolio accounting, equity/drawdown curves and performance analytics.
- Atomic PostgreSQL persistence, stable pagination, REST APIs and typed WebSocket events.
- Backtest and PAPER TRADING dashboards with exact financial strings and UTC labels.
- Docker-first WSL2/Linux/macOS workflow and isolated CI/integration databases.

The public demo API uses the registered AAPL fixture and fixed default zero-cost execution; it
does not expose every engine configuration. LIMIT execution exists in the engine but is not a
dashboard control.

## Architecture

```text
Market Data → Indicators → Strategy → Signal → Risk Engine → OMS → Execution
                                                                    ↓
Analytics ← Portfolio ← Fill ←──────────────────────────────────────┘
    ↓
PostgreSQL → REST / incremental WebSocket → React Dashboard
```

- Financial values use Python `Decimal`, PostgreSQL `NUMERIC(78, 38)`, and exact JSON/UI strings.
- Authoritative timestamps are timezone-aware UTC; naive datetimes are rejected.
- Strategies consume completed Bars only. A signal on Bar T may fill at the next later
  same-symbol Bar OPEN, never on the signal Bar.
- Fresh state, fixed fixtures, stable event ordering and deterministic identifiers make runs
  reproducible.
- Optional `Idempotency-Key` values converge identical requests and reject conflicting reuse.
- Successful result graphs commit atomically; paper lifecycle/event sequence allocation is
  serialized with PostgreSQL row locks.
- WebSocket delivery is bounded and incremental. REST snapshots are always authoritative.
- Paper lifecycle is `CREATED → STARTING → RUNNING → STOPPING → STOPPED`, with terminal
  `FAILED` and restart-safe `INTERRUPTED` outcomes.

Domain engines do not import FastAPI or SQLAlchemy, and React performs no authoritative trading,
risk, accounting, or analytics calculations. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Screenshots

No fabricated or generated screenshots are committed. The recommended capture set is:

1. Backtest history with several independent persisted runs.
2. Backtest creation with strategy and risk controls visible.
3. Successful result with performance summary and equity curve.
4. Risk decisions, Orders and Fills tables on the same result page.
5. Active PAPER TRADING session showing WebSocket status, latest Bar and portfolio.

Use only deterministic fixtures and simulated sessions; exclude profiles, machine paths, tokens,
and unrelated windows. See the precise [screenshot plan](docs/SCREENSHOTS.md).

## Quick Start

Requires Git, GNU Make, and Docker with Compose v2.24.4 or newer. On Windows 11, enable Ubuntu
integration in Docker Desktop and run the commands inside WSL2.

```bash
git clone https://github.com/MakenzieAhern/quant-trading-platform.git
cd quant-trading-platform
cp .env.example .env
make setup
make up
```

Open the [dashboard](http://localhost:5173/backtests), [API health](http://localhost:8000/api/health),
or [OpenAPI](http://localhost:8000/docs). Migrations run automatically. Stop without deleting
history using `make down`.

## Backtesting

Create a run at `/backtests/new`; inspect history at `/backtests` and an immutable result at
`/backtests/:runId`. Results expose signals, risk decisions, Orders, Fills, portfolio snapshots,
equity and analytics. Execution is synchronous and uses registered dataset/strategy identifiers,
never client-provided paths or dynamic imports.

## Risk and OMS

Signals become immutable proposals before Risk Engine evaluation. A rejected proposal creates no
broker Order. Approved proposals reserve projected exposure/buying power in deterministic order;
Fill, rejection, cancellation, or submission failure releases the reservation. Dashboard controls
expose buying-power enforcement and maximum Order notional while the engine supports additional
documented limits.

## Portfolio and Analytics

One portfolio engine owns cash, signed positions, cost basis, realized/unrealized PnL,
commission, market value and equity. Analytics consumes immutable snapshots to calculate return,
CAGR, drawdown, Sharpe, Sortino, exposure and trade counts. Undefined statistics remain null—never
infinity or a fabricated value.

## Paper Trading

Paper sessions replay six registered completed Bars through the same Strategy → Risk → OMS →
simulated Broker → Portfolio path. Start/stop is retry-safe; pending Orders are cancelled on stop.
Active sessions become `INTERRUPTED` after backend process loss and never silently resume.

This is deterministic local replay, not a live-data feed, brokerage sandbox, or execution venue.

## REST and WebSocket

- `POST /api/backtests`; `GET /api/backtests/{id}` plus result/audit collections.
- `POST /api/paper-trading/sessions` plus `/{id}/start` and `/{id}/stop`.
- `GET /api/paper-trading/sessions/{id}/snapshot` and `/events`.
- `/api/paper-trading/sessions/ws/{id}` for incremental events.

Collections enforce limits of 1–200 and stable ordering. Each browser WebSocket queue is bounded;
a slow or uncertain client reconnects and reloads authoritative REST state.

## Persistence

Alembic manages a single PostgreSQL schema head. Backtest metadata and audit collections persist
across backend, PostgreSQL, and Compose restarts. Paper lifecycle and typed event journals are
durable; a coherent REST snapshot is reconstructed transactionally from them. Audit foreign keys
use restrictive deletion semantics.

## Testing

The v1.0.0 release baseline is **257 backend tests and 70 frontend tests**, with no skips.

```bash
make test       # all suites against disposable PostgreSQL
make lint       # Ruff, format check, strict mypy, ESLint, TypeScript
make build      # production frontend bundle
```

CI also validates development, test, and release Compose configurations. See
[release validation](docs/RELEASE_VALIDATION.md) and [performance baselines](docs/PERFORMANCE.md).

## Docker / WSL

Canonical commands run in pinned containers; host Python and Node are not required. Tests use the
separate `quant-mvp-tests` project and never truncate application history. `make down` preserves
named volumes. Windows details are in [the WSL2 guide](docs/WINDOWS_WSL_SETUP.md); optional host
development is documented in [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md).

For a local release rehearsal using installed backend code and nginx static assets:

```bash
docker compose -f docker-compose.yml -f compose.release.yml up --build -d --wait
```

## Security

This is an unauthenticated single-user application intended only for loopback. Compose binds all
published ports to `127.0.0.1`; do not expose them to a shared or public network. Browser mutation
origins and WebSocket origins are restricted, HTTP request bodies are capped at 64 KiB, identifiers
are registry/UUID constrained, validation omits reflected input, and unexpected errors are
sanitized. `.env`, credentials, databases, dependency trees and build outputs are ignored.

## Limitations

- Local single-user simulated trading only; no authentication or public-internet deployment.
- No live data, broker connectivity, credentials, real-money Orders, or production HA.
- A process crash during synchronous backtest execution may leave a stale `RUNNING` record;
  automatic recovery is not implemented. No result is fabricated for that record.
- Paper history is durable, but active in-memory execution is interrupted rather than resumed.
- Registered fixtures are small finite regression/demo inputs, not licensed market-data feeds.
- No distributed workers, HFT, options, futures, broker margin/borrow model, ML, or GPU strategies.

## Future Work

Possible future work—none included in v1.0.0—includes authenticated/public deployment,
lease-backed asynchronous job recovery, rolling live-data retention, additional asset classes,
advanced visualizations, and separately reviewed broker/ML/GPU research. Any real-money capability
requires a new security, compliance, and correctness review.

Use [DEMO.md](DEMO.md) for a 5–10 minute walkthrough, [ROADMAP.md](ROADMAP.md) for completed scope,
and [RELEASE_NOTES.md](RELEASE_NOTES.md) for v1.0.0 release notes.

> Research and education only. Simulated results do not guarantee future performance and are not
> financial advice.
