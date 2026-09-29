# Deployment

## Local release rehearsal

**Do not run this rehearsal on the current v1.2 workbench** until the
data-integrity and independent-backup gates pass. The command replaces running
project containers, so verify a recoverable independent backup before trying it.

With Docker Compose 2.24.4 or newer:

```bash
docker compose -f docker-compose.yml -f compose.release.yml up --build -d --wait
```

This uses the installed backend image without a source-code mount and an nginx-served
frontend production bundle (no Vite server). The registered fixture directory is read-only.
It retains the same loopback ports and local PostgreSQL history. This is a local release
rehearsal, not an authenticated public deployment. `make up` switches back to
development containers only for the **same schema-compatible checkout**; it is
not a rollback to an older tag and does not undo a database migration.
It replaces the running project containers, but the release backend uses its image command
and does not run Alembic automatically. Check the schema and run any required migration as
a controlled one-off only after a verified independent backup. CI separately
smokes the static frontend and the production backend image; the backend check
uses isolated tmpfs PostgreSQL/Redis with no project data mounts. Neither CI
check replaces the live-data backup/rehearsal gate.

## Code and data rollback gate — not yet passed for v1.2

At the 2026-09-29 checkpoint, the local database reports Alembic revision
`20260924_0016`. The published `v1.1.0` tag lacks product migrations
`20260922_0012` through `20260924_0016`. Do **not** check out `v1.1.0` and run
`make up` (or start its image) against the current PostgreSQL volume: old code
does not know that schema revision. Do not downgrade the live database, delete
volumes, or call an on-disk copy on the same physical drive an independent
backup.

A rollback can be considered only after a consistent, independently stored
pre-upgrade backup of PostgreSQL **and** product data has been verified. First
restore a copy into a separate checkout pinned to the intended release tag,
with a separate Compose project, private volumes and loopback ports. Never
mount the current live database or writable product directory into that
rehearsal. Confirm the restored database revision is known to that tag, then
smoke its frontend, `/api/health`, saved research and paper-ledger reads. Record
which post-backup records would be absent. Only a successful isolated rehearsal
and a reviewed downtime/data-loss decision can authorize a later cutover;
preserve the original volumes for recovery. Until then, **rollback is not
verified or available**. Keep running schema-compatible code or stop safely.

Docker Compose is the supported development deployment, not a production trading topology.
The following bootstrap commands are for a clean install. On an existing database,
verify an independent backup and review the migration before running them; do not
rerun this block on the current v1.2 workbench.

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
