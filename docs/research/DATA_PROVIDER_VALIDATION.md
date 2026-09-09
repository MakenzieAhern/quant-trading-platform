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

Round 2 introduces official-file composition: SSE/SZSE reference exports define point-in-time
identity/listing/exit coverage; BaoStock supplies audited daily fields; AKShare remains a non-writing
spot-check adapter. The official importer accepts CSV, JSON and XLSX, pins source-file checksums and
versions, and refuses incomplete or changed inputs. No complete 2010–2025 official exports are staged
yet, so this capability is implemented but not evidenced as complete.

Benchmark selection remains frozen before results: CSI300 is primary, CSI500 is secondary, and
`ELIGIBLE_EQUAL_WEIGHT` is derived only from the audited `eligible_universe(trading_date)`. The
provider interface and BaoStock adapter already support CSI300 and CSI500 bars/membership. Missing
point-in-time membership keeps benchmark readiness PARTIAL; it never triggers post-result
substitution.

Repeat with:

```bash
PYTHONPATH=/path/to/optional/providers python backend/scripts/audit_baostock.py
PYTHONPATH=backend:/path/to/optional/providers python backend/scripts/ingest_research_data.py --pilot --root /outside/git/data/research
make audit-universe
```
