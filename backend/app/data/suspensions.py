"""Shared read-only interpretation of accepted exchange suspension boundaries."""

import re
from datetime import date, time
from typing import Any


def suspension_boundary(value: str | None) -> tuple[str | None, time | None]:
    if value is None:
        return None, None
    match = re.match(r"^(\d{4})[-/](\d{2})[-/](\d{2})(?:\s+(\d{1,2}):(\d{2}))?", value)
    if match is None:
        raise ValueError("DATASET_INTEGRITY_FAILED")
    year, month, day, hour, minute = match.groups()
    return date(int(year), int(month), int(day)).isoformat(), (
        time(int(hour), int(minute)) if hour is not None else None
    )


def suspension_evidence(row: dict[str, Any], day: str) -> dict[str, Any] | None:
    start, start_time = suspension_boundary(row["suspended_at"])
    end, end_time = suspension_boundary(row["resumed_or_ended_at"])
    if start is None or (end is not None and end < start):
        raise ValueError("DATASET_INTEGRITY_FAILED")
    if day < start or (end is not None and day > end):
        return None
    recorded = {"1": True, "0": False}.get(str(row.get("execution_open_blocked")))
    exchange = row.get("exchange") or row["security_id"].split(":")[1]
    if day == start:
        blocked = (
            recorded
            if exchange == "SSE"
            else (start_time <= time(9, 30) if start_time is not None else None)
        )
        semantics = "SUSPENSION_START_DAY"
        active = True
    elif day == end:
        # SSE endStopDate is not a proved resumption-at-open timestamp.
        # SZSE supplements' blocked flag applies to the resumption boundary, not its start.
        blocked = (
            (
                recorded
                if recorded is not None
                else end_time > time(9, 30)
                if end_time is not None
                else None
            )
            if exchange == "SZSE"
            else None
        )
        semantics = (
            "SZSE_RESUMPTION_BOUNDARY" if exchange == "SZSE" else "SSE_END_STOP_DATE_UNCERTAIN"
        )
        active = blocked is True
    else:
        blocked, active, semantics = True, True, "INSIDE_SUSPENSION_INTERVAL"
    return {
        **row,
        "suspended_date": start,
        "resumed_or_ended_date": end,
        "boundary_semantics": semantics,
        "day_open_blocked": blocked,
        "suspension_confirmed_on_day": active,
    }
