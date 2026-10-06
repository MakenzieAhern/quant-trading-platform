"""Cross-check a retrospective official SZSE bonus table, never admit economic events."""

import argparse
import json
import re
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_distribution_cash import verified

NUMBER = r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?"
DAY = r"\d{4}-\d{1,2}-\d{1,2}"
ROW = re.compile(rf"^(\d{{6}})\s+(.+?)\s+({NUMBER})\s+({DAY})\s+({DAY})\s+({DAY})\s+({NUMBER})$")


def parse_bonus_section(pages: list[str], year: int) -> list[dict]:
    """Keep PDF page boundaries and reject every unparsed security-code row."""
    found = ended = False
    rows = []
    for number, page in enumerate(pages, 1):
        page = unicodedata.normalize("NFKC", page)
        compact = re.sub(r"\s+", "", page)
        if not found:
            if not all(
                token in compact
                for token in (
                    "4.11B深市上市公司送股一览表",
                    "每10股送股或转",
                    "赠股数(股)",
                    "股权登记日",
                    "除权日",
                    "红股上市日",
                )
            ):
                continue
            found = True
            page = page[page.index("4.11B") :]
        if "4.12A" in page:
            page = page[: page.index("4.12A")]
            ended = True
        for line in page.splitlines():
            line = line.strip()
            if not re.match(r"^\d{6}", line):
                continue
            match = ROW.fullmatch(line)
            if not match:
                raise ValueError("YEARBOOK_UNPARSED_ROW")
            symbol, name, shares, recorded, ex, listed, total = match.groups()
            dates = [date(*map(int, value.split("-"))) for value in (recorded, ex, listed)]
            if any(value.year != year for value in dates):
                raise ValueError("YEARBOOK_ROW_YEAR_MISMATCH")
            if symbol.startswith(("0", "3")) and not dates[0] < dates[1] <= dates[2]:
                raise ValueError("YEARBOOK_ROW_DATE_ORDER")
            if not symbol.startswith(("0", "2", "3")):
                raise ValueError("YEARBOOK_NOT_SZSE_SECURITY")
            if Decimal(shares.replace(",", "")) <= 0:
                raise ValueError("YEARBOOK_INVALID_BONUS_QUANTITY")
            rows.append(
                dict(
                    symbol=symbol,
                    source_observed_name=name,
                    bonus_shares_per_ten=str(Decimal(shares.replace(",", ""))),
                    record_date=dates[0].isoformat(),
                    ex_date=dates[1].isoformat(),
                    declared_listing_date=dates[2].isoformat(),
                    annual_bonus_total_ten_thousand_shares=str(Decimal(total.replace(",", ""))),
                    pdf_page=number,
                    source_line=line,
                )
            )
        if ended:
            break
    if not found:
        raise ValueError("YEARBOOK_SECTION_HEADER_UNRESOLVED")
    if not ended or not rows:
        raise ValueError("YEARBOOK_SECTION_END_UNRESOLVED")
    keys = [(row["symbol"], row["record_date"], row["ex_date"]) for row in rows]
    if len(set(keys)) != len(keys):
        raise ValueError("YEARBOOK_DUPLICATE_EVENT")
    return sorted(rows, key=lambda row: (row["symbol"], row["record_date"], row["ex_date"]))


def coverage_gaps(rows: list[dict], oracle: list[dict]) -> list[dict]:
    """Keep 0/3-code candidates, not an instrument-type or stable-ID admission."""
    present = {(row["symbol"], row["ex_date"]) for row in oracle}
    return sorted(
        (
            row
            for row in rows
            if row["symbol"].startswith(("0", "3"))
            and (row["symbol"], row["ex_date"]) not in present
        ),
        key=lambda row: (row["symbol"], row["record_date"], row["ex_date"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta_path = Path(str(args.pdf) + ".meta.json")
    meta = json.loads(meta_path.read_bytes())
    url = urlsplit(meta["url"])
    if (
        url.scheme != "https"
        or url.netloc != "www.chinaclear.cn"
        or not url.path.endswith(".pdf")
        or meta.get("http_status") != 200
        or meta.get("error")
        or meta["sha256"] != sha256_file(args.pdf)
        or datetime.fromisoformat(meta["retrieved_at_utc"]).utcoffset() is None
    ):
        raise ValueError("YEARBOOK_OFFICIAL_SOURCE_NOT_VERIFIED")
    import pymupdf

    with pymupdf.open(args.pdf) as doc:
        pages = [page.get_text(sort=True) for page in doc]
    rows = parse_bonus_section(pages, args.year)
    oracle = verified(args.oracle)
    gaps = coverage_gaps(rows, oracle["rows"])
    if gaps != coverage_gaps(list(reversed(rows)), list(reversed(oracle["rows"]))):
        raise ValueError("YEARBOOK_INPUT_ORDER_MISMATCH")
    report = dict(
        parser_version="CSDCC_SZSE_BONUS_COVERAGE_ORACLE_V1",
        scope="RETROSPECTIVE_COVERAGE_ORACLE_NOT_PIT_OR_EVENT_ADMISSION",
        year=args.year,
        official_source=meta,
        rows=rows,
        source_only_rows=gaps,
        input_order_reproducibility="PASS",
        accepted_events=0,
        dataset_created=False,
        limitations=[
            "CODE_PREFIX_AND_OBSERVED_NAME_ARE_NOT_PIT_INSTRUMENT_AUTHORITY",
            "CONTEMPORANEOUS_FINAL_AND_CORRECTION_CHAIN_REQUIRED",
            "ANNUAL_TOTAL_IS_NOT_EVENT_ENTITLEMENT_QUANTITY",
            "DECLARED_LISTING_DATE_IS_NOT_UNRESTRICTED_ALL_HOLDER_AUTHORITY",
            "NO_CASH_OR_OTHER_ACTION_CLASS_COMPLETENESS_CLAIM",
        ],
        inputs=[
            dict(path=str(path), sha256=sha256_file(path))
            for path in (args.pdf, meta_path, args.oracle, Path(__file__))
        ],
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            dict(rows=len(rows), source_only=len(gaps), manifest_sha256=report["manifest_sha256"])
        )
    )


if __name__ == "__main__":
    main()
