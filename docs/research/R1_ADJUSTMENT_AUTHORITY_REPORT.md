# R1 adjustment authority investigation

2026-09-10; starting commit `92a08589bead59227568888eabb97a071185fae4`.
No accepted ST audit was rerun. No strategy or performance metric was calculated.

## Recovered lineage

`BAOSTOCK_CAPABILITY_AUDIT.md` explicitly marks `query_adjust_factor` PARTIAL,
not accepted across the pilot. `CORPORATE_ACTION_POLICY.md` names forward-adjusted
close for features and raw execution prices. The adapter also exposes event factors.
No checksum-linked artifact was recovered that settles the intended complete
adjustment-method definition. Repository/data/history discovery from the preceding
recovery was reused, with targeted factor/SDK inspection this run.

Installed BaoStock package 0.8.9, SDK 00.8.90, implements `query_adjust_factor` via
`tcp://www.baostock.com:10030`, not a fabricated HTTP endpoint. SDK source SHA-256:
`d5a96d956c5f44823740ad8e216257158dc9214dcaaf36541c8f8c6503014421`.
Two fresh anonymous-login attempts both returned 10002007 after bounded timeouts;
no factor response was obtained. Exact vendor factor/revision semantics therefore
remain empirically unverified. No credential or access-control workaround was used.

## Candidate evidence, not substitution

[AKShare documentation](https://akshare.akfamily.xyz/data/stock/stock.html)
identifies `stock_zh_a_daily(adjust="hfq-factor")` as the Sina factor interface.
Installed version 1.18.94 uses
`https://finance.sina.com.cn/realstock/company/{symbol}/hfq.js`.
Its HFQ path multiplies raw price by the most recent dated factor. The factor
branch ignores requested date bounds; any accepted consumer must filter explicitly
and never use a future factor or backfill a missing baseline. Raw execution remains
separate. A frozen snapshot is not proof of historically available publication time;
the vendor's historical revision policy remains UNKNOWN.

The SDK uses eval on the response. This investigation did NOT execute that path:
it decoded the JSON assignment safely, retaining original response text and hashes.
The initial parser attempt included a trailing comment and failed; those failures
are preserved. Correct first-line JSON parsing then recovered these repeated samples:

| Symbol | Factor rows | Two-fetch logical SHA-256 (identical) |
| --- | ---: | --- |
| sh600000 | 29 | 9df567d97499c4d38c97134efeaf3057eb0b84602baff2e267d018ff6cc2262b |
| sz000001 | 32 | 090f4b1683c09dfe00f8b1b64ad6c885254fb94c66f1a6df8495f49b0ec0d41e |
| sz000732 | 12 | aea5bc697c4cc8893f70ed8a33ad5f542878b9b6a216d9328ef48c486e5bad88 |
| sz002113 | 5 | 5f12b054735940a248f53e7998df13946b5b2dce775c6560b4a1a734307ffe1b |

All supplied factors are positive. These are source samples, not full-universe
coverage, a pilot dataset, or proof of corporate-action economic completeness.

## Concrete method mismatch

The existing AKShare raw route is `stock_zh_a_hist(adjust="")`, Eastmoney
`https://push2his.eastmoney.com/api/qt/stock/kline/get`, daily klt=101, fqt=0.
Four bounded WSL SDK calls failed with ConnectionError. Native Windows HTTPS
reached the same endpoint; neither provider nor adjustment mode was silently changed.
Raw and fqt=2 HFQ source responses for 600000 were retained outside Git.

On 2023-07-17 raw close=7.42 and Eastmoney HFQ close=78.53. On 2023-07-18 they
are 7.39 and 78.34. Assuming half-cent rounding of adjusted prices, implied factor
intervals are [10.582884,10.584232] and [10.600135,10.601489]: disjoint.
Sina's dated multiplicative factor is unchanged between those dates. The two
methods cannot be made equivalent by choosing one constant base multiplier.
This is a mathematical methodology difference, not a claim either vendor is corrupt.
Do not turn daily adjusted/raw ratios into authoritative corporate-action factors.

## Decision and retained artifacts

ADJUSTMENT_AUTHORITY = PARTIAL_CANDIDATE
OHLCV_AUTHORITY = BOUND_NOT_ACCEPTED
SOURCE_AUTHORITY_PREFLIGHT = FAIL
STOP_CONDITION = AUTHORITATIVE_SOURCE_AMBIGUITY

The smallest unresolved item is the authoritative adjustment-method choice/lineage.
Recover the accepted definition or explicitly resolve the new methodology, then
validate it before proceeding. No provider definition is selected from performance.
The raw response alone does not settle suspension status, benchmark alignment,
market-rule acceptance or full-universe coverage. No R2/R3 result is claimed.

External root: `/home/yuchen/data/research/staging/source-authority-r1-20260910`.
Contains BaoStock failure probe, Sina raw-text snapshots with metadata, original
Eastmoney JSON, adjustment-semantics audit and canonical source-authority manifest.
Canonical manifest SHA-256:
`7eec56c7d3ba16b137851686258b6a65ef59e83d4f7c291bf4b7331e67729fbb`.
All retained JSON artifacts are individually hashed in that manifest. Windows raw
download timestamps were not recovered into metadata and are not invented.
The manifest records a failed R1 preflight, not a successful publication.
