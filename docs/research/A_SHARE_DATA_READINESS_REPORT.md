# A-Share Data Readiness Report

Decision: **A_SHARE_DATA_READINESS = BLOCKED**
Assessment date: 2026-09-09 (Round 2)

| Field | Status | Research consequence |
|---|---|---|
| Historical OHLCV | PASS | Raw and adjusted daily fields were empirically returned in earlier 2010/2018 probes and remain strictly separated. |
| Trading calendar | PARTIAL | Contract and normalization exist, but the complete 2010–2025 range could not be refreshed during the provider outage. |
| Historical universe | FAIL | A deterministic official-file master and audit now exist, but complete SSE/SZSE source files are not staged; using today's active list remains prohibited. |
| Listing history | PARTIAL | Effective-date import and leakage checks pass on fixtures, but actual 2010–2025 official coverage is not yet evidenced. |
| Delisting handling | FAIL | Exited securities are retained correctly in tested master logic, but complete official exit records are not yet supplied. |
| Historical ST state | PASS | Daily `isST` is normalized point in time; earlier historical rows were returned. |
| Suspension status | PASS | Daily `tradeStatus` is normalized; missing sessions remain distinct from an explicit suspension. |
| Adjustment data | PASS | Factor-only adjusted close is stored separately from raw execution prices; direct factor rows are normalized with provenance hashes. |
| Corporate actions | PARTIAL | Cash/stock/bonus accounting is implemented; queried-security, source-row, actionable, unsupported and reconciled-ex-date counts remain unavailable for 2010–2025. |
| Liquidity proxy | PASS | Volume, amount and turnover are normalized without forcing cross-provider unit equivalence. |
| CSI300 benchmark | PARTIAL | Endpoint and ingestion exist; pilot bars could not be frozen during the outage. |
| Historical benchmark membership | PARTIAL | A 2010 CSI300 query returned 300 members; comprehensive date coverage remains unaudited. |
| Historical market rules | PARTIAL | Core SSE/SZSE Main, STAR and pre/post-2020 ChiNext timelines are versioned; unknown security-specific exceptions remain conservative exclusions. |
| Deterministic dataset checksums | PASS | Canonical Parquet, byte hashes, metadata-independent logical partition hashes and aggregate logical hashes are tested. |

## Blocking capability

The smallest concrete blocker is a reproducible historical-security snapshot/exit audit. BaoStock's
TCP service timed out before login twice on 2026-09-09, so the required 2010–2025 snapshots and
delisted-security retention tests could not be completed. Without them, Development and Validation
would have a material known survivorship-bias risk.

The safest free path is to rerun the committed BaoStock audit when reachable and reconcile exited
codes against official SSE/SZSE termination-of-listing notices and historical listed-company
directories. AKShare may spot-check discrepancies but cannot silently replace the primary universe.

Round 2 narrows the next action further: stage complete official SSE/SZSE listing and termination
exports under the documented security-master contract, then run `make audit-universe`. The official
files, not BaoStock availability alone, are now the blocking input.

Development: **NOT RUN**

Validation: **NOT RUN**

Official OOS: **NOT RUN**
