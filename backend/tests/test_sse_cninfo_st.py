"""Offline disclosure fixtures are factual text extracted from six archived CNINFO PDFs."""

# Intentional source punctuation is part of the parser regression fixture.
# ruff: noqa: RUF001

import copy
import json
from pathlib import Path

import pytest

from scripts.reconcile_sse_cninfo import (
    canonical,
    fetch,
    issuer_subject,
    load_candidates,
    match,
    sha,
)
from scripts.sse_st_events import extract, normalize, status_on

FIXTURES = json.loads((Path(__file__).parent / "fixtures/cninfo_st_disclosures.json").read_text())
EXPECTED = [
    ("STAR_ST", "ST", "2022-01-14"),
    ("NORMAL", "ST", "2022-02-09"),
    ("ST", "NORMAL", "2022-03-28"),
    ("STAR_ST", "NORMAL", "2022-04-21"),
    ("ST", "STAR_ST", "2022-04-26"),
    ("NORMAL", "STAR_ST", "2022-04-28"),
]


def test_issuer_prefix_spacing_and_leading_escaped_newline():
    sse = {"SECURITY_NAME": None}
    cn = {"secName": "ST春 兰"}
    assert issuer_subject("ST春兰关于撤销风险警示", sse, cn) == "关于撤销风险警示"
    company = "上海龙韵传媒集团股份有限公司"
    assert issuer_subject(r"\n" + company + "股票实施其他风险警示", sse, cn) == (
        issuer_subject("\n" + company + "股票实施其他风险警示", sse, cn)
    )
    assert issuer_subject("*ST春兰关于撤销风险警示", sse, cn).startswith("*ST")
    assert issuer_subject("关于撤消风险警示", sse, cn) != issuer_subject(
        "关于撤销风险警示", sse, cn
    )
    subject = "会计师对《关于对西安宏盛科技发展股份有限公司的问询函》的说明"
    assert issuer_subject(subject, sse, cn) == issuer_subject("ST春兰：" + subject, sse, cn)


@pytest.mark.parametrize(("fixture", "expected"), list(zip(FIXTURES, EXPECTED, strict=True)))
def test_real_disclosure_transition(fixture, expected):
    event = extract(fixture["pages"], fixture["record"])
    assert (event["old_status"], event["status"], event["effective_from"]) == expected
    assert event["sse_publication_date"] < event["effective_from"]
    assert event["cninfo_publication_date"] < event["effective_from"]
    assert event["support"] and event["cninfo_document_sha256"]
    assert status_on([event], event["security_id"], event["sse_publication_date"]) == "UNKNOWN"
    assert status_on([event], event["security_id"], event["effective_from"]) == event["status"]


def test_duplicate_rows_and_mirrors_are_not_duplicate_transitions():
    fixture = copy.deepcopy(FIXTURES[0])
    record = fixture["record"]
    record["cninfo"] *= 2
    assert match(record["sse"], record["cninfo"])[0] == "EXACT"
    event = extract(fixture["pages"], record)
    assert normalize([event, event]) == [event]
    record["cninfo"][1] = {**record["cninfo"][1], "announcementId": "different-mirror"}
    assert match(record["sse"], record["cninfo"])[0] == "AMBIGUOUS"
    with pytest.raises(ValueError, match="MATCH_NOT_EXACT"):
        extract(fixture["pages"], record)


def test_pdf_subject_review_is_bound_to_document_and_preserves_other_checks():
    fixture = copy.deepcopy(FIXTURES[0])
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    cn = record["cninfo"][0]
    subject = issuer_subject(cn["announcementTitle"], record["sse"], cn)
    subject = subject[subject.index("关于") :]
    changed = subject.replace("公告", "特别公告")
    record["sse"]["TITLE"] = changed
    cn["announcementTitle"] = changed
    with pytest.raises(ValueError, match="PDF_SUBJECT_METADATA_MISMATCH"):
        extract(fixture["pages"], record)
    record["pdf_subject_review"] = dict(
        announcement_id=cn["announcementId"],
        source_sha256=record["cninfo_document_sha256"],
        metadata_subject=changed,
        pdf_subject=subject,
        page=1,
    )
    assert extract(fixture["pages"], record)["status"] == "ST"
    with pytest.raises(ValueError, match="WRONG_SECURITY_CODE"):
        extract(
            [p.replace(record["sse"]["SECURITY_CODE"], "600000") for p in fixture["pages"]], record
        )
    record["pdf_subject_review"]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="PDF_SUBJECT_METADATA_MISMATCH"):
        extract(fixture["pages"], record)


