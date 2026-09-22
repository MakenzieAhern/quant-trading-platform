# R5 SZSE 2011-07-25 raw-row candidate audit v1

## Scope

The v32 official SZSE row-presence audit leaves exactly 239 unresolved
security-days. Every row is a ChiNext security on 2011-07-25. The retained
official daily workbook omits the whole ChiNext block on that date, so it cannot
establish a bar or prove a market-wide suspension. The fixed source-gap report
SHA-256 is
`7350f64444a39b10b43dc1b4650174628272c773c29df4079e210fbec37da9ed`.

This audit is candidate evidence only. Tencent and Sina are not promoted to
official authority under `OFFICIAL_PUBLIC_SOURCE_RECONSTRUCTION_V1`.

## Deterministic audit

`backend/scripts/probe_r5_szse_raw_gap.py` reuses the fixed 239-row residual and
the pinned offline Sina decoder. It checkpoints each raw response with URL,
retrieval timestamp, response SHA-256 and HTTP metadata. The pinned decoder
SHA-256 is
`435bf1763531d0eb33d9a8ba25fbc9ab3c5bcc11bbd7834978cbdfdec4c0bbb9`.
The 478 unique source responses were retrieved between
2026-09-19T17:27:21.214217+00:00 and 2026-09-19T17:39:18.318913+00:00.

The amount comparison applies the already-accepted closed interval of plus or
minus 100 CNY. It also reuses the existing 20-observation liquidity rule and
checks every contiguous window containing 2011-07-25. This is a conservative
superset of scheduled evaluations and does not inspect strategy performance.

The audit also parses the official SZSE 2011 statistical yearbook directly.
The retained PDF was retrieved at 2026-09-18T20:04:12.261327+00:00 from
`https://docs.static.szse.cn/www/market/periodical/year/W020250610540370351431.pdf`.
Its SHA-256 is
`38289a861878de122015747d09ca3dc1f7e05de127c572ae2ac4792206460bd4`.
Printed pages 147 and 148 (PDF pages 163 and 164) report the 2011-07-25
ChiNext totals as 432.73 million shares and 9,673.76 million CNY.

## Results

- fixed residual rows completed: 239 / 239
- OHLC parity: 239 / 239
- volume parity: 239 / 239
- amount within accepted interval: 239 / 239
- maximum amount difference: 52 CNY (`CN-A:SZSE:300021`)
- liquidity decisions invariant: 239 / 239
- liquidity windows checked: 4,684
- minimum distance to the 10,000,000 CNY threshold: 365 CNY
  (`CN-A:SZSE:300019`)
- input-order reproducibility: PASS
- access denials or retrieval failures: 0
- candidate total: 431.34 million shares and 9,649.92 million CNY
- official minus candidate: 1,385,518 shares and 23,836,400 CNY for Tencent;
  Sina differs from Tencent by only 65 CNY
- official aggregate parity: FAIL
- official block trades: 2 rows for 300020 and 300166, totalling 1,390,000
  shares and 23,837,000 CNY
- candidate plus official block trades at yearbook precision: PASS for both
  providers (432.73 million shares / 9,673.76 million CNY)
- candidate report file SHA-256:
  `1afdab62bb7b244beef5be97604bf6a47f37ea43bdac7d73b0a101b3e8372919`

The external report is
`/home/yuchen/data/research/staging/full-raw-coverage-v1/tencent-sina-20110725-candidate-v1/report.json`.
Raw responses remain outside Git. The official SZSE block-trade XLSX hashes
for tabs 1/2/3 are respectively
`6af77beb3db19b19af2884d5c36415ee6b2729473b96f763838edd0f42fd8478`,
`7cf3a7542336d24605558e3cd1aac01ea0c569d214ec4e764cad75597e2f0fb1`
and `591ed686e34824214953678e2e64d777fac323e0ff06a890e5e04be2898ae843`.

## Authority decision

The candidate values are mutually consistent and the accepted amount precision
cannot change any relevant liquidity decision. Official block-trade detail now
explains the board-level aggregate difference at the yearbook's published
precision, establishing that the candidate volume/value excludes those two
block trades. It still does not make the non-official per-security OHLC bars an
official source or settle the separate 223-symbol after-hours scope question.
`RAW:FULL_UNIVERSE` therefore remains open. No provider is promoted and no Full
Dataset, freeze or study is authorized by this result.
