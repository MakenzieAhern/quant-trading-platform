"""Close residual ordinary-holder bonus facts from retained official sources."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.corporate_actions import CorporateAction, require_supported_corporate_action
from scripts.audit_p1_public_fact_requirements import verified
from scripts.reconcile_retained_bonus_fraction_policy import APPROVAL_SHA256, POLICY_ID


def implementation_ratio(pages: list[str]) -> Decimal:
    text = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "\n".join(pages)))
    preferred = re.findall(
        r"权益分派方案为:.{0,500}?向全体股东每(10|1)?股转增(?:股)?(\d+(?:\.\d+)?)股",
        text,
    )
    candidates = preferred or re.findall(r"向全体股东每(10|1)?股转增(?:股)?(\d+(?:\.\d+)?)股", text)
    ratios = {Decimal(value) / Decimal(base or "1") for base, value in candidates}
    if len(ratios) != 1:
        raise ValueError("RESIDUAL_BONUS_RATIO_NOT_UNIQUE")
    return next(iter(ratios))


def exchange_matches(ratio: Decimal, evidence: list[dict]) -> str | None:
    values = {Decimal(row["ratio"]) for row in evidence}
    if values == {ratio}:
        return "EXACT_EXCHANGE_CORROBORATION"
    if len(values) == 1:
        value = next(iter(values))
        rounded = ratio.quantize(
            Decimal(1).scaleb(value.as_tuple().exponent), rounding=ROUND_HALF_UP
        )
        if rounded == value:
            return "ROUNDED_EXCHANGE_CORROBORATION"
    return None


def source_index(staging: Path, wanted: set[tuple[str, str]]) -> dict[tuple[str, str], dict]:
    found = {}
    for manifest_path in sorted(staging.rglob("source-manifest.json")):
        raw = json.loads(manifest_path.read_bytes())
        if not isinstance(raw, dict):
            continue
        for source in raw.get("documents", []):
            key = source.get("url"), source.get("source_sha256")
            if key not in wanted or source.get("retrieval_status") != "PASS":
                continue
            verified(manifest_path)
            root = manifest_path.parents[1]
            pdf = (root / source["source_path"]).resolve()
            cache = root / "batch-v1/text" / f"{key[1]}.json"
            if sha256_file(pdf) != key[1] or not cache.is_file():
                raise ValueError(f"RESIDUAL_BONUS_SOURCE_CHANGED:{key[0]}")
            extracted = json.loads(cache.read_bytes())
            if extracted["source_sha256"] != key[1]:
                raise ValueError(f"RESIDUAL_BONUS_TEXT_CHANGED:{key[0]}")
            candidate = {
                **source,
                "pages": extracted["pages"],
                "text_cache_sha256": sha256_file(cache),
                "manifest_sha256": sha256_file(manifest_path),
            }
            prior = found.get(key)
            if prior and any(
                prior[field] != candidate[field] for field in ("issuer", "title", "published_on")
            ):
                raise ValueError(f"CONFLICTING_RESIDUAL_BONUS_SOURCE:{key[0]}")
            found[key] = candidate
    return found


def listing_date(text: str, ex_date: str) -> str | None:
    year, month, day = map(int, ex_date.split("-"))
    token = f"{year}年{month}月{day}日"
    return ex_date if re.search(rf"上市(?:流通)?(?:日期|日|时间)[:为]?{token}", text) else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "queue",
        "triage",
        "cash-base",
        "prior-bonus",
        "oracle",
        "master",
        "source-manifest",
        "source-root",
        "staging",
        "policy",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    queue = json.loads(args.queue.read_bytes())
    triage, cash, prior_bonus, oracle, sources = (
        verified(path)
        for path in (
            args.triage,
            args.cash_base,
            args.prior_bonus,
            args.oracle,
            args.source_manifest,
        )
    )
    master = json.loads(args.master.read_bytes())
    policy = json.loads(args.policy.read_bytes())
    if (
        triage["source_requirements_sha256"] != sha256_file(args.queue)
        or triage["source_manifest_sha256"] != sha256_file(args.source_manifest)
        or policy["lineage"]["retained_bonus_fraction_approval_sha256"] != APPROVAL_SHA256
        or not any(row.get("policy_id") == POLICY_ID for row in policy["policies"])
    ):
        raise ValueError("RESIDUAL_BONUS_INPUT_CHANGED")
    requirements = {row["document_id"]: row for row in queue}
    source_rows = {row["document_id"]: row for row in sources["documents"]}
    candidates = [
        row
        for row in triage["documents"]
        if row["document_id"] in requirements
        and not re.search(r"重整|资本公积", requirements[row["document_id"]]["title"])
        and (
            row["bonus_candidate_per_share"] is not None
            or row["bonus_parser_error"]
            in {
                "CONFLICTING_BONUS_COMPONENT",
                "NONSTANDARD_ENTITLEMENT_REQUIRES_REVIEW",
            }
        )
    ]
    issuers = {requirements[row["document_id"]]["issuer"] for row in candidates}
    retained = [row for row in cash["accepted_cash_matches"] if row["issuer"] in issuers]
    prior_rows = [row for row in prior_bonus["corroborated"] if row["issuer"] in issuers]
    wanted = {(row["url"], row["source_sha256"]) for row in [*retained, *prior_rows]}
    historical_sources = source_index(args.staging, wanted)
    oracle_by_key = {
        (row["symbol"], row["record_date"], row["ex_date"]): row for row in oracle["rows"]
    }
    closed, events = [], []
    for row in sorted(candidates, key=lambda item: item["document_id"]):
        requirement = requirements[row["document_id"]]
        source = source_rows[row["document_id"]]
        cache = args.source_root / "batch-v1/text" / f"{source['source_sha256']}.json"
        extracted = json.loads(cache.read_bytes())
        if (
            source["retrieval_status"] != "PASS"
            or source["source_sha256"] != row["source_sha256"]
            or sha256_file(cache) != row["text_cache_sha256"]
            or extracted["source_sha256"] != row["source_sha256"]
        ):
            raise ValueError(f"RESIDUAL_BONUS_CURRENT_SOURCE_CHANGED:{row['document_id']}")
        try:
            ratio = implementation_ratio(extracted["pages"])
        except ValueError as exc:
            raise ValueError(f"RESIDUAL_BONUS_RATIO_UNRESOLVED:{row['document_id']}") from exc
        dates = list(zip(row["record_dates"], row["ex_dates"], strict=True))
        if not dates:
            cash_dates = sorted(
                (
                    item["record_date"],
                    item["ex_date"],
                )
                for item in retained
                if item["issuer"] == requirement["issuer"]
                and requirement["published_on"] <= item["record_date"]
            )
            dates = cash_dates[:1]
        if len(dates) != 1:
            raise ValueError(f"RESIDUAL_BONUS_DATES_UNRESOLVED:{row['document_id']}")
        record_date, ex_date = dates[0]
        key = requirement["issuer"], record_date, ex_date
        identities = {
            item["security_id"]
            for item in master["records"]
            if item["symbol"] == key[0]
            and item["effective_from"]
            <= record_date
            < ex_date
            <= (item["effective_to"] or "9999-12-31")
        }
        if len(identities) != 1 or not requirement["published_on"] <= ex_date:
            raise ValueError(f"RESIDUAL_BONUS_IDENTITY_UNRESOLVED:{row['document_id']}")
        oracle_row = oracle_by_key.get(key)
        corroboration = exchange_matches(ratio, oracle_row["evidence"]) if oracle_row else None
        point_source = {
            **source,
            "pages": extracted["pages"],
            "text_cache_sha256": sha256_file(cache),
        }
        if requirement["published_on"] >= ex_date:
            earlier = []
            for item in [*prior_rows, *retained]:
                if item["issuer"] == key[0] and (item["record_date"], item["ex_date"]) == key[1:]:
                    candidate = historical_sources.get((item["url"], item["source_sha256"]))
                    if candidate and candidate["published_on"] < ex_date:
                        try:
                            candidate_ratio = implementation_ratio(candidate["pages"])
                        except ValueError:
                            continue
                        if candidate_ratio == ratio:
                            earlier.append(candidate)
            if not earlier:
                raise ValueError(
                    f"RESIDUAL_BONUS_POINT_IN_TIME_SOURCE_MISSING:{row['document_id']}"
                )
            point_source = max(earlier, key=lambda item: (item["published_on"], item["url"]))
        event = CorporateAction.model_validate(
            {
                "security_id": {"value": next(iter(identities))},
                "action_type": "BONUS_SHARE",
                "announcement_date": point_source["published_on"],
                "effective_date": ex_date,
                "record_date": record_date,
                "ex_date": ex_date,
                "listing_date": listing_date(
                    re.sub(r"\s+", "", unicodedata.normalize("NFKC", "".join(extracted["pages"]))),
                    ex_date,
                ),
                "share_ratio": str(ratio),
                "source_document": point_source["title"],
                "source_url": point_source["url"],
                "source_document_sha256": point_source["source_sha256"],
                "retrieved_at": point_source["retrieved_at_utc"],
                "source_provider": "OFFICIAL_ISSUER_CNINFO_EXCHANGE_RECONCILED",
                "source_version": "RESIDUAL_BONUS_FACT_CLOSURE_V1",
                "source_record_hash": canonical_sha256(
                    {
                        "document_id": row["document_id"],
                        "record_date": record_date,
                        "ex_date": ex_date,
                        "share_ratio": str(ratio),
                        "point_source_sha256": point_source["source_sha256"],
                    }
                ),
                "completeness": "COMPLETE",
            }
        )
        require_supported_corporate_action(event)
        classification = corroboration or "SINGLE_OFFICIAL_ISSUER_SOURCE"
        closed.append(
            {
                "document_id": row["document_id"],
                "affected_events": requirement["affected_events"],
                "issuer": key[0],
                "security_id": next(iter(identities)),
                "record_date": record_date,
                "ex_date": ex_date,
                "bonus_ratio": str(ratio),
                "classification": classification,
                "source_sha256": row["source_sha256"],
                "point_in_time_source_sha256": point_source["source_sha256"],
                "exchange_evidence_sha256": oracle_row["evidence_sha256"] if oracle_row else None,
                "accounting_policy_id": POLICY_ID,
            }
        )
        events.append(
            {
                "event": event.model_dump(mode="json"),
                "event_checksum": event.event_checksum,
                "classification": classification,
                "policy_id": POLICY_ID,
            }
        )
    closed.sort(key=lambda row: row["document_id"])
    events.sort(key=lambda row: (row["event"]["security_id"]["value"], row["event"]["ex_date"]))
    report = {
        "report_version": "P1_RESIDUAL_BONUS_FACT_CLOSURE_V2",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            name: sha256_file(path)
            for name, path in (
                ("queue", args.queue),
                ("triage", args.triage),
                ("cash_base", args.cash_base),
                ("prior_bonus", args.prior_bonus),
                ("oracle", args.oracle),
                ("master", args.master),
                ("source_manifest", args.source_manifest),
                ("policy", args.policy),
            )
        },
        "closed_documents": len(closed),
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "classifications": dict(sorted(Counter(row["classification"] for row in closed).items())),
        "closed": closed,
        "events": events,
        "new_economic_events_created": len(events),
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps({key: value for key, value in report.items() if key not in {"closed", "events"}})
    )


if __name__ == "__main__":
    main()
