# Autonomous Quant Project Checkpoint

## 2026-09-14 integer retained-bonus subset and historical fee evidence

288 candidates use integer ratios, already retained 2010–2021 issuer notices,
and a next-accepted-session scheduled new-share listing. 169 supported events
(159 ratio-one, ten ratio-two), 119 unresolved candidates; remaining 7,119 oracle
rows are deferred/outside this subset, not assumed absent or excluded.
Policy BASIS_CONSERVED_RETAINED_BONUS unchanged. Source/date/master/instrument
checks, exact official/exchange ratio agreement, event serialization and hashes
required. Cash components remain separately reconciled; no double-crediting.
Ledger v2 SHA bf1ac5428237ff2a4980242a02637e1940b741b50948f7b24f260512fc61b703;
v1 event checksums preserved, reverse date-link-file ordering/idempotent publication
reproduces v2. Accounting regressions cover both admitted ratios at precision 6/50,
integer quantity and aggregate-basis conservation, unchanged cash, no order events.
598 backend tests plus Ruff/format/mypy PASS. Full census/actual tradability NOT PASS.

CSRC 2012-08 bulletin PDF retained, SHA
b556e44b3784d03922c04cb5b77e9f5fcf9bbec9439b0e20ca9512f94c161bc2.
PDF page127 / printed114 visually reviewed because text extraction yields glyph
names. Article dated 2012-08-02, transition 2012-09-01. Printed transfer denominator
conflicts with face-value evidence; full investor fee/broker component/minimum
not established. Review SHA 16cb65e50bdf0fa5b71474c1f283c5bbadbf206216615ea03218c52b82f38767.
Two HTML retrieval failures preserved (DNS, HTTP403); no HTML retry. Separate annual
report timeout recovery returned non-PDF and is rejected, no further retry:
d9e4506d37357440c60016218a802e195b3fbd5adc4f792294bcd56b77528762.
No historical fee-model change, full dataset publication, strategy or merge.

## 2026-09-14 remaining restoration parser review

Coordinate extraction removes overprinted glyphs from 59806624 and 60050789
without changing source bytes; both now yield provisional dated STAR_ST-to-ST.
Optional A-share wording and explicit next-day phrases resolve three more
document records. 600633 normal relisting requires an explicit exchange approval
removing risk treatment; normal-looking names alone remain rejected.
Restoration v3: 16 provisional documents, four unresolved, SHA
8d366f27e5cf4de171ad38f4dc19da360a9feb17d809dba30631d109bbb4f021.
Full v12 preserves all prior records: 705 provisional / 872 parser unresolved /
three metadata variants, SHA 5d37f9da5cd7e09f821093fc1af0d1162db302d5530d744b92b1bf26c4ca2b38.
325 chains / 92 gaps, zero conflicts, reverse-order PASS; not full authority.
600057 PDF header visibly prints 600870 while body and official metadata say
600057. Header guard remains intact. Targeted original SSE mirror denied access;
no retry, manifest e83f6b5dae8dda6446aba118766c8d5f0c0b2b9b9f50187d899c13d1c3338428.
Windows-to-WSL hard-link publication is unsupported; alternate extraction was
published locally on Windows then imported with the existing WSL immutable writer.
No source overwrite or replacement fallback. 596 tests PASS; intentional fixture
punctuation lint annotation added. ed209a9 CI 34813352211 SUCCESS. Continue R5.

## 2026-09-14 2021 cash and restoration recovery completed

2021 snapshot 3,187 PASS / 18 DNS failures; all 18 recovered separately.
Reconciled 3,205-PDF manifest SHA
328436fd05258da983c276c4bf968bdd9780112981f0bbc3fcf5b3a0f17a7c2c.
Date links 2,859/3,139, four parsing errors, zero extraction gaps; SHA
24a5ab92080b5d7927d4b9d26e7040a1d2797c93362083899e8a5d03d7c6ef8c.
Cash 2,420 supported / 688 unresolved, ledger SHA
b022439bb1784333004eaaaa9126706d532ab4b58a0c749e3e850122e435f7bd.
Total twelve-year bounded cash 20,683/3,809; full census remains PARTIAL.
After confirmed DNS recovery, one missing-only SSE retry resolved 17 documents
across 16 failed issuer/days; three earlier cached matches retained. Recovery SHA
9ce1657ab1ec59758b880c75273d303be68ea4c4ca2c9ade1329924c3a12ad55.
Failed fetch metadata is retained as a gap, not opened as a nonexistent response;
regression covers this checkpoint recovery path. Original failures unchanged.
Narrow relisting parsing requires explicit dates and matching first-day NST/later
ST names. Ten provisional events; ten documents remain unresolved. Union SHA
5ac88e9c4f1d795f5223165fde392e1dc5116d9b513313f9a1c963e8f25b18cd;
all prior 689 event records preserved, total 699. Chain v3 has 324 chains, 95 gaps,
zero conflicts; SHA 884352702f607f6559cdbb0e6dfac276b2011b07247509fe62f99a44e954b2a7.
18 year-window Tencent controls returned target rows without duplicate dates;
outside-year rows require explicit filtering. Not accepted full raw authority.
Probe SHA 56911f5929916c06b6c606fbc909fea6fae19dca781b07777789c5b0a7c30c5f.
596 backend tests/quality PASS; e4e5bbf CI 34812475961 SUCCESS. Continue R5.

## 2026-09-14 restoration coverage and chain diagnostic

Fact-book restoration inventory: 17 explicit dated rows, no accepted events;
SHA 5a67fdb7cde1757e975ddb33fa545406bd10b32583078205da1aa40d2a907ad0.
CNINFO routing: 38 leads, 20 selected documents, 18 other leads retained.
PDF manifest SHA b089eb8e259b46178ec1731431fc221d65c8a7bd30c4596b2fdba02605aaeea4;
all 20 retained/indexed, zero PDF retrieval failures. Separate SSE batch has
three cached exact matches and 16 explicit DNS failures, not source acceptance;
manifest SHA 88ff4194d02dc8daa470d4d568c737913fe327914197e4221efe26e3aaaaabd3.
No repeated DNS retry or denied static-mirror retry. 600057 PDF 59855729 prints
600870 in its header but 600057 in body: identity conflict remains explicit.
600385 correction 1200096190 changes first-day intraday suspension rules, not
the restoration date/name; retain correction SHA
e679eb09cc7a4b2fb4b024489d0f32d5fac713174b3420aeec35e8105b6bff17.
Chain diagnostic v2 SHA 6b8e5516183881a0382ac8de04fb3d16dabc4ffafa21ebce20fb846ec3ddd95c:
322 chains, 102 missing-transition gaps, zero same-day conflicts, zero unmapped
events; 15 pre-target observations counted separately. This does not certify
no-event securities or daily states. Reversed event order check PASS.
594 backend tests and all quality checks PASS; 76d4851 CI 34810743949 SUCCESS.
Existing distribution worker continues. No full publication/freeze/studies/merge.

## 2026-09-14 source-oracle and ST constraint continuation

Provisional SSE transitions 689; 868 parser cases and three metadata variants
remain unaccepted. Full-v8 SHA 8bdb95ce9d11060909315d056bddadc555bbe081989674bbb4cca90ea8728e22.
v7/v8 preserve prior event rows; v9 parser adds document-bound reviewed title
equivalence only. Wrong document/code remains rejected. Full backend 593 and
Ruff/format/mypy PASS. Prior 220d75c CI 34809275007 SUCCESS.
Earlier 683-transition plus 345-retained-evidence chain diagnostic: 321 chains,
103 gaps, zero same-date state conflicts; 15 pre-target observations retained
outside target. Diagnostic is not complete daily state/authority acceptance.
Source-mirror gap probe: two access-denial responses, one timeout; no further
mirror retries. Existing CNINFO evidence preserved. Mirror manifest SHA
9cf3c0d2ca8dbb87c5d1ed0fc366efe9cb11b7135b78e344350de49bb8e30d7f.
Bonus oracle/lifecycle/boundary joins reuse accepted source tables and master;
no accepted Pilot recomputation. See bonus report. Four bounded Tencent requests
show 640-row truncation and empty 5,000-count daily payloads; empty is not proof
of missing history. Root full-raw-coverage-v1/long-range-count-probe-v1;
manifest SHA bd67f0a9307123698bc9be9f78a571df012af7e21866b835465b1cbc561fe8f0.
No strategy, full dataset publication, freeze or merge. Continue independent R5.

## 2026-09-14 2017 cash and missing-case parser continuation

