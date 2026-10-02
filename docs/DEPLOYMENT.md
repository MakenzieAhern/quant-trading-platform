# Deployment

## Local release rehearsal

**Do not run this rehearsal on the current v1.2 workbench** until the relevant
data-integrity/cutover gates pass. The command replaces running project
containers, so verify a recoverable, consistent backup before trying it.
Independent physical media are recommended disaster protection, not an extra
mandatory product gate; a same-drive copy must not be called independent backup.

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
a controlled one-off only after a verified recoverable backup. CI separately
smokes the static frontend and the production backend image; the backend check
uses isolated tmpfs PostgreSQL/Redis with no project data mounts. Neither CI
check replaces the live-data backup/rehearsal gate.

## Current-baseline restore — scoped pass, not old-tag rollback

On 2026-10-02, the existing pre0016 PostgreSQL dump and product receipt snapshot
were restored into a separate empty tmpfs database, upgraded to0016 and checked
against all44 original table fingerprints, six receipt bundles and41 GET paths.
Actual packaged Chrome reopened the saved study/comparison and five STOPPED
accounts, including existing cash/fills/event history. Four exact runtime images
are retained in the private local package and were successfully loaded/ID-checked.
The corrected read-only verifier directly compares original newline-delimited
fingerprints, not merely pre/post counts. Original volumes/services were untouched.

[Tested restore commands and prerequisites](../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261002-current-restore/RESTORE.md)
and [actual restored UI scope](../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261002-restored-ui/README.md)
are outside Git. The recorded current post-loss baseline does not contain two
older missing accounts; this rehearsal did not recover them. Historical archive
and fixtures remain external read-only prerequisites. Same-host logical restore
is not independent disaster protection, automatic live cutover, complete product
acceptance or a published v1.2 release.

## Old-tag code and data rollback — not verified for v1.2

At the 2026-09-29 checkpoint, the local database reports Alembic revision
`20260924_0016`. The published `v1.1.0` tag lacks product migrations
`20260922_0012` through `20260924_0016`. Do **not** check out `v1.1.0` and run
`make up` (or start its image) against the current PostgreSQL volume: old code
does not know that schema revision. Do not downgrade the live database, delete
volumes, or call an on-disk copy on the same physical drive an independent
backup.

A rollback can be considered only after a consistent retained pre-upgrade backup
of PostgreSQL **and** product data has been verified. First
restore a copy into a separate checkout pinned to the intended release tag,
with a separate Compose project, private volumes and loopback ports. Never
mount the current live database or writable product directory into that
rehearsal. Confirm the restored database revision is known to that tag, then
smoke its frontend, `/api/health`, saved research and paper-ledger reads. Record
which post-backup records would be absent. Only a successful isolated rehearsal
and a reviewed downtime/data-loss decision can authorize a later cutover;
preserve the original volumes for recovery. Until then, **old-tag rollback is not
verified or available**; the scoped current-baseline restore above does not
authorize it. Keep running schema-compatible code or stop safely.

Docker Compose is the supported development deployment, not a production trading topology.
The following bootstrap commands are for a clean install. On an existing database,
verify a recoverable consistent backup and review the migration before running them; do not
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
