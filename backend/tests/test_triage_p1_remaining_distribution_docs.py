from scripts.triage_p1_remaining_distribution_docs import diagnose


def test_bonus_only_document_is_a_candidate_not_cash_acceptance():
    result = diagnose(["证券代码:300747\n本次实施方案为每10股转增3股,不派发现金红利。"], "300747")
    assert result["candidate_class"] == "BONUS_ONLY"
    assert result["bonus_candidate_per_share"] == "0.3"
    assert result["cash_candidate_per_share"] is None


def test_differentiated_cash_remains_a_corroboration_candidate():
    pages = [
        "证券代码:600157 每股分配比例 A股每股现金红利0.00555元(含税) 相关日期 差异化分红送转:是"
    ]
    result = diagnose(pages, "600157", "2023年年度权益分派实施公告")
    assert result["cash_candidate_per_share"] is None
    assert result["differentiated_cash_candidate_per_share"] == "0.00555"
    assert result["candidate_class"] == "NEITHER"
