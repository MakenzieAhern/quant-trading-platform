# Unfrozen Pilot catalog publication and audit

The R2 composer reuses verified `materialize_akshare_partitions` receipts and the
accepted source snapshots. It cannot publish while any in-scope security input,
partition, source preflight, instrument classification or amount check is unresolved.
The approved scope is 5177 ordinary A shares from 5178 candidates; the CDR ledger
is metadata, never a market-data requirement. Original 2580 receipts remain pinned.

Run from `backend` with the existing pinned provider SDK and PyArrow environment:

```text
python -m scripts.publish_akshare_pilot --staging STAGING --repository REPOSITORY --prepare-calendar-history --sdk-root SDK
python -m scripts.materialize_akshare_partitions --staging STAGING
python -m scripts.audit_amount_impact --staging STAGING --repository REPOSITORY --sdk-root SDK --include-recovered
python -m scripts.publish_akshare_pilot --staging STAGING --repository REPOSITORY
python -m scripts.publish_akshare_pilot --staging STAGING --repository REPOSITORY
python -m scripts.audit_published_pilot --staging STAGING --dataset DATASET
```

The first command only decodes the already accepted calendar snapshot offline,
retaining December 2022 sessions for IPO-age resolution. It must reproduce all
382 accepted Pilot sessions exactly. Do not re-fetch accepted authorities.

Publication builds below external staging and atomically renames the completed
catalog to `STAGING/../cn-a-pilot-akshare-20230101-20240731-v1`. Existing raw/factor
Parquet bytes are copied without re-encoding. Every partition has physical and
logical SHA-256 receipts; the canonical manifest is immutable. Interrupted builds
reuse the persisted input digest and original build timestamp. Changed inputs
fail closed. The second publication invocation verifies real resume without source
requests or partition rewriting. Synthetic interruption coverage is also in tests.

The catalog separates raw bars, HFQ feature factors, point-in-time daily risk
states, master/lifecycle metadata, explicit out-of-scope evidence, missing-observation
intervals, calendar, CSI300 price-index bars, effective rules and provenance contracts.
It does not infer index membership from benchmark prices.
Master names are display metadata, not historical-name or ST eligibility inputs.

Missing observations are not synthetic bars or inferred suspensions. The accepted
daily execution convention requires independent official tradeability evidence;
OHLCV alone does not supply it. Therefore official daily `is_suspended` and
`is_tradeable` remain null, and execution is no-fill unless separate evidence is
available. Known dated delisting-period starts are retained from accepted timelines;
unknown dates are not invented. `pre_close` is not fabricated. Separate HFQ curves
are as-of feature inputs, not execution prices or a complete cash-distribution ledger.

R3 replays scope, source normalization, lifecycle/calendar, official ST state,
factor temporal safety, effective rule/cost selection and partition checksums.
Rule-resolution checks use an explicitly conservative no-fill proxy; this is not
written back as an official suspension fact. Reversed input rows must reproduce
every physical and logical partition hash. Source authority decisions are reused,
not reopened. Audit output lives outside the immutable catalog.

Only a complete passing audit permits `DATASET_AUDITED=YES` and Gate A readiness.
These commands never freeze the dataset, authorize a study, merge PR #12, or create
a release. The human freeze gate remains mandatory.
