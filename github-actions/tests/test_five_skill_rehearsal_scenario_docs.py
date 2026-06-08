import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FiveSkillRehearsalScenarioDocsTests(unittest.TestCase):
    def test_runbook_mentions_registry_driven_scenario_selection(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "five-skill-integration-rehearsal.md"
        ).read_text(encoding="utf-8")
        self.assertIn("scenario_id", text)
        self.assertIn("core-objective-baseline", text)
        self.assertIn("scenario registry", text)
        self.assertIn("workflow_dispatch", text)


if __name__ == "__main__":
    unittest.main()
