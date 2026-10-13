"""Pinned source-date derivation reaches real isolated builds, not financial admission."""

import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pyarrow.parquet as pq
import pytest

from app.data.catalog.checksums import sha256_file
from app.domain.markets.corporate_actions import CorporateAction, OrdinaryDistributionReference
from scripts import materialize_full_dataset as materializer
from scripts import ordinary_distribution_dates as dates
from scripts.full_dataset_build_inputs import CandidateBuildInputs
from tests.test_full_dataset_build_inputs import build
from tests.test_full_dataset_sources import _manifest
from tests.test_successor_dataset_audit import audit_inputs, run_audit
from tests.test_successor_reference_inputs import reference_inputs, update_spec

TITLE = "2010年度权益分派实施公告"
NOTICE = (
    "证券代码:000001 证券简称:测试股份 公告编号:2011-001\n"
    "测试股份有限公司\n2010年度权益分派实施公告\n"
    "一、权益分派方案\n向全体股东每10股派2元(含税),每10股转增5股。"
    "二、股权登记日与除权除息日\n股权登记日为2011年1月31日,"
    "除权除息日为2011年2月1日。"
    "三、分派对象\n本次权益分派对象为:2011年1月31日下午交易所收市后,"
    "在登记结算公司登记在册的本公司全体股东。"
    "四、转增股本方法\n本次转增股于2011年02月01日直接记入股东证券账户。"
    "五、本次转增的无限售条件流通股的起始交易日为2011年2月1日。"
    "六、现金红利发放日:2011年2月1日。"
    "2、本公司此次委托中国证券登记结算有限责任公司深圳分公司代派的股息将于"
    "2011年02月01日通过股东托管证券公司(或其他托管机构)直接划入其资金账户。"
)


class JsonPagesReader:
    def __init__(self, stream):
        self.pages = [
            SimpleNamespace(extract_text=lambda text=text: text) for text in json.load(stream)
        ]


def prepare_dates(tmp_path, monkeypatch, *, audit_ready=False, relative_pdf=True):
    monkeypatch.setattr(dates, "PdfReader", JsonPagesReader)
    if audit_ready:
        repository, path, spec = audit_inputs(tmp_path)
    else:
        repository, path, spec, _, _, _ = reference_inputs(tmp_path)
    spec["work_root"] = str(tmp_path / "dates-work")
    spec["final_root"] = str(tmp_path / "dates-candidate" / spec["dataset_id"])
    source = tmp_path / "date-source" / "notice-pages.json"
    source.parent.mkdir()
    source.write_text(json.dumps([NOTICE]), encoding="utf-8")
    source_sha = sha256_file(source)
    inventory_path = tmp_path / "ordinary-dates.json"
    items, original_events, replacements, acceptances = [], {}, {}, {}
    contracts = {row["name"]: row for row in spec["source_contracts"]}
    for name, field in (("CASH_ACTIONS", "payment_date"), ("BONUS_ACTIONS", "listing_date")):
        original = json.loads(Path(contracts[name]["source_path"]).read_bytes())["events"][0]
        event = CorporateAction.model_validate(
            {
                **original["event"],
                "security_id": {"value": "CN-A:SZSE:000001"},
                "source_document": TITLE,
                "source_document_sha256": source_sha,
                "source_url": "https://static.cninfo.com.cn/finalpage/2011-01-28/12345678.PDF",
                field: None,
            }
        )
        accepted = {
            "event_checksum": event.event_checksum,
            "status": "SYNTHETIC_TEST_ONLY",
            "policy_id": "UNCHANGED_TEST_POLICY",
            "details": {"keep": [name, "old evidence"]},
        }
        _manifest(
            Path(contracts[name]["source_path"]),
            {"events": [{"event": event.model_dump(mode="json"), **accepted}]},
        )
        original_events[field] = event
        acceptances[field] = accepted
        replacements[field] = CorporateAction.model_validate(
            {**event.model_dump(), field: date(2011, 2, 1)}
        )
        items.append(
            {
                "event_checksum": event.event_checksum,
                "source_pdf": {
                    "path": str(source.relative_to(tmp_path) if relative_pdf else source),
                    "sha256": source_sha,
                },
                "source_title": TITLE,
            }
        )
    inventory = {"version": "ORDINARY_DISTRIBUTION_DATES_V1", "items": items}
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    spec["auxiliary_inputs"]["ordinary_dates"] = {
        "path": str(inventory_path),
        "sha256": sha256_file(inventory_path),
    }
    reference_pin = spec["auxiliary_inputs"]["ordinary_references"]
    reference_path = Path(reference_pin["path"])
    reference_report = json.loads(reference_path.read_bytes())
    reference_row = reference_report["private_candidate_reference_rows"][0]
    reference = OrdinaryDistributionReference.model_validate(
        {
            **json.loads(reference_row["event_json"]),
            "security_id": {"value": "CN-A:SZSE:000001"},
            "source_document": TITLE,
            "source_document_sha256": source_sha,
            "source_url": replacements["payment_date"].source_url,
            "cash_event_checksum": replacements["payment_date"].event_checksum,
            "share_event_checksum": replacements["listing_date"].event_checksum,
        }
    )
    reference_row.update(
        event_json=reference.model_dump_json(), event_checksum=reference.event_checksum
    )
    reference_report.pop("manifest_sha256")
    _manifest(reference_path, reference_report)
    reference_pin["sha256"] = sha256_file(reference_path)
    update_spec(repository, path, spec)
    return {
        "repository": repository,
        "path": path,
        "spec": spec,
        "source": source,
        "inventory_path": inventory_path,
        "inventory": inventory,
        "original_events": original_events,
        "replacements": replacements,
        "acceptances": acceptances,
    }


