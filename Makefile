SHELL := /bin/sh
PYTHON ?= python3.12
VENV := .venv
BIN := $(VENV)/bin

.PHONY: help setup dev up down backend frontend test lint format typecheck migrate seed clean

help:
	@echo "setup      Create local environments and install locked dependencies"
	@echo "dev/up     Build and start the complete Docker development stack"
	@echo "down       Stop the Docker development stack"
	@echo "backend    Run the backend locally (infrastructure must be running)"
	@echo "frontend   Run the frontend locally"
	@echo "test       Run backend and frontend tests"
	@echo "lint       Run backend lint/type checks and frontend lint/type checks"
	@echo "format     Format backend and frontend source"
	@echo "migrate    Apply database migrations"
	@echo "seed       Run the idempotent development seed command"
	@echo "clean      Remove local generated build and test output"

setup:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/pip install -r backend/requirements.lock
	$(BIN)/pip install -e backend --no-deps
	npm ci --prefix frontend

dev up:
	docker compose up --build

down:
	docker compose down

backend:
	$(BIN)/uvicorn app.main:app --app-dir backend --reload --host 0.0.0.0 --port 8000

frontend:
	npm run dev --prefix frontend

test:
	$(BIN)/pytest backend/tests
	npm test --prefix frontend -- --run

lint:
	$(BIN)/ruff check backend
	$(BIN)/mypy backend/app
	npm run lint --prefix frontend
	npm run typecheck --prefix frontend

format:
	$(BIN)/ruff format backend
	$(BIN)/ruff check --fix backend
	npm run format --prefix frontend

typecheck:
	$(BIN)/mypy backend/app
	npm run typecheck --prefix frontend

migrate:
	cd backend && ../$(BIN)/alembic upgrade head

seed:
	$(BIN)/python -m app.db.seed

clean:
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache backend/htmlcov frontend/dist frontend/coverage
	find backend frontend -type d -name __pycache__ -prune -exec rm -rf {} +
