import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FiveSkillRehearsalWorkflowTests(unittest.TestCase):
    def read_workflow(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "five-skill-rehearsal.yml"
        return workflow.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "five-skill-rehearsal.yml"
        self.assertTrue(workflow.exists(), str(workflow))

    def test_workflow_uses_workflow_dispatch_only(self):
        text = self.read_workflow()
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("issue_comment:", text)
        self.assertNotIn("schedule:", text)

    def test_workflow_runs_rehearsal_runner_and_summary_helper(self):
        text = self.read_workflow()
        self.assertIn(
            "python3 github-actions/run_five_skill_integration_rehearsal.py > five-skill-rehearsal-report.json",
            text,
        )
        self.assertIn(
            "python3 github-actions/render_rehearsal_workflow_summary.py five-skill-rehearsal-report.json",
            text,
        )

    def test_workflow_uploads_artifact_even_on_failure(self):
        text = self.read_workflow()
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("five-skill-rehearsal-${{ github.run_id }}", text)
        self.assertIn("five-skill-rehearsal-report.json", text)


if __name__ == "__main__":
    unittest.main()
