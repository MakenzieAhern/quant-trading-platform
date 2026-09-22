"""Revalidate every accepted SZSE resumption against retained official bytes."""

import argparse
import json
from collections import Counter
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.audit_full_suspensions import _identity_index, _lifecycle_ends, normalize_szse
from scripts.reconcile_szse_resumptions import (
    REJECTED_TITLE,
    bind_resumptions,
    continued_halt_restoration_dates,
    exact_restoration_dates,
    exact_resume_dates,
    execution_open_blocked,
    non_equity_resumption_title,
    official_document_text,
)


def _verified(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    if value.get("manifest_sha256") != canonical_sha256(
        {key: item for key, item in value.items() if key != "manifest_sha256"}
    ):
        raise ValueError(f"MANIFEST_CHECKSUM_MISMATCH:{path}")
    return value


def _current_reports(staging: Path, authority: dict) -> list[Path]:
    wanted = set(authority["szse_resumption_manifest_sha256s"])
    found = {}
    patterns = ("full-szse-resumption*/**/*.json", "full-szse-terminal-suspension-v1/*.json")
    for pattern in patterns:
        for path in staging.glob(pattern):
            if "text" in path.parts or path.name.endswith(".meta.json"):
                continue
            digest = sha256_file(path)
            if digest in wanted:
                found[digest] = path
    if set(found) != wanted:
        raise ValueError("CURRENT_RESUMPTION_REPORT_MISSING")
    return [found[digest] for digest in authority["szse_resumption_manifest_sha256s"]]


def _baseline(suspension_root: Path, master_path: Path) -> tuple[list[dict], list[dict]]:
    source_manifest = _verified(suspension_root / "source-manifest-v1.json")
    observations = json.loads(
        (suspension_root / "official-suspension-observations-v1.json").read_bytes()
    )
    master = json.loads(master_path.read_bytes())
    source_hashes = {
        source["path"]: source["sha256"]
        for source in [*source_manifest["sse_sources"], *source_manifest["szse_sources"]]
    }
    normalized, unresolved, conflicts, _, _ = normalize_szse(
        observations["szse"],
        _identity_index(master),
        source_hashes,
        _lifecycle_ends(master),
        {},
    )
    if conflicts:
        raise ValueError("BASELINE_RESUMPTION_CONFLICTS")
    return normalized, unresolved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--suspension-root", type=Path, required=True)
    parser.add_argument("--authority", type=Path)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    authority_path = args.authority or args.suspension_root / "suspension-authority-v1.json"
    authority = _verified(authority_path)
    reports = _current_reports(args.staging, authority)
    normalized, unresolved = _baseline(args.suspension_root, args.master)
    unresolved_keys = {(row["security_id"], row["suspended_at"]) for row in unresolved}
    unresolved_symbols = {row["symbol"] for row in unresolved}

    prior = {}
    for path in reports:
        for row in _verified(path).get("accepted_resumptions", []):
            key = (row["security_id"], row["suspended_at"])
            if key in prior and prior[key] != row:
                raise ValueError("CONFLICTING_PRIOR_RESUMPTIONS")
            prior[key] = row

    evidence = {}
    states = Counter()
    source_manifests = []
    parsed = {}
    continued_halts = {}
    for manifest_path in sorted(args.staging.glob("full-szse-resumption*/**/source-manifest.json")):
        manifest = _verified(manifest_path)
        source_manifests.append({"path": str(manifest_path), "sha256": sha256_file(manifest_path)})
        root = manifest_path.parent.parent
        for document in manifest["documents"]:
            affected = document.get("affected_suspensions", [])
            if affected and not any(tuple(value) in unresolved_keys for value in affected):
                continue
            if not affected and document["issuer"] not in unresolved_symbols:
                continue
            status = document["retrieval_status"]
            if status not in {"PASS", "NON_PDF_ATTACHMENT"}:
                states[status] += 1
                continue
            if REJECTED_TITLE.search(document["title"]):
                states["REJECTED_TITLE"] += 1
                continue
            if non_equity_resumption_title(document["title"]):
                states["NON_EQUITY"] += 1
                continue
            identity = (document["source_sha256"], document["published_on"])
            if identity not in parsed:
                text = official_document_text(root, document)
                parsed[identity] = (
                    sorted(
                        set(exact_resume_dates(text, document["published_on"]))
                        | set(exact_restoration_dates(text))
                    ),
                    continued_halt_restoration_dates(text),
                )
            dates, halted_dates = parsed[identity]
            marker = (document["published_on"], document["source_sha256"])
            for day in halted_dates:
                key = (document["issuer"], day)
                continued_halts[key] = max(continued_halts.get(key, ("", "")), marker)
            state = (
                "EXACT_DATE" if len(dates) == 1 else "AMBIGUOUS_DATES" if dates else "NO_EXACT_DATE"
            )
            states[state] += 1
            if len(dates) != 1:
                continue
            row = {
                "symbol": document["issuer"],
                "resumed_at": dates[0],
                "title": document["title"],
                "url": document["url"],
                "published_on": document["published_on"],
                "retrieved_at_utc": document["retrieved_at_utc"],
                "source_sha256": document["source_sha256"],
                "execution_open_blocked": execution_open_blocked(
                    official_document_text(root, document), dates[0]
                ),
            }
            evidence[json.dumps(row, ensure_ascii=False, sort_keys=True)] = row

    evidence_rows = sorted(
        (
            row
            for row in evidence.values()
            if (row["published_on"], row["source_sha256"])
            > continued_halts.get((row["symbol"], row["resumed_at"]), ("", ""))
        ),
        key=lambda row: (row["symbol"], row["resumed_at"], row["source_sha256"]),
    )
    accepted, remaining = bind_resumptions(unresolved, normalized, evidence_rows)
    if (accepted, remaining) != bind_resumptions(
        list(reversed(unresolved)), list(reversed(normalized)), list(reversed(evidence_rows))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")

    accepted_by_key = {(row["security_id"], row["suspended_at"]): row for row in accepted}
    rejected = [
        {
            "security_id": key[0],
            "suspended_at": key[1],
            "prior_resumed_at": row["resumed_at"],
            "revalidated_resumed_at": accepted_by_key.get(key, {}).get("resumed_at"),
            "reason": "NO_IDENTICAL_CURRENT_EXACT_OFFICIAL_DATE",
        }
        for key, row in sorted(prior.items())
        if accepted_by_key.get(key, {}).get("resumed_at") != row["resumed_at"]
    ]
    new = [row for key, row in sorted(accepted_by_key.items()) if key not in prior]
    report = {
        "parser_version": "SZSE_RETAINED_OFFICIAL_RESUMPTION_REVALIDATION_V5",
        "parser_sha256": sha256_file(Path(__file__)),
        "resumption_parser_sha256": sha256_file(
            Path(__file__).with_name("reconcile_szse_resumptions.py")
        ),
        "authority_input_sha256": sha256_file(authority_path),
        "master_input_sha256": sha256_file(args.master),
        "source_manifests": source_manifests,
        "current_report_sha256s": [sha256_file(path) for path in reports],
        "baseline_unresolved_count": len(unresolved),
        "prior_accepted_count": len(prior),
        "document_counts": dict(sorted(states.items())),
        "accepted_resumptions": accepted,
        "accepted_count": len(accepted),
        "remaining_unresolved": remaining,
        "remaining_count": len(remaining),
        "prior_revalidated_count": len(prior) - len(rejected),
        "prior_rejected_count": len(rejected),
        "rejected_prior_acceptances": rejected,
        "newly_accepted_count": len(new),
        "newly_accepted_resumptions": new,
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {key: value for key, value in report.items() if not isinstance(value, list)},
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
