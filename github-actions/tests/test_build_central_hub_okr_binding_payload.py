import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_central_hub_okr_binding_payload.py"
SPEC = importlib.util.spec_from_file_location("build_central_hub_okr_binding_payload", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class BuildCentralHubOkrBindingPayloadTests(unittest.TestCase):
    def test_build_binding_payload_marks_goal_aligned(self):
        SPEC.loader.exec_module(MODULE)
        payload = MODULE.build_binding_payload(
            {
                "goal_id": "goal-trading-hub-connectivity-20260519",
                "goal_name": "中台与前端联动验证能力打通",
            },
            {
                "objective_id": "obj-central-hub-001",
                "objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
                "objective_owner": "governance-agent",
            },
        )
        self.assertEqual(payload["OKR对齐"], "已对齐")
        self.assertEqual(payload["okr_objective_id"], "obj-central-hub-001")
        self.assertEqual(
            payload["okr_objective_title"],
            "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
        )
        self.assertEqual(payload["okr_owner"], "governance-agent")
        self.assertEqual(payload["okr_sync_status"], "bound")

    def test_build_binding_payload_emits_summary_for_four_krs(self):
        SPEC.loader.exec_module(MODULE)
        payload = MODULE.build_binding_payload(
            {
                "goal_id": "goal-trading-hub-connectivity-20260519",
                "goal_name": "中台与前端联动验证能力打通",
            },
            {
                "objective_id": "obj-central-hub-001",
                "objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
                "objective_owner": "governance-agent",
                "krs": [
                    "KR1: Hub 到 Trading 的实时桥接能力可运行",
                    "KR2: 前端关键页面完成实时联动验证",
                    "KR3: 审批、目标推进、workflow 提醒与老板视图形成运行闭环",
                    "KR4: 架构图、spec、实施计划中的核心功能项被拆解进持续推进机制并可跟踪",
                ],
            },
        )
        self.assertIn("KR1", payload["最近决策摘要"])
        self.assertIn("KR4", payload["最近决策摘要"])


if __name__ == "__main__":
    unittest.main()
