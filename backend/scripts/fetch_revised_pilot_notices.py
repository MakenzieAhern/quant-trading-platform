"""Resume targeted official disclosure inventory for newly discovered Pilot members."""

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode

from scripts.reconcile_sse_cninfo import fetch, save, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    impact = json.loads((args.master / "master-impact.json").read_bytes())
    members = json.loads((args.master / "candidate-master.json").read_bytes())
    for member in members:
        if member["security_id"] not in impact["new_active_during_pilot"]:
            continue
        if member["exchange"] != "SSE":
            raise ValueError("NEW_EXCHANGE_REQUIRES_EXISTING_EXCHANGE_DISCLOSURE_RECONCILER")
        rows, sources = [], []
        groups_seen = 0
        for page in range(1, 101):
            params = {
                "isPagination": "true",
                "pageHelp.pageSize": 100,
                "pageHelp.pageNo": page,
                "pageHelp.beginPage": page,
                "pageHelp.endPage": page,
                "pageHelp.cacheSize": 1,
                "START_DATE": "2019-01-01",
                "END_DATE": "2024-07-31",
                "SECURITY_CODE": member["symbol"],
                "TITLE": "",
                "BULLETIN_TYPE": "",
            }
            url = "https://query.sse.com.cn/security/stock/queryCompanyBulletinNew.do?" + urlencode(
                params
            )
            name = f"{member['symbol']}/p{page:03}.json"
            raw = fetch(args.output, name, url, referer="https://www.sse.com.cn/")
            data = json.loads(raw)
            groups_seen += len(data["result"])
            batch = [row for group in data["result"] for row in group]
            if any(r["SECURITY_CODE"] != member["symbol"] for r in batch):
                raise ValueError("WRONG_DISCLOSURE_ISSUER")
            rows.extend(batch)
            sources.append(dict(path=name, sha256=sha(raw), url=url))
            if page >= int(data["pageHelp"]["pageCount"]):
                if groups_seen != int(data["pageHelp"]["total"]):
                    raise ValueError("INCOMPLETE_DISCLOSURE_PAGINATION")
                break
        else:
            raise ValueError("DISCLOSURE_PAGE_BOUND_EXCEEDED")
        save(
            args.output / f"{member['symbol']}-inventory.json",
            dict(member=member, sources=sources, notices=rows),
        )
        relevant = [
            r
            for r in rows
            if any(t in r["TITLE"] for t in ("风险警示", "退市", "终止上市", "上市公告书", "转板"))
        ]
        print(
            json.dumps(
                dict(symbol=member["symbol"], total=len(rows), relevant=relevant), ensure_ascii=True
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
