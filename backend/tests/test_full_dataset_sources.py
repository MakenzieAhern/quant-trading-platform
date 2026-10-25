import json
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts import audit_full_dataset, freeze_full_dataset, materialize_full_dataset
from scripts.full_dataset_sources import source_path, verify_source_contracts, verify_source_lineage


def _candidate_inputs(tmp_path):
    (tmp_path / "inputs").mkdir()
    repository, _, dataset, authority, rows, state = _inputs(tmp_path / "inputs")
    # Preserve a defective historical reference and its historical PASS; never repair in place.
    state["p0_public_report_manifest_sha256"] += "a"
    next(row for row in rows if row["name"] == "SECURITY_MASTER")["source_manifest_sha256"] += "a"
    (repository / ".research/project_state.json").write_text(json.dumps(state))
    pq.write_table(pa.Table.from_pylist(rows), dataset / "source-contracts.parquet")
    (dataset / "manifest.json").write_text("{}")
    (dataset / ".freeze.json").write_text("{}")
    paths = {source_path(repository, row["source_path"]) for row in rows}
    paths.update(
        {
            authority,
            repository / ".research/project_state.json",
            dataset / "source-contracts.parquet",
            dataset / "manifest.json",
            dataset / ".freeze.json",
        }
    )
    proof = tmp_path / "source-check.json"
    proof.write_text(
        json.dumps(
            {
                "actual_master_authority": json.loads(authority.read_bytes())["manifest_sha256"],
                "full_financial_admission": False,
                "input_sha256": {str(path): sha256_file(path) for path in paths},
            }
        )
    )
    return repository, dataset, tmp_path / "product-candidates/inspection-v1", proof


def test_source_candidate_closes_full_chain_without_inheriting_approval(tmp_path):
    from scripts.inspect_source_reference_candidate import inspect

    repository, dataset, output, proof = _candidate_inputs(tmp_path)
    before = json.loads(proof.read_bytes())["input_sha256"]
    rows = pq.read_table(dataset / "source-contracts.parquet").to_pylist()
    evidence = [
        (source_path(repository, row["source_path"]), row["source_manifest_sha256"])
        for row in rows
        if row["name"] in ("ADJUSTMENTS", "SOURCE_PREFLIGHT")
    ]
    report = inspect(repository, dataset, output, proof, sha256_file(proof), evidence)
    assert report == inspect(
        repository, dataset, output, proof, sha256_file(proof), list(reversed(evidence))
    )
    assert report["status"] == "INSPECTION_ONLY"
    assert report["reference_integrity"] == "VERIFIED"
    assert report["full_financial_admission"] is False
    assert report["financial_coverage"] == "PARTIAL"
    assert report["unchanged_contract_rows"] == 13
    preflight = json.loads((output / "inspection-preflight.json").read_bytes())
    assert preflight["status"] == "INSPECTION_ONLY"
    assert "approval" not in preflight
    assert "r5_status" not in preflight
    pins = json.loads((output / "inspection-pins.json").read_bytes())
    assert len(pins) == 5
    candidate = json.loads((output / "inspection-contracts.json").read_bytes())["contracts"]
    verify_source_contracts(candidate, repository, pins)
    verify_source_lineage(candidate, report["source_lineage"])
    assert before == {path: sha256_file(source_path(repository, path)) for path in before}
    assert not (output / "manifest.json").exists()
    assert not (output / ".freeze.json").exists()


@pytest.mark.parametrize("corruption", ("proof", "source", "missing_pin", "evidence"))
def test_source_candidate_rejects_unbound_inputs_before_publication(tmp_path, corruption):
    from scripts.inspect_source_reference_candidate import inspect

    repository, dataset, output, proof = _candidate_inputs(tmp_path)
    pin = sha256_file(proof)
    evidence = []
    if corruption == "proof":
        proof.write_text("{}")
    elif corruption == "source":
        (dataset / "manifest.json").write_text('{"changed": true}')
    elif corruption == "missing_pin":
        content = json.loads(proof.read_bytes())
        del content["input_sha256"][str(dataset / "manifest.json")]
        proof.write_text(json.dumps(content))
        pin = sha256_file(proof)
    else:
        evidence = [(proof, "0" * 64)]
    with pytest.raises(ValueError):
        inspect(repository, dataset, output, proof, pin, evidence)
    assert not output.exists()


