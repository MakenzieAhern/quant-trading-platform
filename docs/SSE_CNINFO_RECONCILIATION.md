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

This is the preserved **earlier** snapshot. The completeness follow-up below supersedes
its terminal classifications, not its immutable acquisition files or checksums.

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

## SSE ST COMPLETENESS AND PILOT DATASET REPORT

2026-09-10 follow-up, pilot 2023-01-01 through 2024-07-31. PARTIAL / BLOCKED.
No provider change, archive restart, dataset publication, study, freeze, merge or tag.
The original 242 exact SSE/CNINFO pairs remain unchanged. Two factual parser gaps
(stock/short-name wording and optional colon) are fixed in the shared extractor;
the original contradictory date is still rejected. Small original-text fixtures cover
both newly parsed documents and the conflicting document. No dependencies were added.

### Reproduce without network

From `backend`, with the existing locked environment:

```sh
python -m scripts.sse_st_coverage --audit \
  --source <preserved-CNINFO-directory> --output <completeness-directory> \
  --master <audited-SSE-master.csv> --calendar <pilot-sessions.json>
pytest -q tests/test_sse_cninfo_st.py tests/test_sse_st_coverage.py
mypy --strict --explicit-package-bases scripts/reconcile_sse_cninfo.py \
  scripts/sse_st_events.py scripts/sse_st_coverage.py
```

External derivatives: `candidate-audit.json` (all 137 identities and required evidence
fields), `non-primary-audit.json` (66 documents), `normalized-events.json`,
`dated-evidence.json`, `status-intervals.json`, `coverage-summary.json` (including
382 daily denominators and excluded security-days per identity), `audit-manifest.json`.
The audit rereads and verifies original PDF hashes; the manifest hashes every local
derivative and targeted snapshot. These files are not market-dataset publications
and remain outside Git. No accepted historical snapshot is overwritten.

### Targeted predecessor evidence and its limit

The original events supplied last-known pre-pilot states for 57 candidates. Only the
other 80 were queried individually through the existing CNINFO path. All 80 now have
matching issuer-code/short-name observations from 2022: NORMAL 64, ST 14, STAR_ST 2.
Five first-pass header failures were repaired by inspecting earlier same-issuer
documents, with separate immutable repair snapshots. No candidate requires an unknown
document identity simply to obtain a dated observation.

Acquisition is bounded to four concurrent issuers, the newest 30 metadata rows in each
of 2022/2021/2020, and existing per-request timeout checkpoints. Successful observations
stop the lookup. This is NOT an exhaustive historical archive traversal: page limits
must never be described as proof that a full year was searched. No 2021/2020 lookup
was needed in the successful result. The floor is 2020-01-01; reaching a page boundary
without sufficient evidence is an explicit exclusion, not proof of NORMAL.

These new documents are CNINFO issuer-header observations, **not new EXACT SSE matches**
and not invented original implementation dates. The observation becomes known only
on its publication date. A later header or a future event's old name cannot fill an
earlier gap. Observations plus accepted pre-pilot events produce last-known states
NORMAL 92 / ST 31 / STAR_ST 14, but do not certify continuous pilot-start coverage.

The preserved risk-warning category and 242-document selection are not a closed-world
index. Absence from those candidates cannot prove NORMAL for the other 2,150 master
securities. Nor does a dated header alone prove absence of later omitted transitions.
Two bounded SSE metadata probes returned the system-busy wrapper; no SSE PDF attempt,
header spoofing, new provider, or unbounded retry was used.

### Terminal classifications and document closure

All five RESOLVED categories: **0**. CONSERVATIVELY_EXCLUDED: **137**. UNRESOLVED
terminal labels: **0**. This closes the audit accounting, **not** the evidence gap.
Certified candidate pilot-start states: NORMAL 0 / ST 0 / STAR_ST 0 / EXCLUDED 137 /
UNKNOWN 0. Full-master risk resolver: EXCLUDED for all eligible dates until coverage
is certified. This is an audit quarantine, not an accepted research-universe exclusion.

The 66 earlier non-primary classifications are:

