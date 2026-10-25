"""Build an isolated source-reference inspection, never a dataset or an approval."""

import argparse
import json
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.full_dataset_sources import (
    SOURCE_NAMES,
    source_path,
    verify_source_contracts,
    verify_source_lineage,
    verify_source_manifest,
)


def _record(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    result = {**payload, "manifest_sha256": canonical_sha256(payload)}
    write_immutable(path, canonical_json_bytes(result) + b"\n")
    return result


def inspect(
    repository: Path,
    dataset: Path,
    output: Path,
    input_proof: Path,
    input_proof_sha256: str,
    evidence: list[tuple[Path, str]],
) -> dict[str, Any]:
    repository, dataset, output = repository.resolve(), dataset.resolve(), output.resolve()
    candidate_root = dataset.parent.parent / "product-candidates"
    if (
        output.parent != candidate_root
        or output.is_relative_to(repository)
        or output.is_relative_to(dataset.parent)
        or any((parent / ".freeze.json").exists() for parent in (output, *output.parents))
        or any(
            (output / name).is_symlink()
            for name in (
                "inspection-preflight.json",
                "inspection-contracts.json",
                "inspection-pins.json",
                "inspection-report.json",
            )
        )
    ):
        raise ValueError("CANDIDATE_OUTPUT_NOT_ISOLATED")
    input_proof = input_proof.resolve()
    if sha256_file(input_proof) != input_proof_sha256:
        raise ValueError("SOURCE_INPUT_PROOF_BYTES_CHANGED")
    proof = json.loads(input_proof.read_bytes())
    if proof["full_financial_admission"] is not False:
        raise ValueError("SOURCE_INPUT_PROOF_NOT_INSPECTION")
    state_path = repository / ".research/project_state.json"
    state = json.loads(state_path.read_bytes())
    rows = sorted(
        pq.read_table(dataset / "source-contracts.parquet").to_pylist(),
        key=lambda row: row["name"],
    )
    if len(rows) != len(SOURCE_NAMES) or {row["name"] for row in rows} != SOURCE_NAMES:
        raise ValueError("SOURCE_CONTRACT_SET_CHANGED")
    original = {row["name"]: dict(row) for row in rows}
    authority_path = (repository / state["p0_public_report_path"]).resolve()
    paths = {source_path(repository, row["source_path"]) for row in rows}
    paths.update(
        {
            authority_path,
            state_path,
            dataset / "source-contracts.parquet",
            dataset / "manifest.json",
            dataset / ".freeze.json",
        }
    )
    before = {str(path): sha256_file(path) for path in sorted(paths)}
    if before != proof["input_sha256"]:
        raise ValueError("SOURCE_INPUT_PROOF_BINDINGS_CHANGED")
    master_sha = proof["actual_master_authority"]
    verify_source_manifest(authority_path, master_sha)
    contents = {}
    for row in rows:
        path = source_path(repository, row["source_path"])
        if sha256_file(path) != row["source_file_sha256"]:
            raise ValueError("SOURCE_CONTRACT_BYTES_CHANGED")
        contents[row["name"]] = verify_source_manifest(
            path,
            master_sha if row["name"] == "SECURITY_MASTER" else row["source_manifest_sha256"],
            master_authority_path=authority_path if row["name"] == "SECURITY_MASTER" else None,
        )
    evidence_bindings = {}
    for path, expected in sorted(evidence):
        path = path.resolve()
        if str(path) in evidence_bindings:
            raise ValueError("DUPLICATE_INSPECTION_EVIDENCE")
        verify_source_manifest(path, expected)
        evidence_bindings[str(path)] = {
            "manifest_sha256": expected,
            "file_sha256": sha256_file(path),
        }
    all_inputs = dict(before)
    for input_path, expected in [(str(input_proof), input_proof_sha256)] + [
        (path, binding["file_sha256"]) for path, binding in evidence_bindings.items()
    ]:
        if input_path in all_inputs and all_inputs[input_path] != expected:
            raise ValueError("INSPECTION_INPUT_BINDING_CONFLICT")
        all_inputs[input_path] = expected
    # Copy only reference fields, never old PASS/status/approval or economic assertions.
    old_components = contents["SOURCE_PREFLIGHT"]["components"]
    fields = {
        "st_history": ("sse_manifest_sha256", "szse_probe_sha256"),
        "suspension_history": ("authority_manifest_sha256",),
        "adjustment_factors": ("authority_report_manifest_sha256", "authority_report_file_sha256"),
        "trading_calendar": ("manifest_sha256",),
        "csi300_benchmark": ("manifest_sha256",),
        "market_rules_and_transaction_costs": ("report_manifest_sha256", "report_file_sha256"),
    }
    components = {
        component: {key: old_components[component][key] for key in keys}
        for component, keys in fields.items()
    }
    components["security_master"] = {"manifest_sha256": master_sha}
    boundary = {
        "status": "INSPECTION_ONLY",
        "scope": "FULL_SOURCE_REFERENCE_CHAIN_NOT_DATASET_AUTHORITY",
        "financial_coverage": "PARTIAL",
        "full_financial_admission": False,
        "approval_inherited": False,
        "dataset_created": False,
        "dataset_registered": False,
        "frozen_dataset_modified": False,
        "strategy_run": False,
    }
    preflight_path = output / "inspection-preflight.json"
    preflight = _record(
        preflight_path,
        {
            **boundary,
            "components": components,
            "historical_preflight_reference": original["SOURCE_PREFLIGHT"],
            "evidence_bindings": evidence_bindings,
            "evidence_semantics": "Bound historical observations; no financial approval inferred.",
        },
    )
    candidate = {row["name"]: dict(row) for row in rows}
    candidate["SECURITY_MASTER"]["source_manifest_sha256"] = master_sha
    candidate["SOURCE_PREFLIGHT"].update(
        source_path=str(preflight_path),
        source_manifest_sha256=preflight["manifest_sha256"],
        source_file_sha256=sha256_file(preflight_path),
        status="INSPECTION_ONLY",
    )
    pins = {
        "p0_public_report_path": str(authority_path),
        "p0_public_report_manifest_sha256": master_sha,
        "p0_public_report_file_sha256": sha256_file(authority_path),
        "full_source_preflight_manifest_sha256": preflight["manifest_sha256"],
        "full_source_preflight_file_sha256": sha256_file(preflight_path),
    }
    contracts = list(candidate.values())
    verified = verify_source_contracts(contracts, repository, pins)
    if verified != verify_source_contracts(list(reversed(contracts)), repository, pins):
        raise ValueError("SOURCE_INPUT_ORDER_CHANGED")
    lineage = sorted(f"{row['name']}:{row['source_manifest_sha256']}" for row in contracts)
    verify_source_lineage(contracts, lineage)
    unchanged = sum(row == original[row["name"]] for row in contracts)
    if unchanged != len(SOURCE_NAMES) - 2:
        raise ValueError("CANDIDATE_UNEXPECTED_REFERENCE_CHANGE")
    _record(
        output / "inspection-contracts.json",
        {
            **boundary,
            "contracts": contracts,
            "row_status_semantics": "Retained source status is historical, not candidate approval.",
        },
    )
    write_immutable(output / "inspection-pins.json", canonical_json_bytes(pins) + b"\n")
    if any(sha256_file(Path(path)) != expected for path, expected in all_inputs.items()):
        raise ValueError("INSPECTION_INPUT_CHANGED_DURING_PUBLICATION")
    # The report is the final completion record; partial output is never registered.
    return _record(
        output / "inspection-report.json",
        {
            **boundary,
            "reference_integrity": "VERIFIED",
            "legacy_dataset_source_integrity": "FAIL_UNCHANGED",
            "source_contract_count": len(contracts),
            "unchanged_contract_rows": unchanged,
            "source_lineage": lineage,
            "input_order_reproducibility": "PASS",
            "input_bytes_sha256": all_inputs,
            "output_bytes_sha256": {
                name: sha256_file(output / name)
                for name in (
                    "inspection-preflight.json",
                    "inspection-contracts.json",
                    "inspection-pins.json",
                )
            },
            "code_sha256": {
                str(path): sha256_file(path)
                for path in (
                    Path(__file__).resolve(),
                    Path(__file__).with_name("full_dataset_sources.py").resolve(),
                    Path(__file__).resolve().parent.parent / "app/data/catalog/checksums.py",
                    Path(__file__).resolve().parent.parent / "app/data/catalog/freeze.py",
                )
            },
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "dataset", "output", "input-proof"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument("--input-proof-sha256", required=True)
    parser.add_argument(
        "--evidence", nargs=2, action="append", default=[], metavar=("PATH", "SHA256")
    )
    args = parser.parse_args()
    report = inspect(
        args.repository,
        args.dataset,
        args.output,
        args.input_proof,
        args.input_proof_sha256,
        [(Path(path), expected) for path, expected in args.evidence],
    )
    print(
        json.dumps(
            {key: report[key] for key in ("status", "reference_integrity", "manifest_sha256")}
        )
    )
