# R5 SZSE terminal-suspension closure v1

Status: **42 SOURCE-BOUND TERMINAL CLOSURES ACCEPTED; AUTHORITY REMAINS PARTIAL**.

The prior suspension audit could close an unresolved SZSE event only with an
official resumption date. That left direct-to-delisting suspensions unresolved
even when the retained official issuer notice said both that the stock stopped
on the exact event date and that it would not enter a delisting-consolidation
period.

The v1 terminal pass scanned 3,391 already retained, checksum-verified official
CNINFO documents. It accepts a closure only when all of these hold:

1. the official issuer PDF states the exact suspension date;
2. the same PDF states that the stock does not enter a delisting-consolidation
   period;
3. the accepted official SZSE point-in-time master supplies one matching
   terminal lifecycle date for the same stable security identity; and
4. source bytes, extracted text, master source, retrieval timestamp and SHA-256
   remain bound in the output.

No `resumed_at` value is created for these events. They are represented as
`OFFICIAL_TERMINATION_NO_DELISTING_PERIOD` with a separate `terminal_at`
boundary. Reverse-input replay is byte-logically identical.

Results:

- SZSE target suspension events: **22,077**
- prior unresolved exact boundaries: **1,921**
- new official terminal closures: **42**
- current unresolved exact boundaries: **1,879**
- official resumption supplements retained: **8,884**
- resumption conflicts: **0**
- SSE unresolved suspension facts: **0**

Immutable terminal report:

- path: `/home/yuchen/data/research/staging/full-szse-terminal-suspension-v1/szse-terminal-suspension-closures-v1.json`
- file SHA-256: `5fc6f264c028b9a6064913860bafa0459e3e1221763bb5eaa33f9ab261184b7e`
- canonical manifest SHA-256: `70ef1ae3b94e908dcf84db8592606e7cd4051793b38f9b2620651b00930f0522`

Full replay:

- authority file SHA-256: `860eb85aacb18c548b1251eec9ab681690c91b434c9dae447c52e87ae39bfd13`
- authority manifest SHA-256: `5cc9d7a86dd57342d2f8d0da8addb4ad5ab5b70ee1db949518891295701a21a0`
- normalized-event file SHA-256: `eaebe56db7e155873d35fc761c0fdd77651e095477d434a57fa45c7714d90e48`
- unresolved file SHA-256: `5064b693279df3c38ed10efce78048723c8e3c94a3e572362a7b02797aa3d906`

This is real suspension-ledger progress, not a Full Dataset PASS. The 1,879
remaining exact resumption boundaries, 239 ChiNext raw-source dates, P1
corporate-action gaps and retained-bonus fractional-accounting gate remain
open. No dataset, strategy result or freeze was produced.
