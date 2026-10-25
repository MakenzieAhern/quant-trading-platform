"""Loader trust-boundary tests with mocked PDF text, not real-PDF acceptance."""

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.data.catalog.checksums import sha256_file
from scripts import candidate_cash_corrections as loader

SID = "CN-A:SZSE:300155"
OLD_URL = "https://static.cninfo.com.cn/finalpage/2011-04-27/59344595.PDF"
NEW_URL = "https://static.cninfo.com.cn/finalpage/2011-04-27/59352083.PDF"
ISSUER = "广东安居宝数码科技股份有限公司"
PARAGRAPH = (
    "3、本次利润分配以截止2010年12月31日总股本72,000,000股为基数,"
    "向全体股东每10股派发现金红利8元(含税,扣税后个人每10股派现金红利7.2元),"
    "共计派发股利576,000,000元。"
)
ORIGINAL = (
    "证券代码:300155 证券简称:安居宝 公告编号:2011-037\n"
    + ISSUER
    + "2010年度权益分派实施公告\n股权登记日:2011年5月5日。除权除息日:2011年5月6日。"
    "二、利润分配及转增股本方案\n"
    "每10股转增15股。" + PARAGRAPH
)
CORRECTION = (
    "证券代码:300155 证券简称:安居宝 公告编号:2011-038\n" + ISSUER + "更正公告\n"
    "本公司及董事会全体成员保证信息披露的内容真实、准确、完整,没有虚假记载、误导性陈述或重大遗漏。"
    + ISSUER
    + "于2011年4月26日公告的文件,公告编号2011-037《"
    + ISSUER
    + "2010年度权益分派实施公告》,公告第一页,二、利润分配及转增股本方案的"
    "共计派发股利金额由于笔误出现错误。"
    "原文:"
    + PARAGRAPH
    + "现更正为:"
    + PARAGRAPH.replace("576,000,000", "57,600,000")
    + "本公司对上述更正给投资者带来的不便深表歉意,并将认真汲取教训,切实履行好信息披露义务,"
    "不断提高信息披露质量。特此公告。" + ISSUER + "董事会2011年4月27日"
)


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return {"path": path.name, "sha256": sha256_file(path)}


@pytest.fixture
def correction_inputs(tmp_path, monkeypatch):
    # The reader consumes the exact bytes passed by the production checksum reader.
    def fake_reader(stream):
        pages = json.loads(stream.getvalue())
        return SimpleNamespace(
            pages=[SimpleNamespace(extract_text=lambda page=page: page) for page in pages]
        )

    monkeypatch.setattr(loader, "PdfReader", fake_reader)
    original = save(tmp_path / "original.pdf", [ORIGINAL])
    correction = save(tmp_path / "correction.pdf", [CORRECTION])
    index = {
        "announcements": [
            {
                "secCode": "300155",
                "orgId": "9900015941",
                "announcementId": doc,
                "announcementTitle": title,
                "adjunctType": "PDF",
                "adjunctUrl": f"finalpage/2011-04-27/{doc}.PDF",
                "announcementTime": timestamp,
            }
            for doc, title, timestamp in (
                ("59344595", "2010年度权益分派实施公告", 1303857000000),
                ("59352083", "更正公告", 1303890780123),
            )
        ]
    }
    index_pin = save(tmp_path / "index.json", index)
    receipt_pin = save(
        tmp_path / "correction.meta.json",
        {
            "sha256": correction["sha256"],
            "http_status": 200,
            "url": NEW_URL,
            "retrieved_at_utc": "2026-01-01T01:02:03+00:00",
        },
    )
    index_receipt_pin = save(
        tmp_path / "index.meta.json",
        {
            "sha256": index_pin["sha256"],
            "http_status": 200,
            "url": loader.CNINFO_INDEX,
            "retrieved_at_utc": "2026-01-01T01:02:02Z",
            "params": {"stock": "300155,9900015941", "column": "szse"},
        },
    )
    gap = {
        "security_id": SID,
        "record_date": "2011-05-05",
        "ex_date": "2011-05-06",
        "source_sha256": original["sha256"],
        "source_url": OLD_URL,
        "declared_shares": "72000000",
        "declared_gross_cash_per_share": "0.8",
        "declared_total": "576000000",
        "derived_exact_total": "57600000",
    }
    parent = {
        "records": [gap, {"security_id": "UNCHANGED_OTHER_GAP"}],
        "financial_admission": False,
    }
    parent_pin = save(tmp_path / "parent.json", parent)
    gaps = {
        **deepcopy(parent),
        loader.EXTENSION: {
            "version": "CASH_AGGREGATE_CORRECTIONS_V1",
            "parent_inventory": parent_pin,
            "items": [
                {
                    "security_id": SID,
                    "record_date": "2011-05-05",
                    "ex_date": "2011-05-06",
                    "original_pdf": original,
                    "correction_pdf": correction,
                    "correction_receipt": receipt_pin,
                    "official_index": index_pin,
                    "official_index_receipt": index_receipt_pin,
                }
            ],
        },
    }
    inventory = tmp_path / "inventory.json"
    save(inventory, gaps)
    return gaps, inventory


