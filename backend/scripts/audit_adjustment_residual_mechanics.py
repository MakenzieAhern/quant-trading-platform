"""Audit official mechanics for the 33 factor changes with no prior source candidate."""

import argparse
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_adjustment_factor_economics import factor_steps
from scripts.audit_adjustment_gap_candidate_terms import cache_index, pages_for
from scripts.build_cash_gap_queue import verified

TOLERANCE = Decimal("3e-8")


def spec(step: str, source: str, *required: str, classification="OFFICIAL_SHARE_MECHANICS"):
    return {
        "expected_factor_step": step,
        "source_sha256": source,
        "required_text": required,
        "classification": classification,
    }


MECHANICS = {
    "FACTOR:CN-A:SSE:600381:2014-06-27": spec(
        "0.1242",
        "1946a7f10e6fba57ed4954c5cde65c73d32964d215bdd66fb870696f2bff13aa",
        "总股本将由重整前的1,601,845,390股缩减至198,925,752股",
        classification="OFFICIAL_TOTAL_CAPITAL_RATIO_ROUNDED",
    ),
    "FACTOR:CN-A:SSE:600610:2014-11-17": spec(
        "3",
        "9603b5fed63f71d6bedd52066151e97fd87a43cb25bcd8e06b9f060dc90c0979",
        "每10股转增20股",
    ),
    "FACTOR:CN-A:SSE:600610:2014-11-25": spec(
        "1.4",
        "457a354f33c8ff7aa26621a093720839da86e94ac29ba38099f8c0b2ebd50f4c",
        "每持有10股流通股将获得大申集团支付的4股对价股份",
    ),
    "FACTOR:CN-A:SSE:600610:2015-08-19": spec(
        "1.1",
        "403e8e3ba981082279f14b77cb71daa42fbfa88bfe1701276c5d76f738c4b5c1",
        "每10股追加送股1股",
    ),
    "FACTOR:CN-A:SSE:600681:2011-09-08": spec(
        "1.4",
        "220322362e2e7d21d02c84f0bf7b341d3439f2a734ec880e1b3115d1f575bc7d",
        "每10股流通股将获得4股定向转增股份",
    ),
    "FACTOR:CN-A:SSE:600688:2013-08-20": spec(
        "1.5",
        "3abf73ac5ccf3fc017e62b5e5a20022c204931c90d312662c4b88eda989a842e",
        "每持有10股流通A股将获得",
        "支付的5股上海石化A股股票",
    ),
    "FACTOR:CN-A:SSE:600705:2012-08-30": spec(
        "3.1",
        "f9734a7487d2041856bff3dbd45819298ba6bf017d51755866d1b798b2ca7052",
        "每10股转增8股",
        "每10股定向转增13股",
    ),
    "FACTOR:CN-A:SSE:600751:2013-06-03": spec(
        "2.29162",
        "caf16216480888cff9776564a408b793d420a70ad4500789d3ab0fce12f80084",
        "每10股定向转增12.9162股",
    ),
    "FACTOR:CN-A:SSE:600817:2013-02-08": spec(
        "1.25",
        "1ac085717478e280d7823d0c8dae943e06b191497b961372c69b5b33e67b312b",
        "每10股转增2.5股",
    ),
    "FACTOR:CN-A:SSE:600871:2013-08-20": spec(
        "1.5",
        "df334c0950dd15110f1010f52c504e5d3e29bb00902f16b201e734c49bbc1568",
        "每持有10股流通A股将获得",
        "支付的5股仪征化纤A股股票",
    ),
    "FACTOR:CN-A:SZSE:000010:2013-07-19": spec(
        "4",
        "ed8a53614e6b6de59e21029c9f8a3fdf574880dd34100e009e4b39ea6a40d017",
        "每10股获得30股",
    ),
    "FACTOR:CN-A:SZSE:000033:2017-05-24": spec(
        "1.304545721558199",
        "5b0c991eb2ee192bcd12f299cdcf7c6a3fbcfac624d142396db1d0250f0d1300",
        "每10股转增3.04545721558199股",
    ),
    "FACTOR:CN-A:SZSE:000038:2013-02-08": spec(
        "1.3",
        "87c793d029956f2ed8eef76fc6b2fa694c3f9eeb6e9bbb1b3d29f8d0fb42819e",
        "每10股定向转增3股",
    ),
    "FACTOR:CN-A:SZSE:000403:2013-02-08": spec(
        "1.6",
        "4cd0e45fd50098a11158b6146baa15a3ddf54e63857cbb7e5f5d587696622477",
        "每10股获定向转增6股",
    ),
    "FACTOR:CN-A:SZSE:000509:2014-01-09": spec(
        "3.5",
        "331936b0998af1c697f73b66e63347bf7f024d85824b87d04c023bdb8e5f4564",
        "每10股获得25股",
    ),
    "FACTOR:CN-A:SZSE:000536:2011-03-25": spec(
        "1.0267233",
        "c90e58710e8640112f5be37541e2801b817828cd7d9dd0874d1ecf15b082c96b",
        "每10股送0.267233股",
    ),
    "FACTOR:CN-A:SZSE:000587:2011-08-18": spec(
        "3",
        "6816aca91a9582476578b6d24fe1b8407c38fc53d54f9b0eb2c2d9a1945aa4be",
        "每10股转增20股",
    ),
    "FACTOR:CN-A:SZSE:000620:2011-07-08": spec(
        "1.4",
        "f6d31b8c516011e32517fdeb89b4b764f3eff78cc1d3bc05eb8f8c47892a4340",
        "每持有10股流通股获得非流通股东支付4股股份的对价",
    ),
    "FACTOR:CN-A:SZSE:000622:2013-02-08": spec(
        "3",
        "25864bcdaa3d3be3d04133dbbfa4a9c837fca3b7733f999366b66e0ab3dea1ea",
        "每10股转增20股",
    ),
    "FACTOR:CN-A:SZSE:000670:2014-07-14": spec(
        "3",
        "4100833e8b223a361d9871e3f8e6a1001055b2e2b04552558bd4a9565893197f",
        "每10股获得20股",
    ),
    "FACTOR:CN-A:SZSE:000688:2013-04-26": spec(
        "1.27",
        "3484e0b1e743718dba043ae8ec2d4c7fea0f5a3cc372a48be66276b06d291b4b",
        "每10股定向转增2.7股",
    ),
    "FACTOR:CN-A:SZSE:000736:2010-04-29": spec(
        "1.0133536",
        "a1aab84705a4984292cedf3b9e404d109152314dd6e0f2a291e746c115f17a8b",
        "每10股流通股获得追送0.133536股",
    ),
    "FACTOR:CN-A:SZSE:000750:2011-08-09": spec(
        "1.2",
        "f994d99237e1a7831282e0d697669983bb70a018e6bac920799306d7eae367d2",
        "每持有10股流通股将获得非流通股股东支付的2股对价",
    ),
    "FACTOR:CN-A:SZSE:000757:2013-02-08": spec(
        "1.2",
        "7cdbe712a14c02b5a88ed6e97958c1f337cd17567c5fe60e01146a6e40ac90e0",
        "以方向光电总股本305,277,713股为基数",
        "每10股转增2股",
        "转增股份为管理人持有及变现",
        classification="OFFICIAL_NON_HOLDER_CAPITAL_INCREASE",
    ),
    "FACTOR:CN-A:SZSE:002506:2015-08-12": spec(
        "2.99165402124431",
        "db5b2122a4ab111c36c6ea939c758cc84d9c53099f318a7e92178c8bfde79f90",
        "每10股转增19.9165402124431股",
        "转增的股份直接划给至公司管理人",
        classification="OFFICIAL_NON_HOLDER_CAPITAL_INCREASE",
    ),
}

