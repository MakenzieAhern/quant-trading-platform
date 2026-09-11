# Current state

R1 AWAITING_HUMAN: PILOT_EXECUTION_CONVENTION_DECISION_REQUIRED. Not Gate A.
Original SZSE PDF dependency RETIRED by the user's source-recovery decision.
Do not retry the three retired URLs or ask the user to download them again.

14 accessible official SZSE sources preserved, including all four supplied
alternatives. Publication 2023-02-17 / 深证上〔2023〕98号 verified from the later
official notice; implementation 2023-04-10 verified from technical PDF page 18.
Later-version behavior is NOT applied to the Pilot. Handbook PDF pages 21-22
(printed 33-36) visually reviewed. Preceding 2021 rule PDF recovered too.

Git ledger: docs/research/SZSE_RULE_CLAIMS.json, 28 claims, 12 explicitly unclosed.
Backend 356 PASS; Ruff/format/strict mypy PASS. Tests are NOT authority acceptance.
Version .5 identifies preceding Main rules and distinguishes the first IPO
session from ordinary 10%, retaining the existing first-day no-fill.

Actual code review found MARKET orders filled at next daily open, although SZSE
accepts MARKET only in continuous auction for price-limited securities. Daily open
may itself be a resumed/continuous first trade, not proof of opening-auction fill.
Quantity caps, tick rounding, expiry, intraday phase/status and relisting handling
must close under an explicit execution convention, not be declared immaterial.
Transfer-fee 0.00001 provenance remains incomplete under official-SZSE-only scope;
the retrieved candidate yearbook is actually 2015 and is not Pilot fee evidence.

Next human decision: approve an explicitly specified conservative limit/auction
execution convention replacing MARKET-at-open, or retain the current convention
and remain blocked. Approval alone does not grant PASS: implementation, evidence
gaps and regression checks must still close before R2/R3.

All seven accepted data authorities preserved; MARKET_RULE PARTIAL, preflight FAIL.
Docker, PostgreSQL, Redis, backend/API200 and frontend5173/200 verified healthy.
Branch feature/a-share-research-v1.1; MakenzieAhern; PR12 open/unmerged.
Dataset not created/audited/frozen. No Development, Validation, OOS or strategy run.

External staging: market-rule-claims-20260911
Rule ledger canonical SHA256: 6dac2bab94829a6f726f76a185309e5ebca752c285e11d1fc31cc2ae011b81f2
Normalized rules SHA256: a2910f18646d8670feeb52dcf4af7b593f6f988e880b8cc95d1959dfd4a2b625
Preflight SHA256: 73030b9314c9ed4582c7c0526c92872bb13b39e359d725a09a58c7792933a92e
