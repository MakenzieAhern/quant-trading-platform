# Contributing

This is currently a solo-developer project, so the workflow is intentionally light. Start from an updated `main`, work on a descriptive branch, keep commits focused, and open a pull request for significant features or architecture changes. Follow [docs/GIT_WORKFLOW.md](docs/GIT_WORKFLOW.md).

Before requesting review:

```bash
make test
make lint
docker compose config --quiet
```

Use type hints and tests for backend behavior, strict TypeScript for frontend behavior, Alembic for schema changes, and documentation for user-visible commands or architectural assumptions. Conventional Commit-style subjects are preferred: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`, or `chore:`.

Never include credentials, personal paths, generated dependencies, large data, or trained-model artifacts. Real-money trading changes are outside the current project boundary.
