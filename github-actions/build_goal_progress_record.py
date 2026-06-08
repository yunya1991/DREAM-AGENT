import json
import sys


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
STATUS_TO_CN = {
    "planned": "待开始",
    "active": "推进中",
    "blocked": "已阻塞",
    "waiting_decision": "等待决策",
    "ready_for_release": "待发布",
    "released": "已发布",
}


def choose_risk(tasks):
    max_name = "low"
    for task in tasks:
        candidate = task.get("risk_level", "low")
        if task.get("approval_status") in {"pending", "timeout"}:
            candidate = "high"
        if RISK_ORDER.get(candidate, 0) > RISK_ORDER.get(max_name, 0):
            max_name = candidate
    return max_name


def compute_goal_status(tasks):
    if any(task.get("approval_status") in {"pending", "timeout"} for task in tasks):
        return "waiting_decision"
    if any(task.get("platform_status") == "checks_failing" for task in tasks):
        return "blocked"
    if any(task.get("governance_status") == "blocked" for task in tasks):
        return "blocked"
    if tasks and all(task.get("governance_status") == "released" for task in tasks):
        return "released"
    return "active"


def compute_goal_progress(tasks):
    if not tasks:
        return 0
    completed = sum(1 for task in tasks if task.get("governance_status") in {"ready", "released"})
    return int(completed * 100 / len(tasks))


def first_non_empty(tasks, key):
    for task in tasks:
        value = task.get(key, "")
        if value:
            return value
    return ""


def to_boss_status(status):
    return STATUS_TO_CN.get(status, status or "待开始")


def compute_okr_alignment(goal, goal_status):
    if goal.get("okr_sync_status") in {"error", "failed"}:
        return "对齐异常"
    if goal.get("okr_objective_id"):
        return "已对齐"
    if goal_status in {"active", "blocked", "waiting_decision"}:
        return "待补OKR"
    return "待同步"


def compute_workflow_signal(tasks, okr_alignment):
    if any(task.get("approval_status") in {"pending", "timeout"} for task in tasks):
        return "approval_waiting"
    if okr_alignment != "已对齐":
        return "missing_okr_alignment"
    if any(task.get("risk_level") == "high" and task.get("blocker") for task in tasks):
        return "risk_blocked"
    return "healthy"


def build_goal_record(goal, tasks):
    goal_status = compute_goal_status(tasks)
    blocker = first_non_empty(tasks, "blocker")
    decision_summary = first_non_empty(tasks, "decision_summary")
    risk = choose_risk(tasks)
    okr_alignment = compute_okr_alignment(goal, goal_status)
    next_action = goal.get("next_action") or goal.get("next_milestone", "")
    return {
        "goal_id": goal.get("goal_id", ""),
        "goal_name": goal.get("goal_name", ""),
        "goal_owner": goal.get("goal_owner", ""),
        "goal_status": goal_status,
        "goal_progress": compute_goal_progress(tasks),
        "current_phase": goal.get("current_phase", ""),
        "key_blocker": blocker,
        "next_milestone": goal.get("next_milestone", ""),
        "risk_level": risk,
        "latest_decision_summary": decision_summary,
        "目标名称": goal.get("goal_name", ""),
        "当前状态": to_boss_status(goal_status),
        "当前阻塞": blocker,
        "风险等级": risk,
        "下一步动作": next_action,
        "最近决策摘要": decision_summary,
        "OKR对齐": okr_alignment,
        "okr_objective_id": goal.get("okr_objective_id", ""),
        "okr_objective_title": goal.get("okr_objective_title", ""),
        "okr_owner": goal.get("okr_owner", ""),
        "okr_sync_status": goal.get("okr_sync_status", ""),
        "okr_last_sync_at": goal.get("okr_last_sync_at", ""),
        "workflow_signal": compute_workflow_signal(tasks, okr_alignment),
        "last_workflow_run_at": goal.get("last_workflow_run_at", ""),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_goal_record(payload.get("goal", {}), payload.get("tasks", [])),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
