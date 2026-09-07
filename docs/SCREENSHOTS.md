# README screenshot capture record

These real screenshots were captured from the Docker-backed v1.0.0 application at a consistent
wide desktop viewport. They use only the registered deterministic AAPL fixture. Browser chrome,
profile, desktop, terminal, machine paths, tokens, and unrelated windows are outside the captures.

| Filename | Route | Visible evidence |
| --- | --- | --- |
| `docs/screenshots/dashboard.jpg` | `/backtests` | Production/paper label plus successful persisted Moving Average and RSI runs |
| `docs/screenshots/create-backtest.jpg` | `/backtests/new` | Registered dataset, capital, sizing and Moving Average strategy inputs |
| `docs/screenshots/backtest-result.jpg` | `/backtests/{id}` | SUCCEEDED, UTC lifecycle labels, final equity `100012.2`, and performance summary |
| `docs/screenshots/equity-curve.jpg` | `/backtests/{id}` | Six-point equity curve and the deterministic BUY signal |
| `docs/screenshots/execution-details.jpg` | `/backtests/{id}` | APPROVED risk decision, FILLED Order, and Fill at next-Bar OPEN `183.92` |
| `docs/screenshots/paper-trading.jpg` | `/paper/{id}` | PAPER safety banner, connected WebSocket, RUNNING status, latest Bar, and portfolio |

The reference backtest uses Moving Average periods `2`/`3`, initial cash `100000`, quantity `10`,
and buying-power enforcement. A second successful run uses RSI period `2` with `30`/`70`
thresholds. The paper image was captured during the same finite replay while the WebSocket was
connected. Browser error logs were checked after capture and contained zero application errors.
