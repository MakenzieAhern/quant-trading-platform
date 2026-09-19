from scripts.audit_adjustment_gap_candidate_terms import classify_document, pages_for


def test_exact_official_terms_remain_candidates_only() -> None:
    document = {
        "issuer": "000001",
        "title": "2013年度权益分派实施公告",
        "url": "https://static.cninfo.com.cn/finalpage/one.PDF",
        "source_sha256": "a" * 64,
        "affected_factor_changes": ["FACTOR:CN-A:SZSE:000001:2014-06-12"],
    }
    pages = [
        "证券代码:000001 证券简称:测试\n"
        "本公司及董事会全体成员保证公告内容真实、准确和完整,没有虚假记载、误导性陈述或者重大遗漏。\n"
        "本公司2013年度权益分派方案为:向全体股东每10股派1.00元人民币现金(含税),"
        "同时每10股转增2股。\n股权登记日:2014年6月11日。除权除息日:2014年6月12日。"
    ]
    result = classify_document(document, pages)
    assert result["status"] == "EXACT_DATE_OFFICIAL_TERMS_CANDIDATE"
    assert result["cash_per_share"] == "0.10"
    assert result["bonus_share_ratio"] == "0.2"
    assert result["matched_factor_changes"] == document["affected_factor_changes"]


def test_unparseable_retained_bytes_fail_closed(tmp_path) -> None:
    source = tmp_path / "bad.pdf"
    source.write_bytes(b"not a pdf")
    pages, receipt = pages_for(
        tmp_path,
        {"source_sha256": "a" * 64, "source_path": source.name},
        {},
    )
    assert pages is None
    assert receipt["text_source"] == "SOURCE_BYTES_NOT_PARSEABLE_AS_PDF"
