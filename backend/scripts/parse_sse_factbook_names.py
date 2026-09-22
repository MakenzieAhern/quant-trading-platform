"""Dated annual name-table cross-check evidence, never undated ordering or admission."""

import argparse
import json
import re
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.sse_st_events import status


def name_row(line):
    line = re.sub(r"(?<=ST)\s+(?=[\u4e00-\u9fff])", "", line)
    found = re.fullmatch(
        r"\s*(?:\d{1,3}\s+)?(\d{6})(?:\.SH)?\s+(\d{4})[-/](\d{1,2})[-/](\d{1,2})\s+(\S+)\s+(\S+)\s*",
        line,
    )
    if not found:
        raise ValueError("NAME_TABLE_ROW_UNRESOLVED")
    code, year, month, day, new, old = found.groups()
    return dict(
        symbol=code,
        effective_date=date(int(year), int(month), int(day)).isoformat(),
        old_name=old,
        new_name=new,
        old_status=status(old),
        new_status=status(new),
    )


def name_pages(pages):
    active = False
    for number, text in enumerate(pages, 1):
        compact = re.sub(r"\s+", "", text)
        header = any(
            value in compact
            for value in ("更名日期新股票简称原股票简称", "更名日期新A股简称原A股简称")
        )
        content = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
            and line.strip() != "上市公司"
            and "市场资料" not in line
            and not line.strip().isdigit()
        ]
        continuation = (
            active
            and content
            and re.match(r"(?:\d{1,3}\s+)?\d{6}(?:\.SH)?\s+\d{4}[-/]", content[0])
        )
        active = bool(header or continuation)
        if active:
            yield number, text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    source_path = args.root / "factbook-index-snapshot-v1/source-manifest.json"
    sources = json.loads(source_path.read_bytes())
    results = []
    for source in sorted(sources["documents"], key=lambda r: r["issuer"]):
        pdf = Path(source["source_path"])
        if sha256_file(pdf) != source["source_sha256"]:
            raise ValueError("FACTBOOK_SOURCE_CHANGED")
        cache = args.root / "batch-v1/text" / f"{source['source_sha256']}.json"
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != source["source_sha256"]:
            raise ValueError("FACTBOOK_TEXT_IDENTITY_CHANGED")
        expected_year = int(source["issuer"][-4:]) - 1
        records, errors, pages = [], [], []
        for number, text in name_pages(extracted["pages"]):
            pages.append(number)
            for line in text.splitlines():
                if not re.match(r"\s*(?:\d{1,3}\s+)?\d{6}(?:\.SH)?\s", line):
                    continue
                try:
                    row = name_row(line)
                except ValueError as exc:
                    errors.append(dict(page=number, raw_line=line, error=str(exc)))
                    continue
                row.update(
                    page=number,
                    raw_line=line,
                    outside_caption_year=not row["effective_date"].startswith(str(expected_year)),
                    ordinary_a_code_candidate=row["symbol"].startswith("6"),
                )
                row["evidence_sha256"] = canonical_sha256(
                    dict(row, source_sha256=source["source_sha256"])
                )
                records.append(row)
        results.append(
            dict(
                year=expected_year,
                source=source,
                extraction_sha256=sha256_file(cache),
                pages=pages,
                records=records,
                errors=errors,
                source_publication_date=None,
            )
        )
    report = dict(
        results=results,
        source_manifest_sha256=sha256_file(source_path),
        parser_sha256=sha256_file(Path(__file__)),
        accepted_events=0,
        scope="DATED_TABLE_CROSSCHECK_NOT_COMPLETE_ST_LEDGER_OR_ADMISSION",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.root / "factbook-names-v2.json", canonical_json_bytes(report) + b"\n")
    print([(r["year"], len(r["records"]), len(r["errors"])) for r in results])


if __name__ == "__main__":
    main()
