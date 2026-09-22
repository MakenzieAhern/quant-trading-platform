# R5 SZSE intraday and named-resumption parser v9

Status: **4 ADDITIONAL EXACT RESUMPTION BOUNDARIES ACCEPTED; AUTHORITY REMAINS PARTIAL**.

Parser v9 covers three narrow official forms that remained outside the dated
grammar:

1. `复牌时间为 YYYY年M月D日`;
2. a full-date morning halt followed by an explicit afternoon resumption; and
3. a full-date halt followed by `一小时后复牌` or `半天后复牌`.

The forms are deliberately bounded. `一天后`, disclosure-dependent,
application, conditional and deadline-only wording are not converted into
dates.

Accepted official boundaries:

- 000761: 2011-04-13 -> 2011-04-20
- 300086: 2011-02-14 morning halt -> same-date afternoon resumption
- 000506: 2012-01-05 halt -> same-date one-hour-later resumption
- 002456: 2015-10-28 -> 2015-10-30

Immutable reconciliations:

- batch 1 file SHA-256: `d0ba42aa823cfecd433b772409fc1ca49eaaab51e3d5f149ea0a03a9b7570455`
- batch 1 manifest: `df3f3ea7952e64eaaf65e1188f9b47c085bca297212546695a444f8896181320`
- batch 2 file SHA-256: `d2445531b1a40318c7d3182f01402f7c81a7e57a0d9afc5f4e591f1930b79ca9`
- batch 2 manifest: `a68071ee948b2e40670379521f8daa51482888ff9d49abe82b273740f35b45b2`

Full replay:

- true official resumption supplements: **8,913**
- official terminal closures: **58**
- unresolved SZSE boundaries: **1,834**
- conflicts: **0**
- authority manifest: `0c2678ac55fd0384e82d7c28601cf2f1e3e621c1d5d28e1067d92f606090fe42`

Suspension authority remains PARTIAL. No Full Dataset, freeze or strategy
study was produced.
