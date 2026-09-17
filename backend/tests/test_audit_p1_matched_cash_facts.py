import json

from app.data.catalog.checksums import sha256_file
from scripts.audit_p1_matched_cash_facts import close_facts


def test_exact_cash_fact_closes_by_primary_or_stronger_official_notice(tmp_path):
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
    triage = [
        {
            "document_id": "test",
            "url": url,
            "source_sha256": source_sha,
            "text_cache_sha256": sha256_file(cache),
            "candidate_class": "CASH_ONLY",
            "preferred_instrument_marker": False,
            "cash_candidate_per_share": "0.40",
            "record_dates": ["2023-11-29"],
            "ex_dates": ["2023-11-30"],
        }
    ]
    requirements = [
        {
            "document_id": "test",
            "issuer": "000001",
            "published_on": "2023-11-24",
            "title": "2023年三季度权益分派实施公告",
            "affected_events": ["test-event"],
        }
    ]
    cash = [
        {
            "event": {
                "security_id": {"value": "CN-A:SZSE:000001"},
                "record_date": "2023-11-29",
                "ex_date": "2023-11-30",
                "cash_per_share": "0.4",
                "source_url": url,
                "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
                "source_document": "2023年三季度权益分派实施公告",
            },
            "event_checksum": "accepted",
        }
    ]
    master = [
        {
            "symbol": "000001",
            "security_id": "CN-A:SZSE:000001",
            "effective_from": "1991-01-01",
            "effective_to": None,
            "instrument_type": "COMMON_A_SHARE",
        }
    ]
    sources = [
        {
            "url": url,
            "source_path": "notice.pdf",
            "source_sha256": source_sha,
            "retrieval_status": "PASS",
            "issuer": "000001",
            "title": requirements[0]["title"],
        }
    ]
    primary = close_facts(triage, requirements, cash, master, sources, tmp_path, set())
    assert primary[0]["classification"] == "OFFICIAL_PRIMARY_NOTICE_EXACT_CORROBORATION"
    requirements[0]["title"] = sources[0]["title"] = "关于分红派息实施后调整回购价格的公告"
    derivative = close_facts(triage, requirements, cash, master, sources, tmp_path, set())
    assert derivative[0]["classification"] == "STRONGER_ACCEPTED_OFFICIAL_NOTICE_SUBSTITUTION"
    cache.write_text(
        json.dumps(
            {
                "source_sha256": source_sha,
                "pages": [
                    "证券代码:000001\n每10股派发现金4.00元(含税),每10股转增4股。\n"
                    "股权登记日:2023年11月29日;除权除息日:2023年11月30日。"
                ],
            }
        )
    )
    triage[0]["text_cache_sha256"] = sha256_file(cache)
    triage[0]["candidate_class"] = "BOTH"
    mixed = close_facts(triage, requirements, cash, master, sources, tmp_path, set())
    assert mixed[0]["bonus_component_status"] == "SOURCE_TERMS_ONLY_ACCOUNTING_PENDING"
