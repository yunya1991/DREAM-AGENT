import json
import sys


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


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


def build_goal_record(goal, tasks):
    return {
        "goal_id": goal.get("goal_id", ""),
        "goal_name": goal.get("goal_name", ""),
        "goal_owner": goal.get("goal_owner", ""),
        "goal_status": compute_goal_status(tasks),
        "goal_progress": compute_goal_progress(tasks),
        "current_phase": goal.get("current_phase", ""),
        "key_blocker": first_non_empty(tasks, "blocker"),
        "next_milestone": goal.get("next_milestone", ""),
        "risk_level": choose_risk(tasks),
        "latest_decision_summary": first_non_empty(tasks, "decision_summary"),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_goal_record(payload.get("goal", {}), payload.get("tasks", [])),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