def test_source_candidate_evidence_cannot_rebind_an_original_byte_pin(tmp_path, monkeypatch):
    from scripts import inspect_source_reference_candidate as candidate

    repository, dataset, output, proof = _candidate_inputs(tmp_path)
    state = json.loads((repository / ".research/project_state.json").read_bytes())
    authority = source_path(repository, state["p0_public_report_path"])
    manifest = json.loads(authority.read_bytes())["manifest_sha256"]
    original_verify = candidate.verify_source_manifest
    authority_reads = 0

    def changed_during_evidence(path, expected, **kwargs):
        nonlocal authority_reads
        if path == authority:
            authority_reads += 1
            if authority_reads == 2:
                # Same canonical authority, different bytes after the original snapshot.
                authority.write_text(json.dumps(json.loads(authority.read_bytes()), indent=4))
        return original_verify(path, expected, **kwargs)

    monkeypatch.setattr(candidate, "verify_source_manifest", changed_during_evidence)
    with pytest.raises(ValueError, match="INSPECTION_INPUT_BINDING_CONFLICT"):
        candidate.inspect(
            repository, dataset, output, proof, sha256_file(proof), [(authority, manifest)]
        )
    assert not output.exists()


@pytest.mark.parametrize(
    "protected", ("dataset", "repository", "symlink", "file_symlink", "frozen_parent")
)
def test_source_candidate_cannot_publish_under_protected_ancestors(tmp_path, protected):
    from scripts.inspect_source_reference_candidate import inspect

    repository, dataset, output, proof = _candidate_inputs(tmp_path)
    if protected == "dataset":
        output = dataset / "product-candidates/inspection"
    elif protected == "repository":
        output = repository / "product-candidates/inspection"
    elif protected == "symlink":
        output.parent.symlink_to(dataset, target_is_directory=True)
    elif protected == "file_symlink":
        output.mkdir(parents=True)
        (output / "inspection-preflight.json").symlink_to(proof)
    else:
        output.parent.mkdir()
        (output.parent / ".freeze.json").write_text("{}")
    with pytest.raises(ValueError, match="CANDIDATE_OUTPUT_NOT_ISOLATED"):
        inspect(repository, dataset, output, proof, sha256_file(proof), [])
    if protected != "file_symlink":
        assert not (output / "inspection-preflight.json").exists()
    else:
        assert (output / "inspection-preflight.json").read_bytes() == proof.read_bytes()


NAMES = (
    "SOURCE_PREFLIGHT",
    "SECURITY_MASTER",
    "SSE_ST",
    "SZSE_ST",
    "SUSPENSIONS",
    "ADJUSTMENTS",
    "CASH_ACTIONS",
    "BONUS_ACTIONS",
    "GAP_DISTRIBUTION_ACTIONS",
    "RIGHTS_ACTIONS",
    "MERGER_ACTIONS",
    "STRUCTURAL_ACTIONS",
    "CALENDAR",
    "BENCHMARK",
    "MARKET_RULES_AND_COSTS",
)

