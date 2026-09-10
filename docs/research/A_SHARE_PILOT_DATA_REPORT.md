# A-Share Pilot Data Report

Status: **NOT CREATED — BaoStock login unavailable**

Latest attempt date: 2026-09-10

- Intended ID: `cn-a-pilot-baostock-20230101-20240731-v1`
- Intended coverage: 2023-01-01 through 2024-07-31
- Bounded securities: SSE 600000/688001 and SZSE 000001/300001
- Intended benchmark: CSI300 bars and end-date membership
- Pilot checksum: unavailable

The pilot command uses BaoStock only, writes security identity, calendar, raw/adjusted bars, daily
status/limit locks, normalized corporate actions, CSI300 bars and membership to deterministic
Parquet outside Git. It was executed, but BaoStock port 10030 timed out before login. No fixture,
AKShare substitution or partial directory was called a real pilot.

The writer-level reproducibility test passes: identical normalized inputs in reversed input order
produce byte-identical Parquet, identical per-partition SHA-256 and identical metadata-independent
logical hashes. This does not claim that an uncreated real pilot has a checksum.

The official SSE/SZSE point-in-time master now passes the pilot gate with checksum
`d4b02d6934eed85fa8588c65c688de20cb39ee871c17044e41a27c63c140f0ba`. The command verifies that
master before provider login. BaoStock port 10030 timed out on the 2026-09-10 attempt, so no partial
dataset was retained and the overall pilot readiness remains blocked.
