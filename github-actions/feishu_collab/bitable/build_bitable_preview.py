import json
import sys


def _build_task_records(okr_preview):
    tasks = []
    goal = okr_preview["goal_record_candidates"][0]
    for item in okr_preview.get("task_candidates", []):
        tasks.append(
            {
                "task_id": item["task_id"],
                "goal_ref": goal["goal_id"],
                "objective_ref": goal.get("okr_objective_id", ""),
                "kr_ref": item.get("kr_ref", ""),
                "title": item["title"],
                "owner": item.get("owner", "governance-agent"),
                "status": item.get("status", "planned"),
                "risk_level": "medium",
                "blocker": "",
                "next_action": item.get("deliverable", ""),
                "deliverable": item.get("deliverable", ""),
                "source_refs": [item["task_id"]],
            }
        )
    return tasks


def _build_progress_records(task_records):
    return [
        {
            "goal_id": task["goal_ref"],
            "task_ref": task["task_id"],
            "progress_status": task["status"],
            "governance_status": "planned",
            "approval_status": "not_required",
            "risk_level": task["risk_level"],
            "blocker": task["blocker"],
            "decision_summary": "",
            "last_sync_at": "",
        }
        for task in task_records
    ]


def build_bitable_preview(okr_preview, base_context):
    goal = okr_preview["goal_record_candidates"][0]
    task_records = _build_task_records(okr_preview)
    progress_records = _build_progress_records(task_records)

    missing_fields = [
        field
        for field in base_context.get("required_fields", [])
        if field not in base_context.get("existing_fields", [])
    ]
    drift_flags = []
    if missing_fields:
        drift_flags.append("missing_required_fields")
    if not task_records:
        drift_flags.append("task_goal_unlinked")
    if not base_context.get("views"):
        drift_flags.append("view_projection_incomplete")

    return {
        "task_record_candidates": task_records,
        "progress_record_candidates": progress_records,
        "goal_projection_candidates": [
            {
                "goal_id": goal["goal_id"],
                "goal_name": goal["goal_name"],
                "okr_objective_id": goal.get("okr_objective_id", ""),
                "okr_objective_title": goal.get("okr_objective_title", ""),
                "okr_owner": goal.get("okr_owner", ""),
                "okr_sync_status": goal.get("okr_sync_status", ""),
                "goal_status": "active",
                "goal_progress": 0,
                "workflow_signal": "healthy",
                "key_blocker": "",
                "next_milestone": "",
                "next_action": "",
            }
        ],
        "field_governance_report": {
            "required_fields": base_context.get("required_fields", []),
            "missing_fields": missing_fields,
            "stale_fields": [],
            "field_mapping": {
                "任务标题": "title",
                "任务负责人": "owner",
                "当前状态": "progress_status",
            },
            "writeback_scope": ["tasks", "progress", "goal_projection"],
        },
        "view_projection_candidates": [
            {
                "view_name": view["view_name"],
                "view_type": "table",
                "required_columns": view.get("required_columns", []),
                "sort_keys": ["风险等级"],
                "filter_rules": [],
                "projection_fields": view.get("required_columns", []),
                "consumer_role": "manager",
            }
            for view in base_context.get("views", [])
        ],
        "drift_flags": drift_flags,
        "requires_confirmation": True,
        "writeback_order": [
            "field_governance_check",
            "task_writeback",
            "progress_writeback",
            "goal_projection_writeback",
            "view_validation",
        ],
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_bitable_preview(payload["okr_preview"], payload["base_context"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
