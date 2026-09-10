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
