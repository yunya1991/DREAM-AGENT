import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_hybrid_unit_dispatch_payload.py"
SPEC = importlib.util.spec_from_file_location(
    "build_hybrid_unit_dispatch_payload", MODULE_PATH
)
MODULE = importlib.util.module_from_spec(SPEC)


class BuildHybridUnitDispatchPayloadTests(unittest.TestCase):
    def test_build_payload_extracts_hybrid_dispatch_fields(self):
        SPEC.loader.exec_module(MODULE)
        payload = MODULE.build_payload(
            {
                "unit": {
                    "unit_id": "unit-001",
                    "track": "strategy-mainline",
                    "feishu_asset_mode": "degraded-with-backfill",
                    "version_anchor": {"git_commit_before": "abc123"},
                    "rollback_strategy": {"default_level": "unit"},
                }
            }
        )
        self.assertEqual(payload["unit_id"], "unit-001")
        self.assertEqual(payload["track"], "strategy-mainline")
        self.assertEqual(payload["feishu_asset_mode"], "degraded-with-backfill")
        self.assertEqual(payload["rollback_level"], "unit")


if __name__ == "__main__":
    unittest.main()