def repin_inventory(case):
    path = case["inventory_path"]
    path.write_text(json.dumps(case["inventory"]), encoding="utf-8")
    case["spec"]["auxiliary_inputs"]["ordinary_dates"]["sha256"] = sha256_file(path)
    update_spec(case["repository"], case["path"], case["spec"])


def input_hashes(tmp_path):
    return {path: sha256_file(path) for path in tmp_path.rglob("*") if path.is_file()}


def assert_unchanged(hashes):
    assert all(sha256_file(path) == digest for path, digest in hashes.items())


@pytest.mark.parametrize("relative_pdf", [True, False])
def test_real_build_and_resume_preserve_inputs_and_only_replace_pinned_dates(
    tmp_path, monkeypatch, relative_pdf
):
    case = prepare_dates(tmp_path, monkeypatch, relative_pdf=relative_pdf)
    before = input_hashes(tmp_path)
    report = build(case["repository"], case["path"])
    assert build(case["repository"], case["path"]) == report
    rows = pq.read_table(Path(case["spec"]["final_root"]) / "corporate-actions.parquet").to_pylist()
    for field, expected in case["replacements"].items():
        row = next(row for row in rows if row["event_checksum"] == expected.event_checksum)
        event = CorporateAction.model_validate_json(row["event_json"])
        assert event == expected
        original = case["original_events"][field]
        assert {
            name
            for name, value in event.model_dump().items()
            if value != original.model_dump()[name]
        } == {field}
        assert row["policy_id"] == "UNCHANGED_TEST_POLICY"
        assert json.loads(row["acceptance_json"]) == {
            "event_checksum": expected.event_checksum,
            "original_acceptance": case["acceptances"][field],
            "date_normalization": {
                "version": "ORDINARY_DISTRIBUTION_DATES_V1",
                "original_event_checksum": original.event_checksum,
                "event_checksum": expected.event_checksum,
                "field": field,
                "date": "2011-02-01",
                "source_pdf_sha256": sha256_file(case["source"]),
                "source_title": TITLE,
                "financial_admission": False,
            },
        }
    assert report["ordinary_reference_rows"] == 1
    assert report["accounting_action_rows"] == 26
    assert not report["full_financial_admission"] and not report["dataset_audited"]
    owner = json.loads((Path(case["spec"]["work_root"]) / "build-inputs.json").read_bytes())
    assert {
        "ordinary_distribution_dates.py",
        "distribution_payment_terms.py",
        "retained_bonus_terms.py",
    } <= set(owner["producer_sha256"])
    assert_unchanged(before)


