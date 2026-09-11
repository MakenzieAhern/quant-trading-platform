# Blockers

SINGLE_SMALLEST_BLOCKER = PILOT_EXECUTION_CONVENTION_DECISION_REQUIRED
HUMAN_APPROVAL_REQUIRED = YES (execution methodology, not dataset freeze).

Official SZSE 2021 rules 3.3.5 and 2023 handbook printed page35 restrict MARKET
submissions to continuous auction and price-limited securities.
ResearchExecutionEngine instead creates MARKET orders and SimulatedBroker fills
them at next daily open. Accepted daily OHLCV cannot identify the execution
phase/order book or establish opening-auction liquidity (2021 rules 4.2.1-4.2.2).
Do not quietly change the execution convention to manufacture a rule PASS.

Smallest next decision: approve a conservative, explicitly priced, next-session
LIMIT/auction convention using only information known before submission, with
unprovable compliance/no auction evidence handled as no-fill, or retain the
existing convention and stop. This is NOT approval to run a strategy/study.

After that decision, ordinary engineering and evidence closure remain in the
28-claim ledger: 12 unclosed claims include caps/ticks/expiry, relisting and
intraday handling, and Pilot settlement-fee provenance. Approval does not erase
these gaps or automatically pass the source gate. No new provider is selected.

OLD SZSE_2023_RULE_BYTES_UNAVAILABLE = RETIRED_REQUIREMENT.
All four replacement official sources retrieved; no dead URL retried.
DOCKER_RUNTIME_FAILURE = RESOLVED.
PUSH_IDENTITY_MISMATCH = RESOLVED; MakenzieAhern unchanged.
Prior seven data authority PASS decisions preserved. This is not Gate A.
