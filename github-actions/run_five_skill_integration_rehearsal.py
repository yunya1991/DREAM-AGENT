import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from feishu_collab.integration.chain_orchestrator import run_rehearsal_chain
from feishu_collab.integration.rehearsal_reporter import build_rehearsal_report
from feishu_collab.integration.scenario_loader import load_rehearsal_scenario


DEFAULT_SCENARIO = (
    ROOT / "tests" / "fixtures" / "integration" / "core_objective_baseline.json"
)


def run_rehearsal(scenario_path=None):
    payload = load_rehearsal_scenario(ROOT.parent, scenario_path or DEFAULT_SCENARIO)
    result = run_rehearsal_chain(payload)
    return build_rehearsal_report(
        scenario_manifest=payload["scenario_manifest"],
        step_results=result["step_results"],
        breakpoints=result["breakpoints"],
    )


if __name__ == "__main__":
    report = run_rehearsal()
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