def test_real_audit_reconstructs_normalized_actions_without_financial_pass(tmp_path, monkeypatch):
    case = prepare_dates(tmp_path, monkeypatch, audit_ready=True)
    build(case["repository"], case["path"])
    before = input_hashes(tmp_path)
    report = run_audit(case["repository"], case["path"], case["spec"], tmp_path / "audit.json")
    assert report["gates"]["SOURCE_EVENT_SET_MATCH"] == "PASS"
    assert report["gates"]["REFERENCE_PRICE_CONTINUITY"] == "PASS"
    assert report["gates"]["SOURCE_ECONOMIC_INTEGRITY"] == "NOT_EVIDENCED"
    assert report["gates"]["CASH_RECONCILIATION"] == "NOT_EVIDENCED"
    assert report["audit_status"] != "PASS"
    assert not report["dataset_audited"] and not report["full_financial_admission"]
    assert not report["accounting_invariant_evidence"]["portfolio_accounting_run"]
    assert {
        "ordinary_distribution_dates.py",
        "distribution_payment_terms.py",
        "retained_bonus_terms.py",
    } <= {Path(path).name for path in report["audit_code_sha256"]}
    assert_unchanged(before)


def test_interrupted_date_build_resumes_without_replacing_raw_partitions(tmp_path, monkeypatch):
    case = prepare_dates(tmp_path, monkeypatch)
    write_table = materializer.write_table

    def interrupt(*args, **kwargs):
        raise RuntimeError("SIMULATED_DATE_BUILD_INTERRUPTION")

    monkeypatch.setattr(materializer, "write_table", interrupt)
    with pytest.raises(RuntimeError, match="SIMULATED_DATE_BUILD_INTERRUPTION"):
        build(case["repository"], case["path"])
    staged = Path(case["spec"]["work_root"]) / "catalog-build"
    raw_before = {
        path.relative_to(staged): (sha256_file(path), path.stat().st_mtime_ns)
        for path in (staged / "raw").rglob("*.parquet")
    }
    assert len(raw_before) == 2
    monkeypatch.setattr(materializer, "write_table", write_table)
    report = build(case["repository"], case["path"])
    final = Path(case["spec"]["final_root"])
    assert raw_before == {
        path.relative_to(final): (sha256_file(path), path.stat().st_mtime_ns)
        for path in (final / "raw").rglob("*.parquet")
    }
    assert build(case["repository"], case["path"]) == report
    assert not report["full_financial_admission"]


@pytest.mark.parametrize("change", ["duplicate", "missing_target", "source_sha", "supplied_date"])
def test_invalid_date_inventory_cannot_publish_candidate(tmp_path, monkeypatch, change):
    case = prepare_dates(tmp_path, monkeypatch)
    items = case["inventory"]["items"]
    if change == "duplicate":
        items.append(deepcopy(items[0]))
    elif change == "missing_target":
        items[0]["event_checksum"] = "0" * 64
    elif change == "source_sha":
        for item in items:
            item["source_pdf"]["sha256"] = "0" * 64
    else:
        items[0]["payment_date"] = "2011-02-01"
    repin_inventory(case)
    before = input_hashes(tmp_path)
    with pytest.raises(ValueError):
        build(case["repository"], case["path"])
    assert not Path(case["spec"]["final_root"]).exists()
    assert_unchanged(before)


def test_existing_price_reference_must_not_be_automatically_resigned(tmp_path, monkeypatch):
    case = prepare_dates(tmp_path, monkeypatch)
    pin = case["spec"]["auxiliary_inputs"]["ordinary_references"]
    reference_path = Path(pin["path"])
    report = json.loads(reference_path.read_bytes())
    report.pop("manifest_sha256")
    row = report["private_candidate_reference_rows"][0]
    event = OrdinaryDistributionReference.model_validate(
        {
            **json.loads(row["event_json"]),
            "cash_event_checksum": case["original_events"]["payment_date"].event_checksum,
            "share_event_checksum": case["original_events"]["listing_date"].event_checksum,
        }
    )
    row.update(event_json=event.model_dump_json(), event_checksum=event.event_checksum)
    _manifest(reference_path, report)
    pin["sha256"] = sha256_file(reference_path)
    update_spec(case["repository"], case["path"], case["spec"])
    with pytest.raises(ValueError, match="ORDINARY_REFERENCE"):
        build(case["repository"], case["path"])
    assert not Path(case["spec"]["final_root"]).exists()