STAGING_PATHS = {
    "SSE_ST": "full-sse-st-v1/sse-st-authority-v4.json",
    "SZSE_ST": "full-szse-st-v1/dated-name-coverage-probe-v9.json",
    "SUSPENSIONS": "full-suspension-revalidation-v36/suspension-authority-v1.json",
    "ADJUSTMENTS": "full-adjustment-audit-v1/full-adjustment-authority-v2.json",
    "CASH_ACTIONS": "full-distribution-notices-v1/cash-full-coverage-v43.json",
    "BONUS_ACTIONS": "full-bonus-inventory-v1/retained-bonus-ledger-v32.json",
    "GAP_DISTRIBUTION_ACTIONS": "full-adjustment-audit-v1/accepted-gap-distribution-ledger-v1.json",
    "RIGHTS_ACTIONS": "full-rights-inventory-v1/full-rights-census-v1.json",
    "MERGER_ACTIONS": "full-merger-v1/merger-candidate-census-v4.json",
    "STRUCTURAL_ACTIONS": "full-structural-census-v1/structural-action-census-v1.json",
    "CALENDAR": "full-calendar-v1/calendar-manifest-v3.json",
    "BENCHMARK": "full-benchmark-v1/acceptance-manifest-v2.json",
}


def _manifest(path, payload):
    content = {**payload, "manifest_sha256": canonical_sha256(payload)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content), encoding="utf-8")
    return content


def _inputs(tmp_path):
    repository = tmp_path / "repository"
    staging = tmp_path / "staging"
    dataset = tmp_path / materialize_full_dataset.DATASET_ID
    dataset.mkdir()
    master_path = staging / "full-master-public-v1-final/point-in-time-security-master.json"
    master_path.parent.mkdir(parents=True)
    master = [{"security_id": "CN-A:SZSE:000001", "effective_from": "2010-01-01"}]
    master_path.write_text(json.dumps(master), encoding="utf-8")
    authority_path = master_path.with_name("p0-public-reconstruction-report-v1.json")
    authority = _manifest(authority_path, {"reconstructed_master_sha256": canonical_sha256(master)})
    preflight_path = repository / ".research/preflight.json"
    preflight = _manifest(
        preflight_path,
        {
            "status": "PASS",
            "components": {"security_master": {"manifest_sha256": authority["manifest_sha256"]}},
        },
    )
    contracts = []
    for name in NAMES:
        if name == "SECURITY_MASTER":
            path, manifest = master_path, authority
        elif name == "SOURCE_PREFLIGHT":
            path, manifest = preflight_path, preflight
        else:
            path = (
                staging / STAGING_PATHS[name]
                if name in STAGING_PATHS
                else repository / "backend/fixtures" / f"{name}.json"
            )
            manifest = _manifest(
                path,
                {
                    "name": name,
                    "status": "PASS",
                    "SSE_HISTORICAL_ST_RECONSTRUCTION": "PASS",
                    "adjustment_authority": "PASS",
                },
            )
        contracts.append(
            {
                "name": name,
                "source_path": str(path)
                if name == "SECURITY_MASTER"
                else str(path.relative_to(repository / "backend", walk_up=True)),
                "source_file_sha256": sha256_file(path),
                "source_manifest_sha256": manifest["manifest_sha256"],
                "status": "PASS",
            }
        )
    state = {
        "r5_status": "RUNNING_FULL_DATASET_MATERIALIZATION",
        "p0_public_report_path": str(authority_path),
        "p0_public_report_file_sha256": sha256_file(authority_path),
        "p0_public_report_manifest_sha256": authority["manifest_sha256"],
        "full_source_preflight_report": str(preflight_path),
        "full_source_preflight_manifest_sha256": preflight["manifest_sha256"],
        "full_source_preflight_file_sha256": sha256_file(preflight_path),
        "full_dataset_audit_report": str(preflight_path),
        "full_dataset_materialization_report": str(preflight_path),
    }
    by_name = {row["name"]: row for row in contracts}
    preflight = _manifest(
        preflight_path,
        {
            "status": "PASS",
            "components": {
                "security_master": {"manifest_sha256": authority["manifest_sha256"]},
                "st_history": {
                    "sse_manifest_sha256": by_name["SSE_ST"]["source_manifest_sha256"],
                    "szse_probe_sha256": by_name["SZSE_ST"]["source_manifest_sha256"],
                },
                "suspension_history": {
                    "authority_manifest_sha256": by_name["SUSPENSIONS"]["source_manifest_sha256"]
                },
                "adjustment_factors": {
                    "authority_report_manifest_sha256": by_name["ADJUSTMENTS"][
                        "source_manifest_sha256"
                    ],
                    "authority_report_file_sha256": by_name["ADJUSTMENTS"]["source_file_sha256"],
                },
                "trading_calendar": {
                    "manifest_sha256": by_name["CALENDAR"]["source_manifest_sha256"]
                },
                "csi300_benchmark": {
                    "manifest_sha256": by_name["BENCHMARK"]["source_manifest_sha256"]
                },
                "market_rules_and_transaction_costs": {
                    "report_manifest_sha256": by_name["MARKET_RULES_AND_COSTS"][
                        "source_manifest_sha256"
                    ],
                    "report_file_sha256": by_name["MARKET_RULES_AND_COSTS"]["source_file_sha256"],
                },
            },
        },
    )
    by_name["SOURCE_PREFLIGHT"].update(
        source_file_sha256=sha256_file(preflight_path),
        source_manifest_sha256=preflight["manifest_sha256"],
    )
    state.update(
        full_source_preflight_manifest_sha256=preflight["manifest_sha256"],
        full_source_preflight_file_sha256=sha256_file(preflight_path),
    )
    state.update(
        {
            "full_szse_st_probe_sha256": by_name["SZSE_ST"]["source_manifest_sha256"],
            "full_szse_st_status": "PASS",
            "full_suspension_authority_manifest_sha256": by_name["SUSPENSIONS"][
                "source_manifest_sha256"
            ],
            "full_transaction_cost_report": str(
                source_path(repository, by_name["MARKET_RULES_AND_COSTS"]["source_path"])
            ),
            "full_transaction_cost_report_manifest_sha256": by_name["MARKET_RULES_AND_COSTS"][
                "source_manifest_sha256"
            ],
            "full_transaction_cost_authority": "PASS",
        }
    )
    _manifest(
        staging / "full-adjustment-audit-v1/retained-curve-inventory-v2.json", {"intervals": []}
    )
    return repository, staging, dataset, authority_path, contracts, state


