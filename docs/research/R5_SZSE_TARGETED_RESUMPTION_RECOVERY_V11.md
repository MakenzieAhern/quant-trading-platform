# R5 SZSE targeted resumption recovery v11

## Result

The strict v10 residual was joined to all 13,515 retained official CNINFO
metadata pages. A first pass reused 2,292 already-retained source documents;
four bounded title families then acquired 380 additional official documents
with zero failures. Titles routed acquisition only. Every accepted boundary
still required one unambiguous effective date in the retained official bytes.

Ten true boundaries close: seven from the retained-byte pass, two from formal
2011 rights-issue timetables, and 002322's explicit 2015-03-16 13:00
resumption. The 95-document regulatory-review family produced no residual
boundary; the 262-document official inquiry/reply family produced only 002322.

## Continued-halt correction

000520 exposed a separate restoration/trading distinction. An earlier notice
stated a 2015-08-18 restoration of listing, while a later official notice said
the stock would remain suspended that same day for another matter. The shared
parser now records a continued-halt veto and applies publication-order
precedence across official documents. A later explicit resumption can override
the veto; an earlier restoration decision cannot. 000520 therefore remains
unresolved rather than becoming a false trading resumption.

## Deterministic replay

- strict exact resumptions: **7,303**
- official terminal closures: **58**
- unresolved SZSE boundaries: **3,444**
- conflicts: **0**
- SSE unresolved facts: **0**
- forward/reverse supplement replay: **byte-identical PASS**

Current residual routing has 74,569 unprocessed low-precision document leads:
1,923 unresolved facts have at least one remaining metadata candidate and
1,521 have no remaining unprocessed candidate in the retained metadata. The
high-yield explicit-resumption, clarification, abnormal-volatility,
major-matter, review-result and inquiry/reply families are exhausted for this
residual. Generic board/shareholder-resolution acquisition remains deferred;
its volume and observed precision do not justify blind bulk retrieval.

## Immutable evidence

- revalidation report:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v11.json`
- report file SHA-256:
  `21f53a091fdfee81377adefc22eeccc668dd592646398321be9c7a3694c7f909`
- report manifest:
  `b250b207360d0721cd820ff591e70910a2c9c83a7d53ced52ccf362d5743732f`
- full authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v13/suspension-authority-v1.json`
- authority file SHA-256:
  `d4941cf890010c6014b6e8277a83d95ad802ab5275a621719846346b8dba55e9`
- authority manifest:
  `6051aab6be1fba90c901a326285f76f92516f4f9359f82a6404be6c37fe0d704`
- normalized events SHA-256:
  `e54b749fafd5cd8dcb586e08919e0bd559e420d32a60b04c9b46d09b3cb40cfb`
- unresolved facts SHA-256:
  `15338bc218060235bff56feb571b0706d32392eea6c75266c57ac7ae194bc1e0`
- residual gap report:
  `/home/yuchen/data/research/staging/full-szse-resumption-v10/gap-queue-report-v4.json`
- gap report file SHA-256:
  `7bd1b5fa96ef7ee831db450700d1fb159d1bf4d89d0d42143d65389c85cd354e`
- gap report manifest:
  `a3bb494442a67e528d8dffd45355c779f78ba005d9697966869076bcf3337561`

Suspension authority remains `PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`. No Full
Dataset, freeze, profitability inspection or study was run.
