import json
import sys


def build_payload(raw):
    unit = raw.get("unit", {})
    rollback = unit.get("rollback_strategy") or {}
    version_anchor = unit.get("version_anchor") or {}
    return {
        "unit_id": unit.get("unit_id", ""),
        "unit_name": unit.get("unit_name", ""),
        "track": unit.get("track", ""),
        "feishu_asset_mode": unit.get("feishu_asset_mode", "full-sync"),
        "suggested_agents": list(unit.get("suggested_agents", [])),
        "acceptance_mode": (unit.get("acceptance_target") or {}).get("mode", ""),
        "rollback_level": rollback.get("default_level", ""),
        "rollback_owner": rollback.get("owner", ""),
        "git_commit_before": version_anchor.get("git_commit_before", ""),
        "workflow_run_id": version_anchor.get("workflow_run_id", ""),
    }


if __name__ == "__main__":
    json.dump(build_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
