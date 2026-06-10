import json
import sys


def normalize_task_status(payload):
    if payload.get("approval_status") in {"rejected", "timeout"}:
        return "blocked"
    if payload.get("automation_status") == "blocked":
        return "blocked"
    if payload.get("blocker"):
        return "blocked"
    if payload.get("governance_status") == "released":
        return "done"
    if payload.get("pr_number") or payload.get("pr_url") or payload.get("automation_status") in {
        "running",
        "proceed",
        "completed",
    }:
        return "in_progress"
    return "backlog"


def build_module_task_record(payload):
    record = {
        "task_id": payload.get("task_id", ""),
        "goal_id": payload.get("goal_id", ""),
        "status": normalize_task_status(payload),
        "pr_number": payload.get("pr_number", ""),
        "pr_url": payload.get("pr_url", ""),
        "comment_anchor": payload.get("last_comment_anchor", ""),
        "blocker": payload.get("blocker", ""),
        "next_action": payload.get("next_action", ""),
        "owner_agent": payload.get("owner_agent", ""),
    }
    if payload.get("task_name"):
        record["任务"] = payload["task_name"]
    if payload.get("repo"):
        record["repo"] = payload["repo"]
    return record


def build_monitor_record(payload):
    return {
        "任务ID": payload.get("task_id", ""),
        "任务名称": payload.get("task_name", ""),
        "目标ID": payload.get("goal_id", ""),
        "仓库": payload.get("repo", ""),
        "分支": payload.get("branch", ""),
        "PR号": payload.get("pr_number", ""),
        "Workflow运行ID": payload.get("workflow_run_id", ""),
        "实现状态": payload.get("implementation_status", ""),
        "平台状态": payload.get("platform_status", ""),
        "治理状态": payload.get("governance_status", ""),
        "自动化状态": payload.get("automation_status", ""),
        "风险等级": payload.get("risk_level", "low"),
        "审批状态": payload.get("approval_status", "not_required"),
        "审批决策ID": payload.get("approval_decision_id", ""),
        "审批截止时间": payload.get("approval_due_at", ""),
        "决策摘要": payload.get("decision_summary", ""),
        "最近评论锚点": payload.get("last_comment_anchor", ""),
        "最近提交": payload.get("last_commit", ""),
        "当前阻塞": payload.get("blocker", ""),
        "下一步建议": payload.get("next_action", ""),
        "远程动作": payload.get("remote_action", "none"),
        "远程动作结果": payload.get("remote_action_result", ""),
    }


def build_feishu_record(payload):
    return build_monitor_record(payload)


def project_github_collab_state(payload):
    return build_monitor_record(payload)


if __name__ == "__main__":
    json.dump(build_monitor_record(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