@pytest.mark.parametrize("entry", ("materialize-new", "materialize-resume", "audit", "freeze"))
@pytest.mark.parametrize("bad_digest", ("a" * 65, "0" * 64))
def test_all_full_dataset_entries_reject_unverified_master_before_processing(
    tmp_path, monkeypatch, entry, bad_digest
):
    repository, staging, dataset, _, contracts, state = _inputs(tmp_path)
    state["p0_public_report_manifest_sha256"] = bad_digest
    next(row for row in contracts if row["name"] == "SECURITY_MASTER")["source_manifest_sha256"] = (
        bad_digest
    )
    (repository / ".research/project_state.json").write_text(json.dumps(state), encoding="utf-8")
    pq.write_table(pa.Table.from_pylist(contracts), dataset / "source-contracts.parquet")

    def unvalidated(*_):
        raise AssertionError("UNVALIDATED_DATASET_REACHED")

    module = {"audit": audit_full_dataset, "freeze": freeze_full_dataset}.get(
        entry, materialize_full_dataset
    )
    monkeypatch.setattr(module, "load_manifest", unvalidated)
    if entry == "materialize-new":
        monkeypatch.setattr(module, "SecurityResolver", unvalidated)
    with pytest.raises(ValueError, match=r"SOURCE_MANIFEST_(INVALID|MISMATCH)"):
        if entry == "materialize-new":
            # Only remove an empty disposable fixture, never an existing dataset.
            (dataset / "source-contracts.parquet").unlink()
            dataset.rmdir()
            module.materialize(staging, repository)
        elif entry == "materialize-resume":
            module.materialize(staging, repository)
        elif entry == "audit":
            module.audit(dataset, repository, tmp_path / "audit.json")
        else:
            module.freeze(dataset, repository)
    assert not (staging / "full-dataset-build-v1").exists()
    assert not (tmp_path / "audit.json").exists()
    assert not (dataset / ".freeze.json").exists()


