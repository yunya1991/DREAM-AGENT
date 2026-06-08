import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_rehearsal_workflow_summary.py"
SPEC = importlib.util.spec_from_file_location(
    "render_rehearsal_workflow_summary",
    MODULE_PATH,
)


class RenderRehearsalWorkflowSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_report(self, system_status="pass", breakpoints=None):
        return {
            "scenario_manifest": {"scenario_id": "core-objective-baseline"},
            "system_status": system_status,
            "step_results": [
                {
                    "skill_name": "okr-driven",
                    "normalized": {"system_status": "pass"},
                    "verification": {"status": "confirmed"},
                },
                {
                    "skill_name": "approval",
                    "normalized": {"system_status": system_status},
                    "verification": {
                        "status": "confirmed" if system_status == "pass" else "soft_block"
                    },
                },
            ],
            "breakpoints": breakpoints or [],
            "verification_summary": {
                "step_count": 2,
                "breakpoint_count": len(breakpoints or []),
                "highest_status": system_status,
            },
        }

    def test_build_summary_markdown_renders_core_fields_and_step_table(self):
        module = self.load_module()
        summary = module.build_summary_markdown(
            self.sample_report(
                breakpoints=[
                    {
                        "skill_name": "approval",
                        "breakpoint_type": "contract_gap",
                        "recovery_hint": "align approval projection",
                    }
                ]
            )
        )
        self.assertIn("core-objective-baseline", summary)
        self.assertIn("System Status: `pass`", summary)
        self.assertIn("| Skill | Raw Verification | System |", summary)
        self.assertIn("| approval | confirmed | pass |", summary)
        self.assertIn("contract_gap", summary)
        self.assertIn("align approval projection", summary)

    def test_workflow_exit_code_returns_zero_only_for_pass(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_report("pass")), 0)
        self.assertEqual(module.workflow_exit_code(self.sample_report("warn")), 1)
        self.assertEqual(module.workflow_exit_code(self.sample_report("fail")), 1)
        self.assertEqual(module.workflow_exit_code(self.sample_report("blocked")), 1)


if __name__ == "__main__":
    unittest.main()
