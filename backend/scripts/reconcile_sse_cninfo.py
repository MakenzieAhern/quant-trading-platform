"""Snapshot public CNINFO disclosures against the preserved SSE candidate index."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

QUERY = "https://www.cninfo.com.cn/new/hisAnnouncement/query"
STATIC = "https://static.cninfo.com.cn/"


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value))
    temporary.replace(path)


def fetch(
    root: Path,
    name: str,
    url: str,
    params: dict[str, object] | None = None,
    *,
    referer: str | None = None,
) -> bytes:
    """Checkpoint every response; resume timeouts at most three times, never access denial."""
    path = root / name
    meta_path = path.with_suffix(path.suffix + ".meta.json")
    previous = []
    attempt = 1
    if meta_path.exists():
        meta = json.loads(meta_path.read_bytes())
        if meta["url"] != url or meta["params"] != params or meta.get("referer") != referer:
            raise ValueError("snapshot request identity mismatch")
        if meta.get("error"):
            if meta["error"] != "TimeoutError" or meta["attempt"] >= 3:
                raise RuntimeError("previous request failed; no automatic retry")
            previous = [
                *meta.get("previous_attempts", []),
                {k: v for k, v in meta.items() if k != "previous_attempts"},
            ]
            attempt = meta["attempt"] + 1
            time.sleep(attempt)
        else:
            raw = path.read_bytes()
            if sha(raw) != meta["sha256"]:
                raise ValueError("snapshot checksum mismatch")
            return raw
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(params).encode() if params else None,
        headers={"Referer": referer} if referer else {},
    )
    record: dict[str, Any] = {
        "url": url,
        "params": params,
        "attempt": attempt,
        "previous_attempts": previous,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
    }
    if referer:
        record["referer"] = referer
    try:
        with urllib.request.urlopen(request, timeout=35) as response:
            raw = bytes(response.read())
            record.update(
                http_status=response.status,
                headers={
                    k: v
                    for k, v in response.headers.items()
                    if k.lower()
                    in {
                        "content-type",
                        "content-length",
                        "date",
                        "etag",
                        "last-modified",
                        "x-tengine-error",
                    }
                },
            )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        record["sha256"] = sha(raw)
        if b"denied by bot" in raw.lower() or any(
            "denied by bot" in v.lower() for v in record["headers"].values()
        ):
            raise RuntimeError("ACCESS_DENIED_STOP")
        save(meta_path, record)
        time.sleep(0.3)
        return raw
    except Exception as exc:
        record["error"] = type(exc).__name__
        save(meta_path, record)
        raise


def title_key(title: str) -> str:
    return re.sub(r"[\s：:，,。、“”\"（）()《》]", "", title)  # noqa: RUF001


def publication(row: dict[str, Any]) -> str:
    return (
        datetime.fromtimestamp(row["announcementTime"] / 1000, timezone(timedelta(hours=8)))
        .date()
        .isoformat()
    )


def issuer_subject(title: str, sse: dict[str, Any], cn: dict[str, Any]) -> str:
    """Strip one explicit issuer prefix; preserve the entire announcement subject."""
    prefixes = [
        p for p in (sse.get("SECURITY_NAME"), cn.get("secName")) if isinstance(p, str) and p
    ]
    company = re.match(r"[\u4e00-\u9fff]+(?:股份有限公司|有限责任公司)", title)
    if company:
        prefixes.append(company[0])
    for prefix in sorted(prefixes, key=len, reverse=True):
        if title.startswith(prefix):
            title = title[len(prefix) :]
            break
    return title_key(title)


def match(
    sse: dict[str, Any], rows: list[dict[str, Any]], *, issuer_prefix: bool = False
) -> tuple[str, list[dict[str, Any]]]:
    """No keyword-only or fuzzy acceptance; security, date and full title must agree."""

    def key(title: str, cn: dict[str, Any]) -> str:
        return issuer_subject(title, sse, cn) if issuer_prefix else title_key(title)

    matches = {
        r["announcementId"]: r
        for r in rows
        if r["secCode"] == sse["SECURITY_CODE"]
        and publication(r) == sse["SSEDATE"]
        and key(r["announcementTitle"], r) == key(sse["TITLE"], r)
    }
    result = sorted(matches.values(), key=lambda r: r["announcementId"])
    return ("EXACT" if len(result) == 1 else "AMBIGUOUS" if result else "NO_MATCH", result)


def load_candidates(
    snapshot: Path, inventory: Path
) -> tuple[list[dict[str, Any]], dict[str, str], set[str]]:
    manifest = json.loads((snapshot / "source-manifest.json").read_bytes())
    expected = manifest.pop("manifest_sha256")
    if sha(canonical(manifest)) != expected:
        raise ValueError("SSE manifest checksum mismatch")
    docs: dict[str, dict[str, Any]] = {}
    provenance: dict[str, str] = {}
    for page in manifest["pages"]:
        raw = (snapshot / page["relative_path"]).read_bytes()
        if sha(raw) != page["sha256"]:
            raise ValueError("SSE page checksum mismatch")
        for group in json.loads(raw)["pageHelp"]["data"]:
            for row in group:
                if row["URL"] in docs and docs[row["URL"]] != row:
                    raise ValueError("conflicting SSE rows for the same document URL")
                docs[row["URL"]] = row
                provenance[row["URL"]] = min(
                    provenance.get(row["URL"], page["sha256"]), page["sha256"]
                )
    selected = [
        docs[r["source_url"].removeprefix("https://static.sse.com.cn")]
        for r in {r["source_url"]: r for r in json.loads(inventory.read_bytes())}.values()
    ]
    return (
        sorted(selected, key=lambda r: (r["SSEDATE"], r["SECURITY_CODE"], r["URL"])),
        provenance,
        {r["SECURITY_CODE"] for r in docs.values()},
    )


def run(snapshot: Path, inventory: Path, output: Path) -> None:
    candidates, provenance, _ = load_candidates(snapshot, inventory)
    results = []
    dates = sorted({r["SSEDATE"] for r in candidates})
    for index, day in enumerate(dates):
        rows: list[dict[str, Any]] = []
        for page in range(1, 21):
            params: dict[str, object] = {
                "pageNum": page,
                "pageSize": 30,
                "column": "sse",
                "tabName": "fulltext",
                "stock": "",
                "searchkey": "风险警示",
                "secid": "",
                "plate": "",
                "category": "",
                "trade": "",
                "seDate": f"{day}~{day}",
                "sortName": "",
                "sortType": "",
                "isHLtitle": "false",
            }
            payload = json.loads(fetch(output, f"metadata/{day}-p{page:03}.json", QUERY, params))
            rows.extend(payload.get("announcements") or [])
            if not payload["hasMore"]:
                break
        else:
            raise ValueError("query pagination limit reached; coverage incomplete")
        for sse in (r for r in candidates if r["SSEDATE"] == day):
            classification, found = match(sse, rows)
            for search_kind, search_key in (
                ("title", sse["TITLE"]),
                ("subject", sse["TITLE"].split("关于", 1)[-1]),
            ):
                if classification != "NO_MATCH":
                    break
                fallback_rows: list[dict[str, Any]] = []
                for fallback_page in range(1, 21):
                    fallback = {**params, "pageNum": fallback_page, "searchkey": search_key}
                    filename = (
                        f"metadata/{search_kind}-{sse['ORG_BULLETIN_ID']}-p{fallback_page:03}.json"
                    )
                    payload = json.loads(fetch(output, filename, QUERY, fallback))
                    fallback_rows.extend(payload.get("announcements") or [])
                    if not payload["hasMore"]:
                        break
                else:
                    raise ValueError("fallback query pagination incomplete")
                classification, found = match(sse, fallback_rows)
            result = {
                "sse": sse,
                "sse_metadata_snapshot_sha256": provenance[sse["URL"]],
                "match_method": "security+publication_date+punctuation_normalized_full_title",
                "match_confidence": classification,
                "cninfo": found,
            }
            if classification == "EXACT":
                cn = found[0]
                path = cn["adjunctUrl"]
                if not re.fullmatch(r"finalpage/\d{4}-\d{2}-\d{2}/\d+\.PDF", path):
                    raise ValueError("unexpected document path")
                raw = fetch(output, f"documents/{cn['announcementId']}.pdf", STATIC + path)
                if not raw.startswith(b"%PDF"):
                    raise ValueError("document response is not PDF; stop ingestion")
                result["cninfo_document_sha256"] = sha(raw)
            results.append(result)
        save(output / "reconciliation.json", results)
        exact = sum(r["match_confidence"] == "EXACT" for r in results)
        print(
            f"dates={index + 1}/{len(dates)} candidates={len(results)}/{len(candidates)} "
            f"exact={exact}",
            flush=True,
        )
    entries = []
    searched: set[str] = set()
    failures: list[dict[str, Any]] = []
    for path in sorted(output.rglob("*.meta.json")):
        metadata = json.loads(path.read_bytes())
        original = path.with_name(path.name.removesuffix(".meta.json"))
        if sha(original.read_bytes()) != metadata["sha256"]:
            raise ValueError("source snapshot changed during ingestion")
        failures.extend(
            {
                "source_url": metadata["url"],
                "snapshot": str(original.relative_to(output)),
                **attempt,
            }
            for attempt in metadata.get("previous_attempts", [])
        )
        if original.parent.name == "metadata":
            searched.update(
                r["announcementId"]
                for r in (json.loads(original.read_bytes()).get("announcements") or [])
            )
        entries.append(
            {"path": path.relative_to(output).as_posix(), "sha256": sha(path.read_bytes())}
        )
    save(
        output / "source-manifest.json",
        {"snapshots": entries, "aggregate_sha256": sha(canonical(entries))},
    )
    save(output / "failure-manifest.json", failures)
    save(
        output / "source-summary.json",
        {
            "cninfo_documents_searched": len(searched),
            "candidate_documents": len(results),
            "exact_matches": sum(r["match_confidence"] == "EXACT" for r in results),
            "high_confidence_matches": 0,
            "ambiguous": sum(r["match_confidence"] == "AMBIGUOUS" for r in results),
            "no_match": sum(r["match_confidence"] == "NO_MATCH" for r in results),
            "downloaded": len(list((output / "documents").glob("*.pdf"))),
            "failed_attempts": len(failures),
            "outstanding_download_failures": 0,
            "cninfo_aggregate_sha256": sha(canonical(entries)),
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sse-snapshot", type=Path, required=True)
    parser.add_argument("--candidate-inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.sse_snapshot, args.candidate_inventory, args.output)
