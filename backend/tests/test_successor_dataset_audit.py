"""Candidate audits read real synthetic partitions, never the frozen archive or DB."""

import json
from datetime import date
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from openpyxl import load_workbook

from app.data.catalog import load_manifest
from app.data.catalog.checksums import canonical_sha256, sha256_file
from app.data.full_dataset import FullDataset
from app.domain.markets import SecurityId
from app.domain.markets.calendar import TradingCalendar
from app.domain.markets.corporate_actions import OrdinaryDistributionReference
from app.execution import FixedCommission
from app.research.engine import ResearchExecutionEngine
from app.research.models import ResearchPeriodKind
from app.research.splits import TemporalPeriod
from scripts import audit_full_dataset as auditor
from scripts import materialize_full_dataset as materializer
from scripts.audit_full_dataset import audit
from scripts.publish_akshare_pilot import write_table
from tests.test_full_dataset_build_inputs import build
from tests.test_full_dataset_raw_checkpoint import _source
from tests.test_full_dataset_sources import _manifest
from tests.test_merger_accounting import event as merger
from tests.test_ordinary_distribution_sessions import NoTargets, _state
from tests.test_pass_through_accounting import event as pass_through
from tests.test_successor_reference_inputs import reference_inputs, update_spec


def audit_inputs(
    tmp_path,
    *,
    include_reference=True,
    conflicting_pass_through=False,
    bonus_updates=None,
):
    repository, path, spec, cash, bonus, reference = reference_inputs(tmp_path)
    contracts = {row["name"]: row for row in spec["source_contracts"]}
    sid = SecurityId(value="CN-A:SZSE:000001")
    cash, bonus = (event.model_copy(update={"security_id": sid}) for event in (cash, bonus))
    if bonus_updates:
        bonus = bonus.model_copy(update=bonus_updates)
    reference = OrdinaryDistributionReference.model_validate(
        {
            **reference.model_dump(),
            "security_id": sid,
            "cash_event_checksum": cash.event_checksum,
            "share_event_checksum": bonus.event_checksum,
        }
    )
    for name, event in (("CASH_ACTIONS", cash), ("BONUS_ACTIONS", bonus)):
        _manifest(
            Path(contracts[name]["source_path"]),
            {
                "events": [
                    {"event": event.model_dump(mode="json"), "event_checksum": event.event_checksum}
                ]
            },
        )
    reference_pin = spec["auxiliary_inputs"]["ordinary_references"]
    reference_path = Path(reference_pin["path"])
    _manifest(
        reference_path,
        {
            "private_candidate_reference_rows": [
                {
                    "event_kind": "ORDINARY_REFERENCE",
                    "event_json": reference.model_dump_json(),
                    "event_checksum": reference.event_checksum,
                    "application_date": "2011-02-01",
                }
            ]
        },
    )
    reference_pin["sha256"] = sha256_file(reference_path)
    master_path = Path(contracts["SECURITY_MASTER"]["source_path"])
    master = json.loads(master_path.read_bytes())
    for row in master:
        row.update(instrument_type="COMMON_A_SHARE", board=f"{row['exchange']}_MAIN")
    master_path.write_text(json.dumps(master))
    authority_path = repository / spec["reference_pins"]["p0_public_report_path"]
    authority = _manifest(authority_path, {"reconstructed_master_sha256": canonical_sha256(master)})
    contracts["SECURITY_MASTER"].update(
        source_file_sha256=sha256_file(master_path),
        source_manifest_sha256=authority["manifest_sha256"],
    )
    spec["reference_pins"].update(
        p0_public_report_file_sha256=sha256_file(authority_path),
        p0_public_report_manifest_sha256=authority["manifest_sha256"],
    )
    # Typed synthetic census, deliberately NOT a claim of actual issuer/lifecycle evidence.
    events = [
        merger().model_copy(update={"parent_security": SecurityId(value=f"CN-A:SZSE:{900000 + i}")})
        for i in range(24)
    ]
    merger_path = Path(contracts["MERGER_ACTIONS"]["source_path"])
    census = _manifest(
        merger_path,
        {
            "executable_events": [
                {"event": event.model_dump(mode="json"), "event_checksum": event.event_checksum}
                for event in events
            ]
        },
    )
    contracts["MERGER_ACTIONS"].update(
        source_file_sha256=sha256_file(merger_path),
        source_manifest_sha256=census["manifest_sha256"],
    )
    # Cross-month reference carried over an absent affected-security bar, then recovered.
    for day, symbol, previous, close in (
        ("2011-01-31", "000001", "10", "29.29"),
        ("2011-02-01", "000002", "10", "10"),
        ("2011-02-02", "000001", "19.45", "19.55"),
        ("2011-07-25", "000001", "19.55", "10"),
        ("2015-12-30", "000002", "10", "10"),
    ):
        raw_path = tmp_path / "szse" / f"{day}.xlsx"
        _source(raw_path, "SZSE", day)
        workbook = load_workbook(raw_path)
        sheet = workbook.active
        for cell, value in (
            ("B2", symbol),
            ("D2", previous),
            ("E2", close),
            ("F2", close),
            ("G2", close),
            ("H2", close),
        ):
            sheet[cell] = value
        workbook.save(raw_path)
        workbook.close()
        metadata = raw_path.with_suffix(".xlsx.meta.json")
        meta = json.loads(metadata.read_bytes())
        meta["sha256"] = sha256_file(raw_path)
        metadata.write_text(json.dumps(meta))
        spec["raw_sources"]["SZSE"].append(
            {
                "path": str(raw_path),
                "sha256": sha256_file(raw_path),
                "metadata_sha256": sha256_file(metadata),
            }
        )
    calendar_path = Path(contracts["CALENDAR"]["source_path"])
    days = sorted(
        [
            "2010-01-04",
            "2010-01-05",
            "2011-01-31",
            "2011-02-01",
            "2011-02-02",
            "2011-07-25",
            "2015-12-30",
        ]
    )
    calendar = _manifest(calendar_path, {"sessions": days})
    contracts["CALENDAR"].update(
        source_file_sha256=sha256_file(calendar_path),
        source_manifest_sha256=calendar["manifest_sha256"],
    )
    benchmark = write_table(
        tmp_path,
        "audit-benchmark.parquet",
        [{"trading_date": day, "close": "100"} for day in days],
        ("trading_date",),
    )
    spec["auxiliary_inputs"]["benchmark_parquet"] = {
        "path": str(tmp_path / "audit-benchmark.parquet"),
        "sha256": benchmark.sha256,
    }
    benchmark_path = Path(contracts["BENCHMARK"]["source_path"])
    benchmark_report = _manifest(benchmark_path, {"partition": benchmark.model_dump(mode="json")})
    contracts["BENCHMARK"].update(
        source_file_sha256=sha256_file(benchmark_path),
        source_manifest_sha256=benchmark_report["manifest_sha256"],
    )
    preflight_path = Path(contracts["SOURCE_PREFLIGHT"]["source_path"])
    preflight = json.loads(preflight_path.read_bytes())
    preflight["components"]["security_master"].update(
        manifest_sha256=authority["manifest_sha256"],
        securities=len(master),
        intervals=len(master),
        true_p0_unresolved_facts=0,
    )
    preflight["components"]["trading_calendar"]["manifest_sha256"] = calendar["manifest_sha256"]
    preflight["components"]["csi300_benchmark"]["manifest_sha256"] = benchmark_report[
        "manifest_sha256"
    ]
    if conflicting_pass_through:
        # Synthetic supported event with a real partition-level trading conflict.
        event = pass_through()
        event = type(event).model_validate(
            {
                **event.model_dump(),
                "security_id": SecurityId(value="CN-A:SZSE:000002"),
                "effective_date": "2015-12-30",
                "temporary_registration_date": "2015-12-30",
                "transfer_date": "2015-12-30",
            }
        )
        structural_path = Path(contracts["STRUCTURAL_ACTIONS"]["source_path"])
        structural = json.loads(structural_path.read_bytes())
        structural.pop("manifest_sha256")
        structural["bonus_pass_through_full_census"]["events"] = [
            {"event": event.model_dump(mode="json"), "event_checksum": event.event_checksum}
        ]
        structural = _manifest(structural_path, structural)
        contracts["STRUCTURAL_ACTIONS"].update(
            source_file_sha256=sha256_file(structural_path),
            source_manifest_sha256=structural["manifest_sha256"],
        )
    preflight_path.write_text(json.dumps(preflight))
    if not include_reference:
        del spec["auxiliary_inputs"]["ordinary_references"]
    update_spec(repository, path, spec)
    build(repository, path)
    return repository, path, spec


