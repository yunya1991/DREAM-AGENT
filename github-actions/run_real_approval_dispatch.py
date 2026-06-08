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


APPROVAL_CYCLE = load_module(
    "run_goal_progress_approval_cycle",
    "run_goal_progress_approval_cycle.py",
)


def build_dispatch_payload(
    approval_code,
    applicant_open_id,
    tenant_access_token,
    task_payload,
    goal_payload,
    sibling_tasks=None,
):
    return {
        "approval_code": approval_code,
        "applicant_open_id": applicant_open_id,
        "tenant_access_token": tenant_access_token,
        "task_payload": task_payload,
        "goal_payload": goal_payload,
        "sibling_tasks": sibling_tasks or [],
    }


def build_dispatch_result(dispatch_payload, cycle_result):
    task_updates = cycle_result["task_updates"]
    return {
        "approval_code": dispatch_payload["approval_code"],
        "task_id": dispatch_payload["task_payload"].get("task_id", ""),
        "goal_id": dispatch_payload["goal_payload"].get("goal_id", ""),
        "approval_instance_code": task_updates.get("approval_instance_code", ""),
        "approval_status": task_updates.get("approval_status", ""),
        "automation_status": task_updates.get("automation_status", ""),
        "decision_summary": task_updates.get("decision_summary", ""),
        "task_record": cycle_result.get("task_record", {}),
        "goal_record": cycle_result.get("goal_record", {}),
        "task_updates": task_updates,
    }


def main():
    payload = json.load(sys.stdin)
    dispatch_payload = build_dispatch_payload(
        approval_code=payload.get("approval_code", ""),
        applicant_open_id=payload.get("applicant_open_id", ""),
        tenant_access_token=payload.get("tenant_access_token", ""),
        task_payload=payload.get("task_payload", {}),
        goal_payload=payload.get("goal_payload", {}),
        sibling_tasks=payload.get("sibling_tasks", []),
    )
    cycle_result = APPROVAL_CYCLE.run_cycle(
        task_payload=dispatch_payload["task_payload"],
        goal_payload=dispatch_payload["goal_payload"],
        sibling_tasks=dispatch_payload["sibling_tasks"],
        tenant_access_token=dispatch_payload["tenant_access_token"],
        approval_code=dispatch_payload["approval_code"],
        applicant_user_id="",
        applicant_open_id=dispatch_payload["applicant_open_id"],
    )
    json.dump(
        build_dispatch_result(dispatch_payload, cycle_result),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
