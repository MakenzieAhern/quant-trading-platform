# R5 full adjustment retained-source recovery v1 — 2026-09-19

This audit continues from the 1,416 retained factor-change dates that had no
exact bonus-oracle date. It searches existing official CNINFO implementation
metadata in a bounded 60-day pre-event window, reuses retained source bytes,
and parses candidate terms without accepting a CorporateAction event.

## Coverage

- factor changes with CNINFO metadata candidates: **1,383**
- factor changes without a retained candidate: **33**
- candidate official documents: **1,421**
- retained checksum-bound official documents: **1,421**
- missing documents / new downloads: **0 / 0**
- unique exact official term candidates: **1,311**
- no exact official term candidate: **72**

Document parsing classifies 1,312 exact-date term candidates, 12 exact-date
documents without supported terms, 25 non-unique or mismatched dates, 70
non-final documents and two retained byte objects that are not parseable PDFs.
The exact candidates contain 817 cash-only, 463 cash-plus-bonus and 32
bonus-only term shapes. Multiple documents collapse by exact term signature;
they are not counted as multiple economic events.

## Economic diagnostic

All 463 combined gross-cash-plus-bonus candidates have an official SZSE raw
pre-close. Applying the accepted gross formula to the retained factor step
produces 463 conflicts. The checked dates span 2010–2014. This does not prove
the official issuer terms wrong: gross shareholder cash must not be replaced
by an unevidenced historical tax-net or provider-specific cash basis merely to
fit a factor. It instead keeps factor economics and provider convention
explicitly unresolved.

Correction precedence, stable lifecycle admission, actual registry allocation
and the retained-bonus fractional-share policy remain separate gates. No
candidate is added to the accepted corporate-action ledger, adjustment
authority remains **PARTIAL**, and no dataset or strategy is run.

## Immutable reports

- candidate routing:
  `/home/yuchen/data/research/staging/full-adjustment-audit-v1/unrouted-implementation-candidates-v1.json`
  - file SHA-256: `6858d17794abed8608992690f49845e498a67ea5171e7f4c8cbfbdaaa95c6b7e`
  - manifest SHA-256: `b7dac748c4c0228e1c1d233efe3767555e5f251e598508b914f9c6280ee2d678`
- retained-source inventory:
  `/home/yuchen/data/research/staging/full-adjustment-audit-v1/retained-candidate-source-report-v1.json`
  - file SHA-256: `5a5c168b9476f90c35c2a6a5607d1e0d64044392ef81dc564717ebe7889d2124`
  - manifest SHA-256: `db7a9ac94d423fc3542c2a999f2178c3b03a122c2d6f2bbc7ef0856bc3776cf4`
- official term candidates:
  `/home/yuchen/data/research/staging/full-adjustment-audit-v1/official-terms-candidates-v1.json`
  - file SHA-256: `238101790c49d795f0817de96d37388dfa9775238842e9ac8ee3fd1033ad369d`
  - manifest SHA-256: `0af35ecddac88311712ce7fbb67a24ee40393f78298ed0c676ac3dbb494b437e`
- gross-term factor diagnostic:
  `/home/yuchen/data/research/staging/full-adjustment-audit-v1/factor-economics-v2.json`
  - file SHA-256: `eca085f01fca7937c6e2791c985fa12674e4d1d560f585ebeee00322e3931f97`
  - manifest SHA-256: `ba1f7b04b9f27ce01e76599441ed1616846b2c702ab99021b3c7a1dd96d86b8a`

Input-order reproducibility passes for candidate routing, retained-source
inventory and term parsing. The factor diagnostic also reproduces under
reversed factor and term ordering.