2017 source snapshot verified against its 2,564 queue URLs and PDF hashes.
Date links 2,451/2,538; cash supported 2,241 / unresolved 233. Eleven processed
years total 18,263 supported / 3,121 unresolved cash groups, full census PARTIAL.
Source/date/cash manifests are in distribution-2017-snapshot-v1; cash SHA
d508f0fd10d572f6fa6942ad564e1483b7a3650a06333872d7bbf9d68c8e184a.
SSE whitespace/leading escaped-newline normalization resolves two metadata
matches; all 1,555 earlier exact matches preserved. Homophone and old/new-name
differences remain explicit review cases, not fuzzy matches. Parser v6 accepts
only direct resumption/name clauses with company/A-share prefixes: 677 provisional
transitions, 880 parser gaps, three metadata gaps. Full-v4 SHA
03509aa33b03694fcc571efb0731d584d2cb2500755d84680794941b79df358f.
Full-v3 intermediate matcher regression preserved; punctuation boundaries restored
before publication of v4. 600392 annual table says May 3, 2012; retained issuer
notice says May 2. This date conflict remains unresolved, not silently preferred.
Bonus accounting regression failed under ambient precision and missing explicit
basis. Fixed at shared portfolio path using existing context and original basis;
no fractional-share choice or strategy run. 592 backend tests/quality PASS.
Prior milestone CI 34808558506 SUCCESS; PR12 remains OPEN. Continue independent R5.

## 2026-09-14 SSE pagination and alternate PDF extraction

52 repeated-page failures recovered using beginPage and grouped result counts;
all original failures preserved. Exact metadata 1,555 / unmatched five.
133 identity/header failures received separate coordinate-deduplicated text;
16 additional provisional transitions, total 660 / parser unresolved 895.
No accepted event or full authority promotion. Earlier 644 records unchanged;
reverse-input normalization PASS. Windows immutable writer now removes its
temporary hard link before applying Windows read-only attributes; actual Windows
idempotence/replacement rejection check PASS, existing Linux regression PASS.
590 backend tests, Ruff/format/mypy PASS. CI 34806671415 PASS for prior 63353cc.
Nine fact books retained/indexed; 389 dated name rows (366 A-code), 105 risk
changes require event reconciliation. No undated-name ordering or backdated
source publication. External hashes in ST report/state. Continue independent R5.

## 2026-09-14 ST PDF source batch and bounded parser continuation

1,560 selected ST PDFs retrieved/indexed; zero retrieval failures. SSE metadata
corroboration continues with cache reuse and issuer/day-only queries. Snapshot
193 explicit transitions remain provisional, not complete ST authority. Thirteen
additional dates use directly connected resumption/name-change clauses; existing
180 records preserved. Backend 588 / quality checks PASS. See ST extension report.
All 128 distribution JS summaries identified as retained-PDF companions; no new
event or retrieval. Existing economic/date gaps remain, including 300137 typo.
CI 34805678054 PASS at 8a34438. Full dataset not created/audited/frozen; no studies.

## 2026-09-14 six-year cash batch continuation

2011–2016 source reconciliation completed: 11,551 PDFs / 128 JavaScript summaries,
zero remaining retrieval failures after 35 separate transient recoveries.
Existing date and gross-cash parsers produce 8,134 additional supported events,
1,547 unresolved groups. Combined bounded ten-year result: 16,022 supported /
2,888 unresolved. All event serializations validated by the existing pipeline.
No code, policy, accepted Pilot, strategy or freeze change. Full census PARTIAL.
See ../research/R5_CASH_DIVIDEND_BATCH_V1.md for immutable hashes.

## 2026-09-14 missing-only factor and ST source extension

Cached factor evidence supplies 5,301 full-target code-interval baselines;
135 missing intervals were fetched separately using the existing parser and
bounded source helper. All have a baseline, including old code aliases, but
baseline presence does not certify full factor completeness or corporate-action
alignment. No accepted Pilot artifacts were changed. External manifests and
checksums are recorded in project_state.json.

346 ST keyword/month windows now have complete query responses; one HTTP 502
was recovered in a separate immutable checkpoint. 6,724 unique leads remain
source leads. 1,560 transition PDFs are queued, with warnings/applications and
unexpected attachments retained separately. Full ST authority remains PARTIAL.
2011–2016 distribution receipts form a verified 11,679-row snapshot; 35 transient
failures are being retried separately, and 128 JavaScript summary attachments
are not treated as full PDF evidence. Indexing and other queues continue.
CI 34804569207 SUCCESS for cc4b7b9; no domain code changed in this continuation.

## 2026-09-14 SSE starting anchor / cash missing-only extension

SSE official 2009 yearbook capital table supplies 860 starting risk names; a split
S/newline/T cell is normalized, with regression test. Three paused issuer rows
visually checked. PDF and extraction hashes preserved; publication date unknown,
not backdated. Separate ST metadata collector has 173 missing months × two keyword
queries, skips accepted 2023-01..2024-07, verifies counts/order and keeps failures.
Cash v2 adds 186 events while reusing 7,702 accepted rows and preserving their IDs.
586 backend tests/Ruff/format/mypy PASS; prior milestone CI 34803545764 SUCCESS.
See ../research/R5_SSE_PRESTART_ANCHOR_V1.md and cash report continuation.

## 2026-09-14 exact cash-dividend batch

7,702 supported cash events / 1,527 unresolved source groups in four audited source
years. No rounded-price tolerance, net/gross substitution or ambiguous document
discard. Reuses existing CorporateAction/PortfolioEngine; no new domain policy.
1/81/100-share accounting regression checks conserve quantity/basis and create no
order/fill; source-record and event serialization/checksum checks pass. All 7,005
2018–2020 events reproduce under reversed evidence/master order. 584 backend and
78 frontend tests, lint/type/build PASS. See ../research/R5_CASH_DIVIDEND_BATCH_V1.md.

## 2026-09-14 2018–2020 source recovery and date-table links

All 32 DNS failures recovered once in a separate batch; 8,590/8,590 source PDFs
now verified/indexed. Original receipts and manifest remain unchanged. Fixed
official A-share table columns increase date links to 8,113/8,409 groups.
296 gaps and 15 malformed-text parsing errors remain explicit, not accepted
events. No economic terms promoted. See ../research/R5_DISTRIBUTION_2018_2020_V1.md.

## 2026-09-14 SZSE interval replay

3,028 candidates / 7,876,813 lifecycle security-sessions; no UNKNOWN, no IPO
old-state conflicts, no future-event or ordering differences. Existing accepted
Pilot IPO initialization reused explicitly. Overall full authority still PARTIAL.
Probe v8 hash is recorded in project_state.json. Prestart milestone CI 34802149128 PASS.
2018–2020 download manifest completed: 8,558 PASS, 32 DNS failures. The failed-only
32-document recovery has a separate immutable queue; original receipts preserved.

## 2026-09-14 SZSE prestart risk-state corroboration

Reused official dated export and yearbook; only 16 missing trading-table issuers
received targeted 2009 metadata queries. All 32 PDFs PASS; all 16 headers agree
on STAR_ST. 820 yearbook names agree independently. No current-name backfill,
future event use or assumed NORMAL gaps. Full ST authority remains PARTIAL.
580 backend tests PASS; follow-up formatting/type checks recorded at milestone.
See ../research/R5_SZSE_PRESTART_CORROBORATION_V1.md. No stop gate reached.

## 2026-09-14 targeted 2010 distribution coverage

45 issuer/date metadata windows complete; 75 plus seven document leads acquired
or reused, no failures. Reconciled source union: 1,179 documents. 14 reviewed date
ambiguities are source-pinned and exchange-corroborated, including visual PDF QA.
1,056 date links + three existing rights + one structural queue = 1,060 groups.
No ordinary dividend events promoted. 16 focused tests PASS; instrument CI PASS.
See ../research/R5_DISTRIBUTION_2010_DATE_CLOSURE_V1.md. R5 continues.

## 2026-09-14 candidate instrument extension

All 251 missing candidate classifications supported; accepted 5,181 facts reused.
Two connection-reset failures recovered with targeted requests, original receipts
preserved. Prior 600190 correction reused from frozen v2 evidence, not reopened.
15 focused source tests PASS; baseline milestone CI 34798601016 PASS.
See ../research/R5_INSTRUMENT_EXTENSION_V1.md. Independent R5 work continues.

## 2026-09-14 baseline membership source closure

Both exchange baseline membership cross-checks PASS; 18 directory omissions now
have reviewed annual-report identity evidence. 28 targeted PDFs retained, zero
retrieval failures. CNINFO keyword/category false negatives and PDF text issues
are documented, not interpreted as absent issuers. Backend 576 PASS; lint/type PASS.
See ../research/R5_MASTER_BASELINE_CROSSCHECK_V1.md. Full acceptance remains partial.
Previous milestone CI 34797320955 PASS. R5 independent queues continue.

## 2026-09-14 merger suspension batch

600553/600991 retained evidence and three targeted 601299 official notices close
the prior three chronology gaps under approved policy. Nine reviewed candidates
supported, full-market census still incomplete. Source audit manifest:
62f5d5a3068cb1ee02e9d36523e08f58e1d5aa5e4454507d7db8fc028009b676.
31 focused tests PASS. Previous milestone CI 34796787068 PASS. Workers continue.
See ../research/R5_MERGER_SUSPENSION_BATCH_V1.md. No new gate or studies/merge.

## 2026-09-14 retained merger batch

