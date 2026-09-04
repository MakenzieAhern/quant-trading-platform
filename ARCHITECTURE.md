# Architecture

## Goals and boundaries

The MVP supports US equities, daily OHLCV data, deterministic event-driven backtests, and paper trading. It is a modular monolith: module boundaries are explicit but deployment stays simple. Live brokerage, multiple asset classes, machine learning, distributed services, and GPU dependencies are deferred.

Architectural ideas are clean-room adaptations of established projects: [LEAN](https://github.com/QuantConnect/Lean) for engine boundaries and backtest/live separation, [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) and [vn.py](https://github.com/vnpy/vnpy) for event-driven processing and adapters, [Freqtrade](https://github.com/freqtrade/freqtrade) and [Jesse](https://github.com/jesse-ai/jesse) for strategy workflows, [vectorbt](https://github.com/polakowo/vectorbt) for future research sweeps, [Qlib](https://github.com/microsoft/qlib) for future feature/dataset boundaries, and [Hummingbot](https://github.com/hummingbot/hummingbot) for connector isolation. No source code is copied from those projects.

## System context

```text
Browser (React/TypeScript)
        │ REST / future WebSocket
        ▼
FastAPI modular monolith ─── Redis (cache and future transient events)
        │
        └────────────────── PostgreSQL (durable state, Alembic-managed)
```

Phase 1 contains operational foundations only: configuration, logging, API routing, database session infrastructure, a migration baseline, health endpoint, frontend shell, and container orchestration.

## Planned backend modules

```text
MarketDataProvider -> MarketDataEvent -> Strategy -> Signal
                                                 │
                                                 ▼
Portfolio <- Fill <- BrokerAdapter <- OrderManager <- RiskManager
    │
    └-> PortfolioSnapshot -> Analytics -> API/WebSocket
```

- `domain`: immutable typed financial concepts. `Decimal` is used for money/quantity where precision matters; timestamps are timezone-aware UTC.
- `event`: synchronous deterministic in-process bus first. Events carry typed payloads and preserve ordering.
- `data`: provider interfaces and normalized bars. CSV fixtures keep tests independent of external services.
- `strategies` and `indicators`: broker-agnostic signal generation and pure calculations.
- `risk`: converts permitted signals into order intent or records an explicit rejection reason.
- `execution`: order state machine and broker adapters. Backtest and paper adapters reuse fill/accounting rules.
- `portfolio`: the single accounting implementation for cash, positions, realized/unrealized PnL, and equity.
- `backtest`: simulation clock, next-bar execution, replaceable commission/slippage/fill models.
- `analytics`: equity, drawdown, returns, and trade statistics.
- `api`: thin transport adapters using explicit request/response schemas; no business logic or raw ORM responses.
- `db`: SQLAlchemy persistence models/repositories; migrations are the schema authority.

## Correctness contracts

Daily strategies see a bar only after it closes. A market order caused by that bar may first fill at the next available bar's open. Event order and fixture inputs must make runs repeatable. Commission and directional slippage are mandatory inputs; rejections and order transitions are recorded. The initial accounting model is long-only. Tests will explicitly cover timestamp alignment, no same-bar execution, fills, cash, average cost, PnL, and drawdown.

## Runtime separation and safety

Strategies target domain interfaces and cannot call a broker or data vendor directly. A runtime composition root will select `BACKTEST` or `PAPER` adapters. `LIVE` is rejected during configuration validation and can only be added through a separately reviewed roadmap item with unmistakable UI labeling and explicit opt-in.

Secrets enter through environment variables and are never logged. Large data, model weights, virtual environments, and architecture-specific dependencies remain outside Git.

## Portability

Configuration resolves paths from repository files via `pathlib`, not user home directories. Python 3.12 is pinned by `.python-version` and `pyproject.toml`; resolved Python packages are locked in `backend/requirements.lock`. Node 24 LTS is pinned by `.nvmrc` and `package.json`; npm is the sole Node package manager and `package-lock.json` is authoritative. Official images support ARM64 and x86_64, and CI continuously exercises Linux.

## Deployment shape

Docker Compose is the supported local topology. Production should build immutable images, use managed PostgreSQL/Redis or protected durable services, terminate TLS at an ingress, inject secrets from a secret manager, run Alembic once before application rollout, and expose only the frontend/API. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
