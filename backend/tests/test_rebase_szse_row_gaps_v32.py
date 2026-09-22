from scripts.rebase_szse_row_gaps_v32 import close_report


def test_close_report_reapplies_intervals_without_changing_residual_scope() -> None:
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V1",
        "missing_rows": 3,
        "source_collection_sha256": "source",
        "suspension_events_sha256": "events",
        "classification_counts": {
            "DATED_SOURCE_HALT_INTERVAL": 0,
            "NO_MATCHING_HALT_SOURCE": 2,
            "UNKNOWN_RESUMPTION_NOT_CLOSED": 1,
        },
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000001",
                "date": "2011-01-03",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000002",
                "date": "2011-01-03",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000003",
                "date": "2011-01-03",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            },
        ],
        "raw_authority_promoted": False,
        "manifest_sha256": "base-manifest",
    }
    prior = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_CORRECTED_V5",
        "missing_rows": 3,
        "source_collection_sha256": "source",
        "classification_counts": {
            "NO_MATCHING_HALT_SOURCE": 1,
            "OFFICIAL_2010PLUS_LISTING_SUSPENSION": 1,
            "UNKNOWN_RESUMPTION_NOT_CLOSED": 1,
        },
        "official_intervals": [
            {
                "security_id": "CN-A:SZSE:000001",
                "suspended_from": "2011-01-01",
                "first_trading_day": "2011-01-04",
                "classification": "OFFICIAL_2010PLUS_LISTING_SUSPENSION",
            }
        ],
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000002",
                "date": "2011-01-03",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            },
            {
                "security_id": "CN-A:SZSE:000003",
                "date": "2011-01-03",
                "reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            },
        ],
        "raw_authority_promoted": False,
        "manifest_sha256": "prior-manifest",
    }

    report = close_report(base, prior, "base", "prior")

    assert len(report["unresolved_rows"]) == 2
    assert report["classification_counts"]["OFFICIAL_2010PLUS_LISTING_SUSPENSION"] == 1
    assert report["residual_scope_changed"] is False
    assert report["residual_reason_changes"] == [
        {
            "security_id": "CN-A:SZSE:000002",
            "date": "2011-01-03",
            "prior_reason": "UNKNOWN_RESUMPTION_NOT_CLOSED",
            "v32_reason": "NO_MATCHING_HALT_SOURCE",
        }
    ]
