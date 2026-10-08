"""Isolated successor builds use synthetic authorities, never the retained archive."""

import json
from pathlib import Path

import pytest

from app.data.catalog import load_manifest, verify_dataset
from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts import materialize_full_dataset as materializer
from scripts.full_dataset_build_inputs import REFERENCE_PINS, CandidateBuildInputs
from scripts.full_dataset_sources import source_path
from scripts.publish_akshare_pilot import write_table
from tests.test_full_dataset_raw_checkpoint import _inputs as raw_inputs
from tests.test_full_dataset_raw_checkpoint import _source as raw_source
from tests.test_full_dataset_sources import _inputs, _manifest


def candidate_inputs(tmp_path: Path):
    repository, _, _, authority_path, contracts, state = _inputs(tmp_path)
    paths = {row["name"]: source_path(repository, row["source_path"]) for row in contracts}
    sse, master_sse, statuses_sse = raw_inputs(tmp_path / "sse", "SSE")
    szse, master_szse, statuses_szse = raw_inputs(tmp_path / "szse", "SZSE")
    features = []
    for index in range(239):
        symbol = str(2000 + index).zfill(6)
        sid = f"CN-A:SZSE:{symbol}"
        master_szse.append(
            {
                "security_id": sid,
                "exchange": "SZSE",
                "symbol": symbol,
                "effective_from": "2010-01-01",
                "effective_to": None,
            }
        )
        statuses_szse.append(
            {
                "security_id": sid,
                "effective_from": "2010-01-01",
                "effective_to": "2025-12-31",
                "status": "NORMAL",
            }
        )
        features.append(
            {
                "security_id": sid,
                "official_target_close": "10",
                "official_volume_interval_shares": ["1", "2"],
                "official_amount_interval_cny": ["10", "20"],
            }
        )
    master = master_sse + master_szse
    paths["SECURITY_MASTER"].write_text(json.dumps(master))
    authority = _manifest(authority_path, {"reconstructed_master_sha256": canonical_sha256(master)})
    _manifest(paths["SSE_ST"], {"intervals": statuses_sse})
    _manifest(paths["SZSE_ST"], {"daily_replay": {"intervals": statuses_szse}})
    auxiliary = {}

    def aux(name, payload):
        path = tmp_path / f"{name}.json"
        _manifest(path, payload)
        auxiliary[name] = {"path": str(path), "sha256": sha256_file(path)}
        return path

    inventory = aux(
        "adjustment_inventory",
        {
            "intervals": [
                {
                    "security_id": row["security_id"],
                    "effective_from": "2010-01-01",
                    "effective_to": "2025-12-31",
                    "in_interval_variants": {
                        "fixture": {"baseline": ["2009-12-31", "1"], "period_rows": []}
                    },
                }
                for row in master
            ]
        },
    )
    _manifest(
        paths["ADJUSTMENTS"],
        {
            "official_cash_overlay_events": [],
            "inputs": [{"path": str(inventory), "sha256": sha256_file(inventory)}],
        },
    )
    rights = aux("rights_inventory", {"rows": []})
    _manifest(
        paths["RIGHTS_ACTIONS"],
        {"inventory_path": str(rights), "inventory_sha256": sha256_file(rights)},
    )
    aux("suspension_events", {"sse": [], "szse": []})
    feature = aux("feature_only_observations", {"target_date": "2011-07-25", "results": features})
    for name in ("CASH_ACTIONS", "BONUS_ACTIONS", "GAP_DISTRIBUTION_ACTIONS"):
        _manifest(paths[name], {"events": []})
    # The pipeline's historical merger census remains intact; these are not approved market events.
    _manifest(
        paths["MERGER_ACTIONS"],
        {
            "executable_events": [
                {
                    "event": {
                        "parent_security": {"value": f"fixture-{index}"},
                        "effective_date": "2015-01-05",
                        "policy": "SYNTHETIC_TEST_ONLY",
                    },
                    "event_checksum": canonical_sha256({"fixture": index}),
                }
                for index in range(24)
            ]
        },
    )
    _manifest(
        paths["STRUCTURAL_ACTIONS"],
        {
            name: {"events": []}
            for name in (
                "demerger_full_census",
                "partial_surrender_full_census",
                "bonus_pass_through_full_census",
                "share_consolidation_full_census",
            )
        },
    )
    sessions = ["2010-01-04", "2010-01-05", "2011-07-25"]
    _manifest(paths["CALENDAR"], {"sessions": sessions})
    benchmark = write_table(
        tmp_path,
        "benchmark.parquet",
        [{"trading_date": day, "close": "100"} for day in sessions],
        ("trading_date",),
    )
    auxiliary["benchmark_parquet"] = {
        "path": str(tmp_path / "benchmark.parquet"),
        "sha256": benchmark.sha256,
    }
    _manifest(paths["BENCHMARK"], {"partition": benchmark.model_dump(mode="json")})
    for row in contracts:
        path = paths[row["name"]]
        row.update(
            source_path=str(path),
            source_file_sha256=sha256_file(path),
            source_manifest_sha256=authority["manifest_sha256"]
            if row["name"] == "SECURITY_MASTER"
            else json.loads(path.read_bytes())["manifest_sha256"],
        )
    by_name = {row["name"]: row for row in contracts}
    components = {
        "security_master": {"manifest_sha256": authority["manifest_sha256"]},
        "corporate_actions": {},
        "raw_ohlcv": {
            "report_path": str(feature),
            "report_file_sha256": sha256_file(feature),
            "report_manifest_sha256": json.loads(feature.read_bytes())["manifest_sha256"],
        },
    }
    for name, component, manifest_key, file_key in (
        ("SSE_ST", "st_history", "sse_manifest_sha256", None),
        ("SZSE_ST", "st_history", "szse_probe_sha256", None),
        ("SUSPENSIONS", "suspension_history", "authority_manifest_sha256", None),
        (
            "ADJUSTMENTS",
            "adjustment_factors",
            "authority_report_manifest_sha256",
            "authority_report_file_sha256",
        ),
        ("CALENDAR", "trading_calendar", "manifest_sha256", None),
        ("BENCHMARK", "csi300_benchmark", "manifest_sha256", None),
        (
            "MARKET_RULES_AND_COSTS",
            "market_rules_and_transaction_costs",
            "report_manifest_sha256",
            "report_file_sha256",
        ),
    ):
        components.setdefault(component, {})[manifest_key] = by_name[name]["source_manifest_sha256"]
        if file_key:
            components[component][file_key] = by_name[name]["source_file_sha256"]
    for component in components.values():
        component["status"] = "PASS"
    dataset_id = "synthetic-successor-build-test-v2"
    preflight_path = tmp_path / "new-preflight.json"
    preflight = _manifest(
        preflight_path,
        {
            "dataset_id": dataset_id,
            "coverage": [materializer.START, materializer.END],
            "operation": "ISOLATED_SUCCESSOR_MATERIALIZATION",
            "status": "PASS",
            "components": components,
            "mandatory_incomplete_components": [],
        },
    )
    by_name["SOURCE_PREFLIGHT"].update(
        source_path=str(preflight_path),
        source_file_sha256=sha256_file(preflight_path),
        source_manifest_sha256=preflight["manifest_sha256"],
    )
    state.update(
        p0_public_report_manifest_sha256=authority["manifest_sha256"],
        p0_public_report_file_sha256=sha256_file(authority_path),
        full_source_preflight_manifest_sha256=preflight["manifest_sha256"],
        full_source_preflight_file_sha256=sha256_file(preflight_path),
    )
    spec = {
        "operation": "ISOLATED_SUCCESSOR_MATERIALIZATION",
        "authorization_source": "ACCEPTED_V1_2_PRODUCT_GOAL",
        "dataset_id": dataset_id,
        "coverage": [materializer.START, materializer.END],
        "recorded_at_utc": "2026-10-08T00:00:00Z",
        "work_root": str(tmp_path / "owned-work"),
        "final_root": str(tmp_path / dataset_id),
        "reference_pins": {key: state[key] for key in REFERENCE_PINS},
        "source_contracts": contracts,
        "auxiliary_inputs": auxiliary,
        "raw_sources": {
            exchange: [
                {
                    "path": str(path),
                    "sha256": sha256_file(path),
                    "metadata_sha256": sha256_file(path.with_suffix(path.suffix + ".meta.json")),
                }
                for path in source_paths
            ]
            for exchange, source_paths in (("SSE", sse), ("SZSE", szse))
        },
        "market_rule_manifest_sha256": "1" * 64,
    }
    preflight.pop("manifest_sha256")
    preflight["input_selection_sha256"] = CandidateBuildInputs.model_validate(
        spec
    ).input_selection_sha256(repository)
    preflight = _manifest(preflight_path, preflight)
    by_name["SOURCE_PREFLIGHT"].update(
        source_manifest_sha256=preflight["manifest_sha256"],
        source_file_sha256=sha256_file(preflight_path),
    )
    spec["reference_pins"].update(
        full_source_preflight_manifest_sha256=preflight["manifest_sha256"],
        full_source_preflight_file_sha256=sha256_file(preflight_path),
    )
    path = tmp_path / "build-spec.json"
    path.write_text(json.dumps(spec))
    return repository, path, spec


