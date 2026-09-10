"""Coverage-oracle dispositions require dated official evidence, never name ordering."""

# Intentional fullwidth source characters exercise normalization.
# ruff: noqa: RUF001

from scripts.sse_st_coverage import header_state
from scripts.sse_st_residual import token_disposition


def test_residual_boundaries_are_exact_and_not_invented_dates():
    anchor = {"name": "普通名", "status": "NORMAL"}
    observed = [{"name_key": "ST旧名", "date": "2001-01-01", "document": "official"}]
    assert (
        token_disposition("ST旧名", [], anchor, observed)["classification"]
        == "EVENT_OUTSIDE_RELEVANT_PERIOD"
    )
    assert token_disposition("*ST旧名", [], anchor, observed)["classification"] == "UNRESOLVED"
    assert token_disposition("SST旧名", [], anchor, observed)["classification"] == "UNRESOLVED"
    assert (
        token_disposition("ST旧名", [], anchor, [dict(observed[0], date="2024-01-01")])[
            "classification"
        ]
        == "UNRESOLVED"
    )
    future = dict(observed[0], date="2025-01-01")
    assert token_disposition("ST旧名", [], anchor, [future])["classification"] == "UNRESOLVED"
    future["boundary_kind"] = "POST_PILOT_ENTRY"
    assert (
        token_disposition("ST旧名", [], anchor, [future])["classification"]
        == "EVENT_OUTSIDE_RELEVANT_PERIOD"
    )
    assert header_state(["证券代码：600001 股票名称：＊ST旧名"], "600001", "*ST旧名") == "STAR_ST"
