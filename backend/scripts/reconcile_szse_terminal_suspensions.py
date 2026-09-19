"""Close official SZSE suspensions that lead directly to delisting."""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable

OFFICIAL_PDF = "https://static.cninfo.com.cn/finalpage/"
NO_DELISTING_PERIOD = re.compile(r"不(?:再)?进入退市整理期|不设退市整理期")


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text)


def _states_exact_suspension(text: str, start: str) -> bool:
    year, month, day = map(int, start.split("-"))
    return bool(
        re.search(
            rf"{year}年0?{month}月0?{day}日[^\u3002\uff1b;]{{0,120}}停牌",
            _compact(text),
        )
    )


def build_terminal_closures(
    documents: list[dict], unresolved: list[dict], master: list[dict]
) -> list[dict]:
    facts = defaultdict(list)
    for row in unresolved:
        facts[row["symbol"]].append(row)
    identities = defaultdict(list)
    for row in master:
        identities[row["security_id"]].append(row)

    grouped = defaultdict(list)
    for document in documents:
        match = NO_DELISTING_PERIOD.search(_compact(document["text"]))
        if match is None:
            continue
        published = document["published_on"]
        candidates = [
            row
            for row in facts[document["issuer"]]
            if row["suspended_at"][:10].replace("/", "-") <= published
        ]
        if not candidates:
            continue
        fact = max(candidates, key=lambda row: row["suspended_at"])
        start = fact["suspended_at"][:10].replace("/", "-")
        if not _states_exact_suspension(document["text"], start):
            continue
        rows = [
            row
            for row in identities[fact["security_id"]]
            if row["effective_from"] <= start
            and row["effective_to"] is not None
            and published <= row["effective_to"]
        ]
        terminal_dates = {row["effective_to"] for row in rows}
        if len(terminal_dates) != 1:
            continue
        master_row = min(rows, key=lambda row: (row["effective_from"], row["source_sha256"]))
        key = (fact["security_id"], fact["suspended_at"], next(iter(terminal_dates)))
        grouped[key].append(
            {
                "published_on": published,
                "retrieved_at_utc": document["retrieved_at_utc"],
                "source_sha256": document["source_sha256"],
                "title": document["title"],
                "url": document["url"],
                "terminal_treatment": match.group(0),
                "master_source_id": master_row["source_id"],
                "master_source_sha256": master_row["source_sha256"],
                "master_source_url": master_row["source_url"],
            }
        )

    return [
        {
            "security_id": security_id,
            "symbol": security_id.rsplit(":", 1)[-1],
            "suspended_at": suspended_at,
            "terminal_at": terminal_at,
            "binding_policy": (
                "EXACT_SUSPENSION_PLUS_NO_DELISTING_PERIOD_AND_OFFICIAL_LIFECYCLE_END_V1"
            ),
            "evidence": sorted(
                {row["source_sha256"]: row for row in evidence}.values(),
                key=lambda row: (row["published_on"], row["source_sha256"]),
            ),
        }
        for (security_id, suspended_at, terminal_at), evidence in sorted(grouped.items())
    ]


def load_documents(roots: list[Path]) -> tuple[list[dict], list[str]]:
    documents, manifest_hashes = {}, []
    for manifest_path in sorted(
        path for root in roots for path in root.rglob("source-manifest.json")
    ):
        manifest = json.loads(manifest_path.read_bytes())
        manifest_hashes.append(sha256_file(manifest_path))
        for row in manifest.get("documents", []):
            source_sha = row.get("source_sha256")
            if (
                row.get("retrieval_status") != "PASS"
                or not source_sha
                or not row.get("url", "").startswith(OFFICIAL_PDF)
            ):
                continue
            source = Path(row["source_path"])
            if not source.is_absolute():
                source = manifest_path.parent.parent / source
            cache = manifest_path.parent / "text" / f"{source_sha}.json"
            if not source.exists() or not cache.exists() or sha256_file(source) != source_sha:
                continue
            extracted = json.loads(cache.read_bytes())
            if extracted.get("source_sha256") != source_sha:
                raise ValueError("TERMINAL_SUSPENSION_EXTRACTION_CHANGED")
            document = {
                "issuer": row["issuer"],
                "published_on": row["published_on"],
                "retrieved_at_utc": row["retrieved_at_utc"],
                "source_sha256": source_sha,
                "title": row["title"],
                "url": row["url"],
                "text": "\n".join(extracted["pages"]),
            }
            previous = documents.get(source_sha)
            if previous is not None and previous != document:
                raise ValueError("CONFLICTING_TERMINAL_SUSPENSION_DOCUMENT")
            documents[source_sha] = document
    return sorted(documents.values(), key=lambda row: row["source_sha256"]), sorted(
        set(manifest_hashes)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, action="append", required=True)
    parser.add_argument("--unresolved", type=Path, required=True)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    documents, manifest_hashes = load_documents(args.source_root)
    unresolved = json.loads(args.unresolved.read_bytes())
    master = json.loads(args.master.read_bytes())
    accepted = build_terminal_closures(documents, unresolved, master)
    if accepted != build_terminal_closures(
        list(reversed(documents)), list(reversed(unresolved)), list(reversed(master))
    ):
        raise ValueError("INPUT_ORDER_CHANGED")
    report = {
        "parser_version": "SZSE_OFFICIAL_TERMINAL_SUSPENSION_CLOSURE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "source_manifest_sha256s": manifest_hashes,
        "unresolved_input_sha256": sha256_file(args.unresolved),
        "master_input_sha256": sha256_file(args.master),
        "documents_scanned": len(documents),
        "accepted_terminal_closures": accepted,
        "accepted_count": len(accepted),
        "remaining_count": len(unresolved) - len(accepted),
        "input_order_reproducibility": "PASS",
        "full_dataset_created": False,
    }
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(args.output, canonical_json_bytes(report) + b"\n")
    print(json.dumps({key: value for key, value in report.items() if not isinstance(value, list)}))


if __name__ == "__main__":
    main()
