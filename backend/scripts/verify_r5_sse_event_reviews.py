"""Verify document-bound official SSE event reviews and emit auditable events."""

import argparse
import html
import io
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from pypdf import PdfReader

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_sse_cninfo import publication
from scripts.sse_st_events import normalize, status


def verified(path: Path) -> dict:
    document = json.loads(path.read_bytes())
    body = {key: value for key, value in document.items() if key != "manifest_sha256"}
    if document["manifest_sha256"] != canonical_sha256(body):
        raise ValueError(f"INPUT_MANIFEST_CHANGED:{path}")
    return document


def date_is_bound(review: dict, text: str, published_on: str) -> bool:
    effective = date.fromisoformat(review["effective_from"])
    exact = f"{effective.year}年{effective.month}月{effective.day}日"
    mode = review.get("effective_date_evidence", "EXACT_FULL_DATE")
    if mode == "EXACT_FULL_DATE":
        return exact in text
    if mode == "PUBLICATION_YEAR_PLUS_MONTH_DAY":
        return (
            effective.year == date.fromisoformat(published_on).year
            and f"{effective.month}月{effective.day}日" in text
        )
    if mode == "ONE_YEAR_SOURCE_TYPO_CORRECTED_BY_PUBLICATION_YEAR":
        published = date.fromisoformat(published_on)
        stale = f"{effective.year - 1}年{effective.month}月{effective.day}日"
        return effective.year == published.year and stale in text and f"{effective.year}年" in text
    raise ValueError(f"UNKNOWN_EFFECTIVE_DATE_EVIDENCE:{mode}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, action="append", required=True)
    parser.add_argument("--source-manifest", type=Path, action="append", required=True)
    parser.add_argument("--source-root", type=Path, action="append", required=True)
    parser.add_argument("--text-root", type=Path, action="append", default=[])
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if len(args.source_manifest) != len(args.source_root):
        raise ValueError("SOURCE_MANIFEST_ROOT_COUNT_MISMATCH")

    records = {
        str(cn["announcementId"]): record
        for path in args.reconciliation
        for checkpoint in verified(path)["results"]
        for record in checkpoint["records"]
        for cn in record["cninfo"]
        if record["match_confidence"] == "EXACT"
    }
    sources = {}
    for manifest_path, source_root in zip(args.source_manifest, args.source_root, strict=True):
        for row in verified(manifest_path)["documents"]:
            announcement_id = row.get("announcement_id") or Path(urlparse(row["url"]).path).stem
            sources[str(announcement_id)] = (row, source_root)

    review_document = json.loads(args.reviews.read_bytes())
    if review_document["scope"] != "DOCUMENT_BOUND_OFFICIAL_EFFECTIVE_DATED_ST_EVENTS":
        raise ValueError("WRONG_REVIEW_SCOPE")
    results, text_inputs = [], []
    for review in review_document["records"]:
        announcement_id = str(review["announcement_id"])
        reference_id = str(review.get("identity_reference_announcement_id", announcement_id))
        record = records.get(reference_id)
        source, source_root = sources[announcement_id]
        document = source_root / source["source_path"]
        if (
            source["source_sha256"] != review["source_sha256"]
            or sha256_file(document) != review["source_sha256"]
        ):
            raise ValueError(f"SOURCE_CHANGED:{announcement_id}")
        cache = next(
            (
                root / f"{review['source_sha256']}.json"
                for root in args.text_root
                if (root / f"{review['source_sha256']}.json").exists()
            ),
            None,
        )
        if cache:
            cached = json.loads(cache.read_bytes())
            if cached["source_sha256"] != review["source_sha256"]:
                raise ValueError(f"TEXT_SOURCE_CHANGED:{announcement_id}")
            pages = cached["pages"]
            text_inputs.append(cache)
        elif document.suffix.lower() in {".html", ".shtml"}:
            raw = document.read_text(encoding="utf-8")
            pages = [html.unescape(re.sub(r"<[^>]+>", "", raw))]
        else:
            pages = [
                unicodedata.normalize("NFKC", page.extract_text() or "")
                for page in PdfReader(io.BytesIO(document.read_bytes())).pages
            ]
        evidence = review["evidence"]
        if not evidence or any(
            item["text"] not in re.sub(r"\s+", "", pages[item["page"] - 1]) for item in evidence
        ):
            raise ValueError(f"EVIDENCE_NOT_FOUND:{announcement_id}")
        joined = "".join(item["text"] for item in evidence)
        published_on = source.get("published_on")
        if not published_on and record:
            published_on = publication(record["cninfo"][0])
        if not published_on or not date_is_bound(review, joined, published_on):
            raise ValueError(f"EVENT_FACT_NOT_BOUND:{announcement_id}")
        if review.get("new_name") and review["new_name"] not in joined:
            raise ValueError(f"NEW_NAME_NOT_BOUND:{announcement_id}")
        if review.get("old_name") and review["old_name"] not in joined:
            raise ValueError(f"OLD_NAME_NOT_BOUND:{announcement_id}")
        if review.get("new_name") and status(review["new_name"]) != review["status"]:
            raise ValueError(f"STATUS_NAME_CONFLICT:{announcement_id}")
        if not review.get("new_name") and not review.get("status_only"):
            raise ValueError(f"MISSING_NEW_NAME:{announcement_id}")
        if review.get("status_only") and not any(
            label in joined for label in ("退市风险警示", "其他风险警示", "风险警示板")
        ):
            raise ValueError(f"STATUS_NOT_BOUND:{announcement_id}")
        if review.get("old_name") and status(review["old_name"]) != review["old_status"]:
            raise ValueError(f"STATUS_NAME_CONFLICT:{announcement_id}")
        if source.get("issuer") and source["issuer"] != review["symbol"]:
            raise ValueError(f"SECURITY_IDENTITY_CHANGED:{announcement_id}")
        if record:
            cn, sse = record["cninfo"][0], record["sse"]
            if cn["secCode"] != review["symbol"] or sse["SECURITY_CODE"] != review["symbol"]:
                raise ValueError(f"SECURITY_IDENTITY_CHANGED:{announcement_id}")
        elif review.get("identity_method") == "OFFICIAL_CNINFO_DOCUMENT_HEADER":
            if "static.cninfo.com.cn" not in source["url"] or review["symbol"] not in re.sub(
                r"\s+", "", pages[0][:1000]
            ):
                raise ValueError(f"SECURITY_IDENTITY_CHANGED:{announcement_id}")
            cn = sse = None
        else:
            raise ValueError(f"MISSING_OFFICIAL_IDENTITY:{announcement_id}")
        official_kind = (
            "SSE_EXCHANGE_DECISION_PAGE"
            if "sse.com.cn" in source["url"] and "cninfo.com.cn" not in source["url"]
            else "CNINFO_ISSUER_DISCLOSURE"
        )
        event = {
            **{key: review.get(key) for key in ("security_id", "symbol", "old_name", "new_name")},
            "old_status": review["old_status"],
            "status": review["status"],
            "event_type": review["event_type"],
            "effective_from": review["effective_from"],
            "effective_to": None,
            "cninfo_document_id": announcement_id,
            "official_document_url": source["url"],
            "official_document_id": announcement_id,
            "official_publication_date": published_on,
            "official_document_sha256": review["source_sha256"],
            "official_source_kind": official_kind,
            "retrieved_at_utc": source["retrieved_at_utc"],
            "match_method": "DOCUMENT_BOUND_OFFICIAL_EVENT_REVIEW",
            "match_confidence": "EXACT",
            "support": evidence,
            "review_sha256": canonical_sha256(review),
        }
        if sse:
            event.update(
                sse_announcement_id=sse["ORG_BULLETIN_ID"],
                sse_title=sse["TITLE"],
                sse_publication_date=sse["SSEDATE"],
                sse_metadata_snapshot_sha256=record["sse_metadata_snapshot_sha256"],
            )
        elif official_kind == "SSE_EXCHANGE_DECISION_PAGE":
            event.update(
                sse_announcement_id=announcement_id,
                sse_title=source["title"],
                sse_publication_date=published_on,
                sse_metadata_snapshot_sha256=review["source_sha256"],
            )
        if official_kind == "CNINFO_ISSUER_DISCLOSURE":
            event.update(
                cninfo_document_url=source["url"],
                cninfo_publication_date=published_on,
                cninfo_document_sha256=review["source_sha256"],
            )
        event["event_sha256"] = canonical_sha256(event)
        results.append(
            {
                "announcement_id": announcement_id,
                "symbol": review["symbol"],
                "status": "PARSED_TRANSITION_REQUIRES_LIFECYCLE_AND_COVERAGE_REVIEW",
                "event": event,
            }
        )

    events = [row["event"] for row in results]
    if normalize(events) != normalize(list(reversed(events))):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "scope": review_document["scope"],
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in [
                args.reviews,
                *args.reconciliation,
                *args.source_manifest,
                *sorted(set(text_inputs)),
            ]
        ],
        "accepted_events": 0,
        "input_order_reproducibility": "PASS",
        "results": results,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.report, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                "verified_events": len(results),
                "manifest_sha256": report["manifest_sha256"],
            }
        )
    )


if __name__ == "__main__":
    main()
