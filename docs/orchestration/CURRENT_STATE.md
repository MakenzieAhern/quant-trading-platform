# Current state

R1 BLOCKED at an authoritative-source ambiguity, not at a normal milestone.
Dataset not created/audited/frozen. OOS and release unauthorized.
Branch `feature/a-share-research-v1.1`, PR #12 open/unmerged; starting HEAD
`92a08589bead59227568888eabb97a071185fae4`, clean and synchronized.
Master/SSE/SZSE/calendar acceptance preserved. Remaining authority checks:
adjustment, raw OHLCV binding, CSI300 binding and market-rule evidence.
BaoStock 0.8.9 factor login failed twice. Four Sina HFQ candidate samples repeat
exactly, including exited securities, but they are not prior accepted authority.
Windows HTTPS reached the existing Eastmoney raw route; WSL requests failed.
600000 on 2023-07-17/18 proves Eastmoney HFQ is not interchangeable with a single
Sina-style multiplicative factor even allowing half-cent rounding. Neither is
declared corrupt; the research methodology needs an authoritative definition.
Details: `docs/research/R1_ADJUSTMENT_AUTHORITY_REPORT.md`.

Next: obtain the prior audited adjustment definition or a human decision resolving
the new method's authority, then complete its validation and remaining R1 checks.
Gate A is NOT reached. This is the explicitly allowed source-ambiguity exception.

Machine authority: `.research/project_state.json`; no study or freeze authorized.
The read-only `python -m scripts.project_controller --root /path/to/repository`
returns STOP. Its checks validate state consistency, not external evidence truth;
the controller must inspect checksum-linked artifacts before changing acceptance.
