"""Audit retained provider factors against official special-action mechanics."""

import argparse
import json
import re
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal, localcontext
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_adjustment_factor_economics import factor_steps, sse_pre_closes
from scripts.audit_adjustment_gap_candidate_terms import cache_index, pages_for
from scripts.build_cash_gap_queue import verified

TOLERANCE = Decimal("3e-8")
PRICE_TICK = Decimal("0.01")


def direct(step: str, source: str, *required: str, classification: str) -> dict:
    return {
        "kind": "DIRECT_FACTOR_STEP",
        "expected_factor_step": step,
        "source_sha256": source,
        "required_text": required,
        "classification": classification,
    }


def formula(
    old_shares: int,
    consideration: tuple[str, ...],
    added_shares: int,
    source: str,
    *required: str,
) -> dict:
    return {
        "kind": "OFFICIAL_REFERENCE_PRICE_FORMULA",
        "old_shares": old_shares,
        "consideration": consideration,
        "added_shares": added_shares,
        "source_sha256": source,
        "required_text": required,
        "classification": "OFFICIAL_RESTRUCTURING_REFERENCE_PRICE_FORMULA",
    }


EVENTS = {
    "FACTOR:CN-A:SSE:600165:2025-12-11": formula(
        684_883_775,
        ("576358452.00", "1241323635.04"),
        48_029_871 + 882_970_129,
        "4bc14a97f1dc188163d8e25437f5462a29fefa4d39c699394ead9e70fed0beff",
        "转增前总股本为684,883,775股",
        "转增股份抵偿公司及子公司债务的金额为576,358,452.00元",
        "重整投资人受让转增股份支付的现金为1,241,323,635.04元",
    ),
    "FACTOR:CN-A:SSE:600211:2010-09-07": direct(
        "1.1",
        "c10a9a3c7445705e37a0235a9f87260b7d7ee0b404411ade2834dace7566bb46",
        "每10股无限售条件流通股获转增1股股份",
        classification="OFFICIAL_PUBLIC_HOLDER_DIRECTED_CAPITAL_INCREASE",
    ),
    "FACTOR:CN-A:SSE:600225:2010-07-15": direct(
        "1.09281361",
        "6d5837f1330eab3c2639a7fed73a87bfe3275b1e202b9fd189891026c4e74447",
        "无限售流通股股东每10股定向转增0.9281361股",
        classification="OFFICIAL_PUBLIC_HOLDER_DIRECTED_CAPITAL_INCREASE",
    ),
    "FACTOR:CN-A:SSE:600306:2023-12-26": formula(
        231_574_918,
        ("262510687.50", "450000000.00"),
        116_481_537 + 80_357_144,
        "b7f98d058d66f4fdc210436cf94bb5e86db55705ee9b6badb77e063a1f9c6372",
        "转增前总股本为231,574,918股",
        "相应可抵偿债务的金额为262,510,687.50元",
        "重整投资者受让转增股份支付的现金为450,000,000.00元",
    ),
    "FACTOR:CN-A:SSE:600375:2024-12-26": formula(
        654_314_844,
        (str(433_370_916 * 8), "1765156821.00"),
        433_370_916 + 515_385_607,
        "98ec6d100268088fe6fc67390492b9ea3d4917c8d82c45a3fddfbef9822a64da",
        "433,370,916股*8元/股+1,765,156,821元",
        "433,370,916股+515,385,607股",
    ),
    "FACTOR:CN-A:SSE:600401:2014-06-12": direct(
        "1.044",
        "0c0309d409235fbedb1d114cadd6f980fd1d1062de614e87eb73e9ea03cde276",
        "总股本实际增加46,060,365股,实际增加比例为4.4%",
        classification="OFFICIAL_DIFFERENTIATED_CAPITAL_INCREASE",
    ),
    "FACTOR:CN-A:SSE:600423:2018-12-18": formula(
        399_347_513,
        (str(211_737_774 * Decimal("4.83")), str(187_609_739 * Decimal("3.22"))),
        211_737_774 + 187_609_739,
        "7a3f03ea4d7ac18c66d36598efbbb16f6251a4dbfc60ecd39a53bc8bc6412604",
        "抵偿债务部分的价格为4.83元/股",
        "重整投资人认购部分的价格为3.22元/股",
        "调整后的除权(息)参考价格为4.45元/股",
    ),
    "FACTOR:CN-A:SSE:600589:2023-12-29": formula(
        704_033_281,
        ("1082370405", "701350000"),
        709_436_609 + 65_000_000,
        "d408f5c7777135948d141d68afc674c6df010a81037559790cb5e570796b2540",
        "转增前总股本704,033,281股",
        "1,082,370,405元+701,350,000元",
    ),
    "FACTOR:CN-A:SSE:600601:2022-12-23": formula(
        2_194_891_204,
        ("2536558945", "1930000000"),
        1_975_402_083,
        "d795f29222cdb4053f6844394a08ec407047533a4477a19c6dba2cdd88196501",
        "抵偿债务金额为2,536,558,945元",
        "1,930,000,000元",
        "转增前总股本2,194,891,204股",
    ),
    "FACTOR:CN-A:SSE:600654:2022-12-23": formula(
        1_283_020_992,
        ("3126009734.40", "1200000000.00"),
        726_979_008 + 800_000_000,
        "61809045b8b70b0f908448f423e79712ad6f8789fe5314af42ef1a3da92e433e",
        "转增前总股本为1,283,020,992股",
        "转增股份抵偿债务的金额为3,126,009,734.40元",
        "重整投资者受让转增股份支付的现金为1,200,000,000.00元",
    ),
    "FACTOR:CN-A:SSE:600666:2023-02-20": formula(
        1_227_326_240,
        ("989465020.00", "483326468.00"),
        1_236_831_275 + 299_355_328,
        "970ef48e67afb4f92a54a08e18e702f5cda46b593fb56f546a291800b6e5f22f",
        "转增股份支付的现金为989,465,020.00元",
        "解决业绩承诺导致不公平让渡问题投入现金金额为483,326,468.00元",
        "1,227,326,240",
    ),
    "FACTOR:CN-A:SSE:600715:2024-12-16": formula(
        1_854_853_500,
        ("3012500000.00", "1066000000.00"),
        1_205_000_000 + 1_000_000_000,
        "f2f9d23deb7d8363fcd64829580414aaf8ca1b77008f97d41b4a1e16d5514dd8",
        "转增前总股本为1,854,853,500股",
        "3,012,500,000.00元+1,066,000,000.00元",
    ),
    "FACTOR:CN-A:SSE:600728:2010-06-08": direct(
        "1.9",
        "c067540623c268fd4fec2656ac7fc1e27fb70df8c8d74ffe204144d75b13c875",
        "向股改方案实施日登记在册的全体流通股股东每10股转增9股",
        classification="OFFICIAL_PUBLIC_HOLDER_DIRECTED_CAPITAL_INCREASE",
    ),
    "FACTOR:CN-A:SSE:600734:2022-02-15": formula(
        622_372_316,
        (str(Decimal("0.58") * 1_555_930_790),),
        1_555_930_790,
        "9e783ab3488159068e7a19d0dde8d953ea9f2ac588d971751d0dfa28da5c6582",
        "重整投资人受让的资本公积金转增股票价格为0.58元/股",
        "转增股份由重整投资人认购的股份数量为1,555,930,790股",
        "实达集团当前总股本为622,372,316股",
    ),
    "FACTOR:CN-A:SSE:600891:2011-02-28": direct(
        "1.5",
        "0fcd3afa084b378e2a9e93a12ed6dd97992b7295bd6b9d0fbaa325e3f776800f",
        "流通股东每10股转增5股",
        "本日股价不计算除权参考价",
        classification="OFFICIAL_PUBLIC_HOLDER_SHARE_REFORM_CONSIDERATION",
    ),
    "FACTOR:CN-A:SSE:603007:2024-12-26": formula(
        406_847_052,
        ("497817290.00", "409725470.08", "90414975.24"),
        49_781_729 + 377_065_323 + 43_201_997,
        "d71db0b45ec7b944e9987f23a24da40b56145133323eb3c1a744ae9d5bba9e8a",
        "497,817,290.00元+409,725,470.08元+90,414,975.24元",
        "49,781,729股+377,065,323股+43,201,997股",
    ),
    "FACTOR:CN-A:SSE:603030:2023-12-26": formula(
        678_403_329,
        ("518939946", "710000000"),
        649_089_991,
        "cc5e514813f749403f13087027873747da6662ec5b1c0b9b1fb27ccda5b7010c",
        "转增前总股本678,403,329股",
        "转增股份抵偿公司债务的金额为518,939,946元",
        "重整投资人受让转增股份支付的现金为710,000,000元",
    ),
    "FACTOR:CN-A:SSE:603559:2024-12-26": formula(
        143_313_207,
        ("615404575.18", "835629761.71"),
        45_350_374 + 212_613_398,
        "6e1653a57ece1523b7f4ab7fecfb01e457972172b0a0b26c810fb4eb7e559383",
        "转增前总股本为143,313,207股",
        "转增股份抵偿中通国脉债务的金额为615,404,575.18元",
        "重整投资者受让转增股份支付的现金为835,629,761.71元",
    ),
    "FACTOR:CN-A:SSE:688005:2025-03-06": direct(
        "1.4798",
        "62c167f736bbf62d5749fa14dc091addaef5cbf59e91cd2c2dfadc91ef837d32",
        "472,909,420\u00d70.49",
        "482,999,855≈0.4798",
        classification="OFFICIAL_DIFFERENTIATED_CAPITAL_INCREASE",
    ),
    "FACTOR:CN-A:SSE:688603:2025-01-06": direct(
        "1.4441",
        "3e65bff172eedd51fb3410d1572074d5109c3cf8aa7c807dc94980a83e33815c",
        "57,378,370\u00d70.45",
        "58,136,926≈0.4441",
        classification="OFFICIAL_DIFFERENTIATED_CAPITAL_INCREASE",
    ),
}


