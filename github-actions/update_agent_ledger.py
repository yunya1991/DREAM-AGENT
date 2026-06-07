from datetime import datetime, timezone


def quality_multiplier(score):
    if score >= 90:
        return 1.2
    if score >= 80:
        return 1.0
    return 0.0


def calculate_reward(base_reward, score):
    multiplier = quality_multiplier(score)
    return {
        "quality_multiplier": multiplier,
        "final_reward": int(base_reward * multiplier),
    }


def utc_now():
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def append_reward_record(reward_index, record):
    reward_index["generated_at"] = utc_now()
    reward_index["reward_records"].append(record)
    return reward_index


GOVERNANCE_ALLOWED_TRANSITIONS = {
    "accepted": {"ledgered"},
    "ledgered": {"archived"},
    "archived": {"knowledge_synced"},
}


def build_governance_closure(
    archive_summary,
    index_updates,
    faq_decision,
    faq_entries,
    closure_agent,
):
    return {
        "archive_summary": archive_summary,
        "index_updates": list(index_updates),
        "faq_decision": faq_decision,
        "faq_entries": list(faq_entries),
        "closure_agent": closure_agent,
        "closure_completed_at": utc_now(),
    }


def normalize_version_anchor(anchor):
    anchor = anchor or {}
    return {
        "git_commit_before": anchor.get("git_commit_before", ""),
        "git_branch_or_pr_ref": anchor.get("git_branch_or_pr_ref", ""),
        "workflow_run_id": anchor.get("workflow_run_id", ""),
        "acceptance_request_id": anchor.get("acceptance_request_id", ""),
        "feishu_asset_before_snapshot": anchor.get("feishu_asset_before_snapshot", ""),
    }


def apply_status_transition(task, requested_status):
    task["version_anchor"] = normalize_version_anchor(task.get("version_anchor"))
    current_status = task.get("status")
    if current_status == requested_status:
        return task, {
            "previous_status": current_status,
            "new_status": requested_status,
            "state_changed": False,
            "knowledge_sync_written": False,
        }

    allowed_statuses = GOVERNANCE_ALLOWED_TRANSITIONS.get(current_status)
    if allowed_statuses is not None and requested_status not in allowed_statuses:
        raise ValueError(
            f"invalid governance transition: {current_status} -> {requested_status}"
        )

    knowledge_sync_written = False
    if requested_status == "knowledge_synced":
        closure = task.get("governance_closure", {})
        required_fields = {
            "archive_summary": "archive_summary required",
            "index_updates": "index_updates required",
            "faq_decision": "faq_decision required",
            "closure_agent": "closure_agent required",
        }
        for field, error_message in required_fields.items():
            if not closure.get(field):
                raise ValueError(error_message)
        task["knowledge_synced_at"] = utc_now()
        knowledge_sync_written = True

    if requested_status == "archived":
        task["archived_at"] = utc_now()

    task["status"] = requested_status
    return task, {
        "previous_status": current_status,
        "new_status": requested_status,
        "state_changed": True,
        "knowledge_sync_written": knowledge_sync_written,
    }
