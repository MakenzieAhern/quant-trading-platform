# R5 SZSE media-clarification recovery v21 — 2026-09-19

The v20 residual metadata was screened for three bounded official-document
families that can plausibly carry a final trading boundary without naming
`复牌` in the title:

- one acquisition-implementation completion notice;
- six acquisition-asset transfer completion notices;
- thirty media-report, market-rumour, investor-concern or media-question
  clarification notices.

Titles were routing clues only. All 37 official CNINFO attachments were
retrieved and replayed from checksum-bound bytes: 36 PDFs and one official
non-PDF attachment. The first two families produced no exact resumption. The
media-clarification family produced eight exact final boundaries:

| Security | Suspended at | Exact resumption | Official evidence |
|---|---|---|---|
| 000150 | 2014/07/16 09:30 | 2014-08-25 | 关于市场传闻核实情况的说明 |
| 000661 | 2014/05/14 09:30 | 2014-05-19 | 关于媒体报道情况的自查公告 |
| 000712 | 2010/06/11 09:30 | 2010-06-17 | 关于媒体报道核实情况的公告 |
| 002321 | 2012/03/20 即时 | 2012-03-27 | 关于媒体质疑情况说明的公告 |
| 300052 | 2013/09/12 09:30 | 2013-09-13 | 关于媒体报道及自查公告 |
| 300058 | 2014/11/20 13:00 | 2014-11-21 | 关于海外媒体报道相关事项的说明公告 |
| 300221 | 2014/03/25 09:30 | 2014-03-25 | 关于媒体报道公司即将获得3D打印资助的说明公告 |
| 300251 | 2013/03/04 09:30 | 2013-03-05 | 关于媒体报道“人在囧途”状告“泰囧”的公告 |

The first media acquisition attempt preserved 21 DNS-failure receipts when the
local resolver could not resolve `static.cninfo.com.cn`. A fresh bounded batch
used the independently resolved official CDN address while retaining the
original HTTPS host and official URLs. It then retrieved all 30 documents with
zero failures. No source was substituted.

## Result

- official documents acquired: 37
- PDF attachments: 36
- official non-PDF attachments: 1
- final acquisition failures: 0
- new exact boundaries: 8
- prior accepted boundaries lost or changed: 0
- exact resumptions: 8,726
- terminal closures: 58
- unresolved SZSE boundaries: 2,021
- conflicts: 0

## Reproducibility

- implementation-completion priority report file SHA-256:
  `bc1d1a9b27d5aa853de029751d365f68dd049fc0ffda9bc9c6cd6775b2ec6be0`
- implementation-completion source manifest file SHA-256:
  `946f5b82754875a39e5457d688b042e0fff9f2979c57b0485f95ae5d864a1464`
- asset-transfer priority report file SHA-256:
  `3056492cb459019cf627d712628e39e9084e5297e04b9a32498319ff466a91ad`
- asset-transfer source manifest file SHA-256:
  `f8e5549e0a27c626f47888994f2fa85173fc17ace6f7a1d4d5054793d0de9e11`
- media-clarification priority report file SHA-256:
  `4ec60f7f69ea28455488e3e998c1794e799dba3669ba54e5e7be2d2c849e22cc`
- media-clarification source manifest file SHA-256:
  `e1241410ed635ee4185cf0177d36b727c04cf5c0c454708f66c623cba0464e84`
- media-clarification source canonical manifest:
  `0c240b69f0cce3e5fe90656dd0ff3ce9abeffc2be2bc57e3f72461e61a7c31b7`
- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v27.json`
- retained replay file SHA-256:
  `5574d4fdb702df01fad5289f354e107410e9468b4dcd3c9dc167c63712a3c1f8`
- retained replay canonical manifest:
  `0880c7081621c1bb3605ff01b55138b4c8ce6264aea38b81fccfa9311ea900b8`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v24/suspension-authority-v1.json`
- full authority file SHA-256:
  `51f41a565a307be61e925cd329669476ec4909bbf89c1d761615bdb575600bd5`
- full authority canonical manifest:
  `d4d51d1aca7460a6e599dddc4673cc8d18fcd12e4874a345bb017293925aac3d`
- normalized events SHA-256:
  `65773a73696b40f994c344e3c89a77953363cf51c3cafcee9284843eb145a765`
- unresolved facts SHA-256:
  `44b91a4d5f782970d8a0d68501a1eea2ba198b682e24b643d640d8ba6085d1fb`
- input-order reproducibility: PASS
- source checksum repeatability: PASS

Suspension authority remains `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`. No Full
Dataset was created, audited or frozen. Development, Validation and Official OOS
remain unrun and locked. PR #12 remains open and unmerged. The independent
retained-bonus fractional methodology gate is unchanged.
