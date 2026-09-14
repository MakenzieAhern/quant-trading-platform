"""Offline checks for historical anchor and independent coverage-oracle boundaries."""

import copy
import json
from pathlib import Path

import pytest

from scripts.reconcile_sse_cninfo import canonical, fetch, match, sha
from scripts.sse_st_closure import anchor_names, controls, explain_names, historical_names
from scripts.sse_st_events import extract, status


def test_anchor_period_unicode_and_duplicates():
    pages = [""] * 6 + ["2022年1月1日至2022年12月31日"]
    table = "年末个股股东持股情况\n600260 \u2217ST凯乐 123\n600070 浙江富润 456"
    rows = anchor_names([*pages, table])
    assert rows["600260"]["status"] == "STAR_ST"
    assert rows["600070"]["status"] == "NORMAL"
    assert status("\uff0aST凯乐") == "STAR_ST"
    assert status("\ufe61ST贤成") == "STAR_ST"
    with pytest.raises(ValueError, match="DUPLICATE"):
        anchor_names([*pages, table, table])
    with pytest.raises(ValueError, match="WRONG_ANCHOR_PERIOD"):
        anchor_names([*([""] * 7), table])


def test_oracle_supplies_no_dates_and_entry_alone_is_not_closure():
    raw = ('page_symbol="sh600001";证券简称更名历史</td><td>普通名 ST样本 *ST样本</td>').encode(
        "gb18030"
    )
    assert historical_names(raw, "600001") == ["普通名", "ST样本", "*ST样本"]
    with pytest.raises(ValueError, match="IDENTITY"):
        historical_names(raw, "600002")
    entry = {
        "old_name": "样本",
        "new_name": "ST样本",
        "old_status": "NORMAL",
        "status": "ST",
        "effective_from": "2020-01-02",
        "cninfo_document_id": "entry",
    }
    exit_ = {
        "old_name": "ST样本",
        "new_name": "样本",
        "old_status": "ST",
        "status": "NORMAL",
        "effective_from": "2021-01-02",
        "cninfo_document_id": "exit",
    }
    assert not explain_names(["ST样本"], [entry], None)[0]["explained"]
    assert explain_names(["ST样本"], [entry, exit_], None)[0]["explained"]
    assert not explain_names(["ST样本"], [entry, {**exit_, "effective_from": "2019-01-01"}], None)[
        0
    ]["explained"]
    assert explain_names(["ST样本"], [entry, exit_], None) == explain_names(
        ["ST样本"], [exit_, entry], None
    )


def test_control_sample_is_stratified_and_order_independent():
    master = [
        {
            "security_id": f"{board}-{date}-{i}",
            "board": board,
            "listing_date": date,
            "delisting_date": "2025-01-01" if i == 29 else "",
        }
        for board in ("SSE_MAIN", "STAR")
        for date in ("2010-01-01", "2022-01-01")
        for i in range(30)
    ]
    selected = controls(master, set())
    assert len(selected) >= 100
    assert selected == controls(list(reversed(master)), set())
    assert all(row in selected for row in master if row["delisting_date"])


def test_optional_prefix_matching_stays_exact_and_null_safe():
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes()
    )
    record = copy.deepcopy(fixtures[1]["record"])
    record["sse"]["TITLE"] = "样本关于实施风险警示的公告"
    record["sse"]["SECURITY_NAME"] = None
    record["cninfo"][0]["secName"] = "样本"
    record["cninfo"][0]["announcementTitle"] = "关于实施风险警示的公告"
    assert match(record["sse"], record["cninfo"])[0] == "NO_MATCH"
    assert match(record["sse"], record["cninfo"], issuer_prefix=True)[0] == "EXACT"
    record["cninfo"][0]["announcementTitle"] = "关于撤销风险警示的公告"
    assert match(record["sse"], record["cninfo"], issuer_prefix=True)[0] == "NO_MATCH"


def test_missing_sse_name_requires_exact_cninfo_pdf_header_identity():
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes()
    )
    fixture = copy.deepcopy(fixtures[1])
    record = fixture["record"]
    old = record["sse"]["SECURITY_NAME"]
    record["sse"]["SECURITY_NAME"] = None
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    record["cninfo"][0]["secName"] = old
    assert extract(fixture["pages"], record)["old_name"] == old
    record["cninfo"][0]["secName"] = "another issuer"
    with pytest.raises(ValueError, match="WRONG_ISSUER_NAME"):
        extract(fixture["pages"], record)


def test_space_delimited_security_code_still_requires_exact_digits():
    fixture = copy.deepcopy(
        json.loads((Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes())[1]
    )
    record = fixture["record"]
    symbol = record["sse"]["SECURITY_CODE"]
    body = "\n".join(fixture["pages"])
    for label in ("证券代码", "股票代码"):
        pages = [f"{label} {symbol}\n" + body]
        assert extract(pages, record)["symbol"] == symbol
        for wrong in ("600999", symbol + "0", "0" + symbol):
            with pytest.raises(ValueError, match="WRONG_SECURITY_CODE"):
                extract([f"{label} {wrong}\n" + body], record)


def test_pdf_subject_must_match_metadata():
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes()
    )
    fixture = copy.deepcopy(fixtures[1])
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    record["sse"]["TITLE"] = record["cninfo"][0]["announcementTitle"] = "关于另一项风险警示的公告"
    with pytest.raises(ValueError, match="PDF_SUBJECT_METADATA_MISMATCH"):
        extract(fixture["pages"], record)


