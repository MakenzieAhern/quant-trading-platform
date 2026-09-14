"""Normalize reviewed mandatory stock mergers using existing accounting and source audits."""

import argparse
import json
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from app.domain.markets.mergers import MERGER_POLICY, ZERO_WHOLE_SHARE_POLICY, MergerEvent
from scripts.audit_merger_evidence import audit


def raw_boundaries(payload, exchange, code, start, end):
    key = {"SSE": "sh", "SZSE": "sz"}[exchange] + code
    rows = json.loads(payload.decode().split("=", 1)[-1])["data"][key]["day"]
    dates = [r[0] for r in rows if start <= r[0] <= end]
    if not dates or dates != sorted(set(dates)):
        raise ValueError("RAW_BOUNDARY_DATES_INVALID")
    return dates[0], dates[-1]


def event_from_review(row):
    exchange = row.get("exchange", "SZSE")
    parent_exchange = row.get("parent_exchange", exchange)
    successor_exchange = row.get("successor_exchange", exchange)
    return MergerEvent.model_validate(
        dict(
            parent_security={"value": f"CN-A:{parent_exchange}:" + row["parent"]},
            successor_security={"value": f"CN-A:{successor_exchange}:" + row["successor"]},
            conversion_ratio=row["conversion_ratio"],
            conversion_denominator=row.get("conversion_denominator", "1"),
            parent_last_trading_date=row["parent_last_trading_date"],
            record_date=row["record_date"],
            effective_date=row["effective_date"],
            successor_listing_date=row["successor_listing_date"],
            successor_shares_tradable_from=row.get("successor_shares_tradable_from"),
            activation_sources=row.get("activation_sources", []),
            official_fractional_method="GLOBAL_SHAREHOLDER_ALLOCATION_UNREPRODUCIBLE",
            research_fractional_method="FLOOR_NO_CASH_COMPENSATION_RESEARCH_CONVENTION",
            cash_election_offered=row["cash_election_offered"],
            zero_whole_share_policy=ZERO_WHOLE_SHARE_POLICY,
            sources=[
                dict(
                    url=row["source_url"],
                    sha256=row["source_sha256"],
                    published_on=row["publication_date"],
                    retrieved_at=row["retrieved_at"],
                    document="Official issuer merger implementation notice",
                ),
                *row.get("additional_event_sources", []),
            ],
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("root", "reviews", "master", "boundaries", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    reviews = json.loads(args.reviews.read_bytes())
    if reviews["policy"] != MERGER_POLICY:
        raise ValueError("POLICY_MISMATCH")
    if reviews["boundary_policy"] != "FIRST_POST_EVENT_TRADING_BOUNDARY_V1":
        raise ValueError("BOUNDARY_POLICY_MISMATCH")
    paths = [args.root / "batch-v2/source-manifest.json", args.master, args.boundaries]
    values = []
    for path in paths:
        value = json.loads(path.read_bytes())
        if (
            canonical_sha256({k: v for k, v in value.items() if k != "manifest_sha256"})
            != value["manifest_sha256"]
        ):
            raise ValueError("INPUT_MANIFEST_CHANGED")
        values.append(value)
    sources, master, boundaries = values
    results = []
    for row in sorted(reviews["cases"], key=lambda r: (r["effective_date"], r["parent"])):
        event = event_from_review(row)
        matches = [
            s for s in sources["documents"] if s.get("source_sha256") == row["source_sha256"]
        ]
        if not matches and row.get("source_path"):
            matches = [
                dict(
                    source_path=row["source_path"],
                    url=row["source_url"],
                    source_sha256=row["source_sha256"],
                    issuer=row["parent"],
                    published_on=row["publication_date"],
                    retrieved_at_utc=row["retrieved_at"],
                )
            ]
        if len(matches) != 1:
            raise ValueError("SOURCE_IDENTITY_AMBIGUOUS")
        source = matches[0]
        if source["issuer"] != row["parent"] or source["published_on"] != row["publication_date"]:
            raise ValueError("ISSUER_OR_PUBLICATION_MISMATCH")
        for code, expected, field, exchange in [
            (
                row["parent"],
                row.get("parent_delisting_date", row["effective_date"]),
                "delisting_date",
                row.get("parent_exchange", row.get("exchange", "SZSE")),
            ),
            (
                row["successor"],
                row["successor_listing_date"],
                "listing_date",
                row.get("successor_exchange", row.get("exchange", "SZSE")),
            ),
        ]:
            records = [
                m for m in master["records"] if m["symbol"] == code and m["exchange"] == exchange
            ]
            if len(records) != 1 or records[0][field] != expected:
                raise ValueError("MASTER_LIFECYCLE_MISMATCH")
            raw = [b for b in boundaries["results"] if b["symbol"] == code]
            if len(raw) != 1 or raw[0]["status"] != "BOUNDARY_CORROBORATION_ONLY":
                raise ValueError("TRADABLE_BOUNDARY_UNVERIFIED")
            b = raw[0]
            payload = args.boundaries.parent / f"{code}-{b['start']}-{b['end']}.json"
            payload = Path(b.get("source_path", payload)).resolve()
            if not payload.is_relative_to(args.root.resolve()):
                raise ValueError("RAW_BOUNDARY_OUTSIDE_STAGING")
            if sha256_file(payload) != b["source"]["sha256"]:
                raise ValueError("RAW_BOUNDARY_SOURCE_CHANGED")
            if raw_boundaries(payload.read_bytes(), exchange, code, b["start"], b["end"]) != (
                b["first_date"],
                b["last_date"],
            ):
                raise ValueError("RAW_BOUNDARY_RECEIPT_MISMATCH")
            observed = b["last_date"] if code == row["parent"] else b["first_date"]
            expected = (
                row["parent_last_trading_date"]
                if code == row["parent"]
                else row.get("first_post_event_trading_date", row["successor_listing_date"])
            )
            if observed != expected:
                raise ValueError("TRADABLE_BOUNDARY_MISMATCH")
        if (
            not row["parent_last_trading_date"]
            < row["continuous_suspension_from"]
            <= row["effective_date"]
        ):
            raise ValueError("SUSPENSION_BOUNDARY_MISMATCH")
        document = dict(
            path=source["source_path"],
            url=source["url"],
            sha256=source["source_sha256"],
            published_on=source["published_on"],
            retrieved_at_utc=source["retrieved_at_utc"],
        )
        review = dict(
            policy=MERGER_POLICY,
            documents=[document, *row.get("additional_review_documents", [])],
            reviewed_terms=row,
            boundary_policy=reviews["boundary_policy"],
            registry_timestamp="NOT_INFERRED",
        )
        result = audit(review, event, args.root)
        if (
            audit({**review, "documents": list(reversed(review["documents"]))}, event, args.root)
            != result
        ):
            raise ValueError("INPUT_ORDER_REPRODUCIBILITY_FAILED")
        results.append(result)
    if len({r["event_checksum"] for r in results}) != len(results):
        raise ValueError("DUPLICATE_EVENT")
    report = dict(
        parser_version="REVIEWED_MERGER_IMPLEMENTATION_BATCH_V2",
        parser_sha256=sha256_file(Path(__file__)),
        reviews_sha256=sha256_file(args.reviews),
        inputs=[dict(path=str(p), sha256=sha256_file(p)) for p in paths],
        results=results,
        supported_events=len(results),
        unresolved_material_in_reviewed_batch=0,
        metadata_only_unknown_cash_offer=sum(
            r["cash_election_offered"] is None for r in reviews["cases"]
        ),
        full_census_certified=False,
        full_dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("results", "inputs")}))


if __name__ == "__main__":
    main()