Four official implementation records normalized; nine reviewed candidates now have
six supported events and three retained gaps. Full census is not established.
Source hashes and lifecycle corroboration PASS; two metadata-only cash-offer unknowns.
Backend 571 / frontend 78 PASS; frontend lint/build and backend lint/type checks PASS.
See ../research/R5_MERGER_BATCH_CLOSURE_V1.md. R5 continues; no new approval gate.

## 2026-09-14 runtime recovery

WORKER_RECOVERY_STATUS=PASS_RESUMED_DURABLE_RECEIPTS; DUPLICATE_WORKER_PREVENTED=YES.
No live old workers, PID/lock files or temporary manifests found. Verified 44,504
unique, disjoint queued URLs and all processed PDF hashes. Two existing batch
names resumed from 1,977 and 584 processed receipts respectively; 2010 not restarted.
14 focused local source tests PASS. Docker was not started; Desktop launched
without reset/deletion for the isolated full suite. No research acceptance changes.
See .research/reports/r5-worker-recovery-20260914.json for the timestamped snapshot.

## R5 retained distribution notice recovery

2010: 1,113 PDFs indexed, one explicit HTTP 502 failure. 2018–2020: 8,590
document leads downloading with source/checkpoint reuse. Missing-date-range
recovery reuses retained pages; 2011/2012 reconcile to original annual totals.
566 backend tests/quality checks PASS; recovery focused source suite 11 PASS.
See ../research/R5_DISTRIBUTION_NOTICE_RECOVERY_V1.md and external manifests.
R5 RUNNING_BATCH_CLOSURE; no new gate, dataset creation/audit/freeze or studies.

## R5 distribution row audit continuation

20,346 candidate groups, three retained B-only rows, no normalization errors.
Eight cash collisions reconciled to official issuer PDFs with exact gross
ordinary-holder amounts; full source-table precision is not accepted automatically.
Four holder-class differences and four combined-period distributions map to the
approved cash policy. Synthetic ex-price reference cash is not shareholder cash.
559 backend tests and quality checks PASS; prior aa372ac CI PASS.
R5 continues independent yearbook rights-census checks; no human gate or study.
Evidence: ../research/R5_FULL_RANGE_SOURCE_EXTENSION_V1.md.

## Current: R5 exchange distribution census; batch closure continues

All 192 official SZSE monthly tables retrieved: 23,682 source rows; all 74
rights candidates match the existing official event ledger, no source-only or
ledger-only entries. SSE eight cash collisions resolved to exact issuer terms.
These are source/census checks, not full cash precision or dataset acceptance.
CNINFO API probe is supplementary only: average cash fields and missing delisted
history cannot replace official issuer evidence. 561 backend tests and quality
checks PASS. See ../research/R5_EXCHANGE_DISTRIBUTION_CENSUS_V1.md.
R5 RUNNING_BATCH_CLOSURE; no new human gate, no dataset creation/audit/freeze.
Remaining independent source and accounting queues continue; no studies/merge.

## Prior milestone: R5 full-range source extension

Calendar: 3,886 target sessions verified. Official CSI300 close history aligns
exactly, matches all 382 accepted Pilot closes and passes deterministic Parquet
replay. Accepted Pilot and raw stock authorities are unchanged.
SSE distribution source tables collected: 17,920 dividend rows / 2,500 bonus
rows including B-only records; source rows are NOT accepted accounting events.
Exact rational merger flooring implemented without changing accepted event IDs.
558 backend / 78 frontend tests and quality checks PASS.
See ../research/R5_FULL_RANGE_SOURCE_EXTENSION_V1.md.
R5 remains RUNNING_BATCH_CLOSURE, no human gate or new methodology blocker.
Full dataset CREATED/AUDITED/FROZEN=NO; remaining source queues continue.

## Prior milestone: R5 rights batch reconciled

153 identified rights events / 142 securities now reconcile to official direct-subscription
notices; material unresolved in this identified queue = 0, metadata-only incomplete = 149.
Full exchange census remains PARTIAL. Source documents and code-transition candidates
are not full-dataset acceptance. 554 backend tests and quality checks PASS.
See ../research/R5_BATCH_SOURCE_CLOSURE_V1.md and
.research/reports/r5-batch-source-closure-v1.json. R5 remains RUNNING_BATCH_CLOSURE;
no human gate, no full dataset creation/audit/freeze, no studies, merge or release.

## Prior milestone: consolidation decision resolved

The approved 15-class policy catalog is frozen (not the dataset):
`CORPORATE_ACTION_POLICY_MATRIX_V1`, file SHA-256
`3784d6817fb7ab30081e57d9693bc1ac7adbfbaccebe200e2903e7021d8a0352`.
600381 consolidation June 25 and separate surrender June 30, 2014 have source-byte,
Decimal accounting, replay and persistence checks. Source receipt:
`dcfa8e2a408629a0be0b8ab9b101ab08206642eaaae621cc5412b94f96a93383`.
Its prior human methodology blocker is RESOLVED. R5 remains RUNNING_BATCH_CLOSURE;
no new human approval requested. Rights, merger/restructuring, master and remaining
full-period authority queues remain independent. Document leads are not accepted events.
Full Dataset CREATED/AUDITED/FROZEN=NO; safe start NOT_ESTABLISHED. No studies,
profitability inspection, merge or release. Accepted Pilot v2 remains unchanged.
The retained merger/capital-adjustment source worker checkpoints under external
`full-merger-v1/batch-v1`; unavailable sources cannot silently pass.

## Historical checkpoint (superseded): 600817 PASS; former 600381 gate

600817 approved net pass-through accounting/source/replay/persistence PASS; old blocker RESOLVED.
R5 reviewed21 further retained-queue plan documents and two600381 implementation/reference PDFs.
600381 ordinary100 ->16 share consolidation occurred2014-06-25, distinct from later12% surrender.
Historical aggregate basis treatment of the consolidation is not covered by accepted policies.
SINGLE_SMALLEST_BLOCKER=RESTRUCTURING_SHARE_CONSOLIDATION_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600381.
HUMAN_APPROVAL_GATE=R5_RESTRUCTURING_SHARE_CONSOLIDATION_ACCOUNTING;
HUMAN_APPROVAL_REQUIRED=YES; HUMAN_SOURCE_INPUT_REQUIRED=NO.
544 backend/78 frontend tests; Ruff/format/mypy and migration checks PASS.
Full dataset CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No studies, profitability review, PR12 merge or release. No background worker.
Report: ../research/PASS_THROUGH_R5_CHECKPOINT.md. Resume preserved queues after decision.



## Current:600817 approved net pass-through PASS; R5 RUNNING

Human decision b42ec74db5f29f3a1434b96bdc04f9833dcb572a20198ee5b6fe69e3fe7293d6
approves CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1 /
NET_PASS_THROUGH_NO_BASIS_ALLOCATION. Five official PDF receipts verify25% bonus,
registration2012-07-31, transfer2012-08-01, unchanged originals and suspension.
Generic metadata-only accounting, persistence and raw-price separation checks PASS.
Old600817 methodology blocker RESOLVED; HUMAN_APPROVAL_REQUIRED=NO.
R5 resumes retained census/source queues; no prior acceptance is repeated or changed.
Full dataset CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No Development/Validation/OOS, profitability inspection, PR merge or release.
Evidence: ../research/RESTRUCTURING_PASS_THROUGH_V1.md.



Final current validation:529 backend/78 frontend tests, Ruff/format/mypy PASS.
600817 source bytes and receipt verified; manifest
8e3f61bf12d377b225c042aefdf3acb1342db7138cab6caad75f8f59ec9a23d0.

## Current:600462 PASS; R5 new600817 pass-through methodology gate

600462 boundary and ceiling convention accepted/tested; original registry source
blocker RESOLVED. Historical timestamp/fraction facts remain NOT_PUBLICLY_EVIDENCED.
R5 resumed2010 merger leads and the preserved capital-adjustment queue.
600817 official notices establish temporary25% bonus credit then transfer to the
administrator, while original shares remain. Gross bonus/surrender versus net
issuer-level pass-through would allocate basis differently. Neither selected.
SINGLE_SMALLEST_BLOCKER=RESTRUCTURING_BONUS_PASS_THROUGH_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600817.
HUMAN_APPROVAL_GATE=R5_RESTRUCTURING_BONUS_PASS_THROUGH_ACCOUNTING;
HUMAN_APPROVAL_REQUIRED=YES; HUMAN_SOURCE_INPUT_REQUIRED=NO.
528 backend tests/Ruff/format/mypy PASS. Full dataset CREATED/AUDITED/FROZEN=NO;
safe start/full coverage NOT_ESTABLISHED. No studies, profitability review or merge.
Report: ../research/600462_CONVENTION_R5_CHECKPOINT.md.
No background worker. Resume preserved queues after this new methodology decision.

## Current:600462 approved boundary/fraction convention PASS; R5 RUNNING

