import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "scenario_registry.py"
SPEC = importlib.util.spec_from_file_location("scenario_registry", MODULE_PATH)
REGISTRY_PATH = ROOT / "github-actions" / "tests" / "fixtures" / "integration" / "scenario_registry.json"


class IntegrationScenarioRegistryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_registry_contains_core_objective_baseline(self):
        module = self.load_module()
        registry = module.load_scenario_registry(ROOT, REGISTRY_PATH)
        self.assertIn("core-objective-baseline", registry)
        self.assertEqual(
            registry["core-objective-baseline"]["manifest_path"],
            "github-actions/tests/fixtures/integration/core_objective_baseline.json",
        )

    def test_resolve_registered_scenario_returns_manifest_path(self):
        module = self.load_module()
        result = module.resolve_scenario_manifest(
            repo_root=ROOT,
            scenario_id="core-objective-baseline",
            registry_path=REGISTRY_PATH,
        )
        self.assertTrue(str(result).endswith("core_objective_baseline.json"))

    def test_unknown_scenario_id_raises_clear_error(self):
        module = self.load_module()
        with self.assertRaisesRegex(ValueError, "unknown_scenario_id:missing-scenario"):
            module.resolve_scenario_manifest(
                repo_root=ROOT,
                scenario_id="missing-scenario",
                registry_path=REGISTRY_PATH,
            )


if __name__ == "__main__":
    unittest.main()
