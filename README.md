# Quant Trading Platform

A local research and demonstration platform for deterministic US-equity backtests and simulated paper replay. It connects typed market data, indicators, strategies, pre-trade risk, OMS, execution, accounting and analytics to durable PostgreSQL history and a React dashboard.

**NO LIVE TRADING. NO REAL BROKER CONNECTIVITY. NO REAL-MONEY ORDER EXECUTION.**
This project currently supports simulated paper trading only.

## Supported MVP

- Registered daily historical CSV fixtures; SMA, EMA, RSI, MACD and Bollinger Bands.
- Moving-average crossover and RSI mean-reversion strategies.
- Deterministic next-Bar OPEN execution, transaction-cost models, portfolio accounting and analytics.
- Pre-trade limits, buying-power reservations, explicit OMS states and auditable rejections.
- PostgreSQL backtest results, paginated REST APIs and an equity/audit dashboard.
- Paper replay lifecycle, durable events, bounded WebSocket updates and REST recovery.

The Python engine supports cost-model and multi-strategy composition. The public demo API uses the registered fixture and fixed default zero-cost execution; it does not expose every engine configuration. LIMIT execution, live feeds, broker margin/borrow rules, options, futures, HFT, distributed workers, ML and GPU are outside this MVP.

## Quick start: Windows / WSL2, Linux or macOS

Requires Git, GNU Make and Docker with Compose v2. On Windows enable Ubuntu integration in Docker Desktop and work inside WSL.

```bash
git clone https://github.com/MakenzieAhern/quant-trading-platform.git
cd quant-trading-platform
cp .env.example .env
make setup
make up
```

Open [dashboard](http://localhost:5173/backtests), [API health](http://localhost:8000/api/health) or [OpenAPI](http://localhost:8000/docs). Migrations run before the backend starts.

```bash
make test       # complete suites; disposable, isolated PostgreSQL
make lint       # Ruff + format, mypy, ESLint, TypeScript
make build      # frontend production bundle
make down       # preserves application database history
```

No host Python or Node install is required for these commands. Test containers use a separate Compose project and temporary database; tests never use the application's database URL. Do not run two `make test` commands simultaneously because they share that disposable project name. Optional host development: [development guide](docs/DEVELOPMENT.md).

## Architecture

```text
Historical Bars → Strategy → Signal → Risk → OMS → simulated Broker
                                                         ↓ Fill
                                              Portfolio → Analytics
                                                         ↓
                                                   PostgreSQL
                                                         ↓
                                             REST / WebSocket → React
```

Python 3.12 / FastAPI / Pydantic / SQLAlchemy / Alembic; PostgreSQL 16; React / TypeScript / Vite / Node 24; pytest / Vitest / Docker Compose. Redis is provisioned for future cache use; current trading and WebSocket delivery use the in-process event bus, not Redis.

Domain engines do not import FastAPI or SQLAlchemy. Financial values remain Decimal in Python and exact strings in JSON and UI state; chart coordinates are approximate presentation only. Authoritative timestamps are aware UTC. See [architecture](ARCHITECTURE.md).

## API and dashboard

- `/backtests`, `/backtests/new`, `/backtests/:runId`: history, creation, metrics, equity, signals, risk decisions, orders and fills.
- `/paper`, `/paper/new`, `/paper/:sessionId`: simulated session creation, start/stop and live updates.
- `POST /api/backtests`: synchronous execution; optional `Idempotency-Key`.
- `GET /api/backtests/{id}` and `/result`, `/signals`, `/risk-decisions`, `/orders`, `/fills`, `/equity`.
- `POST /api/paper-trading/sessions` and `/{id}/start`, `/{id}/stop`.
- `GET /api/paper-trading/sessions/{id}/snapshot` and `/events`.
- `/api/paper-trading/sessions/ws/{id}`: incremental delivery; REST is authoritative.

Collection pages accept limits 1–200. Inputs use registered identifiers, never user-supplied paths or imports. Financial JSON inputs are strings with at most 40 integral and 38 fractional digits.

## Paper semantics and recovery

A signal from completed Bar T may fill only at the next later same-symbol Bar OPEN. Replay never contacts a market-data vendor or broker. Each session owns isolated strategies, risk reservations, broker and portfolio. Stopping cancels pending orders. Shutdown/restart marks active sessions INTERRUPTED and never resumes execution automatically. Financial event batches commit before publication; each browser queue is bounded to 64 events and saturation requests REST resynchronization.

Backtests execute synchronously. A process crash may leave a stale RUNNING backtest; its missing result is never fabricated. Automatic backtest job recovery is unsupported. Paper restart interruption is supported. Finite registered replay data bounds runtime history; endless feeds require a future retention design.

## Security and configuration

This is a single-user local MVP without authentication. Compose binds every published port to loopback; do not expose it to a shared network. CORS/WebSocket origins are restricted, HTTP bodies are limited to 64 KiB, validation does not reflect original inputs, and unexpected failures return sanitized JSON. There are no broker credentials or live adapters.

`.env` is ignored. Compose defines safe local container URLs and intentionally local-only development credentials; `.env.example` documents optional host settings. `VITE_API_BASE_URL` is public browser configuration and must contain no secrets. [Configuration and operations](docs/DEVELOPMENT.md), [deployment limits](docs/DEPLOYMENT.md).

## Demo, validation and status

Follow [DEMO.md](DEMO.md) for a 5–10 minute walkthrough and exact expected results. The small registered fixture is for regression/demo use, not a licensed market feed or investment recommendation. No external dataset is downloaded.

[Performance baseline](docs/PERFORMANCE.md) records synthetic measurements for regression comparison. CI runs backend, frontend and Compose checks. [ROADMAP.md](ROADMAP.md) distinguishes implemented MVP work from future capabilities.

Screenshots can be added from the local deterministic demo; no live account imagery is required.