def item(gaps):
    return gaps[loader.EXTENSION]["items"][0]


def change_file(inputs, field, mutate):
    gaps, inventory = inputs
    pin = item(gaps)[field]
    path = inventory.parent / pin["path"]
    value = json.loads(path.read_bytes())
    changed = mutate(value)
    item(gaps)[field] = save(path, changed if changed is not None else value)
    if field in {"original_pdf", "correction_pdf", "official_index"}:
        if field == "original_pdf":
            gaps["records"][0]["source_sha256"] = item(gaps)[field]["sha256"]
            parent = {key: value for key, value in gaps.items() if key != loader.EXTENSION}
            gaps[loader.EXTENSION]["parent_inventory"] = save(
                inventory.parent / "parent.json", parent
            )
        else:
            receipt = (
                "correction_receipt" if field == "correction_pdf" else "official_index_receipt"
            )
            change_file(
                inputs, receipt, lambda value: value.update(sha256=item(gaps)[field]["sha256"])
            )


def test_legacy_has_no_new_authority_or_file_access():
    assert loader.load_cash_corrections({"records": []}, Path("missing")) == ([], {})


def test_valid_correction_preserves_parent_and_exact_millisecond_boundary(correction_inputs):
    gaps, inventory = correction_inputs
    before = deepcopy(gaps)
    proofs, pins = loader.load_cash_corrections(gaps, inventory)
    assert gaps == before
    assert len(proofs) == 1 and len(pins) == 6
    proof = proofs[0]
    assert proof["cash_per_share"] == "0.8"
    assert proof["bonus_share_ratio"] == "1.5"
    assert proof["base_shares"] == 72000000
    assert proof["original_aggregate"] == "576000000"
    assert proof["corrected_aggregate"] == "57600000"
    assert proof["published_at"] == "2011-04-27T07:53:00.123000+00:00"
    assert proof["original_published_at"] == "2011-04-26T22:30:00+00:00"
    assert proof["original_notice_number"] == "2011-037"
    assert proof["correction_notice_number"] == "2011-038"
    assert proof["original_paragraph"] == PARAGRAPH
    assert all(path.is_absolute() and sha256_file(path) == digest for path, digest in pins.items())
    gaps["records"].reverse()
    assert loader.load_cash_corrections(gaps, inventory)[0] == proofs


@pytest.mark.parametrize("change", ["delete", "terms", "extra", "nested", "zero_not_false"])
def test_parent_inventory_cannot_be_weakened(correction_inputs, change):
    gaps, inventory = correction_inputs
    if change == "delete":
        gaps["records"].pop()
    elif change == "terms":
        gaps["records"][0]["declared_gross_cash_per_share"] = "0.9"
    elif change == "extra":
        gaps["financial_admission"] = True
    elif change == "zero_not_false":
        gaps["financial_admission"] = 0
    else:
        parent = deepcopy(gaps)
        gaps[loader.EXTENSION]["parent_inventory"] = save(inventory.parent / "parent.json", parent)
    with pytest.raises(ValueError, match="PARENT"):
        loader.load_cash_corrections(gaps, inventory)


@pytest.mark.parametrize("change", ["version", "unknown", "duplicate", "pin", "conflicting"])
def test_extension_and_pin_validation(correction_inputs, change):
    gaps, inventory = correction_inputs
    if change == "version":
        gaps[loader.EXTENSION]["version"] = "UNKNOWN"
    elif change == "unknown":
        item(gaps)["reviewed"] = True
    elif change == "duplicate":
        gaps[loader.EXTENSION]["items"].append(deepcopy(item(gaps)))
    elif change == "pin":
        item(gaps)["correction_pdf"]["sha256"] = "0" * 64
    else:
        item(gaps)["correction_pdf"] = {**item(gaps)["original_pdf"], "sha256": "0" * 64}
    with pytest.raises(ValueError):
        loader.load_cash_corrections(gaps, inventory)


