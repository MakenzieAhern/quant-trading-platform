# R5 rights policy and inventory checkpoint

## Outcome

Human-approved `CN_A_RIGHTS_ISSUE_POLICY_V1` / `DECLINE_SUBSCRIPTION` is implemented
in the existing immutable event / centralized portfolio path, with no new dependency.
Event model, accounting and deterministic replay engineering PASS. The previous blocker
`FULL_HISTORY_RIGHTS_ISSUE_TREATMENT_REQUIRES_HUMAN_DECISION` is RESOLVED.

R5 remains blocked under the user's Section 8 evidence rule, **not on choosing whether
to subscribe** and not at the full dataset freeze gate. No large R5 materialization began.

## Inventory scope and counts

The complete retrieved Eastmoney `RPT_IPO_ALLOTMENT` response has 984 unique source rows
across two pages (the server caps page size). Filtering by record/window/ex/listing lifecycle
overlap with 2010-01-01..2025-12-31 identifies 148 events and 137 securities. Dates are not
filtered using current security names or current ST status. Both pages and request metadata
are preserved. This is **all identified provider events, not a complete exchange census**.
There are no 2024/2025 or STAR events in this response; absence is not independently certified.
The existing official SSE 2010 factbook's 17 record-date-year constituents exactly match
the 17 SSE 2010 provider constituents, with no missing/extra codes. This one-year check
does not certify 2011-2025 or SZSE completeness.

| Measure | Count |
| --- | ---: |
| RIGHTS_EVENTS_TOTAL | 148 |
| SECURITIES_WITH_RIGHTS_EVENTS | 137 |
| EVENTS_WITH_COMPLETE_TERMS (including verified supported variant) | 2 |
| EVENTS_WITH_INCOMPLETE_TERMS / UNRESOLVED_EVENTS | 146 |
| SUPPORTED_STANDARD_EVENTS | 2 |
| UNSUPPORTED_VARIANTS (positively identified non-standard structures) | 0 |
| Unresolved events carrying fail-closed RIGHTS_EVENT_UNSUPPORTED_VARIANT safety code | 146 |
| Securities excluded because of rights | 0 |

Zero confirmed special structures does **not** mean all 148 are standard. Of the four
deterministically selected sample events, two are supported and two retain variant evidence
gaps. The other 144 are inventoried, not individually source-accepted. Source-populated
price/date columns are not equivalent to complete audited economic terms.

## Official sample and reconciliation

Selection was fixed without strategy results: required600036, earliest target SZSE Main
event000960, earliest target ChiNext event300147, latest target event000049. All four have
official price/ratio/record/window/effective-date corroboration; result and listing notices
are retained separately. Exact URLs, PDF SHA-256, retrieval UTC and claim locations are in
`RIGHTS_ISSUE_SOURCE_REVIEW.json`. PDFs are external, not in Git.

| Security / record date | Price CNY | Ratio per share | Subscription window | Ex date | Variant acceptance |
| --- | ---: | ---: | --- | --- | --- |
| 600036 / 2010-03-04 | 8.85 | 0.13 | 2010-03-05..11 | 2010-03-15 | Supported; prospectus p.36 explicitly prohibits transfer and compensation for declined A-share rights |
| 000960 / 2010-01-18 | 8.98 | 0.24 | 2010-01-19..25 | 2010-01-27 | Unresolved non-transferability evidence |
| 300147 / 2015-06-09 | 10.46 | 0.30 | 2015-06-10..16 | 2015-06-18 | Unresolved non-transferability evidence |
| 000049 / 2023-11-29 | 21.16 | 0.30 | 2023-11-30..12-06 | 2023-12-08 | Supported; prospectus pp.6/26 explicitly prohibits transfer and compensation |

600036's source `TOTAL_SHARES_BEFORE=19,119,490,016` includes non-A capital; the official
A-share eligible base is **15,658,890,016**. The normalizer never substitutes total capital.
600066's provider `FIRST_NOTICE_DATE=2012-02-23` follows its ex-date2012-02-21. Its raw
claim is preserved, normalized announcement remains null, and it remains unresolved;
no invented pre-ex announcement or silent backdating. Later listing dates remain in raw
evidence; reviewed ex-date events do not import listing facts disclosed subsequently.

