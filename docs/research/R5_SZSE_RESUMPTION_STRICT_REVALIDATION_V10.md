# R5 SZSE strict resumption revalidation v10

## Finding

The retained official bytes exposed a material parser defect in the historical
resumption supplements. Deadline and application language such as `不迟于`,
`最迟于` and `申请复牌` had been accepted as implemented trading boundaries in
some prior passes. Those reports remain immutable historical records, but their
acceptance counts no longer feed suspension authority.

The shared parser now rejects deadline-only, conditional, application-only and
same-sentence superseded resumption language. It still accepts a final notice
that states, after an application, that the stock **will** resume on one exact
date. Evidence rows with equal URL and SHA are sorted by their complete
canonical bytes, and supplement-report paths are sorted before audit replay.

## Retained-evidence replay

- baseline unresolved SZSE facts before supplements: **10,805**
- prior accepted resumption supplements: **8,913**
- prior events revalidated at the identical date: **7,276**
- prior event dates corrected from retained final notices: **10**
- prior event boundaries reopened without a current exact date: **1,627**
- newly accepted exact boundaries: **7**
- strict accepted resumptions: **7,293**
- retained terminal closures: **58**
- final unresolved SZSE boundaries: **3,454**
- conflicts: **0**

The seven newly closed facts include six final resumption notices and 002217's
separate 2014-04-28 final notice. Its superseded 2014-04-25 planned resumption
is explicitly rejected.

## Immutable evidence

- revalidation report:
  `/home/yuchen/data/research/staging/full-szse-resumption-revalidation-v1/szse-retained-official-revalidation-v4.json`
- report file SHA-256:
  `836441d21fde6c0a7231d1f992052c9a95671cb213d0f64a13561adfebb58168`
- report manifest:
  `b93145efb018320585041b8eac39410b8d194b02a0d92729202ddf445b8a8b1f`
- corrected authority:
  `/home/yuchen/data/research/staging/full-suspension-revalidation-v5/suspension-authority-v1.json`
- authority file SHA-256:
  `99867011f60a70f538c0e72b1edc22c7bba76387ec49cdec1690114041941183`
- authority manifest:
  `ba77ba3320da9ecf612f57776ec0ba7f67d79cf997d6ac053cc02da7ed50ae47`
- unresolved file SHA-256:
  `fe28ee707116dc51ff3298dfb6e9c8cc9888e52ab8ba4d254dc94e6509f02c4b`

Forward and reversed supplement-report order produced byte-identical normalized
events, authority, conflict and unresolved outputs. Suspension authority remains
`PARTIAL_OFFICIAL_RESUMPTION_BOUNDARIES`; no Full Dataset or study was run.
