"""Recover only failed SSE pages; preserve original first pages and failure receipts."""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlencode

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_full_st_metadata import exact_rows, page_rows
from scripts.reconcile_sse_cninfo import fetch, publication


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    metadata = json.loads((root / "metadata-manifest-v1.json").read_bytes())
    recovery = json.loads((root / "metadata-recovery-v1/risk/2022-04-checkpoint.json").read_bytes())
    selected_ids = {
        r["announcement_id"]
        for r in json.loads((root / "queues/transition-pdfs-v1.json").read_bytes())
    }
    cns = {
        r["announcementId"]: r
        for window in [*metadata["results"], recovery]
        for r in window.get("records", [])
        if r["announcementId"] in selected_ids
    }
    for prior_path in sorted((root / "sse-reconciliation-v1").glob("*.json")):
        prior = json.loads(prior_path.read_bytes())
        if prior.get("error") != "ValueError: SSE_REPEATED_METADATA_ROW":
            continue
        code, day = prior["symbol"], prior["date"]
        output = root / "sse-pagination-recovery-v1" / f"{code}-{day}.json"
        if output.exists():
            earlier = json.loads(output.read_bytes())
            if earlier.get("error") != "ValueError: SSE_TOTAL_NOT_RECONCILED":
                continue
            output = root / "sse-pagination-review-v2" / f"{code}-{day}.json"
            if output.exists():
                continue
        result = dict(
            symbol=code,
            date=day,
            prior_sha256=sha256_file(prior_path),
            records=[],
            accepted_events=0,
        )
        try:
            first = root / "sse-metadata-v1" / f"{code}-{day}-p001.json"
            meta = json.loads(Path(str(first) + ".meta.json").read_bytes())
            if sha256_file(first) != meta["sha256"]:
                raise ValueError("SSE_FIRST_PAGE_CHANGED")
            payload = json.loads(first.read_bytes())["pageHelp"]
            expected, pages = payload["total"], payload["pageCount"]
            groups = len(payload["data"])
            seen = set()
            rows = page_rows(payload, code, day, seen)
            hashes = {canonical_json_bytes(row): meta["sha256"] for row in rows}
            for page in range(2, pages + 1):
                params = {**meta["params"]} if meta.get("params") else None
                # The original receipt stores GET parameters in its URL.
                from urllib.parse import parse_qsl, urlsplit

                params = dict(parse_qsl(urlsplit(meta["url"]).query)) if params is None else params
                params.update({"pageHelp.pageNo": page, "pageHelp.beginPage": page})
                raw = fetch(
                    root,
                    f"sse-pagination-recovery-v1/pages/{code}-{day}-p{page:03}.json",
                    "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?"
                    + urlencode(params),
                    referer="https://www.sse.com.cn/disclosure/listedinfo/announcement/",
                )
                payload = json.loads(raw)["pageHelp"]
                if (
                    payload["total"],
                    payload["pageCount"],
                    payload["pageNo"],
                    payload["beginPage"],
                ) != (expected, pages, page, page):
                    raise ValueError("SSE_PAGINATION_IDENTITY_OR_TOTAL_CHANGED")
                additions = page_rows(payload, code, day, seen)
                groups += len(payload["data"])
                rows.extend(additions)
                hashes.update(
                    (canonical_json_bytes(row), sha256(raw).hexdigest()) for row in additions
                )
            if groups != expected:
                raise ValueError("SSE_TOTAL_NOT_RECONCILED")
            for cn in cns.values():
                if cn["secCode"] != code or publication(cn) != day:
                    continue
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
                    record.update(
                        sse=matches[0],
                        sse_metadata_snapshot_sha256=hashes[canonical_json_bytes(matches[0])],
                    )
                result["records"].append(record)
            result.update(
                status="METADATA_RECONCILED_NOT_EVENT_ACCEPTANCE",
                verified_rows=len(rows),
                verified_groups=groups,
            )
        except Exception as exc:
            result.update(status="FAILED", error=f"{type(exc).__name__}: {exc}")
        result["manifest_sha256"] = canonical_sha256(result)
        write_immutable(output, canonical_json_bytes(result) + b"\n")
        print(code, day, result["status"], flush=True)
        if (
            "403" in result.get("error", "")
            or "429" in result.get("error", "")
            or "ACCESS_DENIED" in result.get("error", "")
        ):
            break


if __name__ == "__main__":
    main()
