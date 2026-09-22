"""Close the 35 retained factor residuals with checksum-bound official mechanics."""

import argparse
import json
import warnings
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from io import BytesIO
from pathlib import Path

from openpyxl import load_workbook

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_adjustment_factor_economics import (
    economics,
    factor_steps,
    sse_pre_closes,
    szse_pre_closes,
)
from scripts.audit_adjustment_residual_mechanics import parity
from scripts.audit_adjustment_special_mechanics import source_texts
from scripts.build_cash_gap_queue import verified

PRICE_TICK = Decimal("0.01")


def reference(pre: str, result: str, source: str) -> dict:
    return {
        "kind": "OFFICIAL_DECLARED_REFERENCE_PRICE",
        "expected_pre_close": pre,
        "expected_reference_price": result,
        "source_sha256": source,
        "required_text": (f"{result}元/股",),
    }


def direct(step: str, source: str, *required: str, classification: str) -> dict:
    return {
        "kind": "OFFICIAL_DIRECT_FACTOR_STEP",
        "expected_factor_step": step,
        "source_sha256": source,
        "required_text": required,
        "classification": classification,
    }


REFERENCES = {
    "FACTOR:CN-A:SSE:600515:2021-12-22": reference(
        "8.67", "5.87", "1713b6823f0a4ef74a83d15be52e93e32b3ea96e0caf07f38f38d0c2a8a38c88"
    ),
    "FACTOR:CN-A:SZSE:000430:2025-12-29": reference(
        "7.90", "6.87", "0039497f81acd5b9bbcba79d381a52cef39bb78d563408dee993f69aa5067634"
    ),
    "FACTOR:CN-A:SZSE:000525:2024-11-18": reference(
        "10.10", "9.07", "e17b6c501993b434e5ad47a0eeede81a1d4b0decb6bffae04ff8b33f2ad7ecd8"
    ),
    "FACTOR:CN-A:SZSE:000615:2025-12-29": reference(
        "4.18", "3.53", "cd61df57890322155f93e48891ecf27c62914c312b7d580f82f180fa3d59d731"
    ),
    "FACTOR:CN-A:SZSE:000697:2025-11-28": reference(
        "8.52", "8.05", "e72e4f05a0f80bee6a798e9cd1d5ed85727c22c6fd5fea39f4f421d71390cde5"
    ),
    "FACTOR:CN-A:SZSE:000796:2023-12-20": reference(
        "4.08", "3.93", "b058d90cc01d9f384b34467accf4abd5ed934a9c06d18973bf052089dc7fe54b"
    ),
    "FACTOR:CN-A:SZSE:000981:2022-02-25": reference(
        "3.50", "2.10", "59cee8bc672d89968d53f0e3d2617b399ea37f2b82db8a6b844aaac64d23d166"
    ),
    "FACTOR:CN-A:SZSE:002021:2023-12-29": reference(
        "3.53", "2.80", "ead472b11f8adbf7768ef420c429e1a0c55af939da6a9469891930c1dd22fb4f"
    ),
    "FACTOR:CN-A:SZSE:002076:2022-12-21": reference(
        "2.60", "2.23", "01e168895c5cd35713acb7895f5bb1b92aa34dae8eebf2fd1f89fe6969cdfee2"
    ),
    "FACTOR:CN-A:SZSE:002200:2025-12-12": reference(
        "7.82", "6.94", "c8e49596d7b8ae5592b15df9b0b9ad48d769d7f1425fca9051ba6719d968e637"
    ),
    "FACTOR:CN-A:SZSE:002219:2022-06-23": reference(
        "3.40", "2.49", "4a513432d3c12240bd9fa98bd66f16fb1be31782f203fe906155672b0102db5d"
    ),
    "FACTOR:CN-A:SZSE:002323:2022-01-06": reference(
        "5.38", "2.98", "8c3172b17de32ed127c0fbef2885e6bb854e7ec694556c93c63992627fed0854"
    ),
    "FACTOR:CN-A:SZSE:002647:2025-03-13": reference(
        "5.96", "5.25", "807e81a251fb3ec4871fdc458f0e1838e12bf90ce09db13bfc0d4a5adc419bab"
    ),
    "FACTOR:CN-A:SZSE:002713:2025-12-30": reference(
        "11.00", "8.14", "102db0e2d61978c54af65ea9fb3d7689a21048d4d77823d692a9fcd47ec9df86"
    ),
    "FACTOR:CN-A:SZSE:002742:2025-12-10": reference(
        "4.85", "4.64", "8cb61a8bb4b61ffa8f14ab71e1442a141bef9b42074c99ab351cd5c619bae764"
    ),
    "FACTOR:CN-A:SZSE:002822:2025-12-30": reference(
        "4.07", "3.84", "8298a9c77647537646afb9861419607dc890a4198433fe622af8955dcd3f9c52"
    ),
    "FACTOR:CN-A:SZSE:300010:2023-12-27": reference(
        "2.68", "2.52", "e3682eb3e5477243eef493b05e9d5f52d13e8f6c9d69db89509fd60987fd9423"
    ),
    "FACTOR:CN-A:SZSE:300093:2025-11-20": reference(
        "14.83", "13.06", "08c024273da2ffccba91a6959d3230de52f795a583213da276971be2b7060c5e"
    ),
    "FACTOR:CN-A:SZSE:300125:2025-12-29": reference(
        "7.86", "6.22", "c8391c1d1f7a65691d937d8597358ee0fd1b33ca5eb44f44d3d79e9eda0bc9f7"
    ),
    "FACTOR:CN-A:SZSE:300159:2025-12-24": reference(
        "3.39", "2.88", "b52b60f527898c6473eaf593e5be58f9a5364c50aaec26a1eb972143ce049e49"
    ),
    "FACTOR:CN-A:SZSE:300209:2024-12-20": reference(
        "6.29", "4.79", "4c29458ef3f76c4ac72fde518152395b61bb095e2ae75d5222052a65d49474aa"
    ),
    "FACTOR:CN-A:SZSE:300370:2022-12-20": reference(
        "2.66", "2.64", "c971665f1d491060779a5add120192361820f6d1d213cc00fe6412cd697b1f22"
    ),
    "FACTOR:CN-A:SZSE:300506:2025-12-22": reference(
        "4.19", "3.16", "6310675f4254fc30c58c63dd4f703e1c33e1bf3d31a19c664434b60d4ed3e881"
    ),
}

