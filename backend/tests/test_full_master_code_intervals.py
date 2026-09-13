from scripts.split_full_master_code_intervals import split_intervals


def test_effective_dated_alias_preserves_identity_and_no_future_symbol():
    row = dict(
        security_id="CN-A:SSE:601607",
        symbol="601607",
        exchange="SSE",
        effective_from="1994-03-24",
        effective_to="",
        listing_date="1994-03-24",
    )
    transition = dict(
        exchange="SSE",
        old_symbol="600849",
        new_symbol="601607",
        effective_date="2010-03-05",
        sha256="a" * 64,
        source_url="https://www.sse.com.cn/fixture",
    )
    result = split_intervals([row], [transition])
    assert [r["symbol"] for r in result] == ["600849", "601607"]
    assert [r["security_id"] for r in result] == [row["security_id"]] * 2
    assert result[0]["effective_to"] == "2010-03-04"
    assert result[1]["effective_from"] == "2010-03-05"
    assert row["symbol"] == "601607"  # Input and frozen Pilot are untouched.
