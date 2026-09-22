"""Close the bounded retained-bonus ledger under the approved generic fraction policy."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from decimal import Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.link_distribution_notices import notice_dates
from scripts.reconcile_distribution_cash import verified
from scripts.retained_bonus_terms import retained_ratio

APPROVAL_SHA256 = "26bf7dafd15bf2eca4476b2dfeaa09b5fc95ee90dbe2769637ae9a21bfa603e5"
PRIOR_POLICY_SHA256 = "8e4269e5b62a7a738e4e46a0f0caada47fe07af98b482ae3f81fd946cf759c79"
POLICY_ID = "CN_A_RETAINED_BONUS_FRACTIONAL_SHARE_POLICY_V1"


def restructuring_holder_ratio(pages: list[str]) -> Decimal:
    """Return the ordinary-holder retained ratio; zero means no entitlement."""
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "\n".join(pages)))
    holder_ratios = {
        Decimal(value) / Decimal(10)
        for value in re.findall(
            r"(?:其他(?:全部)?股东|全体股东).{0,300}?每10股转增(?:约)?(\d+(?:\.\d+)?)股",
            text,
        )
    }
    holder_ratios.update(
        Decimal(value) / Decimal(10)
        for value in re.findall(
            r"10转(?:约)?(\d+(?:\.\d+)?)股部分.{0,80}?将在.{0,180}?"
            r"其他(?:全部)?股东.{0,50}?无偿分配",
            text,
        )
    )
    if len(holder_ratios) == 1:
        return next(iter(holder_ratios))
    if holder_ratios:
        raise ValueError("RESTRUCTURING_ORDINARY_HOLDER_RATIO_UNRESOLVED")
    if re.search(r"不(?:再)?向(?:原股东|原出资人|股东)(?:进行)?分配", text):
        return Decimal(0)
    direct = {
        Decimal(value) / Decimal(base)
        for base, value in re.findall(
            r"每(10|1)股转增(\d+(?:\.\d+)?)股的比例"
            r"(?:对.{0,100}?全体股东实施|登记到.{0,100}?全体股东证券账户)",
            text,
        )
    }
    if len(direct) == 1:
        return next(iter(direct))
    if direct:
        raise ValueError("RESTRUCTURING_ORDINARY_HOLDER_RATIO_UNRESOLVED")
    values = {
        Decimal(value) / Decimal(base)
        for base, value in re.findall(
            r"每(10|1)股转增(\d+(?:\.\d+)?)股的比例.{0,160}?全体股东", text
        )
    }
    if len(values) != 1:
        raise ValueError("RESTRUCTURING_ORDINARY_HOLDER_RATIO_UNRESOLVED")
    return next(iter(values))


def combined_retained_ratio(pages: list[str], symbol: str) -> Decimal:
    """Prefer the shared parser; resolve only conflicting per-share summary typos."""
    try:
        return retained_ratio(pages, symbol)
    except ValueError as exc:
        if str(exc) != "CONFLICTING_BONUS_COMPONENT":
            raise
        conflict = exc
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "\n".join(pages)))
    send = {
        Decimal(value) / Decimal(10)
        for value in re.findall(r"每10股(?:送股股数:?|送(?:红股|股)?)(\d+(?:\.\d+)?)股", text)
    }
    transfer = {
        Decimal(value) / Decimal(10)
        for value in re.findall(r"每10股转增(?:股本|股|股数:?)?(\d+(?:\.\d+)?)股", text)
    }
    if len(send) <= 1 and len(transfer) <= 1 and (send or transfer):
        return sum(send, Decimal(0)) + sum(transfer, Decimal(0))

    def component(values: set[Decimal]) -> Decimal:
        if not values:
            return Decimal(0)
        if len(values) == 1:
            return next(iter(values))
        largest = max(values, default=Decimal(0))
        if largest and sum(values - {largest}, Decimal(0)) == largest:
            return largest
        return sum(values, Decimal(0))

    all_transfer = {
        Decimal(value) / Decimal(base or "1")
        for base, value in re.findall(r"每(10|1)?股转增(?:股本|股|股数:?)?(\d+(?:\.\d+)?)股", text)
    }
    if not (send or all_transfer):
        raise ValueError("CONFLICTING_BONUS_COMPONENT") from conflict
    return component(send) + component(all_transfer)


def _documents_and_links(prior: dict, distribution_root: Path) -> tuple[list[dict], list[dict]]:
    documents, links = [], []
    for item in prior["inputs"]:
        path = Path(item["path"])
        if path.name == "source-manifest.json" and distribution_root in path.parents:
            documents.extend(verified(path)["documents"])
        elif path.name.startswith("date-links-"):
            manifest = verified(path)
            for row in manifest["results"]:
                links.extend(
                    {**document, "identity": (row["symbol"], row["record_date"], row["ex_date"])}
                    for document in row["documents"]
                )
    return documents, links


def _unique_document(documents: list[dict], source_sha256: str) -> dict:
    matches = [row for row in documents if row.get("source_sha256") == source_sha256]
    identities = {
        (row["issuer"], row["published_on"], row["title"], row["url"], row["source_sha256"])
        for row in matches
    }
    if len(identities) != 1:
        raise ValueError(f"BONUS_SOURCE_NOT_UNIQUE:{source_sha256}")
    return min(matches, key=lambda row: row["source_path"])


def _source(
    row: dict,
    documents: list[dict],
    links: list[dict],
    distribution_root: Path,
) -> tuple[dict, list[str], str]:
    hashes = {item["source_sha256"] for item in row["unresolved_documents"]}
    if not hashes:
        raise ValueError(f"BONUS_SOURCE_HASH_NOT_UNIQUE:{row['symbol']}:{row['ex_date']}")
    candidates = [_unique_document(documents, source_sha256) for source_sha256 in hashes]
    best_rank = min("提示" in document["title"] for document in candidates)
    preferred = [document for document in candidates if ("提示" in document["title"]) == best_rank]
    if len(preferred) != 1:
        raise ValueError(f"BONUS_SOURCE_HASH_NOT_UNIQUE:{row['symbol']}:{row['ex_date']}")
    document = preferred[0]
    source_sha256 = document["source_sha256"]
    identity = row["symbol"], row["record_date"], row["ex_date"]
    linked = [
        item
        for item in links
        if item["identity"] == identity and item["source_sha256"] == source_sha256
    ]
    if len(linked) != 1:
        raise ValueError(f"BONUS_DATE_LINK_NOT_UNIQUE:{row['symbol']}:{row['ex_date']}")
    pdf = (distribution_root / document["source_path"]).resolve()
    cache = distribution_root / "batch-v1/text" / f"{source_sha256}.json"
    if (
        document["retrieval_status"] != "PASS"
        or document["issuer"] != row["symbol"]
        or not document["published_on"] <= row["record_date"] < row["ex_date"]
        or not pdf.is_relative_to(distribution_root.resolve())
        or sha256_file(pdf) != source_sha256
        or sha256_file(cache) != linked[0]["extraction_sha256"]
    ):
        raise ValueError(f"BONUS_SOURCE_IDENTITY_CHANGED:{row['symbol']}:{row['ex_date']}")
    extracted = json.loads(cache.read_bytes())
    if extracted["source_sha256"] != source_sha256:
        raise ValueError(f"BONUS_TEXT_CACHE_CHANGED:{row['symbol']}:{row['ex_date']}")
    return document, extracted["pages"], sha256_file(cache)


def reconcile(prior: dict, staging: Path, policy_path: Path) -> dict:
    distribution_root = staging / "full-distribution-notices-v1"
    documents, links = _documents_and_links(prior, distribution_root)
    oracle = verified(staging / "full-bonus-inventory-v1/source-oracle-v1.json")
    boundaries = verified(staging / "full-bonus-inventory-v1/listing-boundary-check-v2.json")
    master = verified(staging / "full-code-transitions-v1/master-code-intervals.json")
    instruments = verified(staging / "full-instrument-scope-v1/classification-manifest-v3.json")
    by_oracle = {(row["symbol"], row["record_date"], row["ex_date"]): row for row in oracle["rows"]}
    by_boundary = {(row["symbol"], row["ex_date"]): row for row in boundaries["rows"]}
    ordinary = {
        row["classification"]["security_id"]["value"]
        for row in instruments["classifications"]
        if row["classification"]["instrument_type"] == "COMMON_A_SHARE"
    }
    replacements, accepted, no_entitlement = {}, [], []
    unresolved = [
        row for row in prior["results"] if row["status"] != "EXACT_INTEGER_RETAINED_BONUS"
    ]
    if len(unresolved) != 45:
        raise ValueError("BONUS_PRIOR_RESIDUAL_CHANGED")
    for row in sorted(unresolved, key=lambda item: (item["symbol"], item["ex_date"])):
        key = row["symbol"], row["record_date"], row["ex_date"]
        reasons = {item["reason"] for item in row["unresolved_documents"]}
        document, pages, text_cache_sha256 = _source(row, documents, links, distribution_root)
        schedule = by_boundary[key[0], key[2]]
        members = [
            member
            for member in master["records"]
            if member["symbol"] == key[0]
            and member["security_id"] in ordinary
            and member["effective_from"]
            <= key[1]
            < key[2]
            <= (member["effective_to"] or "2025-12-31")
            and member["listing_date"] <= key[1]
            and schedule["next_session"] <= (member["delisting_date"] or "2025-12-31")
        ]
        if schedule["status"] != "NEXT_ACCEPTED_SESSION" or len(members) != 1:
            raise ValueError(f"BONUS_LIFECYCLE_CHANGED:{key[0]}:{key[2]}")
        if notice_dates(pages) != ([key[1]], [key[2]]):
            raise ValueError(f"BONUS_NOTICE_DATES_CHANGED:{key[0]}:{key[2]}")
        total_ratio = Decimal(row["ratio"])
        holder_ratio = total_ratio
        status = "EXACT_RETAINED_BONUS_COMBINED_COMPONENT_POLICY"
        policies = ["BASIS_CONSERVED_RETAINED_BONUS", POLICY_ID]
        if reasons == {"FRACTIONAL_COMPONENT_ALLOCATION_UNRESOLVED"}:
            try:
                parsed_ratio = combined_retained_ratio(pages, key[0])
            except ValueError as exc:
                raise ValueError(f"BONUS_TERMS_UNRESOLVED:{key[0]}:{key[2]}:{exc}") from exc
            if parsed_ratio != total_ratio:
                raise ValueError(f"BONUS_TERMS_CHANGED:{key[0]}:{key[2]}")
        elif reasons == {"NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW"}:
            try:
                holder_ratio = restructuring_holder_ratio(pages)
            except ValueError as exc:
                raise ValueError(
                    f"RESTRUCTURING_HOLDER_RATIO_UNRESOLVED:{key[0]}:{key[2]}"
                ) from exc
            policies.append("CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1")
            if holder_ratio == 0:
                result = {
                    **row,
                    "evidence": [document],
                    "unresolved_documents": [],
                    "status": "RESTRUCTURING_NO_ORIGINAL_HOLDER_ENTITLEMENT",
                    "ordinary_holder_ratio": "0",
                    "source_total_ratio": str(total_ratio),
                    "policy_ids": policies,
                }
                replacements[key] = result
                no_entitlement.append(
                    {
                        "security_id": members[0]["security_id"],
                        "record_date": key[1],
                        "ex_date": key[2],
                        "source_sha256": document["source_sha256"],
                        "classification": "NO_ORIGINAL_HOLDER_ENTITLEMENT_NO_PORTFOLIO_MUTATION",
                        "policy_id": "CN_A_RESTRUCTURING_BONUS_PASS_THROUGH_POLICY_V1",
                    }
                )
                continue
            status = "EXACT_RESTRUCTURING_RETAINED_BONUS_COMPONENT_POLICY"
        else:
            raise ValueError(f"BONUS_UNEXPECTED_RESIDUAL:{key[0]}:{key[2]}:{sorted(reasons)}")
        result = {
            **row,
            "evidence": [document],
            "unresolved_documents": [],
            "status": status,
            "ordinary_holder_ratio": str(holder_ratio),
            "source_total_ratio": str(total_ratio),
            "policy_ids": policies,
        }
        action = CorporateAction.model_validate(
            {
                "security_id": {"value": members[0]["security_id"]},
                "action_type": "BONUS_SHARE",
                "announcement_date": document["published_on"],
                "effective_date": key[2],
                "record_date": key[1],
                "ex_date": key[2],
                "listing_date": schedule["next_session"],
                "share_ratio": str(holder_ratio),
                "source_document": document["title"],
                "source_url": document["url"],
                "source_document_sha256": document["source_sha256"],
                "retrieved_at": document["retrieved_at_utc"],
                "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
                "source_version": "RETAINED_BONUS_FRACTION_POLICY_V1",
                "source_record_hash": canonical_sha256(result),
                "completeness": "COMPLETE",
            }
        )
        require_supported_corporate_action(action)
        accepted.append(
            {
                "event": action.model_dump(mode="json"),
                "event_checksum": action.event_checksum,
                "policy_id": POLICY_ID,
                "base_policy_id": "BASIS_CONSERVED_RETAINED_BONUS",
                "component_allocation": "COMBINE_OFFICIAL_COMPONENTS_THEN_FLOOR_FINAL_POSITION",
                "support_state": "SUPPORTED_BY_GENERIC_RETAINED_BONUS_FRACTION_POLICY",
                "source_oracle_evidence_sha256": by_oracle[key]["evidence_sha256"],
                "source_total_ratio": str(total_ratio),
                "ordinary_holder_ratio": str(holder_ratio),
                "scheduled_listing_not_actual_tradability": True,
                "accounting_scope": "WHOLE_POSITION_FLOOR_NO_CASH_BASIS_CONSERVED",
                "text_cache_sha256": text_cache_sha256,
            }
        )
        replacements[key] = result
    results = sorted(
        (
            replacements.get((row["symbol"], row["record_date"], row["ex_date"]), row)
            for row in prior["results"]
        ),
        key=lambda row: (row["symbol"], row["record_date"], row["ex_date"]),
    )
    events = sorted(
        [*prior["events"], *accepted],
        key=lambda row: (
            row["event"]["security_id"]["value"],
            row["event"]["record_date"],
            row["event"]["ex_date"],
        ),
    )
    return {
        "results": results,
        "events": events,
        "no_entitlement_classifications": sorted(
            no_entitlement, key=lambda row: (row["security_id"], row["ex_date"])
        ),
        "accepted_events": len(events),
        "newly_accepted_fraction_policy_events": len(accepted),
        "newly_classified_no_entitlement": len(no_entitlement),
        "counts": dict(sorted(Counter(row["status"] for row in results).items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prior = verified(args.prior)
    for item in prior["inputs"]:
        path = Path(item["path"])
        if path.name == args.policy.name:
            if item["sha256"] != PRIOR_POLICY_SHA256:
                raise ValueError("BONUS_PRIOR_POLICY_LINEAGE_CHANGED")
            continue
        elif sha256_file(path) != item["sha256"]:
            raise ValueError(f"BONUS_PRIOR_INPUT_CHANGED:{path}")
    policy = json.loads(args.policy.read_bytes())
    policies = {row["class"]: row for row in policy["policies"]}
    if (
        policy["status"] != "FROZEN_POLICY_CATALOG_NOT_DATASET"
        or policy["revision"] != 3
        or policy["lineage"]["retained_bonus_fraction_approval_sha256"] != APPROVAL_SHA256
        or policies["RETAINED_BONUS_FRACTION"]["policy_id"] != POLICY_ID
    ):
        raise ValueError("RETAINED_BONUS_FRACTION_POLICY_NOT_APPROVED")
    result = reconcile(prior, args.staging, args.policy)
    reversed_result = reconcile(
        {
            **prior,
            "inputs": list(reversed(prior["inputs"])),
            "results": list(reversed(prior["results"])),
            "events": list(reversed(prior["events"])),
        },
        args.staging,
        args.policy,
    )
    if result != reversed_result:
        raise ValueError("RETAINED_BONUS_POLICY_INPUT_ORDER_CHANGED")
    report = {
        **{
            key: value
            for key, value in prior.items()
            if key
            not in {
                "manifest_sha256",
                "results",
                "events",
                "counts",
                "accepted_events",
                "scope",
                "full_dataset_created",
            }
        },
        **result,
        "report_version": "R5_RETAINED_BONUS_POLICY_CLOSURE_V2",
        "scope": "BOUNDED_RETAINED_BONUS_NEXT_SESSION_NOT_FULL_CENSUS",
        "prior_report_path": str(args.prior),
        "prior_report_sha256": sha256_file(args.prior),
        "policy_path": str(args.policy),
        "policy_sha256": sha256_file(args.policy),
        "human_approval_sha256": APPROVAL_SHA256,
        "parser_sha256": sha256_file(Path(__file__)),
        "input_order_reproducibility": "PASS",
        "unresolved_candidates": sum(
            row["status"] == "UNRESOLVED_TERMS_OR_LIFECYCLE" for row in result["results"]
        ),
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if key not in {"results", "events"}}
        )
    )


if __name__ == "__main__":
    main()
