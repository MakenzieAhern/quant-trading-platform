"""Same-day evidence is explicit, opt-in and never repairs a frozen dataset."""

import json
import sys
from pathlib import Path

import pytest

from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts import reconcile_retained_bonus
from scripts.retained_bonus_terms import same_day_listing

TITLE = "2010年度权益分派实施公告"
RECORD = "2011-03-25"
EX = "2011-03-28"
NOTICE = (
    "证券代码:600000\n2010年度权益分派实施公告。"
    "一、权益分派方案\n向全体股东每10股转增10股。"
    "二、股权登记日与除权除息日\n股权登记日为2011年3月25日,"
    "除权除息日为2011年3月28日。"
    "三、分派对象\n本次权益分派对象为:2011年3月25日下午交易所收市后,"
    "在登记结算公司登记在册的本公司全体股东。"
    "四、转增股本方法\n本次转增股于2011年03月28日直接记入股东证券账户。"
    "五、本次转增的无限售条件流通股的起始交易日为2011年3月28日。"
)


@pytest.mark.parametrize(
    ("credit", "listing"),
    (
        ("本次所转增股份", "本次所转增"),
        ("本次所(转增)股", "本次所(转增)"),
        ("本次所送(转增)股", "本次所送(转增)"),
    ),
)
def test_same_day_retained_notice_wording_keeps_all_dates_and_holder_scope(credit, listing):
    notice = (
        NOTICE.replace("本次权益分派对象", "本次分派对象")
        .replace("本次转增股", credit)
        .replace("本次转增的无限售", listing + "的无限售")
        .replace("证券账户", "证券帐户")
    )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("本公司全体股东", "本公司控股股东"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("起始交易日为2011年3月28日", "起始交易日待定"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    # A conflicting alternative wording is still an official-date conflict.
    with pytest.raises(ValueError):
        same_day_listing(
            [NOTICE + notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )


@pytest.mark.parametrize(
    ("holder_prefix", "credit"),
    (("截止", "本次转增股"), ("", "本次转增的股份"), ("截止", "本次转增的股份")),
)
def test_explicit_cutoff_and_credit_wording_never_infers_missing_dates(holder_prefix, credit):
    notice = NOTICE.replace("对象为:", "对象为:" + holder_prefix).replace(
        "本次转增股于", credit + "于"
    )
    assert same_day_listing([notice], "600000", TITLE, RECORD, EX) == EX
    for old, new in (
        ("2011年3月25日下午", "2011年3月24日下午"),
        ("2011年3月25日下午", "2011年2月30日下午"),
        ("2011年3月25日下午", "股权登记日下午"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "直接记入"),
        ("全体股东", "控股股东"),
        ("无限售条件", "有限售条件"),
        ("2011年3月28日。", "上市日期另行公告。"),
    ):
        with pytest.raises(ValueError):
            same_day_listing([notice.replace(old, new)], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError):
        same_day_listing(
            [NOTICE + notice.replace("2011年3月25日下午", "2011年3月24日下午")],
            "600000",
            TITLE,
            RECORD,
            EX,
        )
    with pytest.raises(ValueError):
        same_day_listing(
            [notice.replace("2011年03月28日直接记入", "2011年03月29日直接记入") + NOTICE],
            "600000",
            TITLE,
            RECORD,
            EX,
        )
    # The actual 002006 source has explicit credit but no unrestricted listing clause.
    with pytest.raises(ValueError):
        same_day_listing([notice.split("五、本次")[0]], "600000", TITLE, RECORD, EX)


def test_same_day_requires_same_final_issuer_holder_credit_and_listing():
    assert same_day_listing([NOTICE], "600000", TITLE, RECORD, EX) == EX
    with pytest.raises(ValueError, match="FINAL_ISSUER"):
        same_day_listing([NOTICE], "600001", TITLE, RECORD, EX)
    for title in (
        "董事会决议公告",
        "年度利润分配预案",
        "权益分派实施提示性公告",
        "2010年度权益分派实施公告(预案)",
        "2010年度权益分派实施公告(提议)",
        "2010年度权益分派实施公告(进展)",
        "2010年度权益分派实施公告(实施后)",
        "董事会关于2010年度权益分派实施公告",
    ):
        with pytest.raises(ValueError, match="FINAL_ISSUER"):
            same_day_listing([NOTICE], "600000", title, RECORD, EX)
    for old, new in (
        ("2011年03月28日直接记入", "直接记入"),
        ("2011年03月28日直接记入", "3月28日直接记入"),
        ("2011年03月28日直接记入", "2011年03月29日直接记入"),
        ("2011年03月28日直接记入", "2011年02月30日直接记入"),
        ("无限售条件", "有限售条件"),
        ("起始交易日为2011年3月28日", "起始交易日未确定"),
        ("起始交易日为2011年3月28日", "起始交易日为2011年3月29日"),
        ("本公司全体股东", "本公司控股股东"),
    ):
        expected = "NONSTANDARD_OR_TENTATIVE" if "未确定" in new else "DATES_UNRESOLVED"
        with pytest.raises(ValueError, match=expected):
            same_day_listing([NOTICE.replace(old, new)], "600000", TITLE, RECORD, EX)
    for suffix in (
        "本次转增股于2011年03月29日直接记入股东证券账户。",
        "本次转增的无限售条件流通股的起始交易日为2011年2月30日。",
        "本次转增的无限售条件流通股的起始交易日为2011年3月29日。",
        "股权登记日为2011年2月30日。",
        "除权除息日为2011年2月30日。",
        "差异化分红送转:是",
        "拟于除权日入账。",
        "上市日期另行公告。",
        "本条款适用于B股。",
        "本次转增的无限售条件流通股的起始交易日未确定。",
        "取消本次转增股份入账。",
        "新增股份上市日期另行通知。",
    ):
        with pytest.raises(ValueError):
            same_day_listing([NOTICE + suffix], "600000", TITLE, RECORD, EX)
    with pytest.raises(ValueError, match="RECORD_EX_CONFLICT"):
        same_day_listing([NOTICE], "600000", TITLE, "2011-03-24", EX)
    # A cross-page date cannot be assembled from unverified margin/page text.
    first, second = NOTICE.split("2011年03月28日直接记入")
    with pytest.raises(ValueError, match="DATES_UNRESOLVED"):
        same_day_listing(
            [first + "2011年03月", "28日直接记入" + second], "600000", TITLE, RECORD, EX
        )


def _manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({**data, "manifest_sha256": canonical_sha256(data)}))


def test_opt_in_reconciliation_is_immutable_and_preserves_default_schedule(tmp_path, monkeypatch):
    # CLI provenance is relative to its own source, not the caller's working directory.
    monkeypatch.chdir(tmp_path)
    staging = tmp_path / "staging"
    root = staging / "full-distribution-notices-v1"
    bonus = staging / "full-bonus-inventory-v1"
    pdf = root / "pdf/notice.pdf"
    pdf.parent.mkdir(parents=True)
    pdf.write_bytes(b"synthetic source bytes for an offline parser boundary test")
    source_sha = sha256_file(pdf)
    cache = root / "batch-v1/text" / f"{source_sha}.json"
    cache.parent.mkdir(parents=True)
    cache.write_text(json.dumps({"source_sha256": source_sha, "pages": [NOTICE]}))
    doc = dict(
        issuer="600000",
        published_on="2011-03-22",
        title=TITLE,
        retrieval_status="PASS",
        url="https://static.cninfo.com.cn/finalpage/fixture.PDF",
        source_sha256=source_sha,
        source_path="pdf/notice.pdf",
        retrieved_at_utc="2026-10-03T00:00:00Z",
    )
    source = root / "source-manifest.json"
    _manifest(source, {"documents": [doc]})
    evidence = [{"ratio": "1.000"}]
    identity = dict(symbol="600000", record_date=RECORD, ex_date=EX)
    oracle = bonus / "source-oracle-v1.json"
    _manifest(
        oracle,
        {
            "rows": [
                {**identity, "evidence": evidence, "evidence_sha256": canonical_sha256(evidence)}
            ]
        },
    )
    boundary = bonus / "listing-boundary-check-v2.json"
    _manifest(boundary, {"source_sha256": sha256_file(oracle), "rows": []})
    master = staging / "full-code-transitions-v1/master-code-intervals.json"
    _manifest(
        master,
        {
            "records": [
                dict(
                    symbol="600000",
                    security_id="CN-A:SSE:600000",
                    effective_from="2000-01-01",
                    effective_to=None,
                    listing_date="2000-01-01",
                    delisting_date=None,
                )
            ]
        },
    )
    _manifest(
        staging / "full-instrument-scope-v1/classification-manifest-v3.json",
        {
            "source_master_sha256": sha256_file(master),
            "classifications": [
                {
                    "classification": {
                        "security_id": {"value": "CN-A:SSE:600000"},
                        "instrument_type": "COMMON_A_SHARE",
                    }
                }
            ],
        },
    )
    links = root / "date-links-2011.json"
    _manifest(
        links,
        {
            "year": 2011,
            "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
            "results": [
                {
                    **identity,
                    "documents": [
                        {
                            "url": doc["url"],
                            "source_sha256": source_sha,
                            "extraction_sha256": sha256_file(cache),
                        }
                    ],
                }
            ],
        },
    )

    def run(name, *flags):
        output = tmp_path / name
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "reconcile_retained_bonus",
                "--staging",
                str(staging),
                "--date-links",
                str(links),
                "--output",
                str(output),
                *flags,
            ],
        )
        reconcile_retained_bonus.main()
        return json.loads(output.read_bytes())

    assert run("default.json")["accepted_events"] == 0
    accepted = run("same-day.json", "--explicit-same-day")
    assert accepted["accepted_events"] == 1
    assert not accepted["full_dataset_created"]
    assert accepted["same_day_dependency_sha256"] == {
        name: sha256_file(Path(reconcile_retained_bonus.__file__).with_name(name))
        for name in (
            "link_distribution_notices.py",
            "audit_p1_retained_cash_sources.py",
            "audit_p1_orphan_cash_facts.py",
            "audit_p1_cash_census_counterexamples.py",
        )
    }
    event = accepted["events"][0]
    assert event["event"]["source_version"] == "INTEGER_RETAINED_BONUS_EXPLICIT_SAME_DAY_V3"
    assert event["event"]["listing_date"] == EX
    assert event["event"]["share_ratio"] == "1.000"
    assert not event["scheduled_listing_not_actual_tradability"]
    assert event["support_state"] == "SUPPORTED_FOR_INTEGER_HOLDINGS_EXPLICIT_SAME_DAY"
    assert run("same-day.json", "--explicit-same-day") == accepted
    _manifest(
        boundary,
        {
            "source_sha256": sha256_file(oracle),
            "rows": [
                {
                    "symbol": "600000",
                    "ex_date": EX,
                    "status": "NEXT_ACCEPTED_SESSION",
                    "next_session": "2011-03-29",
                }
            ],
        },
    )
    default = run("next-session.json")
    assert default["scope"] == "BOUNDED_INTEGER_NEXT_SESSION_BONUS_NOT_FULL_CENSUS"
    assert "same_day_dependency_sha256" not in default
    assert default["events"][0]["event"]["listing_date"] == "2011-03-29"
    assert default["events"][0]["scheduled_listing_not_actual_tradability"]
    assert (
        default["events"][0]["support_state"]
        == "SUPPORTED_FOR_INTEGER_HOLDINGS_NEXT_SESSION_SCHEDULE"
    )

    # Rebind outer manifests deliberately: the inner PDF/text identity must still agree.
    original_cache = json.loads(cache.read_bytes())
    for name, content in (
        ("wrong-inner-sha.json", {**original_cache, "source_sha256": "0" * 64}),
        ("fraction.json", {**original_cache, "pages": [NOTICE.replace("转增10股", "转增15股")]}),
        (
            "no-listing.json",
            {**original_cache, "pages": [NOTICE.replace("无限售条件", "有限售条件")]},
        ),
    ):
        cache.write_text(json.dumps(content))
        _manifest(
            links,
            {
                "year": 2011,
                "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
                "results": [
                    {
                        **identity,
                        "documents": [
                            {
                                "url": doc["url"],
                                "source_sha256": source_sha,
                                "extraction_sha256": sha256_file(cache),
                            }
                        ],
                    }
                ],
            },
        )
        rejected = run(name, "--explicit-same-day")
        assert rejected["accepted_events"] == 0
        assert rejected["results"][0]["unresolved_documents"]
    cache.write_text(json.dumps(original_cache))
    for name, changed in (
        ("wrong-host.json", {**doc, "url": "https://example.invalid/fixture.PDF"}),
        ("wrong-issuer.json", {**doc, "issuer": "600001"}),
        ("late-published.json", {**doc, "published_on": EX}),
        ("path-escape.json", {**doc, "source_path": "../../escape.pdf"}),
    ):
        _manifest(source, {"documents": [changed]})
        _manifest(
            links,
            {
                "year": 2011,
                "inputs": [{"path": str(source), "sha256": sha256_file(source)}],
                "results": [
                    {
                        **identity,
                        "documents": [
                            {
                                "url": changed["url"],
                                "source_sha256": source_sha,
                                "extraction_sha256": sha256_file(cache),
                            }
                        ],
                    }
                ],
            },
        )
        if name == "wrong-host.json":
            assert run(name, "--explicit-same-day")["accepted_events"] == 0
        else:
            with pytest.raises(ValueError, match="BONUS_SOURCE_IDENTITY_CHANGED"):
                run(name, "--explicit-same-day")
