"""Bounded existing BaoStock corporate-action route check; no source promotion."""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.data.catalog.checksums import canonical_json_bytes, sha256_file
from app.data.catalog.freeze import write_immutable

QUERY = """
import json, socket, sys, baostock as bs
import baostock.common.contants as constants
socket.setdefaulttimeout(10)
login = bs.login()
report = dict(login_error_code=login.error_code, login_error_message=login.error_msg, queries=[],
              endpoint=f'tcp://{constants.BAOSTOCK_SERVER_IP}:{constants.BAOSTOCK_SERVER_PORT}',
              sdk_version=constants.BAOSTOCK_CLIENT_VERSION)
if login.error_code == '0':
    for year in ('2010', '2025'):
        result = bs.query_dividend_data(code=sys.argv[1], year=year, yearType='operate')
        rows = []
        while result.error_code == '0' and result.next():
            rows.append(dict(zip(result.fields, result.get_row_data(), strict=True)))
        report['queries'].append(dict(year=year, error_code=result.error_code,
                                     error_message=result.error_msg, rows=rows))
        if result.error_code != '0':
            break
print('RESULT=' + json.dumps(report, ensure_ascii=True), flush=True)
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code", default="sh.600000")
    args = parser.parse_args()
    if not re.fullmatch(r"(?:sh|sz)\.\d{6}", args.code):
        parser.error("expected exchange-qualified six-digit code")
    path = args.output / "probe.json"
    sdk = args.sdk_root / "baostock"
    source_hashes = {
        p.relative_to(sdk).as_posix(): sha256_file(p) for p in sorted(sdk.rglob("*.py"))
    }
    if not source_hashes:
        raise ValueError("EXISTING_SDK_MISSING")
    if path.exists():
        cached = json.loads(path.read_bytes())
        if cached["code"] != args.code or cached["sdk_source_sha256"] != source_hashes:
            raise ValueError("CACHED_PROBE_IDENTITY_CHANGED")
        print(path.read_text())
        return
    attempts = []
    for number in (1, 2):
        row = dict(attempt=number, retrieved_at_utc=datetime.now(UTC).isoformat())
        try:
            result = subprocess.run(
                [sys.executable, "-c", QUERY, args.code],
                env={
                    **os.environ,
                    "PYTHONPATH": os.pathsep.join(
                        filter(None, (str(args.sdk_root), os.environ.get("PYTHONPATH")))
                    ),
                },
                capture_output=True,
                text=True,
                timeout=35,
                check=False,
            )
            row.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
            payload = [
                line[7:] for line in result.stdout.splitlines() if line.startswith("RESULT=")
            ]
            if payload:
                row["result"] = json.loads(payload[-1])
        except subprocess.TimeoutExpired:
            row["error"] = "SUBPROCESS_DEADLINE_EXCEEDED_35_SECONDS"
        attempts.append(row)
        print(json.dumps(row), flush=True)
        if not row.get("error") and row.get("result", {}).get("login_error_code") not in {
            "10002003",
            "10002007",
            "10002008",
        }:
            break
    report = dict(
        provider="BaoStock",
        endpoint=attempts[-1].get("result", {}).get("endpoint"),
        function="query_dividend_data",
        code=args.code,
        years=[2010, 2025],
        year_type="operate",
        attempts=attempts,
        sdk_source_sha256=source_hashes,
        status="PROBE_ONLY_NOT_ACCEPTED",
        corporate_action_authority="NOT_ESTABLISHED",
    )
    write_immutable(path, canonical_json_bytes(report) + b"\n")


if __name__ == "__main__":
    main()