def test_short_header_name_requires_adjacent_matching_security_code():
    fixture = copy.deepcopy(
        json.loads((Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes())[1]
    )
    record = fixture["record"]
    old = record["sse"]["SECURITY_NAME"]
    symbol = record["sse"]["SECURITY_CODE"]
    record["sse"]["SECURITY_NAME"] = None
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    record["cninfo"][0]["secName"] = old
    body = f"{record['sse']['TITLE']}。股票简称由“{old}”变更为“*ST样本”。"
    body += "实施退市风险警示的起始日:2022年2月9日。"
    assert extract([f"证券代码:{symbol} 简称:{old}\n" + body], record)["status"] == "STAR_ST"
    for header in (
        f"证券代码:{symbol} 债券代码:122060 简称:{old}",
        f"证券代码:{symbol} 另文简称:{old}",
        f"证券代码:{symbol} 证券代码:600999 简称:{old}",
    ):
        with pytest.raises(ValueError, match="CNINFO_NAME_NOT_PDF_HEADER"):
            extract([header + "\n" + body], record)


def test_referer_is_part_of_snapshot_identity(tmp_path, monkeypatch):
    raw = b"snapshot"
    (tmp_path / "page").write_bytes(raw)
    (tmp_path / "page.meta.json").write_bytes(
        canonical(
            {
                "url": "https://example.com/query",
                "params": None,
                "referer": "https://example.com/public",
                "sha256": sha(raw),
            }
        )
    )

    def no_network(*args, **kwargs):
        raise AssertionError("cached snapshot must not use network")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    assert (
        fetch(tmp_path, "page", "https://example.com/query", referer="https://example.com/public")
        == raw
    )
    with pytest.raises(ValueError, match="identity mismatch"):
        fetch(tmp_path, "page", "https://example.com/query")


def test_legacy_clause_does_not_select_adjacent_suspension_date():
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes()
    )
    fixture = copy.deepcopy(fixtures[1])
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    # Keep the real identity/name-change fixture, replace only its date label syntax.
    import re

    pages = [
        re.sub(r"起始日[\uff1a:]?\s*2022\s*年\s*2\s*月\s*9\s*日", "日期另列", p)
        for p in fixture["pages"]
    ]
    old = record["sse"]["SECURITY_NAME"]
    new = extract(fixture["pages"], record)["new_name"]
    pages.append(f"2022年2月8日停牌一天,自2022年2月9日起,股票简称由“{old}”变更为“{new}”。")
    assert extract(pages, record)["effective_from"] == "2022-02-09"
    for weekday in ("星期三", "周三"):
        assert (
            extract([*pages[:-1], pages[-1].replace("日起,", f"日({weekday})开始,")], record)[
                "effective_from"
            ]
            == "2022-02-09"
        )
    with pytest.raises(ValueError, match="WEEKDAY_DATE_CONFLICT"):
        extract([*pages[:-1], pages[-1].replace("日起,", "日(星期二)开始,")], record)
    assert (
        extract([*pages[:-1], pages[-1].replace("日起,", "日开始,")], record)["effective_from"]
        == "2022-02-09"
    )
    pages[-1] = pages[-1].replace("自2022年2月9日起,", "")
    with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
        extract(pages, record)


def test_resumption_date_requires_direct_exact_name_change_clause():
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes()
    )
    fixture = copy.deepcopy(fixtures[1])
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    baseline = extract(fixture["pages"], record)
    old, new = baseline["old_name"], baseline["new_name"]
    header = f"证券代码:{baseline['symbol']} 证券简称:{old} {record['sse']['TITLE']}。"
    clause = f"股票简称由“{old}”变更为“{new}”。"
    for prefix in ("公司的", "公司", "公司A股", ""):
        text = header + "2022年2月8日停牌一天,2022年2月9日复牌," + prefix + clause
        assert extract([text], record)["effective_from"] == "2022-02-09"
        alternate_name = clause.replace("股票简称", "证券简称")
        assert extract([header + alternate_name + text], record)["effective_from"] == "2022-02-09"
    for names in (
        f"股票简称将从“{old}”变更为“{new}”。",
        f"股票简称由{old}变更为{new}。",
        f"股票简称由“{old}”变成“{new}”。",
        f"股票简称由原“{old}”变为“{new}”。",
        f"股票简称由“{old}”改为“{new}”。",
    ):
        text = header + "2022年2月9日复牌,公司的" + names
        assert extract([text], record)["new_name"] == new
        with pytest.raises(ValueError, match="NAME_TRANSITION_UNRESOLVED"):
            extract([text.replace(names, names.replace(old, "错误名称"))], record)
    for text in (
        header + "2022年2月9日复牌。公司的" + clause,
        header + "2022年2月9日停牌,公司的" + clause,
    ):
        with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
            extract([text], record)
    text = header + "公司股票将于2022年2月9日实施其他风险警示。" + clause
    assert extract([text], record)["effective_from"] == "2022-02-09"
    measures = (
        header + "2022年2月8日停牌一天,从2022年2月9日起实行其他风险警示。具体处理措施为:" + clause
    )
    assert extract([measures], record)["effective_from"] == "2022-02-09"
    with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
        extract([measures.replace("起实行其他风险警示", "起实行退市风险警示")], record)
    for invalid in (
        text.replace("实施其他风险警示。", "实施退市风险警示。"),
        text.replace("公司股票将于", "关联公司股票将于"),
    ):
        with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
            extract([invalid], record)


