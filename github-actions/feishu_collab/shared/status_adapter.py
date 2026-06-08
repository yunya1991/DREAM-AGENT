STATUS_MAP = {
    "confirmed": "pass",
    "degraded_success": "warn",
    "soft_block": "fail",
    "hard_block": "blocked",
    "blocked": "blocked",
}

POLICY_FLAGS = {
    "missing_approval_code",
    "missing_applicant_open_id",
    "unknown_asset_type",
}
CONTRACT_FLAGS = {
    "status_projection_gap",
    "event_coverage_gap",
    "missing_goal_link",
    "missing_task_link",
}
DATA_FLAGS = {"empty_title", "missing_evidence_refs", "task_goal_unlinked"}


def _breakpoint_type(raw_status, risk_flags):
    flags = set(risk_flags or [])
    if flags & POLICY_FLAGS:
        return "policy_gap"
    if flags & DATA_FLAGS:
        return "data_gap"
    if flags & CONTRACT_FLAGS:
        return "contract_gap"
    if raw_status == "degraded_success":
        return "execution_gap"
    if raw_status in {"soft_block", "hard_block", "blocked"}:
        return "execution_gap"
    if raw_status not in STATUS_MAP:
        return "contract_gap"
    return ""


def _recovery_hint(skill_name, system_status, breakpoint_type):
    if system_status == "pass":
        return "continue to next skill"
    if breakpoint_type == "policy_gap":
        return f"fix governance inputs before rerunning {skill_name}"
    if breakpoint_type == "data_gap":
        return f"repair missing scenario data before rerunning {skill_name}"
    if breakpoint_type == "contract_gap":
        return f"align upstream or downstream contracts before rerunning {skill_name}"
    return f"review {skill_name} execution evidence and rerun the rehearsal"


def normalize_skill_result(skill_name, raw_status, risk_flags=None, verification=None):
    system_status = STATUS_MAP.get(raw_status, "fail")
    breakpoint_type = _breakpoint_type(raw_status, risk_flags)
    return {
        "skill_name": skill_name,
        "raw_status": raw_status,
        "system_status": system_status,
        "breakpoint_type": breakpoint_type,
        "risk_flags": list(risk_flags or []),
        "verification": verification or {},
        "recovery_hint": _recovery_hint(skill_name, system_status, breakpoint_type),
    }
