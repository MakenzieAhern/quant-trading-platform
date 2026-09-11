# R2 Sina factor coverage blocker

SINGLE_SMALLEST_BLOCKER = SINA_FACTOR_BASELINE_UNAVAILABLE_689009.
R2 BLOCKED; HUMAN_APPROVAL_REQUIRED = YES; not Gate A.

## Exact source gap

CN-A:SSE:689009 has382 preserved Tencent raw observations,2023-01-03 through
2024-07-31. The accepted Sina factor request returned HTTP200, not a transport
failure or access denial:

https://finance.sina.com.cn/realstock/company/sh689009/hfq.js

The assignment is `var sh689009hfq={"total":0, "data":[]}`. Parser
`sina-multiplicative-asof-v1` correctly rejects it with
`INCOMPLETE_FACTOR_RESPONSE`. Empty data establish neither absence of corporate
actions nor a factor baseline of1. Root cause of vendor noncoverage is UNKNOWN.
No CDR-specific explanation is asserted without evidence.

Retrieval UTC:2026-09-11T16:10:18.215968+00:00.
Response SHA256:4ace5d54cd12ab56dc560483b2c3c09ff435c7d9a5e272879dd951f2bd10762c.
Raw Tencent response SHA256:
b9fdcf61711aa856242deeac0b675a1cb46e1942707783dfb4390623b1bf4567.
Normalized raw SHA256:
86d117244e83fc2bc87363257accec1821653f87d05113cb8899f939c89adfed.
Files persist under external staging pilot-akshare-20260911/secondary-attempts/0
and secondary-normalized/689009.json, with original request metadata.

Searched all existing `/home/yuchen/data/research` files for689009. No other
factor snapshot exists. Read the exact saved response and current shared parser,
accepted Sina authority and frozen raw failover policy. Existing source acceptance
explicitly prohibits inventing a missing baseline. The final retry is transport-only;
repeating this successful empty response or introducing another source is not an
approved remedy. No primary success was re-requested and no new source introduced.

Required human resolution: supported approved factor baseline/dated history for
689009 (or an explicit separately reviewed source-policy decision). Do not silently
drop this member or turn its absent factor into1. All already accepted R1 authorities
remain PASS; this is a concrete full-universe availability exception, not a rerun or
revocation of the accepted adjustment convention.

## Preserved recovery checkpoint

Primary657 + secondary1923 =2580 fully staged/partitioned securities.
951927 raw observations;6250 separate factor rows; partition failures0.
One attempted input failure (689009 factor);2597 unattempted members remain.
UNRESOLVED_REQUIRED_DATA=2598, not2598 failed HTTP requests.
689009's raw382 rows are saved but not admitted as a complete raw/factor partition.
The worker was stopped at a freshly persisted completed-batch checkpoint, after
other independent securities continued during diagnosis. No worker is left running.
Checkpoint/failure-manifest counts and contents agree. Pending work can resume
without re-fetching completed primary/secondary inputs once source resolution is recorded.

| External artifact under pilot-akshare-20260911 | SHA256 |
| --- | --- |
| secondary-checkpoint.json | 31598dfc8fc9d0697953ecb84cd94ac279758e9ad758e0352a496189ebd4b49b |
| secondary-failure-manifest.json | a14427dba2dd187b9be254541a96e8e3a61c6dd0d8dfae2d01ac98d4e50d34e6 |
| partition-checkpoint.json | ff844abd20b651ae9a962515a6feb6cc551f90468daf7b984959da7121149ca6 |
| original recovery-checkpoint.json | ffdc46937ecbd30f74a28660ef1769d2a7b8506ef65d0f1c2ae45ddac4841a68 |
| observation-coverage-current.json | 4c615022b1d50d4a46b7a5dd5e6c832f4fd6e93d4afa88e34c814fc2e6bc2916 |
| 689009-amount-guard-audit.json | 64e0f616f52e46156f72a9c99bc539f3d9b6c9eec9885b71eb7f8cb4bc118e72 |

## Amount acceptance remains closed

AKShare-returned amount=CNY; upstream=10000CNY; nominal quantum100CNY.
No claimed rounding mode or exact tick-level parity. Frozen uncertainty envelope
is [max(0,A-100),A+100]CNY; unchanged20-observation mean>=10000000CNY rule.

Current full completed-input audit:2580 securities,951927 rows,17061 potential
amount decisions,0 ambiguous. Separately retained689009 raw history contributes
382 rows and7 stable potential decisions despite its missing factor. Combined
available sample:2581 securities,952309 rows,17068 decisions,17068 stable,0 ambiguous.
No security or date with an actual ambiguous amount decision; maximum ambiguous
distance is NOT_APPLICABLE. The old600666/2024-01-19 all-date stress case remains
documented but is both ST-filtered and not scheduled; it is not silently erased.

Current main audit SHA256:
499f52d1595707a943f461d8b28a4e65677f82c3a21ab13205b58dcd80273de9.
The source/code usage inventory and retained2478-row cross-source statistics are
in PILOT_AMOUNT_DECISION_IMPACT.md. No strategy was called for these static checks.
TENCENT_AMOUNT_CLASSIFICATION=LIMITED_PRECISION_PARITY.
SECONDARY_AMOUNT_AUTHORITY=PASS_FOR_PILOT; SECONDARY_ACCEPTANCE=PASS_FOR_PILOT.

## Dataset and quality state

Observation inventory:3556 missing lifecycle-session observations across254
partitioned securities; zero-volume observations0. Missing does not imply suspended.
This is not full R3, and no overall dataset audit PASS is claimed.
PILOT_DATASET_CREATED=NO; PILOT_A_SHARE_DATA_READINESS=BLOCKED.
DATASET_AUDITED=NO; DATASET_FROZEN=NO.
DEVELOPMENT_STUDY=NO; VALIDATION_STUDY=NO; OFFICIAL_OOS=NO.
PR12 remains unmerged. No release/tag or strategy run.
406 backend tests, Ruff/format and strict mypy passed at the observation milestone;
CI for97eebf32960ce0d0f32a6d8796a7240435265b2b passed. This checkpoint changes docs/state only.
