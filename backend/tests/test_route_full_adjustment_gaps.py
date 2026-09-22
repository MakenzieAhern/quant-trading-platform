from scripts.route_full_adjustment_gaps import route


def test_routes_bonus_oracle_without_promoting_authority() -> None:
    adjustment = {
        "requested_coverage": ["2010-01-01", "2025-12-31"],
        "factor_changes": [
            {
                "security_id": "CN-A:SZSE:000001",
                "symbol": "sz000001",
                "effective_date": "2013-06-20",
                "status": "NO_SUPPORTED_EVENT_DATE",
                "supported_events": [],
            },
            {
                "security_id": "CN-A:SSE:600000",
                "symbol": "sh600000",
                "effective_date": "2014-01-01",
                "status": "NO_SUPPORTED_EVENT_DATE",
                "supported_events": [],
            },
        ],
        "intervals": [
            {
                "security_id": "CN-A:SZSE:000001",
                "in_interval_variants": {
                    "a": {
                        "baseline": ["2012-01-01", "1"],
                        "period_rows": [["2013-06-20", "2"]],
                    }
                },
            },
            {
                "security_id": "CN-A:SSE:600000",
                "in_interval_variants": {
                    "b": {
                        "baseline": ["2013-01-01", "1"],
                        "period_rows": [["2014-01-01", "2"]],
                    }
                },
            },
        ],
    }
    oracle_row = {
        "symbol": "000001",
        "ex_date": "2013-06-20",
        "ratio_consistency": "SINGLE_DISPLAYED_RATIO",
        "new_share_tradability": "NOT_EVIDENCED",
        "evidence_sha256": "a" * 64,
        "evidence": [
            {
                "exchange": "SZSE",
                "ratio": "1.000",
                "source_evidence": {
                    "source_sha256": "b" * 64,
                    "source_url": "https://investor.szse.cn/official.html",
                    "raw_cells": [""] * 5 + ["0.000"] + [""] * 6 + ["5.000", "10.000"],
                },
            }
        ],
    }
    cash_ledger = {
        "coverage": ["2010-01-01", "2025-12-31"],
        "unresolved_official_cash_events": 0,
        "input_order_reproducibility": "PASS",
        "checksum_repeatability": "PASS",
        "events": [],
    }
    report = route(adjustment, {"rows": [oracle_row]}, cash_ledger)
    assert report["route_counts"] == {
        "NO_RETAINED_OFFICIAL_BONUS_DATE": 1,
        "RETAINED_OFFICIAL_BONUS_SOURCE_DATE": 1,
    }
    assert report["bonus_ratio_classes"] == {"INTEGER": 1}
    assert report["displayed_price_ratio_statuses"] == {"DISPLAYED_PRICE_RATIO_BOUNDS_PASS": 1}
    assert report["zero_cash_bonus_ratio_statuses"] == {"ZERO_CASH_BONUS_RATIO_BOUNDS_PASS": 1}
    assert report["factor_economic_alignment_statuses"] == {
        "OFFICIAL_BONUS_FACTOR_ALIGNMENT_PASS": 1
    }
    assert report["adjustment_authority_promoted"] is False
    assert report == route(
        dict(
            adjustment,
            factor_changes=list(reversed(adjustment["factor_changes"])),
            intervals=list(reversed(adjustment["intervals"])),
        ),
        {"rows": [oracle_row]},
        cash_ledger,
    )
