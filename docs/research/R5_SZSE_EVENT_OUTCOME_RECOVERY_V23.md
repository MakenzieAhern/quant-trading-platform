# R5 SZSE event-outcome recovery v23 — 2026-09-19

Six bounded official CNINFO title families were screened against the v22
residual. Titles remained routing clues only; exact dates were accepted only
from checksum-bound official attachment text.

| Family | Official PDFs | Exact boundaries |
|---|---:|---:|
| production restoration | 5 | 1 |
| reorganization regulatory approval | 9 | 3 |
| issuance review outcome | 2 | 1 |
| tender-offer result | 4 | 2 |
| adverse reorganization decision | 1 | 0 |
| reorganization termination | 2 | 0 |

All 23 PDFs were retrieved with zero failures. Seven exact boundaries were
added; no prior accepted boundary was lost or changed.

| Security | Suspended at | Exact resumption | Official evidence |
|---|---|---|---|
| 000007 | 2011/01/10 09:30 | 2011-01-11 | 董事会关于非公开发行A股股票申请获得有条件通过的公告 |
| 000656 | 2011/05/26 09:30 | 2011-05-30 | 关于公司新增股份吸收合并重庆市金科实业（集团）有限公司及重庆市金科投资有限公司及一致行动人申请豁免要约收购事宜获得中国证监会核准的公告 |
| 002276 | 2011/06/09 09:30 | 2011-07-01 | 关于公司恢复生产的公告 |
| 000501 | 2012/07/23 09:30 | 2012-07-25 | 武汉商联（集团）股份有限公司及其一致行动人部分要约收购公司股份的结果公告 |
| 000903 | 2012/12/31 09:30 | 2013-01-04 | 关于云南内燃机厂部分要约收购公司股份的结果公告 |
| 300004 | 2014/05/23 09:30 | 2014-05-23 | 关于发行股份及支付现金购买资产并募集配套资金事项获得中国证券监督管理委员会正式批复的公告 |
| 000935 | 2014/07/03 09:30 | 2014-07-10 | 发行股份购买资产暨关联交易方案获有条件通过的公告 |

## Result

- official PDFs acquired: 23
- acquisition failures: 0
- new exact boundaries: 7
- prior accepted boundaries lost or changed: 0
- exact resumptions: 8,735
- terminal closures: 58
- unresolved SZSE boundaries: 2,012
- conflicts: 0

## Reproducibility

- production source manifest file SHA-256:
  `55583b1fddb49c7ae6f91370c12b58f6b348e7ec05800fc518c36844482d0b31`
- regulatory-approval source manifest file SHA-256:
  `9d68094a4261c73fdd54fe7cd192943a4711a1e03016eacaca1eb578074427d7`
- issuance-review source manifest file SHA-256:
  `3f8aa98b636ba6ff7309056db4163112b43d873265adff43a3efd08679d48be7`
- tender-offer source manifest file SHA-256:
  `d69bf92b8fbce46bc06ce7f806638adc98b0d44629a5a1b56305788d28395b3f`
- adverse-decision source manifest file SHA-256:
  `91f14ad6f805692a597ad191f3ca16890cc09367168eb25155d26071da858a52`
- reorganization-termination source manifest file SHA-256:
  `c487478a84718edc8864c06d8b4e2f860e2293fc520cc1935fc954f9fb12555a`
- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v35.json`
- retained replay file SHA-256:
  `2231d56758fb9a4233a2923557b0df39f15bd26e853baa8c49aff514f9b2d818`
- retained replay canonical manifest:
  `48dd41edbfb471f37ff48b24231ea6c3cd45bae3097498340cacbf94af568cdd`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v30/suspension-authority-v1.json`
- full authority file SHA-256:
  `7747153498adb5651c802278808a2eb8c7df17e8e4d7f144c4faec5e348741d3`
- full authority canonical manifest:
  `316914aa9658f05133d32015b70b1fdb8948e50b4a1d4f53d36829f269e79c05`
- normalized events SHA-256:
  `23a1501277009fe7eeffcf90ccaf6eeeffb874255e2bdce18cf993363ddf1b15`
- unresolved facts SHA-256:
  `750ba34b72308bc1acde3d549444e9ae8d0fc20a9e63f27bb30e56f3578b640e`
- input-order reproducibility: PASS
- source checksum repeatability: PASS

The high-information production, final regulatory-outcome, tender-offer and
reorganization-termination title routes are exhausted for this residual.
Remaining generic or routine metadata leads do not justify blind retrieval.
Suspension authority remains `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`.

No Full Dataset was created, audited or frozen. Development, Validation and
Official OOS remain unrun and locked. PR #12 remains open and unmerged. The
independent retained-bonus fractional methodology gate is unchanged.
