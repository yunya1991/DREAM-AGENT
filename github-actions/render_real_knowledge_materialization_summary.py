import json
import os
import sys
from pathlib import Path


def build_summary_markdown(result):
    source_refs = result.get("source_refs", {})
    runbook = result.get("runbook", {})
    handoff = result.get("handoff", {})
    lines = [
        "# Real Knowledge Materialization",
        "",
        f"- Task ID: `{source_refs.get('task_id', '')}`",
        f"- Goal ID: `{source_refs.get('goal_id', '')}`",
        f"- Approval Instance Code: `{source_refs.get('approval_instance_code', '')}`",
        f"- Runbook Path: `{runbook.get('target_path', '')}`",
        f"- Handoff Path: `{handoff.get('target_path', '')}`",
        f"- Materialization Status: `{result.get('materialization_status', '')}`",
        f"- Index Update Status: `{result.get('index_update_status', '')}`",
        f"- Failure Reason: `{result.get('failure_reason', '')}`",
        "",
    ]
    return "\n".join(lines)


def workflow_exit_code(result):
    return 0 if (
        result.get("materialization_status") == "success"
        and result.get("index_update_status") == "success"
    ) else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    result_path = Path(argv[0])
    result = json.loads(result_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(result)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")
    else:
        sys.stdout.write(summary + "\n")
    raise SystemExit(workflow_exit_code(result))


if __name__ == "__main__":
    main()