def run_audit(repository, path, spec, output):
    return audit(
        Path(spec["final_root"]),
        repository,
        output,
        build_spec=path,
        build_spec_sha256=sha256_file(path),
    )


def test_candidate_audit_is_version_bound_and_does_not_inherit_financial_pass(tmp_path):
    repository, path, spec = audit_inputs(tmp_path)
    output = tmp_path / "reports" / "audit.json"
    before = {str(p): sha256_file(p) for p in tmp_path.rglob("*") if p.is_file()}
    report = run_audit(repository, path, spec, output)
    assert report == run_audit(repository, path, spec, output)
    assert report["dataset_id"] == spec["dataset_id"]
    assert report["ordinary_reference_rows"] == 1 and report["accounting_action_rows"] == 26
    assert report["runtime_scan"]["sessions"] == 7
    assert report["gates"]["REFERENCE_PRICE_CONTINUITY"] == "PASS"
    assert report["gates"]["SOURCE_EVENT_SET_MATCH"] == "PASS"
    assert report["gates"]["ACTION_SESSION_PRECONDITIONS"] == "PASS"
    assert report["runtime_scan"]["action_session_failures"] == []
    for gate in (
        "CASH_RECONCILIATION",
        "BASIS_RECONCILIATION",
        "INPUT_ORDER_REPRODUCIBILITY",
        "RESUME_RESTART",
    ):
        assert report["gates"][gate] == "NOT_EVIDENCED"
    assert not report["dataset_audited"] and not report["full_financial_admission"]
    assert not report["dataset_frozen"] and not report["dataset_registered"]
    assert report["audit_status"] != "PASS"
    assert not (repository / ".research/project_state.json").exists()
    assert all(sha256_file(Path(p)) == digest for p, digest in before.items())


