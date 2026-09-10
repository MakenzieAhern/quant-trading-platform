# PILOT-SCOPED ST CLOSURE AND DATASET MATERIALIZATION REPORT

Audit date: 2026-09-10. Scope: 2023-01-01 through 2024-07-31.
Branch: `feature/a-share-research-v1.1`. PR #12 stays open and unmerged.

## 600721

| Field | Result |
| --- | --- |
| LISTING_DATE | 1996-06-26, official audited SSE master |
| ANCIENT_ST_PT_EVIDENCE | CNINFO 509408, published 2001-04-30: PT百花村, suspension 2001-04-30, first special transfer 2001-05-11; SSE 2001 factbook p.56 corroborates PT. Exact earlier ST百花村 entry date remains unknown. |
| LATEST_AUTHORITATIVE_PRE_PILOT_ANCHOR | Official SSE year-end snapshot as of 2022-12-31, p.769; corroborates the effective-dated 2022-05-05 removal, CNINFO 1213213457 published 2022-04-29 |
| STATUS_AT_ANCHOR | NORMAL |
| STATUS_ON_2023_01_01 | NORMAL |
| PILOT_TRANSITIONS | 0 |
| STATUS_DURING_PILOT | NORMAL |
| ANCIENT_UNRESOLVED_EVENT_INTERSECTS_PILOT | NO |
| CLASSIFICATION | FULL_HISTORY_ONLY_UNRESOLVED |

The last accepted pre-pilot risk transition is *ST百花 → 百花村, effective
2022-05-05. The ordinary-name difference 百花村 / 百花医药 does not create an ST
transition. No later risk notice was found in the saved complete issuer-scoped
CNINFO query or the checksum-verified 74-page SSE category-31 ledger spanning
2022-01 through 2024-07. No contradictory later issuer-name observation exists
in the saved evidence. The year-end anchor agrees with the removal state.

Official documents:

