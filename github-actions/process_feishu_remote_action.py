import json
import sys


def apply_remote_action(current, incoming):
    action = incoming.get("remote_action", "none")
    result = dict(current)
    result["remote_action"] = "none"

    if action == "pause":
        result["automation_status"] = "paused"
        result["remote_action_result"] = "pause_applied"
        return result

    if action == "retry":
        result["automation_status"] = "running"
        result["remote_action_result"] = "retry_triggered"
        return result

    result["remote_action_result"] = "no_action"
    return result


if __name__ == "__main__":
    data = json.load(sys.stdin)
    json.dump(
        apply_remote_action(data.get("current", {}), data.get("incoming", {})),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