@pytest.mark.parametrize("target", ["inventory", "source"])
def test_changed_pinned_date_input_is_rejected_before_publication(tmp_path, monkeypatch, target):
    case = prepare_dates(tmp_path, monkeypatch)
    path = case["inventory_path"] if target == "inventory" else case["source"]
    path.write_bytes(path.read_bytes() + b" ")
    before = input_hashes(tmp_path)
    with pytest.raises(ValueError):
        build(case["repository"], case["path"])
    assert not Path(case["spec"]["final_root"]).exists()
    assert_unchanged(before)


def test_date_selection_is_bound_to_preflight_input_identity(tmp_path, monkeypatch):
    case = prepare_dates(tmp_path, monkeypatch)
    del case["spec"]["auxiliary_inputs"]["ordinary_dates"]
    case["path"].write_text(json.dumps(case["spec"]))
    with pytest.raises(ValueError, match="CANDIDATE_PREFLIGHT_INPUT_SELECTION_MISMATCH"):
        build(case["repository"], case["path"])
    assert not Path(case["spec"]["work_root"]).exists()


def test_source_pdf_pin_is_part_of_build_output_isolation(tmp_path, monkeypatch):
    case = prepare_dates(tmp_path, monkeypatch)
    case["spec"]["work_root"] = str(case["source"].parent)
    update_spec(case["repository"], case["path"], case["spec"])
    before = input_hashes(tmp_path)
    with pytest.raises(ValueError, match="CANDIDATE_INPUT_OUTPUT_OVERLAP"):
        build(case["repository"], case["path"])
    assert_unchanged(before)


@pytest.mark.parametrize("alias", ["direct", "symlink", "hardlink"])
def test_audit_output_cannot_replace_date_pdf_input(tmp_path, monkeypatch, alias):
    case = prepare_dates(tmp_path, monkeypatch, audit_ready=True)
    build(case["repository"], case["path"])
    source = case["source"]
    output = source if alias == "direct" else tmp_path / "output-alias.json"
    if alias == "symlink":
        output.symlink_to(source)
    elif alias == "hardlink":
        output.hardlink_to(source)
    before = source.read_bytes()
    with pytest.raises(ValueError, match="AUDIT_OUTPUT_NOT_ISOLATED"):
        run_audit(case["repository"], case["path"], case["spec"], output)
    assert source.read_bytes() == before


@pytest.mark.parametrize("phase", ["build", "audit"])
def test_source_changed_after_pdf_parse_is_rechecked_before_output(tmp_path, monkeypatch, phase):
    case = prepare_dates(tmp_path, monkeypatch, audit_ready=phase == "audit")
    if phase == "audit":
        build(case["repository"], case["path"])
    changed = False

    class ChangeAfterRead(JsonPagesReader):
        def __init__(self, stream):
            nonlocal changed
            super().__init__(stream)
            if not changed:
                changed = True
                case["source"].write_bytes(case["source"].read_bytes() + b" ")

    monkeypatch.setattr(dates, "PdfReader", ChangeAfterRead)
    output = tmp_path / "audit.json"
    with pytest.raises(ValueError):
        if phase == "build":
            build(case["repository"], case["path"])
        else:
            run_audit(case["repository"], case["path"], case["spec"], output)
    assert changed
    assert not output.exists()
    if phase == "build":
        assert not Path(case["spec"]["final_root"]).exists()


def test_pinned_source_change_blocks_existing_build_resume(tmp_path, monkeypatch):
    case = prepare_dates(tmp_path, monkeypatch)
    build(case["repository"], case["path"])
    final = Path(case["spec"]["final_root"])
    before = input_hashes(final)
    case["source"].write_bytes(case["source"].read_bytes() + b" ")
    with pytest.raises(ValueError):
        build(case["repository"], case["path"])
    assert_unchanged(before)


def test_candidate_recheck_includes_nested_pdf_pins(tmp_path, monkeypatch):
    case = prepare_dates(tmp_path, monkeypatch)
    candidate = CandidateBuildInputs.model_validate(case["spec"])
    assert candidate.date_source_pins(case["repository"]) == {
        case["source"]: sha256_file(case["source"])
    }
