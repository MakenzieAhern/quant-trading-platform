from decimal import Decimal

from scripts.link_distribution_notices import notice_dates, star_cash_dates
from scripts.reconcile_distribution_cash import differentiated_cash
from scripts.reconcile_p1_differentiated_cash import decision, official_correction


def test_differentiated_cash_never_overrides_conflicting_accepted_event():
    assert decision([], "2024-08-23", Decimal("0.00555")) == "NEW_OFFICIAL_ISSUER_EVENT"
    peer = {"event": {"record_date": "2024-08-23", "cash_per_share": "0.00555"}}
    assert decision([peer], "2024-08-23", Decimal("0.00555")) == "EXACT_ACCEPTED_EVENT"
    assert decision([peer], "2024-08-23", Decimal("0.00551")) == "ACCEPTED_EVENT_CONFLICT"
    assert decision([peer], "2024-08-24", Decimal("0.00555")) == "ACCEPTED_EVENT_CONFLICT"


def test_actual_holder_cash_is_not_diluted_ex_price_reference():
    pages = [
        "证券代码:600157\n每股分配比例 A股每股现金红利0.00555元(含税)\n"
        "相关日期\n差异化分红送转:是\n"
        "每股现金红利=(参与分配股份数*0.00555)÷总股本=0.00551元/股。"
    ]
    assert differentiated_cash(pages, "600157", "2023年年度权益分派实施公告") == Decimal("0.00555")


def test_unlabeled_star_cash_table_needs_one_valid_date_chain():
    table = "股权登记日 除权(息)日 现金红利发放日\n2024/6/13 2024/6/14 2024/6/14"
    assert star_cash_dates([table, table]) == (["2024-06-13"], ["2024-06-14"])
    four = (
        "股权登记日 除权(息)日 新增无限售条件流通股份上市日 现金红利发放日\n"
        "2025/6/4 2025/6/5 2025/6/5 2025/6/5"
    )
    assert star_cash_dates([four, four]) == (["2025-06-04"], ["2025-06-05"])
    assert notice_dates([table]) == (["2024-06-13"], ["2024-06-14"])
    assert notice_dates([four]) == (["2025-06-04"], ["2025-06-05"])
    assert notice_dates([table, four]) == ([], [])
    assert star_cash_dates(["股份类别" + table]) == ([], [])
    assert star_cash_dates(
        [table, "股权登记日 除权(息)日 现金红利发放日\n2024/7/1 2024/7/2 2024/7/2"]
    ) == ([], [])


def test_only_pre_record_official_issuer_correction_supersedes_old_amount():
    corrected = {
        "title": "公司权益分派实施公告(更正版)",
        "issuer": "688320",
        "published_on": "2024-06-08",
        "source_sha256": "b" * 64,
        "retrieval_status": "PASS",
    }
    peer = {
        "event": {
            "record_date": "2024-06-13",
            "announcement_date": "2024-06-08",
            "source_document_sha256": "b" * 64,
            "source_document": corrected["title"],
            "source_provider": "OFFICIAL_ISSUER_CNINFO_DIFFERENTIATED_PUBLIC_A",
        }
    }
    original = {"issuer": "688320", "published_on": "2024-06-07"}
    assert official_correction(peer, original, corrected)
    assert not official_correction(peer, original, {**corrected, "title": "未更正公告"})
    assert not official_correction(peer, original, {**corrected, "published_on": "2024-06-14"})
