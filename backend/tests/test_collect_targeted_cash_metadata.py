import json

from scripts.collect_targeted_cash_metadata import gap_symbols, official_orgs


def test_official_orgs_reuses_retained_cninfo_pages(tmp_path):
    (tmp_path / "page.json").write_text(
        json.dumps(
            {
                "announcements": [
                    {"secCode": "600000", "orgId": "gssh0600000"},
                    {"secCode": "000001", "orgId": "gssz0000001"},
                ]
            }
        )
    )
    (tmp_path / "page.json.meta.json").write_text("not an API page")
    assert official_orgs(tmp_path, {"600000"}) == {"600000": "gssh0600000"}


def test_gap_symbols_accepts_audited_cash_coverage():
    assert gap_symbols({"unresolved_events": [{"security_id": "CN-A:SZSE:000001"}]}) == {"000001"}
