import json
from urllib.parse import parse_qs, urlsplit

from scripts.fetch_a_share_security_master import _fetch_sse
from scripts.probe_full_raw_coverage import requests


def test_sse_master_includes_star_exits_without_overwriting_old_snapshot():
    class Fetcher:
        def get(self, name, url, **kwargs):
            query = parse_qs(urlsplit(url).query)
            rows = []
            if query["COMPANY_STATUS"] == ["3"]:
                assert query["STOCK_TYPE"] == ["1,8"]
                assert name == "sse-terminated-a-boards.json"
                rows = [
                    dict(
                        A_STOCK_CODE=code,
                        LIST_DATE=listing,
                        DELIST_DATE=exit_date,
                        COMPANY_ABBR=code,
                    )
                    for code, listing, exit_date in (
                        ("688086", "20200226", "20230707"),
                        ("688555", "20200623", "20230707"),
                        ("688287", "20220525", "20260610"),
                    )
                ]
            return json.dumps({"pageHelp": {"data": rows}}).encode()

    rows = _fetch_sse(Fetcher())
    assert {r["symbol"] for r in rows} == {"688086", "688555", "688287"}
    assert all(r["board"] == "SSE_STAR" for r in rows)
    assert next(r for r in rows if r["symbol"] == "688287")["effective_to"] == "2026-06-10"


def test_full_raw_probe_keeps_unadjusted_semantics_and_explicit_dates():
    urls = requests("600553")
    primary = parse_qs(urlsplit(urls["Eastmoney"]).query)
    secondary = parse_qs(urlsplit(urls["Tencent"]).query)
    assert primary["fqt"] == ["0"]
    assert primary["beg"] == ["20100101"] and primary["end"] == ["20101231"]
    assert secondary["param"] == ["sh600553,day,2010-01-01,2011-12-31,640,"]