def test_candidate_audit_checks_production_action_boundaries_without_accounting(
    tmp_path, monkeypatch
):
    from app.portfolio import PortfolioEngine

    def forbidden(*args, **kwargs):
        pytest.fail("audit must not instantiate a portfolio or strategy execution engine")

    monkeypatch.setattr(PortfolioEngine, "__init__", forbidden)
    monkeypatch.setattr(ResearchExecutionEngine, "__init__", forbidden)
    repository, path, spec = audit_inputs(tmp_path, conflicting_pass_through=True)
    report = run_audit(repository, path, spec, tmp_path / "audit.json")
    assert report["gates"]["SOURCE_EVENT_SET_MATCH"] == "PASS"
    assert report["gates"]["ACTION_SESSION_COVERAGE"] == "PASS"
    assert report["gates"]["ACTION_SESSION_PRECONDITIONS"] == "FAIL"
    assert report["runtime_scan"]["action_session_failures"] == [
        {
            "trading_date": "2015-12-30",
            "reason": "PASS_THROUGH_TRADING_OBSERVATION_CONFLICT",
        }
    ]
    assert report["audit_status"] == "FAIL_CLOSED"
    assert report["gates"]["CORPORATE_ACTION_ACCOUNTING"] == "NOT_EVIDENCED"
    assert not report["accounting_invariant_evidence"]["portfolio_accounting_run"]
    assert not report["dataset_audited"] and not report["strategy_run"]


