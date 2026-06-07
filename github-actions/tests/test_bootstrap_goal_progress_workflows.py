import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "bootstrap_goal_progress_workflows",
    ROOT / "github-actions" / "bootstrap_goal_progress_workflows.py",
)
MODULE = importlib.util.module_from_spec(SPEC)

FIELDS = {
    "当前阻塞": "fld_blocker",
    "风险等级": "fld_risk",
    "approval_status": "fld_approval",
    "OKR对齐": "fld_okr_align",
    "目标负责人": "fld_goal_owner_user",
    "OKR负责人": "fld_okr_owner_user",
}


class BootstrapGoalProgressWorkflowsTests(unittest.TestCase):
    def test_builds_three_workflow_specs(self):
        SPEC.loader.exec_module(MODULE)
        workflows = MODULE.build_workflow_specs(table_name="目标推进表", field_ids=FIELDS)
        self.assertEqual(len(workflows), 3)
        self.assertEqual(workflows[0]["title"], "阻塞升级提醒")
        self.assertEqual(workflows[1]["title"], "审批完成提醒更新目标")
        self.assertEqual(workflows[2]["title"], "OKR对齐缺失提醒")

    def test_change_record_triggers_include_condition_list(self):
        SPEC.loader.exec_module(MODULE)
        workflows = MODULE.build_workflow_specs(table_name="目标推进表", field_ids=FIELDS)

        expected_fields_by_workflow = [
            {FIELDS["当前阻塞"], FIELDS["风险等级"]},
            {FIELDS["approval_status"]},
            {FIELDS["OKR对齐"]},
        ]
        for workflow, expected_field_ids in zip(workflows, expected_fields_by_workflow):
            trigger = workflow["steps"][0]
            self.assertEqual(trigger["type"], "ChangeRecordTrigger")
            self.assertIn("condition_list", trigger["data"])
            self.assertTrue(trigger["data"]["condition_list"])
            for condition in trigger["data"]["condition_list"]:
                self.assertIn("field_id", condition)
                self.assertIn("operator", condition)
                self.assertIn("value", condition)
            self.assertTrue(
                expected_field_ids.issubset(
                    {condition["field_id"] for condition in trigger["data"]["condition_list"]}
                )
            )

    def test_message_receivers_reference_own_trigger_step(self):
        SPEC.loader.exec_module(MODULE)
        workflows = MODULE.build_workflow_specs(table_name="目标推进表", field_ids=FIELDS)

        self.assertEqual(
            workflows[1]["steps"][1]["data"]["receiver"],
            [{"value_type": "ref", "value": f"$.trigger_approval.{FIELDS['目标负责人']}"}],
        )
        self.assertEqual(
            workflows[2]["steps"][1]["data"]["receiver"],
            [{"value_type": "ref", "value": f"$.trigger_okr.{FIELDS['OKR负责人']}"}],
        )

    def test_missing_fields_raise_clear_error(self):
        SPEC.loader.exec_module(MODULE)
        with self.assertRaisesRegex(ValueError, "missing workflow fields"):
            MODULE.build_workflow_specs(table_name="目标推进表", field_ids={"当前阻塞": "fld_only"})


if __name__ == "__main__":
    unittest.main()
