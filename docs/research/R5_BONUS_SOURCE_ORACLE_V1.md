# R5 bonus source-oracle review

## Component-integrality correction — 2026-09-18

The original official source terms remain 603023's 0.5 stock dividend plus
1.5 capital-reserve shares. Their sum is two, but the earlier v28 ledger did
not prove that each integer-holding account receives two whole shares when
the components are registered. The same issue occurs in 38 other previously
accepted bounded events. This is uncertainty about account allocation, not
about the published ratio or the retrospectively confirmed listing date.
No document establishes a universal combined-allocation rule for the event
dates. The existing policy does not authorize a fractional retained-bonus
convention, so all 39 are now explicitly unresolved rather than assumed safe.

The source-byte-verified, deterministic replay is `integer-bonus-ledger-v30.json`
(file SHA-256 `05421d892782d219316c47952e21f3e87ce16c6b55acf8041b01132f9b6d939d`,
manifest `e5df58295be544873872d40b10dc82a591d921f8dd2108ac4144943afcd0e2e4`):
**243 supported / 45 unresolved** of 288 bounded candidates. Each rejected
source SHA and reason is in the ledger's `unresolved_documents`. The narrower
dual P1 audit v7 closes **11/16** source requests (22 facts), rejects five
missing an accepted bonus leg, and cumulative v54 leaves **257 facts / 252
documents** open. v28/v6/v53 below are immutable *historical* results now
superseded for current acceptance. The 7,119 oracle rows outside the bounded
subset remain unassessed; no full corporate-action census is claimed.

## Previous 603023 bounded parser correction — 2026-09-18

The retained original [2016-06-04 CNINFO issuer notice](https://static.cninfo.com.cn/finalpage/2016-06-04/1202356226.PDF)
(SHA-256 `b54bfa9d42641fd1d3f0bf2c0e45e7cd0730bd7797c058a117cc293a9e513b73`)
states gross cash **0.15 CNY/share**, stock dividend **0.5 share/share** and
capital-reserve transfer **1.5 shares/share**, total retained-share ratio
**2.0**; record 2016-06-14 and ex/cash 2016-06-15. The shared term parser
mistook the later tax discussion's split **1.3 tax-free + 0.2 taxable**
capital-reserve shares for competing entitlement ratios. It now excludes the
tax-explanation section from entitlement extraction while still fail-closing
on nonstandard markers in the full document. Deterministic replay of all 288
bounded candidates preserves the prior 281 event checksums and adds only
603023: v28 **282/288** supported, **6** unresolved and **7,119** source-oracle
rows outside the integer/next-session subset. Immutable v28 file SHA-256
`9df2264ba93ca5cd0a0abee1074b38f281143d3c9a61fb495967f3e785714a0d`,
manifest `2b65dfe5bd7807363f833e5a7d00a686fc8a798dccc4c5330022a039a2260027`.

The notice's cover gives new unrestricted-share listing **2016-06-16**, while
its body says **2016-04-16**, before the record date. The later official
[2016 half-year report (revised)](https://static.cninfo.com.cn/finalpage/2016-09-02/1202669225.PDF)
(SHA-256 `e66612fa75a69524c32469c563618dfde70867a3bd7eee089b8339f25d2e8d30`)
retrospectively states **2016-06-16** on PDF pages 15, 21 and 61. Its CNINFO
metadata and original download receipt are retained and SHA-verified. This
resolves the exact two-leg P1 source request as an **audit-only** corroboration,
never a signal available on the 2016 ex-date. The existing bounded event
still carries `scheduled_listing_not_actual_tradability`; it does not infer
individual account-level awards or certify the full bonus census. P1 dual
source closure v6 is **16/16 documents, 32 facts**, manifest
`343002c25a3c070cb451678f6e07dbcaedb5f18937a675055ba3f25dfccb1271`.
Cumulative v53 is **16,073/16,320** handled, **1,991** official substitutions,
**247 facts / 247 documents** open (241 acquired distribution, 6 other),
manifest `3a7d57f3b3c8ce4839cdad846bdc0e1a20c0e8246e2578d40432fbacf6776db3`.
Full census and Full Dataset remain unadmitted.

Retained SSE/SZSE tables yield 7,407 source date groups, not accepted events.
7,368 directly match one full-master interval; one more maps through the already
verified 601313/601360 code transition and dated original issuer PDF. 38 B-share
source rows remain explicit and out of ordinary-A scope. No CDR row occurs here.

Source display ratios: 6,035 fractional / 1,372 integer across all source rows.
These are not registry allocations or full corporate-action classifications.
5,711 rows lack a source-scheduled new-share listing date; 1,696 have one. Of
the latter, 1,695 are the next accepted calendar session after ex-date. The one
exception is 600817, already accepted as mandatory pass-through. Its actual
resumption was 2013-02-08, not the table's 2012-08-02 scheduled date. Existing
review/source manifest reused; no event re-audit or double-counted acceptance.

601360's source table retrospectively labels a 2013 event with the current code.
The retained 2013-03-29 issuer notice (62294278, SHA
abfa8f00fb01b0934db8272d4ebf0dee74939d00bcc0ca6d98f40fc5d196da9b)
has actual code 601313, record 2013-04-03, ex 2013-04-08, conversion 0.8 and
new-share listing 2013-04-09. Original source code/name preserved; no backdated
current name. Fractional allocation and accounting admission remain separate.

External root: `/home/yuchen/data/research/staging/full-bonus-inventory-v1`.

- source-oracle-v1.json: `835b9a734804d34c835cf6ae77eeeb570813bd309437313267e1e55f5382caed`
- lifecycle-crosscheck-v2.json: `bf1f676709d307a10142797ff5e707ea797b49f54609aa4ed0853df98d5495bd`
- listing-boundary-check-v2.json: `6f68629b959de30e8fbe711bb5756bf74d02a2543ace949d939dde6c6a26b18b`

Earlier v1 `first_tradable_date` field is source-scheduled listing only, never
proof of actual trading; v2 boundary review explicitly records that distinction.
Accepted new events = 0. Full census/readiness remains PARTIAL. No new fractional
policy, strategy, full dataset creation/audit/freeze or PR merge.
