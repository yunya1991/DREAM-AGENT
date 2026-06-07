import json
import sys


HIGH_RISK_SCOPES = {
    "multi_agent_expansion",
    "release_handoff",
    "rollback",
    "high_cost_retry",
    "goal_switch",
}


def build_default_options(task):
    return [
        {
            "key": "recommended",
            "label": "按推荐方案继续",
            "risk": task.get("risk_level", "low"),
            "rollback": "use existing version anchor",
        },
        {
            "key": "pause",
            "label": "暂停并等待人工接手",
            "risk": "low",
            "rollback": "no-op",
        },
    ]


def evaluate_gate(task):
    change_scope = task.get("change_scope", "")
    risk_level = task.get("risk_level", "low")
    requires_approval = risk_level in {"high", "critical"} or change_scope in HIGH_RISK_SCOPES
    if not requires_approval:
        return {
            "requires_approval": False,
            "approval_status": "not_required",
            "trigger_reason": "",
            "recommended_option": "auto_continue",
            "options": [],
            "timeout_fallback": {"action": "auto_continue"},
        }

    return {
        "requires_approval": True,
        "approval_status": "pending",
        "trigger_reason": change_scope or "high_risk_change",
        "recommended_option": "recommended",
        "options": build_default_options(task),
        "timeout_fallback": {"action": "pause"},
    }


if __name__ == "__main__":
    json.dump(evaluate_gate(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
