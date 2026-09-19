from scripts.build_adjustment_gap_candidate_queue import candidates


def test_candidates_are_bounded_by_security_date_and_do_not_accept_events() -> None:
    routing = {
        "rows": [
            {
                "security_id": "CN-A:SZSE:000001",
                "symbol": "sz000001",
                "effective_date": "2014-06-12",
                "route": "NO_RETAINED_OFFICIAL_BONUS_DATE",
            },
            {
                "security_id": "CN-A:SSE:600000",
                "symbol": "sh600000",
                "effective_date": "2014-06-12",
                "route": "NO_RETAINED_OFFICIAL_BONUS_DATE",
            },
        ]
    }
    metadata = {
        "results": [
            {
                "documents": [
                    {
                        "issuer": "000001",
                        "published_on": "2014-06-10",
                        "title": "2013年度权益分派实施公告",
                        "url": "https://static.cninfo.com.cn/finalpage/a.PDF",
                    },
                    {
                        "issuer": "600000",
                        "published_on": "2014-01-01",
                        "title": "too old",
                        "url": "https://static.cninfo.com.cn/finalpage/b.PDF",
                    },
                ]
            }
        ]
    }
    queue, uncovered = candidates(routing, metadata)
    assert queue == [
        {
            "affected_factor_changes": ["FACTOR:CN-A:SZSE:000001:2014-06-12"],
            "issuer": "000001",
            "published_on": "2014-06-10",
            "queue_type": "OFFICIAL_ADJUSTMENT_GAP_CANDIDATE_PDF",
            "title": "2013年度权益分派实施公告",
            "url": "https://static.cninfo.com.cn/finalpage/a.PDF",
        }
    ]
    assert uncovered == [
        {
            "factor_change": "FACTOR:CN-A:SSE:600000:2014-06-12",
            "reason": "NO_RETAINED_CNINFO_IMPLEMENTATION_METADATA_WITHIN_60_DAYS",
        }
    ]
    assert (queue, uncovered) == candidates(
        {"rows": list(reversed(routing["rows"]))},
        {"results": list(reversed(metadata["results"]))},
    )
