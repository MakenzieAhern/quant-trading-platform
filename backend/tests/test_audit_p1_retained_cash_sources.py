from decimal import Decimal

from scripts.audit_p1_retained_cash_sources import (
    eligible,
    exchange_amount_matches,
    exchange_resolves_year_conflict,
)


def test_retained_cash_candidates_require_exact_event_and_official_issuer_source():
    requirements = [
        {
            "document_id": "cash-1",
            "priority": "P1",
            "required_document_types": [
                "FINAL_IMPLEMENTATION_NOTICE_WITH_GROSS_ORDINARY_A_SHARE_CASH"
            ],
            "known_urls": [],
            "affected_events": ["CASH:600001:2022-06-01:2022-06-02"],
        }
    ]
    cash = [
        {
            "event": {
                "security_id": {"value": "SSE:600001"},
                "record_date": "2022-06-01",
                "ex_date": "2022-06-02",
                "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_DATED",
            }
        }
    ]
    assert eligible(requirements, set(), cash) == (requirements, cash)
    assert eligible(requirements, {"cash-1"}, cash) == ([], [])
    assert eligible(requirements, set(), cash + cash) == ([], [])
    cash[0]["event"]["source_provider"] = "UNVERIFIED_VENDOR"
    assert eligible(requirements, set(), cash) == ([], [])
    assert exchange_amount_matches(Decimal("0.100022"), {Decimal("0.1000")})
    assert not exchange_amount_matches(Decimal("0.1006"), {Decimal("0.1000")})


def test_year_conflict_needs_impossible_issuer_year_and_exact_exchange_month_day():
    row = {"record_date": "2015-06-25", "ex_date": "2015-06-26"}
    assert exchange_resolves_year_conflict(row, ["2015-06-25"], ["2014-06-26"], "2015-06-18")
    assert not exchange_resolves_year_conflict(row, ["2015-06-25"], ["2014-06-27"], "2015-06-18")
    assert not exchange_resolves_year_conflict(row, ["2015-06-25"], ["2014-06-26"], "2014-06-01")
    assert not exchange_resolves_year_conflict(
        row, ["2015-06-25", "2014-06-25"], ["2014-06-26"], "2015-06-18"
    )
