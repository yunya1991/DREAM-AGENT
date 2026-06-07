import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_collaboration_closure_payload.py"
SPEC = importlib.util.spec_from_file_location(
    "build_collaboration_closure_payload", MODULE_PATH
)
MODULE = importlib.util.module_from_spec(SPEC)


class BuildCollaborationClosurePayloadTests(unittest.TestCase):
    def test_build_payload_keeps_four_state_layers(self):
        SPEC.loader.exec_module(MODULE)
        payload = MODULE.build_payload(
            {
                "task_id": "task-001",
                "implementation_status": "tested",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
            }
        )
        self.assertEqual(payload["task_id"], "task-001")
        self.assertEqual(payload["implementation_status"], "tested")
        self.assertEqual(payload["platform_status"], "checks_pending")
        self.assertEqual(payload["governance_status"], "review_required")
        self.assertEqual(payload["automation_status"], "running")


if __name__ == "__main__":
    unittest.main()
