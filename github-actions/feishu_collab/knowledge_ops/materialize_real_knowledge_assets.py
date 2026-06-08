from pathlib import Path


RUNBOOK_TEMPLATE = """# {title}

## Trigger

- Approval Instance Code: `{approval_instance_code}`

## Scope

- Task ID: `{task_id}`
- Goal ID: `{goal_id}`

## Preconditions

- Approval Status: `{approval_status}`
- Automation Status: `{automation_status}`

## Detection

- Decision Summary: `{decision_summary}`

## Investigation Steps

- Review approval artifact and writeback artifact.

## Recovery Steps

- Continue from the current approval and Base writeback state.

## Verification

- Task Writeback: `{task_writeback_status}`
- Goal Writeback: `{goal_writeback_status}`

## Escalation

- Escalate if status and Base writeback drift again.

## Evidence To Capture

- Approval Instance Code: `{approval_instance_code}`
- Task ID: `{task_id}`
- Goal ID: `{goal_id}`

## Follow-up Knowledge Update

- Sync handoff after state changes.
"""


HANDOFF_TEMPLATE = """# {title}

## Background

- Approval Instance Code: `{approval_instance_code}`

## Current State

- Approval Status: `{approval_status}`
- Automation Status: `{automation_status}`

## Completed Work

- Task Writeback: `{task_writeback_status}`
- Goal Writeback: `{goal_writeback_status}`

## Remaining Work

- Continue approval follow-up until final decision lands.

## Active Blocker

- Pending approval decision.

## Next Action

- Review the latest approval result and rerun writeback if state changes.

## Dependencies

- Task ID: `{task_id}`
- Goal ID: `{goal_id}`

## Risk Notes

- Keep knowledge documents aligned with approval state.

## Evidence Links

- Decision Summary: `{decision_summary}`

## Handover Focus

- Preserve approval state, Base state, and rerun path.
"""


def _render_context(source_refs, approval_status_result, approval_writeback_result, title):
    return {
        "title": title,
        "approval_instance_code": source_refs.get("approval_instance_code", ""),
        "task_id": approval_writeback_result.get("task_id", source_refs.get("task_id", "")),
        "goal_id": approval_writeback_result.get("goal_id", source_refs.get("goal_id", "")),
        "approval_status": approval_status_result.get("approval_status", ""),
        "automation_status": approval_status_result.get("automation_status", ""),
        "decision_summary": approval_status_result.get("decision_summary", ""),
        "task_writeback_status": approval_writeback_result.get("task_writeback_status", ""),
        "goal_writeback_status": approval_writeback_result.get("goal_writeback_status", ""),
    }


def _write_text(repo_root, target_path, text):
    path = Path(repo_root) / target_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _empty_result(spec, write_status):
    return {
        "target_path": spec["target_path"],
        "title": spec["title"],
        "write_status": write_status,
        "index_status": "pending",
        "evidence_refs": [],
    }


def materialize_real_knowledge_assets(
    repo_root,
    payload,
    approval_status_result,
    approval_writeback_result,
):
    source_refs = payload.get("source_refs", {})
    runbook_spec = payload["runbook"]
    handoff_spec = payload["handoff"]

    runbook_result = _empty_result(runbook_spec, "failed")
    handoff_result = _empty_result(handoff_spec, "skipped")

    try:
        runbook_text = RUNBOOK_TEMPLATE.format(
            **_render_context(
                source_refs,
                approval_status_result,
                approval_writeback_result,
                runbook_spec["title"],
            )
        )
        _write_text(repo_root, runbook_spec["target_path"], runbook_text)
        runbook_result["write_status"] = "success"
        runbook_result["evidence_refs"] = [runbook_spec["target_path"]]
    except Exception as exc:
        runbook_result["error"] = str(exc)
        return {"runbook": runbook_result, "handoff": handoff_result}

    try:
        handoff_text = HANDOFF_TEMPLATE.format(
            **_render_context(
                source_refs,
                approval_status_result,
                approval_writeback_result,
                handoff_spec["title"],
            )
        )
        _write_text(repo_root, handoff_spec["target_path"], handoff_text)
        handoff_result["write_status"] = "success"
        handoff_result["evidence_refs"] = [handoff_spec["target_path"]]
    except Exception as exc:
        handoff_result["write_status"] = "failed"
        handoff_result["error"] = str(exc)

    return {"runbook": runbook_result, "handoff": handoff_result}
