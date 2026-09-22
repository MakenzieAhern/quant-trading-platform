import pytest

from scripts.reconcile_retained_bonus_supplements import select_sources


def test_targeted_bonus_recovery_requires_unique_near_record_official_receipts():
    rows = [
        {
            "symbol": symbol,
            "record_date": record,
            "ex_date": ex,
            "status": "UNRESOLVED_TERMS_OR_LIFECYCLE",
            "evidence": [],
            "unresolved_documents": [],
        }
        for symbol, record, ex in (
            ("603315", "2016-06-06", "2016-06-07"),
            ("603889", "2016-04-18", "2016-04-19"),
        )
    ]
    docs = [
        {
            "issuer": symbol,
            "published_on": published,
            "retrieval_status": "PASS",
            "url": f"https://static.cninfo.com.cn/finalpage/{symbol}.PDF",
            "source_sha256": symbol,
        }
        for symbol, published in (("603315", "2016-06-01"), ("603889", "2016-04-12"))
    ]
    assert len(select_sources(rows, docs)) == 2
    assert len(select_sources(rows, [*docs, {**docs[0], "published_on": "2016-04-15"}])) == 2
    with pytest.raises(ValueError, match="BONUS_OFFICIAL_SOURCE_NOT_UNIQUE"):
        select_sources(rows, [*docs, dict(docs[0])])
