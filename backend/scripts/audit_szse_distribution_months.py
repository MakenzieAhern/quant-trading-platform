"""Check official monthly source rows and independently cross-check the rights ledger."""

import argparse
import json
from datetime import datetime
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable


class Rows(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"}:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None:
            if self.row is not None:
                self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def extract(raw, month):
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("gb18030")
    parser = Rows()
    parser.feed(text)
    if not parser.rows or len(parser.rows[0]) != 14 or "Rts Issues" not in parser.rows[0][6]:
        raise ValueError("UNKNOWN_MONTHLY_TABLE_SCHEMA")
    rows = []
    for cells in parser.rows[1:]:
        if len(cells) == 14 and not any(cells):
            continue
        if len(cells) != 14 or len(cells[0]) != 6 or not cells[0].isdigit():
            raise ValueError("UNPARSED_MONTHLY_ROW")
        ex = datetime.strptime(cells[10], "%Y/%m/%d").date().isoformat()
        record = datetime.strptime(cells[11], "%Y/%m/%d").date().isoformat()
        if ex[:7] != month or (not cells[0].startswith("2") and record >= ex):
            raise ValueError("MONTHLY_EVENT_DATE_MISMATCH")
        rights = Decimal(cells[6].replace(",", "")) if cells[6] else Decimal(0)
        ratio = Decimal(cells[7]) if cells[7] else Decimal(0)
        price = Decimal(cells[8]) if cells[8] else Decimal(0)
        if any(not value.is_finite() or value < 0 for value in (rights, ratio, price)):
            raise ValueError("INVALID_RIGHTS_ISSUANCE_QUANTITY")
        rows.append(
            dict(
                symbol=cells[0],
                ex_date=ex,
                record_date=record,
                rights_candidate=any(value > 0 for value in (rights, ratio, price)),
                raw_cells=cells,
            )
        )
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    root = args.staging / "full-szse-distribution-census-v1"
    rows, failures, sources, empty_months = [], [], [], []
    for year in range(2010, 2026):
        for month in range(1, 13):
            period = f"{year}-{month:02}"
            path = root / f"distributions-{period}.html"
            try:
                receipt = json.loads(Path(str(path) + ".meta.json").read_bytes())
                if receipt.get("error") or sha256_file(path) != receipt["sha256"]:
                    raise ValueError("MONTHLY_SOURCE_NOT_VERIFIED")
                found = extract(path.read_bytes(), period)
                if not found:
                    empty_months.append(period)
                rows.extend(
                    dict(
                        **row,
                        source_sha256=receipt["sha256"],
                        source_url=receipt["url"],
                        month=period,
                    )
                    for row in found
                )
                sources.append(receipt)
            except (OSError, ValueError, KeyError) as exc:
                failures.append(dict(month=period, error=f"{type(exc).__name__}: {exc}"))
    rights = [r for r in rows if r["rights_candidate"] and not r["symbol"].startswith("2")]
    inventory_path = args.staging / "full-rights-inventory-v1/inventory-batch-reconciled-v3.json"
    inventory = json.loads(inventory_path.read_bytes())
    existing = {
        (r["event"]["security_id"]["value"].split(":")[-1], r["event"]["ex_date"])
        for r in inventory["rows"]
        if ":SZSE:" in r["event"]["security_id"]["value"]
    }
    observed = {(r["symbol"], r["ex_date"]) for r in rights}
    report = dict(
        parser_version="SZSE_MONTHLY_DISTRIBUTION_AUDIT_V2",
        parser_sha256=sha256_file(Path(__file__)),
        sources=sources,
        source_empty_months=empty_months,
        rows=rows,
        rights_rows=rights,
        failures=failures,
        source_only_rights=sorted(observed - existing),
        ledger_only_rights=sorted(existing - observed),
        inventory_sha256=sha256_file(inventory_path),
        full_census_accepted=False,
        full_dataset_created=False,
        precision_status="SUMMARY_TABLE_DISPLAY_PRECISION_NOT_EXACT_CASH_AUTHORITY",
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(root / "monthly-row-audit-v2.json", canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            dict(
                rows=len(rows),
                rights=len(rights),
                failures=failures,
                source_only=report["source_only_rights"],
                ledger_only=report["ledger_only_rights"],
                manifest_sha256=report["manifest_sha256"],
            )
        )
    )


if __name__ == "__main__":
    main()
