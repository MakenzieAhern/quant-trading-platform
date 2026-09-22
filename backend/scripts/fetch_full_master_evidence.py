"""Checkpoint targeted official full-history master evidence; not acceptance."""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlsplit

from scripts.fetch_a_share_security_master import OfficialFetcher, _json_bytes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--exchange", choices=("SSE", "SZSE"), default="SZSE")
    args = parser.parse_args()
    if Path(args.name).name != args.name or args.name in ("", ".", ".."):
        parser.error("name must be a basename")
    host = urlsplit(args.url).hostname or ""
    domain = "sse.com.cn" if args.exchange == "SSE" else "szse.cn"
    if urlsplit(args.url).scheme != "https" or not (host == domain or host.endswith("." + domain)):
        parser.error("expected an official HTTPS exchange source")
    manifest = args.output / "source-snapshot-manifest.json"
    prior = json.loads(manifest.read_text()) if manifest.exists() else {"snapshots": []}
    cached = {item["raw_snapshot_filename"]: item for item in prior["snapshots"]}
    existing = args.output / "raw" / args.name
    if existing.exists() and (
        args.name not in cached
        or cached[args.name]["source_url"] != args.url
        or cached[args.name]["sha256"] != hashlib.sha256(existing.read_bytes()).hexdigest()
    ):
        raise ValueError("EXISTING_EVIDENCE_IDENTITY_CHANGED_USE_NEW_FILENAME")
    fetcher = OfficialFetcher(args.output / "raw", cached=cached)
    fetcher.get(args.name, args.url, exchange=args.exchange, referer=f"https://www.{domain}/")
    cached.update({item["raw_snapshot_filename"]: item for item in fetcher.snapshots})
    value = {
        "status": "EVIDENCE_ONLY_NOT_ACCEPTED",
        "snapshots": [cached[k] for k in sorted(cached)],
    }
    manifest.write_bytes(_json_bytes(value) + b"\n")
    print(json.dumps(fetcher.snapshots, ensure_ascii=True))


if __name__ == "__main__":
    main()
