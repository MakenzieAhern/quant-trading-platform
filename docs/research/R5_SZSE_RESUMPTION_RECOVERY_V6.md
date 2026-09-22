# R5 SZSE targeted resumption recovery v6

Status: **21 TRUE RESUMPTIONS AND 5 TERMINAL CLOSURES ACCEPTED; AUTHORITY REMAINS PARTIAL**.

The v6 pass reuses 13,515 retained official CNINFO metadata pages and the
current exact suspension intervals. The initial metadata join produced 75,579
unprocessed interval documents, so titles were used only to route a bounded
150-document `复牌 / 恢复交易 / 终止上市` batch. All 150 official PDFs were
retrieved with zero failures and page-addressable SHA-bound text extraction.

Exact-text parsing accepted 13 true resumption boundaries, all stated in
official termination-decision notices as the start of delisting-consolidation
trading. The remaining documents were not promoted from their titles. A
separate terminal replay accepted five no-consolidation closures for 000627,
000666, 000732, 002619 and 002740.

A second 126-document restoration-title batch was acquired with zero failures.
Those new documents were progress, application or historical reports and did
not independently close a current fact. They exposed a parser coverage gap in
already retained official material: `恢复上市` effective trading boundaries
were distinct from ordinary `复牌`. Parser v5 now accepts only full-date forms
that explicitly place the stock back into listed trading; application,
acceptance, progress, supervision, suspension and aspirational contexts are
rejected. Replay of the retained v5 official source manifest accepted eight
restoration boundaries: 000751, 002506, 000155, 000629, 000950, 000995,
000670 and 000792.

Final replay:

- SSE target events / unresolved: **16,393 / 0**
- SZSE target events: **22,077**
- true official resumption supplements: **8,905**
- official terminal closures: **58**
- current unresolved exact boundaries: **1,842**
- resumption conflicts: **0**
- input-order reproducibility: **PASS**

Immutable evidence:

- v6 exact-resumption report file SHA-256: `2dfca245d8217749a58369bf4fad6fd76664db40a6271533b9d89445ad0c86b3`
- v6 exact-resumption manifest: `1a8a13277927360b16631fb01ac0a0ce056dbd5f9f30665aa07b6805e2279a13`
- terminal v4 report file SHA-256: `2d2a88351a33beb2ddd27bd2a140ab0ccbef0a18263d4e5510f0166a65684de4`
- terminal v4 manifest: `ac4c9e2bcb6cbe9e6298aa6b24e31181d43d03f9d25fb40d191ca78f432c69e8`
- restoration v5 report file SHA-256: `1df8836684569f26b66376f9ee57025bfaaf0d385e61308f70d7c576374c9bbc`
- restoration v5 manifest: `496594445b9d84dc89bb925a1c9c884b93333a69487573c6f0a5bf165d364152`
- full authority file SHA-256: `08e3f7b13a5dad822ac5dfb25bff8a7c28fbe6e3edf91742719d4c2b75ef734a`
- full authority manifest: `9d1a6e9101d5ebdf95ac0511b8745d0dc2802aaa22f92f53e6fc96a4a218dcbe`
- normalized-event file SHA-256: `75cf706a06155018cd635c36b10d2d36dd185b6daf360014ef7909dacc4c2912`
- unresolved file SHA-256: `39822927043a59bb307155c9b51885ef58f20a0d3a02375bf6c8090b0044047d`

The residual metadata queue contains official leads for 1,690 of the 1,850
pre-restoration residual facts and no retained candidate for 160; titles remain
routing evidence only. Suspension authority is still PARTIAL. No Full Dataset,
freeze or strategy study was produced.
