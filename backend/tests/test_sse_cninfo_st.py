"""Offline disclosure fixtures are factual text extracted from six archived CNINFO PDFs."""

import copy
import json
from pathlib import Path

import pytest

from scripts.reconcile_sse_cninfo import canonical, fetch, load_candidates, match, sha
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


def test_explicit_date_label_variants():
    fixture = FIXTURES[1]
    pages = [p.replace("起始日\uff1a", "起始日为\uff1a") for p in fixture["pages"]]
    assert extract(pages, fixture["record"])["effective_from"] == "2022-02-09"
    for variant in ("股票简称\uff1a由", "股票简称将由"):
        pages = [p.replace("股票简称由", variant) for p in fixture["pages"]]
        assert extract(pages, fixture["record"])["status"] == "ST"


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


def test_partial_warning_removal_is_not_normal_exit():
    fixture = json.loads(
        (Path(__file__).parent / "fixtures/cninfo_st_confirmation.json").read_text()
    )
    event = extract(fixture["pages"], fixture["record"])
    assert event["event_type"] == "STATUS_CONFIRMATION"
    assert event["old_status"] == event["status"] == "STAR_ST"
    assert event["effective_from"] == "2022-01-24"
    assert status_on([event], event["security_id"], "2023-01-01") == "STAR_ST"