def build(repository, path):
    return materializer.materialize(
        None, repository, build_spec=path, build_spec_sha256=sha256_file(path)
    )


def test_successor_materializes_without_frozen_research_state_and_resumes(tmp_path):
    repository, path, spec = candidate_inputs(tmp_path)
    assert not (repository / ".research/project_state.json").exists()
    report = build(repository, path)
    assert report == build(repository, path)
    final = Path(spec["final_root"])
    manifest = load_manifest(final / "manifest.json")
    verify_dataset(final, manifest)
    assert manifest.dataset_id == report["dataset_id"] == spec["dataset_id"]
    assert report["feature_only_rows"] == 239 and report["corporate_action_rows"] == 24
    assert report["raw_rows"] == 4 and report["full_financial_admission"] is False
    assert (
        not report["dataset_registered"]
        and not report["dataset_audited"]
        and not report["dataset_frozen"]
    )
    assert not (final / ".freeze.json").exists()


@pytest.mark.parametrize(
    "change", ["inspection", "old_approval", "old_identity", "incomplete", "missing_component"]
)
def test_successor_rejects_unapproved_preflight_before_writes(tmp_path, change):
    repository, path, spec = candidate_inputs(tmp_path)
    row = next(row for row in spec["source_contracts"] if row["name"] == "SOURCE_PREFLIGHT")
    preflight_path = Path(row["source_path"])
    preflight = json.loads(preflight_path.read_bytes())
    preflight.pop("manifest_sha256")
    if change == "inspection":
        preflight["status"] = "INSPECTION_ONLY"
    elif change == "old_approval":
        preflight["approval"] = {"status": "APPROVED", "policy": "R5_RESEARCH_CONVENTIONS_V1"}
    elif change == "old_identity":
        preflight["dataset_id"] = materializer.DATASET_ID
    elif change == "incomplete":
        preflight["mandatory_incomplete_components"] = ["corporate_actions"]
    else:
        preflight["components"].pop("raw_ohlcv")
    changed = _manifest(preflight_path, preflight)
    row.update(
        source_manifest_sha256=changed["manifest_sha256"],
        source_file_sha256=sha256_file(preflight_path),
    )
    spec["reference_pins"].update(
        full_source_preflight_manifest_sha256=changed["manifest_sha256"],
        full_source_preflight_file_sha256=sha256_file(preflight_path),
    )
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="CANDIDATE_SOURCE_PREFLIGHT_NOT_AUTHORIZED"):
        build(repository, path)
    assert not Path(spec["work_root"]).exists() and not Path(spec["final_root"]).exists()


