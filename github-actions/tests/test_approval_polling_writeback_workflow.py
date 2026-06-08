import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ApprovalPollingWritebackWorkflowTests(unittest.TestCase):
    def read_workflow(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "approval-polling-writeback.yml"
        return workflow.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "approval-polling-writeback.yml"
        self.assertTrue(workflow.exists(), str(workflow))

    def test_workflow_declares_required_inputs(self):
        text = self.read_workflow()
        self.assertIn("approval_instance_code:", text)
        self.assertIn("decision_id:", text)
        self.assertIn("task_payload_json:", text)
        self.assertIn("goal_payload_json:", text)
        self.assertIn("base_sync_json:", text)

    def test_workflow_calls_query_writeback_and_summary_helpers(self):
        text = self.read_workflow()
        self.assertIn("python3 github-actions/query_real_approval_status.py", text)
        self.assertIn("python3 github-actions/run_approval_polling_writeback.py", text)
        self.assertIn("python3 github-actions/render_approval_polling_writeback_summary.py", text)
        self.assertIn("decoder.raw_decode", text)

    def test_workflow_uploads_artifacts_even_on_failure(self):
        text = self.read_workflow()
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("approval_status_result.json", text)
        self.assertIn("approval_writeback_result.json", text)

    def test_workflow_injects_bot_lark_runtime_for_writeback(self):
        text = self.read_workflow()
        self.assertIn("LARK_IDENTITY: bot", text)
        self.assertIn("LARKSUITE_CLI_APP_ID: ${{ secrets.LARK_APP_ID }}", text)
        self.assertIn(
            "LARKSUITE_CLI_TENANT_ACCESS_TOKEN: ${{ env.LARK_TENANT_ACCESS_TOKEN }}",
            text,
        )
        self.assertIn("LARKSUITE_CLI_STRICT_MODE: off", text)
        self.assertIn("tenant_access_token/internal", text)


if __name__ == "__main__":
    unittest.main()
