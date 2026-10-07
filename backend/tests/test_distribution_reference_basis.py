import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal, localcontext

import pytest

from app.data.full_dataset import pa, pq
from app.domain.markets.corporate_actions import (
    CorporateActionType,
    require_supported_corporate_action,
)
from tests.test_full_dataset_materializer import _reference_fixture
from tests.test_rights_issue_policy import rights

CASES = (
    ("29.29", "0.2", "0.5", "0.1983936", "0.4959841", "19.45"),
    ("124.39", "0.5", "0.4", "0.4990476", "0.399238", "88.54"),
    ("39.03", "0.5", "0.4", "0.49791413", "0.39833131", "27.56"),
    ("18.60", "0.6", "0.4", "0.5928607", "0.3952404", "12.91"),
    ("76.92", "0.2", "0.4", "0.1982171", "0.3964343", "54.94"),
    ("32.62", "0.4", "0.4", "0.3965351", "0.3965351", "23.07"),
    ("68.40", "0.4", "0.4", "0.3987349", "0.3987349", "48.62"),
)


def reference_fixture(tmp_path, values=CASES[0]):
    previous, cash, ratio, price_cash, price_ratio, reference = values
    dataset = _reference_fixture(
        tmp_path,
        boundary="2011-02-01",
        cash_per_share=cash,
        previous_close=previous,
        reference_close=reference,
    )
    cash_action = dataset.actions["2011-02-01"]["CORPORATE_ACTION"][0].model_copy(
        update=dict(
            announcement_date=date(2011, 1, 28),
            record_date=date(2011, 1, 31),
            effective_date=date(2011, 2, 1),
            source_document="Isolated final distribution fixture",
            source_url="https://static.cninfo.com.cn/finalpage/2011-01-28/fixture.PDF",
            source_document_sha256="b" * 64,
            retrieved_at=datetime(2026, 10, 7, tzinfo=UTC),
        )
    )
    bonus = cash_action.model_copy(
        update=dict(
            action_type=CorporateActionType.BONUS_SHARE,
            cash_per_share=Decimal(0),
            share_ratio=Decimal(ratio),
            listing_date=date(2011, 2, 1),
        )
    )
    dataset.actions = {"2011-02-01": {"CORPORATE_ACTION": [cash_action, bonus]}}
    payload = dict(
        security_id={"value": str(cash_action.security_id)},
        announcement_date="2011-01-28",
        record_date="2011-01-31",
        ex_date="2011-02-01",
        cash_event_checksum=cash_action.event_checksum,
        share_event_checksum=bonus.event_checksum,
        cash_per_total_old_share=price_cash,
        share_ratio_per_total_old_share=price_ratio,
        basis="ISSUER_EXPLICIT_TOTAL_CAPITAL_REPURCHASE_EXCLUDED",
        source_document=cash_action.source_document,
        source_url=cash_action.source_url,
        source_document_sha256="b" * 64,
        retrieved_at="2026-10-07T00:00:00Z",
        source_version="ISOLATED_SOURCE_TERMS_NOT_REAL_AUTHORITY",
    )
    return dataset, cash_action, bonus, payload


def write_actions(dataset, cash, bonus, payload, *, duplicate=False):
    rows = [
        dict(
            application_date="2011-02-01",
            event_kind="CORPORATE_ACTION",
            event_json=a.model_dump_json(),
            event_checksum=a.event_checksum,
        )
        for a in (cash, bonus)
    ]
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    row = dict(
        application_date=payload["ex_date"],
        event_kind="ORDINARY_REFERENCE",
        event_json=serialized,
        event_checksum=hashlib.sha256(serialized.encode()).hexdigest(),
    )
    rows.extend([row, row] if duplicate else [row])
    pq.write_table(pa.Table.from_pylist(rows), dataset.root / "corporate-actions.parquet")


@pytest.mark.parametrize("values", CASES)
def test_explicit_price_basis_reaches_loader_without_changing_entitlements(tmp_path, values):
    dataset, cash, bonus, payload = reference_fixture(tmp_path, values)
    sid = cash.security_id
    assert [s.unexplained_reference_adjustment_ids for s in dataset.sessions()] == [(), (), (sid,)]
    originals = (
        cash.model_dump_json(),
        bonus.model_dump_json(),
        cash.event_checksum,
        bonus.event_checksum,
    )
    write_actions(dataset, cash, bonus, payload)
    dataset.actions = dataset._actions("2011-02-02")
    with localcontext() as context:
        context.prec = 3
        sessions = tuple(dataset.sessions())
    assert all(not s.unexplained_reference_adjustment_ids for s in sessions)
    assert sessions == tuple(dataset.sessions())
    assert sessions[1].corporate_actions == (cash, bonus)
    assert len(sessions[1].corporate_actions) == 2  # Price basis is never accounting.
    assert originals == (
        cash.model_dump_json(),
        bonus.model_dump_json(),
        cash.event_checksum,
        bonus.event_checksum,
    )
    assert not dataset._actions("2011-01-31")
    assert not any(s.corporate_actions for s in dataset.sessions(execution=False))