| Classification | Count |
| --- | ---: |
| DUPLICATE_EVIDENCE | 1 |
| STATUS_CONFIRMATION | 34 |
| APPLICATION_ONLY | 4 |
| PROGRESS_NOTICE | 18 |
| NON_STATE_RISK_NOTICE | 3 |
| NO_EFFECTIVE_CHANGE | 3 |
| MISSING_EFFECTIVE_DATE | 0 |
| PARSER_FAILURE | 2 |
| CONFLICTING_EVIDENCE | 1 |

Both historical PARSER_FAILURE entries are now fixed (`resolved_by_parser_fix=true`,
`potential_blocker=false`): 1213274369 / 600654 / 2022-05-06 and
1219926861 / 600112 / 2024-05-06. They remain labeled by the cause of their earlier
non-primary status so all 66 reconcile; neither remains an unresolved parser failure.
Document 1213268833 / 600260 explicitly contains both 2020-05-06 and 2022-05-06.
It is preserved as CONFLICTING_EVIDENCE, not silently repaired. Later observations
can describe later state without resolving that earlier implementation date.

### Timelines and materiality

178 normalized records: ENTRY 65 / EXIT 57 / ST_TO_STAR_ST 25 / STAR_ST_TO_ST 19 /
STATUS_CONFIRMATION 12. Pilot subset: ENTRY 50 / EXIT 29 / ST_TO_STAR_ST 17 /
STAR_ST_TO_ST 8 / STATUS_CONFIRMATION 7. New entries: ST 25, STAR_ST 25.
Removals: ST 20, STAR_ST 9. Observed pilot risk securities: **at least 95**.
Last-known evidence-only timelines are all NORMAL for 42 candidates; this is not
permission to call those 42 proven never-risk-warning securities.

2,391 compact intervals preserve evidence-status changes but keep actual `status`
EXCLUDED and `coverage_certified=false`. No gaps or overlaps; all 382 pilot trading
sessions resolve exactly once per eligible security. Listing dates prevent future-IPO
rows; delisting dates clip eligibility without removing historical identities.
24 master securities delist by pilot end and remain represented historically.
The Sina calendar raw bytes and the decoded session list have preserved checksums.

Excluded securities **2,287 / 2,287 (100%)**; excluded eligible security-days
**853,328 / 853,328 (100%)**. Exclusions affect every pilot session at 100%, not a
particular date cluster. They cover all 95 observed risk-warning and all 24
pilot-delisted securities, rather than selectively deleting those groups. Underlying
uncertified evidence intervals: 2,391; unexplained missing resolver results: 0.

Acceptance rationale: require complete coverage or evidence that residual exclusions
are immaterial; neither a small arbitrary cutoff nor a strategy-performance result
can supply that evidence. Excluding the entire universe is necessarily material.
Therefore the executable structural invariant PASS **does not** imply readiness PASS.

### Gates and downstream outcome

- PILOT_START_STATUS: PARTIAL.
- ENTRY_EFFECTIVE_DATE / EXIT_EFFECTIVE_DATE: PASS for accepted events only;
  exhaustive entry/exit coverage remains PARTIAL.
- DELISTED_RETENTION / FUTURE_EVENT_LEAKAGE / INPUT_ORDER_REPRODUCIBILITY: PASS
  for this audit and resolver, not a nonexistent dataset.
- SSE_HISTORICAL_ST_RECONSTRUCTION: PARTIAL.
- AKSHARE_ACCEPTANCE: NOT PROMOTED TO PASS_FOR_PILOT.
- PILOT_A_SHARE_DATA_READINESS: BLOCKED.
- PILOT_DATASET_CREATED / DATASET_AUDITED / DATASET_FROZEN: NO.
- DEVELOPMENT_STUDY_RUN / VALIDATION_STUDY_RUN / OFFICIAL_OOS_RUN: NO.
- PR_MERGED / V1.1.0_CREATED: NO.

Dataset survivorship, future-IPO, delisting-retention, look-ahead, ST point-in-time,
stable-ID, OHLC, calendar, adjustment, suspension, checksum, order reproducibility
and restart/resume audits: NOT RUN (no pilot dataset). Bars, missing/rejected/failed
observations, suspensions, partitions and dataset-manifest hash: N/A, not zero.

