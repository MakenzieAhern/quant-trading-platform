# R5 SZSE monthly raw-gap reconstruction

Date: 2026-09-20

## Decision

`SZSE_20110725_PUBLIC_OFFICIAL_RECONSTRUCTION = PARTIAL_EXECUTION_FIELDS_UNRESOLVED`.

The remaining 239 source-presence gaps are all ChiNext observations on
2011-07-25. Free official SZSE evidence now fixes the close and bounds volume
and amount for every row. Propagating the full official amount interval through
the 20-session liquidity rule leaves the decision unchanged for 239/239 rows.
The maximum possible average-amount perturbation is CNY 170; the smallest
retained threshold margin is CNY 365.

This does not create complete raw bars. Exact official open is unavailable for
239 rows, high for 235, low for 228, volume for 239 and amount for 239. The date
is neither a configured rebalance session nor an execution session, but using a
partial, non-tradable feature observation is a material methodology choice and
is not approved here.

## Official evidence

| Evidence | Official URL | SHA-256 |
|---|---|---|
| Per-security monthly history endpoint | `https://www.szse.cn/api/market/ssjjhq/getHistoryData` | snapshot manifest `b30701e120d4ac74817d1b81d05242c883c021539bf92191b81713af7f115601` |
| July 2011 monthly statistics | `https://docs.static.szse.cn/www/market/periodical/documents/P020180328477226703858.html` | `66faa42440a1fd8cf021f78f43693e1edf8cce646a7c42ffeb47d2f74deefd0f` |
| July 2011 turnover-value table | `https://docs.static.szse.cn/www/market/periodical/documents/P020180328477218847613.html` | `dce5ad2eef57b92918d8dcdb59032b555246cd920806785ec21826e39bcb3593` |
| July 2011 official daily workbooks | retained SZSE daily-report URLs in the manifest | `d7bea9b7dde55b83abca4f11f67aa7d22d3e598837f2f4ea1ec3bbde4416c58a` |
| 2011-07-25 official block trades | retained SZSE `ShowReport` URL | `3e9bfa68f8b3b02a1b7c1a08473b9afd35c547988ae1038bba33f2bc2ee4cb5d` |

All response bytes and retrieval metadata remain outside Git under
`/home/yuchen/data/research/staging/full-raw-coverage-v1/`. The immutable V6
report is
`szse-20110725-monthly-reconstruction-v6/report.json`; file SHA-256 is
`f66b4a5237f1310aa1702b48f46f5887a86458f5f50660033605dc167a3e9f64`
and canonical manifest SHA-256 is
`ec29601a5b3d0968374aa34db8dc2720a4a9c461a8886289d9ab03c504b3738f`.

## Reconstruction method

1. The next official session's `pre_close` fixes the 2011-07-25 close.
2. The official July total minus the other 20 official daily observations and
   the two target-day official block trades yields conservative volume and
   amount intervals. Every displayed-value rounding quantum is included.
3. Tencent/Sina values are used only to test interval consistency. They remain
   non-authoritative and are not promoted or written as official facts.
4. The full amount interval, not merely the candidate difference, is propagated
   through the 20-session liquidity mean and compared with every retained
   threshold margin.
5. Reversing input order yields identical rows and two consecutive immutable
   report writes yield the same bytes.

## Results

| Check | Result |
|---|---:|
| Gap rows | 239 |
| Exact official close | 239 |
| Candidate volume inside official interval | 239 |
| Candidate amount inside official interval | 239 |
| Liquidity decision invariant over full official interval | 239 |
| Exact official open / high / low | 0 / 4 / 11 |
| Complete official OHLCV rows | 0 |
| Current history API rows / unavailable | 221 / 18 |
| Input-order reproducibility | PASS |
| Checksum repeatability | PASS |

One official cross-surface conflict is retained: for 300058, the current
monthly-history API reports July low 32.11 while the contemporaneous monthly
publication reports 31.350. The target-day low is not uniquely inferred for
that security, so the conflict does not change a reconstructed target field.
It is not silently resolved.

## Remaining gate

Choose exactly one path without inspecting strategy performance:

- approve an official partial feature row containing the exact close, bounded
  amount/volume evidence and derived liquidity eligibility, with open/high/low
  and exact amount/volume unavailable and execution permanently prohibited; or
- provide/authorize a manual official SZSE/SSIC archival extract that establishes
  exact 2011-07-25 per-security OHLCV.

No Full Dataset was created, frozen or studied.