def _check(repository, state, contracts):
    return verify_source_contracts(contracts, repository, state)


def test_exact_sources_repeat_with_reversed_contracts_and_preserve_input_bytes(tmp_path):
    repository, _, _, authority_path, contracts, state = _inputs(tmp_path)
    paths = [source_path(repository, row["source_path"]) for row in contracts] + [authority_path]
    before = {path: path.read_bytes() for path in paths}
    first = _check(repository, state, contracts)
    assert first == _check(repository, state, list(reversed(contracts)))
    assert tuple(first) == tuple(sorted(NAMES))
    lineage = tuple(sorted(f"{r['name']}:{r['source_manifest_sha256']}" for r in contracts))
    verify_source_lineage(contracts, lineage)
    verify_source_lineage(list(reversed(contracts)), lineage)
    assert before == {path: path.read_bytes() for path in paths}


@pytest.mark.parametrize("entry", ("materialize-resume", "audit", "freeze"))
@pytest.mark.parametrize(
    "corruption,reason",
    (
        ("wrong_reference", "SOURCE_MANIFEST_MISMATCH"),
        ("self_manifest", "SOURCE_MANIFEST_MISMATCH"),
        ("p0_manifest", "SOURCE_MANIFEST_MISMATCH"),
        ("master_binding", "SOURCE_MASTER_AUTHORITY_MISMATCH"),
        ("preflight_binding", "SOURCE_PREFLIGHT_MASTER_REFERENCE_MISMATCH"),
        ("bytes", "SOURCE_CONTRACT_BYTES_CHANGED"),
        ("duplicate", "SOURCE_CONTRACT_SET_CHANGED"),
        ("missing", "SOURCE_CONTRACT_SET_CHANGED"),
        ("unexpected", "SOURCE_CONTRACT_SET_CHANGED"),
    ),
)
def test_resumed_materialization_audit_and_freeze_share_complete_guard(
    tmp_path, monkeypatch, entry, corruption, reason
):
    repository, staging, dataset, authority_path, contracts, state = _inputs(tmp_path)
    row = next(row for row in contracts if row["name"] == "SSE_ST")
    if corruption == "wrong_reference":
        row["source_manifest_sha256"] = "0" * 64
    elif corruption in {
        "self_manifest",
        "bytes",
        "master_binding",
        "preflight_binding",
        "p0_manifest",
    }:
        name = {"master_binding": "SECURITY_MASTER", "preflight_binding": "SOURCE_PREFLIGHT"}.get(
            corruption, "SSE_ST"
        )
        row = next(row for row in contracts if row["name"] == name)
        path = (
            authority_path
            if corruption == "p0_manifest"
            else source_path(repository, row["source_path"])
        )
        content = json.loads(path.read_bytes())
        if corruption == "master_binding":
            content[0]["effective_from"] = "2011-01-01"
        elif corruption == "preflight_binding":
            content["components"]["security_master"]["manifest_sha256"] = "0" * 64
            content = _manifest(path, {k: v for k, v in content.items() if k != "manifest_sha256"})
            state["full_source_preflight_manifest_sha256"] = content["manifest_sha256"]
        else:
            content["changed_without_manifest_rehash"] = True
        path.write_text(json.dumps(content), encoding="utf-8")
        if corruption not in {"bytes", "p0_manifest"}:
            row["source_file_sha256"] = sha256_file(path)
        if corruption == "preflight_binding":
            row["source_manifest_sha256"] = content["manifest_sha256"]
            state["full_source_preflight_file_sha256"] = row["source_file_sha256"]
    elif corruption == "duplicate":
        contracts.append(dict(row))
    elif corruption == "missing":
        contracts.remove(row)
    else:
        row["name"] = "UNEXPECTED"
    (repository / ".research/project_state.json").write_text(json.dumps(state), encoding="utf-8")
    pq.write_table(pa.Table.from_pylist(contracts), dataset / "source-contracts.parquet")

    def unvalidated(*_):
        raise AssertionError("UNVALIDATED_DATASET_REACHED")

    module = {"audit": audit_full_dataset, "freeze": freeze_full_dataset}.get(
        entry, materialize_full_dataset
    )
    monkeypatch.setattr(module, "load_manifest", unvalidated)
    with pytest.raises(ValueError, match=reason):
        if entry == "materialize-resume":
            module.materialize(staging, repository)
        elif entry == "audit":
            module.audit(dataset, repository, tmp_path / "audit.json")
        else:
            module.freeze(dataset, repository)
    assert not (staging / "full-dataset-build-v1").exists()
    assert not (tmp_path / "audit.json").exists()
    assert not (repository / ".research/freezes").exists()


