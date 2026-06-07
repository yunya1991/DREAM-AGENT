import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "check_hybrid_unit_dispatch.py"
SPEC = importlib.util.spec_from_file_location("check_hybrid_unit_dispatch", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CheckHybridUnitDispatchTests(unittest.TestCase):
    def test_blocks_missing_rollback_level(self):
        result = MODULE.evaluate_payload(
            {
                "unit_id": "unit-001",
                "track": "strategy-mainline",
                "feishu_asset_mode": "degraded-with-backfill",
                "acceptance_mode": "chain-runnable",
                "rollback_level": "",
            }
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_ROLLBACK_STRATEGY_REQUIRED", result["reason_codes"])

    def test_passes_minimal_runnable_payload(self):
        result = MODULE.evaluate_payload(
            {
                "unit_id": "unit-001",
                "track": "strategy-mainline",
                "feishu_asset_mode": "degraded-with-backfill",
                "acceptance_mode": "chain-runnable",
                "rollback_level": "unit",
            }
        )
        self.assertEqual(result["decision"], "PASS")


if __name__ == "__main__":
    unittest.main()
