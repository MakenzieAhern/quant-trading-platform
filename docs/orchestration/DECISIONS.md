# Decisions

- 2026-09-10: Continue on existing branch/PR. No scheduler, new branch or conversation.
- Preserve accepted SSE/SZSE/master/calendar work. Ancient 600721 is full-history-only.
- A legacy PASS claim is not checksum-linked pilot authority acceptance.
- Execution always uses raw prices. Provider adjusted close is not an economic cash flow.
- Persist Gates A/B/C and false OOS/release flags. Current research CLI already refuses
  execution without readiness; state files do not grant permission to bypass it.
- Keep generated evidence outside Git; commit small reproducible code and summaries only.
- 2026-09-10 R1: New Sina factors are CANDIDATE_ONLY, not an implicit provider
  substitution. Different adjusted-price algorithms are not treated as corrupt
  data or interchangeable factors. Stop under the explicit authority-ambiguity
  exception while preserving all new recovery evidence; no normal gate reached.
