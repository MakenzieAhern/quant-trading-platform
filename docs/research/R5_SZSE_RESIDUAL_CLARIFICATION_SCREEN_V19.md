# R5 SZSE residual clarification screen v19 — 2026-09-19

The v18 residual was rejoined to all 13,515 retained official CNINFO metadata
pages after the strict parser corrections. Of 2,031 unresolved suspension
facts, 1,778 have at least one unprocessed metadata lead and 253 have none.
Those leads comprise 72,624 documents, overwhelmingly generic reports,
opinions and meeting records; titles remain routing clues, not event facts.

A bounded four-document clarification/nuclear-result title screen was selected
from the new residual. All four official CNINFO PDFs were acquired successfully
and parsed from checksum-bound bytes. Two state one exact final boundary:

| Symbol | Suspended at | Exact resumption | Official evidence |
|---|---|---|---|
| 000030 | 2011/09/22 09:30 | 2011-09-26 | 相关事项核查结果公告 |
| 000541 | 2010/08/24 09:30 | 2010-09-16 | 关于深交所关注函核查结果的公告 |

000037 and 000534 do not state an admissible exact boundary and remain
unresolved. No title or publication date was promoted as a fact.

## Result

- official PDFs acquired: 4
- acquisition failures: 0
- new exact boundaries: 2
- prior accepted boundaries lost or changed: 0
- exact resumptions: 8,718
- terminal closures: 58
- unresolved SZSE boundaries: 2,029
- conflicts: 0

The full 72,620-document remainder is not a justified acquisition queue. The
high-precision clarification family is now exhausted for the current residual;
generic board, meeting, annual-report and legal-opinion titles remain deferred
unless a fact-specific evidence gap identifies them.

## Reproducibility

- residual gap report:
  `/home/yuchen/data/research/staging/full-szse-resumption-v11-gap-v1/gap-queue-report-v1.json`
- residual gap report file SHA-256:
  `97db7b0d2b26ae772d2370913f35ac6819ee1cc4d65ef614ae1905c3feccea74`
- residual gap canonical manifest:
  `a7bd3a2ac62e26ab80b113ba5f1f1efe0729dad04215f7280b8618d5e06d1635`
- priority report file SHA-256:
  `5e6d82c0a168e63872904b1b36d20cfbccc2bfd0728076b618ffc8178c184668`
- priority report canonical manifest:
  `abd5943c3e6253d5a0e7f1049199b165c35496785ab6f2728781a782dfb64e05`
- source manifest file SHA-256:
  `72cf4ceb4fb63a9e875223af644ea6c21e8e1b016a774ed6282e9a7aaca87d5a`
- source manifest canonical manifest:
  `812eb9a5e3050956bd98dac70a049a492836fad673ac5c1c45a79fa31d6d1b69`
- retained replay:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v23.json`
- retained replay file SHA-256:
  `3ee4ef60677996aa6c4c867efa04c83f86aaf5ddaaf9cb01f3b25b0e24afd9cd`
- retained replay canonical manifest:
  `844be767dd4a886c76e4554793fc3ca3dbb5345790b5b9b8497ba7bd728c7423`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v22/suspension-authority-v1.json`
- full authority file SHA-256:
  `1148be5da6f6e18b719b9253685ebc5d76fa135a71af5ae1f6e4fa6b61b4ec94`
- full authority canonical manifest:
  `b51fc1be5ecb50e294017a01eb4a38152ea6e8cb158c7b894355075497626280`
- normalized events SHA-256:
  `7612f2a308c53057720043ebe94bf1aa06c6f65a55a801fadcd12450cc58433e`
- unresolved facts SHA-256:
  `efbe7c908a511f4b93cc54b0dd7b80081fc56f4cb78f41bc5eeb98940766ef7d`
- input-order reproducibility: PASS
- source checksum repeatability: PASS
- focused parser tests: 7 passed

Suspension authority remains `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`. No Full
Dataset was created, audited or frozen. Development, Validation and Official
OOS remain unrun and locked. PR #12 remains open and unmerged. The independent
retained-bonus fractional methodology gate is unchanged.
