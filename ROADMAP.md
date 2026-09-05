# Roadmap

Each phase must be deterministic, documented, linted, and tested before dependent work begins. Correctness takes priority over headline performance.

## Phase 0 — Repository design (complete)

- Architecture and phased roadmap
- Cross-platform repository policies and Git workflow
- Initial modular-monolith directory boundaries

## Phase 1 — Foundation (complete)

- FastAPI app, safe settings, structured logging, CORS, and health endpoint
- SQLAlchemy async session foundation and Alembic baseline
- React/TypeScript/Vite application shell
- PostgreSQL, Redis, backend, and frontend Docker Compose topology
- Locked dependencies, standard Make commands, CI, and platform setup guides

## Phase 2 — Domain and market data (complete)

- Typed `Bar`, signal, order, fill, position, portfolio, and snapshot models
- Deterministic in-process event bus and event contracts
- `MarketDataProvider`, strict CSV adapter, data service, and deterministic fixtures
- Offline validation for ordering, filtering, timestamps, corrupt data, and event publication
- PostgreSQL bar persistence and HTTP transport intentionally deferred to Phase 7

## Phase 3 — Indicators and strategies (complete)

- Pure SMA, EMA, RSI, MACD, and Bollinger Band functions
- Broker-independent strategy interface and parameter metadata
- Moving-average crossover and RSI mean-reversion strategies
- Unit tests proving completed-bar-only inputs
- Strict per-symbol chronological processing, deterministic reset, and `MARKET_DATA` to `SIGNAL` event integration

## Phase 4 — Backtest and simulated execution (complete)

- Simulation clock and event-driven engine
- Order manager and explicit transition table
- Replaceable fixed/percentage commission and basis-point slippage
- Next-bar-open fill model, market and limit orders, and rejection paths
- Deterministic result records with manually verifiable next-Bar-open tests

## Phase 5 — Portfolio accounting and analytics (complete)

- Cash, positions, average cost, realized/unrealized PnL, and equity series
- Equity and drawdown series
- Return, CAGR, volatility, Sharpe, Sortino, exposure, and trade metrics
- Documented annualization and zero/negative-series behavior

## Phase 6 — Pre-trade risk and order management (complete)

- Immutable Order proposals and explicit approved/rejected Risk decisions
- Decimal position, Order-notional, symbol/gross-exposure, leverage, buying-power, and drawdown rules
- Deterministic OMS lifecycle, idempotency, same-Bar reservations, and release on Fill/broker rejection
- Simplified short exposure controls; stop Orders and broker margin/borrow rules remain deferred

## Phase 7 — Application API (complete)

- Synchronous backtest run lifecycle and application service over framework-independent protocols
- Approved dataset/strategy registries, idempotent submission, and bounded result collection APIs
- PostgreSQL audit persistence for runs, signals, proposals, decisions, orders, fills, snapshots, metrics, and reservations
- Alembic migration, exact Decimal/UTC serialization, atomic success writes, and durable failure records

## Phase 8 — Research dashboard

- TradingView Lightweight Charts candlesticks/volume/indicators
- Dynamic strategy forms, backtest workflow, results, trade markers, and responsive analytics

## Phase 9 — Paper trading

- Paper broker using shared order, fill, risk, and accounting paths
- Start/stop controls, account state, positions/orders/PnL, and WebSocket updates
- Persistent and unmistakable `PAPER TRADING` labeling

## Phase 10 — Hardening

- End-to-end fixtures, failure recovery, performance profiling, documentation polish, and deployment rehearsal

Only after the MVP acceptance flow passes should work begin on live adapters, additional assets, optimization, machine learning, GPU/CUDA, or native acceleration.
