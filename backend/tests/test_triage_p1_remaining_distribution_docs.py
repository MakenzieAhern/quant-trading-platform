from scripts.triage_p1_remaining_distribution_docs import diagnose


def test_bonus_only_document_is_a_candidate_not_cash_acceptance():
    result = diagnose(["证券代码:300747\n本次实施方案为每10股转增3股,不派发现金红利。"], "300747")
    assert result["candidate_class"] == "BONUS_ONLY"
    assert result["bonus_candidate_per_share"] == "0.3"
    assert result["cash_candidate_per_share"] is None