DIRECT = {
    "FACTOR:CN-A:SZSE:000017:2010-03-18": direct(
        "1.5149022",
        "06534c7a9a93f2ebe412ac6f115e8ee015fd8d3d31b8a29095a4c1922961106e",
        "流通A股股东每10股将获得以资本公积金定向转增的5.149022股",
        "当日公司股票不计算除权参考价",
        classification="OFFICIAL_A_SHARE_REFORM_PUBLIC_HOLDER_RATIO",
    ),
    "FACTOR:CN-A:SZSE:000564:2021-12-31": direct(
        "3.20357146",
        "b66ffd369504ba429bafab6740907b31f5c0eb4d70dd54f3f3f4d882aaa1f0b8",
        "合计转增股票数量13,181,773,325股",
        "现有总股本5,982,004,024股",
        classification="OFFICIAL_TOTAL_CAPITAL_RATIO_PROVIDER_NORMALIZATION",
    ),
    "FACTOR:CN-A:SZSE:000818:2011-01-25": direct(
        "1.4",
        "b95c752e22393e044434cfd0820e679ed6b6921bbd07a1c901c83bdf7384eebe",
        "每10股转增10股",
        "原股东实际获得转增股份数为转增股份的40%",
        classification="OFFICIAL_NET_RETAINED_HOLDER_RATIO",
    ),
    "FACTOR:CN-A:SZSE:002326:2019-09-30": direct(
        "1.1206188",
        "e55d958fc8de6141db8ce1513f08e1c1c6ac0a3b131092b2aab0a44b0f0e62f4",
        "其他股东每10股转增1.206188股",
        classification="OFFICIAL_DIRECTED_PUBLIC_HOLDER_RATIO",
    ),
}