@pytest.mark.parametrize("change", ["raw_subset", "suspension", "rules"])
def test_successor_cannot_change_selected_inputs_under_the_same_preflight(tmp_path, change):
    repository, path, spec = candidate_inputs(tmp_path)
    if change == "raw_subset":
        spec["raw_sources"]["SSE"].pop()
    elif change == "suspension":
        replacement = tmp_path / "replacement.json"
        replacement.write_text(json.dumps({"sse": [], "szse": [], "unapproved": True}))
        spec["auxiliary_inputs"]["suspension_events"] = {
            "path": str(replacement),
            "sha256": sha256_file(replacement),
        }
    else:
        spec["market_rule_manifest_sha256"] = "2" * 64
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="CANDIDATE_PREFLIGHT_INPUT_SELECTION_MISMATCH"):
        build(repository, path)
    assert not Path(spec["work_root"]).exists()


@pytest.mark.parametrize("change", ["counts", "audited", "financial", "manifest_file"])
def test_successor_resume_cannot_trust_an_altered_report(tmp_path, change):
    repository, path, spec = candidate_inputs(tmp_path)
    build(repository, path)
    report_path = Path(spec["work_root"]) / "materialization-report.json"
    report = json.loads(report_path.read_bytes())
    if change == "counts":
        report["raw_rows"] += 100
    elif change == "audited":
        report["dataset_audited"] = True
    elif change == "financial":
        report["full_financial_admission"] = True
    else:
        report["manifest_file_sha256"] = "0" * 64
    report_path.chmod(0o600)
    report_path.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="CANDIDATE_PUBLICATION_IDENTITY_CHANGED"):
        build(repository, path)


