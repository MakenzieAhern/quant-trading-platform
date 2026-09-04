# Git and cross-machine workflow

GitHub is the single source of truth. `main` should remain stable; significant changes use pull requests. Before switching computers, commit and push meaningful work. Before starting on another computer, fetch or pull. Never develop the same uncommitted change independently on both machines.

## Start a feature on machine A

```bash
git switch main
git pull --ff-only
git switch -c feature/example
# develop, then make test && make lint
git status
git add .
git commit -m "feat: example"
git push -u origin feature/example
```

Open a GitHub pull request for significant work. Prefer branches such as `feature/backtest-engine`, `feature/risk-engine`, `feature/paper-trading`, `feature/dashboard`, `fix/portfolio-accounting`, and `docs/wsl-setup`.

## Continue on machine B

For merged work: `git switch main && git pull --ff-only`. To continue an open branch:

```bash
git fetch origin
git switch feature/example
git pull --ff-only
```

Check `git status` before switching or pulling. Commit and push, or intentionally stash short-lived work, rather than copying working directories between machines. Resolve dependency changes through the committed lock files, not by committing `.venv` or `node_modules`.

Use concise Conventional Commit-style subjects: `feat: implement backtest engine`, `fix: prevent same-bar execution`, `test: add order state machine tests`, `docs: add WSL2 development guide`, `refactor: simplify event bus`, or `chore: update dependencies`.
