# SSE / CNINFO disclosure reconciliation

SSE announcement metadata is the **PRIMARY EXCHANGE INDEX**. A reconciled CNINFO
issuer document is **DISCLOSURE DOCUMENT EVIDENCE**, not a replacement rule authority.

CNINFO describes itself as SZSE's statutory disclosure platform, operated by Shenzhen
Securities Information Co., Ltd., a wholly owned SZSE subsidiary:
https://www.cninfo.com.cn/new/index?lang=zh
Its operator describes coverage including Shanghai main-board and STAR disclosures:
https://www.szsi.cn/cpfw/
The public announcement query's `column=sse` interface returns Shanghai issuer
disclosures (verified with the 2023-04-28 Blue Light Development announcements).

`backend/scripts/reconcile_sse_cninfo.py` reads the preserved SSE source manifest and
candidate failure inventory, validates source hashes, then searches ordinary public
CNINFO disclosure metadata by date and risk-warning subject. Keywords retrieve
candidates only. Acceptance requires identical security code, Shanghai-local
publication date, and full title after punctuation/whitespace normalization.
Multiple distinct document IDs remain AMBIGUOUS; no fuzzy/high-confidence matches
are accepted automatically. Issuer identity must additionally agree in PDF content
before an event can be normalized. HTTP snapshots, exact request parameters, UTC
retrieval times, sanitized response metadata and original PDF bytes remain outside Git.

Requests are sequential, with a 35-second timeout and checkpoints. Only plain network
timeouts may be resumed, at most three attempts total with bounded backoff; prior
attempt records are retained in the snapshot metadata.
Cached successful responses are checksum-verified; non-timeout failures are not retried.
No spoofed browser headers, proxy, CAPTCHA, stealth, or SSE PDF
request is used. A denial or non-PDF response stops ingestion.

Run with `--sse-snapshot`, `--candidate-inventory`, and `--output` paths. Successful
snapshots are reused on restart. Selection is the existing 242-document heuristic,
not proof of complete exchange history. Unknown periods must never become NORMAL.
Dataset creation, freeze, and strategy studies remain gated until coverage is proven.

## Offline event reconstruction

Run `python -m scripts.sse_st_events --root <CNINFO snapshots> --master <SSE CSV>
--sse-snapshot <preserved SSE snapshots>` from `backend` with locked dependencies.
The parser verifies the PDF digest, security code and issuer identity, then requires
an explicit stock-name change and risk-warning start-date label. It also handles an
explicit continued-name statement with an explicit start date as STATUS_CONFIRMATION,
never an EXIT. Normalized statuses are NORMAL, ST and STAR_ST; missing knowledge is
UNKNOWN. Partial removal of risk reasons must not remove the STAR_ST classification.

Every accepted record retains both source identities/checksums/publication dates,
CNINFO retrieval UTC, parser version, and supporting page/compact-text offsets.
No publication-date fallback, inferred initial NORMAL, or retrospective application
of later disclosures is permitted. `status_on` is explicitly a **last-known-event**
query, not a certified complete market-status service. `effective_to` stays null
because an interval end cannot be certified from an incomplete event index.

The 137 candidate securities are all retained in a classification manifest with
listing/delisting-clipped unresolved ranges. Until the candidate heuristic and initial
states have a completeness proof, no candidate is labeled fully resolved merely
because one of its events parsed. Unknowns are not automatically excluded to force
a passing gate. Whole-pilot exclusions without a materiality demonstration are not
adopted; no strategy results are used to choose exclusions.

Small offline fixtures contain extracted factual disclosure text and source lineage
for all six transitions and a partial-removal/continued-STAR_ST example. Original
PDFs remain in external staging. Tests distinguish functional point-in-time behavior
from real-world completeness certification.

## 2026-09-10 acceptance snapshot

All 242 selected SSE announcements have exactly matched CNINFO metadata and archived
PDFs (992 distinct CNINFO metadata documents searched). One query timeout and one PDF
timeout recovered on the second attempt; no outstanding downloads or ambiguous matches.
The PDF-content retrieval blocker is resolved without accessing the restricted SSE CDN.

The strict parser produced 176 records across 112 securities: 65 ENTRY, 57 EXIT,
23 ST_TO_STAR_ST, 19 STAR_ST_TO_ST, and 12 STATUS_CONFIRMATION. Of these, the pilot
contains 50 ENTRY, 29 EXIT, 16 ST_TO_STAR_ST, 8 STAR_ST_TO_ST and 7 confirmations.
Sixty-six documents remain unresolved as effective-dated events: 33 lack an accepted
explicit start-date pattern, 31 lack an accepted name transition/confirmation, and two
are retrospective references held for review. These include progress/application notices,
not necessarily 66 missing transitions. No remaining parsed-chain conflicts were found.

The source index selection does not certify complete transitions or initial states.
All 137 candidate securities therefore remain UNRESOLVED **for full-period coverage**,
despite 112 having parsed evidence. Last-known pre-pilot events suggest 29 risk-warning
states, but that is not a certified pilot-start census. No blanket exclusion is adopted.
The gate is PARTIAL / BLOCKED, not PASS. No pilot dataset, freeze, studies, merge or tag.

SSE metadata aggregate SHA-256:
`a1e45cce9e9d2715bee19d23ef4a8cf9c5f2036b946a551939d1905b9445ab47`

CNINFO snapshot-manifest aggregate SHA-256:
`e111a0a06a73c487adae5c32173775ffed5dfad2a79174f28dac6f8168f892a9`

Normalized event SHA-256:
`846e4614812042c235631ce8abbfb5dd8ff8a10da2e8346d419662cbf9118675`
