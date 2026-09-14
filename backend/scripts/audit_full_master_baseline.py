"""Cross-check 2009 master membership; not full-history or ST/tradability acceptance."""

import argparse
import json
import re
import unicodedata
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def yearbook_codes(pages, heading):
    rows = {}
    for number, text in enumerate(pages, 1):
        text = unicodedata.normalize("NFKC", text)
        if heading not in re.sub(r"\s+", "", text):
            continue
        for code in re.findall(r"(?m)^\s*((?:000|001|002|300|600|601|900)\d{3})(?=\s)", text):
            if code in rows:
                raise ValueError("DUPLICATE_DIRECTORY_CODE")
            rows[code] = number
    if not rows:
        raise ValueError("EMPTY_DIRECTORY")
    return rows


def active_codes(records, exchange, boundary="2009-12-31"):
    rows = [
        r["symbol"]
        for r in records
        if r["exchange"] == exchange
        and r["effective_from"] <= boundary
        and (not r["effective_to"] or r["effective_to"] >= boundary)
    ]
    if len(rows) != len(set(rows)):
        raise ValueError("OVERLAPPING_MASTER_INTERVALS")
    return set(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("master", "sse-text", "sse-pdf", "szse-text", "szse-pdf", "review", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    master = json.loads(args.master.read_bytes())
    if (
        canonical_sha256({k: v for k, v in master.items() if k != "manifest_sha256"})
        != master["manifest_sha256"]
    ):
        raise ValueError("MASTER_MANIFEST_CHANGED")
    review = json.loads(args.review.read_bytes())
    if review["scope"] != "MASTER_MEMBERSHIP_ONLY_NOT_ST_OR_TRADABILITY":
        raise ValueError("REVIEW_SCOPE_CHANGED")
    supplemental = set()
    for r in review["records"]:
        if r["security_id"] != "CN-A:SZSE:" + r["symbol"] or r["status_history_acceptance"]:
            raise ValueError("SUPPLEMENT_IDENTITY_OR_SCOPE_CHANGED")
        path = Path(r["source_path"])
        meta = json.loads(Path(str(path) + ".meta.json").read_bytes())
        if (
            sha256_file(path) != r["source_sha256"]
            or meta["sha256"] != r["source_sha256"]
            or meta["url"] != r["source_url"]
            or meta["retrieved_at_utc"] != r["retrieved_at_utc"]
            or meta.get("http_status") != 200
            or not r["reviewed_identity_pages"]
        ):
            raise ValueError("REVIEW_SOURCE_MISMATCH")
        if r["symbol"] in supplemental:
            raise ValueError("DUPLICATE_SUPPLEMENT")
        supplemental.add(r["symbol"])
    results = []
    for exchange, text_path, pdf, heading in (
        ("SSE", args.sse_text, args.sse_pdf, "上市公司基本信息"),
        ("SZSE", args.szse_text, args.szse_pdf, "上市公司中英文名称对照表"),
    ):
        extracted = json.loads(text_path.read_bytes())
        if sha256_file(pdf) != extracted["source_sha256"]:
            raise ValueError("YEARBOOK_SOURCE_CHANGED")
        rows = yearbook_codes(extracted["pages"], heading)
        active = active_codes(master["records"], exchange)
        supplements = supplemental if exchange == "SZSE" else set()
        if supplements - (active - rows.keys()):
            raise ValueError("SUPPLEMENT_OUTSIDE_BASELINE_GAPS")
        classifications = []
        for code in sorted(rows.keys() - active):
            histories = [
                r for r in master["records"] if r["exchange"] == exchange and r["symbol"] == code
            ]
            if exchange == "SSE" and code.startswith("900"):
                state = "B_SHARE_OUTSIDE_ORDINARY_A_SCOPE"
            elif exchange == "SZSE" and code in review["b_only_company_code_aliases"]:
                b_code = review["b_only_company_code_aliases"][code]
                if not any(b_code in unicodedata.normalize("NFKC", p) for p in extracted["pages"]):
                    raise ValueError("B_SHARE_EVIDENCE_MISSING")
                state = "B_ONLY_COMPANY_DIRECTORY_CODE_NOT_A_SHARE"
            elif histories and all(r["effective_from"] > "2009-12-31" for r in histories):
                state = "FUTURE_LISTING_NOT_BASELINE"
            elif histories and all(
                r["effective_to"] and r["effective_to"] < "2009-12-31" for r in histories
            ):
                state = "EXITED_BEFORE_BASELINE"
            else:
                state = "UNRESOLVED"
            classifications.append(dict(symbol=code, pdf_page=rows[code], classification=state))
        missing = sorted(active - rows.keys() - supplements)
        results.append(
            dict(
                exchange=exchange,
                directory_rows=rows,
                master_active=len(active),
                supplemental_symbols=sorted(supplements),
                missing_active=missing,
                extra_directory_rows=classifications,
                status="PASS_MEMBERSHIP_CROSSCHECK"
                if not missing
                and not any(r["classification"] == "UNRESOLVED" for r in classifications)
                else "PARTIAL",
            )
        )
    body = dict(
        parser_version="FULL_MASTER_BASELINE_CROSSCHECK_V1",
        parser_sha256=sha256_file(Path(__file__)),
        master_sha256=sha256_file(args.master),
        review_sha256=sha256_file(args.review),
        yearbook_sha256=[sha256_file(args.sse_pdf), sha256_file(args.szse_pdf)],
        results=results,
        full_master_acceptance="PARTIAL",
        historical_st_acceptance="NOT_PERFORMED",
        full_dataset_created=False,
        full_dataset_frozen=False,
    )
    body["manifest_sha256"] = canonical_sha256(body)
    write_immutable(args.output, canonical_json_bytes(body) + b"\n")
    print(
        json.dumps(
            {
                "manifest_sha256": body["manifest_sha256"],
                "results": [{k: v for k, v in r.items() if k != "directory_rows"} for r in results],
            }
        )
    )


if __name__ == "__main__":
    main()
