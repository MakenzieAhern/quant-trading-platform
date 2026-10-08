# Isolated successor dataset builds

This is an offline engineering entry point, not source/economic acceptance or a
UI dataset-registration command. The existing frozen v1 archive, `.research`,
methodology and Official OOS remain unchanged. The accepted v1.2 product goal
authorizes independent engineering; it does not approve incomplete source facts.

From `backend`, use the existing materializer with an explicitly selected JSON
specification and its independently recorded whole-file SHA-256:

```text
python -m scripts.materialize_full_dataset --repository /absolute/repository \
  --build-spec /absolute/new-build-spec.json --build-spec-sha256 <64-hex-SHA256>
```

`--staging` is the separate legacy mode; it cannot be combined with the new mode.
There is no fallback to `.research/project_state.json` in successor mode. The
strict schema is `CandidateBuildInputs` in `backend/scripts/full_dataset_build_inputs.py`:

- `operation`: `ISOLATED_SUCCESSOR_MATERIALIZATION`;
  `authorization_source`: `ACCEPTED_V1_2_PRODUCT_GOAL` (not a new human approval).
- New `dataset_id`, coverage `2010-01-01` through `2025-12-31`, stable UTC
  `recorded_at_utc`, separate `work_root` and `final_root`. Final directory name
  must equal the new ID. Outputs stay outside the repository, input trees and
  frozen ancestors; work/final must support a same-filesystem atomic rename.
- Exact existing 15 `source_contracts` and five `reference_pins`. Source paths
  retain the existing repository/backend-relative convention; the P0 report
  path is repository-relative. Work/final/raw/auxiliary relative paths use the
  specification directory. Absolute paths are recommended for retained specs.
- Five required `auxiliary_inputs`, each with `path` and `sha256`: adjustment inventory,
  rights inventory, normalized suspension events, feature-only observations and
  benchmark Parquet. Parent references are checked where they exist; normalized
  suspensions have an explicit byte pin, not an invented parent-output reference.
  Optional `ordinary_references` binds the existing canonical report containing
  `private_candidate_reference_rows`. Each price-only companion must match its
  exact cash/share event checksums, source, identity and date. It never replaces
  shareholder entitlements or becomes an accounting event.
- Exact nonempty `raw_sources.SSE` and `.SZSE` lists, each pinning `path`, `sha256`
  and adjacent `metadata_sha256`. Raw filename/metadata identity cannot use
  symlinks. Explicit `market_rule_manifest_sha256`; never inherit frozen state.

The new preflight must bind the new ID/coverage/operation, all nine existing
component results and an empty mandatory-incomplete list. Inspection-only,
partial or inherited legacy `approval` records are rejected. Its
`input_selection_sha256` is computed using the schema's method over normalized
absolute input paths: 14 non-preflight contracts, P0 pins, auxiliary/raw/meta
pins, rule digest, identity and timestamp. The preflight's own contract/digests
and output directories are excluded to avoid a circular hash. Changing the
selection requires a new genuinely verified preflight, not just resigning a spec.

Builds verify the exact bytes parsed, retain immutable ownership/report records
and bind the two entry-point files plus the shared event/session parser and byte-checksum helper. The raw parser requires
the exact selected raw/meta hashes. Resume validates the manifest, partitions,
source lineage and reconstructed report; it cannot inherit edited audit flags.
A crash after raw completion reuses those validated raw partitions. A crash after
final rename can recover only its missing publication receipt. Unknown ownership,
changed inputs/producers or incomplete split raw publication stop without
deleting/replacing published artifacts. This is not exhaustive crash durability.

Every build reports `dataset_audited=false`, `dataset_frozen=false`,
`dataset_registered=false` and `full_financial_admission=false`. No strategy,
provider acquisition, database, registration or freeze runs here.

## Current proof and remaining work

The full pipeline and CLI have been exercised with **synthetic** JSON/XLSX/
Parquet only: new identity without research state, fresh/reordered/resumed
checksums, and injected interruptions. See the latest acceptance checkpoint.
No real successor dataset has been materialized. The real source-reference
candidate remains inspection-only and cannot be fed to this entry point.

The current pipeline deliberately retains the legacy 239 feature-only rows,
24-merger census and approved cost convention; it is not a generic new market
or new methodology builder. Replace neither unresolved source facts nor
financial/lifecycle checks with fixture counts or old audit PASS literals.

## Independent candidate audit

The existing auditor accepts the same explicit inputs, without reading frozen
research state, rebuilding, registering or freezing:

```text
python -m scripts.audit_full_dataset --repository /absolute/repository \
  --dataset /absolute/new-dataset-id --output /absolute/reports/audit.json \
  --build-spec /absolute/new-build-spec.json --build-spec-sha256 <64-hex-SHA256>
```

The report must be outside the repository, owned build/dataset roots and input
files, with no symbolic/hard-link alias. It is immutable and repeatable for the
same inputs/code. The auditor checks candidate ownership, exact partition set,
source contracts, materialization report and manifest. It compares serialized
events with the bound source ledgers (including companions), validates typed
event records, and traverses actual sessions with execution metadata enabled.
All candidate Parquet reads and catalog-backed runtime reads hash and parse the
same partition bytes. Manifest file identity uses the same bytes as parsing,
and audit code identity is captured before input loading. One partition's bytes
are buffered during parsing; full-archive memory/time measurements remain open.
This runs no strategy or Portfolio. Missing reference-price explanations and
action dates absent from the accepted calendar remain explicit failures.

New reports separate reference rows from accounting rows and bind audit code.
Legacy accounting, lifecycle, input-order and restart PASS literals are not
inherited: unexecuted obligations remain `NOT_EVIDENCED`. A partial report is not
financial admission. The legacy three-argument audit and freeze interface stay
unchanged; no candidate report may be used to unlock old research/OOS.
