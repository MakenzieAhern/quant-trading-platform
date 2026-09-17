"""Proposal-only notices must never substitute for final cash facts."""

from scripts.audit_p1_nonfinal_proposals import (
    a_share_schedule,
    classify,
    convertible_halt_final,
    preferred_header_only,
)


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


def test_convertible_halt_hint_does_not_set_final_cash_amount():
    title = "中信银行股份有限公司2023年年度A股普通股分红派息实施公告"
    pages = [
        "若本行总股本在股权登记日前发生变动,相应调整每股分配比例。"
        "本行将于2024年7月3日在上海证券交易所网站发布《" + title + "》。"
    ]
    promised = convertible_halt_final(pages)
    assert promised == ("2024-07-03", title)
    requirement = {
        "document_id": "bond-hint",
        "affected_events": ["CNINFO:bond-hint"],
        "issuer": "601998",
        "published_on": "2024-06-27",
        "title": "关于A股普通股分红派息实施时中信转债停止转股的提示性公告",
        "url": "official-bond-hint",
    }
    triage = {
        "document_id": "bond-hint",
        "candidate_class": "CASH_ONLY",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": False,
        "cash_candidate_per_share": "0.356",
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    final = {
        "event_checksum": "final",
        "event": {
            "security_id": {"value": "CN-A:SSE:601998"},
            "record_date": "2024-07-09",
            "ex_date": "2024-07-10",
            "announcement_date": "2024-07-03",
            "cash_per_share": "0.3261",
            "source_url": "https://static.cninfo.com.cn/finalpage/final.PDF",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_document": title,
        },
    }
    result = classify([requirement], [triage], set(), [final], bond_notices={"bond-hint": promised})
    assert result[0]["classification"] == (
        "NONFINAL_CONVERTIBLE_HALT_MATCHED_LATER_FINAL_IMPLEMENTATION"
    )
    assert (result[0]["indicative_cash_per_share"], result[0]["final_cash_per_share"]) == (
        "0.356",
        "0.3261",
    )
    assert (
        classify(
            [requirement],
            [triage],
            set(),
            [dict(final, event=dict(final["event"], announcement_date="2024-07-04"))],
            bond_notices={"bond-hint": promised},
        )
        == []
    )


def test_preferred_code_only_in_header_does_not_turn_a_share_proposal_into_preferred_event():
    pages = [
        "证券代码:601009 优先股代码:360019 本公司董事会保证真实。"
        "大股东提议实施中期利润分配,尚需股东大会审议。"
    ]
    assert preferred_header_only(pages)
    assert not preferred_header_only([pages[0] + "优先股股息另行派发。"])
    requirement = {
        "document_id": "proposal",
        "affected_events": ["CNINFO:proposal"],
        "issuer": "601009",
        "published_on": "2024-08-01",
        "title": "关于收到大股东提议实施中期利润分配方案的公告",
        "url": "official-proposal",
    }
    triage = {
        "document_id": "proposal",
        "candidate_class": "NEITHER",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": True,
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    assert classify([requirement], [triage], set()) == []
    assert (
        classify([requirement], [triage], set(), header_only_preferred={"proposal"})[0][
            "classification"
        ]
        == "NONFINAL_PROPOSAL_NO_EXECUTABLE_CASH_OR_BONUS_TERMS"
    )


def test_convertible_halt_announces_unique_later_final_without_indicative_cash():
    final_title = "江苏银行股份有限公司2022年年度权益分派实施公告"
    pages = [
        "证券代码:600919 优先股代码:360026 本公司董事会保证真实。"
        "苏银转债将停止转股,转股价格将调整。"
        "本行将于2023年7月11日刊登《" + final_title + "》。"
    ]
    promised = convertible_halt_final(pages)
    assert promised == ("2023-07-11", final_title)
    requirement = {
        "document_id": "hint",
        "affected_events": ["CNINFO:hint"],
        "issuer": "600919",
        "published_on": "2023-07-05",
        "title": "关于A股分红派息实施暨苏银转债转股连续停牌的提示性公告",
        "url": "official-hint",
    }
    triage = {
        "document_id": "hint",
        "candidate_class": "NEITHER",
        "record_dates": [],
        "ex_dates": [],
        "preferred_instrument_marker": True,
        "cash_candidate_per_share": None,
        "source_sha256": "sha",
        "text_cache_sha256": "cache",
    }
    final = {
        "event_checksum": "final",
        "event": {
            "security_id": {"value": "CN-A:SSE:600919"},
            "record_date": "2023-07-14",
            "ex_date": "2023-07-17",
            "announcement_date": "2023-07-11",
            "cash_per_share": "0.4907",
            "source_url": "https://static.cninfo.com.cn/finalpage/final.PDF",
            "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY",
            "source_document": "江苏银行2022年年度权益分派实施公告",
        },
    }
    result = classify(
        [requirement],
        [triage],
        set(),
        [final],
        bond_notices={"hint": promised},
        header_only_preferred={"hint"},
    )
    assert result[0]["accepted_event_checksum"] == "final"
    assert result[0]["indicative_cash_per_share"] is None
