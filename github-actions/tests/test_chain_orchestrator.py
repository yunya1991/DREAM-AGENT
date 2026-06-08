import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOADER_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "scenario_loader.py"
ORCHESTRATOR_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "chain_orchestrator.py"
SCENARIO_PATH = (
    ROOT
    / "github-actions"
    / "tests"
    / "fixtures"
    / "integration"
    / "core_objective_baseline.json"
)


def load_module(module_path, name):
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChainOrchestratorTests(unittest.TestCase):
    def load_payload(self):
        loader = load_module(LOADER_PATH, "scenario_loader")
        return loader.load_rehearsal_scenario(ROOT, SCENARIO_PATH)

    def test_orchestrator_runs_five_steps_for_core_baseline(self):
        module = load_module(ORCHESTRATOR_PATH, "chain_orchestrator")
        result = module.run_rehearsal_chain(self.load_payload())
        self.assertEqual(
            [item["skill_name"] for item in result["step_results"]],
            ["okr-driven", "bitable", "github-sync", "approval", "knowledge-ops"],
        )
        self.assertEqual(result["step_results"][0]["normalized"]["system_status"], "pass")
        self.assertEqual(result["step_results"][-1]["normalized"]["system_status"], "pass")

    def test_orchestrator_stops_when_approval_becomes_blocked(self):
        module = load_module(ORCHESTRATOR_PATH, "chain_orchestrator")
        payload = self.load_payload()
        payload["inputs"]["approval"]["approval_context"]["approval_code"] = ""
        result = module.run_rehearsal_chain(payload)
        self.assertEqual(result["step_results"][-1]["skill_name"], "approval")
        self.assertEqual(result["step_results"][-1]["normalized"]["system_status"], "blocked")
        self.assertGreaterEqual(len(result["breakpoints"]), 1)


if __name__ == "__main__":
    unittest.main()