def source_texts(paths: list[Path], wanted: set[str] | None = None) -> dict[str, dict]:
    indexed = {}
    wanted = wanted or {item["source_sha256"] for item in EVENTS.values()}
    for path in sorted(paths):
        root = path.parent.parent
        payload = json.loads(path.read_bytes())
        documents = payload if isinstance(payload, list) else payload["documents"]
        caches = cache_index(root)
        for document in documents:
            if document.get("source_sha256") not in wanted:
                continue
            if document.get("retrieval_status") not in {"PASS", "PASS_RETAINED_OFFICIAL_BYTES"}:
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
            if any(
                prior[key] != row[key] for key in ("source_sha256", "source_url", "title", "text")
            ):
                raise ValueError("SOURCE_SHA_IDENTITY_CONFLICT")
    return indexed


def reference_parity(
    pre_close: Decimal,
    factor_step: Decimal,
    old_shares: int,
    consideration: tuple[str, ...],
    added_shares: int,
) -> dict:
    with localcontext() as context:
        context.prec = 50
        consideration_total = sum(map(Decimal, consideration), Decimal(0))
        average_price = consideration_total / Decimal(added_shares)
        reference = (pre_close * old_shares + consideration_total) / (old_shares + added_shares)
        implied = pre_close / factor_step
        delta = abs(reference - implied)
    if pre_close <= average_price:
        status = "OFFICIAL_FORMULA_TRIGGER_CONFLICT"
    elif delta <= TOLERANCE:
        status = "OFFICIAL_FORMULA_REFERENCE_PARITY_PASS"
    elif reference.quantize(PRICE_TICK, rounding=ROUND_HALF_UP) == implied.quantize(
        PRICE_TICK, rounding=ROUND_HALF_UP
    ):
        status = "OFFICIAL_FORMULA_DISPLAY_TICK_PARITY_PASS"
    else:
        status = "OFFICIAL_FORMULA_REFERENCE_PARITY_CONFLICT"
    return {
        "pre_close": str(pre_close),
        "official_average_consideration_price": str(average_price),
        "official_reference_price": str(reference),
        "official_reference_price_display": str(
            reference.quantize(PRICE_TICK, rounding=ROUND_HALF_UP)
        ),
        "provider_implied_reference_price": str(implied),
        "reference_price_absolute_delta": str(delta),
        "observed_factor_step": str(factor_step),
        "status": status,
    }


