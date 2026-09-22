# R5 SZSE broad-subject date precedence v16 — 2026-09-19

Some official resumption notices quote an earlier announcement or planned
boundary before stating the final effective trading date. The shared parser
previously treated its broad `subject + date + resumption` pattern as equal to
the narrower explicit-date forms, causing a valid final date to be rejected as
ambiguous.

The broad subject pattern is now fallback-only. It is used only when no
anchored, relative or intraday effective-date form succeeds. This is pattern
precedence, not date ordering; the parser never selects a date merely because
it is earlier or later.

## Result

All retained official SZSE source bytes were replayed. One additional exact
boundary closes, while all 7,358 v15 boundaries keep the same date:

| Symbol | Suspended at | Exact resumption | Official evidence |
|---|---|---|---|
| 300316 | 2015/06/24 09:30 | 2015-10-08 | 关于终止筹划重大资产重组事项及股票复牌公告 |

`000422` is deliberately not counted. Its official notice describes two
adjacent boundaries: the 2018-04-16 halt was due to end on 2018-04-23, a new
risk-warning halt starts that day, and trading resumes on 2018-04-24. The
current one-date-per-document evidence model safely validates 2018-04-24 for
the second halt but cannot use that date across the intervening 2018-04-23
halt to close the first. The first event therefore remains unresolved rather
than being silently merged.

The resulting authority has 7,359 exact resumptions, 58 terminal closures,
zero conflicts and 3,388 unresolved SZSE boundaries. SSE remains 16,393/0
unresolved. Suspension authority remains
`PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`.

## Reproducibility

- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v15.json`
- retained replay file SHA-256:
  `297758c0a305be020bf8bdec04c3812d1b21a89e313dbb1201ca61251aecc60c`
- retained replay canonical manifest:
  `1034ffebcc2445ae1758952b7b0623ff62171d9484526dfde305ee59a9181805`
- resumption parser SHA-256:
  `6a625d0b1a9a54bea8fb86068ae52c14c765e34dbd4cd918a88b8e7aefee3671`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v19/suspension-authority-v1.json`
- full authority file SHA-256:
  `79f288a5c2627fb383be2b6567e983f7cb16e540cd207655e393aafcb95fe71d`
- full authority canonical manifest:
  `bde792f6663566cf5028099e696a01952fa92428d3d90a1f2dd6d5b7fd9b711e`
- normalized events SHA-256:
  `52f554e8e9ef18bf8c9b3d4944ab15d834192a14666da1825f170fec0f5a5326`
- unresolved facts SHA-256:
  `854e8c35576b1a80386612b3ed4e033915010dd7aa159d175486a9eec9895451`
- input-order reproducibility: PASS
- source checksum repeatability: PASS
- focused parser tests: 6 passed

No source bytes were downloaded. No symbol-specific parser rule was added. No
Full Dataset was created, audited or frozen. Development, Validation and
Official OOS remain unrun and locked. PR #12 remains open and unmerged. The
independent retained-bonus fractional methodology gate is unchanged.
