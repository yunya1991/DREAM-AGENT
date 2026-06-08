import json
from pathlib import Path


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_rehearsal_scenario(repo_root, scenario_path):
    repo_root = Path(repo_root)
    scenario_path = Path(scenario_path)
    manifest = _read_json(scenario_path)
    sources = manifest["sources"]

    def resolve(relative_path):
        return repo_root / relative_path

    return {
        "scenario_manifest": {
            "scenario_id": manifest["scenario_id"],
            "skill_sequence": manifest["skill_sequence"],
            "sources": sources,
        },
        "inputs": {
            "okr": {
                "spec_text": resolve(sources["okr_spec_path"]).read_text(encoding="utf-8"),
                "plan_text": resolve(sources["okr_plan_path"]).read_text(encoding="utf-8"),
            },
            "bitable": {
                "base_context": _read_json(resolve(sources["bitable_base_context_path"])),
            },
            "github_sync": {
                "event_payload": _read_json(resolve(sources["github_sync_event_path"])),
                "collab_context": _read_json(resolve(sources["github_sync_collab_context_path"])),
            },
            "approval": {
                "risk_context": _read_json(resolve(sources["approval_risk_context_path"])),
                "approval_context": _read_json(resolve(sources["approval_context_path"])),
            },
            "knowledge_ops": {
                "handoff_context": _read_json(resolve(sources["knowledge_handoff_context_path"])),
            },
        },
    }