@pytest.mark.parametrize("alias", ["file", "parent", "metadata"])
def test_successor_rejects_raw_aliases_before_writes(tmp_path, alias):
    repository, path, spec = candidate_inputs(tmp_path)
    pin = spec["raw_sources"]["SSE"][0]
    original = Path(pin["path"])
    if alias == "file":
        link = tmp_path / "600999.json"
        link.symlink_to(original)
        pin["path"] = str(link)
    elif alias == "parent":
        link = tmp_path / "aliased-raw"
        link.symlink_to(original.parent, target_is_directory=True)
        pin["path"] = str(link / original.name)
    else:
        metadata = original.with_suffix(original.suffix + ".meta.json")
        saved = metadata.with_name("retained-metadata.json")
        metadata.rename(saved)
        metadata.symlink_to(saved)
    path.write_text(json.dumps(spec))
    with pytest.raises(ValueError, match="CANDIDATE_RAW_PATH_ALIASED"):
        build(repository, path)
    assert not Path(spec["work_root"]).exists()


@pytest.mark.parametrize("name", ["adjustment_inventory", "benchmark_parquet"])
def test_successor_checks_the_exact_auxiliary_bytes_it_parses(tmp_path, monkeypatch, name):
    repository, path, spec = candidate_inputs(tmp_path)
    inventory = Path(spec["auxiliary_inputs"][name]["path"])
    if name == "adjustment_inventory":
        changed = json.loads(inventory.read_bytes())
        changed["intervals"][0]["in_interval_variants"]["fixture"]["baseline"][1] = "2"
        changed_bytes = json.dumps(changed).encode()
    else:
        changed_bytes = b"not the pinned parquet"
    original_read = Path.read_bytes
    injected = False

    def transient_change(selected):
        nonlocal injected
        if selected == inventory and not injected:
            injected = True
            return changed_bytes
        return original_read(selected)

    monkeypatch.setattr(Path, "read_bytes", transient_change)
    with pytest.raises(ValueError, match="CANDIDATE_CONSUMED_BYTES_CHANGED"):
        build(repository, path)
    assert injected and not Path(spec["final_root"]).exists()


def test_successor_reordered_resume_and_fresh_build_are_identical(tmp_path):
    repository, path, spec = candidate_inputs(tmp_path)
    first = build(repository, path)
    spec["source_contracts"].reverse()
    for pins in spec["raw_sources"].values():
        pins.reverse()
    path.write_text(json.dumps(spec))
    assert build(repository, path) == first
    spec["work_root"] = str(tmp_path / "fresh-work")
    spec["final_root"] = str(tmp_path / "fresh" / spec["dataset_id"])
    path.write_text(json.dumps(spec))
    fresh = build(repository, path)
    assert {key: value for key, value in first.items() if key != "build_inputs"} == {
        key: value for key, value in fresh.items() if key != "build_inputs"
    }


@pytest.mark.parametrize("point", ["after_raw", "after_rename"])
def test_successor_resumes_interrupted_build_without_replacing_raw_partitions(
    tmp_path, monkeypatch, point
):
    repository, path, spec = candidate_inputs(tmp_path)
    original = materializer.write_table if point == "after_raw" else materializer.write_immutable

    def interrupt(target, *args):
        if point == "after_raw" or target.name == "publication-checkpoint.json":
            raise RuntimeError("SIMULATED_BUILD_INTERRUPTION")
        return original(target, *args)

    method = "write_table" if point == "after_raw" else "write_immutable"
    monkeypatch.setattr(materializer, method, interrupt)
    with pytest.raises(RuntimeError, match="SIMULATED_BUILD_INTERRUPTION"):
        build(repository, path)
    output = (
        Path(spec["work_root"]) / "catalog-build"
        if point == "after_raw"
        else Path(spec["final_root"])
    )
    before = {
        str(file.relative_to(output)): (sha256_file(file), file.stat().st_mtime_ns)
        for file in (output / "raw").rglob("*.parquet")
    }
    assert len(before) == 2
    monkeypatch.setattr(materializer, method, original)
    report = build(repository, path)
    final = Path(spec["final_root"])
    assert before == {
        str(file.relative_to(final)): (sha256_file(file), file.stat().st_mtime_ns)
        for file in (final / "raw").rglob("*.parquet")
    }
    checkpoint = json.loads((Path(spec["work_root"]) / "publication-checkpoint.json").read_bytes())
    assert checkpoint == {**report, "published": True}


