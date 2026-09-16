"""Collect official SSE/SZSE suspension facts without inferring them from missing bars."""

import argparse
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlencode, urljoin, urlsplit

from app.data.catalog.checksums import canonical_sha256, sha256_file
from scripts.reconcile_sse_cninfo import fetch, save

SSE_QUERY = "https://query.sse.com.cn/commonSoaQuery.do"
SZSE_REFERER = "https://www.szse.cn/"


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", value))).replace("\xa0", " ").strip()


def _row_key(row: dict) -> str:
    return json.dumps(row, ensure_ascii=False, sort_keys=True)


def szse_rows(raw: bytes) -> list[dict[str, str | None]]:
    text = raw.decode("gb18030")
    result = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.I | re.S):
        cells = [_text(cell) for cell in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.I | re.S)]
        if len(cells) != 5 or re.fullmatch(r"\d{6}", cells[0]) is None:
            continue
        result.append(
            {
                "symbol": cells[0],
                "name": cells[1],
                "reason": cells[2],
                "suspended_at": cells[3] or None,
                "resumed_at": cells[4] or None,
            }
        )
    return result


def szse_table_link(menu: bytes, menu_url: str) -> str:
    matches = re.findall(
        r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>\s*证券停牌情况',
        menu.decode("utf-8"),
    )
    if len(matches) != 1:
        raise ValueError("SZSE_SUSPENSION_TABLE_LINK_NOT_UNIQUE")
    url = urljoin(menu_url, unescape(matches[0]))
    host = urlsplit(url).hostname or ""
    if not (host == "szse.cn" or host.endswith(".szse.cn")):
        raise ValueError("NON_OFFICIAL_SZSE_SOURCE")
    return urlsplit(url)._replace(scheme="https").geturl()


def sse_url(year: int, page: int) -> str:
    params = {
        "isPagination": "true",
        "sqlId": "GW_PL_JYTS_TFPXX",
        "pageHelp.pageSize": "2000",
        "pageHelp.pageNo": str(page),
        "productCode": "",
        "keyWords": "",
        "startStopDate": f"{year}0101",
        "endStopDate": f"{year}1231",
    }
    return SSE_QUERY + "?" + urlencode(params)


def _source(root: Path, name: str) -> dict:
    path = root / name
    meta = json.loads(path.with_suffix(path.suffix + ".meta.json").read_bytes())
    if sha256_file(path) != meta["sha256"]:
        raise ValueError("SOURCE_CHECKSUM_MISMATCH")
    return {
        "path": name,
        "url": meta["url"],
        "retrieved_at_utc": meta["retrieved_at_utc"],
        "sha256": meta["sha256"],
    }


def collect_sse(root: Path) -> tuple[list[dict], list[dict]]:
    rows, sources = [], []
    for year in range(2010, 2026):
        page = 1
        while True:
            name = f"sse-{year}-p{page}.json"
            raw = fetch(root, name, sse_url(year, page), referer="https://www.sse.com.cn/")
            data = json.loads(raw)
            rows.extend(
                {**item, "source_file": name, "source_year": year} for item in data["result"]
            )
            sources.append(_source(root, name))
            if page >= data["pageHelp"]["pageCount"]:
                if sum(row["source_year"] == year for row in rows) != data["pageHelp"]["total"]:
                    raise ValueError("SSE_PAGE_TOTAL_MISMATCH")
                break
            page += 1
    return rows, sources


def collect_szse(root: Path, menu_root: Path) -> tuple[list[dict], list[dict]]:
    rows, sources = [], []
    months = [f"{year}-{month:02}" for year in range(2010, 2026) for month in range(1, 13)]
    for month in months:
        menu = menu_root / f"menu-{month}.html"
        menu_meta = json.loads(menu.with_suffix(menu.suffix + ".meta.json").read_bytes())
        if sha256_file(menu) != menu_meta["sha256"]:
            raise ValueError("SZSE_MENU_CHECKSUM_MISMATCH")
        url = szse_table_link(menu.read_bytes(), menu_meta["url"])
        name = f"szse-{month}.html"
        raw = fetch(root, name, url, referer=SZSE_REFERER)
        rows.extend({**row, "source_file": name, "source_month": month} for row in szse_rows(raw))
        sources.append(
            {
                **_source(root, name),
                "menu_path": str(menu),
                "menu_sha256": menu_meta["sha256"],
            }
        )
        print(month, len(rows), flush=True)
    return rows, sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--szse-menu-root", type=Path, required=True)
    args = parser.parse_args()
    sse, sse_sources = collect_sse(args.output)
    szse, szse_sources = collect_szse(args.output, args.szse_menu_root)
    normalized = {
        "sse": sorted(sse, key=_row_key),
        "szse": sorted(szse, key=_row_key),
    }
    save(args.output / "official-suspension-observations-v1.json", normalized)
    report = {
        "parser_version": "FULL_OFFICIAL_SUSPENSION_SOURCE_V1",
        "parser_sha256": sha256_file(Path(__file__)),
        "coverage": ["2010-01-01", "2025-12-31"],
        "sse_rows": len(sse),
        "szse_rows": len(szse),
        "sse_sources": sse_sources,
        "szse_sources": szse_sources,
        "input_order_reproducibility": (
            "PASS"
            if canonical_sha256(normalized)
            == canonical_sha256(
                {
                    "sse": sorted(reversed(sse), key=_row_key),
                    "szse": sorted(reversed(szse), key=_row_key),
                }
            )
            else "FAIL"
        ),
        "source_failures": [],
        "authority_status": "SOURCE_BYTES_RETRIEVED_NOT_YET_DAILY_STATUS_AUTHORITY",
    }
    report["manifest_sha256"] = canonical_sha256(report)
    save(args.output / "source-manifest-v1.json", report)
    print(json.dumps({k: v for k, v in report.items() if not k.endswith("sources")}))


if __name__ == "__main__":
    main()
