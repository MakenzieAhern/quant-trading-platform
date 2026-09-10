"""Coverage-oracle dispositions require dated official evidence, never name ordering."""

# Intentional fullwidth source characters exercise normalization.
# ruff: noqa: RUF001

from scripts.sse_st_coverage import header_state
from scripts.sse_st_residual import anchor_closes_ancient_gap, token_disposition


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


def test_authoritative_anchor_closes_only_reviewed_ancient_uncertainty():
    anchor = dict(
        authoritative=True,
        complete_for_security=True,
        status="NORMAL",
        effective_from="2022-05-05",
        known_on="2022-04-29",
    )
    assert anchor_closes_ancient_gap(anchor, "2001-12-31", [], [], True)
    # Full-history audit remains unresolved even when the pilot scope is proven.
    assert token_disposition("ST旧名", [], {"name": "普通名"}, [])["classification"] == "UNRESOLVED"
    for change in [
        dict(authoritative=False),
        dict(complete_for_security=False),
        dict(status="UNKNOWN"),
        dict(known_on="2023-02-01"),
        dict(effective_from="2023-02-01"),
    ]:
        assert not anchor_closes_ancient_gap(anchor | change, "2001-12-31", [], [], True)
    for boundary in [None, "2022-05-05", "2023-01-01"]:
        assert not anchor_closes_ancient_gap(anchor, boundary, [], [], True)
    assert not anchor_closes_ancient_gap(anchor, "2001-12-31", [], ["conflict"], True)
    assert not anchor_closes_ancient_gap(anchor, "2001-12-31", [], [], False)
    entry = dict(
        old_status="NORMAL",
        status="ST",
        effective_from="2023-03-01",
        sse_publication_date="2023-02-28",
        cninfo_publication_date="2023-02-28",
    )
    removal = entry | dict(old_status="ST", status="NORMAL", effective_from="2023-04-01")
    assert anchor_closes_ancient_gap(anchor, "2001-12-31", [entry, removal], [], True)
    assert anchor_closes_ancient_gap(anchor, "2001-12-31", [removal, entry], [], True)
    assert not anchor_closes_ancient_gap(anchor, "2001-12-31", [removal], [], True)
    assert not anchor_closes_ancient_gap(
        anchor, "2001-12-31", [entry | dict(effective_from="2022-05-05")], [], True
    )
    assert anchor_closes_ancient_gap(
        anchor, "2001-12-31", [removal | dict(effective_from="2025-01-01")], [], True
    )
    assert not anchor_closes_ancient_gap(
        anchor, "2001-12-31", [entry | dict(cninfo_publication_date="2023-03-02")], [], True
    )
