from copy import deepcopy

import pytest

from scripts.inventory_full_rights import inventory, normalize
from scripts.reconcile_official_rights_batch import effective_date, reconcile


def source():
    return dict(
        url="https://example.test/rights", sha256="a" * 64, retrieved_at_utc="2026-09-13T00:00:00Z"
    )


def row(code="600036.SH", identity="one"):
    return dict(
        FINANCE_CODE=identity,
        SECUCODE=code,
        FIRST_NOTICE_DATE="2010-03-02",
        EQUITY_RECORD_DATE="2010-03-04",
        PAY_START_DATE="2010-03-05",
        PAY_END_DATE="2010-03-11",
        EX_DIVIDEND_DATE="2010-03-15",
        LISTING_DATE="2010-03-19",
        ISSUE_PRICE="8.85",
        PLACING_RATIO="1.3",
        TOTAL_SHARES_BEFORE=19119490016,
    )


def test_source_total_capital_never_becomes_eligible_a_share_basis():
    result = normalize(row(), source())
    assert result["event"]["eligible_share_basis"] is None
    assert result["event"]["share_ratio"] == "0.13"
    assert result["event"]["subscription_price"] == "8.85"
    assert result["classification"] == "EVENT_IDENTITY_UNRESOLVED"
    assert result["safety_classification"] == "EVENT_IDENTITY_UNRESOLVED"
    assert result["source_total_capital_not_eligible_basis"] == 19119490016
    assert result["point_in_time_admission"] == "NOT_ADMITTED_FULL_AUTHORITY_PENDING"


def test_contradictory_source_announcement_is_preserved_not_backdated():
    candidate = row("600066.SH")
    candidate["FIRST_NOTICE_DATE"] = "2012-02-23"
    candidate["EX_DIVIDEND_DATE"] = "2012-02-21"
    result = normalize(candidate, source())
    assert result["event"]["announcement_date"] is None
    assert result["source_reported_announcement_date"] == "2012-02-23"
    assert result["source_issues"] == ["SOURCE_ANNOUNCEMENT_AFTER_EX_DATE"]


def test_official_sample_terms_are_compared_not_blindly_overlaid():
    review = dict(
        checks=dict(subscription_price="8.85", ratio="0.13", record_date="2010-03-04"),
        verified_event_fields={},
    )
    assert normalize(row(), source(), review)["classification"] == "EVENT_IDENTITY_UNRESOLVED"
    review["checks"]["subscription_price"] = "8.86"
    with pytest.raises(ValueError, match="OFFICIAL_RIGHTS_TERM_MISMATCH"):
        normalize(row(), source(), review)


def test_inventory_pagination_replay_duplicates_and_prior_year_lifecycle_overlap():
    earlier = row("000960.SZ", "two")
    earlier.update(
        EQUITY_RECORD_DATE="2009-12-21",
        PAY_START_DATE="2009-12-22",
        PAY_END_DATE="2009-12-28",
        EX_DIVIDEND_DATE="2009-12-30",
        FIRST_NOTICE_DATE="2009-12-17",
        LISTING_DATE="2010-01-05",
    )
    pages = [
        (dict(success=True, result=dict(count=2, pages=2, data=[r])), source())
        for r in (row(), earlier)
    ]
    result = inventory(pages, {})
    assert result["rights_events_total"] == 2
    assert result == inventory(list(reversed(pages)), {})
    with pytest.raises(ValueError, match="pagination"):
        inventory(pages[:1], {})
    duplicate = deepcopy(pages)
    duplicate[1][0]["result"]["data"][0] = row()
    with pytest.raises(ValueError, match="pagination"):
        inventory(duplicate, {})


def test_official_result_date_structure_and_record_must_match_before_promotion():
    original = normalize(row(), source())
    notice = dict(
        issuer="600036",
        title="A股配股发行结果公告",
        published_on="2010-03-16",
        url="https://static.cninfo.com.cn/finalpage/2010-03-16/result.PDF",
        source_sha256="b" * 64,
        retrieved_at_utc="2026-09-13T00:00:00Z",
    )
    issuance = {**notice, "title": "A股配股发行公告", "published_on": "2010-03-02"}
    text = (
        "证券代码600036。股权登记日2010年3月4日。按每10股配1.3股。认购缴款工作已于2010年3月11日结束。"
        "本公告见报当日(2010年3月15日)即为A股发行成功的除权基准日。"
    )
    assert effective_date(text, notice["published_on"])[0] == "2010-03-15"
    documents = [(notice, text), (issuance, "股权登记日2010年3月4日")]
    result = reconcile([original], documents)[0]
    assert not result["issues"]
    assert result["event"]["ex_date"] == "2010-03-15"
    assert result["event"]["subscription_price"] is None  # Unverified vendor term retained below.
    assert result["prior_oracle_row"]["event"]["subscription_price"] == "8.85"
    assert result == reconcile([original], list(reversed(documents)))[0]
    wrong_record = [(notice, text.replace("3月4日", "3月5日")), documents[1]]
    assert reconcile([original], wrong_record)[0]["issues"]
    assert reconcile([original], [(notice, text)])[0]["issues"]
    assert reconcile(
        [original], [({**notice, "title": "H股配股发行结果公告"}, text), documents[1]]
    )[0]["issues"]
