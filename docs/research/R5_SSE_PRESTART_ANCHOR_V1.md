# R5 SSE 2009 starting risk-state anchor

All 860 starting SSE members have official historical risk-name evidence:
778 NORMAL, 51 ST, 31 STAR_ST. Full historical ST authority remains PARTIAL;
the full event census and daily coverage have not been certified.

Reused the already retained SSE 2010 yearbook's explicitly labeled "Listed
Companies in 2009" table, with effective lifecycle filtering from the accepted
master cross-check. 857 names also agree with the annual trading table; three
paused members appear only in the company table: 600094 *ST华源 (PDF p210),
600681 S*ST万鸿 and 600705 S*ST北亚 (p230). Both pages visually verified. Zero
market-value cells are not converted to prices, bars, delistings or NORMAL.

The first probe left 600800 UNKNOWN because S and T split across text lines.
The corrected parser preserves ST磁卡 and agrees with the trading table;
the old probe remains immutable. Noneligible 600001/600357/600840 and future
601117/601801 entries remain explicit and are not admitted before listing.

Evidence root: `/home/yuchen/data/research/staging`.

- `full-master-sse-baseline-v1/raw/sse-yearbook-2010.pdf`: SHA-256
  `6ac37b50f03e9d5a9c6fbf0946a409ea1592a876a482d69e3a5168a85e77f0d4`.
- `full-master-sse-baseline-v1/master-text-2010.json`: SHA-256
  `ce484f350cb8fb62a3c92d6a42259c255f7d6c7a928f7239a07fb73daba7390f`.
- `full-sse-st-v1/prestart-anchor-v2.json`: canonical SHA-256
  `fac1a7bbb1a48aeb4efb2a1334e17cf441d1c10c251d90e3862886eef62868e5`.

Official source URL and retrieval UTC are retained in the anchor. Publication
date is unknown, not inferred from the server's Last-Modified header. These are
historical state facts, not a claim that the yearbook was available in 2009.
No effective dates are inferred from undated name-history ordering.

A separate bounded metadata queue now extends only 173 months outside accepted
Pilot 2023-01-01..2024-07-31, using risk-warning and special-treatment keywords.
Counts, duplicate-page detection, immutable per-window checkpoints, source hashes
and access-denial stops reuse existing acquisition helpers. Query completion is
not event-census completion; official reconciliation/name cross-check remain.
Original PDF worker is untouched. Full dataset CREATED/AUDITED/FROZEN=NO;
no studies, merge or release. Backend 586 tests and quality checks PASS.
