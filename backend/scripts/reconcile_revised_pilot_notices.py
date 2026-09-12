"""Targeted CNINFO mirrors for independently inventoried new Pilot disclosures."""

import argparse
import json
from pathlib import Path

from scripts.reconcile_sse_cninfo import QUERY, STATIC, fetch, match, save, sha


def required(title):
    return (
        "上市公告书" in title
        or "进入退市整理期交易的公告" in title
        or ("风险警示" in title and "实施" in title and "可能" not in title)
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    records = []
    for inventory in sorted(args.root.glob("*-inventory.json")):
        for notice in json.loads(inventory.read_bytes())["notices"]:
            if not required(notice["TITLE"]):
                continue
            day = notice["SSEDATE"]
            candidates = []
            for page in range(1, 21):
                params = dict(
                    pageNum=page,
                    pageSize=30,
                    column="sse",
                    tabName="fulltext",
                    stock="",
                    searchkey=notice["TITLE"],
                    secid="",
                    plate="",
                    category="",
                    trade="",
                    seDate=f"{day}~{day}",
                    sortName="",
                    sortType="",
                    isHLtitle="false",
                )
                name = (
                    f"cninfo/{notice['SECURITY_CODE']}-{notice['ORG_BULLETIN_ID']}-"
                    f"{notice['ORG_FILE_TYPE']}-p{page}.json"
                )
                response = json.loads(fetch(args.root, name, QUERY, params))
                candidates.extend(response.get("announcements") or [])
                if not response["hasMore"]:
                    break
            else:
                raise ValueError("CNINFO_PAGE_LIMIT")
            confidence, found = match(notice, candidates)
            record = dict(sse=notice, match_confidence=confidence, cninfo=found)
            if confidence == "EXACT":
                document = found[0]
                raw = fetch(
                    args.root,
                    f"documents/{document['announcementId']}.pdf",
                    STATIC + document["adjunctUrl"],
                )
                if not raw.startswith(b"%PDF"):
                    raise ValueError("NOT_PDF")
                record["cninfo_document_sha256"] = sha(raw)
            records.append(record)
            save(args.root / "targeted-reconciliation.json", records)
            print(notice["SECURITY_CODE"], day, confidence, notice["TITLE"], flush=True)


if __name__ == "__main__":
    main()
