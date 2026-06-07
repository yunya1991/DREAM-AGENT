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
APPROVAL_API = load_module("feishu_approval_api", "feishu_approval_api.py")
LARK = load_module("lark_cli", "lark_cli.py")


def upsert_base_record(base_token, table_id, record_id, fields):
    payload = [
        "base",
        "+record-upsert",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--record-id",
        record_id,
        "--json",
        json.dumps(fields, ensure_ascii=False),
    ]
    return LARK.run_lark_json(payload, identity="bot")


def poll_and_sync(payload):
    base_sync = payload["base_sync"]
    task_updates = dict(payload["task_payload"])
    instance_code = payload["approval_instance_code"]
    task_updates.setdefault("approval_status", "pending")
    task_updates.setdefault("approval_decision_id", task_updates.get("task_id", ""))
    task_updates.setdefault("automation_status", "paused")
    task_updates.setdefault("approval_instance_code", instance_code)

    instance = APPROVAL_API.get_instance(payload["tenant_access_token"], instance_code)
    task_updates.update(
        APPROVAL_API.build_status_projection(
            instance,
            decision_id=task_updates.get("approval_decision_id", task_updates.get("task_id", "")),
            instance_code=instance_code,
        )
    )
    task_record = SYNC.build_feishu_record(task_updates)
    # The goal builder owns the payload shape; keep upstream fields intact here.
    goal_payload = payload["goal_payload"]
    goal_record = GOAL.build_goal_record(
        goal_payload,
        [task_updates, *payload["sibling_tasks"]],
    )

    upsert_base_record(
        base_sync["base_token"],
        base_sync["task_table_id"],
        base_sync["task_record_id"],
        task_record,
    )
    upsert_base_record(
        base_sync["base_token"],
        base_sync["goal_table_id"],
        base_sync["goal_record_id"],
        goal_record,
    )

    return {
        "task_updates": task_updates,
        "task_record": task_record,
        "goal_record": goal_record,
    }


if __name__ == "__main__":
    json.dump(poll_and_sync(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
