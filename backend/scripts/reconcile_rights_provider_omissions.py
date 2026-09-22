"""Add explicitly reviewed official omissions without pretending the vendor is a census."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets import CorporateAction


def reviewed_action(claim, issuance, result):
    for source in (issuance, result):
        if source["issuer"] != claim["security_id"].rsplit(":", 1)[-1]:
            raise ValueError("OFFICIAL_RIGHTS_ISSUER_MISMATCH")
    if not issuance["published_on"] <= claim["record_date"] < claim["ex_date"]:
        raise ValueError("OFFICIAL_RIGHTS_CHRONOLOGY_MISMATCH")
    if result["published_on"] != claim["ex_date"]:
        raise ValueError("REVIEWED_RESULT_PUBLICATION_MISMATCH")
    action = CorporateAction.model_validate(
        dict(
            security_id={"value": claim["security_id"]},
            action_type="RIGHTS_RELATED_EVENT",
            announcement_date=issuance["published_on"],
            effective_date=claim["ex_date"],
            **{
                key: claim[key]
                for key in (
                    "record_date",
                    "ex_date",
                    "share_ratio",
                    "subscription_price",
                    "subscription_end_date",
                )
            },
            rights_event_class="STANDARD_DIRECT_SUBSCRIPTION_RIGHTS_ISSUE",
            source_provider="CNINFO-official-issuer",
            source_version="OFFICIAL_RIGHTS_PROVIDER_OMISSIONS_V1",
            source_record_hash=canonical_sha256(claim),
            source_document=result["title"],
            source_url=result["url"],
            source_document_sha256=result["source_sha256"],
            retrieved_at=result["retrieved_at_utc"],
            completeness="PARTIAL",
        )
    )
    if action.rights_issues():
        raise ValueError(f"REVIEWED_RIGHTS_STILL_UNRESOLVED:{action.rights_issues()}")
    return action


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    prior = json.loads(args.inventory.read_bytes())
    batch = json.loads((args.root / "batch-v2/source-manifest.json").read_bytes())
    review = json.loads(args.review.read_bytes())
    documents = {
        d["source_sha256"]: d for d in batch["documents"] if d["retrieval_status"] == "PASS"
    }
    rows = list(prior["rows"])
    identities = {r["event_id"] for r in rows}
    for claim in sorted(review["events"], key=lambda c: (c["security_id"], c["record_date"])):
        sources = [documents[claim[key]] for key in ("issuance_sha256", "result_sha256")]
        for source in sources:
            if sha256_file(args.root / source["source_path"]) != source["source_sha256"]:
                raise ValueError("OFFICIAL_RIGHTS_SOURCE_CHECKSUM_CHANGED")
        action = reviewed_action(claim, *sources)
        identity = f"{claim['security_id']}:{claim['record_date']}"
        if identity in identities:
            raise ValueError("DUPLICATE_ECONOMIC_RIGHTS_EVENT")
        identities.add(identity)
        rows.append(
            dict(
                event_id=identity,
                event=action.model_dump(mode="json"),
                event_checksum=action.event_checksum,
                classification=action.rights_classification,
                issues=action.rights_issues(),
                metadata_gaps=action.rights_metadata_gaps(),
                official_review=claim,
                sources=sources,
                point_in_time_admission="NOT_ADMITTED_FULL_AUTHORITY_PENDING",
                provider_omission=True,
            )
        )
    rows.sort(key=lambda r: r["event_id"])
    result = dict(
        parser_version="RIGHTS_PROVIDER_OMISSION_RECONCILIATION_V1",
        parser_sha256=sha256_file(Path(__file__)),
        review_sha256=sha256_file(args.review),
        prior_inventory_sha256=sha256_file(args.inventory),
        source_batch_sha256=sha256_file(args.root / "batch-v2/source-manifest.json"),
        rights_events_total=len(rows),
        official_provider_omissions=len(review["events"]),
        supported_standard_events=sum(not r["issues"] for r in rows),
        unresolved_events=sum(bool(r["issues"]) for r in rows),
        inventory_scope="OFFICIAL_PLUS_PROVIDER_IDENTIFIED_EVENTS_NOT_COMPLETE_EXCHANGE_CENSUS",
        census_status="PARTIAL",
        full_authority="NOT_ACCEPTED",
        rows=rows,
    )
    result["manifest_sha256"] = canonical_sha256(result)
    write_immutable(args.output, canonical_json_bytes(result) + b"\n")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