@pytest.mark.parametrize(
    ("bonus_updates", "action_date", "next_date"),
    [
        ({"listing_date": date(2011, 7, 25)}, date(2011, 2, 1), date(2011, 2, 2)),
        ({"listing_date": date(2011, 1, 31)}, date(2011, 2, 1), date(2011, 2, 2)),
        (
            {
                "ex_date": date(2015, 12, 30),
                "effective_date": date(2015, 12, 30),
                "record_date": date(2015, 12, 29),
                "listing_date": date(2015, 12, 31),
            },
            date(2015, 12, 30),
            None,
        ),
    ],
    ids=["later-than-next", "before-ex", "no-accepted-next"],
)
def test_candidate_listing_precondition_matches_runtime_before_accounting(
    tmp_path, bonus_updates, action_date, next_date
):
    repository, path, spec = audit_inputs(
        tmp_path,
        include_reference=False,
        bonus_updates=bonus_updates,
    )
    dataset = Path(spec["final_root"])
    manifest = load_manifest(dataset / "manifest.json")
    loader = FullDataset(
        dataset,
        manifest,
        TemporalPeriod(
            ResearchPeriodKind.FULL_PERIOD, manifest.coverage_start, manifest.coverage_end
        ),
    )
    execution_calendar = (
        TradingCalendar(
            market=loader.calendar.market,
            sessions=(*loader.calendar.sessions, loader.next_session),
        )
        if loader.next_session is not None
        else loader.calendar
    )
    engine = ResearchExecutionEngine(
        NoTargets(),
        initial_cash=Decimal(10000),
        commission_model=FixedCommission(),
        calendar=execution_calendar,
    )
    session = next(
        item for item in loader.sessions(execution=True) if item.trading_date == action_date
    )
    assert engine.next_accepted_session(session.trading_date) == next_date
    before = _state(engine)
    reason = "ORDINARY_DISTRIBUTION_LISTING_DATE_UNSUPPORTED"
    with pytest.raises(ValueError, match=reason):
        engine.process_session(session)
    assert _state(engine) == before

    report = run_audit(repository, path, spec, tmp_path / "audit.json")
    assert report["gates"]["SOURCE_EVENT_SET_MATCH"] == "PASS"
    # Omitting the same-ex price companion is honest: this separate gate still fails.
    assert report["gates"]["REFERENCE_PRICE_CONTINUITY"] == "FAIL"
    assert report["gates"]["ACTION_SESSION_PRECONDITIONS"] == "FAIL"
    assert report["runtime_scan"]["action_session_failures"] == [
        {"trading_date": action_date.isoformat(), "reason": reason}
    ]
    assert not report["accounting_invariant_evidence"]["portfolio_accounting_run"]
    assert not report["full_financial_admission"]


@pytest.mark.parametrize("listing_date", [date(2011, 2, 1), date(2011, 2, 2), None])
def test_candidate_listing_accepts_same_ex_next_and_legacy_unknown_without_accounting(
    tmp_path, monkeypatch, listing_date
):
    from app.portfolio import PortfolioEngine

    repository, path, spec = audit_inputs(
        tmp_path, include_reference=False, bonus_updates={"listing_date": listing_date}
    )

    def forbidden(*args, **kwargs):
        pytest.fail("audit must not instantiate a portfolio or strategy execution engine")

    monkeypatch.setattr(PortfolioEngine, "__init__", forbidden)
    monkeypatch.setattr(ResearchExecutionEngine, "__init__", forbidden)
    report = run_audit(repository, path, spec, tmp_path / "audit.json")
    assert report == run_audit(repository, path, spec, tmp_path / "audit-repeat.json")
    assert report["gates"]["SOURCE_EVENT_SET_MATCH"] == "PASS"
    assert report["gates"]["REFERENCE_PRICE_CONTINUITY"] == "FAIL"
    assert report["gates"]["ACTION_SESSION_PRECONDITIONS"] == "PASS"
    assert report["runtime_scan"]["action_session_failures"] == []
    assert report["gates"]["CORPORATE_ACTION_ACCOUNTING"] == "NOT_EVIDENCED"
    assert not report["accounting_invariant_evidence"]["portfolio_accounting_run"]
    assert not report["full_financial_admission"]


