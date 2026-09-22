def test_selects_only_current_gap_symbols_in_deterministic_order():
    from scripts.index_r5_sse_st_gap_ocr import select_candidates

    queue = {
        "candidates": [
            {"symbol": "600002", "date": "2012-01-02", "id": "2"},
            {"symbol": "600001", "date": "2012-01-01", "id": "1"},
            {"symbol": "600003", "date": "2012-01-03", "id": "3"},
        ]
    }
    chain = {
        "rows": [
            {"security_id": "CN-A:SSE:600001", "gaps": [{}]},
            {"security_id": "CN-A:SSE:600002", "gaps": [{}]},
            {"security_id": "CN-A:SSE:600003", "gaps": []},
        ]
    }

    assert [row["id"] for row in select_candidates(queue, chain)] == ["1", "2"]
