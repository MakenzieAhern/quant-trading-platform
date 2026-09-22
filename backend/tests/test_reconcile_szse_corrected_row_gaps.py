import json

import pytest

from scripts.audit_szse_official_row_gaps import SOURCE_REPORT_SHA
from scripts.reconcile_sse_cninfo import sha
from scripts.reconcile_szse_corrected_row_gaps import close_report, verify_evidence


def test_corrected_overlay_uses_only_official_bounded_dates():
    base = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V1",
        "source_collection_sha256": SOURCE_REPORT_SHA,
        "missing_rows": 3,
        "raw_authority_promoted": False,
        "manifest_sha256": "base",
        "classification_counts": {"NO_MATCHING_HALT_SOURCE": 2, "DATED_SOURCE_HALT_INTERVAL": 1},
        "unresolved_rows": [
            {
                "security_id": "CN-A:SZSE:000693",
                "date": "2013-01-04",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
            {
                "security_id": "CN-A:SZSE:000693",
                "date": "2014-01-10",
                "reason": "NO_MATCHING_HALT_SOURCE",
            },
        ],
    }
    prior = {
        "report_version": "SZSE_OFFICIAL_ROW_GAPS_V7",
        "missing_rows": 3,
        "manifest_sha256": "prior",
        "official_000693_interval": {
            "security_id": "CN-A:SZSE:000693",
            "suspended_from": "2007-05-23",
            "first_trading_day": "2014-01-10",
            "source_absent_rows_closed": 1,
            "evidence": [],
        },
        "additional_official_pre2010_intervals": [],
        "additional_official_2010plus_intervals": [],
        "additional_official_terminal_intervals": [],
    }
    report = close_report(base, prior, "base-sha")
    assert report["classification_counts"]["OFFICIAL_PRE2010_LISTING_SUSPENSION"] == 1
    assert report["classification_counts"]["DATED_SOURCE_HALT_INTERVAL"] == 1
    assert report["unresolved_rows"] == [base["unresolved_rows"][1]]


def test_evidence_bytes_must_match_receipt(tmp_path):
    pdf = tmp_path / "issuer.pdf"
    pdf.write_bytes(b"%PDF-test")
    meta = {
        "url": "https://static.cninfo.com.cn/issuer.pdf",
        "sha256": sha(pdf.read_bytes()),
        "http_status": 200,
        "retrieved_at_utc": "2026-09-18T00:00:00+00:00",
    }
    (tmp_path / "issuer.pdf.meta.json").write_text(json.dumps(meta))
    report = {
        "official_intervals": [
            {
                "security_id": "CN-A:SZSE:000693",
                "evidence": [
                    {
                        "url": meta["url"],
                        "sha256": meta["sha256"],
                        "retrieved_at_utc": meta["retrieved_at_utc"],
                    }
                ],
            }
        ]
    }
    verify_evidence(report, tmp_path)
    pdf.write_bytes(b"%PDF-tampered")
    with pytest.raises(ValueError, match="OFFICIAL_INTERVAL_EVIDENCE_CHANGED"):
        verify_evidence(report, tmp_path)
