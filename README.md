# Quant Trading Platform

A portfolio-grade personal platform for deterministic US-equity research, realistic backtesting, risk-controlled execution, and paper trading. The MVP is deliberately **research/backtest/paper only**; real-money trading is disabled.

## Architecture

The project is a modular monolith: React/Vite provides the dashboard, FastAPI exposes APIs, PostgreSQL persists trading state, and Redis supports cache/event delivery. Trading capabilities will share a typed event-driven core so strategies do not depend on market-data or broker vendors. See [ARCHITECTURE.md](ARCHITECTURE.md).

**Stack:** Python 3.12, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL, Redis, React, TypeScript, Vite, pytest, Vitest, and Docker Compose. Pandas, NumPy, SciPy, and TradingView Lightweight Charts join in the phases that first use them.

**Current features:** reproducible Phase 1 environment, safe configuration, structured logs, database migration baseline, health API, tested frontend shell, and Linux CI. The Phase 2 feature branch adds typed financial contracts, a deterministic in-process event bus, strict offline CSV ingestion, and a source-independent market-data service. Indicators, strategies, backtesting, analytics, risk, and paper execution are sequenced in the [roadmap](ROADMAP.md).

## Quick start

Prerequisites: Docker Desktop with Compose. On Windows, use Ubuntu in WSL2 with Docker Desktop integration.

```bash
cp .env.example .env
docker compose up --build
```

Open <http://localhost:5173>; API health is at <http://localhost:8000/api/health> and OpenAPI at <http://localhost:8000/docs>. Stop with `docker compose down`.

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
