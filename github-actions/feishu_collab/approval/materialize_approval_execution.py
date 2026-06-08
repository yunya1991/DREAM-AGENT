import json
import sys


WRITEBACK_ORDER = [
    "risk_gate_check",
    "approval_request_writeback",
    "approval_status_projection",
    "automation_status_projection",
    "approval_evidence_snapshot",
]


def materialize_approval_execution(preview):
    status = "confirmed"
    risk_flags = preview.get("risk_flags", [])
    if "missing_approval_code" in risk_flags or "missing_applicant_open_id" in risk_flags:
        status = "hard_block"
    elif "instance_lookup_failed" in risk_flags or "approval_scope_conflict" in risk_flags:
        status = "soft_block"

    evidence_refs = [
        preview["approval_request_candidate"].get("instance_external_id", ""),
        preview["approval_request_candidate"].get("approval_code", ""),
    ]

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "approval_request": preview["approval_request_candidate"],
        "status_projection": preview["status_projection_candidate"],
        "timeout_policy": preview["timeout_policy"],
        "knowledge_update": {
            "asset_type": "operations",
            "title": "approval-execution-result",
            "summary": f"status={status}",
            "evidence_refs": [item for item in evidence_refs if item],
        },
        "handoff": {
            "type": "stage_handoff",
            "status": status,
            "summary": f"approval execution {status}",
            "next_action": "review approval verification result",
            "evidence_refs": [item for item in evidence_refs if item],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_approval_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
