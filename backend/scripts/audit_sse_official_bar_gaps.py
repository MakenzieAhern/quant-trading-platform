"""Classify missing SSE official daily bars without promoting raw authority."""

import argparse
import json
from pathlib import Path

from scripts.audit_sse_official_daily_scope import CALENDAR_SHA, MASTER_SHA
from scripts.reconcile_sse_cninfo import canonical, save, sha

SOURCE_REPORT_SHA = "d56d8abef4ff8a3f347d3f247feaf5ed8eb15367430eb3db91e36715048a5940"
FACTBOOKS = {
    2009: ("c962379b144ace00f189065ce7d1d32ea8f5d7fe47e3e617adc8383a291262c2", 86),
    2013: ("5971dc407dff2aefb15ef203b684fba056e56ac351034d0a8f483472278cc4ff", 130),
}
ISSUER_NOTICES = {
    "600053-2010-09-15-halt.pdf": (
        "8b892d52d9538710abedec54c8387423102d938ddcd30af46932aed88e35a05a"
    ),
    "600053-2011-04-01-halt.pdf": (
        "ce5bbcd1ca64917f4d9fc637065bc783925468dfeeaa72763097fe25146c77f7"
    ),
    "600053-2011-04-19-resume.pdf": (
        "d24e760d0a0eaf35783aa85fae68b7a19baeb0e50e9d39b6635f3c99b36657ec"
    ),
    "600240-2015-07-04-halt.pdf": (
        "79012fffb039b3ebe9ae0c1afb1eab347bdd3354b960f877e1718c61dea578e5"
    ),
    "601360-code-change-2018.pdf": (
        "00bec778e95cb844957cf40b25386c2808e92b0af43a3bf76c03e473f7a7bd0d"
    ),
}


