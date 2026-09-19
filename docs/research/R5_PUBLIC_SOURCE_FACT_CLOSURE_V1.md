# R5 official public-source fact closure V1

The retained official corpus closes two more merger facts without a commercial
product or a new economic event. `MERGER:000578:000792` is supported by the
official additional-share, conversion, registry and listing chain;
`MERGER_NEW:600253:600056` is supported by the official last-trade,
termination, conversion, registration and listing chain. Both reuse the
approved `CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1` research convention.

P1 cumulative V65 now establishes **16,313 / 16,320** facts, including **2,031**
explicit official-source substitutions. Seven facts in seven documents remain:

- three cash notices: 301262 has an internally malformed contemporaneous
  ex-date; 601607 and 603408 have 2025 record dates but 2026 ex-dates;
- two cross-market mergers: 000522 to 600332 and 002013 to 600372 require an
  account-registration / successor-account simulation rule that the official
  documents cannot determine for a generic portfolio;
- `RAW:FULL_UNIVERSE` and `SUSPENSION:FULL_DAILY` remain open. The retained
  official audits leave 239 SZSE source rows and 2,010 SZSE resumption
  boundaries unresolved.

The cash subset now supports 13,587 of 13,590 P1 cash documents; the remaining
three are listed above. The retained-bonus fraction gate is resolved and the
bounded official bonus/restructuring closure is complete, but this does not
certify a full corporate-action census.

Full source preflight V6 remains blocked. Adjustment economics still have 478
gross cash-plus-bonus conflicts, and historical transaction costs still have
six unresolved claim groups including the research-account commission scope.
No paid product has been shown to be required or sufficient, so no paid-source
option report is created. Human official-source input and new methodology are
required before the verified safe start can be established.

Immutable external evidence:

- `p1-residual-merger-fact-closure-v2.json`: file SHA-256
  `df7268d1caa6f6a56debe0c84fc6510febd681d410c0961c522a575842ba20f2`,
  manifest SHA-256
  `3587ba3501c4dda63f1c48098a2f256abfadb767b3c8caadc0e3729c6e47ec25`;
- `p1-cumulative-official-fact-closure-v65.json`: file SHA-256
  `372312f16e9265306e6e341f8131b58719771d72c6fa127eb3e6ea960fef017c`,
  manifest SHA-256
  `e6d87aa5a2f16422ca063d5ff9ce3a9a38a2cfaef3e8f8d465c151f561963792`;
- `p1-remaining-cash-source-queue-v18.json`: file SHA-256
  `174f0579d496ff440f49af9b005ed997eabdf24f9170d3e01818af8386b248ba`.

Full Dataset creation, audit and freeze remain `NO`. Development, Validation
and Official OOS remain `NOT_RUN`. PR #12 remains open and unmerged.