def test_candidate_listing_uses_calendar_not_affected_security_price_dates(tmp_path):
    repository, path, spec = audit_inputs(
        tmp_path,
        include_reference=False,
        bonus_updates={
            "ex_date": date(2011, 1, 31),
            "effective_date": date(2011, 1, 31),
            "record_date": date(2011, 1, 28),
            "listing_date": date(2011, 2, 1),
        },
    )
    raw = Path(spec["final_root"]) / "raw/SZSE/2011-02.parquet"
    assert not any(
        row["trading_date"] == "2011-02-01" and row["security_id"] == "CN-A:SZSE:000001"
        for row in pq.read_table(raw).to_pylist()
    )
    report = run_audit(repository, path, spec, tmp_path / "audit.json")
    assert report["gates"]["ACTION_SESSION_PRECONDITIONS"] == "PASS"
    assert report["runtime_scan"]["sessions"] == 7
    assert report["runtime_scan"]["action_session_failures"] == []
    assert not report["full_financial_admission"]


def test_candidate_scan_preserves_accepted_next_session_outside_loaded_period(
    tmp_path, monkeypatch
):
    repository, path, spec = audit_inputs(
        tmp_path, include_reference=False, bonus_updates={"listing_date": date(2011, 2, 2)}
    )

    class BoundedFullDataset(FullDataset):
        """Exercise the real loader's period-end successor, not a guessed calendar."""

        def __init__(self, root, manifest, period):
            super().__init__(
                root, manifest, TemporalPeriod(period.kind, period.start, date(2011, 2, 1))
            )
            assert self.calendar.sessions[-1].session_date == date(2011, 2, 1)
            assert self.next_session is not None
            assert self.next_session.session_date == date(2011, 2, 2)

    # This is specifically a period-boundary wiring check, not a full-period audit proof.
    monkeypatch.setattr(auditor, "FullDataset", BoundedFullDataset)
    report = run_audit(repository, path, spec, tmp_path / "audit.json")
    assert report["gates"]["ACTION_SESSION_PRECONDITIONS"] == "PASS"
    assert report["runtime_scan"]["action_session_failures"] == []
    assert not report["full_financial_admission"]
    assert not report["dataset_audited"] and not report["strategy_run"]


def test_real_candidate_session_scan_reports_missing_price_companion(tmp_path):
    repository, path, spec = audit_inputs(tmp_path, include_reference=False)
    report = run_audit(repository, path, spec, tmp_path / "audit.json")
    assert report["runtime_scan"]["unexplained_reference_adjustments"] == [
        {"trading_date": "2011-02-02", "security_id": "CN-A:SZSE:000001"}
    ]
    assert report["gates"]["REFERENCE_PRICE_CONTINUITY"] == "FAIL"
    assert not report["dataset_audited"] and report["audit_status"] == "FAIL_CLOSED"


def test_candidate_audit_rejects_published_event_not_matching_bound_source(tmp_path, monkeypatch):
    original = materializer.event_rows

    def corrupt(*args, **kwargs):
        rows = original(*args, **kwargs)
        for row in rows:
            row["acceptance_json"] = '{"unrelated_acceptance":true}'
        return rows

    with monkeypatch.context() as patch:
        patch.setattr(materializer, "event_rows", corrupt)
        repository, path, spec = audit_inputs(tmp_path)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="CANDIDATE_SOURCE_EVENT_SET_MISMATCH"):
        run_audit(repository, path, spec, output)
    assert not output.exists()


@pytest.mark.parametrize("code_file", ["scripts/audit_full_dataset.py", "app/research/engine.py"])
def test_auditor_change_during_input_loading_cannot_be_rebound(tmp_path, monkeypatch, code_file):
    repository, path, spec = audit_inputs(tmp_path)
    load = auditor.load_candidate_build_inputs
    digest = auditor.sha256_file
    changed = False
    bound_code = Path(auditor.__file__).parents[1] / code_file

    def changing_loader(*args, **kwargs):
        nonlocal changed
        result = load(*args, **kwargs)
        changed = True
        return result

    def changed_digest(file):
        if changed and Path(file).resolve() == bound_code.resolve():
            return "0" * 64
        return digest(file)

    monkeypatch.setattr(auditor, "load_candidate_build_inputs", changing_loader)
    monkeypatch.setattr(auditor, "sha256_file", changed_digest)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="CANDIDATE_AUDIT_INPUT_CHANGED"):
        run_audit(repository, path, spec, output)
    assert not output.exists()