Human decision6f14546633e87d4a3dfec3564d92e03de07b6778b0636e4f86193994772f03b1
approves FIRST_POST_EVENT_TRADING_BOUNDARY_V1 and CEIL_SURRENDER_FLOOR_RETAINED_V1.
Historical registry date and official fraction rule remain NOT_PUBLICLY_EVIDENCED.
Research application before2012-11-19 resumed tradable Bar; no future-price input
to quantity/basis. Generic ceiling and zero-retained accounting/replay/persistence PASS.
600462 source blocker RESOLVED_BY_APPROVED_CONVENTION, not by fabricated historical facts.
18 source PDF receipts verified; flat-start2010 quantity lattice remains100*n before
surrender, so reachable fractional/positive-zero-retained cases0, economic bound0.
Edge stress Q1/6/101 separately tests ceiling; not historical strategy holdings.
528 backend tests/Ruff/format/mypy PASS. No schema migration needed for JSON audit extension.
HUMAN_APPROVAL_REQUIRED=NO; HUMAN_SOURCE_INPUT_REQUIRED=NO; STATUS=RUNNING.
Resume preserved R5 queues. Full dataset CREATED/AUDITED/FROZEN=NO; coverage/safe start
not established. No studies/profitability inspection/merge/release.
Review/lineage: ../research/600462_APPROVED_CONVENTION_REVIEW_V1.json.
Evidence manifest a4d49ac37c9bff57485be7087122707ad0e03b788cfc39d776e509fdb00fd83a.

Registry recovery validation:520 backend tests, Ruff/format and mypy119 files PASS.
Frontend unchanged; no rerun this turn. No production accounting code changed.

## Latest registry recovery: trading boundary and aggregate totals verified

Official first post-event trading boundary2012-11-19 established; exact registry
book-entry/daily valuation mutation date remains unverified. Actual aggregate
share-capital reconciliation PASS/difference0; plan-to-actual gap28163 and
non-exhaustive exception arithmetic residual116 remain distinct.
Fractional rule NOT_EVIDENCED; generic Portfolio odd quantities reachable,
actual600462 historical reachability NOT_ESTABLISHED (round-lot-only subset safe).
16 official PDF receipts/checksums reverified;3 targeted PDFs added, no restart.
Report: ../research/600462_REGISTRY_RECOVERY.md; manifest
231c167a765e79673cdb5517ec95e4b7a27eecdc53c4451d7014fe63ae3e0aa2.
Original source blocker remains. No new methodology approval; human source input YES.
Approved accounting and all prior acceptance decisions unchanged; no formal studies/freeze/merge.

## Current: partial-surrender policy implemented;600462 source evidence unresolved

CN_A_MANDATORY_PARTIAL_SHARE_SURRENDER_POLICY_V1 APPROVED.
Generic exact-whole-quantity accounting/replay/persistence PASS; historical600462
admission PARTIAL. Ordinary nonexempt20% surrender and separate30% issuer issuance
verified; no direct holder compensation. Do not apply the issuance fractional rule.
Registry effective date and surrender-specific allocation remain unverified after
targeted plan/progress/court/annual-report review. No historical date is invented.
SINGLE_SMALLEST_BLOCKER=PARTIAL_SURRENDER_REGISTRY_EXECUTION_EVIDENCE_UNVERIFIED:CN-A:SSE:600462.
This is source recovery, NOT a repeated basis approval or established new fractional mechanism.
HUMAN_APPROVAL_GATE=NONE; HUMAN_APPROVAL_REQUIRED=NO; HUMAN_SOURCE_INPUT_REQUIRED=YES.
518 backend/78 frontend tests PASS; source replay/Ruff/mypy/schema checks PASS.
Prior Pilotv2/R4v2, rights/demerger/merger/source acceptances remain unchanged.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/full coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR12 merge or release.
Report: ../research/PARTIAL_SURRENDER_CHECKPOINT.md.
Resume preserved R5 source queues after registry evidence recovery; do not restart.
Next dataset gate remains GATE_FULL_RESEARCH_DATASET_FREEZE, not reached.

## Historical checkpoints below (superseded)

## Current: 600005 zero-whole PASS; R5 partial-surrender methodology STOP

Approved WRITE_OFF_PARENT_BASIS_AS_CORPORATE_ACTION_LOSS_V1 implemented in shared
Portfolio accounting. Official600005 ->600019 ratio0.56, conversion2017-02-17,
new-share activation2017-02-27 reverified. Zero parent basis is written off only
as corporate-action PnL; cash/trading PnL/orders/fills remain unchanged.
MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17 RESOLVED.
504 backend/78 frontend tests, source replay, lint/format/types and schema checks PASS.
R5 resumed:95 pages/2849 merger announcements,69 implementation-document leads;
five prior candidates updated,2 supported/3 source-unresolved. Full census unknown.
Broader review:6 pages/175 capital-adjustment notices; official600462 confirms20%
ordinary-holder compulsory surrender, with30% issuance diverted to bankruptcy account.
This is not a merger or zero-successor case; partial-surrender historical-basis treatment
requires a new explicit policy. No loss/full-basis retention, bonus credit or exclusion chosen.
SINGLE_SMALLEST_BLOCKER=MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY_UNAPPROVED:CN-A:SSE:600462.
HUMAN_APPROVAL_GATE=R5_MANDATORY_PARTIAL_SHARE_SURRENDER_BASIS_POLICY;
HUMAN_APPROVAL_REQUIRED=YES. Exact surrender transfer chronology remains separate source work.
Full dataset CREATED/AUDITED/FROZEN=NO; verified safe start/coverage NOT_ESTABLISHED.
Preserved Pilotv2, R4v2, rights/demerger/prior source decisions remain unchanged.
No Development/Validation/OOS, full freeze, PR12 merge or release.
Report: ../research/ZERO_WHOLE_SHARE_CHECKPOINT.md;
machine report: .research/reports/r5-zero-whole-policy-v1.json.
After human decision resume preserved R5 queues, not acquisition from zero.
No background worker remains. Full freeze gate has not been reached.

## Historical checkpoints below (superseded)

## Current: 000024 merger PASS; R5 zero-whole-share basis decision STOP

CN_A_MERGER_FRACTIONAL_SHARE_POLICY_V1 implemented; 000024 evidence/accounting/replay PASS.
Prior MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30 RESOLVED.
Official global allocation remains distinct from approved deterministic floor/no-cash accounting.
Full parent basis transfers to whole successor shares; remainder and CEIL bounds are audit-only.
R5 resumed the historical inventory; five candidates, two official reviews, one supported,
four unresolved including three retained source leads. Full census/materiality NOT_ESTABLISHED.
Official 600005 ratio0.56 exposes hypothetical Q=1 ->0 whole shares: positive B/0 is undefined.
No actual strategy holding is claimed; no loss, residual asset, cash, extra share or exclusion chosen.
SINGLE_SMALLEST_BLOCKER=MERGER_ZERO_WHOLE_SHARES_BASIS_UNAPPROVED:CN-A:SSE:600005:2017-02-17.
HUMAN_APPROVAL_GATE=R5_MERGER_ZERO_WHOLE_SHARE_BASIS_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
494 backend/78 frontend tests; source replay, lint/format/types and additive schema checks PASS.
Rights V2/600003/prior authorities/frozen Pilotv2/R4v2 unchanged. R4 actual fills remain0.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/verified coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR12 merge, release or background worker.
Report: ../research/MERGER_POLICY_V1_CHECKPOINT.md;
machine report: .research/reports/r5-merger-policy-v1.json.
Next after zero-whole basis decision: resume preserved R5 sources/materialization/audit;
stop at GATE_FULL_RESEARCH_DATASET_FREEZE without freezing.

## Historical checkpoints below (superseded)

## Current:600003 demerger PASS; R5 merger fractional-allocation decision STOP

CN_A_MANDATORY_DEMERGER_POLICY_V1 implemented;600003 accounting/replay/source audit PASS.
Prior DEMERGER_ACCOUNTING_POLICY_UNAPPROVED:CN-A:SSE:600003:2010-02-26 RESOLVED.
One identified demerger supported; full event census NOT_ESTABLISHED.
R5 resumed existing lifecycle/inventory evidence and verified000024 ->001979 merger.
Official1:1.6008 conversion requires all-holder remainder ranking with random ties.
SINGLE_SMALLEST_BLOCKER=MERGER_FRACTIONAL_SHARE_POLICY_UNAPPROVED:CN-A:SZSE:000024:2015-12-30.
HUMAN_APPROVAL_GATE=R5_MERGER_FRACTIONAL_SHARE_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
No arbitrary rounding, cash-in-lieu, fractional trading or exclusion was chosen.
484 backend/78 frontend tests, Ruff/format/mypy, schema and source replay checks PASS.
Rights V2 queue/accepted authorities/frozen Pilotv2 unchanged; R4v2 remains PASS with0 fills.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; safe start/verified coverage NOT_ESTABLISHED.
No formal studies, profitability inspection, PR merge, release or background worker.
Report: ../research/DEMERGER_POLICY_V1_CHECKPOINT.md;
machine report: .research/reports/r5-demerger-policy-v1.json.
Next after decision: resume preserved R5 source queues, materialize/audit, stop at full freeze gate.