@pytest.mark.parametrize(
    "field,value",
    (
        ("security_id", {"value": "CN-A:SSE:600001"}),
        ("cash_event_checksum", "0" * 64),
        ("share_event_checksum", "0" * 64),
        ("source_document_sha256", "0" * 64),
        ("announcement_date", "2011-02-02"),
        ("record_date", "2011-02-01"),
        ("ex_date", "2011-02-02"),
        ("cash_per_total_old_share", "NaN"),
        ("share_ratio_per_total_old_share", "0"),
    ),
)
def test_price_basis_must_match_dated_source_and_whole_entitlement_pair(tmp_path, field, value):
    dataset, cash, bonus, payload = reference_fixture(tmp_path)
    payload[field] = value
    write_actions(dataset, cash, bonus, payload)
    with pytest.raises(ValueError):
        dataset._actions("2011-02-02")


def test_duplicate_price_basis_is_not_silently_deduplicated(tmp_path):
    dataset, cash, bonus, payload = reference_fixture(tmp_path)
    write_actions(dataset, cash, bonus, payload, duplicate=True)
    with pytest.raises(ValueError, match="DUPLICATE_ORDINARY_REFERENCE"):
        dataset._actions("2011-02-02")


@pytest.mark.parametrize("event_kind", ["RIGHTS_ISSUE", "CORPORATE_ACTION"])
@pytest.mark.parametrize("with_reference", [False, True])
def test_carried_reference_cannot_be_bypassed_by_later_rights(tmp_path, event_kind, with_reference):
    dataset, cash, bonus, payload = reference_fixture(tmp_path)
    write_actions(dataset, cash, bonus, payload)
    path = dataset.root / "corporate-actions.parquet"
    rows = pq.read_table(path).to_pylist()
    if not with_reference:
        rows = [row for row in rows if row["event_kind"] != "ORDINARY_REFERENCE"]
    later_rights = rights(
        security_id=str(cash.security_id),
        announcement_date="2011-01-28",
        record_date="2011-01-31",
        subscription_start_date="2011-02-01",
        subscription_end_date="2011-02-01",
        subscription_deadline="2011-02-01",
        ex_date="2011-02-02",
        effective_date="2011-02-02",
    )
    require_supported_corporate_action(later_rights)
    rows.append(
        dict(
            application_date="2011-02-02",
            event_kind=event_kind,
            event_json=later_rights.model_dump_json(),
            event_checksum=later_rights.event_checksum,
        )
    )
    pq.write_table(pa.Table.from_pylist(rows), path)
    raw_path = dataset.root / "2011-02.parquet"
    raw = pq.read_table(raw_path).to_pylist()
    for row in raw:
        if row["security_id"] == str(cash.security_id):
            row["pre_close"] = "9.99"  # Official isolated reference is 19.45.
    pq.write_table(pa.Table.from_pylist(raw), raw_path)
    dataset.actions = dataset._actions("2011-02-02")
    sessions = tuple(dataset.sessions())
    assert sessions[1].corporate_actions == (cash, bonus)
    assert sessions[2].corporate_actions == (later_rights,)
    # Keep the existing structural path only when no explicit reference is pending.
    expected = (cash.security_id,) if with_reference else ()
    assert sessions[2].unexplained_reference_adjustment_ids == expected


def test_feature_only_adjusted_price_is_independent_of_caller_context(tmp_path):
    dataset, cash, _, _ = reference_fixture(tmp_path)
    row = dict(
        security_id=str(cash.security_id),
        trading_date="2011-01-31",
        raw_close="29.29",
        hfq_factor_at_day="1.23456789",
        volume_lower="100",
        volume_upper="200",
        amount_lower="1000",
        amount_upper="2000",
        lineage="OFFICIAL_PARTIAL_FEATURE_ONLY_NON_TRADABLE",
    )
    pq.write_table(pa.Table.from_pylist([row]), dataset.root / "feature-only-observations.parquet")
    expected = dataset._features("2011-01-31")
    for precision in (3, 50):
        with localcontext() as context:
            context.prec = precision
            assert dataset._features("2011-01-31") == expected


def test_price_reference_record_requires_its_own_checksum_and_exact_application_day(tmp_path):
    dataset, cash, bonus, payload = reference_fixture(tmp_path)
    write_actions(dataset, cash, bonus, payload)
    path = dataset.root / "corporate-actions.parquet"
    original = pq.read_table(path).to_pylist()
    for field, value in (("event_checksum", "0" * 64), ("application_date", "2011-02-02")):
        rows = [
            {**row, **({field: value} if row["event_kind"] == "ORDINARY_REFERENCE" else {})}
            for row in original
        ]
        pq.write_table(pa.Table.from_pylist(rows), path)
        with pytest.raises(ValueError, match="ORDINARY_REFERENCE_RECORD_MISMATCH"):
            dataset._actions("2011-02-02")
