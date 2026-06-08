import json
from pathlib import Path


def load_scenario_registry(repo_root, registry_path):
    repo_root = Path(repo_root)
    registry_path = Path(registry_path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return {
        item["scenario_id"]: {
            "manifest_path": item["manifest_path"],
            "description": item.get("description", ""),
            "status": item.get("status", ""),
            "resolved_manifest_path": repo_root / item["manifest_path"],
        }
        for item in data.get("scenarios", [])
    }


def resolve_scenario_manifest(repo_root, scenario_id, registry_path):
    registry = load_scenario_registry(repo_root, registry_path)
    if scenario_id not in registry:
        raise ValueError(f"unknown_scenario_id:{scenario_id}")
    return registry[scenario_id]["resolved_manifest_path"]
