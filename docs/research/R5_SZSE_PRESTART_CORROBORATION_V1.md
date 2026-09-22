# R5 SZSE prestart risk-state corroboration

Scope: independent corroboration of 2009-12-31 starting risk states, not full
ST authority or tradability acceptance. Existing accepted Pilot artifacts unchanged.

The retained official dated-name export covers 3,028 full-period candidate
securities, 1,276 target risk transitions, zero detected risk-chain gaps and zero
out-of-lifecycle transitions. All 836 prestart members have a dated transition.
Current-name columns and post-2025 transitions are not used to initialize history.

820 yearbook price-table risk states agree. The table excludes 16 paused issuers;
absence does not mean NORMAL or delisted. Targeted October–December 2009 issuer
queries located 32 official CNINFO PDFs. All 32 opening issuer headers agree with
the respective STAR_ST anchors. Codes with spaced digits and the semicolon label
are normalized; unrelated companies mentioned later in the body are not parsed.
S versus non-S prefixes are not inferred as effective-dated name transitions.

The 16 are 000038, 000156, 000403, 000498, 000620, 000622, 000670, 000672,
000688, 000693, 000719, 000732, 000757, 000787, 000805 and 000863.
Annual company-name fields that omit risk prefixes are not treated as NORMAL.
The yearbook's private-use star glyph was visually verified on PDF page 60;
that mapping is scoped to this retained source, not a global substitution.

## Retained evidence

External root: `/home/yuchen/data/research/staging`.

- Dated export: `szse-st-recovery-20260910/windows-short-name-changes.xlsx`,
  SHA-256 `3c62c9a74edc2849b370d555b67b98018c5c9af90bd9be0bd4de0de0279dece5`.
- Yearbook PDF: `full-master-evidence/raw/szse-yearbook-2009.pdf`,
  SHA-256 `123a972d867cd0560954c7c7500b3a463c9541040e228bee8400eb59bf9f4484`.
- Targeted metadata manifest: `full-szse-st-v1/prestart-corroboration-v1/metadata-manifest.json`,
  canonical SHA-256 `79fbf5e628752cda183668d6a5859c06cbc420582090326df5896567acf661ee`.
- PDF manifest: `full-szse-st-v1/prestart-pdfs-v1/source-manifest.json`,
  canonical SHA-256 `b1ce8d6b3af80b72af2e2013d23afdbe5fb52b16302f20d6c54351e1fe76cda2`.
- Current probe: `full-szse-st-v1/dated-name-coverage-probe-v6.json`, canonical
  SHA-256 `808359addda040a29d091e3174a664668e66d9ab07d198bc6397b9147cddad3a`.

Reports preserve source URLs, UTC retrieval times, PDF hashes and page references.
Earlier probes remain immutable. V5 risk-state counts agreed, but its extracted
name could include the following header label; V6 fixes that boundary. V6 is
authoritative for this corroboration, not those earlier exploratory reports.

Reversed dated-source/master input reproduces the probe. Header tests reject
wrong issuers, body-only matches and missing risk labels. Full-period IPO status
initialization, daily replay and independent completeness checks remain pending.
Full dataset CREATED/AUDITED/FROZEN=NO. No research study, merge or release.

## Subsequent interval replay

Current extended probe: `full-szse-st-v1/dated-name-coverage-probe-v8.json`,
canonical SHA-256 `30af5f8fde6ce8e4ba3114c3cffb297aa71498ad54a3cd795a711db981cd43a8`.
V6 remains the completed prestart-only result. V8 reuses the accepted Pilot
SZSE listing-date NORMAL initialization; it does not infer it from a missing
name-history row. Earliest dated old-status conflicts would force UNKNOWN;
none were found. Missing independent prestart corroboration also forces UNKNOWN.

The existing status_on helper evaluates constant-state intervals; session counts
use the accepted 3,886-session calendar and inclusive delisting boundaries.
7,876,813 security-sessions: 7,613,493 NORMAL, 91,659 ST, 169,881 STAR_ST,
1,780 DELISTING_PERIOD, zero UNKNOWN. All effective-date rows are on calendar
sessions. Reversed-input and removal of future events agree. Regression checks
cover future events, delisting cutoffs, IPO conflicts and missing prestart data.
This is dated-source replay, not full independent historical-name completeness
or suspension authority; the overall source authority remains PARTIAL.