CASH = {
    "FACTOR:CN-A:SZSE:000539:2013-07-03": {
        "expected_pre_close": "4.58",
        "cash_per_share": "0.104083",
        "bonus_share_ratio": "0",
        "source_sha256": "1519e532463aa4f4468240f5a687af2634543bfd35ea1155c97d28215236366e",
        "required_text": ("向其他股东持有的1,426,938,788股每10股派1.04083元人民币",),
        "classification": "OFFICIAL_ORDINARY_OTHER_HOLDER_GROSS_CASH",
    },
    "FACTOR:CN-A:SZSE:300018:2011-05-26": {
        "expected_pre_close": "13.74",
        "cash_per_share": "0.15",
        "bonus_share_ratio": "0",
        "source_sha256": "4abee59579afec817c7a290778b75486417b8e7b9cb634f557df6bd7fd16d363",
        "required_text": ("派1.50元", "现金(含税"),
        "classification": "OFFICIAL_GROSS_CASH_VISUALLY_DATED",
    },
}

DATES = {
    "FACTOR:CN-A:SSE:600710:2017-07-31": {
        "classification": "OFFICIAL_EX_DATE_TO_FIRST_RESUMPTION_FACTOR_BOUNDARY",
        "official_ex_date": "2017-06-09",
        "expected_pre_close": "9.36",
        "cash_per_share": "0.054",
        "bonus_share_ratio": "0",
        "source_sha256": "1ddc6bca3ac0d0ca7fe9d17f59a290e4197f4cb2ed797ec8acd4b787a0aa16a2",
        "required_text": ("除权(息)日", "2017/6/9", "每股派发现金红利0.054元"),
        "deferred": True,
    },
    "FACTOR:CN-A:SZSE:002311:2014-05-21": {
        "classification": "OFFICIAL_INTERNAL_YEAR_TYPO_RECONCILED",
        "expected_pre_close": "9.82",
        "cash_per_share": "0.12",
        "bonus_share_ratio": "0",
        "source_sha256": "b165329601f929f7dd1578802966485caa6c46912abcda9aea493a171621ed61",
        "required_text": ("股权登记日为:2014年05月20日", "除权除息日为:2013年05月21日"),
    },
    "FACTOR:CN-A:SZSE:300048:2011-03-28": {
        "classification": "OFFICIAL_INTERNAL_YEAR_TYPO_RECONCILED",
        "expected_pre_close": "54.07",
        "cash_per_share": "0.25",
        "bonus_share_ratio": "1",
        "source_sha256": "ce8dc3cd47c71da9f4afcf6acea2bba056ecb6b45fc2fd84e660cf38004ab51b",
        "required_text": ("除权除息日:2010年03月28日", "本次所转增股于2011年3月28日"),
    },
    "FACTOR:CN-A:SZSE:300191:2014-06-20": {
        "classification": "OFFICIAL_INTERNAL_YEAR_TYPO_RECONCILED",
        "expected_pre_close": "24.25",
        "cash_per_share": "0.03",
        "bonus_share_ratio": "0",
        "source_sha256": "2955f182b8bab4b5f4fb815d2383bb6cca6d029e424070baee43c4bb7d33c415",
        "required_text": ("股权登记日为:2014年6月19日", "除权除息日为:2013年6月20日"),
    },
    "FACTOR:CN-A:SZSE:300274:2013-05-29": {
        "classification": "OFFICIAL_EX_DATE_TO_FIRST_TRADED_SESSION_FACTOR_BOUNDARY",
        "official_ex_date": "2013-05-28",
        "expected_pre_close": "16.30",
        "cash_per_share": "0.05",
        "bonus_share_ratio": "0",
        "source_sha256": "3d21342246243b34c82f66ddcd9eedc0ee35976a400974bf4dbff4bd8cf3fc42",
        "required_text": ("除权除息日为:2013年05月28日",),
        "deferred": True,
    },
    "FACTOR:CN-A:SZSE:300300:2013-05-23": {
        "classification": "OFFICIAL_EX_DATE_TO_FIRST_TRADED_SESSION_FACTOR_BOUNDARY",
        "official_ex_date": "2013-05-22",
        "expected_pre_close": "17.26",
        "cash_per_share": "0.1",
        "bonus_share_ratio": "1.2",
        "source_sha256": "78c603366990c32b9fba8e808ae220f8e8461d63b42c8a166c4214947e7b1604",
        "required_text": ("除权除息日为:2013年5月22日", "每10股转增12.000000股"),
        "deferred": True,
    },
}