SSE master file SHA-256:
`b4d930c0e3368f67237076588dd65088de4e77ebcd8187d3bc271d761d7c9972`

New normalized event SHA-256:
`0f46662759f427436a13865cc187ac817c1858420a437028d8c509edcb56b0a3`

Pilot-session-list SHA-256:
`314ec2633400880b1573a59508ac71930c834ec3f25ed59d6b55e70c0a917dd6`

Audit manifest SHA-256 (499 local evidence/derivative files; identical on offline rerun):
`19d38262f84fac9fe4edb90c01e4ab624edd841bd247ebec6f41fd2ec52b863c`

Local validation: 335 backend tests (including the v1.0 regression suite), 19 focused
SSE/CNINFO tests, 74 frontend tests; Ruff, format, strict application/script mypy,
ESLint, TypeScript, production build and all three Compose configurations passed.
npm audit and pinned Python dependency audit report no known vulnerabilities.
PostgreSQL and Redis health passed. Alembic downgrade/re-upgrade/schema check passed
only in disposable test PostgreSQL; the application database was not used for tests.
One pytest `pythonpath` setting makes both console and module invocations find local
audit scripts in Docker, without modifying installed runtime packages.

**ONE remaining blocker:** a closed-world, point-in-time SSE baseline/transition
coverage proof for the pilot universe. The current selected disclosures and dated
observations cannot establish absence of omitted changes. Dataset creation stays gated.

## SSE ST COVERAGE CLOSURE AND PILOT DATASET REPORT — 2026-09-10

This supersedes the previous baseline finding, not its immutable snapshots.
The baseline is now established. Full event-index/lifecycle closure is not yet
established, so the pilot dataset is **not created**. No research was run.

### Official historical anchor

`OFFICIAL_HISTORICAL_ANCHOR_FOUND = YES`

