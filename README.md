# Quant Trading Platform

A portfolio-grade personal platform for deterministic US-equity research, realistic backtesting, risk-controlled execution, and paper trading. The MVP is deliberately **research/backtest/paper only**; real-money trading is disabled.

## Architecture

The project is a modular monolith: React/Vite provides the dashboard, FastAPI exposes APIs, PostgreSQL persists trading state, and Redis supports cache/event delivery. Trading capabilities will share a typed event-driven core so strategies do not depend on market-data or broker vendors. See [ARCHITECTURE.md](ARCHITECTURE.md).

**Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Redis, React, TypeScript, Vite, pytest, Vitest, and Docker Compose. Pandas, NumPy, SciPy, and TradingView Lightweight Charts join in the phases that first use them.

**Current features:** reproducible Phase 1 environment, safe configuration, structured logs, database migrations, health API, tested frontend shell, and Linux CI. Phases 2–6 provide typed financial contracts, offline CSV ingestion, Decimal indicators, broker-independent strategies, deterministic event-driven backtests, simulated execution, portfolio accounting, analytics, pre-trade risk, and OMS reservations. Phase 7 adds a synchronous backtest application service, PostgreSQL audit persistence, an approved dataset/strategy registry, and paginated REST result APIs. Dashboard and paper execution remain sequenced in the [roadmap](ROADMAP.md).

## Quick start

Prerequisites: Docker Desktop with Compose. On Windows, use Ubuntu in WSL2 with Docker Desktop integration.

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:5173>; API health is at <http://localhost:8000/api/health> and OpenAPI at <http://localhost:8000/docs>. Stop with `docker compose down`.

The Compose backend applies Alembic migrations after PostgreSQL becomes healthy. A deterministic example run can be submitted with:

```bash
curl -X POST http://localhost:8000/api/backtests \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: example-aapl-ma' \
  -d '{"dataset_id":"AAPL_fixture","symbol":"AAPL","strategy":{"type":"moving_average_crossover","parameters":{"short_period":2,"long_period":3}},"initial_cash":"100000","default_order_quantity":"10"}'
```

Financial inputs and outputs use JSON strings. Phase 7 accepts only registered datasets and the `moving_average_crossover` and `rsi_mean_reversion` strategy types; filesystem paths and Python import names are not accepted.

For host-based development, install Python 3.12, Node 24 LTS, and GNU Make, then:

```bash
make setup
docker compose up -d postgres redis
make migrate
make backend       # terminal 1
make frontend      # terminal 2
```

Run validation with `make test` and `make lint`.

## Supported development environments

- macOS on Apple Silicon: [Mac setup](docs/MAC_SETUP.md)
- Windows 11 using Ubuntu/WSL2: [Windows + WSL2 setup](docs/WINDOWS_WSL_SETUP.md)
- Container images are official multi-architecture images; no architecture-specific virtual environment or `node_modules` is committed.

More detail: [development guide](docs/DEVELOPMENT.md), [Git workflow](docs/GIT_WORKFLOW.md), [deployment notes](docs/DEPLOYMENT.md), and [contributing guide](CONTRIBUTING.md).

> This software is for research and education. Simulated results do not guarantee future performance. It does not provide financial advice and must not be used for real-money trading without an independent security, compliance, and correctness review.
