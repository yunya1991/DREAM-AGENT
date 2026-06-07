import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_module(name, relative_path):
    path = REPO_ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


POLL = load_module(
    "poll_feishu_approval_and_sync_base",
    "github-actions/poll_feishu_approval_and_sync_base.py",
)


class PollFeishuApprovalSyncBaseTest(unittest.TestCase):
    @patch.object(POLL.APPROVAL_API, "get_instance")
    @patch.object(POLL, "upsert_base_record")
    def test_approved_instance_projects_task_goal_and_writeback(
        self,
        mock_upsert,
        mock_get_instance,
    ):
        mock_get_instance.return_value = {"status": "APPROVED"}
        mock_upsert.side_effect = [
            {"record_id": "rec_task_written"},
            {"record_id": "rec_goal_written"},
        ]

        result = POLL.poll_and_sync(
            {
                "tenant_access_token": "tenant-token",
                "approval_instance_code": "instance-1",
                "task_payload": {
                    "task_id": "task-1",
                    "task_name": "Smoke",
                    "goal_id": "goal-1",
                    "approval_instance_code": "instance-1",
                    "approval_decision_id": "task-1",
                    "approval_status": "pending",
                    "automation_status": "paused",
                },
                "goal_payload": {
                    "goal_id": "goal-1",
                    "goal_name": "Goal",
                    "goal_owner": "owner",
                },
                "sibling_tasks": [],
                "base_sync": {
                    "base_token": "app_base",
                    "task_table_id": "tbl_task",
                    "task_record_id": "rec_task",
                    "goal_table_id": "tbl_goal",
                    "goal_record_id": "rec_goal",
                },
            }
        )

        self.assertEqual(result["task_updates"]["approval_status"], "approved")
        self.assertEqual(result["task_updates"]["automation_status"], "running")
        self.assertEqual(result["goal_record"]["goal_status"], "active")
        self.assertEqual(mock_upsert.call_count, 2)

    @patch.object(POLL.APPROVAL_API, "get_instance")
    @patch.object(POLL, "upsert_base_record")
    def test_writeback_uses_feishu_monitor_fields(self, mock_upsert, mock_get_instance):
        mock_get_instance.return_value = {"status": "REJECTED"}
        mock_upsert.side_effect = [{"record_id": "rec_task"}, {"record_id": "rec_goal"}]

        POLL.poll_and_sync(
            {
                "tenant_access_token": "tenant-token",
                "approval_instance_code": "instance-2",
                "task_payload": {
                    "task_id": "task-2",
                    "task_name": "Smoke 2",
                    "goal_id": "goal-2",
                    "approval_instance_code": "instance-2",
                    "approval_decision_id": "task-2",
                },
                "goal_payload": {
                    "goal_id": "goal-2",
                    "goal_name": "Goal 2",
                    "goal_owner": "owner",
                },
                "sibling_tasks": [],
                "base_sync": {
                    "base_token": "app_base",
                    "task_table_id": "tbl_task",
                    "task_record_id": "rec_task",
                    "goal_table_id": "tbl_goal",
                    "goal_record_id": "rec_goal",
                },
            }
        )

        task_fields = mock_upsert.call_args_list[0].args[3]
        self.assertEqual(task_fields["审批状态"], "rejected")
        self.assertEqual(task_fields["审批决策ID"], "task-2")
        self.assertEqual(task_fields["任务ID"], "task-2")


if __name__ == "__main__":
    unittest.main()
