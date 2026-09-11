# R2 raw failover acceptance checkpoint

## Decision

PRIMARY_CURRENT_OPERATIONAL_STATUS = PRIMARY_SYSTEMIC_TRANSPORT_FAILURE.
RAW_OHLCV_PRIMARY_AUTHORITY = PASS (previous authority is preserved).
RAW_OHLCV_SECONDARY_AUTHORITY = NOT_PROMOTED.
RAW_OHLCV_FAILOVER_POLICY = CANDIDATE_NOT_ENABLED.
CROSS_SOURCE_PARITY = PARTIAL. R2 remains blocked, not Gate A.

This decision distinguishes source qualification from current transport availability.
Six fixed primary probes covered SSE main 600000, SZSE main 000001, STAR 688001,
ChiNext 300750 and exited controls 600070/300336. All six closed before HTTP response.
No rate-limit or network-path cause is asserted. This new diagnostic consumed one
request per member, not another full-universe retry; 600070 now has one additional
diagnostic after its previous five exhausted acquisition attempts. Original evidence
and the 657 successful input/partition vintages are unchanged.

## Recovered route evidence and limitations

The repository, full Git history search, local research data, staging and prior
provider reports did not contain a recoverable Tencent acceptance manifest or
snapshot. Do not turn the user's historical capability description into a prior
PASS. The exact installed AKShare 1.18.94 source was recovered and its SHA-256
matches its package RECORD: aa9199665d356ba3a054297004e349d3926fa83026abfd2d50c4b7f832226d84.