@pytest.mark.parametrize("entry", ("materialize-new", "materialize-resume", "audit", "freeze"))
@pytest.mark.parametrize(
    "name,change",
    (
        ("SSE_ST", "manifest"),
        ("SZSE_ST", "manifest"),
        ("SUSPENSIONS", "manifest"),
        ("ADJUSTMENTS", "manifest"),
        ("CALENDAR", "manifest"),
        ("BENCHMARK", "manifest"),
        ("MARKET_RULES_AND_COSTS", "manifest"),
        ("ADJUSTMENTS", "bytes"),
        ("MARKET_RULES_AND_COSTS", "bytes"),
    ),
)
def test_self_signed_source_cannot_escape_pinned_preflight(
    tmp_path, monkeypatch, entry, name, change
):
    repository, staging, dataset, _, contracts, state = _inputs(tmp_path)
    row = next(row for row in contracts if row["name"] == name)
    path = source_path(repository, row["source_path"])
    original = json.loads(path.read_bytes())
    if change == "manifest":
        resigned = _manifest(
            path,
            {
                **{k: v for k, v in original.items() if k != "manifest_sha256"},
                "unapproved_change": True,
            },
        )
        row["source_manifest_sha256"] = resigned["manifest_sha256"]
        state_pin = {
            "SZSE_ST": "full_szse_st_probe_sha256",
            "SUSPENSIONS": "full_suspension_authority_manifest_sha256",
            "MARKET_RULES_AND_COSTS": "full_transaction_cost_report_manifest_sha256",
        }.get(name)
        if state_pin is not None:
            state[state_pin] = resigned["manifest_sha256"]
    else:
        # Same canonical manifest, different bytes; the explicit file pin still binds.
        path.write_text(json.dumps(original, indent=2), encoding="utf-8")
    row["source_file_sha256"] = sha256_file(path)
    (repository / ".research/project_state.json").write_text(json.dumps(state), encoding="utf-8")
    if entry != "materialize-new":
        pq.write_table(pa.Table.from_pylist(contracts), dataset / "source-contracts.parquet")
    else:
        dataset.rmdir()
    module = {"audit": audit_full_dataset, "freeze": freeze_full_dataset}.get(
        entry, materialize_full_dataset
    )

    def unvalidated(*_):
        raise AssertionError("UNVALIDATED_DATASET_REACHED")

    monkeypatch.setattr(module, "load_manifest", unvalidated)
    if entry == "materialize-new":
        monkeypatch.setattr(module, "SecurityResolver", unvalidated)
    reason = (
        "SOURCE_PREFLIGHT_COMPONENT_REFERENCE_MISMATCH"
        if change == "manifest"
        else "SOURCE_PREFLIGHT_COMPONENT_BYTES_MISMATCH"
    )
    with pytest.raises(ValueError, match=reason):
        if entry.startswith("materialize"):
            module.materialize(staging, repository)
        elif entry == "audit":
            module.audit(dataset, repository, tmp_path / "audit.json")
        else:
            module.freeze(dataset, repository)
    assert not (staging / "full-dataset-build-v1").exists()
    assert not (tmp_path / "audit.json").exists()
    assert not (repository / ".research/freezes").exists()
    assert not (dataset / ".freeze.json").exists()


