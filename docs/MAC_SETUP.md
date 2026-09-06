# macOS setup (Apple Silicon)

Install Git, Python 3.12, Node 24 LTS, Docker Desktop, and GNU Make. Homebrew is convenient for Git/Python/Node but is not required; PostgreSQL and Redis run in Docker and should not be installed separately.

```bash
git --version
python3.12 --version
node --version
docker compose version
```

Clone the GitHub repository, then run:

```bash
cp .env.example .env
make host-setup
docker compose up -d postgres redis
cd backend && ../.venv/bin/alembic upgrade head && cd ..
make backend
```

In another terminal run `make frontend`. Alternatively, `make setup && make up` runs everything with only Git, Make and Docker installed. Open <http://localhost:5173> and verify <http://localhost:8000/api/health>.

Run `make test` and `make lint` before pushing. Docker Desktop must be running. Apple Silicon uses ARM64 image variants automatically; do not add `platform: linux/amd64` or copy `.venv`/`node_modules` from another machine. Native Python packages and future numerical libraries must be rebuilt locally from the committed locks.
