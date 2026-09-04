# Local data directories

`raw/`, `processed/`, and `cache/` hold reproducible local datasets and are ignored by Git. Keep only small deterministic test inputs under `backend/tests/fixtures/`. Future download scripts must record source, symbol, interval, timezone, and adjustment policy.