def test_pdf_subject_review_accepts_matching_non_about_title_form():
    fixture = copy.deepcopy(FIXTURES[0])
    record = fixture["record"]
    record["match_method"] = "security+date+exact_subject+issuer_prefix"
    cn = record["cninfo"][0]
    cn["announcementTitle"] = record["sse"]["TITLE"] = "*ST中孚股票实施退市风险警示公告.doc"
    record["pdf_subject_review"] = dict(
        announcement_id=cn["announcementId"],
        source_sha256=record["cninfo_document_sha256"],
        metadata_subject="股票实施退市风险警示公告.doc",
        pdf_subject="股票实施退市风险警示公告",
        page=1,
    )
    fixture["pages"][0] = "股票实施退市风险警示公告" + fixture["pages"][0]
    assert extract(fixture["pages"], record)["status"] == "ST"


def test_wrong_security_date_title_and_issuer_rejected():
    fixture = FIXTURES[0]
    for field, value in (
        ("secCode", "600000"),
        ("announcementTime", 0),
        ("announcementTitle", "unrelated风险警示"),
    ):
        rows = copy.deepcopy(fixture["record"]["cninfo"])
        rows[0][field] = value
        assert match(fixture["record"]["sse"], rows)[0] == "NO_MATCH"
    pages = [p.replace("600595", "600000") for p in fixture["pages"]]
    with pytest.raises(ValueError, match="WRONG_SECURITY_CODE"):
        extract(pages, fixture["record"])
    pages = [p.replace("河南中孚实业股份有限公司", "另一家股份有限公司") for p in fixture["pages"]]
    with pytest.raises(ValueError, match="WRONG_ISSUER_COMPANY"):
        extract(pages, fixture["record"])


def test_missing_explicit_effective_date_is_not_publication_fallback():
    fixture = FIXTURES[1]
    pages = [p.replace("起始日", "日期待定") for p in fixture["pages"]]
    with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
        extract(pages, fixture["record"])


def test_ordinary_name_label_and_expanded_name_do_not_merge():
    record = FIXTURES[1]["record"]
    baseline = extract(FIXTURES[1]["pages"], record)
    old, new = baseline["old_name"], baseline["new_name"]
    header = f"证券代码：{baseline['symbol']} 证券简称：{old} {record['sse']['TITLE']}"
    date_clause = "实施其他风险警示的起始日：2022年2月9日"
    # Synthetic malformed quote models the independently verified 688282 source defect.
    text = (
        header + f"股票简称由“{old}”变更为“{new}；"
        f"扩位证券简称由“{old}”变更为“{new}扩”；" + date_clause
    )
    with pytest.raises(ValueError, match="NAME_TRANSITION_UNRESOLVED"):
        extract([text], record)
    event = extract([text + f"实施后A股简称为{new}，"], record)
    assert (event["new_name"], event["effective_from"]) == (new, "2022-02-09")
    valid = header + f"股票简称由“{old}”变更为“{new}”；" + date_clause
    assert extract([valid + f"扩位证券简称由“{old}”变更为“{new}扩”；"], record)["new_name"] == new
    with pytest.raises(ValueError, match="CONFLICTING_LABELED_NAME"):
        extract([valid + "实施后A股简称为ST错误，"], record)

    same_status = header + date_clause + "实施后A股简称为ST样本，"
    same_status += "实施后A股简称为ST样本公司，"
    event = extract([same_status], record)
    assert event["status"] == "ST"
    assert event["official_same_status_name_variants"] == ["ST样本", "ST样本公司"]


def test_explicit_date_label_variants():
    fixture = FIXTURES[1]
    pages = [p.replace("起始日\uff1a", "起始日为\uff1a") for p in fixture["pages"]]
    assert extract(pages, fixture["record"])["effective_from"] == "2022-02-09"
    assert (
        extract([p.replace("起始日为\uff1a", "起始日\uff1a自") for p in pages], fixture["record"])[
            "effective_from"
        ]
        == "2022-02-09"
    )
    for variant in ("股票简称\uff1a由", "股票简称将由", "简称由", "股票简称\uff1a", "股票由"):
        pages = [p.replace("股票简称由", variant) for p in fixture["pages"]]
        assert extract(pages, fixture["record"])["status"] == "ST"
    conflicting = [*fixture["pages"], "实施其他风险警示的起始日为2020年5月6日"]
    with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
        extract(conflicting, fixture["record"])


def test_pilot_boundary_future_leakage_order_checksum_and_exclusion():
    events = [extract(f["pages"], f["record"]) for f in FIXTURES]
    baseline = events[0]
    identity = baseline["security_id"]
    assert status_on(events, identity, "2023-01-01") == "ST"
    # Synthetic future conflict checks temporal filtering, not a real issuer event.
    future = {
        **baseline,
        "status": "NORMAL",
        "effective_from": "2023-02-01",
        "sse_publication_date": "2023-01-31",
        "cninfo_publication_date": "2023-01-31",
    }
    assert status_on([future, *events], identity, "2023-01-01") == "ST"
    late_publication = {**future, "effective_from": "2022-12-30"}
    assert status_on([late_publication, *events], identity, "2023-01-01") == "ST"
    assert normalize(events) == normalize(list(reversed(events)))
    assert sha(canonical(normalize(events))) == sha(canonical(normalize(events * 2)))
    assert extract(FIXTURES[0]["pages"], FIXTURES[0]["record"]) == baseline
    assert (
        status_on(events, identity, "2023-01-01", ((identity, "2023-01-01", "2024-07-31"),))
        == "UNKNOWN"
    )
    assert status_on(events, "CN-A:SSE:600000", "2023-01-01") == "UNKNOWN"
    conflict = {**baseline, "status": "NORMAL"}
    assert status_on([baseline, conflict], identity, "2023-01-01") == "UNKNOWN"


