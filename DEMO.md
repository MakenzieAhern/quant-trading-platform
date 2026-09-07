# Five-to-ten-minute v1.0.0 demo

This walkthrough uses local deterministic simulation only. No account, broker key, live data, or
real money is involved.

## Start

1. In WSL2/Linux/macOS, run `make setup && make up`.
2. Open <http://localhost:5173/backtests>. Confirm the header reads `production · paper` when
   using the release Compose override, or `development · paper` with `make up`.

## Deterministic backtest

3. Select **New backtest**.
4. Keep `AAPL_fixture` and **Moving average crossover**. Enter short period `2`, long period `3`,
   initial cash `100000`, and quantity `10`. Enable buying-power enforcement and submit once.
5. Confirm the direct result page shows `SUCCEEDED` and explicitly UTC lifecycle timestamps.
6. Inspect the six-point equity curve and accessible data. Expected final equity: `100012.2`.
7. Inspect **Signals**: one `BUY` on `2024-01-08 00:00:00Z`.
8. Inspect **Risk decisions**: one `APPROVED`; it is visibly distinct from broker rejection.
9. Inspect **Orders** and **Fills**: one `FILLED` BUY for quantity `10`, filled on
   `2024-01-09 00:00:00Z` at next-Bar OPEN `183.92`, commission `0`.
10. Inspect portfolio/performance metrics: final cash `98160.8`, market value `1851.4`,
    unrealized PnL `12.2`, one Fill. The public demo's default execution costs are zero.
11. Return to **Backtests**, locate the persisted run, reopen it, and refresh. The identical result
    reloads from PostgreSQL rather than browser memory.

Optional risk demonstration: create another run with maximum Order notional `1`. It succeeds with
one risk rejection and no Order or Fill; this is a valid risk-controlled result, not a broker
rejection or failed run.

## Paper trading and realtime delivery

12. Open **Paper trading** and select **Create paper session** using the same fixture, strategy,
    capital, and quantity. Confirm creation leaves the session `CREATED`.
13. Click **Start replay**. Confirm `STARTING`/`RUNNING` and `WebSocket: connected` are visible.
14. Observe completed Bars, portfolio snapshots, then Signal → Risk → Order → Fill increments.
    Open the same URL in another tab if desired; both subscribers view one durable session.
15. Click **Stop replay** while it is running and confirm `STOPPING` then `STOPPED`, an exact UTC
    stopped time, and a closed socket. The partial portfolio depends on the stop point.

For the fully completed Paper reference, let all six Bars replay: one Fill at `183.92`, cash
`98160.8`, market value `1851.4`, and equity `100012.2`. Refresh the stopped URL; REST restores the
same durable state and the terminal socket stays closed. Restarting the backend during a different
active session produces `INTERRUPTED`, never automatic continuation.

## Close and verify

All financial labels preserve exact Decimal strings; only SVG coordinates are approximate.
Backtest and Paper Order UUID namespaces intentionally differ while financial outcomes agree. The
fixture is a small regression/demo input, not a market-data service or investment recommendation.

Check Chrome DevTools Console for zero application errors. Stop with `make down`, which preserves
history. Automated verification is `make test`; failure, idempotency, concurrency, duplicate,
restart, slow-client and resource-cleanup cases are covered by regression tests.