def test_transient_runtime_partition_change_cannot_hide_price_gap(tmp_path, monkeypatch):
    repository, path, spec = audit_inputs(tmp_path, include_reference=False)
    partition = Path(spec["final_root"]) / "raw/SZSE/2011-02.parquet"
    original_bytes = partition.read_bytes()
    rows = pq.read_table(BytesIO(original_bytes)).to_pylist()
    for row in rows:
        if row["security_id"] == "CN-A:SZSE:000001":
            row["pre_close"] = "19.39"  # Ordinary-holder ratio, hiding the missing price companion.
    stream = BytesIO()
    pq.write_table(pa.Table.from_pylist(rows), stream)
    replacement = stream.getvalue()
    original_sessions = auditor.FullDataset.sessions

    def transient_sessions(self, **kwargs):
        # Disposable synthetic fixture only. Restore A after the runtime reads B.
        partition.chmod(0o644)
        partition.write_bytes(replacement)
        try:
            yield from original_sessions(self, **kwargs)
        finally:
            partition.write_bytes(original_bytes)

    monkeypatch.setattr(auditor.FullDataset, "sessions", transient_sessions)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="PARTITION_CONSUMED_BYTES_CHANGED"):
        run_audit(repository, path, spec, output)
    assert not output.exists() and partition.read_bytes() == original_bytes


def test_manifest_file_digest_cannot_bind_different_bytes_than_publication(tmp_path, monkeypatch):
    repository, path, spec = audit_inputs(tmp_path)
    manifest_path = Path(spec["final_root"]) / "manifest.json"
    original_read = Path.read_bytes

    def altered_read(file):
        data = original_read(file)
        return data + b" " if file == manifest_path else data

    monkeypatch.setattr(Path, "read_bytes", altered_read)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError, match="CANDIDATE_MANIFEST_BYTES_CHANGED"):
        run_audit(repository, path, spec, output)
    assert not output.exists()


@pytest.mark.parametrize("change", ["owner", "spec", "source", "partition", "extra_partition"])
def test_candidate_audit_rejects_unbound_state_without_report(tmp_path, change):
    repository, path, spec = audit_inputs(tmp_path)
    final = Path(spec["final_root"])
    if change == "owner":
        target = final / "build-inputs.json"
    elif change == "spec":
        spec["recorded_at_utc"] = "2026-10-08T00:00:01Z"
        path.write_text(json.dumps(spec))
        target = None
    elif change == "source":
        target = Path(spec["auxiliary_inputs"]["ordinary_references"]["path"])
    else:
        target = final / ("securities.parquet" if change == "partition" else "extra.parquet")
    if target is not None:
        if target.exists():
            target.chmod(0o644)
        target.write_bytes(b"{}")
    output = tmp_path / "audit.json"
    with pytest.raises((ValueError, KeyError)):
        run_audit(repository, path, spec, output)
    assert not output.exists()


@pytest.mark.parametrize(
    "target", ["dataset", "work", "repository", "source", "symlink", "hardlink"]
)
def test_candidate_audit_output_cannot_modify_inputs_or_owned_data(tmp_path, target):
    repository, path, spec = audit_inputs(tmp_path)
    source = Path(spec["auxiliary_inputs"]["ordinary_references"]["path"])
    before = sha256_file(source)
    output = {
        "dataset": Path(spec["final_root"]) / "audit.json",
        "work": Path(spec["work_root"]) / "audit.json",
        "repository": repository / "audit.json",
        "source": source,
    }.get(target, tmp_path / "alias.json")
    if target == "symlink":
        output.symlink_to(source)
    elif target == "hardlink":
        output.hardlink_to(source)
    with pytest.raises(ValueError, match="AUDIT_OUTPUT_NOT_ISOLATED"):
        run_audit(repository, path, spec, output)
    assert sha256_file(source) == before
