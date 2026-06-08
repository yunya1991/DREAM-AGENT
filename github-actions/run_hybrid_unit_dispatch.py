import json
import sys


DEFAULT_AGENTS = [
    "collab-developer-agent",
    "collab-validator-agent",
    "collab-governance-agent",
]


def build_dispatch_plan(payload):
    assigned_agents = payload.get("suggested_agents") or DEFAULT_AGENTS
    return {
        "unit_id": payload.get("unit_id", ""),
        "assigned_agents": assigned_agents,
        "execution_order": [
            "dispatch",
            "developer",
            "validator",
            "governance",
        ],
        "acceptance_mode": payload.get("acceptance_mode", "chain-runnable"),
        "feishu_asset_mode": payload.get("feishu_asset_mode", "full-sync"),
        "rollback_level": payload.get("rollback_level", "unit"),
        "required_comments": [
            "STARTED",
            "TEST_REPORT",
            "VALIDATION_RESULT",
            "UPDATED",
        ],
    }


if __name__ == "__main__":
    json.dump(build_dispatch_plan(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
