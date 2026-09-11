# Checkpointed Tencent recovery

The frozen CN_A_RAW_OHLCV_FAILOVER_V1 policy follows the decision-impact acceptance,
not the superseded exact-rounding blocker. The primary recovery-checkpoint.json is
immutable:657 successes are neither requested again nor replaced. Secondary
successes, immutable request slots, failures and pending identities live separately
in secondary-checkpoint.json / secondary-failure-manifest.json outside Git.

Run from backend with the existing approved external staging and repository paths:

    python -m scripts.stage_tencent_pilot --staging /external/staging --repository /repo
    python -m scripts.materialize_akshare_partitions --staging /external/staging

The optional --limit is only a bounded engineering smoke batch; the unlimited
continuation resumes unprocessed slots rather than restarting successful ones.
Policy, consumer and primary-checkpoint hashes are checked before acquisition.
Only persisted round2 RemoteDisconnected primary failures are scheduled in this
current recovery state. There is no primary network request in the new command.

The2023 SDK query spans2023-01-01..2024-12-31, already encompassing the full Pilot.
Offline comparison of260 recovered histories proved its normalized rows identical
to the two-query merge for every security. New requests omit the redundant2024
query; all existing two-query evidence remains untouched. This reduces requests,
not coverage, retry bounds, validation or source authority. The retrieval worker
was stopped in its two-second inter-batch wait immediately after a complete
checkpoint replacement, then resumed from that checkpoint.

Two workers, two-second inter-batch spacing,35-second request timeout, one initial
and one final transport-only retry round with60-second backoff; no jitter or
access-denial bypass. Failed request slots remain immutable and preserve retry
classification across restart. Successful candidate/raw/factor snapshots are reused
only after request identity and source hash validation. No adjusted-price fallback.

Each recovery requires raw day data, normalized Decimal OHLC and volume, accepted
calendar/lifecycle membership, unique dates, reproducible year overlap, two-place
upstream amount representation and zero ambiguous potentially evaluated amount
decisions under the unchanged frozen rule. Ambiguity or access denial stops and
persists evidence. Other failures remain explicit; no missing record becomes a
suspension, exclusion, normal status, fabricated price or unit factor.

Separate accepted Sina HFQ data must establish the first-observation baseline.
Normalized raw sources retain every upstream source URL/parameter, retrieval UTC,
raw hash, provider/interface, policy hash, primary-failure hash and date coverage.
Parquet rows explicitly identify Tencent or Eastmoney, never relabeling one as the
other. Source responses retain the original upstream amount strings.

The materializer combines disjoint completed inventories; original primary byte
hashes remain unchanged. It verifies source and existing partition hashes, then
writes separate raw/factor Parquet partitions atomically. Repeat/lost-receipt tests
cover both providers. These are partial inputs, not a final manifest or full R3.
All required inputs and full dataset audits remain prerequisites for Gate A.

Smoke recovery retained600070 and600077, with486 additional raw rows and two factor
rows; initial materialization659 securities/244,559 raw rows, zero failures.
Full queue continues from this checkpoint.405 backend tests, Ruff/format and strict
mypy PASS before the acquisition milestone. No dataset freeze, studies or PR merge.
