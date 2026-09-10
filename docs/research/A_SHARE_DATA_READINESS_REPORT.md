# A-Share Data Readiness Report

Decision: **PILOT_A_SHARE_DATA_READINESS = BLOCKED**

Decision: **FULL_2010_2025_DATA_READINESS = PARTIAL**

Assessment date: 2026-09-10 (Round 3)

| Field | Status | Research consequence |
|---|---|---|
| Historical OHLCV | PASS | Raw and adjusted daily fields were empirically returned in earlier 2010/2018 probes and remain strictly separated. |
| Trading calendar | PARTIAL | Contract and normalization exist, but the complete 2010–2025 range could not be refreshed during the provider outage. |
| Historical universe | PASS_FOR_PILOT | Official SSE/SZSE reconstruction represents 5,178 pilot-eligible securities and reconciles exactly to the 2,736-code SZSE 2022 year-end A-share baseline. Full 2010–2025 remains PARTIAL. |
| Listing history | PASS_FOR_PILOT | 276/276 pilot IPO boundary checks exclude securities before listing. |
| Delisting handling | PASS_FOR_PILOT | 142 relevant exits are retained, including 70 post-pilot exits; all 72 in-pilot before/after boundary checks pass. |
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

The security-master blocker is resolved for the frozen pilot interval. The single remaining pilot
blocker is BaoStock connectivity: login to port 10030 timed out on 2026-09-10, so the required real
OHLCV/calendar/status/corporate-action/benchmark dataset cannot yet be frozen. No manual exchange
download is required. Rerun the gated pilot ingestion when BaoStock is reachable.

Development: **NOT RUN**

Validation: **NOT RUN**

Official OOS: **NOT RUN**