def audit(
    routing: dict,
    adjustment: dict,
    sources: dict[str, dict],
    pre_closes: dict[tuple[str, str], Decimal],
) -> dict:
    conflicts = {
        f"FACTOR:{row['security_id']}:{row['effective_date']}"
        for row in routing["rows"]
        if row.get("factor_economic_alignment_status") == "OFFICIAL_BONUS_FACTOR_ALIGNMENT_CONFLICT"
    }
    if conflicts != set(EVENTS):
        raise ValueError("SPECIAL_MECHANICS_SCOPE_CHANGED")
    steps = factor_steps(adjustment)
    rows = []
    for event, item in sorted(EVENTS.items()):
        source = sources.get(item["source_sha256"])
        if source is None:
            raise ValueError(f"REQUIRED_OFFICIAL_SOURCE_MISSING:{event}")
        missing = [text for text in item["required_text"] if text not in source["text"]]
        if missing:
            raise ValueError(f"REQUIRED_OFFICIAL_TERMS_MISSING:{event}:{missing}")
        security_id, day = event.removeprefix("FACTOR:").rsplit(":", 1)
        observed = steps[security_id, day]
        common = {
            "factor_change": event,
            "classification": item["classification"],
            **{key: source[key] for key in ("source_sha256", "source_url", "title", "text_source")},
        }
        if item["kind"] == "DIRECT_FACTOR_STEP":
            expected = Decimal(item["expected_factor_step"])
            delta = abs(observed - expected)
            rows.append(
                {
                    **common,
                    "expected_factor_step": str(expected),
                    "observed_factor_step": str(observed),
                    "absolute_delta": str(delta),
                    "status": (
                        "OFFICIAL_DIRECT_FACTOR_PARITY_PASS"
                        if delta <= TOLERANCE
                        else "OFFICIAL_DIRECT_FACTOR_PARITY_CONFLICT"
                    ),
                }
            )
            continue
        symbol = security_id.rsplit(":", 1)[-1]
        pre_close = pre_closes.get((symbol, day))
        if pre_close is None:
            raise ValueError(f"OFFICIAL_RAW_PRE_CLOSE_MISSING:{event}")
        rows.append(
            {
                **common,
                **reference_parity(
                    pre_close,
                    observed,
                    item["old_shares"],
                    item["consideration"],
                    item["added_shares"],
                ),
            }
        )
    counts = Counter(row["status"] for row in rows)
    passed = sum(value for key, value in counts.items() if key.endswith("PASS"))
    return {
        "report_id": "FULL_ADJUSTMENT_SPECIAL_MECHANICS_V1",
        "status": (
            "OFFICIAL_SPECIAL_MECHANICS_FACTOR_ALIGNMENT_PASS"
            if passed == len(rows)
            else "OFFICIAL_SPECIAL_MECHANICS_FACTOR_ALIGNMENT_PARTIAL"
        ),
        "special_factor_changes": len(rows),
        "passed_factor_changes": passed,
        "counts": dict(sorted(counts.items())),
        "rows": rows,
        "factor_tolerance": str(TOLERANCE),
        "price_tick": str(PRICE_TICK),
        "adjustment_authority_promoted": False,
        "dataset_created": False,
        "limitations": [
            "This audit validates provider normalization against official "
            "special-action mechanics.",
            "It does not create holder entitlements or accept a corporate-action census.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing", type=Path, required=True)
    parser.add_argument("--adjustment", type=Path, required=True)
    parser.add_argument("--source", type=Path, action="append", required=True)
    parser.add_argument("--sse-root", type=Path, required=True)
    parser.add_argument("--sse-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    routing, adjustment = verified(args.routing), verified(args.adjustment)
    sources = source_texts(args.source)
    requests = {
        (event.split(":")[-2], event.split(":")[-1])
        for event, item in EVENTS.items()
        if item["kind"] == "OFFICIAL_REFERENCE_PRICE_FORMULA"
    }
    pre_closes = sse_pre_closes(
        args.sse_root,
        json.loads(args.sse_report.read_bytes()),
        requests,
    )
    report = audit(routing, adjustment, sources, pre_closes)
    replay = audit(
        dict(routing, rows=list(reversed(routing["rows"]))),
        dict(adjustment, intervals=list(reversed(adjustment["intervals"]))),
        source_texts(list(reversed(args.source))),
        pre_closes,
    )
    if report != replay:
        raise ValueError("INPUT_ORDER_CHANGED")
    report.update(
        input_order_reproducibility="PASS",
        checksum_repeatability="PASS",
        inputs=[
            {"path": str(path), "sha256": sha256_file(path)}
            for path in (args.routing, args.adjustment, *sorted(args.source), args.sse_report)
        ],
        parser_sha256=sha256_file(Path(__file__)),
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "status",
                    "special_factor_changes",
                    "passed_factor_changes",
                    "counts",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
