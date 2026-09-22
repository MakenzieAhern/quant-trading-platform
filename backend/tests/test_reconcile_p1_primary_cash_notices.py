import json

from app.data.catalog.checksums import sha256_file
from scripts.reconcile_p1_primary_cash_notices import reconcile


def test_missing_exchange_row_can_be_recovered_from_exact_official_issuer_terms(tmp_path):
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
                    "证券代码:000001\n本次权益分派方案为:每10股派发现金4.00元(含税)。\n"
                    "本次权益分派股权登记日为:2023年11月29日,除权除息日为:2023年11月30日。"
                ],
            }
        )
    )
    url = "https://static.cninfo.com.cn/finalpage/2023-11-24/test.PDF"
    title = "2023年三季度权益分派实施公告"
    finding = {
        "document_id": "test",
        "finding": "NO_ACCEPTED_EX_DATE_EVENT",
        "security_id": "CN-A:SZSE:000001",
        "source_sha256": source_sha,
        "url": url,
        "title": title,
        "record_date": "2023-11-29",
        "ex_date": "2023-11-30",
        "cash_candidate_per_share": "0.40",
    }
    triage = [{"document_id": "test", "text_cache_sha256": sha256_file(cache)}]
    requirements = [
        {
            "document_id": "test",
            "issuer": "000001",
            "published_on": "2023-11-24",
            "title": title,
            "url": url,
        }
    ]
    master = [
        {
            "security_id": "CN-A:SZSE:000001",
            "instrument_type": "COMMON_A_SHARE",
            "effective_from": "1991-01-01",
            "effective_to": None,
        }
    ]
    sources = [
        {
            **requirements[0],
            "retrieval_status": "PASS",
            "source_sha256": source_sha,
            "source_path": "notice.pdf",
            "retrieved_at_utc": "2026-09-16T00:00:00+00:00",
        }
    ]
    events = reconcile([finding], triage, requirements, [], master, sources, tmp_path)
    assert len(events) == 1
    assert events[0]["event"]["cash_per_share"] == "0.40"
    assert events[0]["supersedes_event_checksum"] is None
