# R5 SZSE post-close transaction-scope closure v2

## Result

The separate 2023-04-10 SZSE transaction-scope diagnostic is closed. Of 2,761
Pilot/official daily comparisons, 2,504 match directly within display
precision, 34 reconcile to checksum-bound official block trades and the
remaining 223 ChiNext rows have the deterministic post-close fixed-price
signature. Unexplained scope gaps are **zero**.

The official SZSE guidance states that ChiNext post-close fixed-price trades
execute at the day's close and are added to the stock's daily total after that
session. The official technical notice separately states that
`cashsecurityclosemd_YYYYMMDD.xml` excludes those post-close quantities and
amounts. After subtracting official block trades, each of the 223 residuals is
the missing share quantity multiplied by the official close, within the source
display bounds.

## Authority boundary

This establishes the reason for the transaction-scope difference. It does not
directly observe each post-close trade and does not promote Tencent, Sina or
the 239 separate 2011-07-25 candidate rows to official per-security OHLCV
authority. `RAW:FULL_UNIVERSE` therefore remains open solely on the separate
239-row official-source gap.

## Immutable evidence

| Artifact | SHA-256 |
|---|---|
| Official guidance snapshot | `747f6ed2d82fd3036de57d51444eee66bfdc70969585536305519c21f7efbc14` |
| Official technical-notice snapshot | `400fc548fb053eb4f08791e8d088f68579328e9969c15c7b02670eaa23f661fe` |
| `szse-postclose-scope-v1/scope-audit-v2.json` | `3f715a039a7d7fca78961f36f0c8d32745e645194a1f57ba7150d80cea3333ba` |
| Audit manifest | `4c9a314bb10fc84719da13f46c1c463f9e2f0ecd0d5ad3611e84466b09532da7` |
| Full-source preflight v11 | `0ee4bd5c279cdb0b754041597548f05e4cd0963fb1640e7aa2aba6336239d138` |
| Preflight manifest | `f98e4e34668478403674a747065b5a5d018198287017b92a78600b6a3d1fed4c` |

Input-order replay and repeated artifact generation are byte-identical. The
Full Dataset remains uncreated, unaudited and unfrozen; no study was run.
