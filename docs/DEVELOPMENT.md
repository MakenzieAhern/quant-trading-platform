# Development and configuration

## Canonical Docker workflow

Requires Git, GNU Make and Docker Compose v2, with Docker Desktop WSL integration on Windows. No host Python/Node is required.

```bash
cp .env.example .env
make setup
make up
make test
make lint
make build
make down
```

`make up` waits for database/backend health and applies migrations. `make down` preserves named application volumes. `make test` builds locked images and runs all suites using `compose.test.yml`: a different project, no published database port, and temporary PostgreSQL storage. Its exit trap removes only this disposable test project. Run one test invocation at a time. Lint/build use the same pinned images without starting the application database.

The integration suites truncate tables; direct pytest execution must target a disposable database. Prefer `make test`. The backend suite now exits before collection unless `APP_ENV=test` and `DATABASE_URL` names `quant_test` or `quant_test_*`. Never point direct tests at a database containing demonstration or personal history; the name guard is a last line of defense, not a replacement for checking the actual target.

## Optional host development

Install Python 3.12 and Node 24/npm 11, then `make host-setup`. Start infrastructure with `docker compose up -d postgres redis`. Apply migrations using `cd backend && ../.venv/bin/alembic upgrade head`. Use `make backend` and `make frontend` in separate terminals. Host environments are optional and must be recreated after architecture changes.

## Configuration reference

Compose explicitly supplies container settings; the root `.env` configures host Python execution. No broker keys are needed or supported.

| Variable | Default / purpose |
| --- | --- |
| APP_NAME / APP_VERSION | Quant Trading Platform / 1.0.0, public health metadata |
| APP_ENV | development; also test or production, metadata only, not authentication |
| LOG_LEVEL | INFO; lifecycle logging without sensitive exception text |
| API_HOST / API_PORT | 0.0.0.0 / 8000; metadata settings, use CLI bind flags to change server binding |
| DATABASE_URL | Local PostgreSQL asyncpg URL; backend only |
| REDIS_URL | Local Redis URL; provisioned infrastructure, not trading authority |
| BROKER_MODE | paper or backtest; live is rejected at startup |
| MARKET_DATA_PROVIDER | csv; no vendor adapters |
| MARKET_DATA_PATH | data/raw; administrator-selected local source directory |
| BACKTEST_FIXTURE_PATH | data/fixtures; directory for registered AAPL_fixture |
| FRONTEND_ORIGIN | http://localhost:5173; exact CORS/WebSocket origin |
| VITE_API_BASE_URL | http://localhost:8000; public build-time browser URL |

HTTP request bodies are capped at 65,536 bytes, Decimal input strings at 128 characters, strategy periods at 10,000, and pagination offset at 2,147,483,647. Pagination limit is 1–200. Oversized bodies return 413; validation failures return 422. Configuration paths are trusted operator input, never REST parameters.

State-changing browser requests with an Origin other than FRONTEND_ORIGIN return 403,
including bodyless start/stop requests. CLI clients without Origin remain supported.
This origin check is not authentication; keep the application on loopback.

## Dependency updates

Python 3.12 and Node 24 remain pinned. Update Python ranges in `backend/pyproject.toml` and regenerate `requirements.lock` with pip-compile; npm and `package-lock.json` are the frontend authority. Re-run all checks after changes. Use `make help` for commands.

The local Compose topology has source mounts and Vite for iteration. It is not a public production deployment; see [DEPLOYMENT.md](DEPLOYMENT.md).