def official_source(event: str, item: dict, sources: dict[str, dict]) -> dict:
    source = sources.get(item["source_sha256"])
    if source is None:
        raise ValueError(f"REQUIRED_OFFICIAL_SOURCE_MISSING:{event}")
    missing = [value for value in item["required_text"] if value not in source["text"]]
    if missing:
        raise ValueError(f"REQUIRED_OFFICIAL_TERMS_MISSING:{event}:{missing}")
    return {key: source[key] for key in ("source_sha256", "source_url", "title", "text_source")}


def reference_price_parity(pre_close: Decimal, factor_step: Decimal, expected: Decimal) -> dict:
    implied = pre_close / factor_step
    return {
        "provider_implied_reference_price": str(implied),
        "official_reference_price": str(expected),
        "status": (
            "OFFICIAL_DECLARED_REFERENCE_DISPLAY_TICK_PARITY_PASS"
            if implied.quantize(PRICE_TICK, rounding=ROUND_HALF_UP) == expected
            else "OFFICIAL_DECLARED_REFERENCE_CONFLICT"
        ),
    }


def verify_visual_date_review(path: Path) -> dict:
    review = json.loads(path.read_bytes())
    if review.get("scope") != "DATE_COVERAGE_ONLY_NOT_ECONOMIC_TERMS_OR_ACCOUNTING":
        raise ValueError("DATE_REVIEW_SCOPE_INVALID")
    expected = {
        "symbol": "300018",
        "record_date": "2011-05-25",
        "ex_date": "2011-05-26",
        "source_sha256": CASH["FACTOR:CN-A:SZSE:300018:2011-05-26"]["source_sha256"],
    }
    matched = any(
        all(row.get(key) == value for key, value in expected.items()) for row in review["rows"]
    )
    if not matched:
        raise ValueError("REQUIRED_VISUAL_DATE_REVIEW_MISSING")
    return expected


def szse_trade_rows(root: Path, report: dict, symbol: str, start: str, end: str) -> list[dict]:
    receipts = {row["date"]: row for row in report["results"]}
    rows = []
    for day in sorted(day for day in receipts if start <= day <= end):
        path = root / f"{day}.xlsx"
        if sha256_file(path) != receipts[day]["source_sha256"]:
            raise ValueError("SZSE_DAILY_SOURCE_CHANGED")
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="Workbook contains no default style")
            workbook = load_workbook(BytesIO(path.read_bytes()), read_only=True, data_only=True)
        sheet = workbook.active
        sheet.reset_dimensions()
        values = sheet.values
        headers = tuple(next(values))
        for values_row in values:
            if values_row[1] == symbol:
                row = dict(zip(headers, values_row, strict=True))
                rows.append(
                    {
                        "date": day,
                        "volume": Decimal(str(row["成交量(万股)"]).replace(",", "")),
                    }
                )
                break
        workbook.close()
    return rows


