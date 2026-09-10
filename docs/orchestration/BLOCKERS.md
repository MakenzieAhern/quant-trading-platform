# Blockers

SINGLE_SMALLEST_BLOCKER = SZSE_2023_RULE_SOURCE_UNAVAILABLE.
HUMAN_APPROVAL_REQUIRED = YES (source input; not dataset-freeze approval).

Need checksum-verifiable official Shenzhen Stock Exchange Trading Rules
(2023 revision), including its originating notice. Prior investor.szse.cn
notice returned HTTP 404 from Windows; discovered docs.static.szse.cn PDF
paths under stock/trade and trade/current returned HTTP 404 from WSL.
Search retrieval could not recover the document. No substitute authority used.
Supply a valid official download URL or an official copy with its original URL.

Recovered SSE sources and all failures/checksums remain outside Git in
market-rules-20260911. Remaining market-rule audit is not declared PASS merely
because implementation tests pass. Do not materialize until preflight passes.

DOCKER_RUNTIME_FAILURE = RESOLVED (services verified after recovery).
PUSH_IDENTITY_MISMATCH = RESOLVED; permanent identity MakenzieAhern.
Legacy BaoStock acceptance recovery is not a blocker.