The [official SSE 2023 Statistical Yearbook](https://www.sse.com.cn/aboutus/publication/yearly/documents/c/10791349/files/85c1e61617f44332ac2f04dbbe5cd530.pdf)
contains the year-end individual-stock shareholder table, PDF pages 758–802.
Its explanatory notes specify the 2022 reporting period. It is a retrospective
official 2022 year-end state, **not** a claim that the book was published before 2023.

- `ANCHOR_DATE = 2022-12-31`; last trading session: `2022-12-30`.
- `ANCHOR_SHA256 = 2487b78b13f1c4bf9a8b010708c375de6170a1a817fc142fd683e954bd6cce13`.
- Parser: `sse-yearbook-2023-yearend-shareholders-v1`.
- Independent pypdf/PyMuPDF extraction agrees on all 2,213 code/name pairs.
- All 2,166 master securities eligible at pilot start are covered; no missing codes.
- Raw start census: NORMAL 2,121; ST 31; STAR_ST 14; EXCLUDED 0; UNKNOWN 0.
- The 47 extra table rows are 44 B-shares and three STAR securities already outside
  the pilot lifecycle. They are not silently added to the A-share universe.
- The 121 ordinary post-anchor IPOs use the user-authorized initial NORMAL
  assumption, with the official master listing date/name/source retained. They
  are not inserted before listing and are not inferred NORMAL from a missing event.
- Unicode asterisk variants are normalized before status classification.

The normal public Risk Warning Board XHR uses `PL_SSGSXX_FXJSBGPLB`, without a
historical date parameter. The daily-market overview has a documented `SEARCH_DATE`
but returns aggregates, not historical ST constituents. Current quote-list endpoints
are not historical anchors. Saved HTML/JavaScript and raw probes document these
distinctions; no invented historical parameter or access-control bypass was used.
The originating public-page Referer is preserved as part of request identity.

### Event index and independent oracle

All 137 candidates and 114 deterministic noncandidate controls were checked: 251
securities. Controls include at least 25 in each main/STAR × old/recent stratum,
plus later-delisted controls. Ordering uses a fixed SHA-256 seed, not random sampling.
The original Sina responses are retained; **no date is inferred from name ordering**.

| Oracle classification | Securities |
| --- | ---: |
| HAS_STAR_ST_HISTORY | 106 |
| HAS_ST_HISTORY | 29 |
| NO_ST_NAME_HISTORY | 23 |
| NAME_HISTORY_UNAVAILABLE | 93 |

There are 218 ST and 238 STAR_ST token occurrences, preserving duplicates. Of
these, 228 have accepted dated entry/exit evidence or a left-censored official
anchor followed by a dated exit. A dated entry alone does not prove an exit or
an ongoing right-censored interval. There are 93 securities with unclosed histories,
including 13 controls; zero such histories are in the provisional resolved subset.

Unexpected history appeared in 15 controls. Investigation fetched 1,346 relevant
CNINFO metadata records for the initial 88 flagged issuers (87 complete paginations;
one unresolved organization mapping), then selected only 324 additional possible
state-change documents on 225 publication dates. No unrelated PDFs were downloaded.
Issuer/day all-category SSE fallback is necessary: genuine older warnings were
classified as “其他”, while relevant pilot notices also occur under restructuring
or termination categories. Identical rows repeated across pages are deduplicated;
distinct records remain ambiguous. Issuer/day fallback pagination is bounded and
complete rather than silently accepting only page one.

The original 178 normalized events plus 164 newly accepted records give:

```text
EARLIEST_EVENT_DATE = 2005-04-26
LATEST_EVENT_DATE = 2026-06-23
OFFICIAL_EVENT_RECORDS = 342
PILOT_EVENT_RECORDS = 111
EVENT_LEDGER_COVERAGE = PARTIAL
SECURITIES_CHECKED = 251
CONTROL_NON_CANDIDATES = 114
HISTORICAL_ST_NAMES_FOUND = 218
HISTORICAL_STAR_ST_NAMES_FOUND = 238
EXPLAINED_BY_OFFICIAL_EVENTS = 228 token occurrences (including anchored left boundaries)
UNEXPLAINED_NAME_HISTORIES = 93 securities; 0 in provisional resolved subset
```

Post-2024-07-31 records investigate the oracle only; they never enter pilot replay.
The v3 parser requires exact security/date/subject reconciliation, PDF issuer/header
identity and the full disclosure subject in the PDF. An absent SSE short name may
use the exact CNINFO name only when verified against the PDF header. Older date
clauses must explicitly date the actual name change; an adjacent suspension date
cannot be selected. Unsupported/contradictory text remains unaccepted.

Examples of evidence requiring disposition rather than invented transitions:

- CNINFO `1216709184` has risk-implementation metadata but the actual PDF is a
  suspension/possible-termination notice. It is rejected as a subject mismatch.
- `1216993697` explicitly keeps *ST明诚 while adding a restructuring reason;
  it does not establish a new risk-class transition or a new effective date.
- A separate legacy “特别处理” query finds the official
  [600109 HTML disclosure 10443712](https://static.cninfo.com.cn/finalpage/2003-04-04/10443712.html),
  which expressly describes 2001-03-30 entry and 2003-04-07 exit. The corresponding
  SSE issuer/day metadata query returns zero rows. The HTML is preserved as
  contextual evidence, not silently inserted into the exactly reconciled ledger.
  An empty modern “风险警示” search is therefore not proof of no older ST history.

### Provisional replay, not dataset admission

The former blanket 100% exclusion policy is **not** used as the closure result.
The diagnostic replay separates 2,194 locally resolved securities from 93 residual
quarantines. These quarantines have not been certified as minimal, genuinely
unresolved security-date exclusions: legacy aliases and left/right boundaries still
need disposition. Merely quarantining all observed failures cannot prove the
candidate index complete, especially with unexplained control histories.

Therefore these are **provisional**, not approved admission/exclusion statistics:

```text
Pilot start after provisional quarantines:
NORMAL = 2057
ST = 11
STAR_ST = 5
EXCLUDED = 93
UNKNOWN = 0

Candidate classification in diagnostic replay:
TOTAL = 137
RESOLVED_NORMAL = 28
RESOLVED_ST_AT_PILOT_START = 1
RESOLVED_STAR_ST_AT_PILOT_START = 1
RESOLVED_TRANSITION_TIMELINE = 27
CONSERVATIVELY_EXCLUDED = 80
UNRESOLVED = 0 classification labels (not zero lifecycle gaps)

SSE_MASTER_SECURITIES = 2287
ADMITTED_SSE_SECURITIES = 0 authorized dataset admissions
PROVISIONAL_RESOLVED_SSE_SECURITIES = 2194
EXCLUDED_SSE_SECURITIES = 93 provisional quarantines
EXCLUDED_SECURITY_DAYS = 32097 provisional, of 853328 eligible days
EXCLUDED_UNIVERSE_PERCENTAGE = 4.066463% provisional
EXCLUDED_SECURITY_DAY_PERCENTAGE = 3.761391% provisional
```

No artifact is marked `coverage_certified=true` while the global index gate is
PARTIAL. `closure-intervals.json` retains diagnostic evidence states and
`evidence_replay_resolved`, but cannot be consumed as certified pilot coverage.
Zero authorized admissions is a **publication gate**, not a finding that all
2,287 securities must be excluded or that their baseline states are unknown.

### Validation and reproducibility

| Gate | Result and scope |
| --- | --- |
| PILOT_START_STATUS | PASS: official census, UNKNOWN=0 |
| ENTRY_EFFECTIVE_DATE | PASS for accepted events; exhaustive coverage PARTIAL |
| EXIT_EFFECTIVE_DATE | PASS for accepted events; exhaustive coverage PARTIAL |
| EVENT_LEDGER_COVERAGE | PARTIAL |
| HISTORICAL_NAME_CROSSCHECK | PARTIAL globally; no unexplained token in provisional resolved subset |
| DELISTED_RETENTION | PASS in master/replay audit, not a dataset audit |
| FUTURE_EVENT_LEAKAGE | PASS in pilot replay |
| INPUT_ORDER_REPRODUCIBILITY | PASS: reversed master/events and repeat audit |

The 382-session structural audit has zero interval gaps or overlaps. Reversing
the complete master input and event ordering reproduces the manifest byte-for-byte.
Backend: 343 offline tests passed; frontend: 74 tests passed. Ruff, format, application
mypy, strict four-script mypy, ESLint, TypeScript and production build passed.
Tests used isolated Docker containers; no strategy study or application-database
experiment was performed. No dependency or Git identity was changed.

Evidence is outside Git in `sse-st-pilot/closure-20260910` under the existing staging
root. It includes 2,577 raw/metadata/derived files, UTC retrieval metadata, PDFs,
HTML/JS/XHR snapshots, parser audits, name tokens and per-security diagnostics.

- Combined event SHA-256:
  `3c524bb1dfbc0c8e5be629ecf3e85f4d39f2babe6f4225d612245fc3ee6d2f65`.
- Canonical closure manifest SHA-256:
  `cc78e679b7ce82c69a9552a770229b35dd94ad029a325bf814b53387765c6b8c`.

From `backend`, with the existing preserved staging root in `STAGING`, offline replay:

```sh
python -m scripts.sse_st_closure \
  --master "$STAGING/security-master-pilot/sse-security-master.csv" \
  --candidates "$STAGING/sse-st-pilot/completeness-20260910/candidate-audit.json" \
  --output "$STAGING/sse-st-pilot/closure-20260910" \
  --audit \
  --prior "$STAGING/sse-st-pilot/completeness-20260910" \
  --snapshot "$STAGING/sse-st-pilot/snapshots/20260910T021848Z"
```

This offline command needs the preserved yearbook extractions and metadata; it
does not discover a new anchor or promote partial coverage. Optional acquisition
steps are `--lookups <preserved-cninfo-directory>` and
`--reconcile <preserved-cninfo-directory>`; neither is a dataset materializer.

```text
SSE_HISTORICAL_ST_RECONSTRUCTION = PARTIAL
PILOT_DATASET_CREATED = NO
AKSHARE_ACCEPTANCE = NOT PROMOTED TO PASS_FOR_PILOT
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY_RUN = NO
VALIDATION_STUDY_RUN = NO
OFFICIAL_OOS_RUN = NO
PR_MERGED = NO
V1.1.0_CREATED = NO
```

Dataset ID `cn-a-pilot-akshare-20230101-20240731-v1` remains unmaterialized. Its
13 dataset audits are NOT RUN; bar counts, observation failures and dataset hashes
are N/A, not zero. PR #12 remains OPEN on `feature/a-share-research-v1.1`.

**ONE remaining blocker:** independently closing the residual historical
event-index/lifecycle evidence, including the 13 unexplained controls, sufficiently
to justify interval-specific exclusions. The official pilot-start anchor is no
longer the blocker; provisional quarantine alone is not that missing proof.

## Residual-only closure follow-up (2026-09-10)

This follow-up preserves the previous evidence tree and processes exactly its 93
residual securities, with all 13 controls reviewed first. It does not repeat the
pilot-start anchor acquisition. Results are in `sse-st-pilot/residual-20260910`
under the existing external staging root; no market dataset is committed.

### Controls: all retained, all outside the pilot period

All 13 have genuine historical ST/*ST names; none was relabeled NORMAL or treated
as a false positive. Each terminal classification is `EVENT_OUTSIDE_RELEVANT_PERIOD`.
`control-terminal-audit.json` retains every token, issue, boundary, source URL,
retrieval timestamp and SHA-256. The detailed annotations are in `control-reviews.json`.

| Security | Official evidence bounding the risk-name history |
| --- | --- |
| 600109 | SSE 2001 table and CNINFO 2003 removal HTML |
| 600200 | Explicit *ST implementation 2025-05-06 |
| 600321 | 2019 STAR-to-ST and 2020 removal; conflicting older entry years not repaired |
| 600421 | 2012/2014 and 2018–2021 cycles; subsequent entry 2025-04-29 |
| 600636 | 2017/2018 cycle; subsequent entry 2025-04-29 |
| 600696 | Official 2001 interim report, 2017–2021 cycle, 2025-04-23 entry |
| 600702 | 2020-09-22 entry and 2021-05-19 exit |
| 600705 | 2006 entry, 2012 resumption and 2013-02-06 removal |
| 600811 | Explicit *ST implementation 2025-03-18 |
| 600837 | SSE pre-2001 ST/PT evidence and official 2002 restoration HTML |
| 605081 | Explicit *ST implementation 2025-04-29 |
| 605199 | Explicit ST implementation 2025-04-30 |
| 688022 | Ordinary versus expanded name distinguished; ST entry 2026-05-06 |

### Full residual results

```text
CONTROL_TOTAL = 13
CONTROL_EXPLAINED = 0
CONTROL_FALSE_POSITIVE = 0
CONTROL_OUTSIDE_PERIOD = 13
CONTROL_EXCLUDED = 0
CONTROL_UNRESOLVED = 0

RESIDUAL_TOTAL = 93
EXPLAINED_BY_OFFICIAL_EVENT = 66
NAME_HISTORY_FALSE_POSITIVE = 0
NON_RISK_NAME_CHANGE = 0
EVENT_OUTSIDE_RELEVANT_PERIOD = 26
CONSERVATIVELY_EXCLUDED = 0
UNRESOLVED = 1

HISTORICAL_ST_NAMES_FOUND = 218
HISTORICAL_STAR_ST_NAMES_FOUND = 238
EXPLAINED_BY_OFFICIAL_EVENTS = 233
OUTSIDE_PERIOD_TOKENS = 222
UNEXPLAINED_NAME_HISTORIES = 1
CONTROL_UNEXPLAINED = 0
NONCONTROL_UNEXPLAINED = 1

EXCLUDED_SECURITIES = 0
EXCLUDED_SECURITY_DAYS = 0
EXCLUDED_UNIVERSE_PERCENTAGE = 0
```

Control categories are mutually exclusive: `CONTROL_EXPLAINED` here means the
event-chain category, not all successfully dispositioned controls. The 233 token
explanations include official anchor-supported replay. The 222 outside-period
tokens are reported separately, not counted as accepted effective-dated events.
Duplicate token occurrences remain counted, so 233 + 222 + 1 = 456.

Source reuse closed most gaps. Targeted additions include official 2001/2006/2009
SSE tables, old CNINFO HTML bundles, issuer-header disclosures and issuer
restructuring documents with explicit former-name or dated-transition evidence.
An official dated former-name statement supplies an upper boundary only; its
undated internal name ordering never supplies effective dates. Non-risk renames
are documented at token level but aggregate to outside-period or event-chain
categories where the security also has genuine risk transitions.

Parser v4 separates ordinary names from expanded STAR-board names and rejects
quoted names containing nested quotation marks or semicolons. An independent
explicit ordinary A-share name label may resolve malformed quoted prose, but
conflicting labels are rejected. This corrects 688282's 2024-05-06 entry name;
the entry date and risk state were already in the previous ledger. Header checks
also recognize fullwidth asterisks and explicit company/stock-name header labels.
The resulting ledger contains 345 events, including the same 111 pilot-period
events. No old source snapshot was overwritten.

### Re-run coverage gate

| Gate | Result |
| --- | --- |
| PILOT_START_STATUS | PASS: official anchor unchanged |
| ENTRY_EFFECTIVE_DATE | PASS for accepted pilot events; exhaustive coverage still PARTIAL |
| EXIT_EFFECTIVE_DATE | PASS for accepted pilot events; exhaustive coverage still PARTIAL |
| EVENT_LEDGER_COVERAGE | PARTIAL |
| HISTORICAL_NAME_CROSSCHECK | PARTIAL: one exact token unresolved |
| DELISTED_RETENTION | PASS in master/replay, not a dataset audit |
| FUTURE_EVENT_LEAKAGE | PASS |
| INPUT_ORDER_REPRODUCIBILITY | PASS |

Replay checks cover 2,287 SSE securities, 382 sessions and 853,328 eligible
security-days. There are zero structural unknown states, event-chain gaps or
late-publication transitions. These are **evidence-replay checks**, not proof that
the remaining oracle gap is harmless. Every emitted interval retains
`coverage_certified=false` and `dataset_admission_authorized=false`.

No uncertain whole-pilot interval was invented. `exclusions.json` is empty;
`unresolved-source-gaps.json` separately retains the unresolved security and
searched evidence, with null boundaries rather than fabricated dates. Consequently
zero exclusions does **not** mean the complete universe is accepted.

Two fresh offline processes with different Python hash seeds reproduced the
324-file residual manifest byte-for-byte. Backend: **345 passed**; frontend:
**74 passed**. Focused parser/oracle regression checks, Ruff/format and strict
script type checks passed. The first bare-container full-suite invocation lacked
the test database configuration; the complete suite then passed using the
repository's isolated `compose.test.yml` database and fixtures.

- Event SHA-256: `842d95eff88bf51e60edbd9d85832404ab371dc0746f29e511bbc63d80d70afc`
- Residual canonical manifest SHA-256:
  `188c9ba2f076d334db13380aa304731e6c4f017a4ea7241f9d413c8ad9c0c8da`

Offline replay from `backend`, using preserved staging evidence:

```sh
python -m scripts.sse_st_residual \
  --root "$STAGING/sse-st-pilot" \
  --output "$STAGING/sse-st-pilot/residual-20260910" \
  --master "$STAGING/security-master-pilot/sse-security-master.csv"
```

```text
SSE_HISTORICAL_ST_RECONSTRUCTION = PARTIAL
PILOT_DATASET_CREATED = NO
AKSHARE_ACCEPTANCE = PARTIAL (NOT PROMOTED TO PASS_FOR_PILOT)
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY_RUN = NO
VALIDATION_STUDY_RUN = NO
OFFICIAL_OOS_RUN = NO
PR_MERGED = NO
V1.1.0_CREATED = NO
```

All 13 requested dataset audits are NOT RUN; dataset counts and dataset hashes
are N/A. This follow-up did not create, freeze or run a dataset or strategy.
PR #12 remains OPEN on the existing feature branch; Git identity is unchanged.

**ONE smallest remaining blocker:** an official SSE/CNINFO dated boundary for
600721's exact `ST百花村` token. Targeted old-name/issuer/date queries found the
official 2001-04-30 suspension disclosure (CNINFO 509408) and the SSE PT table,
but neither explicitly identifies the prior ST name. That proves PT history,
not the missing ST-name boundary. No date is borrowed from third-party name order.