UNRESOLVED = {
    "FACTOR:CN-A:SZSE:000156:2012-10-19": spec(
        "1.54062",
        "cde22ab99379590fa113002cebec4d842f82b230ee89addc7ced337e279e61d4",
        "本次非公开发行A股股票的总股数拟定为978,090,000股",
        "确认发行价格为2元/股",
        "总股本为118,935,730股",
        "总股本将变更为1,097,025,730股",
        classification="OFFICIAL_ADDITIONAL_ISSUE_BOUNDARY_PROVIDER_NORMALIZATION_UNRESOLVED",
    )
}


def parity(observed: Decimal, expected: Decimal) -> dict:
    delta = abs(observed - expected)
    return {
        "observed_factor_step": str(observed),
        "expected_factor_step": str(expected),
        "absolute_delta": str(delta),
        "status": "OFFICIAL_MECHANICS_FACTOR_PARITY_PASS" if delta <= TOLERANCE else "CONFLICT",
    }


def source_texts(manifests: list[Path]) -> dict[str, dict]:
    indexed = {}
    for manifest_path in sorted(manifests):
        root = manifest_path.parent.parent
        caches = cache_index(root)
        for document in verified(manifest_path)["documents"]:
            if document["retrieval_status"] != "PASS":
                continue
            source_sha = document["source_sha256"]
            pdf = root / document["source_path"]
            if sha256_file(pdf) != source_sha:
                raise ValueError("OFFICIAL_SOURCE_CHANGED")
            pages, receipt = pages_for(root, document, caches)
            if pages is None:
                raise ValueError("OFFICIAL_SOURCE_PDF_UNREADABLE")
            row = {
                "source_sha256": source_sha,
                "source_url": document["url"],
                "title": document["title"],
                "text": re.sub(r"\s+", "", "".join(pages)),
                **receipt,
            }
            prior = indexed.setdefault(source_sha, row)
            if prior != row:
                raise ValueError("SOURCE_SHA_IDENTITY_CONFLICT")
    return indexed


