# R5 SZSE normal-trading boundary parser v8

Status: **4 ADDITIONAL EXACT RESUMPTION BOUNDARIES ACCEPTED; AUTHORITY REMAINS PARTIAL**.

Retained official notices used `恢复正常交易` as an effective trading term,
which the prior `复牌 / 恢复交易` grammar did not cover. Parser v8 adds that
exact form and fixes a separate multi-date ambiguity: a sentence may name a
disclosure or meeting date before the actual resumption date. A match is now
accepted only when its matched clause contains at most one date; overlapping
matching then selects the date immediately attached to the resumption term.
Conditional or application-only phrases remain rejected.

Accepted official boundaries:

- 000100: 2011-02-25 suspension -> 2011-02-28 resumption
- 300043: 2011-02-25 suspension -> 2011-02-28 resumption
- 000625: 2011-04-15 suspension -> 2011-04-18 resumption
- 000423: 2013-07-12 suspension -> 2013-07-15 resumption

The conditional 000981 notice and the `最迟` 002217 notice remain unresolved;
neither is converted into a fact.

Immutable reconciliation:

- path: `/home/yuchen/data/research/staging/full-szse-resumption-v6/szse-normal-trading-reconciliation-v8.json`
- file SHA-256: `ec7c488a3d97b7daa9497b36daf21d22780f2ad0e0b592bf31bf47a4e339ac25`
- canonical manifest SHA-256: `182326c1cb725a0352e042e9c7cae905abdfd10b55addc3dd6e4ff2342adeb41`

Full replay:

- true official resumption supplements: **8,909**
- official terminal closures: **58**
- unresolved SZSE boundaries: **1,838**
- conflicts: **0**
- authority manifest: `aade1e18a17347dae231a6fbd3d834ea3cabf9c481a2a1322fe2e7649dffb6fb`

Suspension authority remains PARTIAL. No Full Dataset, freeze or strategy
study was produced.
