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

Smallest free resolution: rerun `backend/scripts/audit_baostock.py` when BaoStock is reachable and
reconcile its exited-code sample against official SSE/SZSE termination-of-listing announcements and
historical listed-company directories. Any code missing from BaoStock history must be excluded by an
explicit availability rule, with the resulting coverage bias quantified before research approval.
