# Source Input Requirements V1

As of 2026-09-15, all safe retained-evidence R5 queues are exhausted. The
detailed immutable manifest is:

`/home/yuchen/data/research/staging/source-input-requirements-v1/manifest.json`

- Required authoritative-source items: 16,328
- Material methodology-decision items: 664
- Canonical manifest SHA-256: `e20492797f1249ecf2dc8dd5ef8b06f252199df2883425dca4c82a1045365edc`
- File SHA-256: `20dcd8d612927dc91080d91c55fe2ac1d7da110099f021900de19940eefcbf53`

The source items are grouped by authority and year in the machine-readable
manifest. Each row records the security/event/range, required document type,
authority, reason, affected state, materiality, known URL and HTTP state, local
copy result, alternate-official-source check and whether R5 can proceed without
it. The largest group is 14,347 unavailable CNINFO official issuer disclosures;
the remaining 1,981 items cover exact cash/bonus terms, SSE ST chains, merger
execution evidence, master lifecycle, suspension, historical rules, raw OHLCV
and adjustment-factor authority.

The one unresolved methodology class is
`ORDINARY_A_SHARE_HOLDER_CLASS_AND_PER_SHARE_CASH_POLICY_FOR_DIFFERENTIATED_DISTRIBUTIONS`.
It affects 664 cash groups. No exchange average, unique notice amount or inferred
amount was admitted without that policy.

Metadata-only limitations remain non-blocking and explicit: 23,642 cash payment
dates not normalized, 149 rights-event metadata gaps and one SSE 600179
supplemental metadata variant. They do not alter eligibility, quantity, cash,
cost basis, execution, factors, benchmark alignment or research dates.

No denied CNINFO request was retried or bypassed, and no duplicate writer was
started. Full dataset creation, audit and freeze remain prohibited until the
material source and methodology requirements are resolved.
