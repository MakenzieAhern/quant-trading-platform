# A-Share Data Readiness Report

Status: **BLOCKED — official research must not run**  
Assessment date: 2026-09-07

| Requirement | Status | Evidence / limitation |
|---|---|---|
| Historical OHLCV | YES | BaoStock raw daily fields were probed successfully. |
| Trading calendar | YES | BaoStock trading-date endpoint is normalized by the adapter. |
| Listing history | YES | IPO date is available through stock basics. |
| Delisting history | PARTIAL | Exit dates exist where populated; completeness for delisted securities has not been audited. |
| Historical ST state | YES | Daily `isST` is normalized point in time. |
| Suspension status | YES | Daily `tradestatus` is normalized point in time. |
| Adjustment data | YES | Raw and backward-adjusted closes are ingested separately; execution remains raw. |
| Liquidity data | YES | Volume, amount and turnover are available, subject to provider methodology notes. |
| CSI300 benchmark | YES | Historical index bars are available. |
| Historical benchmark membership | YES | A 2010 CSI300 membership query returned 300 effective-date records. |
| Corporate actions | PARTIAL | Provider dividend data was observed, but a versioned normalization and holdings/cost-basis application pipeline is not complete. |
| Historical market rules | PARTIAL | Effective-dated core rules and costs exist; complete security-specific historical exceptions remain unaudited. |

Material blockers are corporate-action correctness, delisted-security coverage, and complete
historical rule exception validation. Each can bias returns or the eligible universe. No immutable
production dataset ID/checksum has therefore been frozen. Development, validation and official
out-of-sample studies are prohibited until this report is replaced by a fully evidenced `YES` gate.

Official OOS status: **OUT-OF-SAMPLE NOT YET RUN**.