## Historical checkpoints below (superseded)


## Current: rights entitlement V2 PASS; material demerger methodology STOP

Human V2 separates event structure, tradability evidence and portfolio policy.
CN_A_RIGHTS_ISSUE_POLICY_V1 / NO_SUBSCRIPTION_NO_MONETIZATION_V1 implemented.
000960/2010-01-27 verified STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE;
tradability NOT_EVIDENCED; prior exact rights blocker RESOLVED.
148 events reprocessed:4 STANDARD_COMPLETE,0 STANDARD_PARTIAL_BUT_ACCOUNTING_SAFE,
0 EXPLICIT_UNSUPPORTED_VARIANT,144 EVENT_IDENTITY_UNRESOLVED source-work queue.
20 independently identified occurrences match provider records; full census PARTIAL,
not zero unexplained differences. No source backlog is re-labelled a tradability decision.
R5 safety review confirms600003/2010-02-26 one-parent/two-successor demerger.
SINGLE_SMALLEST_BLOCKER=DEMERGER_ACCOUNTING_POLICY_UNAPPROVED:CN-A:SSE:600003:2010-02-26.
Required methodology: successor historical cost allocation and intervening valuation.
HUMAN_APPROVAL_GATE=R5_DEMERGER_ACCOUNTING_POLICY; HUMAN_APPROVAL_REQUIRED=YES.
472 backend/78 frontend tests PASS; replay/Ruff/mypy PASS.
R4v2 PASS with0 actual fills; no rerun, strategy changes or profitability review.
Frozen Pilotv2/accepted authorities unchanged; full2010-2025 CREATED/AUDITED/FROZEN=NO.
Safe start NOT_ESTABLISHED; no formal studies, merge or release. No worker running.
Report: ../research/RIGHTS_ENTITLEMENT_V2_CHECKPOINT.md;
machine report: .research/reports/r5-rights-entitlement-v2.json.

## Historical checkpoints below (superseded)


## Current: rights policy engineering PASS; R5 exact event-evidence STOP

CN_A_RIGHTS_ISSUE_POLICY_V1 / DECLINE_SUBSCRIPTION approved and implemented.
Event model/accounting/reproducibility PASS; old participation-methodology blocker RESOLVED.
Inventory148 events/137 securities:2 supported,146 unresolved,0 positively confirmed
non-standard variants. No rights-based exclusion or full authority promotion.
User section8 STOP: RIGHTS_EVENT_UNSUPPORTED_VARIANT:CN-A:SZSE:000960:2010-01-27.
Its entitlement non-transferability remains unverified; this is not a finding of tradability.
HUMAN_APPROVAL_GATE=R5_RIGHTS_EVENT_VARIANT_REVIEW; HUMAN_APPROVAL_REQUIRED=YES.
R4_V2_STATUS=PASS, R4_REAL_DATA_FILL_COUNT=0; no R4 rerun or frozen Pilot modification.
Full2010-2025 CREATED/AUDITED/FROZEN=NO; verified safe start NOT_ESTABLISHED.
No formal studies, strategy changes, profitability review, PR merge or release.
Current report: ../research/RIGHTS_ISSUE_POLICY_CHECKPOINT.md;
machine state: .research/reports/r5-rights-policy.json. No background worker remains.

## Historical checkpoints below (superseded)

## Current: Pilot v2 frozen; R4 v2 PASS; R5 methodology decision STOP

R1 COMPLETE; R2 v1 SUPERSEDED; R3 v1 INVALIDATED; R2/R3 v2 COMPLETE.
GATE_A_REVISED_DATASET_FREEZE APPROVED and executed, v2 current accepted/frozen.
R4 v2 PASS including fresh replay/no-look-ahead, persistence/API/actual UI.
R5 resumed source preflight, then STOP: FULL_HISTORY_RIGHTS_ISSUE_TREATMENT_REQUIRES_HUMAN_DECISION.
Official6000362010 paid rights issue is absent from the dividend-only response;
existing accounting policy rejects rights. No automatic subscription, forfeiture,
cash injection or exclusion decision. HUMAN_APPROVAL_REQUIRED=YES for this policy,
not full dataset freeze. Full2010-2025 dataset CREATED/AUDITED/FROZEN=NO;
verified research-safe start NOT_ESTABLISHED. No formal studies/merge/release.
Current BaoStock endpoint recovered;124 exited-security factor baselines verified.
Other full-history authorities remain unfinished, not inferred from Pilot PASS.
See `../research/PILOT_V2_FREEZE_R4_R5_CHECKPOINT.md` and
`.research/reports/r5-source-preflight.json`. All probes complete; no worker running.

## Historical checkpoints below (superseded)

## Current: revised Pilot v2 frozen; R4 v2 RUNNING

Latest human approval supersedes prior revised-freeze STOP. All eight approved
component hashes, partition bytes, counts,25 R3 checks and preserved v1 verify.
V2 freeze complete, canonical receipt f9add5f2...635bcb3. Unchanged R4 v2 running;
R1 COMPLETE; R2/R3 v2 COMPLETE; R2 v1 SUPERSEDED, R3 v1 INVALIDATED. On PASS, R5 full-history
materialization/audit. Next gate GATE_FULL_RESEARCH_DATASET_FREEZE, unfrozen.
No formal studies, PR merge or release. Previous acceptance decisions unchanged.

## Historical checkpoints below (superseded)

## Current: revised Pilot Dataset review

V2 CREATED=YES; AUDITED=YES; FROZEN=NO; readiness READY.
25 fresh R3 checks PASS; cross-source2478 rows replayed from original snapshots,
not a copied verdict. All1755700 secondary-source Pilot rows had amount precision
rechecked.433 backend tests passed; full Ruff/format/mypy passed.
5180 ordinary shares;1922643 bars;382 sessions. Candidate master5178 ->5181;
three added STAR exits,zero removed,one corrected A/B listing date (600190).
15528 reused partitions,12 rebuilt,9 new. Complete lists and all hashes:
`../research/REVISED_PILOT_DATASET_REVIEW.md`, `.research/reports/revised-pilot-v2.json`.
V1 immutable checksum verification PASS; original manifest/freeze/R3/R4 preserved.
STOP at GATE_A_REVISED_DATASET_FREEZE. R4 v2 NOT_RUN; R5 blocked; no formal studies.

## Historical checkpoints below (superseded)

## Current: frozen Pilot retained; R4 engineering passed; R5 counterexample

PILOT_DATASET_FROZEN=YES; immutable0696a5c7...manifest remains unchanged.
R4 pipeline/replay/no-look-ahead/metric/API/UI parity checks PASS on the supplied
data:382 sessions,7 rebalances,140 orders,0 fills. All results remain explicitly
PILOT_ENGINEERING_SMOKE_ONLY. No strategy economics changed.
R5 source expansion independently proved three absent STAR exit candidates.
Current dataset acceptance INVALIDATED; original R3 receipts preserved as history.
Full dataset CREATED=NO, AUDITED=NO, FROZEN=NO; all full counts/hash unavailable.
Stop for revised Gate A review, not full freeze approval of an unbuilt dataset.
Blocker=FROZEN_PILOT_MASTER_OMITS_STAR_EXIT_SECURITIES.
Detailed evidence and completed/unfinished work:
`../research/PILOT_FREEZE_R4_R5_CHECKPOINT.md`.

## Historical checkpoints below (superseded)

## Current: approved freeze complete; R4 underway

Pilot freeze PASS after final read-only R3 identity/partition/source verification.
Original manifest/partitions unchanged. Freeze record74870e7d...committed separately.
R4 runs PILOT_ENGINEERING_SMOKE_ONLY with full/reversed/prefix replay and existing
research persistence/API/UI; no economic parameter changes or assumed fills.
Backend422 tests,frontend76 tests,lint/type/build checks pass at this checkpoint.
Full R4 acceptance remains pending actual persisted API/UI parity. No formal
Development/Validation/OOS,merge/release. Next stage is R5 full historical data.

## Historical checkpoints below (superseded)

## Current: R2 published and R3 audited; Gate A stop

RUN_ID=20260912-R2-R3-ORDINARY-A-SHARE; CURRENT_STAGE=R3;
STATUS=AWAITING_HUMAN_APPROVAL. GitHub account MakenzieAhern verified.
Implementation HEAD=5be77b05fa0b674c0f37bc04e19267bdac50b24b;
419 backend tests/Ruff/mypy PASS; CI34665563160 backend/frontend/compose SUCCESS.
Final report-only commit: resolve with `git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md`;
verify its CI separately. Branch feature/a-share-research-v1.1; PR12 OPEN/UNMERGED.

R2 resumed from the original657+1923 inputs;2597 remaining ordinary A shares
recovered, not reacquired from zero. Final657 primary +4520 secondary,5177
securities/1922088 raw rows/12528 factor rows. Required failures/unresolved=0.
Missing observations4210 remain explicit; rejected observations0. Full amount
audit34799 reachable scheduled decisions,0 ambiguous,0 outliers; two all-date
stress ambiguities retained, not used to change policy. Full source-policy pins intact.

