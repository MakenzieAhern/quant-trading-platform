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
- Five `auxiliary_inputs`, each with `path` and `sha256`: adjustment inventory,
  rights inventory, normalized suspension events, feature-only observations and
  benchmark Parquet. Parent references are checked where they exist; normalized
  suspensions have an explicit byte pin, not an invented parent-output reference.
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
and bind the two entry-point source files. The shared raw parser also requires
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
or new methodology builder. Next integrate the already implemented price-only
`ORDINARY_REFERENCE` companions and version-aware actual audit results using
the explicit candidate inputs. Replace neither unresolved source facts nor
financial/lifecycle checks with fixture counts or old audit PASS literals.
