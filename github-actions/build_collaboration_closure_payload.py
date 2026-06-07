import json
import sys


def build_payload(raw):
    return {
        "task_id": raw.get("task_id", ""),
        "pr_number": raw.get("pr_number", ""),
        "repo": raw.get("repo", ""),
        "branch": raw.get("branch", ""),
        "implementation_status": raw.get("implementation_status", "planned"),
        "platform_status": raw.get("platform_status", "no_pr"),
        "governance_status": raw.get("governance_status", "draft"),
        "automation_status": raw.get("automation_status", "idle"),
        "workflow_run_id": raw.get("workflow_run_id", ""),
        "last_comment_anchor": raw.get("last_comment_anchor", ""),
        "blocker": raw.get("blocker", ""),
        "next_action": raw.get("next_action", ""),
    }


if __name__ == "__main__":
    json.dump(build_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
