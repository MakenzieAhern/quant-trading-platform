"""Proposal-only notices must never substitute for final cash facts."""

from scripts.audit_p1_nonfinal_proposals import a_share_schedule, classify


def test_only_undated_nonfinal_proposal_is_out_of_scope():
    requirement = {
        "document_id": "a",
        "affected_events": ["CNINFO:1"],
        "issuer": "000001",
        "published_on": "2024-08-29",
        "title": "关于收到董事长提议实施中期分红的公告",
        "url": "official-url",
    }
    triage = {
        "document_id": "a",
        "candidate_class": "NEITHER",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    assert len(classify([requirement], [triage], set())) == 1
    assert classify([requirement], [dict(triage, record_dates=["2025-01-01"])], set()) == []
    assert classify([requirement], [dict(triage, candidate_class="CASH_ONLY")], set()) == []
    assert classify([requirement], [triage], {"a"}) == []


def test_undated_cash_proposal_requires_unique_later_final_issuer_event():
    requirement = {
        "document_id": "a",
        "affected_events": ["CNINFO:1"],
        "issuer": "600180",
        "published_on": "2024-08-29",
        "title": "关于实施2024年度中期分红的公告",
        "url": "proposal-url",
    }
    triage = {
        "document_id": "a",
        "candidate_class": "CASH_ONLY",
        "cash_candidate_per_share": "0.015",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    final = {
        "event_checksum": "final-checksum",
        "event": {
            "security_id": {"value": "CN-A:SSE:600180"},
            "announcement_date": "2024-10-11",
            "ex_date": "2024-10-17",
            "cash_per_share": "0.015",
            "source_url": "https://static.cninfo.com.cn/finalpage/final.PDF",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_document": "2024年半年度权益分派实施公告",
        },
    }
    result = classify([requirement], [triage], set(), [final])
    assert result[0]["accepted_event_checksum"] == "final-checksum"
    assert (
        result[0]["classification"]
        == "NONFINAL_CASH_PROPOSAL_MATCHED_LATER_OFFICIAL_IMPLEMENTATION"
    )
    assert (
        classify(
            [requirement],
            [triage],
            set(),
            [dict(final, event=dict(final["event"], cash_per_share="0.01"))],
        )
        == []
    )
    assert classify([requirement], [triage], set(), [final, final]) == []


def test_no_distribution_and_deferral_require_no_executable_terms():
    requirement = {
        "document_id": "a",
        "affected_events": ["CNINFO:1"],
        "issuer": "600157",
        "published_on": "2024-08-29",
        "title": "关于推迟2023年度利润分配实施的公告",
        "url": "official-url",
    }
    triage = {
        "document_id": "a",
        "candidate_class": "NEITHER",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    assert classify([requirement], [triage], set())[0]["classification"] == (
        "NONFINAL_DEFERRED_IMPLEMENTATION_NOTICE"
    )
    assert classify([requirement], [dict(triage, candidate_class="CASH_ONLY")], set()) == []
    assert classify([requirement], [dict(triage, preferred_instrument_marker=True)], set()) == []
    requirement["title"] = "关于2024年不实施中期现金分红的公告"
    assert classify([requirement], [triage], set())[0]["classification"] == (
        "NONFINAL_NO_DISTRIBUTION_NOTICE"
    )


def test_dated_a_share_hint_requires_later_exact_final_notice():
    pages = [
        "1.H股利润分配时间安排 股权登记日:2024年7月22日;除息日:2024年7月15日。"
        "2.A股利润分配预计时间安排 股权登记日:2024年7月25日;"
        "除息日、现金红利发放日:2024年7月26日。"
        "公司2023年度A股利润分配实施公告将在交易所另行发布。"
    ]
    schedule = a_share_schedule(pages)
    assert schedule == ("2024-07-25", "2024-07-26")
    requirement = {
        "document_id": "hint",
        "affected_events": ["CNINFO:hint"],
        "issuer": "601390",
        "published_on": "2024-07-06",
        "title": "关于2023年度利润分配实施的提示性公告",
        "url": "official-hint",
    }
    triage = {
        "document_id": "hint",
        "candidate_class": "NEITHER",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    final = {
        "event_checksum": "final",
        "event": {
            "security_id": {"value": "CN-A:SSE:601390"},
            "record_date": "2024-07-25",
            "ex_date": "2024-07-26",
            "announcement_date": "2024-07-20",
            "cash_per_share": "0.21",
            "source_url": "https://static.cninfo.com.cn/finalpage/final.PDF",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_document": "2023年度A股权益分派实施公告",
        },
    }
    assert (
        classify([requirement], [triage], set(), [final], {"hint": schedule})[0][
            "accepted_event_checksum"
        ]
        == "final"
    )
    assert (
        classify(
            [requirement],
            [triage],
            set(),
            [dict(final, event=dict(final["event"], ex_date="2024-07-27"))],
            {"hint": schedule},
        )
        == []
    )
