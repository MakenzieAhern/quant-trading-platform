# Five-to-ten-minute simulated trading demo

Run `make setup && make up`, then open http://localhost:5173/backtests.
The demo is local simulation: no account, broker key, live data, or money is involved.

1. Open **New backtest**. Select AAPL fixture and moving-average crossover.
   Use short period 2, long period 3, initial cash 100000, quantity 10.
   Enable buying-power enforcement. Submit once.
2. Inspect SUCCEEDED, the equity curve and its accessible data table. There are six
   completed Bars, one BUY signal on 2024-01-08, one approved risk decision and one Fill
   on 2024-01-09 at 183.92. Commission is 0. Cash is 98160.8 and final equity 100012.2.
   This default API demo uses zero transaction costs; configurable costs are engine capabilities.
3. Inspect the separate signal, risk, order and fill tables. Refresh the URL: the
   same records load from PostgreSQL. Navigate to history and back.
4. Create another backtest with a maximum order notional of 1. Its risk rejection
   creates no order or fill; this is a valid completed run, not a broker rejection.
5. Open **Paper trading**, create a session using the same fixture, strategy and
   quantities. Creation leaves it CREATED. Click Start replay and watch market,
   signal, risk, order, fill and portfolio events arrive over WebSocket.
6. Open the same URL in another tab. Both tabs observe the same durable session.
   Navigate one away and return. REST restores state before more increments apply.
7. Click Stop replay during replay to demonstrate STOPPING/STOPPED; the exact partial
   portfolio depends on when you stop. For the deterministic final reference, let all
   six Bars complete: equity 100012.2, cash 98160.8, one Fill. Stop again is safe.
8. Refresh after stopping. The socket stays closed, history stays intact. Restarting
   the backend during another active session produces INTERRUPTED, never automatic resume.

All dates are UTC. Financial labels preserve Decimal strings; chart geometry is only
presentation. Backtest and paper order UUID namespaces differ deliberately, while the
reference financial outcome agrees. The fixture is a tiny regression example, not a
market-data service. Use `make down` to stop without deleting history.

For automated verification run `make test`. The golden-path test compares both APIs,
persisted snapshots and financial results. Failure, duplicate, concurrency and slow-client
scenarios are covered by focused regression tests rather than contrived demo trading.
