# v1.1.0 — China A-Share Research Edition

> **PAPER / SIMULATED ONLY. NO LIVE BROKER. NO REAL-MONEY EXECUTION.**

## Highlights

- Immutable 2010–2025 ordinary A-share dataset: 5,431 securities, 3,886 sessions,
  13,411,189 raw daily rows and 42,792 corporate-action rows.
- Point-in-time identity, listing/delisting, ST/*ST, suspension, market-rule and transaction-cost
  resolution with explicit source lineage and checksums.
- Corporate-action-aware research accounting for cash/rights events, mergers, demergers,
  mandatory partial surrenders, restructuring pass-through and share consolidations.
- Frozen S0–S4 Development family, one-run Validation protocol, Gate C methodology freeze and an
  exactly-once Official OOS lock.
- Bilingual A-share research UI with dataset lineage, methodology, CSI300 comparison, equity,
  drawdown, rolling metrics, monthly returns, holdings, rebalances and fills.
- Idempotent publication of immutable Development, Validation and OOS artifacts to PostgreSQL.
- Bilingual local Paper simulation for the frozen A-share strategy on a deterministic synthetic
  2030 scenario, reusing the reviewed risk, OMS, simulated execution and portfolio path.

## Result boundary

No candidate passed every Validation gate. Unchanged S4 was the pre-declared fallback. Official
OOS returned 0.76% with Sharpe 0.067, maximum drawdown -15.70% and 6.61% excess versus a declining
CSI300. This is weak evidence and is not a profitability or future-return claim. The OOS run limit
is consumed; no retuning occurred.

## Compatibility and safety

The v1.0 deterministic backtest and local Paper runtime remain available. The A-share Paper
scenario is product validation, not research evidence, and does not replay Official OOS. v1.1 adds
no live-broker adapter, brokerage credentials, public-internet deployment, real-money execution,
ML/GPU strategy, or Hong Kong/US market scope. Large market datasets and formal run artifacts
remain outside Git.

See [dataset](docs/research/DATASET.md), [methodology](docs/research/METHODOLOGY.md),
[strategy](docs/research/STRATEGY_REPORT.md), [OOS](docs/research/OOS_REPORT.md),
[reproducibility](docs/research/REPRODUCIBILITY.md) and
[limitations](docs/research/LIMITATIONS.md).

---

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
