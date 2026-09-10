# SZSE AUTHORITY RECOVERY AND PILOT DATASET REPORT

2026-09-10. Existing branch `feature/a-share-research-v1.1`, existing PR #12.
Initial HEAD `5340973081eae3c6b040bf3c76fa190b512fe012`; clean and synchronized.
Git identity and GitHub authentication: MakenzieAhern, unchanged. No newer state
was found at preflight. SSE and 600721 reconstruction were not rerun.

## Recovery evidence

OLD_ACCEPTED_ARTIFACT_FOUND = NO. The repository, its Git history, research raw,
audit and staging trees, test fixtures, README files, architecture/roadmap,
provider/readiness reports, Windows `.tmp-official` files and retrievable task
history did not yield the previously accepted SZSE ST artifact. The old checked-in
ST PASS statement concerned BaoStock `isST` capability, not a retained official
SZSE transition dataset. Some recent task-history entries expose no output items;
there is no claim that inaccessible history was exhaustively recovered.

NARROW_OFFICIAL_RECOVERY_PERFORMED = YES. This is a **new official download**, not
a recovered old timestamp or manifest. WSL retrieval failed at TLS negotiation;
normal Windows HTTPS retrieved the public export successfully. No access controls
were bypassed and no manual SZSE download is needed.

| Field | Verified value |
| --- | --- |
| SZSE_ST_AUTHORITY_FOUND | YES |
| SOURCE | SZSE 名称变更 / 简称变更, catalog SSGSGMXX, tab2; existing official 2022 yearbook baseline |
| SOURCE_FILES | New `windows-short-name-changes.xlsx` plus existing `szse-yearbook-2022.pdf`; sidecar metadata retained |
| RETRIEVAL_TIMESTAMP | Export: 2026-09-10T11:36:20.0458737Z |
| PARSER_VERSION | szse-dated-abbreviation-v1 |
| PROVIDER_VERSION | UNKNOWN; direct official download, no invented SDK version |
| SOURCE_DATE_COVERAGE | 1994-01-03 through 2026-09-10 |
| ACCEPTED_PILOT_COVERAGE | 2023-01-01 through 2024-07-31 |
| MANIFEST_PATH | `/home/yuchen/data/research/staging/szse-st-recovery-20260910/audit/manifest.json` |

Source URLs:

