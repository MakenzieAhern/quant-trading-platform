import json

from app.data.catalog.checksums import sha256_file
from scripts.audit_p1_cash_corrections import (
    bonus_removed_without_cash_change,
    close_supplements,
    corrected_cash_amount,
    corrected_entitlement_year,
    corrected_payment_and_record_date,
    corrected_reference_price_only,
    corrected_repurchase_share_count_only,
    unchanged_except_payment_date,
    unchanged_except_share_count,
)
from scripts.triage_p1_remaining_distribution_docs import diagnose


def test_share_count_only_supplement_closes_existing_cash_fact(tmp_path):
    pages = [
        "证券代码:002026\n关于2024年前三季度权益分派实施公告的补充公告\n"
        "原披露内容:以445,567,668股为基数,向全体股东每10股派0.60元人民币现金(含税)。\n"
        "补充后内容:以445,657,639股为基数,向全体股东每10股派0.60元人民币现金(含税)。\n"
        "除上述补充的内容外,原公告其他内容不变。"
    ]
    original, supplement = tmp_path / "original.pdf", tmp_path / "supplement.pdf"
    original.write_bytes(b"original official PDF")
    supplement.write_bytes(b"supplement official PDF")
    original_sha, supplement_sha = sha256_file(original), sha256_file(supplement)
    cache = tmp_path / "batch-v1/text" / f"{supplement_sha}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(json.dumps({"source_sha256": supplement_sha, "pages": pages}))
    original_url = "https://static.cninfo.com.cn/finalpage/2024-12-06/original.PDF"
    supplement_url = "https://static.cninfo.com.cn/finalpage/2024-12-07/supplement.PDF"
    title = "2024年前三季度权益分派实施公告"
    requirement = {
        "document_id": "supplement",
        "issuer": "002026",
        "published_on": "2024-12-07",
        "title": "关于" + title + "的补充公告",
        "affected_events": ["cash-fact"],
    }
    triage = {
        "document_id": "supplement",
        "url": supplement_url,
        "source_sha256": supplement_sha,
        "text_cache_sha256": sha256_file(cache),
        **diagnose(pages, "002026"),
    }
    cash = [
        {
            "event_checksum": "accepted",
            "event": {
                "security_id": {"value": "CN-A:SZSE:002026"},
                "source_url": original_url,
                "source_document_sha256": original_sha,
                "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
                "announcement_date": "2024-12-06",
                "record_date": "2024-12-13",
                "ex_date": "2024-12-16",
                "cash_per_share": "0.06",
            },
        }
    ]
    sources = [
        {
            "url": url,
            "source_path": filename,
            "source_sha256": sha,
            "retrieval_status": "PASS",
            "issuer": "002026",
            "title": source_title,
            "published_on": date,
        }
        for url, filename, sha, source_title, date in (
            (original_url, "original.pdf", original_sha, title, "2024-12-06"),
            (supplement_url, "supplement.pdf", supplement_sha, requirement["title"], "2024-12-07"),
        )
    ]
    closed = close_supplements([triage], [requirement], cash, sources, tmp_path, set())
    assert len(closed) == 1
    assert closed[0]["accepted_event_checksum"] == "accepted"
    assert closed[0]["cash_per_share"] == "0.06"
    assert not close_supplements([triage], [requirement], cash, sources, tmp_path, {"supplement"})
    changed_cash = pages[0].replace("0.60元人民币现金", "0.70元人民币现金", 1)
    assert unchanged_except_share_count([changed_cash]) is None


def test_only_payment_date_may_change():
    pages = [
        "更正前:五、权益分派方法 现金红利将于2024年5月30日通过股东托管证券公司划入账户。"
        "更正后:五、权益分派方法 现金红利将于2024年6月3日通过股东托管证券公司划入账户。"
        "除上述更正内容外,原公告其他内容不变。"
    ]
    assert unchanged_except_payment_date(pages) == {
        "original_payment_date": "2024-05-30",
        "corrected_payment_date": "2024-06-03",
    }
    changed_amount = pages[0].replace("更正后:", "更正后:每10股派1元现金;")
    assert unchanged_except_payment_date([changed_amount]) is None


