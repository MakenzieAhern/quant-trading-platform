# Data Provider Validation

Assessment date: 2026-09-09. BaoStock remains the primary free ingestion source. AKShare remains an
optional validator and never overwrites or silently fills BaoStock records.

## Observed results

- Earlier 2026-09-07 BaoStock probes returned 2010 raw daily fields, historical status/ST, dividend
  fields and 300 CSI300 constituents for a 2010 date.
- One successful AKShare comparison for SSE 600000 found nine common 2018 sessions with no raw OHLC
  differences. Volume/amount equivalence was not asserted because provider units/methods differ.
- Later AKShare Eastmoney requests intermittently ended in `RemoteDisconnected`. That does not block
  BaoStock ingestion and no records were merged.
- On 2026-09-09 both BaoStock capability-audit and pilot-ingestion attempts timed out connecting to
  `www.baostock.com:10030` and ended with `BAOSTOCK_LOGIN_FAILED`.

## Consequence

BaoStock has demonstrated relevant capabilities, but service availability prevented the complete
historical-universe, delisting, adjustment-factor, dividend and benchmark range audit. Provider
failure is recorded, not converted into synthetic coverage. The real pilot dataset was not created
and the research gate remains blocked.

Repeat with:

```bash
PYTHONPATH=/path/to/optional/providers python backend/scripts/audit_baostock.py
PYTHONPATH=backend:/path/to/optional/providers python backend/scripts/ingest_research_data.py --pilot --root /outside/git/data/research
```
