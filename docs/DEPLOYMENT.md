# Deployment

Docker Compose is the supported development deployment, not a production trading topology.

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose ps
curl --fail http://localhost:8000/api/health
```

`docker compose down` preserves named database/cache volumes. `docker compose down --volumes` irreversibly discards local service data and should be used only for an intentional reset.

Before any production-like deployment, build immutable tagged images in CI, remove source bind mounts and dev servers, serve the frontend as static assets, run Uvicorn behind a TLS reverse proxy, use non-default credentials from a secret manager, restrict network exposure, configure backups/observability, and run migrations as a controlled one-off job. PostgreSQL and Redis require durability, authentication, resource limits, and health monitoring.

Production and paper environments must have separate credentials and databases. `BROKER_MODE=live` currently fails startup by design. CUDA/GPU workloads, model artifacts, broker connectivity, and horizontally distributed execution are not part of Phase 1.
