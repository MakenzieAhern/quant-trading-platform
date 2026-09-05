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

Phase 1 contains the operational foundations: configuration, logging, API routing, database session infrastructure, a migration baseline, health endpoint, frontend shell, and container orchestration. Phase 2 adds framework-independent financial contracts, deterministic domain events, and offline market-data ingestion. Phase 3 adds deterministic technical indicators and broker-independent, event-driven signal generation. Phase 4 adds a historical simulation clock, event-driven backtest coordination, and deterministic simulated execution. Phase 5 adds downstream portfolio accounting, end-of-Bar valuation, an equity curve, and performance analytics.

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

## Backtest and execution flow

```text
Historical MarketDataProvider
             │
             ▼
       BacktestEngine
             │
             ▼
      SimulationClock
             │
             ▼
 EventBus / MARKET_DATA -> StrategyEngine -> EventBus / SIGNAL
                                                   │
                                                   ▼
                                         MARKET Order creation
                                                   │
                                                   ▼
                                         SimulatedBroker queue
                                                   │ next same-symbol Bar
                                                   ▼
                                      next-Bar OPEN + adverse slippage
                                                   │
                                                   ▼
                                         Fill + commission
```

The simulation clock advances only from timezone-aware historical timestamps and never reads wall-clock time. Provider output is validated before a run: every Bar must match the requested symbol and timestamps must be strictly increasing. Each run resets clock, strategy, order, fill, and signal state.

Within each completed daily Bar the event order is fixed:

1. advance the simulation clock to the Bar timestamp;
2. execute accepted MARKET orders from earlier signals for that symbol at the current Bar open;
3. publish their `ORDER_FILLED` events;
4. publish `MARKET_DATA` for the current completed Bar;
5. let strategies publish `SIGNAL` events in registration order;
6. translate each BUY/SELL Signal to a fixed-quantity MARKET Order;
7. publish `ORDER_CREATED`, `ORDER_SUBMITTED`, and `ORDER_ACCEPTED`, then queue the Order.

Consequently an Order created from Bar T cannot use any price from Bar T and first becomes eligible at the next Bar for its symbol. Its Fill timestamp is that later Bar timestamp. An Order created on the final Bar remains visibly `ACCEPTED` and unfilled; no final-close fill is invented. Phase 4 supports all-or-nothing MARKET Orders only. Existing LIMIT Orders are deterministically moved from `SUBMITTED` to `REJECTED`, because daily OHLC data cannot establish an unambiguous intrabar path.

Order transitions are explicit and immutable: `CREATED -> SUBMITTED -> ACCEPTED -> FILLED`, with `SUBMITTED -> REJECTED` for unsupported execution. Invalid transitions fail immediately. `ORDER_FILLED` carries the immutable Fill, which includes order and strategy identity, side, quantity, adverse-slippage price, non-negative commission, and execution timestamp.

Transaction costs use replaceable protocols. `FixedCommission` charges one configured Decimal amount per fill. `PercentageCommission` treats its configured rate as a fraction of absolute filled notional, so its result cannot become negative if a signed quantity is supplied at the model boundary. `FixedBasisPointSlippage` increases BUY prices and decreases SELL prices by `basis_points / 10000`; favorable slippage is rejected. Basis points must be non-negative and strictly below 10,000 so adverse SELL slippage cannot produce a zero or negative fill price. Execution arithmetic uses an isolated 28-digit `ROUND_HALF_EVEN` Decimal context and never converts financial values to float.

The backtest result retains ordered Signals, final Order states, Fills, historical bounds, and configuration. Phase 5 extends it with immutable portfolio snapshots, an equity curve, and performance metrics without changing Phase 4 execution.

## Portfolio accounting and analytics flow

```text
Historical Bar -> BacktestEngine -> MARKET_DATA -> Strategy -> Signal -> Order
                         │                                      │
                         │                         next-Bar OPEN ▼
                         └-> PortfolioSnapshot <- Portfolio <- Fill <- Broker
                                              │
                                              ▼
                                      Equity + Analytics
```

