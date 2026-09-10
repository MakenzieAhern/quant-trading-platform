# Current state

R1 BLOCKED on SZSE_2023_RULE_SOURCE_UNAVAILABLE, not Docker or identity.
Docker runtime failure RESOLVED: existing containers/volumes restored without
deletion/recreation. PostgreSQL healthy, Redis PONG, backend healthy and
/api/health HTTP 200. Project frontend HTTP 200 on configured port 5173,
title Quant Trading Platform. No unrelated application stopped.

Branch feature/a-share-research-v1.1, correct identity MakenzieAhern, PR #12
open/unmerged. Implementation checkpoint 7017909152233b2ff099d04053422a511e2abe07.
Version cn-a-2010-2025.3 preserves delisting_period_start in daily status and
serialization, resolves first-session no-limit/later board limits ahead of ST,
preserves suspension, and rejects use outside the audited pilot window.
353 backend and 74 frontend tests pass; lint/type/build checks pass.

Master/SSE/SZSE/adjustment/OHLCV/calendar/benchmark remain PASS; none reacquired
or reaudited. MARKET_RULE = PARTIAL, SOURCE_AUTHORITY_PREFLIGHT = FAIL.
Previously identified source routes were inspected. Official SSE 2023 archived
notice and DOCX recovered. Discovered SZSE 2023 PDF routes return 404; the
original notice also returned 404 using native Windows HTTPS. Web retrieval
also failed. No current-2026 rules or third-party mirror substituted.

External evidence root: /home/yuchen/data/research/staging/market-rules-20260911.
Audit manifest SHA-256:
4910e229314ffe4479af3070dbfc5757236b469d9002db38afb3ef8e453af3d6
Source preflight SHA-256:
bcc43dc1239651b9bb8538d0434cb20acb71c490f074d2b0a31314f9daed94dc

Smallest input: a retrievable official SZSE 2023 trading-rule text/notice or an
officially downloaded copy with its source URL. Then complete source binding
and remaining market-rule checks; only PASS permits R2 -> R3.
This input does not itself grant authority PASS.

Dataset not created/audited/frozen; counts unavailable, not zero.
No Development, Validation, OOS, merge, release or strategy performance run.
Gate A NOT reached. Docker is no longer a blocker.
