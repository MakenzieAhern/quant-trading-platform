# Windows 11 + WSL2 setup

Use Ubuntu under WSL2 as the development environment; Windows remains the host for Docker Desktop, browsers, and optional editors.

1. Enable WSL2 and install Ubuntu (`wsl --install -d Ubuntu` from an elevated PowerShell, then restart if requested).
2. Install Docker Desktop for Windows, enable the WSL2 engine, and enable integration for the Ubuntu distribution.
3. Install Git and GNU Make **inside Ubuntu**. Docker provides Python 3.12 and Node 24 for all canonical checks. Host Python/Node are optional. Use VS Code with Remote - WSL if desired.
4. Configure Git name/email and clone within the Linux filesystem:

```bash
mkdir -p ~/projects
cd ~/projects
git clone <your-github-repository-url> quant-trading-platform
cd quant-trading-platform
cp .env.example .env
make setup
```

Keep the repository under `~/projects/quant-trading-platform`, not `/mnt/c/`. Linux-filesystem storage avoids slower cross-filesystem metadata operations, watcher problems, permission differences, and line-ending surprises. Windows applications can access it through `\\wsl$\Ubuntu\home\<linux-user>\projects`, but code/tooling should run inside WSL.

Docker commands issued in Ubuntu talk to Docker Desktop's Linux VM through WSL integration. Published ports such as 5173 and 8000 are reachable from the Windows browser at `localhost`; named volumes live in Docker's managed storage.

Start everything with:

```bash
docker compose up --build
```

Or start only infrastructure and run application processes in WSL:

```bash
docker compose up -d postgres redis
make host-setup
cd backend && ../.venv/bin/alembic upgrade head && cd ..
make backend
# second Ubuntu terminal
make frontend
```

Validate with `make test`, `make lint` and `make build`. These commands use pinned Docker environments; tests use a separate disposable PostgreSQL service. Never share another machine's `.venv` or `node_modules`. See DEVELOPMENT.md for configuration and test isolation.