`PortfolioEngine` subscribes to successful `ORDER_FILLED` events and records what execution produced; it never creates, sizes, approves, or rejects trades. BUY cash flow is `-(quantity * fill price) - commission`, and SELL cash flow is `+(quantity * fill price) - commission`. Fill price already includes Phase 4 slippage. Commissions reduce cash exactly once, remain outside price-movement realized PnL, and are also accumulated separately for reporting. Negative cash is recorded rather than rejected because capital limits belong to Phase 6. Fill and market-data timestamps share one monotonic portfolio clock; equal timestamps support deterministic multi-symbol updates, while any older event is rejected before it can contaminate historical state.

Positions use signed quantities: positive is long, negative is short, and zero is flat. Same-direction fills use absolute-quantity weighted average cost. Reductions preserve average cost and realize long PnL as `closed quantity * (sell price - average cost)` or short PnL as `closed quantity * (average cost - buy price)`. A fill crossing zero closes the old position at its prior basis and opens the remainder in the opposite direction at the reversing fill price. Flat per-symbol records remain in snapshots so cumulative realized PnL stays auditable.

For each completed daily Bar, old accepted orders first fill at its OPEN and the portfolio consumes those fills. On `MARKET_DATA`, PortfolioEngine updates only that symbol's mark to the completed Bar CLOSE, retains the latest already-observed marks for other symbols, creates and publishes an end-of-Bar `PortfolioSnapshot`, and then StrategyEngine processes the same completed Bar. Thus valuation cannot leak a future price or change next-Bar execution. Snapshot market value is the sum of `signed quantity * latest mark`; unrealized PnL is `signed quantity * (mark - average cost)`; equity is cash plus signed market value. Snapshot ordering is chronological and deterministic. Snapshots contain frozen copies of position records, so later fills and marks cannot mutate history.

Analytics consumes snapshots only. Its equity curve contains one point per timestamp; when asynchronously updated symbols produce the same timestamp, the last snapshot in deterministic event order is the end-of-time-point state and replaces earlier same-time points. This prevents one investment period from being counted more than once. Total return is `final equity / initial equity - 1`, and a non-positive initial equity is an explicit error. Period return is `current / previous - 1`; non-positive previous equity is an explicit error because percentage performance from a zero or negative capital base is not treated as financially defined. Maximum drawdown is reported as the most negative peak-to-trough return, so the sequence `100, 120, 90, 110` reports `-0.25`.

Sharpe and Sortino use configurable `periods_per_year` (252 by default for daily observations) and an explicit per-period risk-free rate (zero by default). Sharpe uses population standard deviation of excess period returns. Sortino uses the root mean square of negative excess returns over all observed periods. Fewer than two returns, zero volatility, or zero downside deviation produces `None`, never infinity. CAGR uses a 365.2425-day year and isolated 28-digit `ROUND_HALF_EVEN` Decimal arithmetic; it is `None` for non-positive duration or non-positive final equity. Analytics is pure downstream output and cannot influence strategies, orders, fills, or the portfolio.

## Correctness contracts

Daily strategies see a bar only after it closes. A market order caused by that bar may first fill at the next available bar's open. Event order and fixture inputs must make runs repeatable. Commission and directional slippage are mandatory inputs; rejections and order transitions are recorded. Portfolio accounting supports both long and short fills but never makes risk or strategy decisions. Tests keep execution timing separate from downstream cash, cost-basis, PnL, valuation, and analytics calculations.

## Runtime separation and safety

Strategies target domain interfaces and cannot call a broker or data vendor directly. A runtime composition root will select `BACKTEST` or `PAPER` adapters. `LIVE` is rejected during configuration validation and can only be added through a separately reviewed roadmap item with unmistakable UI labeling and explicit opt-in.

Secrets enter through environment variables and are never logged. Large data, model weights, virtual environments, and architecture-specific dependencies remain outside Git.

## Portability

Configuration resolves paths from repository files via `pathlib`, not user home directories. Python 3.12 is pinned by `.python-version` and `pyproject.toml`; resolved Python packages are locked in `backend/requirements.lock`. Node 24 LTS is pinned by `.nvmrc` and `package.json`; npm is the sole Node package manager and `package-lock.json` is authoritative. Official images support ARM64 and x86_64, and CI continuously exercises Linux.

## Deployment shape

Docker Compose is the supported local topology. Production should build immutable images, use managed PostgreSQL/Redis or protected durable services, terminate TLS at an ingress, inject secrets from a secret manager, run Alembic once before application rollout, and expose only the frontend/API. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
