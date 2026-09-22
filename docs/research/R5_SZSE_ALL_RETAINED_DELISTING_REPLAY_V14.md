# R5 SZSE all-retained delisting-boundary replay v14 — 2026-09-19

The v13 parser improvement was replayed over every retained official SZSE
resumption source, not only the 31-document v13 acquisition batch. This closes
14 additional exact suspension boundaries from official documents already on
disk. No new source bytes were downloaded and no symbol-specific parser rule
was added.

## Result

The all-retained replay accepts 7,348 exact resumptions. Together with the 58
existing terminal closures, the full authority has zero conflicts and 3,399
unresolved SZSE boundaries, down from 3,413. SSE remains 16,393/0 unresolved.
Suspension authority therefore remains
`PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`.

The 14 newly exposed boundaries relative to the accepted v11 + v13 union are:

| Symbol | Suspended at | Exact resumption | Official evidence |
|---|---|---|---|
| 000502 | 2022/05/05 09:30 | 2022-06-06 | 关于收到股票终止上市决定的公告 |
| 000611 | 2022/05/05 09:30 | 2022-06-07 | 关于收到公司股票终止上市决定的公告 |
| 000613 | 2022/05/05 09:30 | 2022-06-08 | 关于收到公司股票终止上市决定的公告 |
| 000662 | 2021/01/14 09:30 | 2021-02-26 | 关于公司股票进入退市整理期交易的第一次风险提示性公告 |
| 000673 | 2022/05/05 09:30 | 2022-06-13 | 关于收到股票终止上市决定的公告 |
| 002147 | 2022/05/05 09:30 | 2022-06-01 | 关于收到公司股票终止上市决定的公告 |
| 002447 | 2022/05/05 09:30 | 2022-06-06 | 关于收到股票终止上市决定的公告 |
| 002464 | 2022/04/29 09:30 | 2022-06-07 | 关于收到股票终止上市决定的公告 |
| 002473 | 2022/05/05 09:30 | 2022-05-31 | 关于股票进入退市整理期交易首日的风险提示公告 |
| 002499 | 2023/02/03 09:30 | 2023-03-27 | 关于收到股票终止上市决定的公告 |
| 002618 | 2022/05/05 09:30 | 2022-05-31 | 关于公司股票进入退市整理期交易首日的风险提示公告 |
| 002684 | 2022/05/05 09:30 | 2022-06-06 | 关于收到股票终止上市决定的公告 |
| 300372 | 2016/08/23 09:30 | 2017-07-17 | 关于公司股票进入退市整理期交易暨股票将被终止上市的风险提示公告 |
| 300431 | 2020/07/01 09:30 | 2020-09-21 | 关于公司股票进入退市整理期交易暨终止上市的第一次风险提示公告 |

Every accepted document contains one unique effective trading date. Binding
still selects the earliest exact resumption after the halt and before the next
halt. Existing continued-halt precedence remains in force; no proposed,
conditional, application-only or deadline date is admitted.

## Reproducibility

- retained replay report:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v12.json`
- retained replay file SHA-256:
  `8f7193e91faa6f3f14c544caaff32d08bb8f342e3175b6b8b10bafbf81b42d7d`
- retained replay canonical manifest:
  `f2f2ef027dc397f67f523a550f061a099d5880921991d51556ee2c1bd4d699f1`
- resumption parser SHA-256:
  `c08794df73867291f64297664eabc2c7e007b113efe6aaf78bfd59160720275e`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v17/suspension-authority-v1.json`
- full authority file SHA-256:
  `f2f58be4a3c324de9f199ec9ed4af7747eabc554f0d4fc1558d2beb439b76b40`
- full authority canonical manifest:
  `36cc1b50f2d1a96720ea48b5bb96e534eb750be05e886b3509d4513479131075`
- normalized events SHA-256:
  `2f7420f69c2765af33c8e62d88f2701a16e752c84fd0068f7e5e0617218be00b`
- unresolved facts SHA-256:
  `47dea5d7b4a2fc51523762f006b45fa6b0960ffcf3999eae105cbc93887fc161`
- input-order reproducibility: PASS
- source checksum repeatability: PASS
- focused parser tests: 6 passed

No Full Dataset was created, audited or frozen. Development, Validation and
Official OOS remain unrun and locked. PR #12 remains open and unmerged. The
independent retained-bonus fractional methodology gate is unchanged.
