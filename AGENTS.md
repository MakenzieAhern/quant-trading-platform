# Coding agent instructions

These instructions apply throughout the repository.

1. Read `ARCHITECTURE.md` before architectural changes and `ROADMAP.md` before major features. Inspect existing code and tests before editing; preserve working implementations and public behavior unless the task explicitly changes them.
2. Maintain the modular-monolith boundaries. Keep transport logic out of domain code and API routes, strategy code independent of brokers/data vendors, and portfolio accounting centralized. Avoid microservices and unnecessary dependencies.
3. Maintain Python 3.12 and Node 24 compatibility on macOS ARM64 and Linux/WSL2 x86_64. Use `pathlib` and repository-relative paths. Do not hardcode home paths or introduce macOS-only, Windows-only, architecture-specific, shell-specific, CUDA, or GPU assumptions.
4. Preserve determinism. Use timezone-aware UTC timestamps and `Decimal` for important monetary values. Backtests may not use future data or impossible same-bar fills. Automated tests may not depend on live market data.
5. Keep real-money trading disabled by default. Strategy signals must pass through risk and order management before broker adapters. Any future live mode requires explicit configuration and a dedicated safety review.
6. Never commit `.env`, secrets, logs, `.venv`, `node_modules`, generated market datasets, model weights, checkpoints, or experiment artifacts. Do not log credentials. Use small fixtures under `backend/tests/fixtures`.
7. Add or update focused tests with behavior changes. Run relevant tests and lint/type checks before completion; run `docker compose config` for orchestration changes. Update documentation whenever commands, architecture, configuration, or assumptions change.
8. Use Alembic for database schema changes and keep migrations reversible when practical. Do not edit an already-shared migration to change deployed schema.
9. Prefer small typed modules, explicit interfaces, dependency injection at boundaries, and clear names. Avoid global mutable state, circular imports, giant classes, duplicated business rules, and premature optimization.
