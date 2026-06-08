import json
import sys


def build_approval_preview(risk_context, approval_context):
    risk_flags = []
    if not approval_context.get("approval_code"):
        risk_flags.append("missing_approval_code")
    if not approval_context.get("applicant_open_id"):
        risk_flags.append("missing_applicant_open_id")

    return {
        "risk_gate_summary": {
            "risk_level": risk_context.get("risk_level", ""),
            "trigger_reason": risk_context.get("trigger_reason", ""),
            "risk_scope": risk_context.get("task_scope", ""),
            "recommended_action": risk_context.get("recommended_option", ""),
            "requires_approval": risk_context.get("risk_level") == "high",
        },
        "approval_request_candidate": {
            "approval_code": approval_context.get("approval_code", ""),
            "applicant_open_id": approval_context.get("applicant_open_id", ""),
            "instance_external_id": approval_context.get("instance_external_id", ""),
            "form_payload": approval_context.get("form_payload", []),
            "source_refs": approval_context.get("source_refs", []),
            "target_object_id": approval_context.get("target_object_id", ""),
        },
        "status_projection_candidate": {
            "approval_status": "pending",
            "approval_decision_id": risk_context.get("task_id", ""),
            "decision_summary": "approval_created",
            "automation_status": "paused",
        },
        "risk_flags": risk_flags,
        "timeout_policy": risk_context.get("timeout_fallback", {}),
        "requires_confirmation": True,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_approval_preview(payload["risk_context"], payload["approval_context"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
