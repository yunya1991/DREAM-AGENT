import json
import os
from pathlib import Path
import sys


def build_summary_markdown(report):
    scenario_id = report["scenario_manifest"]["scenario_id"]
    system_status = report["system_status"]
    verification = report["verification_summary"]

    lines = [
        "# Five Skill Rehearsal",
        "",
        f"- Scenario: `{scenario_id}`",
        f"- System Status: `{system_status}`",
        f"- Step Count: `{verification['step_count']}`",
        f"- Breakpoint Count: `{verification['breakpoint_count']}`",
        "",
        "| Skill | Raw Verification | System |",
        "| --- | --- | --- |",
    ]

    for step in report.get("step_results", []):
        lines.append(
            f"| {step['skill_name']} | "
            f"{step['verification'].get('status', '')} | "
            f"{step['normalized'].get('system_status', '')} |"
        )

    breakpoints = report.get("breakpoints", [])
    if breakpoints:
        lines.extend(["", "## Breakpoints", ""])
        for item in breakpoints:
            lines.append(
                f"- `{item['skill_name']}` / `{item['breakpoint_type']}`: {item['recovery_hint']}"
            )

    return "\n".join(lines) + "\n"


def workflow_exit_code(report):
    return 0 if report.get("system_status") == "pass" else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    report_path = Path(argv[0])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write(summary)
    else:
        sys.stdout.write(summary)

    raise SystemExit(workflow_exit_code(report))


if __name__ == "__main__":
    main()