Candidate: Tencent, `stock_zh_a_hist_tx(adjust="")`, endpoint
`https://proxy.finance.qq.com/ifzqgtimg/appstock/app/newfqkline/get`.
The [official AKShare interface documentation](https://akshare.akfamily.xyz/data/stock/stock.html)
identifies the empty-adjust route as unadjusted; its older displayed schema is not
used to override the pinned SDK or actual response. No function name was guessed.

Requests use `_var=kline_day{year}`, `param={sh|sz}{symbol},day,{year}-01-01,{year+1}-12-31,640,`,
and the SDK's fixed `r` value, with years 2023 and 2024. This captures the SDK's
underlying raw requests directly, not its whole wrapper: the wrapper's auxiliary
start-year lookup uses adjusted metadata and an unbounded timeout; it is unnecessary
with the accepted PIT master. No adjusted quote was fetched or used. The response
pads years to 640 rows and includes live quote metadata: only `day` rows within
2023-01-01..2024-07-31 are normalized. Never fall back to `qfqday` or `hfqday`.

Raw row schema: date, open, close, high, low, volume, auxiliary object, turnover,
amount, further auxiliary fields. Prices use Decimal, amount field 8 is in ten-thousand
CNY units. Candidate volume normalization uses shares for SSE STAR and lots times
100 for the other sampled boards. The pinned SDK incorrectly exempts `sz000...`
from lot conversion: its 000001 output would be 100 times too small. The candidate
parser makes this difference explicit; it is not silently treated as identical SDK
output. This proposed correction matches primary volume across all 382 000001 dates.
STAR primary whole-lot versus Tencent share precision explains differences of up to
50 shares; all remaining sampled volume fields agree exactly after unit conversion.

Sina `stock_zh_a_daily(adjust="")` uses
`https://finance.sina.com.cn/realstock/company/{symbol}/hisdata_klc2/klc_kl.js`.
Existing immutable snapshots demonstrate active history and raw history for exited
000732; the full SDK wrapper fails when ancillary outstanding-share data is null
and also forward-fills its outer join. The raw decoder, not that filling behavior,
was reused offline. Previous accepted Sina factor authority is NOT raw-OHLCV
failover acceptance. No Sina partition was substituted. One targeted 300336 raw
snapshot was retrieved only to investigate the remaining amount discrepancy.

## Actual candidate coverage and checks

Eight deterministic members, two yearly raw requests each, repeated twice: 32
requests total. All yielded HTTP responses and matching normalized Pilot rows.

| Security | Role | Pilot rows | First | Last |
| --- | --- | ---: | --- | --- |
| SSE:600000 | Active main | 382 | 2023-01-03 | 2024-07-31 |
| SZSE:000001 | Active main | 382 | 2023-01-03 | 2024-07-31 |
| SSE:688008 | Active STAR | 382 | 2023-01-03 | 2024-07-31 |
| SZSE:300750 | Active ChiNext | 382 | 2023-01-03 | 2024-07-31 |
| SSE:600070 | Post-Pilot exit / ST history | 380 | 2023-01-03 | 2024-07-31 |
| SZSE:300336 | Pilot exit | 91 | 2023-01-03 | 2023-07-04 |
| SZSE:000732 | Pilot exit | 100 | 2023-01-03 | 2023-06-02 |
| SSE:603125 | Pilot IPO | 319 | 2023-04-10 | 2024-07-31 |

Observed route checks (not full-universe dataset acceptance):

| Check | Result |
| --- | --- |
| RAW_UNADJUSTED_SEMANTICS | PASS for candidate `day` parser; SDK unit issue explicitly separated |
| DATE_COVERAGE | PASS for observed sample ranges; absent sessions are not inferred suspensions |
| SECURITY_COVERAGE | PASS for all eight fixed sample IDs; full universe NOT tested |
| DELISTED_SECURITY_HANDLING | PASS for three exited samples, no lifecycle-driven omission |
| LISTING_BOUNDARY | PASS, including 603125 actual 2023-04-10 IPO |
| DELISTING_BOUNDARY | PASS, no returned Pilot row on/after master delisting date |
| OHLC_VALIDITY | PASS |
| NON_NEGATIVE_VOLUME | PASS |
| DATE_MONOTONICITY | PASS within each raw response |
| DUPLICATE_SECURITY_DATE | PASS; only identical overlapping year rows coalesced |
| INPUT_ORDER_REPRODUCIBILITY | PASS for reversed yearly input order |
| REQUEST_REPEATABILITY | PASS for both normalized snapshots |
| SOURCE_LINEAGE | PASS, request URL/parameters, UTC and raw/meta hashes retained |
| CHECKSUM_REPEATABILITY | PASS for canonical normalized rows and offline audit replay |
| CROSS_SOURCE_PARITY | PARTIAL, four unexplained amount differences |

Six cached primary controls provide 1,719 matching dates and 6,876 identical numeric
OHLC comparisons. No material price or missing-date difference was observed.
Raw response bytes may differ because of live ancillary metadata; normalized
historical rows and their logical hashes are repeatable. No live quote leaks into
the accepted-date candidate rows.

## Smallest remaining evidence issue

Direct Tencent amount display precision is 0.01 ten-thousand CNY, half quantum
50 CNY. Four differences exceed that direct explanation; no arbitrary larger
tolerance is adopted. Values below are CNY, not share volume or adjusted prices.

| Security/date | Eastmoney | Tencent | Preserved Sina | Direct difference |
| --- | ---: | ---: | ---: | ---: |
| 000001 / 2024-03-18 | 1761249149.98 | 1761249200 | 1761249150 | 50.02 |
| 300750 / 2023-11-28 | 3443539749 | 3443539800 | 3443539750 | 51 |
| 300750 / 2024-04-23 | 2113386949 | 2113387000 | 2113386950 | 51 |
| 300336 / 2023-04-20 | 44005849 | 44005900 | 44005850 | 51 |

Tencent agrees with rounding Sina's whole-CNY value to hundreds. That is evidence
consistent with a precision chain, not independent proof of Eastmoney's remaining
0.02–1 CNY discrepancy. No documented provider-processing explanation or prior
accepted cross-vendor precision policy resolves it. Classification remains
UNEXPLAINED_DIFFERENCE for these four amounts; no price discrepancy is implied.
Resolution requires supported vendor precision evidence or an explicit narrowly
scoped amount-precision policy decision. Do not randomly choose a different provider.

## Immutable artifacts and continuation

External staging `raw-failover-v1/` contains all new raw/meta files and audits:

- `primary-probe/report.json`: 513f04d0ec47408b1f49503af5168eb07d2fbf5270b6a661f4c8e32bf3157d9c
- `candidate-audit.json`: ff0e31d2ffca13fb174995a1bd31eb3f4a6342c0c013dfc26779708469c3db47
- `parity-{symbol}.json`: every date/field comparison; hashes in candidate audit.
- `sina-corroboration/report.json`: ec22b99a0d9724160ab4ef161d84b2482acad8521cae32ac6d8cc2c62f8204c7
- `sina-corroboration/sz300336.js`: 0deef17dfd8d010eadbb111b14a2990baad85b4c48ab18e945759485e806ee23

Policy `CN_A_RAW_OHLCV_FAILOVER_V1.json` is versioned but NOT enabled. Primary
authority manifest is immutable and unchanged; no secondary was promoted into
the Source Authority Manifest. Policy selection is transport-driven, never
performance-driven, and forbids fallback for quality/authority disagreements.
The accepted Sina adjustment authority remains a separate research-only input.

R2 state counts remain: PRIMARY_SUCCEEDED=657; PRIMARY_FAILED_SECONDARY_RECOVERED=0;
PRIMARY_FAILED_SECONDARY_FAILED=0 (no production secondary attempt was authorized);
AUTHORITATIVELY_NO_DATA_EXPECTED=0; UNRESOLVED_REQUIRED_DATA=4521. Candidate samples
are not counted as recovered Pilot partitions. Original checkpoint and partition
SHA-256 values remain pinned. No exclusion, publication, R3, freeze or study ran.

Offline reproduction: `python -m scripts.audit_raw_failover --staging /external/staging`.
Tests: `pytest tests/test_raw_failover.py tests/test_stage_akshare_pilot.py`.
400 backend tests PASS; Ruff, format and strict mypy PASS. No new dependency,
framework, provider-switching runtime or speculative ingestion layer was added.