## Exact current stop

`RIGHTS_EVENT_UNSUPPORTED_VARIANT:CN-A:SZSE:000960:2010-01-27`

This is an **unverified subtype**, not a finding that the rights were tradable. The issuer's
issuance notice proves original-holder subscription, limits, expiry and unpaid-rights lapse.
The result notice proves price8.98, ratio0.24, base651,086,660 and actual ex-date2010-01-27.
It does not establish the missing independently non-tradable entitlement classification
to the same evidence standard as the supported controls. No assumption is promoted from
absence of contrary wording.

Evidence searched: CNINFO category/date query (10 announcements), issuance57498926,
232-page prospectus57498925, summary57498927, result57547253, listing57568546; targeted
issuer/non-transferability searches. Subscription/cash-funding methodology is already approved.
Smallest resolution: official evidence establishing this event's entitlement transferability,
or an explicit human source-classification decision on the retained issuer contract.
Do not exclude000960, erase its event, or label it standard merely to clear the gate.

Source snapshot for the mandatory600003 2010 demerger was also retained while tracing
full-history structural categories. It is not a rights event, not accepted for accounting,
and not a second active approval request. Full-history structural-action work remains pending.

## Engineering and persistent evidence

28 focused rights/inventory tests PASS, including holding/zero shares, subscription/lapse,
raw mark impact, adjusted-price separation, unchanged cash/shares/basis, no Orders/Fills/
capital/reservations, retained master membership, mixed cash/bonus/rights input permutations,
replay, immutable/checksummed events, missing/contradictory terms, unsupported categories,
pagination completeness and raw-source contradictions. Full backend suite467 PASS;
Ruff/format/strict mypy PASS. Frontend78 tests PASS; lint/type/build checked at milestone.

`/home/yuchen/data/research/staging/full-rights-inventory-v1/inventory-reviewed.json`
contains all148 normalized candidate events and their individual checksums, issues and lineage.
Canonical inventory manifest SHA256:
`1b9b070c8ce51d7f78c44c1f5a2b96a60e2e42203c9813c641f358f2fc42647a`.
File SHA256: `709c47e566cfa7c7994b54b09d05d1c7f449f31bc39939cf71ab00d5aada3ea6`.
Official review SHA256: `212cb0fa4b42378d249e41c73dbe1e99dc1c8fa17414fd648dfc8617f0431f58`.
Parser version `RIGHTS_INVENTORY_V1`; parser/model SHA pins are inside the manifest.
Repeat publication reproduced identical bytes with no source retrieval. Reversed page and
row inputs reproduce the same canonical inventory. Initial inventory.json is preserved as
an earlier intermediate snapshot, not the current authority.

Replay from `backend`, with the existing audit Python environment:

```sh
python -m scripts.inventory_full_rights \
  --sources /home/yuchen/data/research/staging/full-rights-inventory-v1 \
  --review ../docs/research/RIGHTS_ISSUE_SOURCE_REVIEW.json \
  --output /home/yuchen/data/research/staging/full-rights-inventory-v1/inventory-reviewed.json
```

## Preserved gates

R4_V2_STATUS=PASS; R4_REAL_DATA_FILL_COUNT=0. Accepted Pilot v2 and its frozen bytes are
unchanged. No R4 replay, strategy modification or profitability inspection. Rights-free
zero-fill R4 sessions retain their engineering conclusions; focused synthetic tests cover
filled-trade accounting, not a claim of real historical fills.

Requested full coverage2010-01-01..2025-12-31; VERIFIED_SAFE_START_DATE and VERIFIED_FULL_COVERAGE
remain NOT_ESTABLISHED across all required authorities. Full dataset reserved id
`cn-a-research-20100101-20251231-v1`; CREATED/AUDITED/FROZEN=NO, counts/hash=null.
R5 source preflight remains PARTIAL, never extrapolated from accepted Pilot PASS.
No Development/Validation/Official OOS, freeze, PR12 merge or v1.1 release. OOS_AUTHORIZED=NO.