@pytest.mark.parametrize(
    "field,old,new",
    [
        ("correction_pdf", "证券代码:300155", "证券代码:300147"),
        ("correction_pdf", "公告编号2011-037", "公告编号2011-036"),
        ("correction_pdf", "公告第一页", "公告第二页"),
        ("correction_pdf", "现更正为:", "不作更正:"),
        ("correction_pdf", "57,600,000", "58,600,000"),
        ("correction_pdf", "8元(含税", "9元(含税"),
        ("original_pdf", "576,000,000", "57,600,000"),
        ("original_pdf", "每10股转增15股", "每10股转增15股和每10股转增16股"),
        ("correction_pdf", "2011年4月27日", "2011年4月28日"),
    ],
)
def test_pdf_text_cannot_claim_a_different_correction(correction_inputs, field, old, new):
    change_file(correction_inputs, field, lambda pages: [page.replace(old, new) for page in pages])
    with pytest.raises(ValueError):
        loader.load_cash_corrections(*correction_inputs)


def test_original_paragraph_must_be_on_referenced_first_page(correction_inputs):
    change_file(
        correction_inputs,
        "original_pdf",
        lambda pages: [pages[0].replace(PARAGRAPH, ""), PARAGRAPH],
    )
    with pytest.raises(ValueError, match="FIRST_PAGE"):
        loader.load_cash_corrections(*correction_inputs)


@pytest.mark.parametrize("extra", ["另每10股派发现金红利由8改9。", "股权登记日改为2011年5月4日。"])
@pytest.mark.parametrize("where", ["before", "after", "inside_apology"])
def test_other_material_changes_outside_quoted_paragraph_fail_closed(
    correction_inputs, extra, where
):
    def alter(pages):
        if where == "before":
            return [extra + pages[0]]
        if where == "after":
            return [pages[0] + extra]
        return [pages[0].replace("特此公告。", extra + "特此公告。")]

    change_file(correction_inputs, "correction_pdf", alter)
    with pytest.raises(ValueError, match="FULL_DOCUMENT"):
        loader.load_cash_corrections(*correction_inputs)


@pytest.mark.parametrize(
    "field,key,value",
    [
        ("correction_receipt", "http_status", 403),
        ("correction_receipt", "sha256", "0" * 64),
        ("correction_receipt", "url", NEW_URL.replace("cninfo.com.cn", "example.com")),
        ("correction_receipt", "retrieved_at_utc", "2026-01-01T00:00:00"),
        ("correction_receipt", "retrieved_at_utc", "2011-04-27T07:52:00+00:00"),
        ("correction_receipt", "retrieved_at_utc", "9999-01-01T00:00:00+00:00"),
        ("correction_receipt", "retrieved_at_utc", "2026-01-01T00:00:00+08:00"),
        ("official_index_receipt", "sha256", "0" * 64),
        ("official_index_receipt", "url", "https://example.com/query"),
        ("official_index_receipt", "params", {"stock": "300147,9900015941"}),
        ("official_index_receipt", "params", {"stock": "300155,9900015941", "column": "sse"}),
        ("official_index_receipt", "params", None),
    ],
)
def test_receipts_must_close_the_same_official_bytes(correction_inputs, field, key, value):
    change_file(correction_inputs, field, lambda receipt: receipt.update({key: value}))
    with pytest.raises(ValueError):
        loader.load_cash_corrections(*correction_inputs)


@pytest.mark.parametrize(
    "key,value",
    [
        ("secCode", "300147"),
        ("orgId", "9900015942"),
        ("adjunctUrl", "finalpage/2011-04-27/other.PDF"),
        ("announcementId", "59352084"),
        ("announcementTitle", "业绩预告"),
        ("announcementTime", 1303856999999),
        ("announcementTime", 1303890780.123),
        ("announcementTime", 10**100),
        ("announcementTime", int(datetime(2011, 5, 4, 16, tzinfo=UTC).timestamp()) * 1000),
    ],
)
def test_official_identity_and_publication_boundaries(correction_inputs, key, value):
    change_file(
        correction_inputs,
        "official_index",
        lambda index: index["announcements"][1].update({key: value}),
    )
    with pytest.raises(ValueError):
        loader.load_cash_corrections(*correction_inputs)


