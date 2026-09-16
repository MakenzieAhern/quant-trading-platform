from datetime import date
from decimal import Decimal


def test_candidate_window_and_exact_cross_source_classification():
    from scripts.audit_p1_cash_public_substitutions import candidates, classify

    rows = [
        {"issuer": "000006", "published_on": "2012-07-04", "url": "official"},
        {"issuer": "000006", "published_on": "2012-06-01", "url": "too-old"},
        {"issuer": "000007", "published_on": "2012-07-04", "url": "wrong-issuer"},
    ]
    assert candidates(rows, "000006", "2012-07-10") == [rows[0]]
    pages = [
        "股票代码:000006\n二、利润分配方案\n每10股送3股派发现金股利0.4元(含税)\n"
        "股权登记日:2012年7月10日\n除权(除息)日:2012年7月11日"
    ]
    assert (
        classify(pages, "000006", date(2012, 7, 10).isoformat(), "2012-07-11", {Decimal("0.04")})[
            "classification"
        ]
        == "EXACTLY_CORROBORATED"
    )
    assert (
        classify(pages, "000006", "2012-07-10", "2012-07-12", {Decimal("0.04")})["classification"]
        == "OFFICIAL_SOURCE_CONFLICT"
    )
    invalid_date = pages[0].replace("2012年7月11日", "2012年2月31日")
    invalid = classify([invalid_date], "000006", "2012-07-10", "2012-07-11", {Decimal("0.04")})
    assert invalid["classification"] == "TEMPORAL_BOUNDARY_AMBIGUITY"
    assert invalid["parsed_ex_dates"] == []
    assert invalid["date_parser_error"] is None
