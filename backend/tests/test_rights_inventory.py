from copy import deepcopy

import pytest

from scripts.inventory_full_rights import inventory, normalize


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
    assert result["classification"] == "UNRESOLVED"
    assert result["safety_classification"] == "RIGHTS_EVENT_UNSUPPORTED_VARIANT"
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
    assert normalize(row(), source(), review)["classification"] == "UNRESOLVED"
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
