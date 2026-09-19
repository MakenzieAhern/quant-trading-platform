"""Bind exact official CNINFO resumption dates to unresolved SZSE suspensions."""

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

TERM = r"(?:复牌|恢复(?:正常)?交易)"
SUBJECT = r"(?:本公司|公司)?(?:股票|证券|A股股票|B股股票|A股|B股)"
FULL_DATE = r"(20\d{2})[年./-](\d{1,2})[月./-](\d{1,2})日?"
MONTH_DAY = r"(?<![年\d])(\d{1,2})月(\d{1,2})日"
REJECTED_TITLE = re.compile(r"延期复牌|继续停牌|停牌期满|暂不复牌|不复牌|申请复牌")
UNCERTAIN = re.compile(r"预计|不迟于|不晚于|最迟于|最晚于|争取|拟于")
CONDITIONAL = re.compile(r"若|如果|如未")
FULL_PATTERNS = (
    re.compile(r"进入退市整理期(?:交易)?的起始日为" + FULL_DATE),
    re.compile(r"(?:并)?将于" + FULL_DATE + r"[^。\uff1b;]{0,30}?" + TERM),
    re.compile(
        SUBJECT
        + r"[^。\uff1b;]{0,80}?(?:将于|自|于|从|并于)"
        + FULL_DATE
        + r"[^。\uff1b;]{0,30}?"
        + TERM
    ),
    re.compile(
        FULL_DATE
        + r"[^。\uff1b;]{0,20}?(?:开市|上午|下午|[0-9:\uff1a时分]|起){1,8}"
        + r"[^。\uff1b;]{0,10}?"
        + TERM
    ),
    re.compile(
        r"(?:本公司|公司)将于"
        + FULL_DATE
        + r"[^。\uff1b;]{0,50}?(?:公告|披露)[^。\uff1b;]{0,10}?(?:并)?复牌"
    ),
    re.compile(FULL_DATE + r"[^。\uff1b;]{0,60}?" + SUBJECT + r"[^。\uff1b;]{0,20}?同日复牌"),
    re.compile(r"(?=(" + FULL_DATE + r"[^。\uff1b;]{0,40}?" + TERM + r"))"),
    re.compile(TERM + r"(?:时间)?(?:为|定为|安排为)[:\uff1a]?" + FULL_DATE),
)
MONTH_DAY_PATTERNS = (
    re.compile(r"(?:并)?将于" + MONTH_DAY + r"[^。\uff1b;]{0,30}?" + TERM),
    re.compile(
        SUBJECT
        + r"[^。\uff1b;]{0,80}?(?:将于|自|于|从|并于)"
        + MONTH_DAY
        + r"[^。\uff1b;]{0,30}?"
        + TERM
    ),
    re.compile(
        MONTH_DAY
        + r"[^。\uff1b;]{0,20}?(?:开市|上午|下午|[0-9:\uff1a时分]|起){1,8}"
        + r"[^。\uff1b;]{0,10}?"
        + TERM
    ),
    re.compile(r"(?=(" + MONTH_DAY + r"[^。\uff1b;]{0,40}?" + TERM + r"))"),
)
RELATIVE_PATTERNS = (
    re.compile(
        SUBJECT + r"[^。\uff1b;]{0,80}?(?:将于|自|于|从)(?:本)?公告"
        r"(?:刊登|披露|发布|公布)?(?:之|当)?日(?:起|开市(?:起|时)?)?" + TERM
    ),
    re.compile(
        r"自(?:本)?公告(?:刊登|披露|发布|公布)?(?:之|当)?日(?:起|开市(?:起|时)?)?"
        r"(?:公司)?股票?" + TERM
    ),
)
RESTORATION_REJECTED = re.compile(r"申请|受理|进展|保荐|督导|措施|暂停上市|无法|争取")
RESTORATION_PATTERNS = (
    re.compile(
        SUBJECT
        + r"[^。\uff1b;]{0,80}?(?:将于|于|自)"
        + FULL_DATE
        + r"起[^。\uff1b;]{0,35}?恢复上市(?:交易)?"
    ),
    re.compile(
        FULL_DATE + r"(?:起)?[^。\uff1b;]{0,25}?" + SUBJECT + r"[^。\uff1b;]{0,35}?恢复上市交易"
    ),
)
INTRADAY_PATTERNS = (
    re.compile(
        FULL_DATE
        + r"[^。\uff1b;]{0,25}?上午[^。\uff1b;]{0,15}?停牌"
        + r"[^。\uff1b;]{0,25}?下午[^。\uff1b;]{0,15}?复牌"
    ),
    re.compile(FULL_DATE + r"[^。\uff1b;]{0,25}?停牌(?:一小时|半天)后复牌"),
)


def _near_publication(day: date, published: date) -> bool:
    return -1 <= (day - published).days <= 14


