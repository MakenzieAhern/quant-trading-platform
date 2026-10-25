"""Reconcile sourced retained ratios; opt-in fractions need approved policy and explicit dates."""

import argparse
import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.reconcile_distribution_cash import verified
from scripts.reconcile_retained_bonus_fraction_policy import APPROVAL_SHA256, POLICY_ID
from scripts.retained_bonus_terms import retained_ratio, same_day_listing


def approved_fraction_policy(path: Path) -> None:
    if sha256_file(path) != "f7c959ea29bbb6aa1e712ff897947d2cfb2932506ace2e2bef1ce567aec9a754":
        raise ValueError("RETAINED_BONUS_FRACTION_POLICY_NOT_APPROVED")
    policy = json.loads(path.read_bytes())
    policies = {row["class"]: row for row in policy["policies"]}
    if (
        policy.get("status") != "FROZEN_POLICY_CATALOG_NOT_DATASET"
        or policy.get("revision") != 3
        or policy.get("lineage", {}).get("retained_bonus_fraction_approval_sha256")
        != APPROVAL_SHA256
        or policies.get("RETAINED_BONUS_FRACTION", {}).get("policy_id") != POLICY_ID
    ):
        raise ValueError("RETAINED_BONUS_FRACTION_POLICY_NOT_APPROVED")


def source_ratio(
    pages: list[str], symbol: str, allow_fraction_policy: bool
) -> tuple[Decimal, bool]:
    try:
        return retained_ratio(pages, symbol, require_integral_components=True), False
    except ValueError as exc:
        if not allow_fraction_policy or str(exc) != "FRACTIONAL_COMPONENT_ALLOCATION_UNRESOLVED":
            raise
    return retained_ratio(pages, symbol), True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--date-links", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--fraction-policy",
        action="store_true",
        help="Approved fractional ratios; requires --explicit-same-day evidence",
    )
    parser.add_argument(
        "--explicit-same-day",
        action="store_true",
        help="Separate candidate ledger requiring official same-ex-date credit/listing terms",
    )
    args = parser.parse_args()
    if args.fraction_policy and not args.explicit_same_day:
        parser.error(
            "--fraction-policy requires --explicit-same-day; no inferred registry boundary"
        )
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
    if args.fraction_policy:
        approved_fraction_policy(policy)
    paths.extend([policy, *args.date_links])
    boundary = {(r["symbol"], r["ex_date"]): r for r in boundaries["rows"]}
    links, years = {}, set()
    for path in sorted(args.date_links):
        manifest = verified(path)
        if manifest["year"] in years:
            raise ValueError("DUPLICATE_YEAR_INPUT")
        years.add(manifest["year"])
        source = Path(manifest["inputs"][0]["path"])
        if sha256_file(source) != manifest["inputs"][0]["sha256"]:
            raise ValueError("DATE_LINK_SOURCE_CHANGED")
        paths.append(source)
        # Paths/cache are relative to the producing pool, not always the distribution pool.
        source_root = root if source.parent == root else source.parent.parent
        if not source_root.resolve().is_relative_to(args.staging.resolve()):
            raise ValueError("DATE_LINK_SOURCE_OUTSIDE_STAGING")
        sources = {}
        for doc in verified(source)["documents"]:
            if doc["retrieval_status"] == "PASS":
                sources[doc["url"], doc["source_sha256"]] = doc
        for row in manifest["results"]:
            key = row["symbol"], row["record_date"], row["ex_date"]
            if int(row["ex_date"][:4]) != manifest["year"]:
                raise ValueError("DATE_LINK_ROW_YEAR_MISMATCH")
            if key in links:
                raise ValueError("DUPLICATE_DATE_LINK_IDENTITY")
            links[key] = [
                (match, sources[match["url"], match["source_sha256"]], source_root)
                for match in row["documents"]
            ]
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
            args.fraction_policy
            and int(key[2][:4]) in years
            and (len(values) != 1 or any(not v.is_finite() or v <= 0 for v in values))
        ):
            rows.append(
                dict(
                    symbol=key[0],
                    record_date=key[1],
                    ex_date=key[2],
                    ratio=None,
                    evidence=[],
                    unresolved_documents=[],
                    status="UNRESOLVED_ORACLE_RATIO",
                )
            )
            continue
        if (
            int(key[2][:4]) not in years
            or len(values) != 1
            or any(
                not v.is_finite()
                or v <= 0
                or (not args.fraction_policy and v != v.to_integral_value())
                for v in values
            )
            or (not args.explicit_same_day and schedule.get("status") != "NEXT_ACCEPTED_SESSION")
        ):
            continue
        ratio = next(iter(values))
        result = dict(symbol=key[0], record_date=key[1], ex_date=key[2], ratio=str(ratio))
        evidence, failures = [], []
        uses_fraction_policy = False
        listing_date = key[2] if args.explicit_same_day else schedule["next_session"]
        for match, doc, source_root in sorted(
            links.get(key, []), key=lambda item: (item[0]["url"], item[0]["source_sha256"])
        ):
            pdf = (source_root / doc["source_path"]).resolve()
            cache = source_root / "batch-v1/text" / (doc["source_sha256"] + ".json")
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
                terms, needs_fraction_policy = source_ratio(
                    extracted["pages"],
                    key[0],
                    args.fraction_policy,
                )
                if terms != ratio:
                    raise ValueError("BONUS_EXCHANGE_TERMS_DISAGREE")
                uses_fraction_policy |= needs_fraction_policy
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
        if uses_fraction_policy:
            result["status"] = "EXACT_SOURCE_RATIO_APPROVED_FRACTION_CONVENTION"
            result["fraction_policy_id"] = POLICY_ID
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
                    "FRACTION_RETAINED_BONUS_EXPLICIT_SAME_DAY_V1"
                    if uses_fraction_policy
                    else "INTEGER_RETAINED_BONUS_EXPLICIT_SAME_DAY_V21"
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
                policy_id=POLICY_ID if uses_fraction_policy else "BASIS_CONSERVED_RETAINED_BONUS",
                support_state=(
                    "EXACT_SOURCE_RATIO_WITH_APPROVED_FRACTION_CONVENTION"
                    if uses_fraction_policy
                    else "SUPPORTED_FOR_INTEGER_HOLDINGS_EXPLICIT_SAME_DAY"
                    if args.explicit_same_day
                    else "SUPPORTED_FOR_INTEGER_HOLDINGS_NEXT_SESSION_SCHEDULE"
                ),
                source_oracle_evidence_sha256=original["evidence_sha256"],
                scheduled_listing_not_actual_tradability=not args.explicit_same_day,
                accounting_scope=(
                    "WHOLE_POSITION_FLOOR_NO_CASH_BASIS_CONSERVED"
                    if uses_fraction_policy
                    else "INTEGER_HOLDINGS_NO_FRACTION_EXPLICIT_SAME_DAY"
                    if args.explicit_same_day
                    else "INTEGER_HOLDINGS_NO_FRACTION_NEXT_SESSION_SCHEDULE"
                ),
            )
        )
        rows.append(result)
    report = dict(
        scope=(
            "ALL_POSITIVE_ORACLE_RATIOS_EXPLICIT_SAME_DAY_NOT_ECONOMIC_ACCEPTANCE"
            if args.fraction_policy
            else "BOUNDED_INTEGER_EXPLICIT_SAME_DAY_BONUS_NOT_FULL_CENSUS"
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
    if args.fraction_policy:
        report["fraction_policy_approval_sha256"] = APPROVAL_SHA256
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