@pytest.mark.parametrize(
    "change",
    ["unknown_work", "frozen_work", "inside_repo", "source_overlap", "old_identity", "spec_pin"],
)
def test_successor_rejects_unsafe_build_identity(tmp_path, change):
    repository, path, spec = candidate_inputs(tmp_path)
    if change == "unknown_work":
        work = Path(spec["work_root"])
        work.mkdir()
        (work / "keep.txt").write_text("user-owned")
    elif change == "frozen_work":
        work = Path(spec["work_root"])
        work.mkdir()
        (work / ".freeze.json").write_text("{}")
    elif change == "inside_repo":
        spec["work_root"] = str(repository / "do-not-write")
    elif change == "source_overlap":
        spec["work_root"] = str(tmp_path / "sse")
    elif change == "old_identity":
        spec["dataset_id"] = materializer.DATASET_ID
    path.write_text(json.dumps(spec))
    before = {str(file): sha256_file(file) for file in tmp_path.rglob("*") if file.is_file()}
    with pytest.raises(ValueError):
        materializer.materialize(
            None,
            repository,
            build_spec=path,
            build_spec_sha256="0" * 64 if change == "spec_pin" else sha256_file(path),
        )
    assert before == {
        str(file): sha256_file(file) for file in tmp_path.rglob("*") if file.is_file()
    }


def test_successor_rejects_extra_published_partition_without_changing_it(tmp_path):
    repository, path, spec = candidate_inputs(tmp_path)
    build(repository, path)
    extra = Path(spec["final_root"]) / "unlisted.parquet"
    extra.write_bytes(b"unexpected")
    with pytest.raises(ValueError, match="CANDIDATE_PUBLICATION_IDENTITY_CHANGED"):
        build(repository, path)
    assert extra.read_bytes() == b"unexpected"


def test_successor_rejects_transient_spec_bytes(tmp_path, monkeypatch):
    repository, path, spec = candidate_inputs(tmp_path)
    spec["work_root"] = str(tmp_path / "different-work")
    original = Path.read_bytes

    def altered(selected):
        return json.dumps(spec).encode() if selected == path else original(selected)

    monkeypatch.setattr(Path, "read_bytes", altered)
    with pytest.raises(ValueError, match="CANDIDATE_BUILD_SPEC_CHANGED"):
        build(repository, path)
    assert not Path(spec["work_root"]).exists()


@pytest.mark.parametrize("point", ["load_inputs", "write_tables"])
def test_successor_does_not_publish_when_producer_changes_during_build(
    tmp_path, monkeypatch, point
):
    repository, path, spec = candidate_inputs(tmp_path)
    original_owner = CandidateBuildInputs.ownership
    operation = "load_candidate_build_inputs" if point == "load_inputs" else "write_table"
    original_write = getattr(materializer, operation)
    changed = False

    def ownership(self):
        record = original_owner(self)
        if changed:
            record["producer_sha256"]["materialize_full_dataset.py"] = "0" * 64
        return record

    def change_during_write(*args, **kwargs):
        nonlocal changed
        changed = True
        return original_write(*args, **kwargs)

    monkeypatch.setattr(CandidateBuildInputs, "ownership", ownership)
    monkeypatch.setattr(materializer, operation, change_during_write)
    with pytest.raises(ValueError, match="CANDIDATE_PRODUCER_CHANGED"):
        build(repository, path)
    assert changed and not Path(spec["final_root"]).exists()


@pytest.mark.parametrize("exchange", ["SSE", "SZSE"])
def test_successor_raw_stage_cannot_select_transient_unapproved_inputs(
    tmp_path, monkeypatch, exchange
):
    repository, path, spec = candidate_inputs(tmp_path)
    original_stage = materializer.raw_stage
    raw = Path(spec["raw_sources"][exchange][0]["path"])
    metadata = raw.with_suffix(raw.suffix + ".meta.json")
    before = (raw.read_bytes(), metadata.read_bytes())

    def substitute(build_root, selected_exchange, *args, **kwargs):
        if selected_exchange != exchange:
            return original_stage(build_root, selected_exchange, *args, **kwargs)
        try:
            raw_source(raw, exchange, "20100104" if exchange == "SSE" else "2010-01-04", close=11)
            return original_stage(build_root, selected_exchange, *args, **kwargs)
        finally:
            raw.write_bytes(before[0])
            metadata.write_bytes(before[1])

    monkeypatch.setattr(materializer, "raw_stage", substitute)
    with pytest.raises(ValueError, match="RAW_SELECTED_INPUT_MISMATCH"):
        build(repository, path)
    assert (raw.read_bytes(), metadata.read_bytes()) == before
    assert not Path(spec["final_root"]).exists()
