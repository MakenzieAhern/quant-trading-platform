# README screenshot plan

The repository intentionally ships without fabricated screenshots. Capture these manually from
the Docker-backed v1.0.0 application in Chrome at 1440 × 900 or another consistent desktop size.
Use the deterministic AAPL fixture only. Keep the address bar, browser profile, desktop, terminal,
machine paths and any tokens outside the crop.

| Filename | Route | Required visible content |
| --- | --- | --- |
| `docs/images/backtest-history.png` | `/backtests` | Header, production/paper label, at least two persisted runs and status badges |
| `docs/images/backtest-create.png` | `/backtests/new` | Dataset, strategy parameters, initial capital, quantity and risk controls |
| `docs/images/backtest-result.png` | `/backtests/{id}` | SUCCEEDED, performance summary, UTC labels and full equity curve |
| `docs/images/backtest-audit.png` | `/backtests/{id}` | Approved or rejected risk decision with the Orders and Fills sections |
| `docs/images/paper-realtime.png` | `/paper/{id}` | PAPER safety banner, connected WebSocket, RUNNING status, latest Bar and portfolio |

Before each capture, use `DEMO.md` to create known state. Prefer one successful backtest, one
maximum-notional rejection run, and a Paper session in progress. Check Chrome's console for zero
application errors, confirm no private browser UI is visible, and optimize images before commit.
Add README image links only after the real files exist and have been reviewed.
