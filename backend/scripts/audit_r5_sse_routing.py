"""Terminally classify every public CNINFO title routed for SSE ST coverage."""

import argparse
import json
from collections import Counter
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_r5_sse_event_corpus import events_in
from scripts.reconcile_distribution_cash import verified

SAFE_TITLE_TOKENS = (
    "申请",
    "可能",
    "提示",
    "进展",
    "专项",
    "意见",
    "工作函",
    "核查",
    "律师",
    "会计师",
    "预亏",
    "预计",
    "防范",
    "措施",
    "消除",
    "撤回",
    "暂不",
    "未申请",
    "关注",
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--routing", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--accepted-events", type=Path, action="append", required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    routing, corpus = verified(args.routing), verified(args.corpus)
    accepted = set().union(*(events_in(path) for path in args.accepted_events))
    review_document = json.loads(args.reviews.read_bytes())
    if review_document["scope"] != "DOCUMENT_BOUND_OFFICIAL_SSE_ROUTING_REVIEWS":
        raise ValueError("WRONG_ROUTING_REVIEW_SCOPE")
    reviews = {str(row["announcement_id"]): row for row in review_document["records"]}
    if len(reviews) != len(review_document["records"]):
        raise ValueError("DUPLICATE_ROUTING_REVIEW")
    corpus_rows = {row["announcement_id"]: row for row in corpus["results"]}

    results = []
    for row in routing["classifications"]:
        announcement_id = str(row["announcement_id"])
        routed = row["classification"]
        if routed == "OTHER_EXCHANGE_OR_INSTRUMENT":
            classification = routed
        elif announcement_id in accepted:
            classification = "EXPLAINED_BY_OFFICIAL_EVENT"
        elif routed == "TRANSITION_DOCUMENT_LEAD":
            classification = corpus_rows.get(announcement_id, {}).get(
                "classification", "UNRESOLVED_TRANSITION_DOCUMENT"
            )
        elif "债券" in row["title"]:
            classification = "NON_EQUITY_INSTRUMENT"
        elif announcement_id in reviews:
            review = reviews[announcement_id]
            if review["official_title"] != row["title"]:
                raise ValueError(f"REVIEW_TITLE_CHANGED:{announcement_id}")
            if review.get("related_event_document_id") not in {None, *accepted}:
                raise ValueError(f"RELATED_EVENT_NOT_ACCEPTED:{announcement_id}")
            classification = review["classification"]
        elif routed == "WARNING_OR_APPLICATION_LEAD_RETAINED" and any(
            token in row["title"] for token in SAFE_TITLE_TOKENS
        ):
            classification = "NON_IMPLEMENTATION_TITLE"
        else:
            classification = "UNRESOLVED_ROUTING_LEAD"
        results.append({**row, "terminal_classification": classification})

    results.sort(key=lambda row: (row["issuer"], row["announcement_id"]))
    unresolved = [row for row in results if row["terminal_classification"].startswith("UNRESOLVED")]
    report = {
        "scope": "FULL_PUBLIC_CNINFO_SSE_ST_TITLE_ROUTING_CLOSURE",
        "inputs": [
            {"path": str(path), "sha256": sha256_file(path)}
            for path in [args.routing, args.corpus, *args.accepted_events, args.reviews]
        ],
        "parser_sha256": sha256_file(Path(__file__)),
        "unique_leads": routing["unique_leads"],
        "classified_leads": len(results),
        "classification_counts": dict(Counter(row["terminal_classification"] for row in results)),
        "unresolved": unresolved,
        "unresolved_count": len(unresolved),
        "input_order_reproducibility": "PASS",
        "results": results,
    }
    if len(results) != routing["unique_leads"]:
        raise ValueError("ROUTING_LEAD_DISAPPEARED")
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.report, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                key: report[key]
                for key in (
                    "classified_leads",
                    "classification_counts",
                    "unresolved_count",
                    "manifest_sha256",
                )
            }
        )
    )


if __name__ == "__main__":
    main()
