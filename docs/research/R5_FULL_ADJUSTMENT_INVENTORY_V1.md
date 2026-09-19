# R5 full-range retained adjustment inventory v1 — 2026-09-19

Every retained Sina adjustment curve was checksum-bound to the accepted P0
point-in-time master and partitioned into pre-interval baseline, in-interval and
future rows. Reverse input order reproduced the same report.

## Coverage

- accepted master intervals: **5,436**
- securities: **5,431**
- verified interval curves: **5,436**
- conflicting interval curves: **0**
- unique retained source files: **5,442**
- in-range factor-change dates: **43,019**

Against the currently supported official cash, integer-bonus and rights ledgers,
40,691 factor-change dates have a same-security/same-date event and 2,328 do
not. All 153 supported rights events align to a factor-change date. Six
currently supported events have no factor change. These are routing results
only: a matching date does not prove numerical factor parity or the economic
transformation.

## Authority decision

`FULL_ADJUSTMENT_AUTHORITY = PARTIAL`

The inventory establishes retained-source identity, interval coverage and
absence of conflicting curve bytes. It does not yet establish full economic
alignment: cash and integer-bonus ledgers are partial, rights/mergers/other
share changes are not reconciled, fractional retained-bonus policy is open,
and raw reference-price parity has not been audited. Future curve rows are
preserved but excluded from each security interval.

Immutable report:
`/home/yuchen/data/research/staging/full-adjustment-audit-v1/retained-curve-inventory-v2.json`

- file SHA-256:
  `44e15ed8fc0c51314de513488bf66899f09a1e121363af90aa59ee85a4e8bcac`
- canonical manifest SHA-256:
  `31859c826876ae5830fb5dc95f03b6591d389300b3f85014c60a95789842bd87`
- checksum repeatability: **PASS**
- input-order reproducibility: **PASS**

No dataset, strategy result or authority PASS was produced.
