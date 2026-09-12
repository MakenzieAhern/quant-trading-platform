"""Dated IPO evidence for mixed stock/CDR venues; typed original A-listing registers elsewhere."""

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from itertools import batched
from pathlib import Path
from urllib.parse import urlencode

from app.domain.markets.identifiers import InstrumentType
from app.domain.markets.security import InstrumentClassification
from scripts.reconcile_sse_cninfo import canonical, fetch, save, sha


def ipo_type(row: dict, symbol: str, listing: str) -> InstrumentType | None:
    if row.get("SECURITY_CODE") != symbol or not row.get("SSEDATE"):
        return None
    if (
        not (date.fromisoformat(listing) - timedelta(days=60)).isoformat()
        <= row["SSEDATE"]
        <= listing
    ):
        return None
    title = row["TITLE"]
    if "上市公告书" not in title or not any(term in title for term in ("首次公开发行", "首次发行")):
        return None
    if "存托凭证" in title:
        return InstrumentType.CDR
    if "发行股票" in title and "优先股" not in title:
        return InstrumentType.COMMON_A_SHARE
    return None


def classify(staging: Path, member: dict) -> dict:
    sources = member["sources"]
    for source in sources:
        if sha((staging / source["path"]).read_bytes()) != source["sha256"]:
            raise ValueError("CLASSIFICATION_REGISTER_CHANGED")
    values = dict(
        security_id={"value": member["security_id"]},
        instrument_type=member["instrument_type"],
        effective_from=member["listing_date"],
    )
    if member["board"] != "SSE_STAR":
        # These are typed original A-share listing columns, not an undated current SEC_TYPE.
        source = sources[0]
        fields = member["source_fields"]
        if member["exchange"] == "SZSE":
            code, listed = (
                fields.get("A股代码", fields.get("agdm")),
                fields.get("A股上市日期", fields.get("agssrq")),
            )
        else:
            code, listed = fields.get("A_STOCK_CODE"), fields.get("LIST_DATE")
            listed = date.fromisoformat(listed).isoformat() if listed else None
        if code != member["symbol"] or listed != member["listing_date"]:
            raise ValueError("ORIGINAL_TYPED_LISTING_NOT_VERIFIED")
        fact = InstrumentClassification(
            **values,
            source_publication_date=None,
            evidence_basis="ORIGINAL_TYPED_LISTING_REGISTER",
            source_listing_date=listed,
            source_url=source["source_url"],
            source_document_sha256=source["sha256"],
            retrieval_timestamp=source["retrieval_timestamp_utc"],
        )
        return dict(
            classification=fact.model_dump(mode="json"),
            sources=sources,
            original_typed_listing_fields=fields,
        )
    output = staging / "instrument-scope-20260912"
    # Reuse the already verified dated CDR fact by identity, never by a symbol exception.
    old = json.loads((output / "classifications.json").read_bytes())
    for record in old:
        fact = InstrumentClassification.model_validate(record["classification"])
        if str(fact.security_id) == member["security_id"]:
            path = output / record["snapshot"]
            if (
                sha(path.read_bytes()) != fact.source_document_sha256
                or fact.instrument_type.value != member["instrument_type"]
            ):
                raise ValueError("EXISTING_DATED_INSTRUMENT_EVIDENCE_CHANGED")
            return dict(
                classification=fact.model_dump(mode="json"),
                sources=[
                    *sources,
                    dict(
                        path=path.relative_to(staging).as_posix(),
                        sha256=fact.source_document_sha256,
                        source_url=fact.source_url,
                        retrieval_timestamp_utc=fact.retrieval_timestamp.isoformat(),
                    ),
                ],
            )
    for page in range(1, 7):
        params = {
            "isPagination": "true",
            "pageHelp.pageSize": 10,
            "pageHelp.cacheSize": 1,
            "pageHelp.pageNo": page,
            "pageHelp.beginPage": page,
            "pageHelp.endPage": page,
            "START_DATE": (
                date.fromisoformat(member["listing_date"]) - timedelta(days=60)
            ).isoformat(),
            "END_DATE": member["listing_date"],
            "SECURITY_CODE": member["symbol"],
            "TITLE": "",
            "BULLETIN_TYPE": "",
        }
        url = "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?" + urlencode(
            params
        )
        name = f"ipo/{member['symbol']}-p{page:03}.json"
        raw = fetch(output, name, url, referer="https://www.sse.com.cn/")
        payload = json.loads(raw)
        matches = [
            row
            for group in payload["result"]
            for row in group
            if ipo_type(row, member["symbol"], member["listing_date"]) is not None
        ]
        if matches:
            if any(
                ipo_type(row, member["symbol"], member["listing_date"]).value
                != member["instrument_type"]
                for row in matches
            ):
                raise ValueError("IPO_AND_CURRENT_REGISTER_TYPE_CONFLICT")
            row = min(matches, key=lambda r: (r["SSEDATE"], r["ORG_BULLETIN_ID"]))
            path = output / name
            meta = json.loads(path.with_suffix(".json.meta.json").read_bytes())
            fact = InstrumentClassification(
                **values,
                source_publication_date=row["SSEDATE"],
                source_url=url,
                source_document_sha256=sha(raw),
                retrieval_timestamp=meta["retrieved_at_utc"],
            )
            return dict(
                classification=fact.model_dump(mode="json"),
                ipo_notice_metadata=row,
                sources=[
                    *sources,
                    dict(
                        path=path.relative_to(staging).as_posix(),
                        sha256=sha(raw),
                        source_url=url,
                        retrieval_timestamp_utc=meta["retrieved_at_utc"],
                    ),
                ],
            )
        if page >= (payload["pageHelp"]["pageCount"] or 0):
            break
    raise ValueError("DATED_IPO_INSTRUMENT_TYPE_UNRESOLVED:" + member["security_id"])


