# R5 transaction-cost official-source closure v7

## Result

Checksum-bound original ChinaClear fee tables close the two remaining public
SSE transfer-fee claim groups. Public official market-rule authority is now
`PASS_PUBLIC_OFFICIAL_MARKET_RULES_ACCOUNT_CONVENTION_PENDING`.

| Effective interval | Investor total | ChinaClear component | Broker-retained component | Basis |
|---|---:|---:|---:|---|
| 2010-01-01 to 2012-05-31 | 1 per mille | 0.5 per mille | 0.5 per mille | face value |
| 2012-06-01 to 2012-08-31 | 0.75 per mille | 0.375 per mille | 0.375 per mille | face value |
| 2012-09-01 to 2015-07-31 | 0.6 per mille | 0.3 per mille | 0.3 per mille | face value |

The first interval follows the official 1-per-mille total and 50/50 split. The
middle interval combines ChinaClear's explicit 0.375-per-mille component with
the uniquely implied prior broker component: the official September notice
reduces that component by 20 percent to 0.3 per mille. The final interval is
explicit in the September 2012 fee table and is repeated in January 2013.

The historical ChinaClear URLs no longer serve the files directly. The exact
published bytes were recovered through an archival transport and are retained
with their original ChinaClear URLs, archival timestamps and SHA-256 values.
The archive is transport only; ChinaClear remains the authority.

## Remaining methodology boundary

The public fee table states no ChinaClear A-share transfer minimum from
2012-09-01. Whether a broker or account applies a separate minimum, and whether
the research commission input is net or all-in, depends on the account contract
or an explicit research convention. No universal account practice is inferred.

The executable model is unchanged. No Full Dataset was created, audited or
frozen, and no strategy study was run.

## Immutable evidence

| Artifact | SHA-256 |
|---|---|
| ChinaClear SSE fee table updated 2010-12-01 | `b4d76d4ff31d20e84ba56795229b051d11e52f4f42027a3d868437583f9f3350` |
| ChinaClear SSE fee table updated 2012-09-01 | `256e6aaab90312497321cf5b1551b366a21d4fa21677051a4c42c3e3ee18e082` |
| ChinaClear SSE fee table updated 2013-01-01 | `5a0d4bbafcf6f3efd3694f6adbb9aec4204af5bec8eb6128d3c9e0cc21a0907e` |
| Transaction-cost report v7 | `7d4f7ebd80e697c31bbfe93b5a0e6a49d824008175842a78802eb78359adf928` |
| Transaction-cost manifest | `a82ba13093b4ab7b698a525097c9c503c17480f26a4a929e93cc55138c0457de` |

The three recovered fee tables were retrieved at `2026-09-20T09:41:39Z`.
Report replay, source checksum repeatability and input-order reproducibility all
pass.
