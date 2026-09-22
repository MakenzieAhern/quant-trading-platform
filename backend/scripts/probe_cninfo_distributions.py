"""Bounded official CNINFO distribution probe using the existing AKShare public client."""

import argparse
import base64
import csv
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.catalog.freeze import write_immutable


def verified_javascript(sdk_root: Path) -> Path:
    javascript = sdk_root / "akshare/data/cninfo.js"
    records = tuple(sdk_root.glob("akshare-*.dist-info/RECORD"))
    if len(records) != 1:
        raise ValueError("PINNED_CNINFO_SDK_RECORD_UNAVAILABLE")
    expected = next(
        (
            row[1]
            for row in csv.reader(records[0].read_text().splitlines())
            if row[0] == "akshare/data/cninfo.js"
        ),
        None,
    )
    actual = "sha256=" + base64.urlsafe_b64encode(
        bytes.fromhex(sha256_file(javascript))
    ).decode().rstrip("=")
    if expected != actual:
        raise ValueError("PINNED_CNINFO_JAVASCRIPT_CHANGED")
    return javascript


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.append(str(args.sdk_root))
    from py_mini_racer import MiniRacer

    sdk = args.sdk_root / "akshare"
    javascript = verified_javascript(args.sdk_root)
    client = sdk / "stock/stock_dividend_cninfo.py"
    runtime = MiniRacer()
    runtime.eval(javascript.read_text())
    for code in ("600989", "600005"):
        target = args.output / f"{code}.json"
        receipt = args.output / f"{code}.json.meta.json"
        if receipt.exists():
            print(code, "CHECKPOINT_EXISTS_NO_RETRY", flush=True)
            continue
        url = "https://webapi.cninfo.com.cn/api/sysapi/p_sysapi1139?" + urlencode(dict(scode=code))
        metadata = dict(
            url=url,
            method="POST",
            retrieved_at_utc=datetime.now(UTC).isoformat(),
            client_sha256=sha256_file(client),
            public_client_js_sha256=sha256_file(javascript),
            parser_version="CNINFO_DISTRIBUTION_RAW_PROBE_V1",
            acceptance="NOT_ESTABLISHED",
        )
        try:
            request = urllib.request.Request(
                url,
                data=b"",
                headers={
                    "Accept-Enckey": runtime.call("getResCode1"),
                    "Referer": "https://webapi.cninfo.com.cn/",
                },
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
                metadata["http_status"] = response.status
            write_immutable(target, raw)
            metadata["sha256"] = sha256_file(target)
            payload = json.loads(raw, parse_float=str)
            metadata["record_count"] = len(payload.get("records", []))
            metadata["response_keys"] = sorted(payload)
            metadata["response_code"] = payload.get("resultcode", payload.get("code"))
        except Exception as exc:
            metadata["error"] = f"{type(exc).__name__}: {exc}"
        write_immutable(receipt, canonical_json_bytes(metadata) + b"\n")
        print(json.dumps(metadata), flush=True)


if __name__ == "__main__":
    main()
