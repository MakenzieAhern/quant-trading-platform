"""Bounded SDK subprocess. No automatic execution/import-time networking."""

import contextlib
import importlib
import json
import os
import socket
import sys
from typing import Any

from app.application.market_updates.contracts import SDK_VERSION, utc_now
from app.application.market_updates.transport import sdk_available


def access_denied(code: object, message: str) -> bool:
    return str(code) in {"401", "402", "403"} or any(
        word in message.lower()
        for word in (
            "401",
            "402",
            "403",
            "forbidden",
            "unauthorized",
            "captcha",
            "payment",
            "paywall",
            "access denied",
            "permission",
            "付费",
            "权限",
            "验证码",
        )
    )


def check_result(result: Any) -> None:
    code = str(result.error_code)
    if code != "0":
        message = str(getattr(result, "error_msg", "")).lower()
        denied = access_denied(code, message)
        raise RuntimeError("SOURCE_ACCESS_DENIED" if denied else "PROVIDER_TRANSPORT_FAILED")


def main() -> None:
    output: dict[str, Any]
    try:
        if not sdk_available():
            raise RuntimeError("BAOSTOCK_SDK_NOT_INSTALLED")
        params = json.loads(sys.argv[1])
        socket.setdefaulttimeout(8)
        sdk = importlib.import_module("baostock")
        with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
            check_result(sdk.login())
            requested = utc_now()
            result = sdk.query_history_k_data_plus(**params)
            check_result(result)
            rows = []
            while result.next():
                check_result(result)
                rows.append(result.get_row_data())
                if len(rows) > 31:
                    raise RuntimeError("PROVIDER_RESPONSE_TOO_LARGE")
            check_result(result)
            completed = utc_now()
        output = {
            "requested_at_utc": requested.isoformat(),
            "response_completed_at_utc": completed.isoformat(),
            "sdk_version": SDK_VERSION,
            "fields": result.fields,
            "rows": rows,
        }
    except Exception as exc:
        safe = {
            "SOURCE_ACCESS_DENIED",
            "PROVIDER_TRANSPORT_FAILED",
            "PROVIDER_RESPONSE_TOO_LARGE",
            "BAOSTOCK_SDK_NOT_INSTALLED",
        }
        # Some SDK/HTTP errors are raised rather than returned as result.error_code.
        code = getattr(exc, "status_code", getattr(exc, "code", None))
        output = {
            "error_code": "SOURCE_ACCESS_DENIED"
            if access_denied(code, str(exc))
            else str(exc)
            if str(exc) in safe
            else "PROVIDER_TRANSPORT_FAILED"
        }
    print(json.dumps(output, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