- [Official name-change page](https://www.szse.cn/www/market/stock/changename/index.html)
- [Official abbreviation-change XLSX](https://www.szse.cn/api/report/ShowReport?SHOWTYPE=xlsx&CATALOGID=SSGSGMXX&TABKEY=tab2)
- [Official SZSE 2022 yearbook](https://docs.static.szse.cn/www/market/periodical/year/W020230915392900565815.pdf)

The [AKShare source](https://github.com/akfamily/akshare/blob/main/akshare/stock/stock_info.py)
was a discovery aid identifying this public official export, not the ST authority.

```text
SOURCE_SHA256 = 3c62c9a74edc2849b370d555b67b98018c5c9af90bd9be0bd4de0de0279dece5
BASELINE_SHA256 = 20ba217d7f42543c29d0cc19ec0d8bd17e53d5338d8d71bc6317a041d8678101
NORMALIZED_NAME_EVENT_SHA256 = d045bdb3114aa43aa38a29b81154d884d491cc52d47a390dd882c0fe1925e4bd
NORMALIZED_ST_EVENT_SHA256 = ac8eb4314f1fc5296dd74dd612aad32ae156d963317d954a927827dbbf0924cc
MANIFEST_SHA256 = a87c14930b06419c20404fc862db92291a85ca7af20483ebec93b4c0e640baff
```

These are **SZSE source/audit hashes**, not a published Pilot Dataset manifest.
The normalized ST file contains state-changing rows, including delisting-period
transitions; the full normalized name file also retains ordinary name changes.

## Interpretation and acceptance

The export contains 7,478 dated rows and retains exited securities. The parser
normalizes 6,714 rows belonging to the audited A-share master (through 2026-09-09).
B shares and other out-of-master securities remain only in the original export.
It uses only `变更日期`, `证券代码`, `变更前简称`, `变更后简称`; the current-name column
`证券简称` is ignored. It never derives dates from undated name order.
The workbook incorrectly advertises an A1-only dimension: read-only extraction
resets dimensions to read the actual XML rows rather than silently retaining one
cell. The original XLSX remains unchanged (spreadsheet skill, read-only).

The existing checksum-verified official yearbook supplies 2,736 pilot-start
anchors, matched to the audited master. The remaining 155 securities are pilot
IPOs, initialized at their official listing dates under the existing ordinary-IPO
NORMAL assumption; no security is admitted before listing. Yearbook page 1442
(printed page 1427) was visually inspected using the PDF skill. Pre-pilot dated
changes agree with the baseline wherever present. No baseline or replay conflict
was found. Full historical completeness before the baseline is not claimed.

The yearbook and downloaded export are retrospective evidence. Their retrieval
dates are **not** backdated to historical publication dates. Individual publication
timestamps are UNKNOWN. This is effective-state reconstruction, not an
announcement-news timestamp dataset. Future-effective rows are removed in the
leakage comparison and do not affect any pilot state.

24 pilot changes into names ending in 退 are represented as DELISTING_PERIOD,
not NORMAL. This agrees with the [official 300799 disclosure](https://disc.static.szse.cn/download/disc/disk03/finalpage/2024-07-23/f89b1793-c2e7-402e-9c04-0ba5acf0ab23.PDF)
identifying 2024-07-08 as the start of its delisting period. The
[000004 removal announcement](https://static.cninfo.com.cn/finalpage/2023-06-27/1217139755.PDF)
likewise distinguishes publication on June 27 from removal effective June 28.
These are corroborating checks; the complete official export is the dated ledger.

```text
SZSE_PILOT_START_STATUS = PASS
SZSE_ENTRY_EFFECTIVE_DATE = PASS
SZSE_EXIT_EFFECTIVE_DATE = PASS
SZSE_FUTURE_EVENT_LEAKAGE = PASS
SZSE_DELISTED_RETENTION = PASS
SZSE_INPUT_ORDER_REPRODUCIBILITY = PASS
SZSE_HISTORICAL_ST_FOR_PILOT = PASS
```

Actual ST audit: 2,891 securities, 559 pilot name changes, 199 state changes,
zero missing anchors, zero chain gaps, zero anchor conflicts, zero lifecycle
boundary violations, zero non-session change dates, zero UNKNOWN security-days.
Two complete offline reruns gave identical manifest bytes.

The audited security-day counts are NORMAL 1,040,430; ST 16,649; STAR_ST 15,961;
DELISTING_PERIOD 384. **These are state-timeline counts, not market bars or Pilot
Dataset observation counts.** No raw OHLCV dataset has been materialized.

## Source authority preflight

| Authority | Result |
| --- | --- |
| SECURITY_MASTER | PASS: existing official SSE/SZSE files and their input manifest checksums verified |
| SSE_AUTHORITY | PASS: previous SSE/CNINFO/anchor acceptance and artifact checksums preserved; no reconstruction rerun |
| SZSE_AUTHORITY | PASS: new official dated export plus existing official baseline |
| OHLCV_AUTHORITY | Prior AKShare acceptance reported; current adapter identifies `stock_zh_a_hist(adjust="")` / Eastmoney, but the previously accepted route has not been independently rebound to its audit evidence |
| ADJUSTMENT_AUTHORITY | UNVERIFIED: exact accepted function/underlying URL, factor semantics and checksum-linked acceptance evidence not found |
| CALENDAR_AUTHORITY | Existing audited pilot calendar, 382 sessions, SHA-256 `314ec2633400880b1573a59508ac71930c834ec3f25ed59d6b55e70c0a917dd6` |
| BENCHMARK_AUTHORITY | Prior CSI300 acceptance reported; exact accepted price-history route/audit artifact not recovered |

SOURCE_AUTHORITY_PREFLIGHT = FAIL

The first concrete unresolved component is the previously accepted **audited
adjustment-factor authority**. The existing AKShare adapter implements raw daily
OHLCV only. Existing BaoStock sample factor-ingestion code does not by itself
establish acceptance for this pilot. No factor basis, endpoint,
provider version or prior acceptance is invented. Raw-route and CSI300 binding
remain unverified too; resolving this first component alone does not imply that
the final preflight will pass.

Preflight evidence:
`/home/yuchen/data/research/staging/szse-st-recovery-20260910/source-authority-preflight.json`
and the adjacent `materialization-failure-manifest.json`.
Preflight SHA-256: `c17cbccf24dca1373ff768585ebd8c3d4551f6b65dc8a0ac4b6dab9470a479dc`.

```text
PILOT_DATASET_CREATED = NO
REQUESTED_DATASET_ID = cn-a-pilot-akshare-20230101-20240731-v1
REQUESTED_COVERAGE = 2023-01-01 through 2024-07-31
INGESTION_STARTED = NO
PUBLICATION_ATTEMPTED = NO
```

Market observation counts, failed-security counts and dataset hashes are
NOT_AVAILABLE, not zero. No incomplete dataset was published. Resumable market
ingestion and atomic Parquet publication were not executed because the authority
precondition failed. Raw market files were not committed.

All dataset-level audits below are NOT_RUN_NO_DATASET:
SURVIVORSHIP, FUTURE_IPO, DELISTING_RETENTION, LOOK_AHEAD, ST_POINT_IN_TIME,
STABLE_ID, OHLC_VALIDITY, TRADING_CALENDAR, ADJUSTMENT_SEPARATION,
SUSPENSION_HANDLING, CHECKSUM_REPEATABILITY, INPUT_ORDER_REPRODUCIBILITY,
RESUME_RESTART. Unit and ST-source audits are not substitutes for these audits.

## Reproduction and engineering validation

Run in the existing locked backend environment; all paths are explicit inputs:

```sh
python -m scripts.szse_st_recovery \
  --source "$STAGING/szse-st-recovery-20260910/windows-short-name-changes.xlsx" \
  --master-root "$STAGING/security-master-pilot" \
  --calendar "$STAGING/sse-st-pilot/completeness-20260910/calendar/pilot-sessions.json" \
  --output "$STAGING/szse-st-recovery-20260910/audit"
```

The implementation reuses the existing canonical JSON/checksum helpers and risk
label normalization, following Ponytail. No provider SDK or dependency was added.
Tests cover ignored current names, state changes/removal, delisting periods,
pre-anchor unknowns, missing predecessors, same-day conflicts, duplicates,
input ordering, invalid dates/identities and source-checksum rejection.

Focused SZSE/catalog/master/provider tests: 23 passed. Full backend: 349 passed.
Frontend: 74 passed.
Ruff, format (175 files), strict mypy (app and new script), ESLint, TypeScript,
production build, npm audit and Python dependency audit passed. PostgreSQL and
Redis are healthy. Compose configuration checks passed for all three variants.
Alembic upgrade/current/check passed at `2054636c61ed`; no schema migration was
introduced, so an additional local downgrade was unnecessary. CI includes its
normal downgrade/re-upgrade check. Full backend includes v1.0 fixture regressions.

The stopped backend was started for validation: `/api/health` returned HTTP 200,
Quant Trading Platform v1.0.0, broker mode paper. The frontend container could
not bind port 5173: an existing unrelated Vite page responds there (main.jsx,
not this repository's main.tsx). That HTTP 200 is **not** a verified platform
frontend PASS. No unrelated process was stopped and no port/security settings
were changed. Frontend unit tests and production build passed independently.

## Final

```text
AKSHARE_ACCEPTANCE = PASS_FOR_PILOT (prior capability decision retained; composition preflight failed)
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY_RUN = NO
VALIDATION_STUDY_RUN = NO
OFFICIAL_OOS_RUN = NO
PR_MERGED = NO
V1.1.0_CREATED = NO
```

SINGLE_SMALLEST_REMAINING_BLOCKER = Recover the previously accepted audited
adjustment-factor authority's exact function/underlying URL, factor definition,
and checksum-linked acceptance evidence. No manual SZSE download is required.
No strategy study, performance calculation, freeze, live trading or ML/GPU work
was performed. Continue on the same branch and PR after that evidence is restored.
