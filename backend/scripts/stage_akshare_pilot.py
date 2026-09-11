"""Resume accepted-route Pilot inputs; fail closed before incomplete publication."""

import argparse
import csv
import json
from pathlib import Path

from scripts.project_controller import next_stage
from scripts.reconcile_sse_cninfo import fetch, save, sha
from scripts.sina_adjustment_audit import factor_at, parse_factors

START, END = "2023-01-01", "2024-07-31"
DATASET_ID = "cn-a-pilot-akshare-20230101-20240731-v1"


def pilot_members(staging: Path) -> list[dict[str, str]]:
    root = staging / "security-master-pilot"
    manifest = json.loads((root / "security-master-input.json").read_bytes())
    if (
        not manifest.get("complete")
        or manifest["coverage_start"] > START
        or manifest["coverage_end"] < END
    ):
        raise ValueError("INCOMPLETE_ACCEPTED_MASTER")
    rows = []
    for source in manifest["sources"]:
        path = root / source["filename"]
        if sha(path.read_bytes()) != source["sha256"]:
            raise ValueError("ACCEPTED_MASTER_CHECKSUM_CHANGED")
        with path.open(encoding="utf-8", newline="") as stream:
            rows.extend(
                row
                for row in csv.DictReader(stream)
                if row["listing_date"] <= END
                and (not row["delisting_date"] or row["delisting_date"] >= START)
            )
    if len({row["security_id"] for row in rows}) != len(rows):
        raise ValueError("DUPLICATE_MASTER_IDENTITY")
    # Test retention risks first; selection is fixed, never performance dependent.
    return sorted(rows, key=lambda row: (not bool(row["delisting_date"]), row["security_id"]))


def raw_url(exchange: str, symbol: str) -> str:
    if exchange not in {"SSE", "SZSE"} or len(symbol) != 6 or not symbol.isdecimal():
        raise ValueError("INVALID_REQUEST_IDENTITY")
    return (
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
        "fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116"
        "&ut=7eea3edcaed734bea9cbfc24409ed989&klt=101&fqt=0"
        f"&secid={1 if exchange == 'SSE' else 0}.{symbol}&beg=20230101&end=20240731"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--repository", required=True, type=Path)
    args = parser.parse_args()
    state = json.loads((args.repository / ".research/project_state.json").read_bytes())
    lock = json.loads((args.repository / ".research/oos_lock.json").read_bytes())
    if next_stage(state, lock) != "R2" or state["current_stage"] != "R2":
        raise ValueError("CONTROLLER_DOES_NOT_AUTHORIZE_R2")
    if (
        state["source_authority_preflight"] != "PASS"
        or state["execution_convention_validation"] != "PASS"
    ):
        raise ValueError("R1_GATES_NOT_PASSED")
    root = args.staging / "pilot-akshare-20260911"
    members = pilot_members(args.staging)
    completed = []
    for row in members:
        sid, symbol, exchange = row["security_id"], row["symbol"], row["exchange"]
        request_url = raw_url(exchange, symbol)
        try:
            accepted_raw = args.staging / "raw-route-20260910" / f"{symbol}-1.json"
            if accepted_raw.exists():
                manifest = json.loads(
                    (accepted_raw.parent / "acceptance-manifest.json").read_bytes()
                )
                expected = next(
                    item["sha256"]
                    for item in manifest["files"]
                    if item["path"] == accepted_raw.name
                )
                if sha(accepted_raw.read_bytes()) != expected:
                    raise ValueError("ACCEPTED_RAW_CHECKSUM_CHANGED")
                raw_path = accepted_raw
                raw = raw_path.read_bytes()
            else:
                raw_path = root / "sources" / f"{symbol}.json"
                raw = fetch(raw_path.parent, raw_path.name, request_url)
            payload = json.loads(raw).get("data")
            if not payload or not payload.get("klines"):
                raise ValueError("RAW_HISTORY_UNAVAILABLE")
            if payload.get("code") != symbol:
                raise ValueError("RAW_SECURITY_IDENTITY_MISMATCH")
            provider_symbol = ("sh" if exchange == "SSE" else "sz") + symbol
            request_url = f"https://finance.sina.com.cn/realstock/company/{provider_symbol}/hfq.js"
            accepted_factor = (
                args.staging / "sina-acceptance-20260910/factors" / f"{provider_symbol}-hfq-1.js"
            )
            if accepted_factor.exists():
                meta = json.loads(accepted_factor.with_suffix(".js.meta.json").read_bytes())
                factor_raw = accepted_factor.read_bytes()
                if sha(factor_raw) != meta["sha256"] or meta["url"] != request_url:
                    raise ValueError("ACCEPTED_FACTOR_CHECKSUM_CHANGED")
                factor_path = accepted_factor
            else:
                factor_path = root / "sources" / f"{provider_symbol}-hfq.js"
                factor_raw = fetch(factor_path.parent, factor_path.name, request_url)
            curve = parse_factors(factor_raw, provider_symbol, "hfq")
            first = min(line.split(",")[0] for line in payload["klines"])
            factor_at(curve, first)
            completed.append(
                dict(
                    security_id=sid,
                    raw_path=raw_path.relative_to(args.staging).as_posix(),
                    raw_sha256=sha(raw),
                    factor_path=factor_path.relative_to(args.staging).as_posix(),
                    factor_sha256=sha(factor_raw),
                    raw_rows=len(payload["klines"]),
                )
            )
            save(
                root / "checkpoint.json",
                dict(
                    dataset_id=DATASET_ID, total=len(members), completed=completed, published=False
                ),
            )
            print(f"{len(completed)}/{len(members)} {sid} INPUTS_STAGED", flush=True)
        except Exception as exc:
            failure = dict(
                dataset_id=DATASET_ID,
                security_id=sid,
                effective_from=max(START, row["listing_date"]),
                effective_to=min(END, row["delisting_date"] or END),
                error=str(exc),
                error_type=type(exc).__name__,
                source_url=request_url,
                evidence_searched=[
                    "accepted raw-route cache",
                    "accepted Sina factor cache",
                    "exact accepted provider route",
                ],
                completed_securities=len(completed),
                universe_securities=len(members),
                published=False,
                dataset_frozen=False,
            )
            save(root / "failure-manifest.json", failure)
            print(json.dumps(failure, ensure_ascii=False), flush=True)
            raise SystemExit(2) from exc
    save(
        root / "input-manifest.json", dict(dataset_id=DATASET_ID, inputs=completed, published=False)
    )


if __name__ == "__main__":
    main()
