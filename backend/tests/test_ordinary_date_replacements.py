"""Replacement identity/lineage tests; parser acceptance is independently tested."""

import json
from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pytest

from app.data.catalog.checksums import sha256_file
from app.domain.markets import SecurityId
from app.domain.markets.corporate_actions import CorporateAction
from scripts import ordinary_distribution_dates as dates
from scripts.materialize_full_dataset import action_row
from tests.test_distribution_reference_basis import reference_fixture

TITLE = "2010年度权益分派实施公告"
PAGE = (
    "证券代码:000001证券简称:测试公告编号:2011-037"
    "测试股份有限公司" + TITLE + "重要提示:此为合成测试,非实际证据。"
)


@pytest.fixture
def replacement(tmp_path, monkeypatch):
    def reader(stream):
        return SimpleNamespace(
            pages=[
                SimpleNamespace(extract_text=lambda page=page: page)
                for page in json.loads(stream.getvalue())
            ]
        )

    monkeypatch.setattr(dates, "PdfReader", reader)
    monkeypatch.setattr(dates, "cash_payment_date", lambda *args: "2011-02-01")
    monkeypatch.setattr(dates, "same_day_listing", lambda *args: "2011-02-01")
    pdf = tmp_path / "notice.pdf"
    pdf.write_text(json.dumps([PAGE]), encoding="utf-8")
    fixture = tmp_path / "fixture"
    fixture.mkdir()
    _, cash, bonus, _ = reference_fixture(fixture)
    events = [
        CorporateAction.model_validate(
            {
                **event.model_dump(mode="json"),
                "security_id": {"value": "CN-A:SZSE:000001"},
                "source_document": TITLE,
                "source_url": "https://static.cninfo.com.cn/finalpage/2011-01-28/12345678.PDF",
                "source_document_sha256": sha256_file(pdf),
                "payment_date": None,
                "listing_date": None,
            }
        )
        for event in (cash, bonus)
    ]
    rows = [
        action_row(
            event.model_dump(mode="json"),
            event.event_checksum,
            event_kind="CORPORATE_ACTION",
            application_date="2011-02-01",
            security_id=str(event.security_id),
            acceptance={
                "event_checksum": event.event_checksum,
                "metadata_only_gaps": ["PAYMENT_DATE_NOT_NORMALIZED"],
                "synthetic_test_only": True,
            },
        )
        for event in events
    ]
    payload = {
        "version": dates.VERSION,
        "items": [
            {
                "event_checksum": event.event_checksum,
                "source_pdf": {"path": pdf.name, "sha256": sha256_file(pdf)},
                "source_title": TITLE,
            }
            for event in events
        ],
    }
    return rows, payload, tmp_path / "dates.json", pdf


def test_replaces_exact_dates_preserving_entitlements_and_negative_acceptance(replacement):
    rows, payload, path, _ = replacement
    original = deepcopy(rows)
    result = dates.normalize_ordinary_dates(rows, payload, path)
    assert rows == original and len(result) == len(rows)
    for before, after, field in zip(rows, result, ("payment_date", "listing_date"), strict=True):
        old, new = (json.loads(row["event_json"]) for row in (before, after))
        assert {key for key in old if old[key] != new[key]} == {field}
        assert new[field] == "2011-02-01"
        assert after["event_checksum"] == CorporateAction.model_validate(new).event_checksum
        assert before["event_checksum"] != after["event_checksum"]
        acceptance = json.loads(after["acceptance_json"])
        assert acceptance["original_acceptance"] == json.loads(before["acceptance_json"])
        assert (
            acceptance["date_normalization"]["original_event_checksum"] == before["event_checksum"]
        )
        assert not acceptance["date_normalization"]["financial_admission"]
        assert {
            key: value
            for key, value in before.items()
            if key
            not in {
                "event_json",
                "event_checksum",
                "acceptance_json",
            }
        } == {
            key: value
            for key, value in after.items()
            if key
            not in {
                "event_json",
                "event_checksum",
                "acceptance_json",
            }
        }
    reversed_payload = {**payload, "items": list(reversed(payload["items"]))}
    assert dates.normalize_ordinary_dates(rows, reversed_payload, path) == result
    assert dates.normalize_ordinary_dates(list(reversed(rows)), payload, path) == list(
        reversed(result)
    )