@pytest.mark.parametrize("identity", ("manifest_sha256", "manifest_file_sha256"))
@pytest.mark.parametrize("changed_pin", ("state", "audit", "materialization"))
def test_freeze_identity_requires_every_pinned_digest_to_match(
    tmp_path, monkeypatch, identity, changed_pin
):
    repository, _, dataset, _, contracts, state = _inputs(tmp_path)
    pq.write_table(pa.Table.from_pylist(contracts), dataset / "source-contracts.parquet")
    manifest_path = dataset / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    expected = "1" * 64
    file_digest = sha256_file(manifest_path)
    reports = {
        "audit": {"manifest_sha256": expected, "manifest_file_sha256": file_digest},
        "materialization": {"manifest_sha256": expected, "manifest_file_sha256": file_digest},
    }
    state.update(
        r5_status="PASS_AUDITED_GATE_B_PREAUTHORIZED",
        gate_b_decision="CONDITIONALLY_PREAUTHORIZED_BY_USER",
        gate_b_conditions="PASS",
        full_dataset_created=True,
        full_dataset_audited=True,
        full_dataset_frozen=False,
        full_dataset_unresolved_required_data=0,
        full_dataset_id=dataset.name,
        full_dataset_manifest_sha256=expected,
        full_dataset_manifest_file_sha256=file_digest,
        full_dataset_audit_report=".research/audit.json",
        full_dataset_materialization_report=str(tmp_path / "materialization.json"),
    )
    if changed_pin == "state":
        state["full_dataset_" + identity] = "2" * 64
    else:
        reports[changed_pin][identity] = "2" * 64
    (repository / state["full_dataset_audit_report"]).write_text(
        json.dumps(reports["audit"]), encoding="utf-8"
    )
    (tmp_path / "materialization.json").write_text(
        json.dumps(reports["materialization"]), encoding="utf-8"
    )
    (repository / ".research/project_state.json").write_text(json.dumps(state), encoding="utf-8")
    lineage = tuple(sorted(f"{r['name']}:{r['source_manifest_sha256']}" for r in contracts))
    monkeypatch.setattr(
        freeze_full_dataset,
        "load_manifest",
        lambda *_: SimpleNamespace(
            dataset_id=dataset.name, canonical_sha256=expected, source_lineage=lineage
        ),
    )
    monkeypatch.setattr(freeze_full_dataset, "verify_dataset", lambda *_: None)

    def sha_after_identity(path):
        if path == repository / state["full_dataset_audit_report"]:
            raise AssertionError("UNVALIDATED_REPORT_REACHED")
        return sha256_file(path)

    monkeypatch.setattr(freeze_full_dataset, "sha256_file", sha_after_identity)
    # Reaching report validation means the earlier identity check was bypassed.
    with pytest.raises(ValueError, match="FULL_DATASET_IDENTITY_CHANGED"):
        freeze_full_dataset.freeze(dataset, repository)
    assert not (dataset / ".freeze.json").exists()
    assert not (repository / ".research/freezes").exists()


