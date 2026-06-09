import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class ReusableDriftGuardWorkflowTests(unittest.TestCase):
    def test_reusable_workflow_exists_with_required_contract(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "reusable-drift-guard.yml"
        self.assertTrue(workflow.exists(), str(workflow))

        text = workflow.read_text(encoding="utf-8")
        self.assertIn("name: reusable-drift-guard", text)
        self.assertIn("workflow_call:", text)
        self.assertIn("id: source_ref", text)
        self.assertIn("repository: yunya1991/DREAM-AGENT", text)
        self.assertIn("path: .workbuddy/_dream_agent_source", text)
        self.assertIn(
            "uses: ./.workbuddy/_dream_agent_source/.github/actions/drift-guard",
            text,
        )
        self.assertNotIn("uses: ./.github/actions/drift-guard", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("uses: actions/github-script@v7", text)
        self.assertIn("comment_on_pr_block:", text)


if __name__ == "__main__":
    unittest.main()
