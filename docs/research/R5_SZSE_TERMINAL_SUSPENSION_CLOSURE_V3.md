# R5 SZSE terminal-suspension closure v3

Status: **5 ADDITIONAL SOURCE-BOUND TERMINAL CLOSURES ACCEPTED; 53 CUMULATIVE; AUTHORITY REMAINS PARTIAL**.

The v3 pass applies the v2 exact-event rule across every retained SZSE
resumption source manifest that carries immutable `affected_suspensions`
bindings. Repeated acquisitions of identical official bytes are merged by
SHA-256: their event bindings are unioned and the earliest UTC retrieval
timestamp is retained, while conflicting issuer, publication, title, URL or
text metadata still fail closed.

The 9,626-document scan closes five merger-related terminal suspensions for
000024, 000522, 000527, 000562 and 300186. Each official issuer notice says
that trading remains suspended through termination for a share-exchange
merger, binds the exact suspension event, and is paired with the accepted
official-master lifecycle end. No `resumed_at` value is created.

Results:

- retained bound official documents scanned: **9,626**
- incremental terminal closures: **5**
- cumulative terminal closures: **53**
- true official resumption supplements: **8,884**
- SZSE target suspension events: **22,077**
- prior unresolved exact boundaries: **1,873**
- current unresolved exact boundaries: **1,868**
- resumption conflicts: **0**
- SSE target events / unresolved: **16,393 / 0**
- input-order reproducibility: **PASS**

Immutable v3 report:

- path: `/home/yuchen/data/research/staging/full-szse-terminal-suspension-v1/szse-terminal-suspension-closures-v3.json`
- file SHA-256: `70cb97e0e27ef67d29cb308c02371649e736dc1507ab09120e5b5552e0919d10`
- canonical manifest SHA-256: `f3ccdfcb9b53e83b1e688a7d8174c3874a5b68c6551a8e238b449b76151e9d72`

Full replay:

- authority file SHA-256: `8d345bf6c12f151b02c5605eebd5be2bda1cdb5dcd02673c44867fc2ecd0b756`
- authority manifest SHA-256: `0583bb29a1e7963f6f2fc247e096ba6486778d8a5338f8f1f4fad9ca5a0aecf7`
- normalized-event file SHA-256: `0a1df1519bc8fe02d24d85da404e949aeb20088270735d2303cb149f1730134e`
- unresolved file SHA-256: `e8f9cb20993b6bb091bf65cdf74fce6d427a26e2d392813d4f7672abc8710df9`

This exhausts the retained official document manifests with exact suspension
bindings for this terminal-treatment rule. It does not make suspension
authority complete. The remaining 1,868 exact SZSE boundaries need targeted
official evidence; 239 ChiNext raw-source dates, P1 corporate-action gaps and
the retained-bonus fractional-accounting gate also remain open. No dataset,
freeze or strategy study was produced.
