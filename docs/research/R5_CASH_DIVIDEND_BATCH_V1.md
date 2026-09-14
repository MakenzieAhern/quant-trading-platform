# R5 exact cash-dividend batch

7,702 cash events supported under `EXISTING_ACCEPTED_CASH_DIVIDEND`; full census
remains PARTIAL. 1,527 cash groups remain unresolved in these four source years.
This is not full dataset creation, source preflight PASS or a strategy study.

## Admission checks

Reuse retained official issuer PDFs and exchange tables, not market-price
inference. Each admitted record requires exact labeled gross-cash terms, matching
issuer header, corroborated record/ex dates and exact exchange gross amount.
No per-share precision tolerance or tax-net substitution. Differentiated
distributions, conflicting amounts, unparsed linked documents and missing dates
remain unresolved. SZSE monthly DPS is explicitly per share, not per ten shares.
Ten-share issuer terms are converted with Decimal under a local precision context.

Master intervals must identify exactly one ordinary A-share lifecycle spanning
record and ex dates. Instrument manifest must reference the same master bytes.
The approved policy catalog checksum is verified before admission. Source PDF,
extraction, input manifest, event checksum, source URL and retrieval UTC remain
attached. Reused source queues are allowed only inside the staging root and with
the expected content hash. Large ledgers remain outside Git.

The existing immutable CorporateAction and PortfolioEngine are reused unchanged.
Cash is applied under the existing gross ex-date accounting convention; actual
payment-date normalization is explicitly missing metadata under that model, not
a newly verified historical cash-deposit date. No new tax/withholding assumption,
payment-delay model or cash election has been introduced. Paired bonus-share
terms require their own independent admission and are not inferred from cash.

## Ledgers

Root: `/home/yuchen/data/research/staging/full-distribution-notices-v1`.

| Year | Supported | Unresolved | Canonical manifest SHA-256 |
| --- | ---: | ---: | --- |
| 2010 | 697 | 287 | ef6e992a7f2c1fae2547da8e7f83aea4d67c92b3ff8488ff35027bfca43d69e8 |
| 2018 | 2,527 | 307 | bcf16a49e15848b7ab6b25a7f58c0f93c01e5847372044b2df1a7e865079c01d |
| 2019 | 2,196 | 433 | 4ae3808feea45aa0c8f13f124a896e2a68ed324e57354b662aae6a6c59b5840a |
| 2020 | 2,282 | 500 | 922207918ac0b37e3f7dc88df9a214b9eb181620008248ae43ba9d13dddfe1b2 |

2010 path: `distribution-2010-reconciled-v1/cash-ledger-2010-v1.json`.
Other paths: `distribution-2018-2020-reconciled-v1/cash-ledger-{year}-v1.json`.
Earlier `cash-terms` probes remain source-only, with zero accepted events.

## Checks

Historical 600000 July 2018 gross 0.1/share fixture: 1, 81 and 100 shares retain
quantity/basis, receive exact cash and corporate-action income, and generate no
Order/Fill. Fixture seeding is not a strategy or historical Portfolio run.
Wrong lifecycle, duplicate identity, non-ordinary instrument, conflicting gross
amounts, net-only terms and differentiated distributions are rejected.
Event JSON round-trips on every accepted event. All 7,005 2018–2020 event checksums
also match reversed evidence/master order. Backend 584, frontend 78 tests PASS;
Ruff/format/mypy and frontend lint/build PASS. No domain-accounting code changed.

Full safe start remains NOT_ESTABLISHED. Full dataset CREATED/AUDITED/FROZEN=NO;
Development/Validation/Official OOS NOT_RUN. PR #12 remains open and unmerged.