def deferred_boundary(
    event: str,
    item: dict,
    sse_root: Path,
    sse_report: dict,
    szse_root: Path,
    szse_report: dict,
) -> dict:
    security_id, factor_day = event.removeprefix("FACTOR:").rsplit(":", 1)
    symbol = security_id.rsplit(":", 1)[-1]
    ex_date = item["official_ex_date"]
    if ":SSE:" in event:
        receipt = next(row for row in sse_report["results"] if row["symbol"] == symbol)
        path = sse_root / f"{symbol}.json"
        if sha256_file(path) != receipt["source_sha256"]:
            raise ValueError("SSE_DAILY_SOURCE_CHANGED")
        rows = [
            {"date": str(row[0]), "volume": Decimal(str(row[5]))}
            for row in json.loads(path.read_bytes())["kline"]
            if ex_date.replace("-", "") <= str(row[0]) <= factor_day.replace("-", "")
        ]
        rows = [
            {**row, "date": f"{row['date'][:4]}-{row['date'][4:6]}-{row['date'][6:]}"}
            for row in rows
        ]
    else:
        rows = szse_trade_rows(szse_root, szse_report, symbol, ex_date, factor_day)
    before = [row for row in rows if row["date"] < factor_day]
    current = [row for row in rows if row["date"] == factor_day]
    if any(row["volume"] > 0 for row in before) or len(current) != 1 or current[0]["volume"] <= 0:
        raise ValueError(f"NOT_FIRST_TRADED_SESSION:{event}")
    return {
        "official_ex_date": ex_date,
        "factor_effective_first_traded_session": factor_day,
        "nontrading_rows_between": len(before),
        "status": "OFFICIAL_DEFERRED_TO_FIRST_TRADED_SESSION_PASS",
    }


