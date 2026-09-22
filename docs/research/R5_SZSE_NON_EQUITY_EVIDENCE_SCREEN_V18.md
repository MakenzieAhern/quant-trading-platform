# R5 SZSE non-equity evidence screen v18 — 2026-09-19

The retained resumption corpus included bond-only notices whose titles identify
a corporate bond or convertible instrument without naming stock or A-share
trading. The earlier filter recognized the literal word `债券` but missed forms
such as `14雏鹰债复牌` and `中装转2复牌及恢复转股`.

The shared classifier now recognizes those bounded instrument-title forms. It
does not reject combined stock/convertible notices naming `股票` or `A股`, and
it does not treat generic words such as `债务` or `基金` as securities.

## Result

All retained official source manifests were replayed with no downloads:

- 16 document occurrences move to `NON_EQUITY` (89 to 105);
- ambiguous document occurrences fall from five to three;
- exact-date document occurrences fall from 9,363 to 9,356;
- accepted equity boundaries remain 8,716;
- unresolved SZSE boundaries remain 2,031;
- conflicts remain zero.

The accepted 002477 boundary on 2018-09-13 no longer cites the bond-only
`14雏鹰债` notice. The same date remains supported by the separate official
equity notice `关于继续推进发行股份购买资产事项暨股票复牌的公告`, source SHA-256
`5a8798dcd620d772097dbfde3b3c87cc660b32feb598b69d547039326c214f5b`.

## Reproducibility

- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v22.json`
- retained replay file SHA-256:
  `6fd1d637280e6f162b653c018493ba9670c09c9a0581c039d181c22ada99eef2`
- retained replay canonical manifest:
  `9a9d85ff7f60ed0b244d014486b7fa8ee70bce5418b1e6d9e4eabe3a85c2a298`
- resumption parser SHA-256:
  `cb97febf0e80a74a3e582dcade6966c81dacc9a8e404c3bffca670cd24f8b0a6`
- revalidation parser SHA-256:
  `f7c318f352b592eff571a12fc29ba95c285be475f5f12c5b2b1557df086d9acf`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v21/suspension-authority-v1.json`
- full authority file SHA-256:
  `68f8eec279613107091982b979412099e099a56cc2fb28a4b86a90b9debd4ce2`
- full authority canonical manifest:
  `eef82d4716b2f5924609311c02d04530040a8d7d8553cd91d3df78664d11df87`
- normalized events SHA-256:
  `628f52d78a74e6430ad14380e9f51f42cf2fbd8e63170a58bd3a504629e5492f`
- unresolved facts SHA-256:
  `fc067aa1cf27d798fc8dc8aa26f9fd7bce582388dd845468c16fee651253542a`
- input-order reproducibility: PASS
- source checksum repeatability: PASS
- focused parser tests: 7 passed

Suspension authority remains `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`. No Full
Dataset was created, audited or frozen. Development, Validation and Official
OOS remain unrun and locked. PR #12 remains open and unmerged. The independent
retained-bonus fractional methodology gate is unchanged.
