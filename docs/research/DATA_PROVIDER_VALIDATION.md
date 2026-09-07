# Data Provider Validation

Assessment date: 2026-09-07. BaoStock is the primary free ingestion provider; AKShare is an
optional independent validator and never overwrites primary data.

## Probe results

- BaoStock package 0.9.3 / reported SDK `00.9.30` authenticated anonymously and returned raw
  daily bars, stock basics, trading calendars, historical CSI300 membership and dividend rows.
- For a deterministic 2018 sample of SSE 600000, one successful AKShare comparison found nine
  common sessions and no raw OHLC differences.
- Volume and amount values were not declared equal because unit/methodology reconciliation is not
  frozen. This is a recorded discrepancy, not silently coerced data.
- Subsequent AKShare/Eastmoney requests intermittently ended with `RemoteDisconnected`; the
  validation tool converts provider failures to stable diagnostics.
- Adjustment and corporate-action equivalence remain unverified. No provider data is silently
  substituted or merged.

## Known limitations

Provider availability is network-dependent. BaoStock corporate actions require a separate schema
normalizer. Delisted-security completeness has not been measured. AKShare is unsuitable as an
automatic fallback until its field units, adjustment semantics and revision policy are frozen.

Run `PYTHONPATH=backend python backend/scripts/validate_providers.py` for a fresh, non-mutating
probe. Probe results are evidence only and are not a frozen research dataset.
