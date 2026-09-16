import json

from app.data.catalog.checksums import sha256_file
from scripts.reconcile_sse_precise_issuer_cash import reconcile


def test_exact_issuer_amount_replaces_rounded_sse_cash_amount(tmp_path):
    pdf = tmp_path / "notice.pdf"
    pdf.write_bytes(b"official fixture")
    source_sha = sha256_file(pdf)
    cache = tmp_path / "batch-v1/text" / f"{source_sha}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(
        json.dumps(
            {
                "source_sha256": source_sha,
                "pages": [
                    "证券代码:600938\n差异化分红送转:否\n"
                    "A股每股现金红利人民币0.60844元(含税)。\n"
                    "股权登记日为2022年10月12日,除权除息日为2022年10月13日。"
                ],
            }
        )
    )
    old = {
        "security_id": {"value": "CN-A:SSE:600938"},
        "record_date": "2022-10-12",
        "ex_date": "2022-10-13",
        "cash_per_share": "0.608",
    }
    previous = {
        "events": [
            {
                "event": old,
                "event_checksum": "old-checksum",
                "evidence": {
                    "issuer_notice": {
                        "url": "https://static.cninfo.com.cn/finalpage/2022-10-07/test.PDF",
                        "retrieval_status": "PASS",
                        "source_path": "notice.pdf",
                        "source_sha256": source_sha,
                        "issuer": "600938",
                        "published_on": "2022-10-07",
                        "title": "2022年A股中期股息分派实施公告",
                        "retrieved_at_utc": "2026-09-16T00:00:00+00:00",
                    }
                },
            }
        ]
    }
    corrected = {
        "events": [],
        "outcomes": [
            {
                "security_id": "CN-A:SSE:600938",
                "ex_date": "2022-10-13",
                "status": "ISSUER_NOTICE_TABLE_CASH_AMOUNT_CONFLICT",
            }
        ],
    }
    events = reconcile(previous, corrected, {"events": []}, previous, tmp_path)
    assert len(events) == 1
    assert events[0]["event"]["cash_per_share"] == "0.60844"
    assert events[0]["supersedes_event_checksum"] == "old-checksum"
