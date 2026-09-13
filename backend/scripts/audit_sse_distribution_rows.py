"""Audit source-table semantics and collisions without accepting accounting events."""

import argparse
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


def normalize(kind, row):
    current = "A_STOCK_CODE" in row
    code = row.get("A_STOCK_CODE", row.get("SECURITY_CODE_A"))
    if code == "-":
        return None
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        raise ValueError("INVALID_SOURCE_SECURITY_CODE")

    def day(new, old):
        value = row[new if current else old].replace("-", "")
        return datetime.strptime(value, "%Y%m%d").date().isoformat()

    record = day("A_REG_DATE", "RECORD_DATE_A")
    if kind == "dividend":
        ex = day("A_DIV_DATE", "EX_DIVIDEND_DATE_A")
        amount = Decimal(row["A_BEFR_TAX_DIV" if current else "DIVIDEND_PER_SHARE2_A"].strip())
    elif kind == "bonus":
        ex = day("A_DERIGHTS_DATE", "EX_RIGHT_DATE_A")
        bonus = Decimal(row["BONUS_RATIO" if current else "BONUS_RATE"].strip())
        conversion = Decimal(row["CONVERT_RATIO" if current else "CHANGE_RATE"].strip())
        if not bonus.is_finite() or bonus < 0:
            raise ValueError("INVALID_BONUS_COMPONENT")
        if not conversion.is_finite() or conversion < 0 or (not current and conversion > bonus):
            raise ValueError("INVALID_CONVERSION_COMPONENT")
        # Historical BONUS_RATE already includes CHANGE_RATE; current fields are separate.
        amount = (bonus + conversion if current else bonus) / Decimal(10)
    else:
        raise ValueError("UNKNOWN_DISTRIBUTION_KIND")
    if not amount.is_finite() or amount < 0 or record >= ex:
        raise ValueError("INVALID_DISTRIBUTION_TERMS")
    return dict(kind=kind, source_symbol=code, record_date=record, ex_date=ex, amount=str(amount))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--review", type=Path)
    args = parser.parse_args()
    raw_sources = {}
    for receipt in args.root.glob("*.json.meta.json"):
        metadata = json.loads(receipt.read_bytes())
        if metadata.get("sha256"):
            raw_sources[metadata["sha256"]] = Path(str(receipt).removesuffix(".meta.json"))
    grouped, excluded, errors, sources = defaultdict(list), [], [], []
    for name in ("source-census-historical-v3.json", "source-census-current-v3.json"):
        path = args.root / name
        payload = json.loads(path.read_bytes())
        checksum = payload.pop("manifest_sha256")
        if canonical_sha256(payload) != checksum or payload["failures"]:
            raise ValueError("SOURCE_CENSUS_NOT_VERIFIED")
        sources.append(dict(path=str(path), sha256=sha256_file(path), manifest_sha256=checksum))
        for record in payload["records"]:
            for source in record["sources"]:
                # Locate receipts by source SHA, without assuming URL query ordering.
                raw_path = raw_sources.get(source["sha256"])
                if (
                    source["http_status"] != 200
                    or raw_path is None
                    or sha256_file(raw_path) != source["sha256"]
                ):
                    raise ValueError("SOURCE_REQUEST_FAILED")
            for row in record["rows"]:
                evidence = dict(raw_row=row, source_manifest=checksum)
                try:
                    normalized = normalize(record["kind"], row)
                    if normalized is None:
                        excluded.append(evidence)
                        continue
                    key = (normalized["kind"], normalized["source_symbol"], normalized["ex_date"])
                    grouped[key].append(dict(normalized=normalized, **evidence))
                except (ValueError, KeyError) as exc:
                    errors.append(dict(error=str(exc), **evidence))
    groups = []
    for key, rows in sorted(grouped.items()):
        terms = {canonical_sha256(row["normalized"]) for row in rows}
        groups.append(
            dict(
                key=key,
                status="CONTRADICTORY_TERMS_REQUIRES_OFFICIAL_NOTICE"
                if len(terms) > 1
                else "CANDIDATE_NOT_ACCEPTED",
                evidence=sorted(rows, key=canonical_sha256),
            )
        )
    reviewed = []
    if args.review:
        from pypdf import PdfReader

        review = json.loads(args.review.read_bytes())
        expected = {tuple(g["key"]) for g in groups if g["status"].startswith("CONTRADICTORY")}
        observed = set()
        for item in review["records"]:
            key = ("dividend", item["symbol"], item["ex_date"])
            if key not in expected or key in observed:
                raise ValueError("REVIEW_SCOPE_MISMATCH")
            observed.add(key)
            source = args.root / item["source_file"]
            receipt = json.loads(Path(str(source) + ".meta.json").read_bytes())
            if sha256_file(source) != item["source_sha256"] or receipt["url"] != item["source_url"]:
                raise ValueError("REVIEW_SOURCE_CHANGED")
            pdf = PdfReader(source)
            text = "".join(
                pdf.pages[page - 1].extract_text() for page in item["reviewed_pdf_pages"]
            )
            if item["symbol"] not in text or item["cash_per_share"] not in "".join(text.split()):
                raise ValueError("REVIEW_TERMS_NOT_IN_SOURCE")
            if (
                not item["publication_date"]
                <= item["record_date"]
                < item["ex_date"]
                <= item["payment_date"]
            ):
                raise ValueError("REVIEW_DATE_ORDER_INVALID")
            reviewed.append(dict(**item, receipt=receipt))
        if observed != expected:
            raise ValueError("REVIEW_INCOMPLETE")
    report = dict(
        parser_version="SSE_DISTRIBUTION_ROW_AUDIT_V3",
        parser_sha256=sha256_file(Path(__file__)),
        sources=sources,
        groups=groups,
        b_only_rows=excluded,
        normalization_errors=errors,
        official_conflict_resolutions=reviewed,
        unresolved_conflicting_groups=sum(g["status"].startswith("CONTRADICTORY") for g in groups)
        - len(reviewed),
        accepted_events=0,
        required_followup=[
            "STABLE_ID_ALIAS_MAPPING",
            "OFFICIAL_TERMS_PRECISION",
            "GROSS_CASH_CONFLICTS",
            "RESTRUCTURING_RETENTION_CLASSIFICATION",
            "FULL_CENSUS_CROSSCHECK",
        ],
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    name = "row-audit-reviewed-v3.json" if args.review else "row-audit-v3.json"
    write_immutable(args.root / name, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            dict(
                manifest_sha256=report["manifest_sha256"],
                groups=len(groups),
                b_only=len(excluded),
                errors=len(errors),
                conflicts=sum(g["status"].startswith("CONTRADICTORY") for g in groups),
            )
        )
    )


if __name__ == "__main__":
    main()
