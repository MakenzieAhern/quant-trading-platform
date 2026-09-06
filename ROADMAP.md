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

## Phase 8 — Research dashboard (complete)

- Typed Phase 7 API client, stable history/create/detail routes, and bounded collection pagination
- Registry-constrained dynamic strategy forms with idempotent submission and safe status/error handling
- Persisted performance summary, lightweight accessible equity chart, and signal/risk/order/fill audit tables
- Exact Decimal-string rendering, explicitly labeled UTC timestamps, and Docker/browser integration coverage
- Candlesticks, volume, additional indicators, and trade-marker overlays remain future dashboard enhancements rather than being fabricated from the current Phase 7 API

## Phase 9 — Paper trading (complete)

- Local-only PaperBroker using shared Order, Fill, risk, OMS, and portfolio paths
- Registered completed-Bar replay provider with deterministic next-Bar OPEN semantics
- Durable session lifecycle and typed event journal with explicit restart interruption
- REST hydration plus bounded WebSocket updates and conservative reconnect/resync
- Start/stop controls, portfolio/orders/fills, and unmistakable `PAPER TRADING` labeling
- Reviewed atomic lifecycle/event persistence, deterministic event ordering, retry-safe commands,
  accepted-order cancellation, restart recovery, and isolated concurrent sessions
- Verified bounded slow-client resynchronization, disconnect cleanup, terminal socket closure,
  browser refresh/reconnect persistence, and repeated-session resource cleanup
- No live broker connectivity, credentials, external order routing, GPU, or ML dependencies

## Phase 10 — MVP hardening and release readiness (complete)

- Final supported MVP: registered historical CSV data, technical indicators, strategy signals,
  deterministic backtesting, simulated orders and transaction costs, portfolio accounting,
  performance analytics, risk management, OMS, PostgreSQL persistence, REST APIs,
  backtest dashboard, paper replay sessions, realtime WebSocket updates, and lifecycle control.
- Golden-path tests, reproducible Docker/WSL commands, security and configuration review,
  restart durability, measured performance baselines, and a documented demonstration.
- Completed local simulated-MVP acceptance and focused review; evidence and limitations
  are recorded in `docs/RELEASE_VALIDATION.md`. Public/live deployment is not certified.

## Beyond the MVP (not implemented)

Live brokerage, real-money orders, broker credentials, ML, GPU strategies, distributed workers,
HFT, options, futures, and broker margin/borrow simulation beyond the documented cash and
exposure semantics are unsupported. Advanced data feeds and additional asset classes are
future work, not release capabilities. The shipped product is local simulated trading only.

Only after the MVP acceptance flow passes should work begin on live adapters, additional assets, optimization, machine learning, GPU/CUDA, or native acceleration.
