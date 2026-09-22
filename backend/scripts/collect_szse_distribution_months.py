"""Resume official monthly distribution tables without inferring event acceptance."""

import argparse
import json
import re
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlsplit

from app.data.catalog.checksums import canonical_json_bytes, canonical_sha256, sha256_file
from app.data.catalog.freeze import write_immutable
from scripts.reconcile_sse_cninfo import fetch

ARCHIVE = "https://investor.szse.cn/market/periodical/month/index.html"


def month_links(text):
    rows = re.findall(r"value:'([^']+)'\s*,\s*text:'([^']+)'", text)
    selected = [
        (month, urljoin(ARCHIVE, link)) for link, month in rows if "2010-01" <= month <= "2025-12"
    ]
    expected = [f"{year}-{month:02}" for year in range(2010, 2026) for month in range(1, 13)]
    if sorted(month for month, _ in selected) != expected:
        raise ValueError("MONTHLY_ARCHIVE_INCOMPLETE_OR_DUPLICATED")
    return sorted(selected)


def table_link(text, menu_url):
    matches = re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>\s*分红派息配股', text)
    if len(matches) != 1:
        raise ValueError("DISTRIBUTION_TABLE_LINK_NOT_UNIQUE")
    url = urljoin(menu_url, unescape(matches[0]))
    parts = urlsplit(url)
    if parts.hostname not in {"investor.szse.cn", "www.szse.cn", "docs.static.szse.cn"}:
        raise ValueError("NON_OFFICIAL_TABLE_SOURCE")
    return parts._replace(scheme="https").geturl()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    archive = fetch(args.root, "monthly-archive-investor.html", ARCHIVE)
    months = month_links(archive.decode("utf-8"))

    def collect(item):
        month, url = item
        try:
            menu_name = f"menu-{month}.html"
            menu = fetch(args.root, menu_name, url).decode("utf-8")
            link = table_link(menu, url)
            table_name = f"distributions-{month}.html"
            raw = fetch(args.root, table_name, link)
            result = dict(
                month=month,
                status="SOURCE_BYTES_RETRIEVED_NOT_ACCEPTED",
                sources=[
                    json.loads((args.root / (name + ".meta.json")).read_bytes())
                    for name in (menu_name, table_name)
                ],
                table_file=table_name,
                bytes=len(raw),
            )
        except Exception as exc:
            result = dict(month=month, status="FAILED", error=f"{type(exc).__name__}: {exc}")
        print(month, result["status"], flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(collect, months))
    report = dict(
        parser_version="SZSE_MONTHLY_DISTRIBUTION_SOURCE_V2",
        parser_sha256=sha256_file(Path(__file__)),
        archive_sha256=sha256_file(args.root / "monthly-archive-investor.html"),
        results=results,
        failure_manifest=[r for r in results if r["status"] == "FAILED"],
        full_census_accepted=False,
        dataset_created=False,
    )
    report["manifest_sha256"] = canonical_sha256(report)
    write_immutable(
        args.root / "monthly-source-manifest-v2.json", canonical_json_bytes(report) + b"\n"
    )


if __name__ == "__main__":
    main()
