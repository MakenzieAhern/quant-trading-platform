"""Close obsolete P1 SSE ST document requests against accepted official facts."""

import argparse
import json
import re
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_p1_public_fact_requirements import verified

TYPES = {
    "OFFICIAL_EFFECTIVE_DATED_ST_OR_NAME_CHANGE_NOTICE",
    "OFFICIAL_SSE_ST_OR_NAME_CHANGE_NOTICE",
}


def close(requirements: list[dict], authority: dict, corpus: dict) -> list[dict]:
    if (
        authority["SSE_HISTORICAL_ST_RECONSTRUCTION"] != "PASS_PUBLIC_OFFICIAL_RECONSTRUCTION"
        or authority["chain_gaps"]
        or authority["chain_conflicts"]
        or authority["unknown_intervals"]
        or authority["unmapped_events"]
        or any(status != "PASS" for status in authority["gates"].values())
        or corpus["unresolved_count"]
    ):
        raise ValueError("SSE_ST_FACT_AUTHORITY_NOT_ACCEPTED")
    chains = {row["security_id"]: row for row in authority["chains"]}
    official_events = {row["announcement_id"]: row for row in corpus["results"]}
    closed = []
    for row in requirements:
        if row["priority"] != "P1" or not set(row["required_document_types"]) & TYPES:
            continue
        if row["required_document_types"] == ["OFFICIAL_EFFECTIVE_DATED_ST_OR_NAME_CHANGE_NOTICE"]:
            match = re.fullmatch(r"SSE_ST_GAP:(CN-A:SSE:6\d{5}):\d+", row["affected_events"][0])
            if match is None:
                raise ValueError("INVALID_OLD_SSE_ST_GAP_ID")
            security_id = match[1]
            if (
                security_id not in chains
                or chains[security_id]["gaps"]
                or chains[security_id]["conflicts"]
            ):
                raise ValueError("OLD_SSE_ST_GAP_NOT_CLOSED")
            evidence = {
                "security_id": security_id,
                "official_chain_event_count": chains[security_id]["event_count"],
            }
        elif row["required_document_types"] == ["OFFICIAL_SSE_ST_OR_NAME_CHANGE_NOTICE"]:
            match = re.fullmatch(r"SSE_ST_MIRROR:(\d+)", row["affected_events"][0])
            if match is None or match[1] not in official_events:
                raise ValueError("OLD_SSE_ST_MIRROR_NOT_CLOSED")
            event = official_events[match[1]]
            if event["classification"] != "EXPLAINED_BY_OFFICIAL_EVENT":
                raise ValueError("OLD_SSE_ST_MIRROR_NOT_ACCEPTED")
            evidence = {"announcement_id": match[1], "source_sha256": event["source_sha256"]}
        else:
            raise ValueError("UNEXPECTED_SSE_ST_REQUIREMENT_TYPE")
        closed.append(
            {
                "document_id": row["document_id"],
                "affected_events": row["affected_events"],
                "classification": "FACT_SET_ESTABLISHED_BY_ACCEPTED_OFFICIAL_SSE_ST_AUTHORITY",
                "evidence": evidence,
            }
        )
    return sorted(closed, key=lambda row: row["document_id"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, required=True)
    parser.add_argument("--authority", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    requirements, authority, corpus = (
        verified(path) for path in (args.requirements, args.authority, args.corpus)
    )
    closed = close(requirements["documents"], authority, corpus)
    if closed != close(list(reversed(requirements["documents"])), authority, corpus):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "report_version": "P1_OFFICIAL_SSE_ST_FACT_SET_CLOSURE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "input_sha256s": {
            "requirements": sha256_file(args.requirements),
            "authority": sha256_file(args.authority),
            "corpus": sha256_file(args.corpus),
        },
        "closed_facts": sum(len(row["affected_events"]) for row in closed),
        "closed_documents": len(closed),
        "closed": closed,
        "input_order_reproducibility": "PASS",
        "no_new_event_created": True,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if key != "closed"}))


if __name__ == "__main__":
    main()