def _match_text(match: re.Match) -> str:
    return match.group(0) or match.group(1)


def _is_certain(segment: str, match: re.Match) -> bool:
    text = _match_text(match)
    context = segment[max(0, match.start() - 10) : match.start()] + text
    wide_context = segment[max(0, match.start() - 40) : match.start()] + text
    final_after_application = bool(
        re.search(r"经(?:公司)?申请", wide_context)
        and re.search(SUBJECT + r"将于" + FULL_DATE + r"[^。\uff1b;]{0,30}?" + TERM, text)
    )
    return (
        not UNCERTAIN.search(context)
        and not CONDITIONAL.search(wide_context)
        and len(re.findall(FULL_DATE, text)) + len(re.findall(MONTH_DAY, text)) <= 1
        and not re.search(r"停牌|会议|议案", text)
        and (final_after_application or not re.search(r"申请[^。\uff1b;]{0,30}复牌", wide_context))
        and not re.search(r"(?:但是|但|然而).*?停牌", segment[match.end() :])
        and not ("B股" in segment and "A股" not in segment)
    )


def exact_resume_dates(text: str, published_on: str) -> list[str]:
    published = date.fromisoformat(published_on)
    values = set()
    fallback_values = set()
    compact = re.sub(r"\s+", "", text)
    for segment in re.split(r"[。\uff01\uff1f\uff1b;]", compact):
        for pattern in INTRADAY_PATTERNS:
            for match in pattern.finditer(segment):
                try:
                    values.add(date(*map(int, match.groups()[-3:])).isoformat())
                except ValueError:
                    continue
        for index, pattern in enumerate(FULL_PATTERNS):
            for match in pattern.finditer(segment):
                if not _is_certain(segment, match):
                    continue
                try:
                    day = date(*map(int, match.groups()[-3:]))
                except ValueError:
                    continue
                if _near_publication(day, published):
                    (fallback_values if index == 6 else values).add(day.isoformat())
        for index, pattern in enumerate(MONTH_DAY_PATTERNS):
            for match in pattern.finditer(segment):
                if not _is_certain(segment, match):
                    continue
                month, day_number = map(int, match.groups()[-2:])
                candidates = []
                for year in (published.year - 1, published.year, published.year + 1):
                    try:
                        day = date(year, month, day_number)
                    except ValueError:
                        continue
                    if _near_publication(day, published):
                        candidates.append(day)
                if len(candidates) == 1:
                    (fallback_values if index == 3 else values).add(candidates[0].isoformat())
        for pattern in RELATIVE_PATTERNS:
            match = pattern.search(segment)
            if match and _is_certain(segment, match):
                values.add(published.isoformat())
    return sorted(values or fallback_values)


def _restoration_dates(compact: str) -> list[str]:
    values = set()
    for segment in re.split(r"[。\uff01\uff1f\uff1b;]", compact):
        for pattern in RESTORATION_PATTERNS:
            for match in pattern.finditer(segment):
                evidence = _match_text(match)
                if RESTORATION_REJECTED.search(evidence):
                    continue
                try:
                    values.add(date(*map(int, match.groups()[-3:])).isoformat())
                except ValueError:
                    continue
    return sorted(values)


