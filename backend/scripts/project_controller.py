"""Read-only R1-R3 next-stage gate; never executes ingestion, studies or Git actions."""

import argparse
import json
from pathlib import Path
from typing import Any

AUTHORITIES = {
    "SECURITY_MASTER",
    "SSE",
    "SZSE",
    "OHLCV",
    "ADJUSTMENT",
    "CALENDAR",
    "BENCHMARK",
    "MARKET_RULE",
}


def next_stage(state: dict[str, Any], lock: dict[str, Any]) -> str:
    """Fail closed; future stages need their separately authorized implementation."""
    if state.get("branch") != "feature/a-share-research-v1.1" or state.get("pr") != 12:
        raise ValueError("WRONG_PROJECT_TARGET")
    for flag in (
        "dataset_frozen",
        "dataset_audited",
        "pilot_dataset_created",
        "oos_authorized",
        "release_authorized",
    ):
        if type(state.get(flag)) is not bool:
            raise ValueError("INVALID_STATE_FLAG")
    if lock.get("oos_authorized") is not False or state["oos_authorized"]:
        raise ValueError("OOS_OUTSIDE_R1_R3_SCOPE")
    if state["dataset_frozen"] or state["release_authorized"]:
        raise ValueError("HUMAN_GATE_OUTSIDE_R1_R3_SCOPE")
    authorities = state.get("authorities", {})
    authority_pass = set(authorities) == AUTHORITIES and all(
        authorities[key] == ("PASS_FOR_PILOT" if key == "MARKET_RULE" else "PASS")
        for key in AUTHORITIES
    )
    preflight_pass = state.get("source_authority_preflight") == "PASS"
    execution_pass = state.get("execution_convention_validation") == "PASS"
    if preflight_pass and not authority_pass:
        raise ValueError("UNSUPPORTED_PREFLIGHT_PASS")
    stage = state.get("current_stage")
    if stage not in {"R1", "R2", "R3"}:
        raise ValueError("FUTURE_STAGE_REQUIRES_APPROVAL")
    if stage != "R1" and not preflight_pass:
        raise ValueError("SOURCE_GATE_NOT_PASSED")
    if stage != "R1" and not execution_pass:
        raise ValueError("EXECUTION_CONVENTION_GATE_NOT_PASSED")
    if state["dataset_audited"] and not state["pilot_dataset_created"]:
        raise ValueError("AUDIT_WITHOUT_DATASET")
    if state["dataset_audited"] and state.get("pilot_data_readiness") != "READY":
        raise ValueError("AUDIT_READINESS_INCONSISTENT")
    if stage == "R3" and not state["pilot_dataset_created"]:
        raise ValueError("DATASET_GATE_NOT_PASSED")
    if state.get("status") in {"BLOCKED", "AWAITING_HUMAN"}:
        return "STOP"
    if state.get("status") != "RUNNING":
        raise ValueError("INVALID_CONTROLLER_STATUS")
    if stage == "R1":
        return "R2" if preflight_pass and execution_pass else "R1"
    if stage == "R2":
        return "R3" if state["pilot_dataset_created"] else "R2"
    return "GATE_A" if state["dataset_audited"] else "R3"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.root / ".research/project_state.json").read_bytes())
    lock = json.loads((args.root / ".research/oos_lock.json").read_bytes())
    print(next_stage(state, lock))
