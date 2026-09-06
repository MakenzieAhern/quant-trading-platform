# Development guide

The same command surface is used on macOS and Ubuntu/WSL2. Platform installation details are in [MAC_SETUP.md](MAC_SETUP.md) and [WINDOWS_WSL_SETUP.md](WINDOWS_WSL_SETUP.md).

## Fresh clone

```bash
git clone <your-github-repository-url> quant-trading-platform
cd quant-trading-platform
cp .env.example .env
```

Choose one workflow:

### Complete Docker workflow

```bash
docker compose up --build
```

This starts PostgreSQL, Redis, FastAPI, and Vite. The backend applies migrations before serving requests. Stop with `make down`; use `docker compose down --volumes` only when intentionally discarding local database/cache state.

### Host application workflow

Install Python 3.12 and Node 24, then:

```bash
make setup
docker compose up -d postgres redis
make migrate
make backend
```

Run `make frontend` in a second terminal. The Python environment lives in `.venv`; Node packages live in `frontend/node_modules`. Both are machine-local and must be recreated after switching CPU architecture.

The Phase 7+ backend integration tests use real PostgreSQL. Start `postgres`, apply migrations, and then run `make test`; SQLite is intentionally not used as a substitute. If npm is not installed in WSL, `make test`, `make lint`, `make format`, and `make typecheck` automatically use the project's `node:24-alpine` frontend image. This Docker fallback uses an isolated `/app/node_modules` volume and does not install or downgrade Node on the host.

## Commands

| Command | Purpose |
| --- | --- |
| `make setup` | Create `.venv` from the Python lock and restore npm packages |
| `make dev` / `make up` | Build and run all Compose services |
| `make down` | Stop services without deleting named volumes |
| `make backend` | Run FastAPI with reload on the host |
| `make frontend` | Run Vite on the host |
| `make test` | Run pytest and Vitest |
| `make lint` | Run Ruff, mypy, ESLint, and TypeScript checks |
| `make format` | Format/fix supported source files |
| `make migrate` | Apply Alembic migrations from the host environment |
| `make seed` | Run the idempotent development seed entry point |
| `make clean` | Remove generated test/build caches, never datasets or databases |

When dependencies change, update `backend/pyproject.toml`, regenerate `backend/requirements.lock` with `pip-compile --extra dev --output-file backend/requirements.lock backend/pyproject.toml`, and validate a clean install. For Node, use npm only: update `frontend/package.json` and run `npm install --prefix frontend` to update the lock.

Tests must be deterministic and offline. Store only small source-controlled fixtures in `backend/tests/fixtures`; use scripts (added with their provider module) to reproduce larger local data under `data/`.
