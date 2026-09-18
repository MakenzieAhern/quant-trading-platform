from scripts.audit_p1_restructuring_no_entitlement import classify


def test_zero_original_holder_distribution_is_narrow_source_closure():
    item = {
        "document_id": "doc",
        "affected_events": ["event"],
        "issuer": "002122",
        "title": "关于重整计划资本公积转增股本实施的公告",
        "published_on": "2022-12-16",
        "url": "https://static.cninfo.com.cn/example.PDF",
    }
    triage = {
        "document_id": "doc",
        "candidate_class": "NEITHER",
        "cash_candidate_per_share": None,
        "bonus_candidate_per_share": None,
        "preferred_instrument_marker": False,
        "source_sha256": "source",
        "text_cache_sha256": "text",
    }
    text = "本次转增股票不向原股东分配,不涉及现金红利。"
    assert len(classify([item], [triage], {"doc": text})) == 1
    assert classify([item], [triage], {"doc": text.replace("不向", "向")}) == []
    assert (
        classify([item], [triage], {"doc": text.replace("不涉及现金红利", "现金红利另行公告")})
        == []
    )
