# Deployment

## Local release rehearsal

With Docker Compose 2.24.4 or newer:

```bash
docker compose -f docker-compose.yml -f compose.release.yml up --build -d --wait
```

This uses the installed backend image without a source-code mount and an nginx-served
frontend production bundle (no Vite server). The registered fixture directory is read-only.
It retains the same loopback ports and local PostgreSQL history. This is a local release
rehearsal, not an authenticated public deployment. Return to development with `make up`.

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

Any future public deployment needs separate protected credentials/databases and authentication.
`BROKER_MODE=live` fails startup by design. CUDA/GPU, model artifacts, broker connectivity,
and distributed execution are outside the completed MVP scope.
