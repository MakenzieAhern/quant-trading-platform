# Local data directories

`raw/`, `processed/`, and `cache/` hold local datasets and are ignored by Git.
`fixtures/` contains the existing small, fixed AAPL demonstration input used by the
registered API replay; test-specific inputs live under `backend/tests/fixtures/`.
Phase 10 adds no downloaded, private, or vendor dataset. See `DEMO.md` for expected
results. These fixtures are regression/demo inputs, not a market-data service.
Future download scripts must record source, license, symbol, interval, timezone,
and adjustment policy before any redistribution is considered.
