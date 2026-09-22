# Revised Pilot Dataset review

2026-09-12 UTC. STOP at **GATE_A_REVISED_DATASET_FREEZE**.
V2 is created, audited, READY and **not frozen**. Human freeze approval is required.
No R4 on v2, R5 continuation, formal studies, PR merge or release was performed.

## Population defect and complete impact

The original SSE exit query omitted STAR. Extending it exposed a second defect:
including B-share type2 could supply a B-share LIST_DATE under a populated
A_STOCK_CODE. The production query now requests A-only types1,8 and preserves
old source snapshots. Independent SSE/SZSE2022 year-end lists were reconciled
against the revised Pilot-start population, with zero missing/extra A shares.
All four current and exited board segments are required. Future IPOs and exits
before Pilot are retained in the external lifecycle census, not admitted to Pilot.

Candidate master5178 ->5181; ordinary A shares5177 ->5180. One CDR remains
explicitly out of scope. Exactly three Pilot additions; no removals:

| Symbol | Instrument/board | Listing | Termination | Pilot eligibility |
| --- | --- | --- | --- | --- |
|688086|Ordinary A / STAR|2020-02-26|2023-07-07|2023-01-01 <= date <2023-07-07|
|688287|Ordinary A / STAR, BSE transfer; no new issuance|2022-05-25|2026-06-10|Entire Pilot|
|688555|Ordinary A / STAR|2020-06-23|2023-07-07|2023-01-01 <= date <2023-07-07|

Changed lifecycle:600190 A-share listing1998-05-19 ->1999-06-09; the former
date belonged to its B share. Delisting2025-07-28 is unchanged. Its partitions
were explicitly rebuilt/revalidated from preserved provider sources, not silently
treated as unaffected. SZSE300114 remains300114 in Pilot; official notice2025-027
makes302132 effective2025-02-17, after Pilot. This is not a new Pilot admission.

The expanded exit census contains188 pre-Pilot exits absent from the intentionally
Pilot-only v1 table. These are not188 new Pilot omissions/admissions. Including
three relevant additions,191 securities were newly inventoried relative to that
table.181 future IPOs remain excluded. Required2022-12 prehistory has no additional
prehistory-only lifecycle. Exact188/181 lists and before/after records are committed
in `.research/reports/revised-pilot-v2.json`; no unexplained master differences remain.

## Source and point-in-time treatment

The full newly discovered issuer disclosure indexes were acquired with page-group
completeness checks. Official SSE metadata reconciles exactly with CNINFO documents.
The existing dated ST parser and independent2022-12-31 shareholder-table anchor
were reused.688086 entered *ST2022-05-06;688555 entered *ST2022-11-22. Both enter
the delisting period2023-06-08.688287 has a NORMAL Pilot-start anchor; its two
Pilot notices warn of possible future other-risk treatment, not an effective entry.
The dated transfer listing notice confirms its A-share identity and2022-05-25 date.
Historical names are not used to invent dates. No omitted member was labeled NORMAL
just to close a gap. Original accepted SSE/SZSE records remain unchanged; new evidence
is a separately hashed extension. Parser/source hashes and publication timestamps
are retained in the external evidence and committed small review.

No acquisition restarted from zero. Eastmoney's targeted bounded failures were
preserved; accepted Tencent raw and Sina factor probes were reused by checksum.
Existing ordinary-A-only scope, amount interval policy, provider precedence,
calendar, benchmark, market rules and conservative execution convention remain.

## Materialization and reuse

| Measure | v2 |
| --- | ---: |
|Ordinary securities|5180|
|SSE / SZSE|2289 /2891|
|SSE Main / STAR|1715 /574|
|SZSE Main / ChiNext|1531 /1360|
|Sessions|382|
|Raw bars|1922643 (+555)|
|Primary / secondary securities|657 /4523|
|Failed securities / unresolved required data / rejected rows|0 /0 /0|
|Missing observations|4281 (+71), explicitly recorded; never fabricated|
|ST / *ST observed bars|26906 /20869|
|Separate adjustment rows|12533|
|Reused / rebuilt / new partitions|15528 /12 /9|

