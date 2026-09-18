"""Read-only SZSE official/Pilot-v2 same-day raw-field cross-check."""

import argparse
import json
import warnings
from decimal import Decimal
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq
from openpyxl import load_workbook

from scripts.probe_szse_official_daily import HEADERS
from scripts.reconcile_sse_cninfo import save, sha

DAY = "2023-04-10"
PRICE_FIELDS = ((4, "raw_open"), (5, "raw_high"), (6, "raw_low"), (7, "raw_close"))


def number(value: object) -> Decimal:
    return Decimal(str(value).replace(",", ""))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--official", type=Path, required=True)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    master_bytes = args.master.read_bytes()
    if sha(master_bytes) != "02f1a2bb145d1d9c98c4d9678bad687a8a4c4ece6f6419f12da939b66507b363":
        raise ValueError("accepted P0 master checksum changed")
    source_bytes = args.official.read_bytes()
    receipt = json.loads(args.official.with_suffix(".xlsx.meta.json").read_bytes())
    if sha(source_bytes) != receipt["sha256"]:
        raise ValueError("official SZSE source checksum mismatch")
    active = {
        row["symbol"]: row["security_id"]
        for row in json.loads(master_bytes)
        if row["exchange"] == "SZSE"
        and row["instrument_type"] == "COMMON_A_SHARE"
        and row["effective_from"] <= DAY
        and (row["effective_to"] is None or row["effective_to"] >= DAY)
    }
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="Workbook contains no default style")
        workbook = load_workbook(args.official, read_only=True, data_only=True)
    sheet = workbook.active
    sheet.reset_dimensions()
    rows = sheet.values
    if tuple(next(rows)) != HEADERS:
        raise ValueError("official SZSE export columns changed")
    results = []
    for row in rows:
        if row[0] != DAY:
            raise ValueError("official SZSE export date mismatch")
        symbol = row[1]
        if symbol not in active:
            continue
        result = {"symbol": symbol, "security_id": active[symbol]}
        path = args.pilot / "SZSE" / symbol / "raw.parquet"
        if not path.exists():
            result["status"] = "PILOT_PARTITION_MISSING"
        else:
            table = pq.read_table(
                path,
                columns=[
                    "trading_date",
                    "raw_open",
                    "raw_high",
                    "raw_low",
                    "raw_close",
                    "volume",
                    "amount",
                ],
            )
            matches = table.filter(pc.equal(table["trading_date"], DAY)).to_pylist()
            if not matches and number(row[9]) == 0 and number(row[10]) == 0:
                result["status"] = "OFFICIAL_ZERO_TURNOVER_NO_PILOT_BAR"
            elif len(matches) != 1:
                result.update(status="PILOT_DAY_MISSING_OR_DUPLICATE", pilot_rows=len(matches))
            else:
                pilot = matches[0]
                try:
                    price_gaps = {
                        name: str(number(row[index]) - number(pilot[name]))
                        for index, name in PRICE_FIELDS
                    }
                    volume_gap = number(row[9]) * 10000 - number(pilot["volume"])
                    amount_gap = number(row[10]) * 10000 - number(pilot["amount"])
                    result.update(
                        status="COMPARED",
                        price_gaps=price_gaps,
                        volume_gap=str(volume_gap),
                        amount_gap=str(amount_gap),
                        price_match=all(number(gap) == 0 for gap in price_gaps.values()),
                        volume_within_combined_precision=abs(volume_gap) <= 100,
                        amount_within_combined_precision=abs(amount_gap) <= 100,
                    )
                except (ValueError, TypeError, ArithmeticError) as exc:
                    result.update(status="NONNUMERIC", reason=str(exc))
        results.append(result)
    controls = {r["symbol"]: r for r in results}
    if controls["000001"]["price_match"] is not True or (
        controls["000001"]["volume_gap"] != "999900.00"
        or controls["000001"]["amount_gap"] != "12029952.38"
    ):
        raise ValueError("known SZSE/Pilot scope control changed")
    compared = [r for r in results if r["status"] == "COMPARED"]
    report = {
        "status": "SCOPE_CROSSCHECK_ONLY_NOT_AUTHORITY",
        "day": DAY,
        "official_sha256": sha(source_bytes),
        "pilot_manifest_sha256": sha((args.pilot / "manifest.json").read_bytes()),
        "master_sha256": sha(master_bytes),
        "official_a_share_rows": len(results),
        "compared": len(compared),
        "price_mismatch": sum(not r["price_match"] for r in compared),
        "volume_beyond_combined_precision": sum(
            not r["volume_within_combined_precision"] for r in compared
        ),
        "amount_beyond_combined_precision": sum(
            not r["amount_within_combined_precision"] for r in compared
        ),
        "zero_turnover_no_pilot_bar": sum(
            r["status"] == "OFFICIAL_ZERO_TURNOVER_NO_PILOT_BAR" for r in results
        ),
        "uncompared": [
            r
            for r in results
            if r["status"] not in ("COMPARED", "OFFICIAL_ZERO_TURNOVER_NO_PILOT_BAR")
        ],
        "results": results,
    }
    save(args.output, report)
    print(
        f"compared={len(compared)} price_mismatch={report['price_mismatch']} "
        f"volume_scope_gap={report['volume_beyond_combined_precision']} "
        f"amount_scope_gap={report['amount_beyond_combined_precision']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
