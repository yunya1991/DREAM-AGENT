import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class CollabWorkflowPresenceTests(unittest.TestCase):
    def test_collab_workflows_exist(self):
        workflows = REPO_ROOT / ".github" / "workflows"
        required = [
            "collab-developer-agent.yml",
            "collab-validator-agent.yml",
            "collab-governance-agent.yml",
        ]
        for name in required:
            self.assertTrue((workflows / name).exists(), str(workflows / name))


class AcceptanceWorkflowPresenceTests(unittest.TestCase):
    def test_acceptance_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        self.assertTrue(workflow.exists(), str(workflow))


if __name__ == "__main__":
    unittest.main()
