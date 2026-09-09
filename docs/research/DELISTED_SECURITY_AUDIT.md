# Delisted Security and Survivorship Audit

Classification: **UNKNOWN**  
Assessment date: 2026-09-09

The deterministic audit targets the last open session on or before 2010-12-31, 2012-12-31,
2015-12-31, 2018-12-31, 2020-12-31, 2022-12-31, 2024-12-31 and 2025-12-31. For every snapshot it
records counts, identifies securities present historically but absent in 2025, then queries their
listing/exit dates, first/last bars and historical ST/tradeStatus.

The probe did not pass BaoStock login on 2026-09-09 because its TCP service timed out. Therefore no
snapshot counts or named delisted-security findings are published. Hard-coded expected counts would
not be an audit.

This unknown creates material survivorship risk: the frozen strategy cannot use today's active list
to reconstruct Development or Validation universes. The official gate remains blocked.

Round 2 adds the fail-closed `make audit-universe` command. It verifies effective-date boundaries,
future-IPO exclusion, exited-security retention, source versions, duplicate/overlapping identities,
history gaps and canonical checksums. Its current persisted result is
`SECURITY_MASTER_INPUT_MANIFEST_MISSING`, because no complete official SSE/SZSE exports were supplied.

Smallest free resolution: obtain the two official files described in
`POINT_IN_TIME_SECURITY_MASTER.md`, stage them with their SHA-256 manifest, and rerun the audit.
BaoStock can then be reconciled to that reference rather than treated as the authoritative universe.