def test_official_bonus_removal_cannot_change_cash_terms():
    pages = [
        "更正前:向全体股东每10股派4元人民币现金(含税),"
        "同时,以资本公积金向全体股东每10股转增2股。"
        "更正后:向全体股东每10股派4元人民币现金(含税)。"
        "除上述更正内容外,原公告其他内容不变。"
    ]
    assert bonus_removed_without_cash_change(pages) == {"removed_bonus_ratio": "0.2"}
    changed_cash = pages[0].replace("更正后:向全体股东每10股派4元", "更正后:向全体股东每10股派5元")
    assert bonus_removed_without_cash_change([changed_cash]) is None


def test_corrected_entitlement_year_requires_exact_before_after_match():
    page = (
        "补充更正前:三、股权登记日与除权除息日股权登记日为:2022年5月15日;"
        "除权除息日为:2022年5月16日。补充更正后:三、股权登记日与除权除息日"
        "股权登记日为:2023年5月15日;除权除息日为:2023年5月16日。"
        "除上述补充更正内容外,公告其他内容不变。"
    )
    assert corrected_entitlement_year([page]) == {
        "original_record_date": "2022-05-15",
        "corrected_record_date": "2023-05-15",
        "original_ex_date": "2022-05-16",
        "corrected_ex_date": "2023-05-16",
    }
    assert corrected_entitlement_year([page.replace("2023年5月16日", "2023年5月17日")]) is None


def test_corrected_cash_amount_requires_only_amount_change():
    page = (
        "原披露内容:二、分配方案每10股派发现金红利0.0298元(含税)。"
        "现更正为:二、分配方案每10股派发现金红利0.3元(含税)。"
        "除上述更正外,其他内容不变。"
    )
    assert corrected_cash_amount([page]) == {
        "original_cash_per_share": "0.00298",
        "corrected_cash_per_share": "0.03",
    }
    assert corrected_cash_amount([page.replace("现更正为:二、", "现更正为:三、")]) is None


def test_payment_and_record_metadata_correction_requires_only_swapped_dates():
    page = (
        "更正前:现金红利将于2024年5月13日划入账户。"
        "申请日至股权登记日:2024年5月14日,责任由公司承担。"
        "更正后:现金红利将于2024年5月14日划入账户。"
        "申请日至股权登记日:2024年5月13日,责任由公司承担。"
        "除上述事项外,原公告其他内容不变。"
    )
    assert corrected_payment_and_record_date([page]) == {
        "original_payment_date": "2024-05-13",
        "corrected_payment_date": "2024-05-14",
        "original_record_date": "2024-05-14",
        "corrected_record_date": "2024-05-13",
    }
    assert (
        corrected_payment_and_record_date([page.replace("更正后:现金", "更正后:每股增派现金")])
        is None
    )


def test_reference_price_correction_does_not_change_gross_cash():
    page = (
        "现就公告中除权(息)参考价格内容进行更正。"
        "更正前:分派的现金红利=(参与分配的股本总数\u00d7实际分派的每股现金红利)"
        "÷总股本=600,668,390\u00d70.5÷601,065,290。"
        "更正后:虚拟分派的现金红利=(参与分配的股本总数\u00d7实际分派的每股现金红利)"
        "÷总股本=600,668,390\u00d70.5÷601,065,290;前收盘价格调整。"
        "除上述更正内容外,原公告其他内容不变。"
    )
    assert corrected_reference_price_only([page]) == {"gross_cash_per_share_unchanged": "0.5"}
    assert (
        corrected_reference_price_only([page.replace("390\u00d70.5÷", "390\u00d70.6÷", 1)]) is None
    )


def test_repurchase_count_correction_preserves_per_share_cash():
    page = (
        "一、关于权益分派实施公告的更正"
        "更正前:公司回购股份余额为42,470,626股,实际参与分配的股份为"
        "2,014,365,650股,共计派发现金红利60,430,969.50元。"
        "更正后:公司回购股份余额为43,470,626股,实际参与分配的股份为"
        "2,013,365,650股,共计派发现金红利60,400,969.50元。"
        "除上述更正外,其他内容保持不变。二、关于回购价格的更正"
    )
    assert corrected_repurchase_share_count_only([page]) == {
        "corrected_repurchased_shares": 43_470_626,
        "corrected_participating_shares": 2_013_365_650,
        "corrected_total_cash": "60400969.50",
        "gross_cash_per_share_unchanged": "0.03",
    }
    assert (
        corrected_repurchase_share_count_only([page.replace("60,400,969.50", "60,500,969.50")])
        is None
    )
