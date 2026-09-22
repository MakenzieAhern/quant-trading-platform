"""Replace rounded cash terms only when the retained primary issuer source is unchanged."""

import argparse
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_cash_gap_candidates import is_final_implementation_title
from scripts.reconcile_distribution_cash import gross_cash, verified


def precision_gap(row, prior):
    if (
        row["status"] != "UNRESOLVED_CASH_TERMS"
        or row["unresolved_documents"]
        or len(row["evidence"]) != 1
        or len(row["exchange_amounts"]) != 1
        or prior is None
    ):
        return False
    source = row["evidence"][0]["source"]
    old = prior["event"]
    expected = Decimal(row["exchange_amounts"][0])
    exact = Decimal(row["evidence"][0]["cash_per_share"])
    source_route = (
        old["source_url"] == source["url"]
        and old["source_document_sha256"] == source["source_sha256"]
        and old["source_provider"].startswith("OFFICIAL_ISSUER_CNINFO_")
    ) or (
        old["source_provider"] == "OFFICIAL_SSE_TABLE_CNINFO_NOTICE_COMPOSITE"
        and old["security_id"]["value"].startswith("CN-A:SSE:")
    )
    return (
        exact > 0
        and exact != expected
        and Decimal(old["cash_per_share"]) == expected
        and exact.quantize(Decimal(1).scaleb(expected.as_tuple().exponent), rounding=ROUND_HALF_UP)
        == expected
        and old["record_date"] == row["record_date"]
        and source_route
    )


def reconcile(reports, baseline, root):
    prior = {
        (item["event"]["security_id"]["value"], item["event"]["ex_date"]): item
        for item in baseline["events"]
    }
    if len(prior) != len(baseline["events"]):
        raise ValueError("DUPLICATE_BASELINE_CASH_EVENT")
    replacements = {}
    for report in reports:
        date_inputs = [item for item in report["inputs"] if "/date-links-" in item["path"]]
        if (
            len(date_inputs) != 1
            or sha256_file(Path(date_inputs[0]["path"])) != date_inputs[0]["sha256"]
        ):
            raise ValueError("DATE_LINK_INPUT_CHANGED")
        links = verified(Path(date_inputs[0]["path"]))
        by_key = {
            (item["symbol"], item["record_date"], item["ex_date"]): item
            for item in links["results"]
        }
        for row in report["results"]:
            key = (
                f"CN-A:{'SZSE' if row['symbol'][0] in '03' else 'SSE'}:{row['symbol']}",
                row["ex_date"],
            )
            old = prior.get(key)
            if not precision_gap(row, old):
                continue
            source = row["evidence"][0]["source"]
            if (
                not source["url"].startswith("https://static.cninfo.com.cn/finalpage/")
                or not is_final_implementation_title(source["title"])
                or source["published_on"] > row["record_date"]
            ):
                raise ValueError("ISSUER_PRECISION_SOURCE_NOT_FINAL")
            pdf = (root / source["source_path"]).resolve()
            cache = root / "batch-v1/text" / f"{source['source_sha256']}.json"
            linked = [
                item
                for item in by_key[row["symbol"], row["record_date"], row["ex_date"]]["documents"]
                if item["url"] == source["url"] and item["source_sha256"] == source["source_sha256"]
            ]
            if (
                not pdf.is_relative_to(root.parent.resolve())
                or sha256_file(pdf) != source["source_sha256"]
                or len(linked) != 1
                or sha256_file(cache) != linked[0]["extraction_sha256"]
            ):
                raise ValueError("ISSUER_PRECISION_SOURCE_CHANGED")
            extracted = json.loads(cache.read_bytes())
            pages = extracted["pages"]
            exact = Decimal(row["evidence"][0]["cash_per_share"])
            if (
                extracted["source_sha256"] != source["source_sha256"]
                or notice_dates(pages) != ([row["record_date"]], [row["ex_date"]])
                or gross_cash(pages, row["symbol"], {Decimal(row["exchange_amounts"][0])}) != exact
            ):
                raise ValueError("ISSUER_PRECISION_TERMS_CHANGED")
            previous = CorporateAction.model_validate(old["event"])
            if previous.event_checksum != old["event_checksum"]:
                raise ValueError("BASELINE_CASH_EVENT_CHANGED")
            terms = {
                "security_id": key[0],
                "record_date": row["record_date"],
                "ex_date": row["ex_date"],
                "cash_per_share": str(exact),
                "source_sha256": source["source_sha256"],
            }
            action = CorporateAction.model_validate(
                {
                    **old["event"],
                    "announcement_date": source["published_on"],
                    "cash_per_share": str(exact),
                    "source_document": source["title"],
                    "source_url": source["url"],
                    "source_document_sha256": source["source_sha256"],
                    "retrieved_at": source["retrieved_at_utc"],
                    "source_provider": "OFFICIAL_ISSUER_CNINFO_PRIMARY_IMPLEMENTATION",
                    "source_version": "RETAINED_ISSUER_PRECISE_CASH_V1",
                    "source_record_hash": canonical_sha256(terms),
                }
            )
            require_supported_corporate_action(action)
            replacement = {
                "event": action.model_dump(mode="json"),
                "event_checksum": action.event_checksum,
                "supersedes_event_checksum": old["event_checksum"],
                "source_terms_sha256": canonical_sha256(terms),
                "source_text_cache_sha256": sha256_file(cache),
                "old_exchange_rounded_amount": old["event"]["cash_per_share"],
                "official_issuer_exact_amount": str(exact),
            }
            if key in replacements and replacements[key] != replacement:
                raise ValueError("CONFLICTING_ISSUER_PRECISION_REPLACEMENT")
            replacements[key] = replacement
    return [replacements[key] for key in sorted(replacements)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--report", type=Path, action="append", required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    paths = sorted(args.report, key=str)
    reports = [verified(path) for path in paths]
    baseline = verified(args.baseline)
    events = reconcile(reports, baseline, args.source_root)
    if events != reconcile(
        [{**report, "results": list(reversed(report["results"]))} for report in reversed(reports)],
        baseline,
        args.source_root,
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "report_version": "RETAINED_ISSUER_PRECISE_CASH_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)} for path in (args.baseline, *paths)
        ],
        "replacements": len(events),
        "events": events,
        "input_order_reproducibility": "PASS",
        "full_cash_census_acceptance": "NOT_YET_REAUDITED",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"events", "inputs"}}))


if __name__ == "__main__":
    main()
