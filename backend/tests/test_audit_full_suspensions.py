import json

from app.data.catalog.checksums import canonical_sha256
from scripts.audit_full_suspensions import (
    load_resumption_supplements,
    normalize_sse,
    normalize_szse,
)

MASTER = {
    ("SSE", "600000"): [
        {"security_id": "CN-A:SSE:600000", "effective_from": "1999-11-10", "effective_to": None}
    ],
    ("SZSE", "000001"): [
        {"security_id": "CN-A:SZSE:000001", "effective_from": "1991-04-03", "effective_to": None}
    ],
}


def test_suspension_audit_deduplicates_overlap_and_never_invents_resume():
    sse_row = {
        "productCode": "600000",
        "productName": "浦发银行",
        "startStopDate": "20100104",
        "endStopDate": "20100105",
        "stopTime": "",
        "type": "LXTP",
        "controlType": "TR",
        "stopReason": "重要事项",
        "endStopReason": "重要公告",
        "source_file": "a.json",
    }
    sse, non_target, duplicates = normalize_sse(
        [sse_row, {**sse_row, "source_file": "b.json"}],
        MASTER,
        {"a.json": "a", "b.json": "b"},
    )
    assert len(sse) == 1 and sse[0]["execution_open_blocked"] is True
    assert non_target == 0 and duplicates == 1

    szse, unresolved, conflicts, non_target, duplicates = normalize_szse(
        [
            {
                "symbol": "000001",
                "suspended_at": "2010/01/04 09:30",
                "resumed_at": "9999/12/31 00:00",
                "source_file": "c.html",
            }
        ],
        MASTER,
        {"c.html": "c"},
        {"CN-A:SZSE:000001": None},
    )
    assert len(szse) == 1 and szse[0]["resumed_at"] is None
    assert len(unresolved) == 1
    assert not conflicts and non_target == duplicates == 0

    szse, unresolved, *_ = normalize_szse(
        [
            {
                "symbol": "000001",
                "suspended_at": "2010/01/04 09:30",
                "resumed_at": "9999/12/31 00:00",
                "source_file": "c.html",
            }
        ],
        MASTER,
        {"c.html": "c"},
        {"CN-A:SZSE:000001": None},
        {
            ("CN-A:SZSE:000001", "2010/01/04 09:30"): {
                "resumed_at": "2010-01-05",
                "evidence": [{"source_sha256": "official"}],
            }
        },
    )
    assert unresolved == []
    assert szse[0]["closure"] == "OFFICIAL_RESUMPTION_DOCUMENT"


def test_resumption_supplements_merge_without_losing_prior_batches(tmp_path):
    paths = []
    for index, day in enumerate(("2010-01-05", "2010-02-05")):
        report = {
            "accepted_resumptions": [
                {
                    "security_id": "CN-A:SZSE:000001",
                    "suspended_at": f"2010/0{index + 1}/04 09:30",
                    "resumed_at": day,
                    "evidence": [],
                }
            ]
        }
        report["manifest_sha256"] = canonical_sha256(report)
        path = tmp_path / f"batch-{index}.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        paths.append(path)

    supplements, hashes = load_resumption_supplements(paths)

    assert len(supplements) == len(hashes) == 2