def audit(
    adjustment: dict,
    residual: dict,
    sources: dict[str, dict],
    pre_closes: dict[tuple[str, str], Decimal],
    sse_root: Path,
    sse_report: dict,
    szse_root: Path,
    szse_report: dict,
) -> dict:
    steps = factor_steps(adjustment)
    expected = set(REFERENCES) | set(DIRECT) | set(CASH) | set(DATES)
    actual = {row["factor_change"] for row in residual["rows"]}
    if actual != expected or len(actual) != 35:
        raise ValueError("RETAINED_RESIDUAL_SCOPE_CHANGED")
    rows = []
    for event, item in sorted(REFERENCES.items()):
        security_id, day = event.removeprefix("FACTOR:").rsplit(":", 1)
        symbol = security_id.rsplit(":", 1)[-1]
        pre_close = pre_closes.get((symbol, day))
        if pre_close != Decimal(item["expected_pre_close"]):
            raise ValueError(f"OFFICIAL_RAW_PRE_CLOSE_CHANGED:{event}")
        expected_reference = Decimal(item["expected_reference_price"])
        result = reference_price_parity(pre_close, steps[security_id, day], expected_reference)
        rows.append(
            {
                "factor_change": event,
                "classification": item["kind"],
                **official_source(event, item, sources),
                "pre_close": str(pre_close),
                "observed_factor_step": str(steps[security_id, day]),
                **result,
            }
        )
    for event, item in sorted(DIRECT.items()):
        security_id, day = event.removeprefix("FACTOR:").rsplit(":", 1)
        rows.append(
            {
                "factor_change": event,
                "classification": item["classification"],
                **official_source(event, item, sources),
                **parity(steps[security_id, day], Decimal(item["expected_factor_step"])),
            }
        )
    for group in (CASH, DATES):
        for event, item in sorted(group.items()):
            security_id, day = event.removeprefix("FACTOR:").rsplit(":", 1)
            symbol = security_id.rsplit(":", 1)[-1]
            pre_close = pre_closes.get((symbol, day))
            if pre_close != Decimal(item["expected_pre_close"]):
                raise ValueError(f"OFFICIAL_RAW_PRE_CLOSE_CHANGED:{event}")
            result = economics(
                pre_close,
                Decimal(item["cash_per_share"]),
                Decimal(item["bonus_share_ratio"]),
                steps[security_id, day],
            )
            if "PASS" not in result["status"]:
                raise ValueError(f"OFFICIAL_TERMS_FACTOR_CONFLICT:{event}")
            boundary = (
                deferred_boundary(event, item, sse_root, sse_report, szse_root, szse_report)
                if item.get("deferred")
                else {}
            )
            rows.append(
                {
                    "factor_change": event,
                    "classification": item["classification"],
                    **official_source(event, item, sources),
                    "pre_close": str(pre_close),
                    "cash_per_share": item["cash_per_share"],
                    "bonus_share_ratio": item["bonus_share_ratio"],
                    **result,
                    **boundary,
                }
            )
    rows.sort(key=lambda row: row["factor_change"])
    failures = [row for row in rows if "PASS" not in row["status"]]
    return {
        "report_id": "FULL_ADJUSTMENT_REMAINING_MECHANICS_V1",
        "status": "OFFICIAL_REMAINING_MECHANICS_PASS" if not failures else "PARTIAL",
        "residual_factor_changes": len(rows),
        "counts": dict(sorted(Counter(row["classification"] for row in rows).items())),
        "failed_factor_changes": [row["factor_change"] for row in failures],
        "rows": rows,
        "factor_tolerance": "3e-8",
        "adjustment_authority_promoted": False,
        "dataset_created": False,
        "limitations": [
            "Factor alignment establishes feature-series normalization only; it creates no cash, "
            "share entitlement, or portfolio corporate action.",
            "Official ex-dates remain authoritative when a provider factor is deferred to the "
            "first positive-volume session.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adjustment", type=Path, required=True)
    parser.add_argument("--residual", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, action="append", required=True)
    parser.add_argument("--szse-root", type=Path, required=True)
    parser.add_argument("--szse-report", type=Path, required=True)
    parser.add_argument("--sse-root", type=Path, required=True)
    parser.add_argument("--sse-report", type=Path, required=True)
    parser.add_argument("--date-review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    adjustment, residual = map(verified, (args.adjustment, args.residual))
    verify_visual_date_review(args.date_review)
    wanted = {
        item["source_sha256"]
        for group in (REFERENCES, DIRECT, CASH, DATES)
        for item in group.values()
    }
    sources = source_texts(args.source_manifest, wanted)
    requests = {
        (event.split(":")[-2], event.rsplit(":", 1)[-1])
        for event in set(REFERENCES) | set(CASH) | set(DATES)
    }
    szse_report = json.loads(args.szse_report.read_bytes())
    sse_report = json.loads(args.sse_report.read_bytes())
    pre_closes = {
        **szse_pre_closes(
            args.szse_root,
            szse_report,
            {item for item in requests if item[0].startswith(("0", "3"))},
        ),
        **sse_pre_closes(
            args.sse_root,
            sse_report,
            {item for item in requests if not item[0].startswith(("0", "3"))},
        ),
    }
    report = audit(
        adjustment,
        residual,
        sources,
        pre_closes,
        args.sse_root,
        sse_report,
        args.szse_root,
        szse_report,
    )
    replay = audit(
        dict(adjustment, intervals=list(reversed(adjustment["intervals"]))),
        dict(residual, rows=list(reversed(residual["rows"]))),
        dict(reversed(list(sources.items()))),
        pre_closes,
        args.sse_root,
        sse_report,
        args.szse_root,
        szse_report,
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        input_order_reproducibility="PASS",
        inputs=[
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (
                args.adjustment,
                args.residual,
                *sorted(args.source_manifest),
                args.szse_report,
                args.sse_report,
                args.date_review,
            )
        ],
        parser_sha256=sha256_file(Path(__file__)),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "residual_factor_changes": report["residual_factor_changes"],
                "failed_factor_changes": report["failed_factor_changes"],
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