def continued_halt_restoration_dates(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    return _restoration_dates(compact) if "继续停牌" in compact else []


def exact_restoration_dates(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", text)
    return [] if "继续停牌" in compact else _restoration_dates(compact)


def official_document_text(root: Path, document: dict) -> str:
    source = root / document["source_path"]
    if sha256_file(source) != document["source_sha256"]:
        raise ValueError("RESUMPTION_SOURCE_CHANGED")
    if document["retrieval_status"] == "NON_PDF_ATTACHMENT":
        if not document["url"].endswith(".js"):
            raise ValueError("UNSUPPORTED_RESUMPTION_ATTACHMENT")
        wrapper = source.read_bytes().decode("gb18030")
        match = re.fullmatch(r"\s*var\s+affiches\s*=\s*(\[.*\])\s*;\s*", wrapper, re.S)
        if match is None:
            raise ValueError("INVALID_CNINFO_JS_ATTACHMENT")
        rows = json.loads(match.group(1))
        if not rows or any(not isinstance(row.get("Zw"), str) for row in rows):
            raise ValueError("INVALID_CNINFO_JS_CONTENT")
        return "\n".join(row["Zw"] for row in rows)
    cache = root / "batch-v1/text" / f"{document['source_sha256']}.json"
    if not cache.exists():
        raise ValueError("RESUMPTION_EXTRACTION_MISSING")
    extracted = json.loads(cache.read_bytes())
    if extracted["source_sha256"] != document["source_sha256"]:
        raise ValueError("RESUMPTION_EXTRACTION_CHANGED")
    return "\n".join(extracted["pages"])


def bind_resumptions(unresolved: list[dict], events: list[dict], evidence: list[dict]):
    starts = defaultdict(list)
    for event in events:
        starts[event["symbol"]].append(event["suspended_at"][:10].replace("/", "-"))
    by_symbol = defaultdict(lambda: defaultdict(list))
    for row in evidence:
        by_symbol[row["symbol"]][row["resumed_at"]].append(row)

    accepted, remaining = [], []
    for fact in sorted(unresolved, key=lambda row: (row["suspended_at"], row["security_id"])):
        start = fact["suspended_at"][:10].replace("/", "-")
        next_start = min((day for day in starts[fact["symbol"]] if day > start), default=None)
        candidates = sorted(
            day
            for day in by_symbol[fact["symbol"]]
            if day >= start and (next_start is None or day < next_start)
        )
        if not candidates:
            remaining.append(fact)
            continue
        resumed_at = candidates[0]
        sources = sorted(
            by_symbol[fact["symbol"]][resumed_at],
            key=canonical_json_bytes,
        )
        accepted.append(
            {
                "security_id": fact["security_id"],
                "symbol": fact["symbol"],
                "suspended_at": fact["suspended_at"],
                "resumed_at": resumed_at,
                "binding_policy": "EARLIEST_EXACT_RESUMPTION_BEFORE_NEXT_SUSPENSION_V1",
                "evidence": sources,
            }
        )
    return accepted, remaining


def unresolved_facts(value: list[dict] | dict) -> list[dict]:
    return value["remaining_unresolved"] if isinstance(value, dict) else value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", default="batch-v1")
    parser.add_argument("--suspensions", type=Path, required=True)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    source_manifest_path = args.root / args.batch / "source-manifest.json"
    source_manifest = json.loads(source_manifest_path.read_bytes())
    suspensions = json.loads(args.suspensions.read_bytes())["szse"]
    unresolved = unresolved_facts(json.loads(args.unresolved.read_bytes()))
    evidence, document_results, continued_halts = [], [], {}
    for document in source_manifest["documents"]:
        result = {
            "source_sha256": document.get("source_sha256"),
            "issuer": document["issuer"],
            "title": document["title"],
        }
        if document["retrieval_status"] not in {"PASS", "NON_PDF_ATTACHMENT"}:
            result["status"] = document["retrieval_status"]
        elif REJECTED_TITLE.search(document["title"]):
            result["status"] = "NOT_FINAL_RESUMPTION_TITLE"
        elif "债券" in document["title"] and not re.search(r"股票|A股", document["title"]):
            result["status"] = "NON_EQUITY_RESUMPTION"
        else:
            text = official_document_text(args.root, document)
            marker = (document["published_on"], document["source_sha256"])
            for day in continued_halt_restoration_dates(text):
                key = (document["issuer"], day)
                continued_halts[key] = max(continued_halts.get(key, ("", "")), marker)
            dates = sorted(
                set(exact_resume_dates(text, document["published_on"]))
                | set(exact_restoration_dates(text))
            )
            result["dates"] = dates
            result["status"] = (
                "EXACT_OFFICIAL_RESUMPTION_DATE"
                if len(dates) == 1
                else "AMBIGUOUS_RESUMPTION_DATES"
                if dates
                else "NO_EXACT_RESUMPTION_DATE"
            )
            if len(dates) == 1:
                evidence.append(
                    {
                        "symbol": document["issuer"],
                        "resumed_at": dates[0],
                        "title": document["title"],
                        "url": document["url"],
                        "published_on": document["published_on"],
                        "retrieved_at_utc": document["retrieved_at_utc"],
                        "source_sha256": document["source_sha256"],
                    }
                )
        document_results.append(result)

    evidence = [
        row
        for row in evidence
        if (row["published_on"], row["source_sha256"])
        > continued_halts.get((row["symbol"], row["resumed_at"]), ("", ""))
    ]
    evidence.sort(key=lambda row: (row["symbol"], row["resumed_at"], row["source_sha256"]))
    accepted, remaining = bind_resumptions(unresolved, suspensions, evidence)
    reversed_result = bind_resumptions(
        list(reversed(unresolved)), list(reversed(suspensions)), list(reversed(evidence))
    )
    if (accepted, remaining) != reversed_result:
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "parser_version": "SZSE_EXACT_OFFICIAL_RESUMPTION_RECONCILIATION_V10",
        "parser_sha256": sha256_file(Path(__file__)),
        "source_manifest_sha256": sha256_file(source_manifest_path),
        "suspensions_input_sha256": sha256_file(args.suspensions),
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "document_counts": dict(sorted(Counter(row["status"] for row in document_results).items())),
        "exact_resumption_documents": len(evidence),
        "accepted_resumptions": accepted,
        "remaining_unresolved": remaining,
        "accepted_count": len(accepted),
        "remaining_count": len(remaining),
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if not isinstance(value, list)},
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
