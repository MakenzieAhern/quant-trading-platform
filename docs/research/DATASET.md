# Frozen A-share research dataset

## Identity

- Dataset: `cn-a-research-20100101-20251231-v1`
- Coverage: 2010-01-01 through 2025-12-31
- Canonical manifest SHA-256:
  `1d7b6134e2c6a7026aa124bed57ab101ea910847e10e3d799c45f6c6a1e17f9e`
- Freeze-record SHA-256:
  `1a89b5d8b6e9bc7b3cc079f0bd426afac294383cfdce0a25af8eb9c980513fc3`
- Securities: 5,431 historically validated ordinary A-shares
- Trading sessions: 3,886
- Raw daily rows: 13,411,189
- Corporate-action rows: 42,792

Large source snapshots and Parquet partitions stay outside Git. The repository stores schemas,
normalizers, audit code, source decisions, checksums and immutable freeze receipts.

## Point-in-time construction

Membership comes from effective-dated SSE/SZSE security-master intervals, not today's listed
universe. A security becomes eligible only after its listing boundary and remains represented
through its accepted delisting boundary. Board, symbol, ST/*ST, suspension and market-rule state
are resolved for each research date. Future IPOs and later rule/name states cannot leak backward.

The v1.1 scope is ordinary RMB-denominated A-share equities on SSE Main/STAR and SZSE
Main/ChiNext. CDRs, B-shares, funds/ETFs, bonds, preferred shares, warrants and other instrument
types are excluded by the approved instrument contract, not by observed strategy performance.

## Price and event layers

- Raw, unadjusted OHLCV is the only execution-price layer.
- Audited adjustment factors produce factor history separately; adjusted prices are never fills.
- Explicit feature-only observations preserve approved factor continuity but are non-tradable.
- Trading calendar, CSI300 benchmark, ST/*ST, suspensions and transaction-cost schedules are
  effective-dated inputs.
- Cash distributions, rights issues, mergers, demergers, mandatory partial surrenders,
  restructuring bonus pass-through and share consolidations are explicit accounting events.

## Integrity and audit

Every partition has a SHA-256 recorded by the canonical manifest. Loading fails closed when the
freeze record, manifest, required partition, calendar continuity, identity interval or event
contract differs. The final R5 audit passed all 29 mandatory gates, including survivorship,
future IPO, delisting retention, look-ahead, stable identity, OHLC validity, calendar continuity,
adjustment separation, suspension handling, checksum/input-order repeatability, restart/resume and
six structural-accounting invariants. Required unresolved data and failed sources are zero.

The manifest and `.frozen.json` receipt are the authority. Copying files without matching those
bytes does not create an accepted dataset.
