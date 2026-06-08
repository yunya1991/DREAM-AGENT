import json
import sys


WRITEBACK_ORDER = [
    "field_governance_check",
    "task_writeback",
    "progress_writeback",
    "goal_projection_writeback",
    "view_validation",
]


def materialize_bitable_execution(preview):
    missing_fields = preview["field_governance_report"].get("missing_fields", [])
    view_candidates = preview.get("view_projection_candidates", [])
    status = "ready"
    if missing_fields:
        status = "hard_block"
    elif not view_candidates:
        status = "degraded_success"

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "tasks": {"items": preview["task_record_candidates"]},
        "progress": {"items": preview["progress_record_candidates"]},
        "goal_projection": {"items": preview["goal_projection_candidates"]},
        "view_validation": {"items": view_candidates},
        "knowledge_update": {
            "asset_type": "delivery",
            "title": "bitable-writeback-result",
            "summary": f"status={status}",
            "evidence_refs": [item["task_id"] for item in preview["task_record_candidates"]],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_bitable_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
