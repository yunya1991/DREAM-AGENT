import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "rehearsal_reporter.py"
SPEC = importlib.util.spec_from_file_location("rehearsal_reporter", MODULE_PATH)


class RehearsalReporterTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_reporter_uses_blocked_fail_warn_pass_precedence(self):
        module = self.load_module()
        report = module.build_rehearsal_report(
            scenario_manifest={"scenario_id": "core-objective-baseline", "skill_sequence": []},
            step_results=[
                {
                    "skill_name": "okr-driven",
                    "normalized": {"system_status": "pass"},
                    "raw_result": {"execution": {"knowledge_update": {"title": "okr"}}},
                },
                {
                    "skill_name": "github-sync",
                    "normalized": {"system_status": "warn"},
                    "raw_result": {"execution": {"knowledge_update": {"title": "sync"}}},
                },
                {
                    "skill_name": "approval",
                    "normalized": {"system_status": "fail"},
                    "raw_result": {"execution": {"knowledge_update": {"title": "approval"}}},
                },
            ],
            breakpoints=[
                {
                    "skill_name": "approval",
                    "breakpoint_type": "contract_gap",
                    "recovery_hint": "fix contract",
                }
            ],
        )
        self.assertEqual(report["system_status"], "fail")
        self.assertEqual(report["handoff"]["status"], "fail")
        self.assertEqual(report["knowledge_update"]["title"], "approval")


if __name__ == "__main__":
    unittest.main()
