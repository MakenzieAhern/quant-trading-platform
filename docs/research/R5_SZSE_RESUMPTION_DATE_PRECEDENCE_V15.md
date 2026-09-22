# R5 SZSE resumption-date precedence v15 — 2026-09-19

Official resumption notices often contain both a final trading boundary and
nearby dates quoted from earlier notices, applications, deadlines or progress
history. The strict parser previously combined its anchored trading-boundary
patterns with a broad fallback pattern. If the fallback found a second date,
the entire document was conservatively rejected as ambiguous.

The parser now uses the broad full-date and month-day lookaheads only when no
anchored or relative effective-date pattern succeeds. This is parser-pattern
precedence, not date ordering: it never chooses the earlier or later date and
does not use observed prices or future trading performance.

## Result

All retained official SZSE sources were replayed. Ten exact boundaries close
relative to v14, while all 7,348 previously accepted boundaries retain the
same date. No source bytes were downloaded and no symbol-specific rule was
added.

| Symbol | Suspended at | Exact resumption | Official evidence |
|---|---|---|---|
| 000779 | 2015/09/08 09:30 | 2015-12-22 | 董事会关于重大资产重组事项复牌的公告 |
| 000962 | 2016/02/02 09:30 | 2016-07-29 | 关于终止筹划重大资产重组暨公司股票复牌的公告 |
| 002012 | 2016/01/19 09:30 | 2016-07-18 | 关于终止重大资产重组事项的投资者说明会召开情况暨公司股票复牌的公告 |
| 002379 | 2016/11/08 09:30 | 2017-04-19 | 关于公司股票复牌的提示性公告 |
| 002598 | 2018/05/18 09:30 | 2018-06-01 | 关于公司股票复牌的公告 |
| 002779 | 2016/10/11 09:30 | 2016-12-12 | 关于终止重大资产重组暨复牌的公告 |
| 002787 | 2017/03/22 09:30 | 2017-09-25 | 关于公司股票复牌的提示性公告 |
| 300319 | 2015/08/24 09:30 | 2015-11-13 | 关于终止重大资产重组暨公司股票复牌的公告 |
| 300358 | 2014/05/26 09:30 | 2014-08-22 | 关于股票复牌公告 |
| 300431 | 2015/10/27 09:30 | 2016-03-28 | 关于公司股票复牌的提示性公告 |

The resulting authority has 7,358 exact resumptions, 58 terminal closures,
zero conflicts and 3,389 unresolved SZSE boundaries. SSE remains 16,393/0
unresolved. Suspension authority remains
`PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`.

## Reproducibility

- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v14.json`
- retained replay file SHA-256:
  `8120e4aa1fd2e8ab8f38918b02a905b0940c6f7a0aa8527a65fa0c18e6b63b96`
- retained replay canonical manifest:
  `e10c83d28490fcdf5667f6194073cf603f9e5bba4ace41d0f6e824f7ef25277f`
- resumption parser SHA-256:
  `564cacf6e8f82bf11a1abfe9f2432390b5378c469e4aeb087e3335e80d693f57`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v18/suspension-authority-v1.json`
- full authority file SHA-256:
  `ddf220fb36c994442f18823c1d59b82c44f86f9eeace5549690670ae2bcb0a1d`
- full authority canonical manifest:
  `bca494a388931c20da5058699451a7f29f6f0a646aaaf750dbc99f7fc16eaa49`
- normalized events SHA-256:
  `f8871aa0fe41b0c78a29ce36746919a85542b7dc78cbfa906ac757412f6a64b2`
- unresolved facts SHA-256:
  `9d8fa726d15d4822cb8d07d59ce77785a46b3329984bb5398f69e0343889fcee`
- input-order reproducibility: PASS
- source checksum repeatability: PASS
- focused parser tests: 6 passed

Documents with two anchored official dates remain ambiguous and unaccepted.
No Full Dataset was created, audited or frozen. Development, Validation and
Official OOS remain unrun and locked. PR #12 remains open and unmerged. The
independent retained-bonus fractional methodology gate is unchanged.
