import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "shared" / "status_adapter.py"
SPEC = importlib.util.spec_from_file_location("status_adapter", MODULE_PATH)


class StatusAdapterTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_confirmed_maps_to_pass_without_breakpoint(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="bitable",
            raw_status="confirmed",
            risk_flags=[],
            verification={"status": "confirmed"},
        )
        self.assertEqual(result["system_status"], "pass")
        self.assertEqual(result["breakpoint_type"], "")
        self.assertEqual(result["recovery_hint"], "continue to next skill")

    def test_degraded_success_maps_to_warn_with_execution_gap_hint(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="github-sync",
            raw_status="degraded_success",
            risk_flags=[],
            verification={"status": "degraded_success"},
        )
        self.assertEqual(result["system_status"], "warn")
        self.assertEqual(result["breakpoint_type"], "execution_gap")
        self.assertIn("github-sync", result["recovery_hint"])

    def test_soft_block_maps_to_fail_and_uses_contract_gap_when_risk_flag_present(
        self,
    ):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="approval",
            raw_status="soft_block",
            risk_flags=["status_projection_gap"],
            verification={"status": "soft_block"},
        )
        self.assertEqual(result["system_status"], "fail")
        self.assertEqual(result["breakpoint_type"], "contract_gap")

    def test_hard_block_maps_to_blocked_and_policy_gap_for_missing_gate_inputs(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="approval",
            raw_status="hard_block",
            risk_flags=["missing_approval_code"],
            verification={"status": "hard_block"},
        )
        self.assertEqual(result["system_status"], "blocked")
        self.assertEqual(result["breakpoint_type"], "policy_gap")

    def test_unknown_status_falls_back_to_fail(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="okr-driven",
            raw_status="mystery",
            risk_flags=[],
            verification={"status": "mystery"},
        )
        self.assertEqual(result["system_status"], "fail")
        self.assertEqual(result["breakpoint_type"], "contract_gap")


if __name__ == "__main__":
    unittest.main()
