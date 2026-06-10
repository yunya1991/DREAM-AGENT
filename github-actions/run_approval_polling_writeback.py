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


POLL = load_module("poll_feishu_approval_and_sync_base", "poll_feishu_approval_and_sync_base.py")


def run_writeback(payload):
    sync_result = POLL.sync_with_status_result(
        payload={
            "task_payload": payload.get("task_payload", {}),
            "goal_payload": payload.get("goal_payload", {}),
            "sibling_tasks": payload.get("sibling_tasks", []),
            "base_sync": payload.get("base_sync", {}),
        },
        status_result=payload.get("status_result", {}),
    )
    return {
        "task_id": payload.get("task_payload", {}).get("task_id", ""),
        "goal_id": payload.get("goal_payload", {}).get("goal_id", ""),
        "task_record": sync_result.get("task_record", {}),
        "goal_record": sync_result.get("goal_record", {}),
        "monitor_record": sync_result.get("monitor_record", {}),
        "task_writeback_status": sync_result.get("task_writeback_status", ""),
        "goal_writeback_status": sync_result.get("goal_writeback_status", ""),
        "monitor_writeback_status": sync_result.get("monitor_writeback_status", ""),
        "writeback_receipts": {
            "task": sync_result.get("task_writeback_receipt", {}),
            "goal": sync_result.get("goal_writeback_receipt", {}),
            "monitor": sync_result.get("monitor_writeback_receipt", {}),
        },
        "error": sync_result.get("error", ""),
    }


def main():
    payload = json.load(sys.stdin)
    json.dump(run_writeback(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
