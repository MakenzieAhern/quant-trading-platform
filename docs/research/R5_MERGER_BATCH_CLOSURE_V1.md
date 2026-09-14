# R5 retained implementation batch closure

Four additional mandatory stock mergers are normalized under the existing floor,
zero-whole-share basis write-off and first-post-event trading-boundary conventions.
No cash election is exercised; unknown offer metadata stays null, not false.

| Parent | Successor | Official ratio | Record date | Daily effective boundary |
| --- | --- | --- | --- | --- |
| 000527 | 000333 | 0.3447 | 2013-09-17 | 2013-09-18 |
| 000562 | 000166 | 2.049382716 | 2015-01-23 | 2015-01-26 |
| 300186 | 300498 | 0.8070 | 2015-10-30 | 2015-11-02 |
| 000916 | 001965 | 0.6956 | 2017-12-22 | 2017-12-25 |

The boundary is not an inferred registry timestamp. Retained official issuer PDFs
establish the terms and continuous suspension; audited master intervals and eight
targeted raw-series requests corroborate the last-parent/first-successor sessions.
The raw requests are boundary evidence only, not full OHLCV authority acceptance.
000562 uses the explicitly published nine-decimal ratio, not a recomputed quotient.
000562 and 300186 have unknown cash-offer metadata, which cannot enable elections.

Reviewed facts, URLs, publication/retrieval timestamps, PDF hashes and reviewed pages:
`backend/tests/fixtures/merger_implementation_batch_v1.json`.
External immutable output:
`/home/yuchen/data/research/staging/full-merger-v1/reviewed-implementation-batch-v1.json`.
Canonical manifest SHA-256:
`ea6feddc44ae61e3540916c03354d070f2c04b11887f4b321f694634c7ba6397`.
All source bytes, input manifests, lifecycle boundaries and event ordering verified.

MERGER_INVENTORY_V3 preserves the five prior candidates and adds four: nine reviewed
candidates, six supported, three still unresolved. This is NOT the full-market
event count. Full census and account-path materiality remain unestablished.
Tests exercise Q=1/81/100, basis, zero-whole outcomes, unchanged cash, no trade PnL,
no order/fill, persistence roundtrip and parent non-orderability. These are synthetic
accounting checks, not strategy studies. Backend 571 and frontend 78 tests pass;
lint/type checks and frontend build pass.

Distribution recovery continues independently. The 2010 date-only linker matches
998/1,060 census groups; it accepts zero economic events. Remaining unmatched groups
and the page-footer extraction error remain explicit. No dataset created, audited
or frozen; no Development, Validation, OOS, PR merge or release.