@pytest.mark.parametrize("entry", ("materialize-resume", "audit", "freeze"))
@pytest.mark.parametrize(
    "lineage", ((), ("fixture",), ("SECURITY_MASTER:" + "0" * 64,), "full_rebound")
)
def test_acceptance_entries_reject_missing_or_rebound_catalog_lineage(
    tmp_path, monkeypatch, entry, lineage
):
    repository, staging, dataset, _, contracts, state = _inputs(tmp_path)
    if lineage == "full_rebound":
        lineage = tuple(
            sorted(
                f"{row['name']}:"
                + ("0" * 64 if row["name"] == "SECURITY_MASTER" else row["source_manifest_sha256"])
                for row in contracts
            )
        )
        assert len(lineage) == 15
    (repository / ".research/project_state.json").write_text(json.dumps(state), encoding="utf-8")
    pq.write_table(pa.Table.from_pylist(contracts), dataset / "source-contracts.parquet")
    module = {"audit": audit_full_dataset, "freeze": freeze_full_dataset}.get(
        entry, materialize_full_dataset
    )
    monkeypatch.setattr(module, "load_manifest", lambda *_: SimpleNamespace(source_lineage=lineage))
    with pytest.raises(ValueError, match="SOURCE_CONTRACT_LINEAGE_MISMATCH"):
        if entry == "materialize-resume":
            module.materialize(staging, repository)
        elif entry == "audit":
            module.audit(dataset, repository, tmp_path / "audit.json")
        else:
            module.freeze(dataset, repository)
    assert not (repository / ".research/freezes").exists()
    assert not (dataset / ".freeze.json").exists()


@pytest.mark.parametrize("name", ("SSE_ST", "SZSE_ST"))
def test_fresh_nonmaster_reference_fails_before_any_build_or_checkpoint(
    tmp_path, monkeypatch, name
):
    repository, staging, dataset, _, contracts, state = _inputs(tmp_path)
    dataset.rmdir()
    if name == "SZSE_ST":
        state["full_szse_st_probe_sha256"] = "0" * 64
    else:
        row = next(row for row in contracts if row["name"] == name)
        path = source_path(repository, row["source_path"])
        content = json.loads(path.read_bytes())
        content["manifest_sha256"] = "0" * 64
        path.write_text(json.dumps(content), encoding="utf-8")
    (repository / ".research/project_state.json").write_text(json.dumps(state), encoding="utf-8")

    def unvalidated(*_):
        raise AssertionError("UNVALIDATED_DATASET_REACHED")

    monkeypatch.setattr(materialize_full_dataset, "SecurityResolver", unvalidated)
    with pytest.raises(ValueError, match="SOURCE_MANIFEST_MISMATCH"):
        materialize_full_dataset.materialize(staging, repository)
    assert not (staging / "full-dataset-build-v1").exists()
    assert not dataset.exists()


@pytest.mark.parametrize("entry", ("audit", "freeze"))
@pytest.mark.parametrize(
    "pin,reason",
    (
        ("p0_public_report_manifest_sha256", "SOURCE_MANIFEST_MISMATCH"),
        ("p0_public_report_file_sha256", "SOURCE_MASTER_AUTHORITY_BYTES_CHANGED"),
        ("full_source_preflight_manifest_sha256", "SOURCE_PREFLIGHT_STATE_REFERENCE_MISMATCH"),
        ("full_source_preflight_file_sha256", "SOURCE_PREFLIGHT_STATE_REFERENCE_MISMATCH"),
    ),
)
def test_authority_state_pins_cannot_drift_from_otherwise_valid_sources(
    tmp_path, monkeypatch, entry, pin, reason
):
    repository, _, dataset, _, contracts, state = _inputs(tmp_path)
    state[pin] = "0" * 64
    (repository / ".research/project_state.json").write_text(json.dumps(state), encoding="utf-8")
    pq.write_table(pa.Table.from_pylist(contracts), dataset / "source-contracts.parquet")
    module = {"audit": audit_full_dataset, "freeze": freeze_full_dataset}[entry]

    def unvalidated(*_):
        raise AssertionError("UNVALIDATED_DATASET_REACHED")

    monkeypatch.setattr(module, "load_manifest", unvalidated)
    with pytest.raises(ValueError, match=reason):
        if entry == "audit":
            module.audit(dataset, repository, tmp_path / "audit.json")
        else:
            module.freeze(dataset, repository)
    assert not (tmp_path / "audit.json").exists()
    assert not (repository / ".research/freezes").exists()