Reused:5176 unaffected securities x(raw,factor,daily-state). Each identity/lifecycle,
provider lineage and hash was checked; daily-state reuse additionally compares a
fresh point-in-time replay row by row. Rebuilt:600190's three partitions plus nine
small global tables. New:three added securities x three partitions. No large market
data is committed. Checkpoints, source failures, per-partition physical/logical
hashes, atomic publication and a successful no-rewrite publication resume are saved
under external `staging/pilot-v2-build`.

Official daily suspension/tradeability remains unknown for1926924 lifecycle
security-sessions, as already approved. Unknown is null and NO FILL; missing bars
are not inferred suspensions. This dataset is not an execution-readiness certificate.

## Fresh R3, not inherited acceptance

All25 required checks passed over the full5180-security v2, including every raw
source normalization, factor temporal replay, lifecycle/delist retention, ST state,
provider lineage, instrument classification, benchmark,5744 market-rule cases,
each partition's reversed-input byte/logical reproducibility, and resume/restart.
Cross-source2478 comparisons were recomputed from original snapshots; the old
verdict was not copied. All1755700 secondary-source Pilot rows had two-decimal
upstream amount precision rechecked. Full-universe unchanged amount-rule interval
checks have zero ambiguous relevant decisions. No strategy economics was evaluated.

Negative tests cover omitted STAR exits, all missing exchange/board segments,
current-only exit reconstruction, retroactive removal, and future code backdating.
Known688086/688287/688555 occur as fixtures; retrieval uses generic board surfaces.

## Hashes and preserved v1

V1 remains FROZEN=YES, SUPERSEDED=YES, RESEARCH_ACCEPTANCE=INVALIDATED,
reason SECURITY_MASTER_COMPLETENESS_DEFECT. Original manifest:
`0696a5c7454f044a3f0ea8886b1c08fbe2228b19598894ddb44ac54498978490`.
Its files, freeze record, original R3 and R4 result were not rewritten. The API/UI
invalidation warning remains; v2 is not advertised as frozen/accepted for studies.

V2 ID:`cn-a-pilot-akshare-20230101-20240731-v2`, parent:v1.

| Component | SHA-256 |
| --- | --- |
|Security master|748890c597a1c7dc9e87603d0314a4c7c7d4038ba74c4739c5d1f9ded965bef7|
|Raw bars|0025a8167c11b0a70db7c6ca94209d4ddaf7f8c88fa5df292f8cec60f384dd9c|
|Adjustments|3536a0976c9f4c356f4f129017b4df2fa72e9ac0e1420c10b72b860631a7b876|
|Benchmark|95a4d25ae9655bfb3e9a033ae53f6c067fbab52989c48c18f5553e5651fdcb76|
|SSE ST extension bundle|1d69107d586d2b205d8a5e68730da7c738024d7a89d9f24dfe541bef1241ef31|
|SZSE ST source|127f4cec8c32277057f6cf35f502a6efd2d54051607d5df32241d99859bed6f1|
|Source preflight|3d9a0802f664b9c95282196b9e649b998e8b77159da6408f1dd64e1488c14c3f|
|V2 canonical manifest|187b8c31d333fa33c5784d31bca60949e44a0c3a0c37a021235e49115bf92600|
|Reuse/rebuild manifest|ce43365911d086916ded52a23998aafe914d2392aaf528cb990e9afe99cf08a3|

Partition component hashes use the existing canonical `{partitions: [...]}` method.
SSE ST bundle hashes the original interval hash plus separately hashed new-member
evidence; SZSE is the unchanged dated-source hash. Source contracts retain parent
provenance; revised master/lineage fields and this fresh audit supersede old census
acceptance. Unchanged benchmark bytes correctly retain the same component hash.

## Stop

HUMAN_APPROVAL_GATE=GATE_A_REVISED_DATASET_FREEZE; HUMAN_APPROVAL_REQUIRED=YES.
SINGLE_SMALLEST_BLOCKER=HUMAN_APPROVAL_REQUIRED_FOR_V2_FREEZE.
V2_FROZEN=NO; R4_V2=NOT_RUN; R5=BLOCKED_PENDING_REVISED_PILOT_ACCEPTANCE.
DEVELOPMENT_STUDY=NOT_RUN; VALIDATION_STUDY=NOT_RUN; OFFICIAL_OOS=NOT_RUN.
PR12 remains open/unmerged; no release, live trading or ML/GPU work.