def build(staging: Path, *, allow_partial_inventory: bool = False) -> None:
    output = staging / "instrument-scope-20260912"
    members = json.loads((output / "current-register-inventory.json").read_bytes())
    if not allow_partial_inventory:
        audit = json.loads((output / "current-register-audit.json").read_bytes())
        if audit["unclassified"] or audit["inventory_sha256"] != sha(canonical(members)):
            raise ValueError("CURRENT_REGISTER_INVENTORY_INCOMPLETE")
    target = output / "approved-classifications.json"
    records = json.loads(target.read_bytes()) if target.exists() else []
    completed = {r["classification"]["security_id"]["value"]: r for r in records}
    for record in records:
        if any(sha((staging / s["path"]).read_bytes()) != s["sha256"] for s in record["sources"]):
            raise ValueError("COMPLETED_CLASSIFICATION_SOURCE_CHANGED")
    remaining = [m for m in members if m["security_id"] not in completed]
    failures = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for batch in batched(remaining, 2):
            jobs = [(m, pool.submit(classify, staging, m)) for m in batch]
            for member, future in jobs:
                try:
                    result = future.result()
                    completed[member["security_id"]] = result
                except Exception as exc:
                    failures.append(
                        dict(
                            security_id=member["security_id"],
                            error_type=type(exc).__name__,
                            error=str(exc),
                        )
                    )
                    if getattr(exc, "code", None) in {403, 429} or "ACCESS_DENIED" in str(exc):
                        save(output / "classification-failures.json", failures)
                        raise
            save(target, [completed[k] for k in sorted(completed)])
            save(output / "classification-failures.json", failures)
            if len(completed) % 25 < 2 or failures or len(completed) == len(members):
                print(
                    f"dated_classifications={len(completed)}/{len(members)} "
                    f"unresolved={len(failures)}",
                    flush=True,
                )
            if any(m["board"] == "SSE_STAR" for m in batch):
                time.sleep(0.5)
    if failures:
        raise SystemExit("HISTORICAL_CLASSIFICATION_GAPS_REQUIRE_TARGETED_REVIEW")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--staging", required=True, type=Path)
    parser.add_argument("--allow-partial-inventory", action="store_true")
    args = parser.parse_args()
    build(args.staging, allow_partial_inventory=args.allow_partial_inventory)
