# R5 exchange distribution census continuation

Date: 2026-09-13. R5 remains RUNNING_BATCH_CLOSURE. No new methodology gate.

## Official SZSE monthly source coverage

The official investor-domain archive exposes all 192 target months, 2010-01
through 2025-12:
https://investor.szse.cn/market/periodical/month/index.html

All 192 linked dividend/bonus/rights HTML tables were retrieved successfully,
with bounded two-worker requests, immutable URL/UTC/byte-SHA receipts and replay
from checkpoints. The www archive request failed with connection reset and was
not hammered; its official investor-domain surface succeeded.
External root: /home/yuchen/data/research/staging/full-szse-distribution-census-v1.
Source manifest v2 canonical SHA-256:
`f618caf6c1d2ec15e9b6910a8d091e264ce87a90268f2b2fc4c30693c5ad12d0`.

The row audit parsed 23,682 rows with zero failed months and no unparsed rows.
All 74 ordinary A-share rights candidates match the existing official-notice
ledger by code/ex-date; source-only = 0, ledger-only = 0.
The 000826 December 2012 table reports issued quantity zero but positive rights
ratio/price. It remains a coverage candidate, not a zero-event exclusion; the
retained official result notice confirms the December 31 ex-date. Source ratio
units are not used to fabricate accepted accounting terms.

Blank 14-cell placeholders remain explicit source-empty months. Partially filled
rows fail parsing. B-share rows remain in source evidence and are not treated as
A-share event dates. Dates, pre-tax cash display values, ratio fields and raw
cells remain separate; table precision is not exact cash authority.
Row audit v2 canonical SHA-256:
`c9b5294e927ef4ac2ea28deffe889a56b8aac6010cdb8053bec9f5336a63768d`.

## SSE reconciliation and source limitations

SSE: 17,920 dividend / 2,500 bonus source rows, 20,346 candidate groups and three
B-only rows. All eight gross cash collisions resolve to official issuer PDFs.
Four are holder-class differences; four are combined-period payments.
See SSE_DISTRIBUTION_CONFLICT_RESOLUTIONS_V1.json and
R5_FULL_RANGE_SOURCE_EXTENSION_V1.md.

Retained SSE yearbook rights sections are cached by source SHA under
full-master-sse-baseline-v1/rights-text. Their dates are not interchangeable:
the 2011 market factbook explicitly groups by 2010 record date, including
600518's 2011 ex-date. The 2017-statistics table omits the already evidenced
600057 December event. Yearbooks supplement, not replace, the event ledger.
Missing sections do not by themselves prove a zero-event year.

## CNINFO API probe: supplementary only

The already installed AKShare public CNINFO client can retrieve
https://webapi.cninfo.com.cn/api/sysapi/p_sysapi1139?scode=600989
but its numeric dividend field returns a company-wide average for known
holder-class distributions. Its description sometimes gives exact class terms
and sometimes omits them. The 600005 request returns zero records despite
known historical events. Neither response is promoted to full authority.

Receipts under full-cninfo-distribution-probe-v1 preserve public-client code
hashes, request identity, response bytes, UTC and SHA; ephemeral request headers
are not stored. 600989 source SHA:
`17b642de945ac094015ff70b10d21620256e7d5130b8e4606ed84d05da6d4a7d`;
600005 source SHA:
`6b5a6d47f53d788ff5677b903eac19693d9a28c6778176590054ec7595025de0`.
This also identifies further precision/class checks for 600989's 2020 and
May 2022 distributions; they are not admitted on an average numeric field.

## Checkpoint

561 backend tests, Ruff/format/mypy PASS. Last frontend 78 tests/lint/build PASS.
No strategies, performance inspection, parameter changes, merge or release.
Full corporate-action census remains PARTIAL: exact cash terms, retained bonus
versus restructuring allocation, complete merger/surrender chains and independent
full master/ST/suspension/rule/raw/factor checks continue. Safe start remains
NOT_ESTABLISHED. Full dataset CREATED/AUDITED/FROZEN = NO.
