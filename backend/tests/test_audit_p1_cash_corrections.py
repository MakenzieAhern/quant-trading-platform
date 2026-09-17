import json

from app.data.catalog.checksums import sha256_file
from scripts.audit_p1_cash_corrections import (
    bonus_removed_without_cash_change,
    close_supplements,
    corrected_cash_amount,
    corrected_entitlement_year,
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
