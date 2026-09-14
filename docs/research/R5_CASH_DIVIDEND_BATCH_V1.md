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

## Missing-only continuation

V2 reuses all 7,702 previously corroborated rows without PDF reparsing; their
event checksums remain unchanged. It adds 186 exact cases from spaced code
headers, explicit A/H labels and tightly linked per-ten-share cash wording.
The first labeled issuer code is required, not another issuer mentioned later.
Differentiated/rounded/conflicting source cases remain unresolved, not relaxed.

| Year | Supported v2 | Unresolved v2 | V2 canonical manifest SHA-256 |
| --- | ---: | ---: | --- |
| 2010 | 784 | 200 | fb56da8ef89a8f319df620ca8ce532c8a606a9787776c6bf9ce2e26529edb2a1 |
| 2018 | 2,562 | 272 | 538d1f20abb1bbfc9b78f90fd02e292a81c3bb4aec36dbfa4d3b31cb796d9b4e |
| 2019 | 2,227 | 402 | 2a574412e17f401fbb8c494becc9867af131fa22f074fb84648fa54f36aea02c |
| 2020 | 2,315 | 467 | b7919d4155103f61f3a17381ad602f88e095d84014be84bc0e862120c33a5cf4 |

Paths use `cash-ledger-{year}-v2.json` in the same respective directories.
Current totals: 7,888 supported, 1,341 unresolved. Full census still PARTIAL.

## 2011–2016 continuation

Existing parsers, policy and accounting reused without changes. All 35 transient
retrieval failures recovered in a separate batch; original receipts preserved.
11,679 source leads comprise 11,551 PDFs and 128 JavaScript summaries. Summaries
are not full-document authority and remain outside this cash reconciliation.
Reconciled source manifest SHA-256:
`254face386cc968d97a6ebcd11c2ade34749f85a2403992f584664426104e9e6`.

| Year | Supported | Unresolved | Canonical manifest SHA-256 |
| --- | ---: | ---: | --- |
| 2011 | 916 | 271 | dd678fd6810a82b09e742e49b813e420b720496e4f58f7a9d7fc6a3248d1c07a |
| 2012 | 1,343 | 211 | a25caf4ed9f9b73b4db17f63de59449acbca39a73aaed65912263a93eb14d34d |
| 2013 | 1,492 | 242 | a07dbc835ef7071288325e7f5b24969335d12f6649f60eb21331aa92035d2064 |
| 2014 | 961 | 182 | 27c043d58a28ae16bc175dbe530d61e6e2241ca240f2d44d8d9921e05be32ef6 |
| 2015 | 1,695 | 322 | 84276a40aadbb2e16dc88357bacccc868d4f3f46317b9234c2699b8e7c2db9be |
| 2016 | 1,727 | 319 | 7462b48a4f952d753f0663f419f40ddf868f97899e9a03eef2cb1aaffa8b19f8 |

Paths: `distribution-2011-2016-reconciled-v1/cash-ledger-{year}-v1.json`.
Combined ten-year bounded result: 16,022 supported / 2,888 unresolved groups.
This is not a full-market count: absent exchange rows, source gaps, bonus terms
and other corporate-action classes remain independent completeness work. Nineteen
unique malformed-date PDF errors remain, not six times nineteen unique errors.