def check_source(event: str, item: dict, sources: dict[str, dict]) -> dict:
    source = sources.get(item["source_sha256"])
    if source is None:
        raise ValueError(f"REQUIRED_OFFICIAL_SOURCE_MISSING:{event}")
    missing = [text for text in item["required_text"] if text not in source["text"]]
    if missing:
        raise ValueError(f"REQUIRED_OFFICIAL_TERMS_MISSING:{event}:{missing}")
    return {key: source[key] for key in ("source_sha256", "source_url", "title", "text_source")}


def audit(adjustment: dict, terms: dict, residual: dict, sources: dict[str, dict]) -> dict:
    steps = factor_steps(adjustment)
    cash = {
        row["factor_change"]: row["evidence"][0]
        for row in terms["factor_results"]
        if row["status"] == "UNIQUE_EXACT_OFFICIAL_TERMS_CANDIDATE"
    }
    residual_events = {row["factor_change"] for row in residual["results"]}
    partitions = [set(MECHANICS), set(cash), set(UNRESOLVED)]
    overlap = any(
        left & right for index, left in enumerate(partitions) for right in partitions[index + 1 :]
    )
    if overlap:
        raise ValueError("RESIDUAL_CLASSIFICATION_OVERLAP")
    if set().union(*partitions) != residual_events:
        raise ValueError("RESIDUAL_CLASSIFICATION_INCOMPLETE")

    rows = []
    for event, item in sorted(MECHANICS.items()):
        security_id, day = event.removeprefix("FACTOR:").rsplit(":", 1)
        rows.append(
            {
                "factor_change": event,
                "classification": item["classification"],
                **check_source(event, item, sources),
                **parity(steps[security_id, day], Decimal(item["expected_factor_step"])),
            }
        )
    for event, evidence in sorted(cash.items()):
        if evidence["source_sha256"] not in sources:
            raise ValueError(f"CASH_OFFICIAL_SOURCE_MISSING:{event}")
        rows.append(
            {
                "factor_change": event,
                "classification": "OFFICIAL_GROSS_CASH_TERMS_PROVIDER_BASIS_UNRESOLVED",
                **evidence,
                "status": "PROVIDER_FACTOR_BASIS_UNRESOLVED",
            }
        )
    for event, item in sorted(UNRESOLVED.items()):
        security_id, day = event.removeprefix("FACTOR:").rsplit(":", 1)
        rows.append(
            {
                "factor_change": event,
                "classification": item["classification"],
                **check_source(event, item, sources),
                "observed_factor_step": str(steps[security_id, day]),
                "status": "PROVIDER_FACTOR_BASIS_UNRESOLVED",
            }
        )
    counts = Counter(row["status"] for row in rows)
    return {
        "report_id": "FULL_ADJUSTMENT_RESIDUAL_MECHANICS_V1",
        "status": "PARTIAL_OFFICIAL_SOURCE_CLOSURE_PROVIDER_FACTOR_BASIS_UNRESOLVED",
        "residual_factor_changes": len(rows),
        "official_source_covered_factor_changes": len(rows),
        "source_uncovered_factor_changes": 0,
        "official_mechanics_factor_parity": counts["OFFICIAL_MECHANICS_FACTOR_PARITY_PASS"],
        "official_gross_cash_terms_recovered": len(cash),
        "provider_factor_basis_unresolved": counts["PROVIDER_FACTOR_BASIS_UNRESOLVED"],
        "counts": dict(sorted(counts.items())),
        "rows": sorted(rows, key=lambda row: row["factor_change"]),
        "factor_tolerance": str(TOLERANCE),
        "adjustment_authority_promoted": False,
        "dataset_created": False,
        "limitations": [
            "Factor parity validates provider normalization against official mechanics; "
            "it does not create holder entitlements.",
            "Seven official gross-cash terms and one additional-issue boundary still lack "
            "a proven provider factor convention.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adjustment", type=Path, required=True)
    parser.add_argument("--terms", type=Path, required=True)
    parser.add_argument("--residual-metadata", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adjustment, terms, residual = map(
        verified, (args.adjustment, args.terms, args.residual_metadata)
    )
    sources = source_texts(args.source_manifest)
    report = audit(adjustment, terms, residual, sources)
    replay = audit(
        dict(adjustment, intervals=list(reversed(adjustment["intervals"]))),
        dict(terms, factor_results=list(reversed(terms["factor_results"]))),
        dict(residual, results=list(reversed(residual["results"]))),
        sources,
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        input_order_reproducibility="PASS",
        inputs=[
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (
                args.adjustment,
                args.terms,
                args.residual_metadata,
                *sorted(args.source_manifest),
            )
        ],
        parser_sha256=sha256_file(Path(__file__)),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    excluded = {"rows", "inputs", "limitations"}
    print(json.dumps({key: value for key, value in report.items() if key not in excluded}))


if __name__ == "__main__":
    main()
