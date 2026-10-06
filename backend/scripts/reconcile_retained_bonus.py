"""Reconcile an explicit integer-ratio, next-session subset; never certify the census."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.reconcile_distribution_cash import verified
from scripts.retained_bonus_terms import retained_ratio, same_day_listing


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--date-links", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--explicit-same-day",
        action="store_true",
        help="Separate candidate ledger requiring official same-ex-date credit/listing terms",
    )
    args = parser.parse_args()
    root = args.staging / "full-distribution-notices-v1"
    bonus = args.staging / "full-bonus-inventory-v1"
    paths = [
        bonus / "source-oracle-v1.json",
        bonus / "listing-boundary-check-v2.json",
        args.staging / "full-code-transitions-v1/master-code-intervals.json",
        args.staging / "full-instrument-scope-v1/classification-manifest-v3.json",
    ]
    oracle, boundaries, master, instruments = map(verified, paths)
    if boundaries["source_sha256"] != sha256_file(paths[0]):
        raise ValueError("BONUS_BOUNDARY_ORACLE_CHANGED")
    if instruments["source_master_sha256"] != sha256_file(paths[2]):
        raise ValueError("INSTRUMENT_MASTER_CHANGED")
    policy = (
        Path(__file__).resolve().parents[2] / ".research/corporate_action_policy_matrix_v1.json"
    )
    policy_data = json.loads(policy.read_bytes())
    policies = {row["class"]: row for row in policy_data["policies"]}
    if (
        policy_data["status"] != "FROZEN_POLICY_CATALOG_NOT_DATASET"
        or policies["RETAINED_BONUS"]["policy_id"] != "BASIS_CONSERVED_RETAINED_BONUS"
    ):
        raise ValueError("APPROVED_POLICY_CHANGED")
    paths.extend([policy, *args.date_links])
    boundary = {(r["symbol"], r["ex_date"]): r for r in boundaries["rows"]}
    links, sources, years = {}, {}, set()
    for path in sorted(args.date_links):
        manifest = verified(path)
        if manifest["year"] in years:
            raise ValueError("DUPLICATE_YEAR_INPUT")
        years.add(manifest["year"])
        source = Path(manifest["inputs"][0]["path"])
        if sha256_file(source) != manifest["inputs"][0]["sha256"]:
            raise ValueError("DATE_LINK_SOURCE_CHANGED")
        paths.append(source)
        for doc in verified(source)["documents"]:
            if doc["retrieval_status"] == "PASS":
                sources[doc["url"], doc["source_sha256"]] = doc
        for row in manifest["results"]:
            links[row["symbol"], row["record_date"], row["ex_date"]] = row["documents"]
    ordinary = {
        r["classification"]["security_id"]["value"]
        for r in instruments["classifications"]
        if r["classification"]["instrument_type"] == "COMMON_A_SHARE"
    }
    rows, accepted = [], []
    for original in sorted(
        oracle["rows"], key=lambda r: (r["symbol"], r["record_date"], r["ex_date"])
    ):
        key = original["symbol"], original["record_date"], original["ex_date"]
        values = {Decimal(e["ratio"]) for e in original["evidence"]}
        schedule = boundary.get((key[0], key[2]), {})
        if (
            int(key[2][:4]) not in years
            or len(values) != 1
            or any(v <= 0 or v != v.to_integral_value() for v in values)
            or (not args.explicit_same_day and schedule.get("status") != "NEXT_ACCEPTED_SESSION")
        ):
            continue
        ratio = next(iter(values))
        result = dict(symbol=key[0], record_date=key[1], ex_date=key[2], ratio=str(ratio))
        evidence, failures = [], []
        listing_date = key[2] if args.explicit_same_day else schedule["next_session"]
        for match in sorted(links.get(key, []), key=lambda r: (r["url"], r["source_sha256"])):
            doc = sources[match["url"], match["source_sha256"]]
            pdf = (root / doc["source_path"]).resolve()
            cache = root / "batch-v1/text" / (doc["source_sha256"] + ".json")
            if (
                not pdf.is_relative_to(args.staging.resolve())
                or sha256_file(pdf) != doc["source_sha256"]
                or sha256_file(cache) != match["extraction_sha256"]
                or doc["issuer"] != key[0]
                or not doc["published_on"] <= key[1] < key[2]
            ):
                raise ValueError("BONUS_SOURCE_IDENTITY_CHANGED")
            try:
                extracted = json.loads(cache.read_bytes())
                if args.explicit_same_day:
                    if extracted["source_sha256"] != doc["source_sha256"] or not doc[
                        "url"
                    ].startswith("https://static.cninfo.com.cn/finalpage/"):
                        raise ValueError("BONUS_SAME_DAY_SOURCE_BINDING_CHANGED")
                    same_day_listing(extracted["pages"], key[0], doc["title"], key[1], key[2])
                terms = retained_ratio(
                    extracted["pages"],
                    key[0],
                    require_integral_components=True,
                )
                if terms != ratio:
                    raise ValueError("BONUS_EXCHANGE_TERMS_DISAGREE")
                evidence.append(doc)
            except ValueError as exc:
                failures.append(dict(source_sha256=doc["source_sha256"], reason=str(exc)))
        result.update(evidence=evidence, unresolved_documents=failures)
        members = [
            m
            for m in master["records"]
            if m["symbol"] == key[0]
            and m["security_id"] in ordinary
            and m["effective_from"] <= key[1] < key[2] <= (m["effective_to"] or "2025-12-31")
            and m["listing_date"] <= key[1]
            and listing_date <= (m["delisting_date"] or "2025-12-31")
        ]
        if not evidence or failures or len(members) != 1:
            result["status"] = "UNRESOLVED_TERMS_OR_LIFECYCLE"
            rows.append(result)
            continue
        result["status"] = "EXACT_INTEGER_RETAINED_BONUS"
        if args.explicit_same_day:
            result.update(
                credit_date=listing_date,
                listing_date=listing_date,
                holder_class="ORDINARY_EXCHANGE_TRADABLE_A_SHARE_PUBLIC_HOLDER",
                boundary_authority="OFFICIAL_EXPLICIT_SAME_EX_DATE_CREDIT_AND_LISTING",
            )
        doc = evidence[0]
        action = CorporateAction.model_validate(
            dict(
                security_id={"value": members[0]["security_id"]},
                action_type="BONUS_SHARE",
                announcement_date=doc["published_on"],
                effective_date=key[2],
                record_date=key[1],
                ex_date=key[2],
                listing_date=listing_date,
                share_ratio=str(ratio),
                source_document=doc["title"],
                source_url=doc["url"],
                source_document_sha256=doc["source_sha256"],
                retrieved_at=doc["retrieved_at_utc"],
                source_provider="OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
                source_version=(
                    "INTEGER_RETAINED_BONUS_EXPLICIT_SAME_DAY_V2"
                    if args.explicit_same_day
                    else "INTEGER_RETAINED_BONUS_V1"
                ),
                source_record_hash=canonical_sha256(result),
                completeness="COMPLETE",
            )
        )
        require_supported_corporate_action(action)
        assert action == CorporateAction.model_validate_json(action.model_dump_json())
        accepted.append(
            dict(
                event=action.model_dump(mode="json"),
                event_checksum=action.event_checksum,
                policy_id="BASIS_CONSERVED_RETAINED_BONUS",
                support_state=(
                    "SUPPORTED_FOR_INTEGER_HOLDINGS_EXPLICIT_SAME_DAY"
                    if args.explicit_same_day
                    else "SUPPORTED_FOR_INTEGER_HOLDINGS_NEXT_SESSION_SCHEDULE"
                ),
                source_oracle_evidence_sha256=original["evidence_sha256"],
                scheduled_listing_not_actual_tradability=not args.explicit_same_day,
                accounting_scope=(
                    "INTEGER_HOLDINGS_NO_FRACTION_EXPLICIT_SAME_DAY"
                    if args.explicit_same_day
                    else "INTEGER_HOLDINGS_NO_FRACTION_NEXT_SESSION_SCHEDULE"
                ),
            )
        )
        rows.append(result)
    report = dict(
        scope=(
            "BOUNDED_INTEGER_EXPLICIT_SAME_DAY_BONUS_NOT_FULL_CENSUS"
            if args.explicit_same_day
            else "BOUNDED_INTEGER_NEXT_SESSION_BONUS_NOT_FULL_CENSUS"
        ),
        source_oracle_rows=len(oracle["rows"]),
        candidate_rows=len(rows),
        results=rows,
        deferred_or_outside_subset=len(oracle["rows"]) - len(rows),
        accepted_events=len(accepted),
        events=accepted,
        counts=dict(Counter(r["status"] for r in rows)),
        inputs=[dict(path=str(p), sha256=sha256_file(p)) for p in sorted(set(paths))],
        parser_sha256=sha256_file(Path(__file__)),
        terms_parser_sha256=sha256_file(Path(__file__).with_name("retained_bonus_terms.py")),
        issuer_parser_sha256=sha256_file(
            Path(__file__).with_name("reconcile_distribution_cash.py")
        ),
        full_dataset_created=False,
    )
    if args.explicit_same_day:
        report["same_day_dependency_sha256"] = {
            name: sha256_file(Path(__file__).with_name(name))
            for name in (
                "link_distribution_notices.py",
                "audit_p1_retained_cash_sources.py",
                "audit_p1_orphan_cash_facts.py",
                "audit_p1_cash_census_counterexamples.py",
            )
        }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in {"results", "events", "inputs"}}))


if __name__ == "__main__":
    main()
