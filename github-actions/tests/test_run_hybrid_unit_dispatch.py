import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_hybrid_unit_dispatch.py"
SPEC = importlib.util.spec_from_file_location("run_hybrid_unit_dispatch", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RunHybridUnitDispatchTests(unittest.TestCase):
    def test_build_dispatch_plan_defaults_to_existing_agents(self):
        plan = MODULE.build_dispatch_plan(
            {
                "unit_id": "unit-001",
                "suggested_agents": [],
                "feishu_asset_mode": "degraded-with-backfill",
                "rollback_level": "unit",
            }
        )
        self.assertEqual(
            plan["assigned_agents"],
            [
                "collab-developer-agent",
                "collab-validator-agent",
                "collab-governance-agent",
            ],
        )
        self.assertEqual(plan["feishu_asset_mode"], "degraded-with-backfill")


if __name__ == "__main__":
    unittest.main()
