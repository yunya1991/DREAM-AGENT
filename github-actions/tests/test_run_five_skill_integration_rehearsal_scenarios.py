import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_five_skill_integration_rehearsal.py"
SPEC = importlib.util.spec_from_file_location(
    "run_five_skill_integration_rehearsal",
    MODULE_PATH,
)


class RunFiveSkillIntegrationRehearsalScenarioTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_run_rehearsal_defaults_to_core_objective_baseline(self):
        module = self.load_module()
        report = module.run_rehearsal()
        self.assertEqual(report["scenario_manifest"]["scenario_id"], "core-objective-baseline")

    def test_run_rehearsal_accepts_registered_scenario_id(self):
        module = self.load_module()
        report = module.run_rehearsal(scenario_id="core-objective-baseline")
        self.assertEqual(report["scenario_manifest"]["scenario_id"], "core-objective-baseline")

    def test_run_rehearsal_rejects_unknown_scenario_id(self):
        module = self.load_module()
        with self.assertRaisesRegex(ValueError, "unknown_scenario_id:missing-scenario"):
            module.run_rehearsal(scenario_id="missing-scenario")


if __name__ == "__main__":
    unittest.main()
