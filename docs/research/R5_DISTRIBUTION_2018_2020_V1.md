# R5 2018–2020 retained-source progress

All 8,590 queued source PDFs are retrieved and indexed. Original acquisition
completed with 8,558 PASS and 32 DNS errors. One missing-only recovery obtained
all 32; original failure receipts were preserved. No duplicate range worker.

External root: `/home/yuchen/data/research/staging/full-distribution-notices-v1`.

| Artifact | Canonical manifest SHA-256 |
| --- | --- |
| distribution-2018-2020-v1/source-manifest.json | a77411bbef44ef26f18312e05fc3ede63cdea16496cba70023f6b76b7825eac5 |
| distribution-2018-2020-dns-recovery-v1/source-manifest.json | 144ec4394991e26c383cc644f55a904e072064388966e3d9523aeb882be22236 |
| distribution-2018-2020-reconciled-v1/source-manifest.json | 562eebd3f233b08bc504f277d733b7cc25217441603c6ed29d738fb1051ff225 |

The shared date parser now supports the fixed official table order: share class,
record date, last trading date, ex date, cash/new-share date. It requires the
A-share row and last-trade placeholder, never reads B-share dates as A-share
dates, and retains conflicting labeled dates. Adjacent single-digit day / next
year text has an explicit boundary regression test. Earlier V5 development
reports had over-greedy day parsing; V6 supersedes them. None accepted events.

| Year | Date-linked groups | Exchange groups | V6 canonical SHA-256 |
| --- | ---: | ---: | --- |
| 2018 | 2,824 | 2,897 | a8bf4e179891eacf3a9b31197f84f2141b8504f948b4eb3409200262f603bc69 |
| 2019 | 2,619 | 2,684 | 0f435818901307c7799d95202efc7a50c5a1cac14113e030742a92c3a78c4083 |
| 2020 | 2,670 | 2,828 | b86f97ed293b7f74acf081c48177ad4862984e7322d49a5ba1ad609eed44adf5 |

Reports are `distribution-2018-2020-reconciled-v1/date-links-{year}-v6.json`.
Total 8,113/8,409; 296 gaps remain. Fifteen malformed-text parsing errors are
retained across the common input batch (not 45 distinct errors). Extraction gaps
are zero. Rights and structural actions remain separate classifications.
Date linkage is not economic-term, accounting or full event-census acceptance.
Remaining-years download continues. No dataset creation/freeze or strategy run.
