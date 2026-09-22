SHELL := /bin/sh
CHECK := docker compose -p quant-mvp-tests -f compose.test.yml

.PHONY: help setup up dev down test lint build format typecheck migrate audit-universe host-setup backend frontend
help:
	@echo "setup      Build locked Python 3.12 / Node 24 environments (Docker + Make only)"
	@echo "up/dev     Start local platform; migrations run automatically"
	@echo "down       Stop platform; preserve database history"
	@echo "test       All tests against isolated disposable PostgreSQL"
	@echo "lint       Ruff, format check, mypy, ESLint and TypeScript"
	@echo "build      Frontend production build"
	@echo "format     Format source in project containers"
	@echo "migrate    Apply application database migrations"
	@echo "audit-universe  Audit staged official SSE/SZSE point-in-time security files"
	@echo "host-setup Optional local install: Python 3.12 and Node 24 required"

setup:
	docker compose build

up dev:
	docker compose up --build -d --wait

down:
	docker compose down

test:
	$(CHECK) build
	@trap '$(CHECK) down --volumes' EXIT INT TERM; \
	$(CHECK) run --rm backend sh -c 'alembic upgrade head && pytest tests' && \
	$(CHECK) run --rm --no-deps frontend npm test -- --run

lint:
	$(CHECK) run --rm --build --no-deps backend sh -c 'ruff check . && ruff format --check . && mypy app'
	$(CHECK) run --rm --build --no-deps frontend sh -c 'npm run lint && npm run typecheck'

build:
	$(CHECK) run --rm --build --no-deps frontend npm run build

format:
	$(CHECK) run --rm --build --no-deps backend sh -c 'ruff check --fix . && ruff format .'
	$(CHECK) run --rm --build --no-deps frontend npm run format

typecheck:
	$(CHECK) run --rm --build --no-deps backend mypy app
	$(CHECK) run --rm --build --no-deps frontend npm run typecheck

migrate:
	docker compose exec backend alembic upgrade head

audit-universe:
	PYTHONPATH=backend .venv/bin/python backend/scripts/audit_a_share_universe.py

host-setup:
	python3.12 -m venv .venv
	.venv/bin/pip install -r backend/requirements.lock
	.venv/bin/pip install -e backend --no-deps
	npm ci --prefix frontend

backend:
	.venv/bin/uvicorn app.main:app --app-dir backend --reload --host 127.0.0.1 --port 8000

frontend:
	npm run dev --prefix frontend
