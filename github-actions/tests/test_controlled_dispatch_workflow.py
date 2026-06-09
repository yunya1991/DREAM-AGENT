import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "controlled-dispatch.yml"


class ControlledDispatchWorkflowTests(unittest.TestCase):
    def test_dispatch_script_parses_json_once_and_keeps_allowlist(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn('"knowledge-materialization": "knowledge-materialization.yml"', text)
        self.assertIn("const raw = ${{ toJSON(inputs.trigger_inputs_json) }}", text)
        self.assertIn("inputs = JSON.parse(raw)", text)
        self.assertNotIn("inputs = JSON.parse(JSON.parse(raw))", text)


if __name__ == "__main__":
    unittest.main()