Real atomic publication completed. Second invocation verified resume without
source fetch or partition rewrite. Real published-data R3 exited0:22 checks PASS,
5725 rule cases, zero unclassified/non-A-share leakage. Original2580 receipt
reconstruction exactly matches ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6.
Canonical manifest0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490;
audit artifact88fa6df2892876bb7318ceabd24883539ca9b7920ec7abf1f2d88be5e9d892d1.

SOURCE_AUTHORITY_PREFLIGHT=PASS; PILOT_DATASET_CREATED=YES;
PILOT_A_SHARE_DATA_READINESS=READY; DATASET_AUDITED=YES; DATASET_FROZEN=NO.
HUMAN_APPROVAL_GATE=GATE_A_DATASET_FREEZE; HUMAN_APPROVAL_REQUIRED=YES.
SINGLE_SMALLEST_BLOCKER=NONE (intentional human approval gate).
DEVELOPMENT_STUDY=NOT_RUN; VALIDATION_STUDY=NOT_RUN; OFFICIAL_OOS=NOT_RUN;
PR_MERGED=NO; V1.1.0_CREATED=NO. Stop; no background data worker remains.

Official daily suspension/tradeability remains unknown/null on1926298 lifecycle
security-sessions. No missing bar was labeled suspended; no fill may be assumed
without separate official evidence. This approved fail-closed handling is audited,
not complete execution coverage. Detailed counts,22 checks,classification evidence,
limitations and hashes: [full checkpoint](../research/R2_R3_ORDINARY_A_SHARE_REPORT.md).

## Historical checkpoints below (superseded)

## Current running milestone: approved instrument scope

Latest running snapshot:4074 completed inputs (657 primary,3417 secondary),1103
remaining,zero required failures;4020 Parquet securities/1498998 raw rows.
Original2580 partition receipts still reproduce
`ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6`.
Incremental amount audit:4032 securities/1503570 rows,26922 potentially reachable
decisions,zero ambiguity/outliers; SHA-256
`052c1067c455f0d9cdb4556509c0409c29ca02cbbbac61141175a73baedcafbd`.
Live worker remains active; external checkpoint supersedes these snapshot counts.
Publication/audit code based on8d6a835 passes419 tests, lint and typing. The offline
synthetic full publication/resume/audit test is not an actual Pilot audit PASS.

Human decision recorded in DECISIONS and research methodology. R2 RUNNING,
approval not required. Shared explicit COMMON_A_SHARE gate preserves four boards
and listing/delisting; unknown/late/overlapping classification fails closed.
Source inventory reuses existing master snapshots and checksums; targeted SSE
SEC_TYPE/IPO metadata supplies the mixed STAR stock/CDR distinction. A current
SEC_TYPE snapshot alone is not accepted as historical classification.
Full scope gate PASS: 5178 candidates, 5177 COMMON_A_SHARE, one CDR (689009),
all other instrument categories zero; zero unclassified. Classification checksum:
`28d56696d2dc3de6d3c217dc557b9d8139729b3389245beb8fa580897ce8b7d7`.
The previous complete suite passed 415 tests; the added shared-source integrity
regression also passes, with Ruff and strict typing. R2 has resumed the remaining
2597 required securities. Existing 657 primary /1923 secondary inputs and 2580
partitions are retained. Historical failure evidence remains separate from the
scope-filtered required-data denominator.
Dataset not created/audited/frozen; no strategy, studies, merge or release.
This is an intermediate engineering milestone, not the terminal Gate A report.

## Historical checkpoints below (superseded)


## Current: instrument-scope decision required

R2 BLOCKED; SINGLE_SMALLEST_BLOCKER=PILOT_INSTRUMENT_SCOPE_REQUIRES_HUMAN_DECISION.
The pre-blocker97eebf3 contract names CN_A and four boards but does not establish
ordinary-equities-only versus CDR-inclusive scope. Official SSE notice confirms
689009 is a CDR, listed2020-10-29; this fact alone does not authorize exclusion.
Full5178-row type-evidence inventory:1 confirmed CDR,5177 UNCLASSIFIED (not assumed
ordinary, not excluded). No other nonordinary instrument was positively established;
this is NOT a complete certified instrument census or zero-leakage PASS.
New sourced InstrumentClassification model is independent of eligibility. No filter,
master checksum, scope, strategy, factor baseline or frozen failover policy changed.
All657 primary/1923 secondary successes and2580 partitions/951927 raw rows unchanged.
The prior689009 empty-factor evidence remains unresolved if CDR is included.
Human must specify ordinary A-share-only versus CDR-inclusive Pilot scope before
classification/eligibility changes and R2 resume. Worker remains stopped.407 tests
and lint/type checks passed. No dataset publication, R3 PASS, freeze, study or merge.
Evidence:docs/research/R2_INSTRUMENT_SCOPE_AUDIT.md. HUMAN_APPROVAL_REQUIRED=YES;
this is not Gate A. Earlier master authority PASS does not certify instrument scope.

## Earlier checkpoints (superseded)



## Current: R2 factor availability blocker

