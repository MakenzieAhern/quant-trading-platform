# Current state

R1 BLOCKED: SZSE_2023_RULE_BYTES_UNAVAILABLE. Not Gate A.
User source identity resolution recorded. Official notice publication:
2023-02-17, 深证上〔2023〕98号. Actual effective date: 2023-04-10, verified
against both successfully downloaded official SZSE listing announcement pages.
The notice and both supplied PDF URLs still returned 404, including native
Windows retrieval of the alternative. No PDF hash or full source PASS invented.

Rule version cn-a-2010-2025.4 now versions BOTH SZSE Main and ChiNext at
2023-04-10. Pre-boundary rules retained; numerical ChiNext limits unchanged.
Regression covers 2023-04-07/10/11/12, publication day, ages 0/4/5, NORMAL/ST/
STAR_ST, suspension, lots, ticks, stamp-duty transition, and reverse/prefix
rule input without future leakage. Backend 354 PASS; lint/format/strict mypy PASS.
Previous frontend baseline 74 PASS; current GitHub CI verified after publication.

MARKET_RULE = PARTIAL; SOURCE_AUTHORITY_PREFLIGHT = FAIL.
Other seven accepted authorities remain PASS, without reacquisition.
Docker recovery remains PASS; no runtime repair or data deletion this turn.
Branch feature/a-share-research-v1.1, identity MakenzieAhern, PR #12 unmerged.
Starting HEAD 54f788d072f9e4f1553f2222157bfefe7e39435d.

External evidence: /home/yuchen/data/research/staging/market-rules-user-resolution-20260911
Rule manifest: cc582b47330923d331e48deb9e3a0818e1d9b2a3e439fa9fbe6315625e85bdce
Normalized rules: 24af13b14402931fc569b8d72c5c95bacbb2b00ae5d004c5c322aa1d5c12cd3b
Source preflight: 9ceacf24b3ab83007bf8bdba4cee8f7ebb06d66d4d6b63391f9ec13a12ee7ed7

Next input: original official PDF/notice files with source URLs, not another
confirmation of already known URLs. Then validate provenance and finish R1;
R2/R3 remain conditional on PASS. Dataset not created/audited/frozen.
No Development, Validation, OOS, strategy performance, merge or release.
