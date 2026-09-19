# R5 SZSE residual regulatory-review screen v20 — 2026-09-19

The corrected v19 residual was screened once more against the retained official
CNINFO metadata. A bounded title family matching `审核通过`, `审核结果` or
`重组委` selected 26 documents from 72,624 unprocessed leads. Titles were routing
clues only and were not treated as resumption facts.

All 26 official attachments were acquired without failure: 24 PDFs and two
official non-PDF attachments. Full retained-byte replay found no new, removed or
changed accepted resumption boundary. The documents are predominantly securities-
issuance review outcomes and do not state a unique final trading-resumption date
for the corresponding unresolved episode.

## Result

- bounded official documents acquired: 26
- PDF attachments: 24
- official non-PDF attachments: 2
- acquisition failures: 0
- new exact boundaries: 0
- prior accepted boundaries lost or changed: 0
- exact resumptions: 8,718
- terminal closures: 58
- unresolved SZSE boundaries: 2,029
- conflicts: 0

The regulatory-review title family is exhausted for the current residual. The
remaining 72,598 generic leads are not a justified blind acquisition queue.

## Reproducibility

- priority report:
  `/home/yuchen/data/research/staging/full-szse-resumption-v11-review-v1/priority-report-v1.json`
- priority report file SHA-256:
  `7c0636a83b43915ce683c847c493f8fe55460bdfbf157f1cfe8d9c7c606de3be`
- priority report canonical manifest:
  `0ab86b632ace8b84c7278040f982698a31e2869f064c0f8e33de70ee78e2addf`
- selected queue SHA-256:
  `36a6a7fa1e3ba79e31e28f66830c4212357248dd0af0372463500ed49ba5cc54`
- source manifest file SHA-256:
  `bfba398e7c0820306931eb8ecc38479778375284922c12432fa8f0fad67e65d9`
- source manifest canonical manifest:
  `0e83bda12629dff4d1db9a2810074e6e8ed89fc214059613c0d3324f5ef0a41f`
- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v24.json`
- retained replay file SHA-256:
  `17244e2dde48139705422c515da2493fd6bdb65bd95b83a5e618458eae41346c`
- retained replay canonical manifest:
  `a4e4eee20cebd850502ecd2863ed833c6f8d8cfff940bbb6a60c1288888aea73`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v23/suspension-authority-v1.json`
- full authority file SHA-256:
  `8628a5dac3a659d0d8deb3c5ed1229fa8aeba29865c0371f396491dd14913699`
- full authority canonical manifest:
  `897f9d17faecee625a64892f533dc6d734ddbcce870aad412ff8cf065d6e616d`
- normalized events SHA-256:
  `7612f2a308c53057720043ebe94bf1aa06c6f65a55a801fadcd12450cc58433e`
- unresolved facts SHA-256:
  `efbe7c908a511f4b93cc54b0dd7b80081fc56f4cb78f41bc5eeb98940766ef7d`
- input-order reproducibility: PASS
- source checksum repeatability: PASS

Suspension authority remains `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`. No Full
Dataset was created, audited or frozen. Development, Validation and Official OOS
remain unrun and locked. PR #12 remains open and unmerged. The independent
retained-bonus fractional methodology gate is unchanged.
