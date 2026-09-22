# R5 SZSE terminal-suspension closure v2

Status: **6 ADDITIONAL SOURCE-BOUND TERMINAL CLOSURES ACCEPTED; 48 CUMULATIVE; AUTHORITY REMAINS PARTIAL**.

The v2 pass reuses the retained official CNINFO corpus and the existing
source-manifest suspension bindings. It removes the v1 nearest-halt heuristic:
an official document can close only the exact `(security_id, suspended_at)`
event already named in its immutable `affected_suspensions` field. The same
document must explicitly say either that no delisting-consolidation period
will occur or that suspension continues through termination, and the accepted
official master must supply one matching terminal lifecycle date.

No `resumed_at` value is created. These remain
`OFFICIAL_TERMINATION_NO_DELISTING_PERIOD` records with a separate
`terminal_at` boundary.

Results:

- retained official documents scanned: **4,598**
- incremental terminal closures: **6**
- cumulative terminal closures: **48**
- true official resumption supplements: **8,884**
- SZSE target suspension events: **22,077**
- prior unresolved exact boundaries: **1,879**
- current unresolved exact boundaries: **1,873**
- resumption conflicts: **0**
- SSE target events / unresolved: **16,393 / 0**
- input-order reproducibility: **PASS**

The six incremental securities are 000418, 000671, 000748, 000780, 000916
and 002013. Every accepted row preserves the official PDF URL, source SHA-256,
publication and retrieval metadata, exact suspension binding and official
master evidence.

Immutable v2 report:

- path: `/home/yuchen/data/research/staging/full-szse-terminal-suspension-v1/szse-terminal-suspension-closures-v2.json`
- file SHA-256: `ea331011b4dc6f59314560cf9b9ce7ca0e2d90d1eb7fe41cd71cd3e35afcf449`
- canonical manifest SHA-256: `0c4a55c663cac28b9457c5aec0a403d840f222baf8628b6c812b84399da8e573`

Full replay:

- authority file SHA-256: `ffdef25e58fe8fb42b55a6385e513ec171edd21adb27ad9f30f71a6e93a6cd90`
- authority manifest SHA-256: `8bc8cdd204f3a3be96eee8c92ebf8d4dc2e37e0368ed11d5bfdd848ac78e7cb9`
- normalized-event file SHA-256: `8753d86bb64e8526847ffdd8f038104e59de0132a74fc61d0595472d6a7d12b3`
- unresolved file SHA-256: `803574b7f7f76a08131aadf57be97aa6ac93e5c1512c38537f22480cb928344b`

This is deterministic source closure, not a Full Dataset PASS. The remaining
1,873 exact SZSE boundaries, 239 ChiNext raw-source dates, P1 corporate-action
gaps and retained-bonus fractional-accounting gate remain open. No dataset,
freeze or strategy study was produced.
