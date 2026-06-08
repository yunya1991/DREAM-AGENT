import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RealApprovalTriggerWorkflowTests(unittest.TestCase):
    def read_workflow(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "real-approval-trigger.yml"
        return workflow.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "real-approval-trigger.yml"
        self.assertTrue(workflow.exists(), str(workflow))

    def test_workflow_declares_required_inputs(self):
        text = self.read_workflow()
        self.assertIn("approval_code:", text)
        self.assertIn("applicant_open_id:", text)
        self.assertIn("task_payload_json:", text)
        self.assertIn("goal_payload_json:", text)

    def test_workflow_calls_dispatch_query_and_summary_helpers(self):
        text = self.read_workflow()
        self.assertIn("python3 github-actions/run_real_approval_dispatch.py", text)
        self.assertIn("python3 github-actions/query_real_approval_status.py", text)
        self.assertIn("python3 github-actions/render_real_approval_summary.py", text)

    def test_workflow_uploads_artifacts_even_on_failure(self):
        text = self.read_workflow()
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("approval_dispatch_result.json", text)
        self.assertIn("approval_status_result.json", text)


if __name__ == "__main__":
    unittest.main()
