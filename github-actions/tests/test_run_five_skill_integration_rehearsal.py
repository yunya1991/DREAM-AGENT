import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_five_skill_integration_rehearsal.py"
SPEC = importlib.util.spec_from_file_location("run_five_skill_integration_rehearsal", MODULE_PATH)


class RunFiveSkillIntegrationRehearsalTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_runner_returns_system_report_for_default_scenario(self):
        module = self.load_module()
        report = module.run_rehearsal()
        self.assertEqual(report["scenario_manifest"]["scenario_id"], "core-objective-baseline")
        self.assertEqual(len(report["step_results"]), 5)
        self.assertIn(report["system_status"], {"pass", "warn", "fail", "blocked"})
        self.assertIn("handoff", report)
        self.assertIn("knowledge_update", report)


if __name__ == "__main__":
    unittest.main()
