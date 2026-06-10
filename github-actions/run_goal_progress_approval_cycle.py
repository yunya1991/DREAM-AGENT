import importlib.util
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module(name, file_name):
    path = HERE / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SYNC = load_module("sync_github_to_feishu", "sync_github_to_feishu.py")
GOAL = load_module("build_goal_progress_record", "build_goal_progress_record.py")
GATE = load_module("evaluate_risk_approval_gate", "evaluate_risk_approval_gate.py")
APPROVAL_API = load_module("feishu_approval_api", "feishu_approval_api.py")


def utc_now():
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def extract_instance_code(payload):
    if not isinstance(payload, dict):
        return ""
    data = payload.get("data")
    if isinstance(data, dict):
        if data.get("instance_code"):
            return data.get("instance_code", "")
        nested = data.get("data")
        if isinstance(nested, dict) and nested.get("instance_code"):
            return nested.get("instance_code", "")
    if payload.get("instance_code"):
        return payload.get("instance_code", "")
    return ""


def build_approval_form(task_payload, gate_result):
    return [
        {"id": "decision_id", "type": "textarea", "value": task_payload.get("task_id", "")},
        {
            "id": "trigger_reason",
            "type": "textarea",
            "value": gate_result.get("trigger_reason", ""),
        },
    ]


def is_approval_timed_out(task_payload):
    due_at = task_payload.get("approval_due_at", "")
    if not due_at:
        return False
    return due_at <= utc_now()


def apply_timeout_fallback(task_updates, gate_result):
    fallback = gate_result.get("timeout_fallback", {})
    if fallback.get("is_safe") and fallback.get("action") != "pause":
        task_updates["approval_status"] = "timeout"
        task_updates["automation_status"] = "running"
        task_updates["decision_summary"] = fallback.get(
            "decision_summary",
            "timeout:auto_continue_safe",
        )
        return

    task_updates["approval_status"] = "timeout"
    task_updates["automation_status"] = "paused"
    task_updates["decision_summary"] = "waiting_for_manual_decision"


def run_cycle(
    task_payload,
    goal_payload,
    sibling_tasks,
    tenant_access_token,
    approval_code,
    applicant_user_id,
    applicant_open_id="",
):
    gate_result = GATE.evaluate_gate(task_payload)
    task_updates = dict(task_payload)
    effective_applicant_open_id = applicant_open_id or applicant_user_id

    if not gate_result.get("requires_approval"):
        task_updates["approval_status"] = "not_required"
        task_updates["decision_summary"] = "auto_continue"
    elif task_payload.get("approval_instance_code"):
        instance = APPROVAL_API.get_instance(
            tenant_access_token,
            task_payload["approval_instance_code"],
        )
        if (
            instance.get("status") == "PENDING"
            and is_approval_timed_out(task_payload)
        ):
            apply_timeout_fallback(task_updates, gate_result)
        else:
            resolved = APPROVAL_API.resolve_instance_status(
                instance,
                decision_id=task_payload.get("task_id", ""),
            )
            task_updates.update(resolved)
    else:
        approval_body = APPROVAL_API.build_create_instance_body(
            approval_code=approval_code,
            applicant_open_id=effective_applicant_open_id,
            instance_external_id=task_payload.get("task_id", ""),
            form=build_approval_form(task_payload, gate_result),
        )
        task_updates["approval_status"] = "pending"
        task_updates["approval_decision_id"] = task_payload.get("task_id", "")
        task_updates["automation_status"] = "paused"
        try:
            created = APPROVAL_API.create_instance(tenant_access_token, approval_body)
        except Exception as exc:
            task_updates["decision_summary"] = "approval_create_failed"
            task_updates["approval_create_error"] = str(exc)
        else:
            instance_code = extract_instance_code(created)
            if instance_code:
                task_updates["approval_instance_code"] = instance_code
                task_updates["decision_summary"] = "approval_created"
            else:
                task_updates["decision_summary"] = "approval_create_failed"
                task_updates["approval_create_error"] = json.dumps(created, ensure_ascii=False)

    goal_record = GOAL.build_goal_record(goal_payload, [task_updates, *sibling_tasks])
    return {
        "task_record": SYNC.build_feishu_record(task_updates),
        "task_updates": task_updates,
        "goal_record": goal_record,
    }


def main():
    payload = json.load(sys.stdin)
    result = run_cycle(
        task_payload=payload.get("task_payload", {}),
        goal_payload=payload.get("goal_payload", {}),
        sibling_tasks=payload.get("sibling_tasks", []),
        tenant_access_token=payload.get("tenant_access_token", ""),
        approval_code=payload.get("approval_code", ""),
        applicant_user_id=payload.get("applicant_user_id", ""),
        applicant_open_id=payload.get("applicant_open_id", ""),
    )
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
