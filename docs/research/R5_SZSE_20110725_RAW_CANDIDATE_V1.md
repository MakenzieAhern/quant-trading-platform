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
- candidate report file SHA-256:
  `314d8953ebdb3171e38f7ebca92027d25521d376316627d8f615476864ab53d8`

The external report is
`/home/yuchen/data/research/staging/full-raw-coverage-v1/tencent-sina-20110725-candidate-v1/report.json`.
Raw responses remain outside Git.

## Authority decision

The candidate values are internally consistent and the accepted amount
precision cannot change any relevant liquidity decision. This closes the
bounded value-reconstruction diagnostic, but not official raw authority.
`RAW:FULL_UNIVERSE` remains open because the candidate providers are
non-official and the separate 223-symbol SZSE official all-methods versus
auction/raw transaction-scope question remains unresolved. No Full Dataset,
freeze or study is authorized by this result.