def test_saved_snapshot_repeatability_and_corruption_rejection(tmp_path, monkeypatch):
    raw = b"original disclosure"
    path = tmp_path / "snapshot"
    path.write_bytes(raw)
    path.with_suffix(".meta.json").write_bytes(
        canonical(
            {
                "url": "https://static.cninfo.com.cn/example",
                "params": None,
                "sha256": sha(raw),
            }
        )
    )

    def no_network(*args, **kwargs):
        raise AssertionError("cached snapshot must not use network")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    assert fetch(tmp_path, "snapshot", "https://static.cninfo.com.cn/example") == raw
    path.write_bytes(b"corruption")
    with pytest.raises(ValueError, match="checksum mismatch"):
        fetch(tmp_path, "snapshot", "https://static.cninfo.com.cn/example")


def test_duplicate_sse_metadata_rows_and_page_order(tmp_path):
    row = FIXTURES[0]["record"]["sse"]
    raw = canonical({"pageHelp": {"data": [[row], [row]]}})
    (tmp_path / "page.json").write_bytes(raw)
    page = {"relative_path": "page.json", "sha256": sha(raw)}
    manifest = {"pages": [page, page]}
    (tmp_path / "source-manifest.json").write_bytes(
        canonical(
            {
                **manifest,
                "manifest_sha256": sha(canonical(manifest)),
            }
        )
    )
    inventory = tmp_path / "inventory.json"
    inventory.write_bytes(canonical([{"source_url": "https://static.sse.com.cn" + row["URL"]}] * 2))
    candidates, hashes, _ = load_candidates(tmp_path, inventory)
    assert candidates == [row]
    assert hashes[row["URL"]] == sha(raw)


def test_denial_is_never_retried(tmp_path, monkeypatch):
    path = tmp_path / "denied.meta.json"
    path.write_bytes(
        canonical(
            {
                "url": "https://static.cninfo.com.cn/example",
                "params": None,
                "attempt": 1,
                "error": "RuntimeError",
            }
        )
    )

    def no_network(*args, **kwargs):
        raise AssertionError("must not retry an access denial")

    monkeypatch.setattr("urllib.request.urlopen", no_network)
    with pytest.raises(RuntimeError, match="no automatic retry"):
        fetch(tmp_path, "denied", "https://static.cninfo.com.cn/example")


def test_transient_dns_failure_is_retried(tmp_path, monkeypatch):
    (tmp_path / "snapshot.meta.json").write_bytes(
        canonical(
            {
                "url": "https://static.cninfo.com.cn/example",
                "params": None,
                "attempt": 1,
                "error": "URLError",
                "error_reason": "<urlopen error [Errno -2] Name or service not known>",
            }
        )
    )

    class Response:
        status = 200

        def __init__(self):
            self.headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def read(self):
            return b"%PDF"

    monkeypatch.setattr("time.sleep", lambda _: None)
    monkeypatch.setattr("urllib.request.urlopen", lambda *args, **kwargs: Response())
    assert fetch(tmp_path, "snapshot", "https://static.cninfo.com.cn/example") == b"%PDF"


def test_partial_warning_removal_is_not_normal_exit():
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_confirmation.json").read_text()
    )
    event = extract(fixture["pages"], fixture["record"])
    assert event["event_type"] == "STATUS_CONFIRMATION"
    assert event["old_status"] == event["status"] == "STAR_ST"
    assert event["effective_from"] == "2022-01-24"
    assert status_on([event], event["security_id"], "2023-01-01") == "STAR_ST"


def test_real_new_name_syntax_and_original_conflicting_dates():
    fixtures = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_parser_closure.json").read_text()
    )
    for fixture in fixtures:
        record = fixture["record"]
        identity = record["cninfo"][0]["announcementId"]
        if identity == "1213268833":
            with pytest.raises(ValueError, match="EFFECTIVE_DATE_UNRESOLVED"):
                extract(fixture["pages"], record)
        else:
            event = extract(fixture["pages"], record)
            assert event["event_type"] == "ST_TO_STAR_ST"
            assert (
                event["effective_from"]
                == {"1213274369": "2022-05-06", "1219926861": "2024-05-06"}[identity]
            )
