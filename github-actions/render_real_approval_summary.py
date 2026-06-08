import json
import os
import sys
from pathlib import Path


def build_summary_markdown(dispatch_result, query_result):
    lines = [
        "# Real Approval Trigger",
        "",
        f"- Approval Code: `{dispatch_result.get('approval_code', '')}`",
        f"- Task ID: `{dispatch_result.get('task_id', '')}`",
        f"- Goal ID: `{dispatch_result.get('goal_id', '')}`",
        f"- Approval Instance Code: `{query_result.get('approval_instance_code', dispatch_result.get('approval_instance_code', ''))}`",
        f"- Approval Status: `{query_result.get('approval_status', dispatch_result.get('approval_status', ''))}`",
        f"- Automation Status: `{query_result.get('automation_status', dispatch_result.get('automation_status', ''))}`",
        f"- Decision Summary: `{query_result.get('decision_summary', dispatch_result.get('decision_summary', ''))}`",
        "",
    ]
    return "\n".join(lines)


def workflow_exit_code(dispatch_result, query_result):
    return 0 if dispatch_result.get("approval_instance_code") and query_result.get("approval_status") else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    dispatch_path = Path(argv[0])
    query_path = Path(argv[1])
    dispatch_result = json.loads(dispatch_path.read_text(encoding="utf-8"))
    query_result = json.loads(query_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(dispatch_result, query_result)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")
    else:
        sys.stdout.write(summary + "\n")
    raise SystemExit(workflow_exit_code(dispatch_result, query_result))


if __name__ == "__main__":
    main()
