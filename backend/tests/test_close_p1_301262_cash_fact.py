import pytest

from scripts.close_p1_301262_cash_fact import (
    DOCUMENT_ID,
    EVENT,
    FACTBOOK_FILE,
    FACTBOOK_SHA,
    FACTBOOK_URL,
    NOTICE_SHA,
    NOTICE_URL,
    close,
)


def test_301262_typo_closure_requires_both_official_sources():
    requirements = {
        "documents": [{"document_id": DOCUMENT_ID, "priority": "P1", "affected_events": [EVENT]}]
    }
    queue = [{"document_id": DOCUMENT_ID, "affected_events": [EVENT]}]
    notice = {
        "url": NOTICE_URL,
        "source_sha256": NOTICE_SHA,
        "retrieval_status": "PASS",
        "published_on": "2023-10-24",
        "retrieved_at_utc": "2026-09-15T00:00:00Z",
    }
    factbook = {
        "raw_snapshot_filename": FACTBOOK_FILE,
        "sha256": FACTBOOK_SHA,
        "source_url": FACTBOOK_URL,
        "http_status": 200,
        "retrieved_at": "2026-09-13T00:00:00Z",
    }
    notice_text = (
        "证券代码:301262 每10股派发现金红利8.500000元 "
        "本次权益分派股权登记日为:2023年10月30日 "
        "除权除息日为:2023年10年31日 现金红利将于2023年10月31日"
    )
    factbook_text = "301262 海看股份 0 354450000.00 10/31/2023 10派8.5元(含税)"
    result = close(
        requirements,
        queue,
        {"documents": [notice]},
        {"snapshots": [factbook]},
        notice_text,
        factbook_text,
    )
    assert result["closed_facts"] == 1
    assert result["closed"][0]["ex_date"] == "2023-10-31"
    assert not result["future_source_used_as_strategy_signal"]
    with pytest.raises(ValueError, match="FACTBOOK_TERMS_CHANGED"):
        close(
            requirements,
            queue,
            {"documents": [notice]},
            {"snapshots": [factbook]},
            notice_text,
            factbook_text.replace("10/31/2023", "10/30/2023"),
        )
