import json
import os
import sys
from pathlib import Path


def build_summary_markdown(status_result, writeback_result):
    lines = [
        "# Approval Polling Writeback",
        "",
        f"- Approval Instance Code: `{status_result.get('approval_instance_code', '')}`",
        f"- Approval Status: `{status_result.get('approval_status', '')}`",
        f"- Automation Status: `{status_result.get('automation_status', '')}`",
        f"- Task ID: `{writeback_result.get('task_id', '')}`",
        f"- Goal ID: `{writeback_result.get('goal_id', '')}`",
        f"- Task Writeback: `{writeback_result.get('task_writeback_status', '')}`",
        f"- Goal Writeback: `{writeback_result.get('goal_writeback_status', '')}`",
        f"- Decision Summary: `{status_result.get('decision_summary', '')}`",
        "",
    ]
    return "\n".join(lines)


def workflow_exit_code(status_result, writeback_result):
    return 0 if (
        status_result.get("approval_status")
        and writeback_result.get("task_writeback_status") == "success"
        and writeback_result.get("goal_writeback_status") == "success"
    ) else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    status_path = Path(argv[0])
    writeback_path = Path(argv[1])
    status_result = json.loads(status_path.read_text(encoding="utf-8"))
    writeback_result = json.loads(writeback_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(status_result, writeback_result)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")
    else:
        sys.stdout.write(summary + "\n")
    raise SystemExit(workflow_exit_code(status_result, writeback_result))


if __name__ == "__main__":
    main()
