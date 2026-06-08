def _doc_slug(task_id, suffix):
    return f"approval-{task_id.lower()}-{suffix}.md"


def build_real_knowledge_payload(
    approval_status_result,
    approval_writeback_result,
    materialization_context,
):
    task_id = approval_writeback_result.get("task_id", "").strip()
    goal_id = approval_writeback_result.get("goal_id", "").strip()
    instance_code = approval_status_result.get("approval_instance_code", "").strip()

    return {
        "source_refs": {
            "approval_instance_code": instance_code,
            "task_id": task_id,
            "goal_id": goal_id,
        },
        "runbook": {
            "title": f"Approval {task_id} Runbook",
            "target_path": f"docs/feishu-collab/runbooks/{_doc_slug(task_id, 'runbook')}",
            "index_path": "docs/feishu-collab/RUNBOOK_INDEX.md",
            "content_context": {
                "approval_status_result": approval_status_result,
                "approval_writeback_result": approval_writeback_result,
                "materialization_context": materialization_context,
            },
        },
        "handoff": {
            "title": f"Approval {task_id} Handoff",
            "target_path": f"docs/feishu-collab/handoffs/{_doc_slug(task_id, 'handoff')}",
            "index_path": "docs/feishu-collab/HANDOFF_INDEX.md",
            "content_context": {
                "approval_status_result": approval_status_result,
                "approval_writeback_result": approval_writeback_result,
                "materialization_context": materialization_context,
            },
        },
    }
