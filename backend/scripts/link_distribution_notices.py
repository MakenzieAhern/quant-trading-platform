"""Link exchange dates to retained issuer notices; never infer or accept economic terms."""

import argparse
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def labeled_dates(text, label):
    compact = re.sub(r"\s+", "", unicodedata.normalize("NFKC", text))
    pattern = label + r"[:为]*(20\d{2})年(\d{1,2})月(\d{1,2})日"
    return sorted({date(*map(int, match)).isoformat() for match in re.findall(pattern, compact)})


def notice_dates(pages):
    # Require dates attached to labels, not unrelated dates elsewhere in an annual report.
    text = "\n".join(pages)
    return (
        labeled_dates(text, r"A股股权登记日") or labeled_dates(text, r"股权登记日"),
        labeled_dates(
            text, r"(?:除权\(除息\)日|除权\(除息日\)|除权\(息\)日|除权除息日|除息日|除权日)"
        ),
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--batch", required=True)
    parser.add_argument("--sse-audit", type=Path, required=True)
    parser.add_argument("--szse-audit", type=Path, required=True)
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    inputs = [args.root / args.batch / "source-manifest.json", args.sse_audit, args.szse_audit]
    manifests = []
    for path in inputs:
        value = json.loads(path.read_bytes())
        if (
            canonical_sha256({k: v for k, v in value.items() if k != "manifest_sha256"})
            != value["manifest_sha256"]
        ):
            raise ValueError("INPUT_MANIFEST_CHANGED")
        manifests.append(value)
    documents, sse, szse = manifests
    index = {}
    extraction_gaps = []
    parsing_errors = []
    for row in documents["documents"]:
        if row["retrieval_status"] != "PASS":
            continue
        pdf = args.root / row["source_path"]
        if sha256_file(pdf) != row["source_sha256"]:
            raise ValueError("PDF_CHANGED")
        cache = args.root / "batch-v1/text" / (row["source_sha256"] + ".json")
        if not cache.exists():
            extraction_gaps.append(row["source_sha256"])
            continue
        extracted = json.loads(cache.read_bytes())
        if extracted["source_sha256"] != row["source_sha256"]:
            raise ValueError("EXTRACTION_IDENTITY_CHANGED")
        try:
            record, ex = notice_dates(extracted["pages"])
        except ValueError as exc:
            parsing_errors.append(dict(source_sha256=row["source_sha256"], error=str(exc)))
            continue
        if len(record) == len(ex) == 1 and row["published_on"] <= record[0] < ex[0]:
            key = (row["issuer"], record[0], ex[0])
            index.setdefault(key, []).append(
                dict(
                    url=row["url"],
                    source_sha256=row["source_sha256"],
                    extraction_sha256=sha256_file(cache),
                )
            )
    targets = set()
    for group in sse["groups"]:
        for evidence in group["evidence"]:
            row = evidence["normalized"]
            targets.add((row["source_symbol"], row["record_date"], row["ex_date"]))
    for row in szse["rows"]:
        if row["symbol"].startswith(("0", "3")):
            targets.add((row["symbol"], row["record_date"], row["ex_date"]))
    results = []
    for symbol, record, ex in sorted(targets):
        if not ex.startswith(str(args.year) + "-"):
            continue
        matched = sorted(index.get((symbol, record, ex), []), key=lambda r: r["url"])
        results.append(
            dict(
                symbol=symbol,
                record_date=record,
                ex_date=ex,
                documents=matched,
                status="MATCHING_DATED_NOTICE_REQUIRES_TERMS_REVIEW"
                if matched
                else "NO_LABELED_DATE_MATCH",
            )
        )
    report = dict(
        parser_version="DISTRIBUTION_NOTICE_DATE_LINK_V2",
        parser_sha256=sha256_file(Path(__file__)),
        inputs=[dict(path=str(p), sha256=sha256_file(p)) for p in inputs],
        year=args.year,
        results=results,
        extraction_gaps=sorted(extraction_gaps),
        parsing_errors=sorted(parsing_errors, key=lambda r: r["source_sha256"]),
        matched=sum(bool(r["documents"]) for r in results),
        total=len(results),
        accepted_events=0,
        full_dataset_created=False,
        limitations=[
            "DATE_LINK_ONLY_NOT_ECONOMIC_TERMS",
            "NO_MATCH_IS_NOT_PROOF_OF_MISSING_EVENT",
            "SSE_SOURCE_CODE_ALIASES_NOT_REWRITTEN",
            "SZSE_ROWS_INCLUDE_RIGHTS",
        ],
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        args.root / args.batch / f"date-links-{args.year}-v2.json",
        canonical_json_bytes(report) + b"\n",
    )
    print(json.dumps({k: v for k, v in report.items() if k not in ("results", "inputs")}))


if __name__ == "__main__":
    main()
