# Bounded command search

The command palette searches personal study names/UUIDs and saved watchlist
security IDs, symbols, names and source-observed names on the server. It does not
search formal research report contents or imply source-observed names are historical
point-in-time names. Pages and the registered strategy catalog are matched locally.

- `GET /api/experiments?q=...&limit=20&offset=...`
- `GET /api/markets/watchlist?q=...&limit=20&offset=...`

`q` is optional (empty preserves existing listing behavior), limited to 80 characters,
trimmed, and matched as a case-insensitive literal substring. SQL wildcard characters
are escaped. Filtering precedes count and pagination; older records outside the first
page remain discoverable. The UI debounces 250 ms, aborts superseded reads, and loads
only an explicitly requested page of up to 20 matches per category. Failures are not
rendered as empty results. No query causes acquisition or a research job.

Watchlist links carry `/markets?dataset=<saved dataset ID>&q=<security ID>`.
The markets reader honors explicit sources including synthetic-demo datasets;
unknown or unavailable sources are shown as unavailable, never silently replaced
with historical or demo data.