def test_duplicate_official_announcement_is_not_silently_overwritten(correction_inputs):
    change_file(
        correction_inputs,
        "official_index",
        lambda index: index["announcements"].append(deepcopy(index["announcements"][1])),
    )
    with pytest.raises(ValueError, match="DUPLICATE_ANNOUNCEMENT"):
        loader.load_cash_corrections(*correction_inputs)


def test_verified_reader_bytes_are_the_pdf_parser_input(correction_inputs, monkeypatch):
    original_reader = loader.verified_file_bytes

    def changed_pdf(path, digest):
        if path.name == "correction.pdf":
            path.write_bytes(b"changed during read")
        return original_reader(path, digest)

    monkeypatch.setattr(loader, "verified_file_bytes", changed_pdf)
    with pytest.raises(ValueError, match="PARTITION_CONSUMED_BYTES_CHANGED"):
        loader.load_cash_corrections(*correction_inputs)


@pytest.mark.parametrize(
    "declared",
    ["declared_shares", "declared_gross_cash_per_share", "declared_total", "derived_exact_total"],
)
def test_changed_parent_claims_cannot_override_pdf_terms(correction_inputs, declared):
    gaps, inventory = correction_inputs
    gaps["records"][0][declared] = "123"
    parent = {key: value for key, value in gaps.items() if key != loader.EXTENSION}
    gaps[loader.EXTENSION]["parent_inventory"] = save(inventory.parent / "parent.json", parent)
    with pytest.raises(ValueError, match="DECLARED_TERMS_MISMATCH"):
        loader.load_cash_corrections(gaps, inventory)


def test_original_publication_must_match_original_url_day(correction_inputs):
    change_file(
        correction_inputs,
        "official_index",
        lambda index: index["announcements"][0].update(announcementTime=1303770600000),
    )
    with pytest.raises(ValueError, match="SIGNED_DATE"):
        loader.load_cash_corrections(*correction_inputs)


def test_exchange_cannot_drift_from_stock_scoped_index(correction_inputs):
    gaps, inventory = correction_inputs
    item(gaps)["security_id"] = "CN-A:SSE:300155"
    gaps["records"][0]["security_id"] = "CN-A:SSE:300155"
    parent = {key: value for key, value in gaps.items() if key != loader.EXTENSION}
    gaps[loader.EXTENSION]["parent_inventory"] = save(inventory.parent / "parent.json", parent)
    with pytest.raises(ValueError, match="ISSUER_QUERY"):
        loader.load_cash_corrections(gaps, inventory)


@pytest.mark.parametrize("field,value", [("record_date", "2011-05-04"), ("ex_date", "2011-05-07")])
def test_repinned_parent_dates_cannot_reassign_the_original_event(correction_inputs, field, value):
    gaps, inventory = correction_inputs
    item(gaps)[field] = value
    gaps["records"][0][field] = value
    parent = {key: value for key, value in gaps.items() if key != loader.EXTENSION}
    gaps[loader.EXTENSION]["parent_inventory"] = save(inventory.parent / "parent.json", parent)
    with pytest.raises(ValueError, match="ORIGINAL_EVENT_DATES"):
        loader.load_cash_corrections(gaps, inventory)


@pytest.mark.parametrize("change", ["missing", "conflicting"])
def test_original_event_dates_must_be_unique_and_explicit(correction_inputs, change):
    if change == "missing":
        change_file(
            correction_inputs,
            "original_pdf",
            lambda pages: [pages[0].replace("股权登记日:2011年5月5日。", "")],
        )
    else:
        change_file(
            correction_inputs,
            "original_pdf",
            lambda pages: [pages[0] + "股权登记日:2011年5月4日。"],
        )
    with pytest.raises(ValueError, match="ORIGINAL_EVENT_DATES"):
        loader.load_cash_corrections(*correction_inputs)


def test_each_bound_input_is_consumed_once(correction_inputs, monkeypatch):
    gaps, inventory = correction_inputs
    actual_reader = loader.verified_file_bytes
    paths = []

    def reader(path, digest):
        paths.append(path)
        return actual_reader(path, digest)

    monkeypatch.setattr(loader, "verified_file_bytes", reader)
    _, pins = loader.load_cash_corrections(gaps, inventory)
    assert set(paths) == set(pins)
    assert len(paths) == len(set(paths))
