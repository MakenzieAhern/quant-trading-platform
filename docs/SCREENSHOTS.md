# README screenshot capture record

## v1.2 development UI used in the current README

These are retained, unmodified captures of the actual application, not generated mockups.
They were reviewed before inclusion for credentials, local paths, personal identities,
account/task identifiers and private market-data rows. They demonstrate interface design,
not current-head runtime health, source admission, financial performance or a v1.2 release.

| Repository asset | Provenance | What it demonstrates / does not demonstrate |
|---|---|---|
| `docs/screenshots/v1.2-guided-research.png` | Original evidence filename `guided-start-zh-1280.png`, already referenced in `docs/product/DEMO.md`; retained file timestamp 2026-09-24. The timestamp is file metadata, not an independently recorded capture receipt. | Chinese light-theme, 1280×800 four-step research wizard. Historical exploration is visibly selected; this is not the synthetic demo and does not authorize new historical execution. |
| `docs/screenshots/v1.2-strategy-detail.jpg` | Original `08-v12-strategy-loaded.jpg`; captured 2026-10-02T16:00:14Z (2026-10-03 Australia/Sydney), from the retained Oct3 comparison evidence. Frontend source `bc7390cd`, backend source `3184281e`. | Chinese dark-theme strategy description; recorded browser viewport 1280×800, retained JPEG 1265×791. This is the v1.2 frontend view, not the reconstructed v1.1 view from the same evidence set. Small browser-extension overlays remain visible; pixels were not altered. |

SHA-256 of the exact files committed here:

```text
67ed0f6723645dcdbf31665394e6410cef5278e47f36c881c344fa8dfa680571  v1.2-guided-research.png
097aaa03cfd1eebfb07f3d483c2cd03d141b1e2efcacb6fcff497a148176b3c7  v1.2-strategy-detail.jpg
```

The original evidence set remains outside Git. Only these two reviewed UI images are
included; no raw market dataset or private research/account ledger was copied.

## Legacy v1.0.0 captures

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
