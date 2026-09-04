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

Phase 1 contains the operational foundations: configuration, logging, API routing, database session infrastructure, a migration baseline, health endpoint, frontend shell, and container orchestration. Phase 2 adds framework-independent financial contracts, deterministic domain events, and offline market-data ingestion. Phase 3 adds deterministic technical indicators and broker-independent, event-driven signal generation.

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

## Market-data flow

```text
CSV / future data source
          │
          ▼
MarketDataProvider
          │ normalized, immutable Bar objects
          ▼
MarketDataService
          │
          ▼
EventBus ── MARKET_DATA ──> future Strategy / Backtest consumers
```

`Bar` requires an aware timestamp and normalizes it to UTC. Prices are positive `Decimal` values, volume is a non-negative `Decimal` so providers can represent both share and fractional asset volume without precision loss, and OHLC relationships are validated. The CSV adapter maps `<SYMBOL>.csv` under a configured directory, validates the entire file before filtering, rejects duplicate columns, extra row values, duplicate UTC instants, and malformed rows, then returns an immutable chronological tuple. Date bounds are inclusive.

The in-process `EventBus` invokes a snapshot of handlers synchronously in registration order. It is intentionally fail-fast: a handler exception propagates to the publisher and later handlers do not run. Subscription changes made during a publish apply to the next event.

Market-bar persistence is deferred to the persistence/API phase. Phase 2 sources are read through `MarketDataProvider`; future PostgreSQL storage will implement the same boundary and add a unique/indexed `(symbol, timestamp)` key. This keeps research and backtesting independent of PostgreSQL and avoids a premature migration. The public market-data REST route remains deferred to Phase 7 for the same reason.

## Indicator and strategy flow

```text
MarketDataProvider -> MarketDataService -> Bar
                                         │
                                         ▼
                              EventBus / MARKET_DATA
                                         │
                                         ▼
                                  StrategyEngine
                                         │ registration order
                                         ▼
                                   BaseStrategy
                                         │ historical closes only
                                         ▼
                                     Indicators
                                         │
                                         ▼
                                      Signal
                                         │
                                         ▼
                                 EventBus / SIGNAL
```

SMA, EMA, Wilder RSI, MACD, and Bollinger Bands are focused pure calculations. They accept `Decimal` values, execute in a fixed 28-digit `ROUND_HALF_EVEN` decimal context, and return `None` until their complete input window is available. EMA uses the SMA of its first complete window as its seed. MACD applies that same rule to both price EMAs and to the signal EMA. Bollinger Bands use population standard deviation.

Each `BaseStrategy` instance supports one normalized symbol and receives completed `Bar` objects sequentially. It can retain only values derived from bars already delivered. A duplicate or older timestamp fails before processing, while `reset()` discards all observed history for deterministic replay. Moving-average crossover signals occur only on true short/long SMA crossings. RSI mean-reversion signals occur only when RSI crosses back into the neutral region from an extreme; strategies emit no `HOLD` events.

`StrategyEngine` subscribes to the existing `MARKET_DATA` event stream, routes a bar only to strategies for its symbol, invokes strategies in registration order, collects their trading intent, then publishes typed `SIGNAL` events in that same order. Signals use the completed bar's timestamp. The engine does not create orders, inspect portfolios, apply risk, access data providers, or interact with brokers.

Strategy processing is fail-fast. If a strategy raises while handling a market-data event, the exception propagates through `EventBus`, later strategies do not run, and the engine publishes no signals collected for that bar. A run that encounters a strategy exception must be treated as aborted; callers must reset or replace its strategies before replay rather than retrying the same bar against potentially advanced strategy-local state.

## Correctness contracts

Daily strategies see a bar only after it closes. A market order caused by that bar may first fill at the next available bar's open. Event order and fixture inputs must make runs repeatable. Commission and directional slippage are mandatory inputs; rejections and order transitions are recorded. The initial accounting model is long-only. Tests will explicitly cover timestamp alignment, no same-bar execution, fills, cash, average cost, PnL, and drawdown.

## Runtime separation and safety

Strategies target domain interfaces and cannot call a broker or data vendor directly. A runtime composition root will select `BACKTEST` or `PAPER` adapters. `LIVE` is rejected during configuration validation and can only be added through a separately reviewed roadmap item with unmistakable UI labeling and explicit opt-in.

Secrets enter through environment variables and are never logged. Large data, model weights, virtual environments, and architecture-specific dependencies remain outside Git.

## Portability

Configuration resolves paths from repository files via `pathlib`, not user home directories. Python 3.12 is pinned by `.python-version` and `pyproject.toml`; resolved Python packages are locked in `backend/requirements.lock`. Node 24 LTS is pinned by `.nvmrc` and `package.json`; npm is the sole Node package manager and `package-lock.json` is authoritative. Official images support ARM64 and x86_64, and CI continuously exercises Linux.

## Deployment shape

Docker Compose is the supported local topology. Production should build immutable images, use managed PostgreSQL/Redis or protected durable services, terminate TLS at an ingress, inject secrets from a secret manager, run Alembic once before application rollout, and expose only the frontend/API. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
