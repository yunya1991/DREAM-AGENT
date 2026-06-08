import json
import sys


WRITEBACK_ORDER = [
    "event_coverage_check",
    "collab_state_writeback",
    "automation_result_writeback",
    "comment_anchor_writeback",
    "verification_snapshot",
]


def materialize_github_sync_execution(preview):
    status = "confirmed"
    if "event_coverage_gap" in preview.get("risk_flags", []):
        status = "soft_block"
    elif not preview.get("field_updates", {}).get("最近评论锚点"):
        status = "degraded_success"

    evidence_refs = [
        preview["event_summary"].get("repo", ""),
        preview["event_summary"].get("number", ""),
    ]

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "collab_state": {"fields": preview["field_updates"]},
        "event_summary": preview["event_summary"],
        "verification_seed": {
            "coverage_hit": preview["event_coverage_hit"],
            "risk_flags": preview["risk_flags"],
        },
        "knowledge_update": {
            "asset_type": "delivery",
            "title": "github-sync-writeback-result",
            "summary": f"status={status}",
            "evidence_refs": [item for item in evidence_refs if item],
        },
        "handoff": {
            "type": "stage_handoff",
            "status": status,
            "summary": f"github sync execution {status}",
            "next_action": "review verification result",
            "evidence_refs": [item for item in evidence_refs if item],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_github_sync_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
