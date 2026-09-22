# R5 SZSE delisting-consolidation recovery v13

Date: 2026-09-19

## Result

A bounded exact-title screen selected 31 previously unprocessed official
CNINFO notices containing `进入退市整理期`. All 31 PDFs were acquired with zero
failures and checksum-bound to their unresolved suspension events.

The notices use the deterministic form
`进入退市整理期（交易）的起始日为 YYYY 年 MM 月 DD 日`. The shared strict
resumption parser did not previously recognize that form even though it is an
effective trading boundary. One narrow parser pattern now covers the observed
official wording; no generic listing, implementation or expected date is
accepted.

All 31 notices contain one exact date, and all 31 bind to the preceding
unresolved halt before any later suspension. Authority therefore moves from
7,303 to **7,334** exact SZSE resumptions. With 58 terminal closures retained,
unresolved SZSE boundaries fall from 3,444 to **3,413**. Conflicts remain zero.

## Controls

- focused parser tests: 6 passed
- Ruff: PASS
- format check: PASS
- reconciliation input-order reproducibility: PASS
- forward/reverse authority replay: byte-identical PASS
- Full Dataset created/frozen: NO
- Development/Validation/Official OOS: NOT RUN

## Immutable evidence

- priority queue SHA-256:
  `9cdff48f783d017b86d66f9ed667f1791155941bd48f0043d57f56e5456ba9e0`
- priority report file SHA-256:
  `65d50fd2ae57c35d4be9a255194ef7b6bd72b992e3401def87ac900426bc7175`
- priority report manifest:
  `b28ee82e0430e50fe8bf346b0860ffa5eab78adf5ec91f1e0ad066e227a0f2d1`
- source manifest file SHA-256:
  `067836498bec52b1938a983551c4ba973e130d06325d7aeccdfa9b66dc244226`
- source manifest:
  `37e1929c9de0d124ba7727b5112d9e734b081bdb48cda2a1249c061c42632818`
- reconciliation file:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-delisting-consolidation-reconciliation-v15.json`
- reconciliation file SHA-256:
  `42e165ba85a6871ce646abefb1a6af8a4a164caeeb71044d9539d01d71207215`
- reconciliation manifest:
  `3cb8f735aaeb2e3585e1649b473d9b7119aab6b981b2ee95cf1811b11655561c`
- parser SHA-256:
  `c08794df73867291f64297664eabc2c7e007b113efe6aaf78bfd59160720275e`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v15/suspension-authority-v1.json`
- authority file SHA-256:
  `1f1dcdda6743fd07316d977c9a0cf5e05de9be9fa97a54c64ae7fe17409472a8`
- authority manifest:
  `9c2815c049d54f20f73eb163edab9566ee95f8b84feb40da6daa77f437d26a91`
- normalized events SHA-256:
  `622758188597809cc47cb3deda231af90aa80fee64704e7e3c9c4e50ead82485`
- unresolved facts SHA-256:
  `876559e641e4dff761d93869dffdc96776f5fcfee9dda77346030c9a4f610af0`

Suspension authority remains `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`; the
bounded title family does not justify broad low-precision retrieval.
