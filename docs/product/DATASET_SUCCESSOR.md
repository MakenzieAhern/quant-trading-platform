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
  Optional `ordinary_dates` binds a versioned source-date inventory described
  below. Both producer and auditor apply it before checking price companions.
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

## Source derived ordinary distribution dates

`ordinary_dates` is a pinned JSON file with `version` equal to
`ORDINARY_DISTRIBUTION_DATES_V1` and a nonempty `items` array. Each item contains
the original `event_checksum`, `source_pdf` (`path`, `sha256`) and `source_title`.
PDF paths are relative to this inventory, not the build specification. Dates are
derived from the verified PDF bytes; the input cannot supply replacement dates.
The inventory participates in the preflight input selection, and its nested
PDFs are checked for changes and input/output overlap before publication.

Only the reviewed final SZSE distribution-notice layout is supported. The PDF
heading must identify the original issuer and title. Cash payment requires a
consistent labeled date and explicit agency transfer wording; bonus listing
uses the existing all-holder credit and unrestricted-listing parser. Conflicting,
tentative, holder-specific or unsupported terms fail closed. Both dates must
equal the existing ex-date; delayed entitlement accounting needs separate work.

The shared normalizer replaces exactly one existing ordinary event per target.
It changes only missing `payment_date` for cash or `listing_date` for bonus
shares. All other typed fields, amounts, original source identity, completeness
and tradability remain unchanged. New event checksums and the complete original
acceptance object are retained in an explicit lineage envelope; old findings
are not deleted or relabeled. Existing price companions carrying the old event
checksums are rejected, not automatically rebound. The audit reports these date
replacements separately from the still-unproven financial and lifecycle gates.

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

`ACTION_SESSION_PRECONDITIONS` runs the same holding-independent validation as
the production research engine, before any financial mutation: ambiguous or
concurrent actions, supported policies, application dates, holder-class metadata,
pass-through trading conflicts and surrender resumption-boundary requirements.
Ordinary share listing dates must be the ex session or the next accepted session.
Both callers provide the calendar successor explicitly; unknown successor means
no later listing can be accepted, not that validation is skipped. The audit uses
the full accepted trading calendar, including a known period-end successor, never
the affected security's price dates. Null legacy listing metadata remains unknown
under the existing policy. This check does not establish missing source dates.
Failures retain the observed session date and reason; the helper's source file
is bound before input loading and rechecked before report publication. This does
not prove actual account holder eligibility (the loader supplies event metadata),
complete issuer lifecycles, source economics or any cash/basis/PnL reconciliation.

New reports separate reference rows from accounting rows and bind audit code.
Legacy accounting, lifecycle, input-order and restart PASS literals are not
inherited: unexecuted obligations remain `NOT_EVIDENCED`. A partial report is not
financial admission. The legacy three-argument audit and freeze interface stay
unchanged; no candidate report may be used to unlock old research/OOS.

### Retained negative source evidence

Candidate audit optionally accepts `--known-source-gaps /absolute/gaps.json`
and `--known-source-gaps-sha256 <whole-file-sha256>` together. These are audit
evidence, not builder inputs or a replacement preflight. The input path is
resolved once, parsed from exactly the hashed bytes, protected from output aliases
and rechecked before immutable publication. Legacy audit rejects these options.

The existing `KNOWN_EVENT_SOURCE_CONTRADICTIONS_NOT_WHOLE_SECURITY_EXCLUSIONS`
inventory binds security/record/ex/PDF-SHA/URL and preserves its complete findings.
All typed ordinary cash/stock/bonus events are checked, including base events and
ordinary events carried under either CorporateAction container label. Price-only
companions, genuine rights and structural multi-document events are not ordinary
economics. Match original document references OR the same security and either
event date; partial identity changes remain unresolved, not silently cleared.
No whole-security exclusion or entitlement correction occurs.

`SOURCE_ECONOMIC_INTEGRITY` is FAIL on related negative evidence and otherwise
NOT_EVIDENCED, including missing inventories and unmatched entries. A negative
list cannot establish complete economics. Simultaneously replacing all identity
and reference anchors is outside this join's evidence; full source/event-set
binding and genuine admission remain required. No accounting or strategy runs.

### Official cash aggregate corrections

The same gap input can carry a `cash_aggregate_corrections` extension. It does
not change the CLI, materializer, financial events or runtime admission. The
extension has `version: CASH_AGGREGATE_CORRECTIONS_V1`, a `parent_inventory`
file pin, and nonempty `items`. Removing this extension must reproduce the
complete parent inventory; only record ordering may differ. Old findings and
their source contradictions remain in the report.

Each item supplies `security_id`, `record_date`, `ex_date`, and five file pins:
`original_pdf`, `correction_pdf`, `correction_receipt`, `official_index`, and
`official_index_receipt`. Each pin is `{path, sha256}`; relative paths use the
gap inventory directory. All resolved inputs are protected from output aliases
and rechecked before publication, alongside the parser code.

The supported one-page CNINFO correction must explicitly change only the
aggregate cash total in an otherwise identical paragraph. Verification reads
the actual hashed PDF and metadata bytes, binds the original notice/issuer and
first-page paragraph, checks exact monetary arithmetic and the unchanged
per-holder cash/share terms, and rejects additional changes outside the quoted
paragraphs. Official metadata supplies the full publication timestamp; retrieval
time is not historical knowledge time. The correction must predate the record
day in Asia/Shanghai. Other layouts remain unsupported, not implicitly accepted.

`source_text_resolutions` records the evidence and its match to current candidate
events separately from the unchanged negative `findings`. Cash/share legs must
have the exact identity, source, amounts and application dates; changed event
checksums after separately evidenced date normalization are not automatically
disqualifying. Remaining matched contradictions keep the gate FAIL. Even with
every known text contradiction explained, the gate is only NOT_EVIDENCED and
financial admission remains false: this does not establish complete source
coverage, payment/listing dates, holder eligibility or correct accounting.