@pytest.mark.parametrize(
    "field",
    [
        "security_id",
        "action_type",
        "application_date",
        "effective_date",
        "ex_date",
        "cash_per_share",
        "share_ratio",
        "source_document_sha256",
        "source_url",
        "event_checksum",
    ],
)
def test_outer_identity_cannot_disagree_with_typed_event(replacement, field):
    rows, payload, path, _ = replacement
    rows[0][field] = "changed"
    with pytest.raises(ValueError, match="ORDINARY_DATES_"):
        dates.normalize_ordinary_dates(rows, payload, path)


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate_rows",
        "duplicate_target",
        "unsupported_kind",
        "title",
        "version",
        "injected_date",
        "source_sha",
        "prior_replacement",
    ],
)
def test_rejects_ambiguous_or_expanded_inputs(replacement, change):
    rows, payload, path, _ = replacement
    if change == "missing":
        rows.pop()
    elif change == "duplicate_rows":
        rows.append(deepcopy(rows[0]))
    elif change == "duplicate_target":
        payload["items"].append(deepcopy(payload["items"][0]))
    elif change == "unsupported_kind":
        rows[0]["event_kind"] = "RIGHTS_ISSUE"
    elif change == "title":
        payload["items"][0]["source_title"] = "2099年度权益分派实施公告"
    elif change == "version":
        payload["version"] = "UNVERIFIED"
    elif change == "injected_date":
        payload["items"][0]["payment_date"] = "2011-02-01"
    elif change == "source_sha":
        payload["items"][0]["source_pdf"]["sha256"] = "0" * 64
    else:
        rows[0]["acceptance_json"] = '{"date_normalization":{}}'
    with pytest.raises(ValueError):
        dates.normalize_ordinary_dates(rows, payload, path)


@pytest.mark.parametrize(
    "change", ["already_present", "unsupported_exchange", "amount", "source_url"]
)
def test_rebound_source_event_cannot_reuse_the_original_target(replacement, change):
    rows, payload, path, _ = replacement
    event = CorporateAction.model_validate_json(rows[0]["event_json"])
    changes = {
        "already_present": {"payment_date": date(2011, 2, 2)},
        "unsupported_exchange": {"security_id": SecurityId(value="CN-A:SSE:000001")},
        "amount": {"cash_per_share": "99"},
        "source_url": {"source_url": "https://example.org/notice.PDF"},
    }[change]
    changed = CorporateAction.model_validate({**event.model_dump(), **changes})
    rows[0] = action_row(
        changed.model_dump(mode="json"),
        changed.event_checksum,
        event_kind="CORPORATE_ACTION",
        application_date="2011-02-01",
        security_id=str(changed.security_id),
        acceptance={},
    )
    with pytest.raises(ValueError, match="ORDINARY_DATES_TARGET_NOT_UNIQUE"):
        dates.normalize_ordinary_dates(rows, payload, path)
    if change != "amount":
        payload["items"][0]["event_checksum"] = changed.event_checksum
        with pytest.raises(ValueError, match="ORDINARY_DATES_"):
            dates.normalize_ordinary_dates(rows, payload, path)


@pytest.mark.parametrize("alias", [False, True])
def test_pdf_bytes_and_resolved_source_path_are_verified(replacement, alias):
    rows, payload, path, pdf = replacement
    if alias:
        link = pdf.with_name("aliased.pdf")
        link.symlink_to(pdf)
        for item in payload["items"]:
            item["source_pdf"]["path"] = link.name
    else:
        pdf.write_text("replaced bytes")
    with pytest.raises(ValueError):
        dates.normalize_ordinary_dates(rows, payload, path)


def test_delayed_date_does_not_imply_accounting_support(replacement, monkeypatch):
    rows, payload, path, _ = replacement
    monkeypatch.setattr(dates, "cash_payment_date", lambda *args: "2011-02-02")
    with pytest.raises(ValueError, match="ORDINARY_DATES_DELAYED_DATE"):
        dates.normalize_ordinary_dates(rows, payload, path)
