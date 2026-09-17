from scripts.audit_p1_derivative_notices import classify, completed_dates


def test_derivative_requires_unique_existing_exact_issuer_cash():
    requirement = {
        "document_id": "a",
        "affected_events": ["CNINFO:a"],
        "issuer": "000001",
        "title": "关于停止转股的提示性公告",
        "published_on": "2024-06-01",
    }
    triage = {
        "document_id": "a",
        "candidate_class": "CASH_ONLY",
        "cash_candidate_per_share": "0.1",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "url": "derivative",
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    accepted = {
        "event_checksum": "event",
        "event": {
            "security_id": {"value": "CN-A:SZSE:000001"},
            "ex_date": "2024-06-05",
            "cash_per_share": "0.100",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_url": "https://static.cninfo.com.cn/finalpage/primary.PDF",
        },
    }
    assert len(classify([requirement], [triage], set(), [accepted])) == 1
    assert (
        len(
            classify(
                [dict(requirement, title="关于实施分红后调整回购股份价格上限的公告")],
                [triage],
                set(),
                [accepted],
            )
        )
        == 1
    )
    assert (
        len(
            classify(
                [dict(requirement, title="关于转股连续停牌的提示性公告")],
                [triage],
                set(),
                [accepted],
            )
        )
        == 1
    )
    assert classify([requirement], [triage], set(), [accepted, accepted]) == []
    assert (
        classify(
            [requirement],
            [triage],
            set(),
            [dict(accepted, event=dict(accepted["event"], cash_per_share="0.2"))],
        )
        == []
    )


def test_historical_option_adjustment_requires_matching_dividend_year():
    requirement = {
        "document_id": "a",
        "affected_events": ["CNINFO:a"],
        "issuer": "600180",
        "title": "关于根据2022年度利润分配实施方案调整公司2023年股票期权激励计划行权价格的公告",
        "published_on": "2024-04-26",
    }
    triage = {
        "document_id": "a",
        "candidate_class": "CASH_ONLY",
        "cash_candidate_per_share": "0.133",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "url": "derivative",
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    accepted = {
        "event_checksum": "event",
        "event": {
            "security_id": {"value": "CN-A:SSE:600180"},
            "ex_date": "2023-06-07",
            "cash_per_share": "0.133",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_url": "https://static.cninfo.com.cn/finalpage/primary.PDF",
            "source_document": "瑞茂通2022年年度权益分派实施公告",
        },
    }
    assert len(classify([requirement], [triage], set(), [accepted])) == 1
    assert (
        classify(
            [requirement],
            [triage],
            set(),
            [
                dict(
                    accepted,
                    event=dict(accepted["event"], source_document="2021年年度权益分派实施公告"),
                )
            ],
        )
        == []
    )


def test_derivative_late_reference_requires_exact_completed_date_and_record():
    requirement = {
        "document_id": "late",
        "affected_events": ["CNINFO:late"],
        "issuer": "600339",
        "title": "关于实施利润分配后调整向特定对象发行A股股票价格的公告",
        "published_on": "2025-10-18",
    }
    triage = {
        "document_id": "late",
        "candidate_class": "CASH_ONLY",
        "cash_candidate_per_share": "0.013",
        "record_dates": ["2025-09-29"],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "url": "derivative",
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    accepted = {
        "event_checksum": "accepted",
        "event": {
            "security_id": {"value": "CN-A:SSE:600339"},
            "record_date": "2025-09-29",
            "ex_date": "2025-09-30",
            "cash_per_share": "0.0130",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_url": "https://static.cninfo.com.cn/finalpage/primary.PDF",
        },
    }
    assert completed_dates(["本次权益分配于2025 年 9 月30 日实施完毕。"]) == {"2025-09-30"}
    assert classify([requirement], [triage], set(), [accepted]) == []
    assert len(classify([requirement], [triage], set(), [accepted], {"late": {"2025-09-30"}})) == 1
    triage["record_dates"] = ["2025-09-28"]
    assert classify([requirement], [triage], set(), [accepted], {"late": {"2025-09-30"}}) == []
