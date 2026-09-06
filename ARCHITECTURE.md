# Architecture

## Goals and boundaries

The MVP supports US equities, daily OHLCV data, deterministic event-driven backtests, and paper trading. It is a modular monolith: module boundaries are explicit but deployment stays simple. Live brokerage, multiple asset classes, machine learning, distributed services, and GPU dependencies are deferred.

Architectural ideas are clean-room adaptations of established projects: [LEAN](https://github.com/QuantConnect/Lean) for engine boundaries and backtest/live separation, [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) and [vn.py](https://github.com/vnpy/vnpy) for event-driven processing and adapters, [Freqtrade](https://github.com/freqtrade/freqtrade) and [Jesse](https://github.com/jesse-ai/jesse) for strategy workflows, [vectorbt](https://github.com/polakowo/vectorbt) for future research sweeps, [Qlib](https://github.com/microsoft/qlib) for future feature/dataset boundaries, and [Hummingbot](https://github.com/hummingbot/hummingbot) for connector isolation. No source code is copied from those projects.

## System context

```text
Browser (React/TypeScript)
        │ REST / typed WebSocket
        ▼
FastAPI modular monolith ─── Redis (cache and future transient events)
        │
        └────────────────── PostgreSQL (durable state, Alembic-managed)
```

Phase 1 contains the operational foundations: configuration, logging, API routing, database session infrastructure, a migration baseline, health endpoint, frontend shell, and container orchestration. Phase 2 adds framework-independent financial contracts, deterministic domain events, and offline market-data ingestion. Phase 3 adds deterministic technical indicators and broker-independent, event-driven signal generation. Phase 4 adds a historical simulation clock, event-driven backtest coordination, and deterministic simulated execution. Phase 5 adds downstream portfolio accounting, end-of-Bar valuation, an equity curve, and performance analytics. Phase 6 adds order proposals, deterministic pre-trade risk decisions, an order management system, and sequential risk reservations. Phase 7 adds an application orchestration boundary, PostgreSQL repositories, and thin REST transport adapters without introducing framework dependencies into the Phase 2–6 engine.

Phase 8 adds a display-only React dashboard over the Phase 7 REST boundary. The typed client performs runtime response validation before state reaches components. Financial JSON strings remain strings through transport, state, tables, and metric labels; conversion to JavaScript numbers is isolated to approximate SVG coordinates and has an explicit non-finite fallback. The browser does not regenerate signals, infer execution or risk state, or recalculate accounting and analytics. Request timeouts, effect cleanup, and active-request identity guards prevent abandoned or older routes from overwriting current state. Only `CREATED` and `RUNNING` detail views poll, one completed request at a time, and terminal state or unmount removes the timer.

## Paper trading runtime and delivery boundary

```text
Registered replay provider -> completed Bar -> per-session EventBus -> StrategyEngine
                                                              -> RiskEngine -> OMS
                                                              -> local PaperBroker
                                                              -> Fill -> PortfolioEngine
                                                              -> PostgreSQL event journal
                                                              -> bounded WebSocket fan-out
REST snapshot ----------------------------------------------------------> React
```

Phase 9 reuses the reviewed strategy, risk, OMS, simulated next-Bar OPEN execution, and portfolio engines. `PaperTradingRuntime` is independent of `BacktestEngine`; every session constructs its own EventBus, strategies, PaperBroker, OMS reservations, RiskEngine, PortfolioEngine, provider subscription, and task. The process-level manager coordinates these isolated runtimes but is not a shared trading engine. The only provider is the registered, local `ReplayMarketDataProvider`; it emits immutable completed Bars in strict chronological order and never connects to a network vendor or accepts paths/URLs from clients.

Phase 9 runtime collections are bounded by the finite, registered replay dataset; the runtime, provider, strategies, OMS, broker, and their in-memory histories are released when the session task reaches a terminal state. Durable history belongs to PostgreSQL. This finite-replay bound is not a claim that the same collections are ready for an endless vendor feed; any future streaming adapter must introduce explicit rolling retention before it is eligible for use.

The lifecycle is `CREATED -> STARTING -> RUNNING -> STOPPING -> STOPPED`, with terminal `FAILED` and `INTERRUPTED` outcomes. Creation, start, and stop are retry-safe. Lifecycle and typed market/signal/risk/order/fill/portfolio events are appended to PostgreSQL in deterministic sequence. A per-session row lock serializes sequence allocation; lifecycle state and its event commit in one transaction, and each completed-Bar financial batch commits before WebSocket publication. Pending local Orders are explicitly moved from `ACCEPTED` to `CANCELLED` on stop/failure/interruption and their OMS reservations are released before the terminal batch is stored. REST snapshots reconstruct current state from that durable journal and are the recovery authority. An active in-memory runtime is never resumed after process loss: graceful shutdown marks it `INTERRUPTED`, and startup converts any orphaned active row to `INTERRUPTED` before serving traffic.

For each completed replay Bar, the durable delivery order is `market.bar`, any prior accepted Order's `order.updated` to `FILLED`, its `fill.created`, current-Bar `signal.created`, `risk.decision`, newly accepted/rejected `order.updated`, then `portfolio.snapshot`. This reflects next-Bar OPEN execution before the strategy consumes that completed Bar while still recording the newly observed Bar first for consumers. A single transaction stores the whole sequence, and WebSocket publication happens only after commit.

WebSocket delivery is incremental, not authoritative history. Every connection owns a bounded queue of 64 events. Publishing never awaits a browser. When a consumer falls behind, all stale queued items are discarded, then `stream.resync_required` and the newest event occupy the bounded queue; the client closes and reloads REST rather than applying that uncertain increment. Server-side receive monitoring detects a disconnected client even when no market event is being sent, so the queue is removed promptly. The React client connects, hydrates REST, applies only increasing event sequences, deduplicates record identities, strictly validates event envelopes and payloads, and performs authoritative rehydration on reconnect. Terminal sessions close the socket without reconnecting. Origin checks use the configured frontend origin. Payload DTOs expose only explicit JSON fields and Decimal strings—never ORM or arbitrary Python objects.

**There is no live broker connectivity in the Phase 9 MVP.** `PaperBroker` is local simulation only. No brokerage credentials, external order endpoints, dynamic providers, or real-money routes exist.

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
- `risk`: purely evaluates typed order proposals against observed portfolio state, explicit limits, and OMS reservations.
- `execution`: order state machine and broker adapters. Backtest and paper adapters reuse fill/accounting rules.
- `portfolio`: the single accounting implementation for cash, positions, realized/unrealized PnL, and equity.
- `backtest`: simulation clock, next-bar execution, replaceable commission/slippage/fill models.
- `analytics`: equity, drawdown, returns, and trade statistics.
- `api`: thin transport adapters using explicit request/response schemas; no business logic or raw ORM responses.
- `db`: SQLAlchemy persistence models/repositories; migrations are the schema authority.

## Backtest application and persistence boundary

```text
REST request -> BacktestApplicationService -> approved dataset + strategy registries
                         │                              │
                         │                              ▼
                         │                       fresh BacktestEngine
                         ▼                              │
               BacktestRepository protocol <----------┘
                         │
                         ▼
                SQLAlchemy/PostgreSQL
```

Each request constructs fresh mutable engine, strategy, risk, OMS, broker, and portfolio state. The application service owns the explicit `CREATED -> RUNNING -> SUCCEEDED|FAILED` lifecycle; it does not reproduce indicators, execution, risk, accounting, or analytics. Application code depends on a repository protocol, while the SQLAlchemy implementation stays in `db`. Synchronous execution is deliberate for Phase 7 and the service boundary permits a future job runner without changing the engine.

Only logical dataset identifiers from the registry can reach a provider. `AAPL_fixture` maps to source-controlled data under the configured fixture root, and the API never accepts a filesystem path. Strategy construction likewise uses an explicit registry containing only the two reviewed Phase 3 strategies; dynamic imports and evaluation are prohibited. An optional `Idempotency-Key` is stored under a database unique constraint with a canonical request hash. Decimal spellings such as `100000.0` and `100000.000`, JSON object key order, and omitted versus explicit defaults produce the same fingerprint. Concurrent identical submissions converge on the single terminal run; conflicting content returns a conflict. A duplicate request that finds a non-terminal run waits for the owning synchronous request for at most 60 seconds, then returns a retryable conflict rather than executing again.

Run metadata is committed at `CREATED`, then `RUNNING`. Signals, proposals, every risk decision (including rejections), final Order states, Fills, snapshots, metrics, and active end-of-run risk reservations are inserted in one transaction with the `SUCCEEDED` transition. A write failure rolls back that complete result and is followed, where safely possible, by a separate `FAILED` transition. Error summaries contain an exception class and stable context only, never a traceback or exception text that could contain paths or secrets.

All financial database columns use PostgreSQL `NUMERIC(78, 38)`: at most 40 integral and 38 fractional digits. No Decimal crosses persistence through `float`. The API and repository reject excess integer digits or scale before PostgreSQL can overflow or silently round; accepted values are stored exactly. REST financial values are canonical non-exponent JSON strings, and undefined metrics remain SQL/JSON null. Snapshot positions use JSONB to avoid a high-cardinality join for immutable snapshot reads; every numeric member is validated against the same precision contract and encoded as a Decimal string. This makes JSONB less convenient for numeric SQL aggregation, a deliberate tradeoff because normalized snapshot totals remain queryable columns. Risk reservations are a separate audit table and are never interpreted as cash or positions.

Collection endpoints order by per-run sequence and enforce `1 <= limit <= 200`. Run lists query metadata only and do not load child events. Repository reads reconstruct the complete ordered domain result from PostgreSQL without process memory. PostgreSQL primary/unique keys preserve deterministic sequence, proposal, and Order identity. Composite foreign keys connect decisions to proposals, Orders to proposals, Fills to Orders, and reservations to their proposal and Order. Run foreign keys use `RESTRICT`: audit history cannot be removed by casually deleting its parent run, while migration downgrade explicitly removes children in dependency order.

Phase 7 execution is intentionally synchronous. FastAPI creates and closes one `AsyncSession` per request, and transaction context managers roll back on exceptions or cancellation. A client disconnect does not provide durable job ownership: cancellation or a process crash after `RUNNING` may leave a stale run because Phase 7 has no worker or recovery lease. Operators can identify those rows by status and timestamps. Automated stale-run recovery, durable cancellation, queues, and workers are explicitly deferred to a future job-execution phase; Phase 7 does not claim crash-safe execution recovery.

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
                                          OrderProposal
                                                   │
                                                   ▼
                                       RiskEngine -> RiskDecision
                                                   │ approved
                                                   ▼
                                          OMS -> MARKET Order
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
6. translate each BUY/SELL Signal to a deterministic fixed-quantity `OrderProposal`;
7. evaluate the proposal using the completed Bar close, current portfolio snapshot, and earlier active reservations;
8. publish a `RISK_DECISION`; stop before Order creation when rejected;
9. let the OMS create an approved MARKET Order, publish `ORDER_CREATED`, and submit it to the broker;
10. publish `ORDER_SUBMITTED` and `ORDER_ACCEPTED`, then queue the Order.

Consequently an Order created from Bar T cannot use any price from Bar T and first becomes eligible at the next Bar for its symbol. Its Fill timestamp is that later Bar timestamp. An Order created on the final Bar remains visibly `ACCEPTED` and unfilled; no final-close fill is invented. Phase 4 supports all-or-nothing MARKET Orders only. Existing LIMIT Orders are deterministically moved from `SUBMITTED` to `REJECTED`, because daily OHLC data cannot establish an unambiguous intrabar path.

Order transitions are explicit and immutable: `CREATED -> SUBMITTED -> ACCEPTED -> FILLED`, with `SUBMITTED -> REJECTED` for unsupported execution. Invalid transitions fail immediately. `ORDER_FILLED` carries the immutable Fill, which includes order and strategy identity, side, quantity, adverse-slippage price, non-negative commission, and execution timestamp.

Transaction costs use replaceable protocols. `FixedCommission` charges one configured Decimal amount per fill. `PercentageCommission` treats its configured rate as a fraction of absolute filled notional, so its result cannot become negative if a signed quantity is supplied at the model boundary. `FixedBasisPointSlippage` increases BUY prices and decreases SELL prices by `basis_points / 10000`; favorable slippage is rejected. Basis points must be non-negative and strictly below 10,000 so adverse SELL slippage cannot produce a zero or negative fill price. Execution arithmetic uses an isolated 28-digit `ROUND_HALF_EVEN` Decimal context and never converts financial values to float.

The backtest result retains ordered Signals, final Order states, Fills, historical bounds, and configuration. Phase 5 extends it with immutable portfolio snapshots, an equity curve, and performance metrics without changing Phase 4 execution.

Phase 6 additionally retains every ordered `OrderProposal` and `RiskDecision`, plus immutable active `RiskReservation` records for accepted Orders that have not reached a terminal state. Permissive `RiskConfig` defaults preserve the exact Phase 4 Order IDs, next-Bar-open timestamps, fill prices, and commissions for approved proposals.

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

## Pre-trade risk and OMS flow

```text
Signal -> ORDER_PROPOSAL -> RiskEngine -> RISK_DECISION
                                           │
                         rejected ──────────┴──> no Order and no broker submission
                                           │ approved
                                           ▼
                              OMS reservation + ORDER_CREATED
                                           │
                                           ▼
                          broker SUBMITTED -> ACCEPTED -> FILLED
                                           │
                                           ▼
                         reservation release; Fill updates Portfolio
```

`OrderProposal` is immutable broker-independent intent with a deterministic proposal ID, strategy and symbol identity, side, type, quantity, and Signal timestamp. The approved Order deliberately reuses that proposal ID, preserving the established deterministic Order IDs. `RiskDecision` is immutable and includes an explicit reason code plus Decimal diagnostics for reference price, projected position, cash, symbol/gross/net exposure, and leverage. A risk rejection is not represented as a broker-rejected Order: no Order is created or submitted. A later broker rejection remains an ordinary `SUBMITTED -> REJECTED` Order transition and releases its reservation.

`RiskConfig` independently controls maximum Order notional, absolute per-symbol position quantity, symbol exposure, gross exposure, gross leverage, optional cash buying power, and maximum tolerated drawdown. Every limit defaults to disabled, which is the permissive regression configuration. MARKET risk notional uses only the target symbol's latest completed-Bar close; it never reads the future execution OPEN. The buying-power estimate uses that observed mark plus the configured commission model. Earlier accepted BUY Orders reserve their full marked cost and commission. Pending SELL proceeds are not available to fund later proposals before execution. This is a conservative cash check, not a broker margin, borrow, or locate model. Short selling remains supported through the same exposure and leverage rules.

Risk evaluates the projected signed position after the proposal. Gross exposure is the sum of absolute marked positions, net exposure is their signed sum, and gross leverage is projected gross exposure divided by current observed equity only when that equity is positive. Missing or non-positive marks, inconsistent snapshots, non-finite reservation inputs, and risk-increasing proposals with non-positive actual or projected equity produce deterministic invalid-state decisions rather than division by zero.

A proposal is genuinely risk-reducing only when it lowers the target symbol's absolute quantity without crossing through zero into a non-flat opposite position. With fixed observed marks and current-equity leverage, this strictly lowers the relevant position, symbol-exposure, gross-exposure, and leverage dimensions; only those genuine reductions may proceed while the portfolio remains above those limits. The same reduction policy permits an orderly short cover despite a cash or drawdown breach. Reversals are risk-increasing and must satisfy every configured limit. Maximum Order notional remains an operational per-Order limit for both increases and reductions. The drawdown guard never creates liquidation Orders by itself.

The OMS evaluates same-Bar proposals sequentially in StrategyEngine registration/event order. Each approval reserves projected signed quantity, mark-based cash, estimated commission, and separately tracked BUY buying power without mutating PortfolioEngine. Later proposals see actual portfolio state plus all active reservations, preventing combined position, symbol exposure, gross exposure, leverage, or buying-power breaches across symbols. A Fill first updates PortfolioEngine through the existing event path and then releases the reservation; a broker rejection or submission failure also releases it. Failures while publishing a decision or creating/submitting an Order propagate and roll back partial OMS reservations and registrations; an aborted event-driven run must still be reset before replay. Identical reprocessing returns the existing decision/Order, while conflicting reuse of a proposal ID, unknown or double reservation release, and illegal Order transitions fail explicitly. All OMS and reservation state resets between backtests.

An accepted final-Bar Order cannot fill because no later Bar exists. It therefore remains `ACCEPTED`, and its immutable active reservation is exposed in `BacktestResult` rather than discarded or converted into a fabricated Fill. The next run resets that OMS-only projected state. Historical cash, positions, snapshots, PnL, and analytics remain driven solely by real Fill events.

## Correctness contracts

Daily strategies see a bar only after it closes. A market order caused by that bar may first fill at the next available bar's open. Event order and fixture inputs must make runs repeatable. Commission and directional slippage are mandatory inputs; risk decisions, broker rejections, and order transitions remain distinct and recorded. Portfolio accounting supports both long and short fills but never makes risk or strategy decisions. Tests keep risk reference marks and reservations separate from execution timing and downstream cash, cost-basis, PnL, valuation, and analytics calculations.

## Runtime separation and safety

Strategies target domain interfaces and cannot call a broker or data vendor directly. A runtime composition root will select `BACKTEST` or `PAPER` adapters. `LIVE` is rejected during configuration validation and can only be added through a separately reviewed roadmap item with unmistakable UI labeling and explicit opt-in.

Secrets enter through environment variables and are never logged. Large data, model weights, virtual environments, and architecture-specific dependencies remain outside Git.

## Research dashboard boundary

The Phase 8 React application is a presentation client for the Phase 7 REST API. Its typed transport layer lives under `frontend/src/api`, API response models under `frontend/src/types`, reusable view components under `frontend/src/components`, and route-level orchestration under `frontend/src/pages`. Browser History API routes make persisted runs directly addressable without introducing another application framework.

React never recreates signals, risk decisions, portfolio accounting, fills, or analytics. Financial values remain Decimal strings from request through rendering. Formatting helpers operate on strings; the equity chart converts values to JavaScript numbers only to derive SVG screen coordinates and retains exact strings in its accessible table and labels. UTC API timestamps are displayed through an explicit UTC formatter rather than converted to unlabeled local time.

The create form exposes only the registered `AAPL_fixture` dataset and the two registered strategy discriminators. Each submission receives a browser-generated `Idempotency-Key`, retains that key across a retry of unchanged inputs, and locks concurrent submissions. Active detail pages conservatively poll only `CREATED` or `RUNNING` runs every five seconds. All terminal results reload from PostgreSQL through the API; no quantitative result is kept solely in browser memory.

## Portability

Configuration resolves paths from repository files via `pathlib`, not user home directories. Python 3.12 is pinned by `.python-version` and `pyproject.toml`; resolved Python packages are locked in `backend/requirements.lock`. Node 24 LTS is pinned by `.nvmrc` and `package.json`; npm is the sole Node package manager and `package-lock.json` is authoritative. Official images support ARM64 and x86_64, and CI continuously exercises Linux.

## Deployment shape

Docker Compose is the supported local topology. Production should build immutable images, use managed PostgreSQL/Redis or protected durable services, terminate TLS at an ingress, inject secrets from a secret manager, run Alembic once before application rollout, and expose only the frontend/API. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
