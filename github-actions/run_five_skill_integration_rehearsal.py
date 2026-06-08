import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from feishu_collab.integration.chain_orchestrator import run_rehearsal_chain
from feishu_collab.integration.rehearsal_reporter import build_rehearsal_report
from feishu_collab.integration.scenario_loader import load_rehearsal_scenario
from feishu_collab.integration.scenario_registry import resolve_scenario_manifest


DEFAULT_SCENARIO_ID = "core-objective-baseline"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "integration" / "scenario_registry.json"


def run_rehearsal(scenario_id=DEFAULT_SCENARIO_ID):
    scenario_path = resolve_scenario_manifest(
        repo_root=ROOT.parent,
        scenario_id=scenario_id,
        registry_path=REGISTRY_PATH,
    )
    payload = load_rehearsal_scenario(ROOT.parent, scenario_path)
    result = run_rehearsal_chain(payload)
    return build_rehearsal_report(
        scenario_manifest=payload["scenario_manifest"],
        step_results=result["step_results"],
        breakpoints=result["breakpoints"],
    )


if __name__ == "__main__":
    selected = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SCENARIO_ID
    report = run_rehearsal(scenario_id=selected)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