def classify(
    symbol: str, day: str, intervals: list[tuple[str, str]], effective_to: str | None = None
) -> str:
    # The 2009 and 2013 SSE factbook pages bound this one pre-2010 suspension.
    if symbol == "600705" and "2010-01-01" <= day < "2012-08-30":
        return "OFFICIAL_LISTING_SUSPENSION"
    if (
        (
            symbol == "600053"
            and ("2010-09-15" <= day < "2010-09-27" or "2011-04-01" <= day < "2011-04-19")
        )
        or (symbol == "600240" and day == "2015-07-03")
        or (symbol == "601360" and "2018-02-23" <= day < "2018-02-28")
    ):
        return "OFFICIAL_ISSUER_HALT"
    if any(start <= day <= end for start, end in intervals):
        return "SSE_OPEN_BLOCKED_SOURCE_INTERVAL"
    if effective_to == day:
        return "MASTER_DELISTING_BOUNDARY_NO_BAR"
    return "UNRESOLVED"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--calendar", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--suspensions", type=Path, required=True)
    parser.add_argument("--factbook-root", type=Path, required=True)
    parser.add_argument("--notice-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    if (
        sha(args.master.read_bytes()) != MASTER_SHA
        or sha(args.calendar.read_bytes()) != CALENDAR_SHA
    ):
        raise ValueError("ACCEPTED_MASTER_OR_CALENDAR_CHANGED")
    source_bytes = (args.source_root / "full-collection-report.json").read_bytes()
    if sha(source_bytes) != SOURCE_REPORT_SHA:
        raise ValueError("AUDITED_SOURCE_REPORT_CHANGED")
    source = json.loads(source_bytes)
    if source["failure_manifest"] or len(source["results"]) != source["expected_symbols"]:
        raise ValueError("SSE_SOURCE_COLLECTION_INCOMPLETE")

    provenance = {}
    for year, (expected_sha, page) in FACTBOOKS.items():
        path = args.factbook_root / f"sse-factbook-{year}.pdf"
        meta = json.loads(path.with_suffix(".pdf.meta.json").read_bytes())
        if sha(path.read_bytes()) != expected_sha or meta["sha256"] != expected_sha:
            raise ValueError(f"OFFICIAL_FACTBOOK_CHANGED:{year}")
        provenance[str(year)] = {
            "url": meta["url"],
            "retrieved_at_utc": meta["retrieved_at_utc"],
            "sha256": expected_sha,
            "pdf_page": page,
        }
    notice_provenance = {}
    for name, expected_sha in ISSUER_NOTICES.items():
        path = args.notice_root / name
        meta = json.loads(path.with_suffix(".pdf.meta.json").read_bytes())
        if sha(path.read_bytes()) != expected_sha or meta["sha256"] != expected_sha:
            raise ValueError(f"OFFICIAL_ISSUER_NOTICE_CHANGED:{name}")
        notice_provenance[name] = {
            "url": meta["url"],
            "retrieved_at_utc": meta["retrieved_at_utc"],
            "sha256": expected_sha,
            "pdf_page": 1,
        }

    master = sorted(
        (
            r
            for r in json.loads(args.master.read_bytes())
            if r["exchange"] == "SSE" and r["instrument_type"] == "COMMON_A_SHARE"
        ),
        key=lambda r: (r["symbol"], r["effective_from"]),
    )
    sessions = json.loads(args.calendar.read_bytes())["sessions"]
    if sessions != sorted(set(sessions)) or len(master) != len(source["results"]):
        raise ValueError("MASTER_OR_CALENDAR_ORDER_CHANGED")
    suspensions_bytes = args.suspensions.read_bytes()
    intervals = {}
    for event in json.loads(suspensions_bytes)["sse"]:
        if event["execution_open_blocked"]:
            intervals.setdefault(event["symbol"], []).append(
                (event["suspended_at"], event["resumed_or_ended_at"])
            )
    counts = {
        "OFFICIAL_LISTING_SUSPENSION": 0,
        "OFFICIAL_ISSUER_HALT": 0,
        "SSE_OPEN_BLOCKED_SOURCE_INTERVAL": 0,
        "MASTER_DELISTING_BOUNDARY_NO_BAR": 0,
        "UNRESOLVED": 0,
    }
    unresolved = []
    active_sessions = in_interval_bars = 0
    for row, result in zip(master, source["results"], strict=True):
        if any(
            result[key] != row[key]
            for key in ("symbol", "security_id", "effective_from", "effective_to")
        ):
            raise ValueError("SOURCE_COLLECTION_IDENTITY_CHANGED")
        raw = (args.source_root / f"{row['symbol']}.json").read_bytes()
        if sha(raw) != result["source_sha256"]:
            raise ValueError(f"SOURCE_BYTES_CHANGED:{row['symbol']}")
        dates = {
            f"{str(bar[0])[:4]}-{str(bar[0])[4:6]}-{str(bar[0])[6:]}"
            for bar in json.loads(raw)["kline"]
            if 20100101 <= bar[0] <= 20251231
            and row["effective_from"] <= f"{str(bar[0])[:4]}-{str(bar[0])[4:6]}-{str(bar[0])[6:]}"
            and (
                row["effective_to"] is None
                or f"{str(bar[0])[:4]}-{str(bar[0])[4:6]}-{str(bar[0])[6:]}" <= row["effective_to"]
            )
        }
        in_interval_bars += len(dates)
        for day in sessions:
            if day < row["effective_from"] or (
                row["effective_to"] is not None and day > row["effective_to"]
            ):
                continue
            active_sessions += 1
            if day in dates:
                continue
            category = classify(
                row["symbol"], day, intervals.get(row["symbol"], []), row["effective_to"]
            )
            counts[category] += 1
            if category == "UNRESOLVED":
                unresolved.append(
                    {"security_id": row["security_id"], "symbol": row["symbol"], "date": day}
                )
    report = {
        "status": "PARTIAL_UNRESOLVED_NOT_RAW_AUTHORITY"
        if unresolved
        else "SOURCE_GAPS_EXPLAINED_NOT_RAW_AUTHORITY",
        "report_version": "SSE_OFFICIAL_BAR_GAPS_V1",
        "parser_sha256": sha(Path(__file__).read_bytes()),
        "master_sha256": MASTER_SHA,
        "calendar_sha256": CALENDAR_SHA,
        "source_collection_sha256": SOURCE_REPORT_SHA,
        "suspension_events_sha256": sha(suspensions_bytes),
        "listing_suspension_factbooks": provenance,
        "issuer_halt_notices": notice_provenance,
        "active_master_sessions": active_sessions,
        "in_interval_bars": in_interval_bars,
        "missing_sessions": sum(counts.values()),
        "classification_counts": counts,
        "unresolved_security_dates": unresolved,
        "delisting_boundary_note": (
            "Identity retained through official delisting date; no raw bar and no "
            "inferred suspension or trade on that date."
        ),
        "raw_authority_promoted": False,
    }
    report["manifest_sha256"] = sha(canonical(report))
    save(args.output, report)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "status",
                    "active_master_sessions",
                    "in_interval_bars",
                    "missing_sessions",
                    "classification_counts",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
