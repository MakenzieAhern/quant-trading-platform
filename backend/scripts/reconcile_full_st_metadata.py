"""Missing-only SSE issuer/day corroboration of retained CNINFO transition leads."""

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path
from threading import Event
from urllib.parse import urlencode

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_sse_cninfo import fetch, match, publication


def exact_rows(rows, cn):
    return list(
        {
            canonical_json_bytes(row): row
            for row in rows
            if match(row, [cn], issuer_prefix=True)[0] == "EXACT"
        }.values()
    )


def page_rows(payload, code, day, seen):
    rows = [row for group in payload["data"] for row in group]
    keys = [canonical_sha256(row) for row in rows]
    if len(set(keys)) != len(keys) or seen.intersection(keys):
        raise ValueError("SSE_REPEATED_METADATA_ROW")
    if any(row["SECURITY_CODE"] != code or row["SSEDATE"] != day for row in rows):
        raise ValueError("SSE_ISSUER_DAY_LEAKAGE")
    seen.update(keys)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--prior", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, action="append")
    parser.add_argument("--queue", type=Path)
    parser.add_argument("--batch", help="Separate checkpoint/page/manifest namespace")
    args = parser.parse_args()
    inputs = args.metadata or [
        args.root / "metadata-manifest-v1.json",
        args.root / "metadata-recovery-v1/risk/2022-04-checkpoint.json",
    ]
    metadata = [json.loads(p.read_bytes()) for p in inputs]
    for data in metadata:
        if data["manifest_sha256"] != canonical_sha256(
            {k: v for k, v in data.items() if k != "manifest_sha256"}
        ):
            raise ValueError("CNINFO_MANIFEST_CHANGED")
    windows = [
        r
        for data in metadata
        for r in data.get("results", [data])
        if r.get("status") == "COMPLETE_FOR_QUERY_NOT_EVENT_CENSUS"
    ]
    cninfo = {r["announcementId"]: r for window in windows for r in window["records"]}
    queue_path = args.queue or args.root / "queues/transition-pdfs-v1.json"
    queue = json.loads(queue_path.read_bytes())
    selected = [cninfo[r["announcement_id"]] for r in queue]
    cached, hashes, cached_source_gaps = [], {}, []
    for meta_path in sorted(args.prior.rglob("*.meta.json")):
        meta = json.loads(meta_path.read_bytes())
        if "query.sse.com.cn/security/stock/queryCompanyBulletinNew.do" not in meta.get("url", ""):
            continue
        if meta.get("error") and "sha256" not in meta:
            cached_source_gaps.append(
                dict(path=str(meta_path), reason="RETAINED_FAILED_RETRIEVAL", error=meta["error"])
            )
            continue
        path = Path(str(meta_path).removesuffix(".meta.json"))
        if not path.exists():
            path = Path(str(path) + ".json")  # Legacy probe receipt omitted the data suffix.
        if sha256_file(path) != meta["sha256"]:
            raise ValueError("SSE_CACHED_SOURCE_CHANGED")
        try:
            payload = json.loads(path.read_bytes()).get("pageHelp")
        except ValueError:
            payload = None
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            cached_source_gaps.append(
                dict(path=str(path), sha256=meta["sha256"], reason="RETAINED_NON_METADATA_RESPONSE")
            )
            continue
        for group in payload.get("data", []):
            for row in group:
                cached.append(row)
                hashes[canonical_json_bytes(row)] = meta["sha256"]
    denied = Event()
    jobs = sorted({(r["secCode"], publication(r)) for r in selected})

    def reconcile(job):
        code, day = job
        checkpoint_root = (
            args.root / args.batch / "checkpoints"
            if args.batch
            else args.root / "sse-reconciliation-v1"
        )
        checkpoint = checkpoint_root / f"{code}-{day}.json"
        if checkpoint.exists():
            result = json.loads(checkpoint.read_bytes())
            if result["manifest_sha256"] != canonical_sha256(
                {k: v for k, v in result.items() if k != "manifest_sha256"}
            ):
                raise ValueError("SSE_RECONCILIATION_CHANGED")
            if result.get("access_denied"):
                denied.set()
            return result
        cns = [r for r in selected if r["secCode"] == code and publication(r) == day]
        rows = [r for r in cached if r["SECURITY_CODE"] == code and r["SSEDATE"] == day]
        source_hashes = dict(hashes)
        result = dict(symbol=code, date=day, records=[], accepted_events=0)
        try:
            if any(len(exact_rows(rows, cn)) != 1 for cn in cns):
                if denied.is_set():
                    raise ValueError("NOT_ATTEMPTED_AFTER_ACCESS_DENIAL")
                seen = set()
                for page in range(1, 41):
                    params = {
                        "isPagination": "true",
                        "pageHelp.pageSize": 25,
                        "pageHelp.pageNo": page,
                        "pageHelp.beginPage": page,
                        "pageHelp.cacheSize": 1,
                        "START_DATE": day,
                        "END_DATE": day,
                        "SECURITY_CODE": code,
                        "TITLE": "",
                        "BULLETIN_TYPE": "",
                        "stockType": "",
                    }
                    raw = fetch(
                        args.root,
                        f"{args.batch + '/pages' if args.batch else 'sse-metadata-v1'}/"
                        f"{code}-{day}-p{page:03}.json",
                        "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?"
                        + urlencode(params),
                        referer="https://www.sse.com.cn/disclosure/listedinfo/announcement/",
                    )
                    payload = json.loads(raw)["pageHelp"]
                    additions = page_rows(payload, code, day, seen)
                    rows.extend(additions)
                    source_hashes.update(
                        (canonical_json_bytes(r), sha256(raw).hexdigest()) for r in additions
                    )
                    if page >= payload["pageCount"]:
                        break
                else:
                    raise ValueError("SSE_PAGINATION_INCOMPLETE")
            for cn in cns:
                matches = exact_rows(rows, cn)
                record = dict(
                    cninfo=[cn],
                    match_confidence="EXACT"
                    if len(matches) == 1
                    else "AMBIGUOUS"
                    if matches
                    else "NO_MATCH",
                    match_method="security+date+exact_subject+issuer_prefix",
                )
                if len(matches) == 1:
                    title = re.sub(r"\s+", "", matches[0]["TITLE"])
                    prefix = title[: title.index("关于")] if "关于" in title else ""
                    record.update(
                        sse=matches[0],
                        sse_metadata_snapshot_sha256=source_hashes[
                            canonical_json_bytes(matches[0])
                        ],
                    )
                    if not matches[0].get("SECURITY_NAME") and 1 <= len(prefix) <= 12:
                        record["derived_security_name_from_sse_title"] = prefix
                result["records"].append(record)
            result["status"] = "METADATA_RECONCILED_NOT_EVENT_ACCEPTANCE"
        except Exception as exc:
            access_denied = getattr(exc, "code", None) in {403, 429}
            if access_denied:
                denied.set()
            result.update(
                status="FAILED", error=f"{type(exc).__name__}: {exc}", access_denied=access_denied
            )
        result["manifest_sha256"] = canonical_sha256(result)
        write_immutable(checkpoint, canonical_json_bytes(result) + b"\n")
        print(code, day, result["status"], flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(reconcile, jobs))
    report = dict(
        results=results,
        cached_source_gaps=cached_source_gaps,
        parser_sha256=sha256_file(Path(__file__)),
        input_sha256=[sha256_file(p) for p in [*inputs, queue_path]],
        accepted_events=0,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        args.root / args.batch / "manifest.json"
        if args.batch
        else args.root / "sse-reconciliation-manifest-v1.json",
        canonical_json_bytes(report) + b"\n",
    )


if __name__ == "__main__":
    main()
