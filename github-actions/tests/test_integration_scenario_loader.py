import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "scenario_loader.py"
SPEC = importlib.util.spec_from_file_location("scenario_loader", MODULE_PATH)
SCENARIO_PATH = (
    ROOT
    / "github-actions"
    / "tests"
    / "fixtures"
    / "integration"
    / "core_objective_baseline.json"
)


class IntegrationScenarioLoaderTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_loader_reads_manifest_and_all_skill_inputs(self):
        module = self.load_module()
        payload = module.load_rehearsal_scenario(ROOT, SCENARIO_PATH)
        self.assertEqual(payload["scenario_manifest"]["scenario_id"], "core-objective-baseline")
        self.assertEqual(
            payload["scenario_manifest"]["skill_sequence"],
            ["okr-driven", "bitable", "github-sync", "approval", "knowledge-ops"],
        )
        self.assertIn("spec_text", payload["inputs"]["okr"])
        self.assertIn("plan_text", payload["inputs"]["okr"])
        self.assertIn("base_context", payload["inputs"]["bitable"])
        self.assertIn("event_payload", payload["inputs"]["github_sync"])
        self.assertIn("risk_context", payload["inputs"]["approval"])
        self.assertIn("handoff_context", payload["inputs"]["knowledge_ops"])

    def test_loader_keeps_repo_relative_paths_in_manifest(self):
        module = self.load_module()
        payload = module.load_rehearsal_scenario(ROOT, SCENARIO_PATH)
        self.assertEqual(
            payload["scenario_manifest"]["sources"]["okr_spec_path"],
            "docs/superpowers/specs/2026-06-08-okr-driven-skill-design.md",
        )


if __name__ == "__main__":
    unittest.main()
