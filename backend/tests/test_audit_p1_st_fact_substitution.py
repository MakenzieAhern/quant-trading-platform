import pytest

from scripts.audit_p1_st_fact_substitution import close


def test_old_sse_st_requests_require_accepted_fact_chain_and_event():
    requirements = [
        {
            "priority": "P1",
            "required_document_types": ["OFFICIAL_EFFECTIVE_DATED_ST_OR_NAME_CHANGE_NOTICE"],
            "affected_events": ["SSE_ST_GAP:CN-A:SSE:600074:1"],
            "document_id": "old-gap",
        },
        {
            "priority": "P1",
            "required_document_types": ["OFFICIAL_SSE_ST_OR_NAME_CHANGE_NOTICE"],
            "affected_events": ["SSE_ST_MIRROR:59504717"],
            "document_id": "old-mirror",
        },
    ]
    authority = {
        "SSE_HISTORICAL_ST_RECONSTRUCTION": "PASS_PUBLIC_OFFICIAL_RECONSTRUCTION",
        "chain_gaps": 0,
        "chain_conflicts": 0,
        "unknown_intervals": 0,
        "unmapped_events": [],
        "gates": {"UNKNOWN_POINT_IN_TIME_STATES": "PASS"},
        "chains": [
            {"security_id": "CN-A:SSE:600074", "gaps": [], "conflicts": [], "event_count": 2}
        ],
    }
    corpus = {
        "unresolved_count": 0,
        "results": [
            {
                "announcement_id": "59504717",
                "classification": "EXPLAINED_BY_OFFICIAL_EVENT",
                "source_sha256": "official-sha",
            }
        ],
    }
    assert len(close(requirements, authority, corpus)) == 2
    corpus["results"][0]["classification"] = "UNRESOLVED"
    with pytest.raises(ValueError, match="OLD_SSE_ST_MIRROR_NOT_ACCEPTED"):
        close(requirements, authority, corpus)