- [2001 suspension notice](https://static.cninfo.com.cn/finalpage/2001-04-30/509408.html)
- [2022 removal notice](https://static.cninfo.com.cn/finalpage/2022-04-29/1213213457.PDF)
- [SSE 2023 yearbook](https://www.sse.com.cn/aboutus/publication/yearly/documents/c/10791349/files/85c1e61617f44332ac2f04dbbe5cd530.pdf)

## Authoritative-anchor rule and limitation

The ancient anomaly is reviewed as belonging to the old ST/PT lifecycle, not
dated from the order of undated names. `2001-12-31` in the review is a coarse
old-lifecycle bound supported by the PT evidence, **not an invented ST entry or
exit date**. The exact old token remains UNRESOLVED in the full-history audit.

A reviewed pre-anchor gap cannot invalidate a later authoritative, complete
security-state anchor by itself. The anchor must establish a recognized status
before the pilot, be known no later than its effective date, and have complete
subsequent coverage without contradictions. Later transitions still require
effective dates and compatible predecessor states. Missing, current-only,
post-pilot, contradictory or incomplete anchors fail closed. An arbitrary
undated token is not automatically exempted by this rule.

The yearbook is retrospective: its as-of date is **not** its publication date.
For 600721 the contemporaneously published 2022 removal establishes pre-pilot
knowledge; the later yearbook corroborates it. Nothing backdates the yearbook's
publication, infers the ancient entry date, or labels unknown history NORMAL.

The existing full-history classifier and its count are preserved. The explicit
pilot review applies only to 600721 / ST百花村, checks saved source hashes and
metadata-page completeness, and does not waive another security or token.
The existing replay/interval/completeness helpers are reused (Ponytail: no new
event engine or dependency). ST-certified intervals do not themselves authorize
market-data publication; `dataset_admission_authorized` remains false.

## Coverage

```text
FULL_HISTORY_UNEXPLAINED_NAME_HISTORIES = 1
PILOT_RELEVANT_UNEXPLAINED_NAME_HISTORIES = 0
FULL_HISTORY_ST_COMPLETENESS = PARTIAL
PILOT_ST_COMPLETENESS = PASS
SSE_HISTORICAL_ST_RECONSTRUCTION_FOR_PILOT = PASS

PILOT_START_STATUS = PASS
ENTRY_EFFECTIVE_DATE = PASS
EXIT_EFFECTIVE_DATE = PASS
EVENT_LEDGER_COVERAGE_FOR_PILOT = PASS
HISTORICAL_NAME_CROSSCHECK_FOR_PILOT = PASS
DELISTED_RETENTION = PASS
FUTURE_EVENT_LEAKAGE = PASS
INPUT_ORDER_REPRODUCIBILITY = PASS
```

All 2,287 SSE master securities remain represented, including delisted names.
382 sessions, 853,328 eligible security-days, zero unknown evidence states,
zero chain/temporal gaps. 345 accepted events, 111 in the pilot. No security
or security-day is excluded for this ancient anomaly. All 13 controls stay
closed. Original residual classifications remain 66 official-event explained,
26 outside-period, 1 full-history unresolved; none is silently relabeled.

## Reproduction and evidence

Run from `backend` with the locked Python environment. `ROOT` is the existing
external SSE staging directory, `MASTER` the accepted SSE master file:

```sh
python -m scripts.sse_st_residual \
  --root "$ROOT" \
  --pilot-source "$ROOT/residual-20260910" \
  --output "$ROOT/pilot-scope-20260910" \
  --master "$MASTER"
```

Current external output: `/home/yuchen/data/research/staging/sse-st-pilot/pilot-scope-20260910`.
Original closure and residual snapshots are untouched. New output includes
`600721-pilot-review.json`, full-history crosscheck, ST coverage intervals,
summary, empty exclusions, and `materialization-failure-manifest.json`.
Two full offline reruns produced identical audit-manifest bytes.

```text
SSE_SECURITY_MASTER_SHA256 = b4d930c0e3368f67237076588dd65088de4e77ebcd8187d3bc271d761d7c9972
ST_EVENT_SHA256 = 842d95eff88bf51e60edbd9d85832404ab371dc0746f29e511bbc63d80d70afc
PILOT_SCOPE_AUDIT_MANIFEST_SHA256 = 8043d9c7e84c8ec6631ee85dbd8d33d348ca0f06e6796d08c175ff0b46c93a6d
```

These are ST-audit hashes, **not a materialized dataset manifest or bars hash**.

## Materialization preflight

```text
PILOT_DATASET_CREATED = NO
REQUESTED_DATASET_ID = cn-a-pilot-akshare-20230101-20240731-v1
REQUESTED_COVERAGE = 2023-01-01 through 2024-07-31
INGESTION_STARTED = NO
PARTITIONS_WRITTEN = 0
```

The single smallest pilot-relevant blocker is the **unlocated existing accepted
effective-dated SZSE historical ST source, including its acceptance/checksum
lineage**. Checked the WSL research raw/audit/staging trees, repository including
ignored files, and Windows `.tmp-official` evidence. Existing SZSE security-master
and delisting evidence is present but is not an ST status timeline. The original
source-task lookup returned no readable task. No accepted SZSE ST artifact was
found; this is a source-recovery requirement, not evidence that the source never
existed or that ancient SSE history still blocks the pilot.

The prior AKShare market-path acceptance is user-confirmed context, not newly
repeated here. The existing ingestion script is BaoStock-only and writes a
four-security sample; it was not run or substituted. No full-universe AKShare
ingestion, resumable Parquet publication or resume/restart dataset audit is
claimed. Supply the existing accepted SZSE dated source location/manifest to
resume the source-authority preflight. Do not restart acquisition from zero.

Dataset observation counts and dataset hashes are NOT_AVAILABLE, not zero.
All following **dataset-level** audits are NOT_RUN_NO_DATASET:
SURVIVORSHIP, FUTURE_IPO, DELISTING_RETENTION, LOOK_AHEAD, ST_POINT_IN_TIME,
STABLE_ID, OHLC_VALIDITY, TRADING_CALENDAR, ADJUSTMENT_SEPARATION,
SUSPENSION_HANDLING, CHECKSUM_REPEATABILITY, INPUT_ORDER_REPRODUCIBILITY,
RESUME_RESTART. Passing unit/ST audits must not be substituted for these.

## Engineering validation

- Focused ST tests: 30 passed; full backend: 346 passed (includes v1.0 regression).
- Frontend: 74 passed; ESLint, TypeScript, production build passed.
- Ruff, format (173 files), mypy app (114 files), strict mypy for the three ST scripts passed.
- npm audit: 0 vulnerabilities; Python locked-dependency audit: no known vulnerabilities.
  pip-audit was installed only in a disposable container; project dependencies unchanged.
- PostgreSQL accepts connections; Redis PONG; all three Compose configurations passed.
- Isolated test database: Alembic head `2054636c61ed`, upgrade and schema check passed.
- GitHub Actions: see the PR's checks for the final commit; no merge performed.

```text
AKSHARE_ACCEPTANCE = PASS_FOR_PILOT
PILOT_A_SHARE_DATA_READINESS = BLOCKED_AT_SOURCE_AUTHORITY_PREFLIGHT
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY_RUN = NO
VALIDATION_STUDY_RUN = NO
OFFICIAL_OOS_RUN = NO
PR_MERGED = NO
V1.1.0_CREATED = NO
```

No strategy study or performance calculation was run. Routine offline regression
tests used fixtures only. Dataset Freeze Review has not been reached.
