import pytest

from scripts.project_controller import AUTHORITIES, next_stage


def test_controller_progresses_only_through_evidenced_pre_research_gates():
    state = dict(
        branch="feature/a-share-research-v1.1",
        pr=12,
        current_stage="R1",
        status="RUNNING",
        dataset_frozen=False,
        dataset_audited=False,
        pilot_dataset_created=False,
        oos_authorized=False,
        release_authorized=False,
        source_authority_preflight="FAIL",
        authorities={},
    )
    lock = {"oos_authorized": False}
    assert next_stage(state, lock) == "R1"
    state["source_authority_preflight"] = "PASS"
    with pytest.raises(ValueError, match="UNSUPPORTED_PREFLIGHT"):
        next_stage(state, lock)
    state["authorities"] = {
        k: "PASS_FOR_PILOT" if k == "MARKET_RULE" else "PASS" for k in AUTHORITIES
    }
    assert next_stage(state, lock) == "R2"
    state["current_stage"] = "R2"
    assert next_stage(state, lock) == "R2"
    state["pilot_dataset_created"] = True
    assert next_stage(state, lock) == "R3"
    state["current_stage"] = "R3"
    state["dataset_audited"] = True
    with pytest.raises(ValueError, match="AUDIT_READINESS"):
        next_stage(state, lock)
    state["pilot_data_readiness"] = "READY"
    assert next_stage(state, lock) == "GATE_A"
    state["status"] = "AWAITING_HUMAN"
    assert next_stage(state, lock) == "STOP"
    state["current_stage"] = "R4"
    with pytest.raises(ValueError, match="FUTURE_STAGE"):
        next_stage(state, lock)
    state["current_stage"] = "R1"
    with pytest.raises(ValueError, match="OOS_OUTSIDE"):
        next_stage(state, {"oos_authorized": True})
    state["dataset_frozen"] = "false"
    with pytest.raises(ValueError, match="INVALID_STATE_FLAG"):
        next_stage(state, lock)