R2 BLOCKED; HUMAN_APPROVAL_REQUIRED=YES; HUMAN_APPROVAL_GATE=NONE (not Gate A).
SINGLE_SMALLEST_BLOCKER=SINA_FACTOR_BASELINE_UNAVAILABLE_689009.
Accepted Sina HFQ URL returned HTTP200 with total=0/data=[] for689009.
No baseline can be inferred; no approved substitute/exclusion applies. No retry
of a non-transport failure, fabricated factor1 or third provider was introduced.
657 primary +1923 secondary complete inputs preserved;2580 securities partitioned,
951927 raw rows /6250 factor rows. One factor failure,2597 unattempted;2598 unresolved.
Worker stopped safely at a complete batch for human source resolution; no background
worker remains. Resume this checkpoint after resolving689009, never from zero.
All accepted R1 authorities and Tencent LIMITED_PRECISION_PARITY remain intact.
Entire available amount sample:17068 potential decisions,zero ambiguous (includes
7 separately audited decisions from689009's saved382 raw rows). Dataset unpublished,
unaudited,unfrozen; no studies,merge or release.406 tests/lint/type checks passed.
Full source/error/checksum evidence:docs/research/R2_SINA_FACTOR_COVERAGE_BLOCKER.md.

## Earlier checkpoints (superseded)


## Ongoing R2 observation inventory

1,505 materialized securities /554,152 raw rows /3,450 factor rows; failures0.
657 original primary successes remain unchanged. Worker continues from its live
secondary checkpoint. Expanded available-input amount audit:1,544 securities,
568,116 rows,9,891 potential decisions,zero ambiguous. No strategy invocation.
New offline observation inventory records3,369 missing lifecycle-session
observations across213 securities; zero-volume observations0. Missing observations
are not inferred suspensions. Exact intervals persist outside Git in
pilot-akshare-20260911/observation-coverage-current.json. Partition snapshot SHA256:
502a7712bc06840bd2febaa7218e34e23064515f29a7f721be15849f013db66b.
Inventory validates partition SHA/identity/count and listing/delisting boundaries;
its runnable test covers disjoint intervals, input reversal and duplicate rejection.
Dataset remains unpublished, unaudited, unfrozen. No studies or merge.

## Current running recovery milestone

R2 RUNNING. Primary657 preserved; secondary516 now materialized, total1,173
securities /428,646 raw rows /2,584 factor rows, zero partition failures.
4,005 inputs remained at this snapshot; live secondary-checkpoint.json is newer
as the worker continues. No dataset publication, full R3, freeze, studies or merge.
The original primary partition-report subset still hashes to
7c2916446fc867a39b41aa45a7062c44452be15fd2708a9b0e65882f5e573896.
Two-query/one-query normalized equality proved on260 recovered securities;
future requests omit the redundant second query without changing policy/coverage.
Delisting-period rule reachability is explicitly included: initial sample4335
potential checks (one more stable primary check than4334 previously reported).
The expanded current audit covered6429 checks with zero ambiguity. Old authority
artifacts retained; current audit writes separate amount-impact-current-* files.
405 backend tests and lint/type checks passed at acquisition milestone74f8c8c;
CI34612957718 SUCCESS. Latest refinements receive their own checks/CI.

## Earlier checkpoints (superseded)


## Current decision-invariance acceptance

R2 RUNNING; HUMAN_APPROVAL_REQUIRED = NO. Prior amount-semantics stop RESOLVED
under the new human-authorized decision-invariance criterion, not guessed rounding.
Tencent upstream unit=10,000 CNY; AKShare returned unit=CNY; nominal granularity100 CNY.
659 available securities/244,772 rows,4,334 potentially evaluated amount decisions,
zero ambiguous decisions. All-date600666/2024-01-19 stress ambiguity is retained,
not hidden: already ST-excluded and not a scheduled evaluation date.
Expanded2,478-row overlap has no OHLC/date mismatch or outside-envelope amount outlier.
SECONDARY_ACCEPTANCE = PASS_FOR_PILOT; LIMITED_PRECISION_PARITY, not exact tick parity.
CN_A_RAW_OHLCV_FAILOVER_V1 frozen SHA256
3fb1941b93f127774ec228d27bb78074d48dc2d35ee29e98826a3b207472f740.
Impact audit SHA256=d950fdc3543fbf8373370c8013f8a8a8579140e8b82523f7d0961033a280323c.
Every recovered partition must pass the same unchanged rule/interval check before
admission. Preserve657 primary successes; resume4,521 pending, no primary refetch.
No new exclusion, dataset freeze, study, merge or release. All R1 authorities intact.
Full trace/evidence:docs/research/PILOT_AMOUNT_DECISION_IMPACT.md.

## Earlier checkpoints (superseded)


## Current focused amount audit checkpoint

STATUS = BLOCKED; CURRENT_STAGE = R2; HUMAN_APPROVAL_REQUIRED = YES; not Gate A.
The authorized audit ran RUNNING without an approval pause, then stopped because
amount is REQUIRED under the pre-existing liquidity screen, not OPTIONAL merely
because the interchange schema accepts null. No methodology change was made.
SECONDARY_ACCEPTANCE = FAIL; amount classification INSUFFICIENT_EVIDENCE.
Six cached primary controls cover four boards, high/low price and volume, ST/*ST,
and retained adjustment-event periods.1,719 rows have raw strings and Decimal
unit/difference calculations; max absolute51 CNY, max relative0.0002227431347383828848417993403.
Observed2 decimals are not a documented provider rounding/error guarantee.
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
Amount audit SHA256 = 3807e6cc28f043b3cdff4d2bca22d0ddea8d99b918d09771171b5467e9da3c93.
Observation SHA256 = b7efbaa5571a63ed4a73e7e4f0adc1d908c9c8517079b234cc6702b6af9d7e96.
No market-data requests,657 primary securities unchanged,4,521 required gaps retained.
No dataset creation/audit/freeze, studies or merge. Existing authorities/policy preserved.
401 backend tests, Ruff/format/strict mypy PASS. GitHub MakenzieAhern verified.
Full report: docs/research/TENCENT_AMOUNT_ACCEPTANCE.md. CI checked after milestone push.

## Previous candidate checkpoint (superseded)


## Latest R2 systemic diagnosis and candidate failover checkpoint

STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; HUMAN_APPROVAL_GATE = NONE.
SINGLE_SMALLEST_BLOCKER = RAW_SECONDARY_AMOUNT_PRECISION_AUTHORITY_UNRESOLVED.
PRIMARY_ROUTE_STATUS = PRIMARY_SYSTEMIC_TRANSPORT_FAILURE (6/6 fixed probes).
RAW_OHLCV_PRIMARY_AUTHORITY = PASS; SOURCE_AUTHORITY_PREFLIGHT = PASS (existing,
unchanged primary manifest, not a secondary promotion).
SECONDARY_ACCEPTANCE = NOT_PROMOTED; CROSS_SOURCE_PARITY = PARTIAL.
CN_A_RAW_OHLCV_FAILOVER_V1 = CANDIDATE_NOT_ENABLED.

32 Tencent candidate requests cover 8 securities/two years/two repetitions;
2,418 normalized candidate rows repeat exactly. Six cached primary controls share
1,719 dates, with zero material OHLC/date mismatches. Four unexplained amounts
remain; prior Sina histories plus one targeted 300336 request corroborate the
rounding base but do not prove the remaining primary vendor precision behavior.
No additional tolerance, source substitution, arbitrary exclusion or strategy
performance criterion was introduced. Source snapshots and field-by-field parity
are external; full details in docs/research/R2_RAW_FAILOVER_ACCEPTANCE.md.

PRIMARY_SUCCEEDED = 657; PRIMARY_FAILED_SECONDARY_RECOVERED = 0;
PRIMARY_FAILED_SECONDARY_FAILED = 0 (no production secondary attempts);
AUTHORITATIVELY_NO_DATA_EXPECTED = 0; UNRESOLVED_REQUIRED_DATA = 4521.
All original raw/factor inputs, Parquet files and checkpoint hashes verified
unchanged. Partial production raw rows = 244,073. Candidate rows are not admitted.
No final manifest or Pilot Dataset was published; no R3, freeze, Development,
Validation, OOS, strategy, PR merge or release occurred. All R1 decisions preserved.

Primary probe SHA256 = 513f04d0ec47408b1f49503af5168eb07d2fbf5270b6a661f4c8e32bf3157d9c
Candidate audit SHA256 = ff0e31d2ffca13fb174995a1bd31eb3f4a6342c0c013dfc26779708469c3db47
Policy SHA256 = 47316572b10b3e1f8cc35362614958a7265463be25432f3de2b4a149841d3dcc
Tests: 11 focused recovery checks PASS; full backend 400 PASS; Ruff/format/mypy PASS.
Finished probes and persistent access-denial stops cannot restart on rerun.
Existing feature branch/PR12 retained. No Git identity change. Final milestone CI
is checked after push; this checkpoint does not claim a future CI result.

## Prior checkpoint (superseded by current failover review)

## Terminal R2 recovery checkpoint

STATUS = BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; HUMAN_APPROVAL_GATE = NONE.
SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070.
Initial pass: 5,178 / 5,178 processed, 504 completed, 4,674 pending.
First retry: 4,674 / 4,674 processed, 151 recovered, 4,523 pending.
Final retry: 4,523 / 4,523 processed, 2 recovered (600605, 600739), 4,521 unresolved.
Last terminal source failure UTC: 2026-09-11T11:49:51.552627+00:00.
The worker ended with FINAL_PUBLICATION_PROHIBITED; no retry process remains.
657 RECOVERED_PRIMARY (493 SSE, 164 SZSE); 0 accepted fallback recoveries;
0 AUTHORITATIVELY_NOT_EXPECTED_TO_HAVE_DATA; 4,521 UNRESOLVED_REQUIRED_DATA
(1,794 SSE, 2,727 SZSE). Every terminal error is RemoteDisconnected from the
accepted Eastmoney raw endpoint. Error classification UNKNOWN, not assumed
anti-bot, outage or lifecycle-driven. 600070 actual requests = 5, all exhausted.
No accepted fallback or existing transport-gap exclusion permits publication.

All master IDs accounted for exactly once in completed/pending sets; no overlap
or silent drop. Failure history has unique security/round slots, every pending
entry is round 2 terminal, and failure manifest exactly matches checkpoint.
No provider access-denial flag or abandoned .tmp file was found.
657 partial securities: 244,073 raw rows, 1,565 factor rows, quality failures 0.
Source/partition SHA checks pass during offline materialization. These are partial
raw/factor checks, NOT full R3 dataset audits or proof of complete observations.
No final input-manifest.json exists. All data and failure evidence remain outside Git.

External evidence under pilot-akshare-20260911:

- recovery-checkpoint.json SHA-256: ffdc46937ecbd30f74a28660ef1769d2a7b8506ef65d0f1c2ae45ddac4841a68
- recovery-failure-manifest.json SHA-256: e1279921716ebf3c3d424acfedceb7b8f70b950dcdd4f6372829e41c811488ce
- partition-checkpoint.json SHA-256: 7c2916446fc867a39b41aa45a7062c44452be15fd2708a9b0e65882f5e573896
- 600070-recovery-result.json SHA-256: 115ed5b78155e53e9f71396eab1c3baee21ef746808f14b4be7e360ea5ac4185
- recovery-completion-report.json SHA-256: be02bd9cba43320007fe7d6731fcdd060f947d63ca23d6d942ee07c6dcafc887

Final offline repeat reproduced the same partition-checkpoint SHA-256 with no
new network request; six focused recovery tests re-run PASS. Controller JSON
verified BLOCKED with all dataset/study permissions unchanged. GitHub login
re-verified MakenzieAhern; branch feature/a-share-research-v1.1.

SOURCE_AUTHORITY_PREFLIGHT = PASS; all R1 authority decisions unchanged.
PILOT_DATASET_CREATED = NO; PILOT_A_SHARE_DATA_READINESS = BLOCKED.
DATASET_AUDITED = NO; DATASET_FROZEN = NO; R3 = NOT_RUN.
DEVELOPMENT_STUDY = NOT_RUN; VALIDATION_STUDY = NOT_RUN; OFFICIAL_OOS = NOT_RUN.
PR12 remains OPEN/unmerged; no new PR, release or strategy execution.
Existing feature branch and MakenzieAhern identity retained. Backend 395 tests,
Ruff/format/strict mypy and preceding milestone CI passed; terminal documentation
checkpoint CI is checked after its single milestone push.

## Preserved active R2 recovery continuation (superseded by terminal state above)

STATUS = RUNNING; HUMAN_APPROVAL_REQUIRED = NO. Prior stop below superseded.
Independent queue continues through per-security failures; 600070 = UNRESOLVED_REQUIRED_DATA.
Three same-construction SSE controls succeeded, 382 rows each. No fallback is in
the current accepted OHLCV manifest; no new exclusion policy is introduced.
At this checkpoint: 657 securities partitioned, 244,073 raw rows, 1,565 factor rows;
quality failures 0, final publication NO. Periodic counts are checkpoint snapshots,
not final-universe acceptance. External pilot-akshare-20260911/recovery-checkpoint.json
and partition-checkpoint.json retain current counts and exact file hashes.
First acquisition pass completed all 5,178 members: 504 completed, 4,674 pending.
Round 1 completed all 4,674 pending members and recovered 151 additional inputs.
Final round 2 is RUNNING after the fixed 60-second backoff for the remaining 4,523
members; the full queue's retries are not yet exhausted. No dataset publication or full R3 audit
is claimed. The last first-pass completion, 300750, reused accepted raw/factor sample snapshots; it
does not establish a new live network recovery.
Round-1 result: 4,674 / 4,674 processed, 151 additional primary recoveries.
The first two were 600419 and 600420, each 382 rows. 4,523 inputs entered final retry.
600070 exhausted its last authorized request at 2026-09-11T08:29:25.145713Z;
RemoteDisconnected before HTTP response, recorded at 08:29:26.078749Z. Actual
requests total five (three prior client diagnostics and two new recovery slots).
Its terminal classification is UNRESOLVED_REQUIRED_DATA; root cause UNKNOWN.
No accepted fallback or existing transport-gap exclusion exists. Evidence is in
600070-recovery-result.json outside Git. No further 600070 request is authorized;
other securities continue their independent final pass, with final publication barred.
Final-pass progress snapshot: 4,390 / 4,523 processed, two additional primary recoveries.
Milestone feabf7055fab86d72ccde1d0d75ae8ef8d442036 is pushed; CI 34579627544 SUCCESS.
First-pass milestone bfb89fb26dd39422da14bf2f1eab2e6c1de9637f is pushed;
CI 34563889226 completed SUCCESS. No PR merge or dataset freeze occurred.
After recording the source failure at 2026-09-11T05:07:34.160687Z, the Windows
process hit WinError 5 while replacing the WSL-backed checkpoint (no separate
exact error timestamp was captured). Both old and newer temporary checkpoints were preserved;
the newer one was verified as the same state plus two failure records and restored
using WSL-native publication. Exact failure timestamps and provider attempt slots
were retained; no network request was replayed. Evidence is external
checkpoint-publication-recovery.json and its before/after snapshots.
Progress reads now use WSL-native Python, avoiding Windows file-sharing locks.
The shared atomic save retries only PermissionError during publication of the same
bytes, at most five attempts with 0.1/0.2/0.4/0.8-second backoff; persistent failure
still retains the prior checkpoint and temporary bytes. Six focused tests and
395 backend tests PASS; Ruff, format and strict mypy PASS. R2 resumed from the
preserved round-1 checkpoint, not from zero.
Checkpoint-fix milestone b1be221fc793642be07356cbf98764011a34eb08 is pushed;
CI 34565166603 completed SUCCESS. The active recovery worker uses this fix.
The scheduler now uses two workers with two-second inter-batch pacing and a
20-second cooldown after ten consecutive failed batches. Three fixed rounds,
30/60-second round backoff, no jitter; no repeated failed request on restart.
Original failure evidence remains untouched. Backend 395 tests PASS; Ruff,
format and strict mypy PASS. Request construction comparison is external
request-comparison.json; no proxy, standard Python-urllib/3.12 header, 35s timeout.
The earlier budgeted 600070 request used the standard requests 2.34.2 Session on
the same accepted URL at 2026-09-11T01:54:36.190841+00:00. It also closed before
HTTP response (ConnectionError wrapping RemoteDisconnected). This consumes the
round-1 recovery slot; it is not an additional provider or a repeated slot.
At that point, three prior diagnostic requests plus this request made four actual
requests; the round-2 slot subsequently failed as recorded above. Root cause remains UNKNOWN.
Five focused ingestion tests PASS, including physical checksum repeatability,
lost-receipt reconstruction and detection of modified partition bytes.
Recovery-test milestone 6cf7623c05844559540af76d5b3f71af1a9233f5 is pushed to the
existing feature branch; CI 34554480884 completed SUCCESS. PR #12 remains unmerged.
Lifecycle-only expected-session check: every one of the 5,178 accepted members
has at least one calendar session on/after listing and before delisting in the
Pilot interval. Zero members qualify as having no expected sessions solely from
listing/delisting boundaries. This does not infer suspension or excuse missing bars.

## Preserved prior checkpoint (superseded by active R2 recovery above)

RUN_ID = 20260911-R1-R2-07
START_SHA = 14c9f8c4c5a616442775d070f26aa34e858785e6
END_SHA = Resolve with git log -1 --format=%H -- docs/orchestration/RUN_REPORT.md
CURRENT_STAGE = R2
STATUS = BLOCKED
BRANCH = feature/a-share-research-v1.1
PR = 12 OPEN / UNMERGED
CI = Verify final publication HEAD after push

PILOT_EXECUTION_CONVENTION_DECISION = APPROVED
MARKET_RULE_AUTHORITY = PASS_FOR_PILOT
EXECUTION_CONVENTION_VALIDATION = PASS
SOURCE_AUTHORITY_PREFLIGHT = PASS
FULL_HISTORY_RULE_AUTHORITY = PARTIAL

Official source claims and simulated execution are now independent gates.
The existing 14 SZSE snapshots support 27 official claims, all VERIFIED.
The old unverified transfer-fee claim remains preserved as an explicitly
non-statutory frozen research allowance under approval section9, not deleted
or promoted to official fact. Rates unchanged. SSE STAR quantity metadata was
checked against official 2019-07-19 Q5-Q6 at
https://edu.sse.com.cn/tib/qa/c/4866268.shtml (raw/meta retained outside Git).

CN_A_DAILY_OPENING_LIMIT_V1 is a SIMULATION_ASSUMPTION. Immutable limit=raw close(t),
signal after close(t), intended next calendar session, independent legal/status/
conservative daily-proxy eligibility, raw OPEN only after acceptance. Unfilled
instructions expire; no synthetic missing bars or extra slippage. The existing
RiskEngine/OMS/broker/portfolio path remains shared. No exact auction-fill claim.
The 1% daily-volume cap is ex-ante model conservatism, not auction liquidity proof.
README, methodology and research report permanently link the limitations.

Backend = 390 tests PASS
Execution convention = 36 focused tests PASS
Ruff / format / strict mypy = PASS

R2 input acquisition started against the 5,178-member accepted master.
A targeted delisting canary 300336 has 91 raw bars and a parsed HFQ curve.
The first fixed-order staging member 600070 failed before receiving HTTP bytes
in three bounded clients. Complete-universe staged count=0; no Parquet publication,
dataset manifest or dataset audit is claimed. A resumable acquisition command,
source metadata and explicit failure manifest remain. Full partition materialization
and R3 audit remain future work after this external access failure is resolved.
Previously accepted master/ST/adjustment/OHLCV/benchmark work was not repeated.

RULE_MANIFEST_SHA256 = cf8689d3e8269ba83bf03fe0b872689d10c441fabd7bf38ded72e30e38ca6583
NORMALIZED_RULE_SHA256 = 5569489384b3af7c7a81c39e6245e27b30bd064e7b801e411fe71de1fd7fd7f1
EXECUTION_VALIDATION_SHA256 = eae4180d8ac77495a82939a165dd94e8fbcf44ff9ad81cc3380c47d97a65f77a
SOURCE_PREFLIGHT_SHA256 = c549b64c562a5b5a08bd7ec7f9c62ba8d58df77ce0eac5eb66ebcc1d7d2ea859
R2_FAILURE_MANIFEST_SHA256 = dc3de6a08fb5377161e17cbf745c4bb51a3ee4535aa30964717b55b3ce3a43ff

DOCKER_RECOVERY = PASS
DOCKER_ENGINE_HEALTHY = YES
DOCKER_COMPOSE_HEALTHY = YES
POSTGRESQL_HEALTHY = YES
REDIS_HEALTHY = YES (PONG)
BACKEND_HEALTHY = YES (/api/health 200)
FRONTEND_HEALTHY = YES (configured 5173 HTTP200)

PILOT_DATASET_CREATED = NO
PILOT_A_SHARE_DATA_READINESS = BLOCKED
DATASET_AUDITED = NO
DATASET_FROZEN = NO
DEVELOPMENT_STUDY = NOT_RUN
VALIDATION_STUDY = NOT_RUN
OFFICIAL_OOS = NOT_RUN
HUMAN_APPROVAL_GATE = NONE (not Gate A)
HUMAN_APPROVAL_REQUIRED = YES
SINGLE_SMALLEST_BLOCKER = R2_RAW_ROUTE_CONNECTION_CLOSED_600070
PR_MERGED = NO
V1.1.0_CREATED = NO

Next external action: restore the accepted 600070 raw-history request or authorize
a complementary source. Do not restart acquisition, discard source failures,
reopen accepted authorities, merge PR12, freeze, or run any study.
