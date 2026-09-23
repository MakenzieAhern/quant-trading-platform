"""Only this supervised child may contact the public single-security endpoint."""

import asyncio
import json
import sys
from contextlib import suppress
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from app.application.market_updates.contracts import (
    SDK_VERSION,
    UpdateCancelled,
    UpdateError,
    utc_now,
)

MAX_OUTPUT = 256 * 1024


def sdk_available() -> bool:
    try:
        return version("baostock") == SDK_VERSION
    except PackageNotFoundError:
        return False


async def fetch(
    parameters: dict[str, str], cancelled: asyncio.Event, *, timeout: float = 45
) -> tuple[dict[str, Any], datetime, datetime]:
    if not sdk_available():
        raise UpdateError("BAOSTOCK_SDK_NOT_INSTALLED")
    if cancelled.is_set():
        raise UpdateCancelled
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "app.application.market_updates.worker",
        json.dumps(parameters),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
        limit=MAX_OUTPUT,
    )
    assert process.stdout is not None

    async def receive() -> dict[str, Any]:
        content = await process.stdout.read(MAX_OUTPUT + 1)  # type: ignore[union-attr]
        if len(content) > MAX_OUTPUT:
            raise UpdateError("PROVIDER_RESPONSE_TOO_LARGE")
        # read(n) can return short before EOF. Accumulate under the same hard bound.
        while extra := await process.stdout.read(MAX_OUTPUT + 1 - len(content)):  # type: ignore[union-attr]
            content += extra
            if len(content) > MAX_OUTPUT:
                raise UpdateError("PROVIDER_RESPONSE_TOO_LARGE")
        await process.wait()
        try:
            payload: dict[str, Any] = json.loads(content)
        except (ValueError, TypeError) as exc:
            raise UpdateError("PROVIDER_TRANSPORT_FAILED") from exc
        if not isinstance(payload, dict):
            raise UpdateError("PROVIDER_TRANSPORT_FAILED")
        code = payload.get("error_code")
        if code is not None:
            raise UpdateError(str(code))
        if process.returncode != 0:
            raise UpdateError("PROVIDER_TRANSPORT_FAILED")
        return payload

    receiving = asyncio.create_task(receive())
    stopping = asyncio.create_task(cancelled.wait())
    try:
        done, _ = await asyncio.wait(
            {receiving, stopping}, timeout=timeout, return_when=asyncio.FIRST_COMPLETED
        )
        if receiving not in done:
            if stopping in done:
                raise UpdateCancelled
            raise UpdateError("PROVIDER_TIMEOUT")
        # If cancellation and a complete response race, retain the received fact
        # (including denial); the manager still cancels subsequent work and success.
        envelope = await receiving
        received = utc_now()
        try:
            requested = datetime.fromisoformat(envelope["requested_at_utc"])
            completed = datetime.fromisoformat(envelope["response_completed_at_utc"])
        except (KeyError, TypeError, ValueError) as exc:
            raise UpdateError("INVALID_RECEIPT_TIMESTAMP") from exc
        if (
            requested.tzinfo is None
            or completed.tzinfo is None
            or not requested <= completed <= received
        ):
            raise UpdateError("INVALID_RECEIPT_TIMESTAMP")
        return envelope, requested, received
    finally:
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.kill()
        await process.wait()
        for task in (receiving, stopping):
            task.cancel()
        await asyncio.gather(receiving, stopping, return_exceptions=True)
