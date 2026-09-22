# R5 SZSE application-boundary revalidation v17 — 2026-09-19

Full retained-source replay exposed two shared parser defects with opposite
effects.

First, a one- or two-digit day token could backtrack before the following
time-of-day grammar. Text such as `11月10日恢复交易` could therefore create the
false date `11月1日`. Deadline, postponement and planned-application phrases
also remained admissible in several observed forms.

Second, the application guard rejected final official clauses such as `经公司
向深圳证券交易所申请，公司股票自...开市起复牌`. These are completed effective
trading statements, not requests to resume. The guard now accepts that exact
form while continuing to reject `计划...申请复牌`, `将申请复牌`, deadlines,
postponements and documents with conflicting effective dates.

## Result

The same checksum-bound official source bytes were replayed with no downloads.
Relative to v16 authority:

- 1,397 previously missed final official boundaries are accepted;
- 40 false or non-final boundaries are reopened;
- four boundaries receive corrected dates from explicit final notices;
- input-order replay remains deterministic and conflicts remain zero.

The four corrected dates are:

| Symbol | Suspended at | Prior date | Correct date |
|---|---|---|---|
| 000735 | 2014/09/12 09:30 | 2017-02-23 | 2014-09-17 |
| 002576 | 2016/06/14 09:30 | 2016-12-13 | 2016-12-12 |
| 300211 | 2014/09/09 09:30 | 2014-09-29 | 2014-09-09 |
| 300352 | 2016/10/21 09:30 | 2016-10-28 | 2016-10-31 |

All 17 newly admitted rows whose document titles omit `复牌`, `恢复交易`,
`恢复上市` or `退市整理` were manually screened. Thirteen contain an explicit
final effective trading clause. Four merely plan or apply for resumption and
are rejected by the shared rule. No symbol-specific exception was added.

The resulting authority has 8,716 exact resumptions, 58 terminal closures,
zero conflicts and 2,031 unresolved SZSE boundaries. SSE remains 16,393/0
unresolved. Suspension authority remains
`PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`.

## Reproducibility

- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v21.json`
- retained replay file SHA-256:
  `cfafd1903b5eee30a6fc41274a691b8906ae13414189fc7917d910e29cde7aff`
- retained replay canonical manifest:
  `1b2c0d351b95b53f5b89596de44dc0f81d8e3e32106c85fc105f173c4a095ffc`
- resumption parser SHA-256:
  `d027a897ec639887b6020d3968ac2c6afdf75d6156fa5197d68bf3fd2f3e2177`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v20/suspension-authority-v1.json`
- full authority file SHA-256:
  `0ad5240b4a59b8dc76de9b600ba5550cc693d0fe260566081d73458af760fd65`
- full authority canonical manifest:
  `9116c5f14ab1b95f1477d0cff55b44746fe0484066621243786d2bad15d0f0bc`
- normalized events SHA-256:
  `d59c56db3281c3dff4ced45426c582d2d89ac85716bd511186382fd9bb9b044a`
- unresolved facts SHA-256:
  `fc067aa1cf27d798fc8dc8aa26f9fd7bce582388dd845468c16fee651253542a`
- input-order reproducibility: PASS
- source checksum repeatability: PASS
- focused parser tests: 6 passed

No Full Dataset was created, audited or frozen. Development, Validation and
Official OOS remain unrun and locked. PR #12 remains open and unmerged. The
independent retained-bonus fractional methodology gate is unchanged.
