import json
import sys


def verify_approval_projection(status_projection, timeout_policy, evidence_snapshot, risk_flags):
    if not status_projection.get("approval_status"):
        status = "hard_block"
    elif "status_projection_gap" in risk_flags:
        status = "soft_block"
    elif not evidence_snapshot.get("instance_code"):
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "approval_status": status_projection.get("approval_status", ""),
        "automation_status": status_projection.get("automation_status", ""),
        "timeout_action": timeout_policy.get("action", ""),
        "instance_code_present": bool(evidence_snapshot.get("instance_code")),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_approval_projection(
            payload["status_projection"],
            payload["timeout_policy"],
            payload["evidence_snapshot"],
            payload["risk_flags"],
        ),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
