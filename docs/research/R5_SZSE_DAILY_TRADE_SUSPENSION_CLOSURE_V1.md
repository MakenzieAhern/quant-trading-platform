# R5 SZSE official daily-trade suspension closure V1

The complete checksum-bound SZSE daily workbook corpus closes the 2,009
resumption facts left by the exact-notice reconstruction without inventing an
intraday resumption time.

- 2,003 events close at the first later official daily row with positive
  turnover. Execution remains blocked at that day's open.
- 2 events have no later trade and close at the accepted official security-
  master lifecycle end.
- 4 events begin in late December 2025 and remain suspended through the
  2025-12-31 coverage boundary. They are right-censored, not assigned a
  resumption date.
- Same-day turnover is never used to close an event because it may precede an
  intraday suspension.

The source corpus contains all 3,886 accepted sessions from 2010-01-04 through
2025-12-31. Every workbook is rechecked against its retained official URL,
referer, UTC receipt and SHA-256 before use. Stable identities come only from
the accepted point-in-time master. The resulting reconciliation and authority
both replay byte-identically.

Evidence:

- reconciliation file SHA-256:
  `dbad34426ccda8f875b10ccc5613820acafe0c29d6274ff2420ef1246df17b81`
- reconciliation manifest SHA-256:
  `ec86a5849a894ab304548ba7ae5d2778fb0f424ffc9208442a2709a7f18d7db9`
- suspension authority file SHA-256:
  `26b72b333a6de0d541c29a665132c810ec11de344f00c124da94558565031433`
- suspension authority manifest SHA-256:
  `b495a9e17337549b37b39e23d699ad2295e7c3168a7f37ef237d61744fab322a`
- full-source preflight V14 file SHA-256:
  `873a0921a05570439074b108fd1184c697d49d94964d5708332472d4c301ac9c`
- full-source preflight V14 manifest SHA-256:
  `77a8eda1f106f0c4ce66297a5c86b321c54c0ce47ed58e27ef57d569ff107a48`

`SUSPENSION_HISTORY = PASS_PUBLIC_OFFICIAL_RECONSTRUCTION`, with SSE unresolved
0, SZSE unresolved 0 and SZSE conflicts 0. This closes
`SUSPENSION:FULL_DAILY`; it does not promote the separate 239-row raw-price
candidate, resolve adjustment-factor economics or select historical transaction
cost conventions. Full Dataset creation, audit and freeze remain `NO`; no study
or profitability inspection was run.
