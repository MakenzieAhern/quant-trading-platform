# R5 official public-source fact closure V2

Status: **PASS for corporate-action source facts**. P1 cumulative V68 establishes
**16,318 / 16,320** required facts with **2,034** explicit official-source
substitutions. The two residual requirements are non-corporate authorities:
`RAW:FULL_UNIVERSE` and `SUSPENSION:FULL_DAILY`.

The two cross-market merger paths are closed by their retained official
conversion, registry and successor-listing chains under the already-approved
merger policies. 301262 is closed at 2023-10-31 by its issuer implementation
notice plus the official SZSE 2023 factbook; the malformed date in the notice is
retained, not silently repaired. The 601607 and 603408 distributions are outside
the requested range because their ex/accounting date is 2026-01-05. The empty
cash queue proves **13,590 / 13,590** P1 cash documents supported.

Immutable evidence:

- cumulative V68: file `455d5cea86036679c55e49f1eb0aab71108556d5e0413345b333e544f69c03f9`, manifest `bff24c37eca440a94cb89ed4357d60bd68d15ce4fac1fc0c6243d6fdd0b06890`;
- merger V3: file `a6f7978e2d3d4418bda3f5fcae108db8d297b764fa07b5adbcb500eee8cf1ba9`, manifest `d8f81b0c46d76ff515de5139a2c87fed210453de0e02bf9e61d24acef2d3f382`;
- 301262 V1: file `b77955f12e11a26cd0bc78a8abb9fefbe975ff2f6df1d4010c9028f1a8b16446`, manifest `220951490ae088b16b3d8fb84f6eb6c881f0d1bf81197d686edb5915b4c5990b`;
- out-of-period V4: file `062716f5bd34bd2ca800e5b8d25ca4e183dca446b2e6e377ff87556a4f1cc8cd`, manifest `22a53f84c40e38a1324933a497b235aac5038a908873ab239ac5aa54babf915c`;
- empty cash queue V21: `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`.

This closes the corporate-action source queue only. It does not promote raw,
suspension, adjustment or transaction-cost authority, create the Full Dataset,
or authorize a strategy run.
