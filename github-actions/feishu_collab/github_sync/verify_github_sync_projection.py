import json
import sys


def verify_github_sync_projection(record_fields, coverage_hit, risk_flags, comment_anchor, automation_summary):
    if not record_fields.get("任务ID"):
        status = "hard_block"
    elif "event_coverage_gap" in risk_flags:
        status = "soft_block"
    elif not comment_anchor:
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "event_type": coverage_hit.get("event_type", ""),
        "action": coverage_hit.get("action", ""),
        "task_id": record_fields.get("任务ID", ""),
        "automation_status": automation_summary.get("status", ""),
        "comment_anchor_present": bool(comment_anchor),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_github_sync_projection(
            payload["record_fields"],
            payload["coverage_hit"],
            payload["risk_flags"],
            payload["comment_anchor"],
            payload["automation_summary"],
        ),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
