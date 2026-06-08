import json
import sys


def _normalize_event(event_payload):
    event_name = event_payload.get("event_name", "")
    action = event_payload.get("action", "")
    repository = event_payload.get("repository", {})
    sender = event_payload.get("sender", {})

    if event_name == "issues":
        issue = event_payload.get("issue", {})
        return {
            "event_type": "github.issue.changed",
            "object_type": "issue",
            "number": str(issue.get("number", "")),
            "title": issue.get("title", ""),
            "repo": repository.get("full_name", ""),
            "action": action,
            "sender": sender.get("login", ""),
            "branch": "",
            "sha": "",
            "workflow_run_id": "",
            "check_conclusion": "",
        }

    if event_name == "pull_request":
        pull_request = event_payload.get("pull_request", {})
        workflow_run = event_payload.get("workflow_run", {})
        head = pull_request.get("head", {})
        return {
            "event_type": "github.pr.changed",
            "object_type": "pull_request",
            "number": str(pull_request.get("number", "")),
            "title": pull_request.get("title", ""),
            "repo": repository.get("full_name", ""),
            "action": action,
            "sender": sender.get("login", ""),
            "branch": head.get("ref", ""),
            "sha": head.get("sha", ""),
            "workflow_run_id": str(workflow_run.get("id", "")),
            "check_conclusion": "",
        }

    check_run = event_payload.get("check_run", {})
    return {
        "event_type": "github.check.changed",
        "object_type": "check_run",
        "number": "",
        "title": check_run.get("name", ""),
        "repo": repository.get("full_name", ""),
        "action": action,
        "sender": sender.get("login", ""),
        "branch": "",
        "sha": check_run.get("head_sha", ""),
        "workflow_run_id": "",
        "check_conclusion": check_run.get("conclusion", ""),
    }


def _field_updates(normalized_event, collab_context):
    field_updates = {
        "任务ID": collab_context.get("task_id", ""),
        "任务名称": collab_context.get("task_name", ""),
        "目标ID": collab_context.get("goal_id", ""),
        "仓库": normalized_event["repo"] or collab_context.get("repo", ""),
        "分支": normalized_event["branch"] or collab_context.get("branch", ""),
        "PR号": collab_context.get("pr_number", ""),
        "Workflow运行ID": normalized_event["workflow_run_id"] or collab_context.get("workflow_run_id", ""),
        "实现状态": collab_context.get("implementation_status", ""),
        "平台状态": collab_context.get("platform_status", ""),
        "治理状态": collab_context.get("governance_status", ""),
        "自动化状态": collab_context.get("automation_status", ""),
        "风险等级": collab_context.get("risk_level", "low"),
        "审批状态": collab_context.get("approval_status", "not_required"),
        "审批决策ID": collab_context.get("approval_decision_id", ""),
        "审批截止时间": collab_context.get("approval_due_at", ""),
        "决策摘要": collab_context.get("decision_summary", ""),
        "最近评论锚点": collab_context.get("last_comment_anchor", ""),
        "最近提交": normalized_event["sha"] or collab_context.get("last_commit", ""),
        "当前阻塞": collab_context.get("blocker", ""),
        "下一步建议": collab_context.get("next_action", ""),
        "远程动作": collab_context.get("remote_action", "none"),
        "远程动作结果": collab_context.get("remote_action_result", ""),
    }

    if normalized_event["event_type"] == "github.pr.changed":
        field_updates["平台状态"] = "checks_pending"
        field_updates["自动化状态"] = "running"
    elif normalized_event["event_type"] == "github.issue.changed":
        field_updates["治理状态"] = "triage_required"
    elif normalized_event["event_type"] == "github.check.changed":
        conclusion = normalized_event["check_conclusion"]
        field_updates["平台状态"] = "checks_passed" if conclusion == "success" else "checks_failed"
        field_updates["自动化状态"] = "completed"

    return field_updates


def build_github_sync_preview(event_payload, collab_context):
    normalized_event = _normalize_event(event_payload)
    risk_flags = []
    fallback_policy = "confirmed"

    if not collab_context.get("goal_id"):
        risk_flags.append("missing_goal_link")
    if not collab_context.get("task_id"):
        risk_flags.append("missing_task_link")

    if normalized_event["event_type"] == "github.check.changed":
        conclusion = normalized_event["check_conclusion"]
        if conclusion not in {"success", "failure", "cancelled", ""}:
            risk_flags.append("unknown_check_state")
            fallback_policy = "soft_block"

    return {
        "event_summary": {
            "event_type": normalized_event["event_type"],
            "object_type": normalized_event["object_type"],
            "repo": normalized_event["repo"],
            "number": normalized_event["number"],
            "action": normalized_event["action"],
            "title": normalized_event["title"],
        },
        "impacted_records": [
            {
                "task_id": collab_context.get("task_id", ""),
                "goal_id": collab_context.get("goal_id", ""),
                "repo": normalized_event["repo"],
            }
        ],
        "field_updates": _field_updates(normalized_event, collab_context),
        "risk_flags": risk_flags,
        "event_coverage_hit": {
            "event_type": normalized_event["event_type"],
            "action": normalized_event["action"],
            "fallback_policy": fallback_policy,
        },
        "writeback_plan": [
            "event_coverage_check",
            "collab_state_writeback",
            "automation_result_writeback",
            "comment_anchor_writeback",
            "verification_snapshot",
        ],
        "requires_confirmation": True,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_github_sync_preview(payload["event_payload"], payload["collab_context"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