def test_explicit_removal_date_requires_issuer_and_single_date():
    fixture = copy.deepcopy(
        json.loads((Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes())[0]
    )
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    text = "证券代码:600595 证券简称:*ST中孚 " + record["sse"]["TITLE"] + "。"
    text += "自2022年1月14日起撤销本公司股票交易退市风险警示。"
    text += "股票简称由“*ST中孚”变更为“中孚”。"
    assert extract([text], record)["effective_from"] == "2022-01-14"
    for invalid in (
        text.replace("撤销本公司", "撤销关联公司"),
        text + "自2022年1月17日起撤销本公司股票交易退市风险警示。",
    ):
        with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
            extract([invalid], record)


def test_historical_name_pair_requires_its_own_explicit_past_date():
    fixture = copy.deepcopy(
        json.loads((Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes())[0]
    )
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    header = "证券代码:600595 证券简称:*ST中孚 " + record["sse"]["TITLE"] + "。"
    past = "自2020年1月1日起,股票简称由“*ST中孚”变更为“中孚”。"
    current = "2022年1月14日复牌,公司股票简称由“*ST中孚”变更为“ST中孚”。"
    result = extract([header + past + current], record)
    assert (result["status"], result["effective_from"]) == ("ST", "2022-01-14")
    for invalid_past in (
        past.replace("自2020年1月1日起,", ""),
        past.replace("2020年1月1日", "2022年1月17日"),
    ):
        with pytest.raises(ValueError, match="NAME_TRANSITION_UNRESOLVED"):
            extract([header + invalid_past + current], record)


def test_date_inside_name_clause_is_not_an_adjacent_suspension_date():
    fixture = copy.deepcopy(
        json.loads((Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes())[0]
    )
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    header = "证券代码:600595 证券简称:*ST中孚 " + record["sse"]["TITLE"] + "。"
    for middle in ("", "发生变更,"):
        clause = f"证券简称自2022年1月14日起{middle}由“*ST中孚”变更为”ST中孚”。"
        result = extract([header + "2022年1月13日停牌。" + clause], record)
        assert (result["status"], result["effective_from"]) == ("ST", "2022-01-14")
        with pytest.raises(ValueError):
            extract([header + clause.replace("*ST中孚", "*ST他人")], record)
        with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
            extract([header + clause + clause.replace("1月14日", "1月17日")], record)


def test_legacy_new_name_label_requires_explicit_date_and_security():
    fixture = copy.deepcopy(
        json.loads((Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_bytes())[1]
    )
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    symbol, old = record["sse"]["SECURITY_CODE"], record["sse"]["SECURITY_NAME"]
    header = f"证券代码:{symbol} 证券简称:{old} {record['sse']['TITLE']}。"
    date_clause = "公司股票自2022年2月9日起实行退市风险警示特别处理。"
    for label in (
        "实行退市风险警示后本公司股票简称:*ST样本。",
        "实行退市风险警示后股票简称:*ST样本。",
        "实行退市风险警示后公司股票的简称:*ST样本,",
        "实行退市风险警示后股票简称为:*ST样本实行退市风险警示后涨跌幅限制为5%。",
        f"股票简称变更为*ST样本,股票代码{symbol},",
    ):
        assert extract([header + date_clause + label], record)["status"] == "STAR_ST"
        with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
            extract([header + label], record)
    with pytest.raises(ValueError, match="NAME_TRANSITION_UNRESOLVED"):
        extract([header + date_clause + "股票简称变更为*ST样本,股票代码600999,"], record)
    dated_label = "实行退市风险警示的起始日:公司股票将于2022年2月8日停牌一天,"
    dated_label += "2022年2月9日起实行退市风险警示。"
    dated_label += "实行退市风险警示后公司股票的简称:*ST样本,"
    assert extract([header + dated_label], record)["effective_from"] == "2022-02-09"
    bare = "退市风险警示起始日:2022年2月9日。实行退市风险警示后股票简称:*ST样本。"
    assert extract([header + bare], record)["effective_from"] == "2022-02-09"
    with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
        extract([header + bare + "退市风险警示起始日:2022年2月10日。"], record)
    for variant in (
        dated_label.replace("将于", "于").replace("2022年2月9日起实行", "自2022年2月9日起实行"),
        dated_label.replace("公司股票", "公司", 1),
        dated_label.replace("日起实行退市风险警示。", "日实行“退市风险警示”。"),
    ):
        assert extract([header + variant], record)["effective_from"] == "2022-02-09"
