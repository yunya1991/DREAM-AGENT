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


BUILDER = load_module(
    "build_agent_collaboration_payload", "build_agent_collaboration_payload.py"
)
CHECKER = load_module("check_agent_collaboration", "check_agent_collaboration.py")
CLOSURE_BUILDER = load_module(
    "build_collaboration_closure_payload", "build_collaboration_closure_payload.py"
)
CLOSURE_CHECKER = load_module(
    "check_collaboration_closure", "check_collaboration_closure.py"
)
UPDATER = load_module("update_agent_ledger", "update_agent_ledger.py")


def run_cycle(raw, task_index_path, reward_index_path):
    payload = BUILDER.build_payload(raw)
    task_id = payload.get("task_id", "")
    if not task_id:
        return {
            "task_id": "",
            "decision": "BLOCK",
            "reason_codes": ["RULE_TASK_ID_REQUIRED"],
            "previous_status": "",
            "new_status": "",
            "reward_written": False,
            "knowledge_sync_written": False,
            "next_required_action": "developer: provide task id",
            "repair_hint": "publish STARTED comment with Task ID",
        }

    requested_status = payload.get("requested_status", "")
    if not requested_status:
        return {
            "task_id": task_id,
            "decision": "BLOCK",
            "reason_codes": ["RULE_REQUESTED_STATUS_REQUIRED"],
            "previous_status": "",
            "new_status": "",
            "state_changed": False,
            "reward_written": False,
            "knowledge_sync_written": False,
            "next_required_action": "governance: provide Governance Handoff",
            "repair_hint": "publish VALIDATION_RESULT with Governance Handoff",
        }

    task_index = json.loads(Path(task_index_path).read_text(encoding="utf-8"))
    reward_index = json.loads(Path(reward_index_path).read_text(encoding="utf-8"))
    task = next(
        (item for item in task_index.get("tasks", []) if item.get("task_id") == task_id),
        None,
    )
    if task is None:
        return {
            "task_id": task_id,
            "decision": "BLOCK",
            "reason_codes": ["RULE_TASK_NOT_FOUND"],
            "previous_status": "",
            "new_status": "",
            "reward_written": False,
            "knowledge_sync_written": False,
            "next_required_action": "governance: register task in ledger",
            "repair_hint": "add task to tasks/index.json before retrying",
        }

    payload["current_status"] = task.get("status", "")
    payload["sync_review_present"] = any(
        comment.startswith("[设计评审 / DESIGN_REVIEW]") for comment in raw.get("comments", [])
    )
    checker_result = CHECKER.evaluate_payload(payload)
    if checker_result.get("decision") != "PASS":
        return {
            "task_id": task_id,
            "decision": checker_result.get("decision", "BLOCK"),
            "reason_codes": checker_result.get("reason_codes", []),
            "previous_status": task.get("status", ""),
            "new_status": task.get("status", ""),
            "state_changed": False,
            "reward_written": False,
            "knowledge_sync_written": False,
            "next_required_action": checker_result.get("recommended_next_action", ""),
            "repair_hint": "fix blocking governance signal before retrying",
        }

    closure_payload = CLOSURE_BUILDER.build_payload(raw)
    closure_payload["task_id"] = closure_payload.get("task_id") or task_id
    closure_result = CLOSURE_CHECKER.evaluate_payload(closure_payload)
    if closure_result.get("decision") != "PASS":
        return {
            "task_id": task_id,
            "decision": "BLOCK",
            "reason_codes": closure_result.get("reason_codes", []),
            "previous_status": task.get("status", ""),
            "new_status": task.get("status", ""),
            "state_changed": False,
            "reward_written": False,
            "knowledge_sync_written": False,
            "next_required_action": "governance: resolve platform/checks mismatch",
            "repair_hint": "do not release governance when checks are not green",
        }

    updated_task, transition = UPDATER.apply_status_transition(
        task, requested_status
    )

    reward_written = False
    if (
        transition.get("state_changed")
        and transition.get("new_status") == "ledgered"
        and payload.get(
        "validation_score"
    )
        is not None
    ):
        reward = UPDATER.calculate_reward(
            base_reward=10, score=int(payload["validation_score"])
        )
        record = {
            "task_id": task_id,
            "reward_type": "effective_delivery",
            "base_reward": 10,
            "quality_multiplier": reward["quality_multiplier"],
            "final_reward": reward["final_reward"],
            "credited_agent": updated_task.get("owner_agent", "") or "UNKNOWN",
            "credited_at": UPDATER.utc_now(),
        }
        UPDATER.append_reward_record(reward_index, record)
        updated_task["reward"] = reward["final_reward"]
        reward_written = True

    knowledge_sync_written = transition.get("knowledge_sync_written", False)
    state_changed = transition.get("state_changed", False)
    wrote_anything = state_changed or reward_written or knowledge_sync_written
    if wrote_anything:
        task_index["generated_at"] = UPDATER.utc_now()
        Path(task_index_path).write_text(
            json.dumps(task_index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        Path(reward_index_path).write_text(
            json.dumps(reward_index, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {
        "task_id": task_id,
        "decision": "PASS",
        "reason_codes": [],
        "previous_status": transition.get("previous_status", ""),
        "new_status": transition.get("new_status", ""),
        "state_changed": transition.get("state_changed", False),
        "reward_written": reward_written,
        "knowledge_sync_written": knowledge_sync_written,
        "next_required_action": payload.get("recommended_next_action", ""),
        "repair_hint": "",
    }


if __name__ == "__main__":
    raw = json.load(sys.stdin)
    task_index_path = Path(sys.argv[1])
    reward_index_path = Path(sys.argv[2])
    json.dump(
        run_cycle(raw, task_index_path, reward_index_path),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
