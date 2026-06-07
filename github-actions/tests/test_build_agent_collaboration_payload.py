import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parents[1] / "build_agent_collaboration_payload.py"
SPEC = importlib.util.spec_from_file_location(
    "build_agent_collaboration_payload", MODULE_PATH
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class TemplatePresenceTests(unittest.TestCase):
    def test_required_collaboration_templates_exist(self):
        required = [
            "templates/pr-comment-exploration-proposal.md",
            "templates/pr-comment-validation-result.md",
            "templates/pr-comment-ledger-entry.md",
        ]
        for rel in required:
            self.assertTrue((ROOT / rel).exists(), rel)


class CollaborationPayloadTests(unittest.TestCase):
    def test_extracts_exploration_and_validation_signals(self):
        raw = {
            "branch": "agent/solo/ledger-v1",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[探索提案 / EXPLORATION_PROPOSAL]\n\n"
                "Agent: SOLO\n"
                "Proposal Type: bugfix\n"
                "Necessity:\n- close gap\n"
                "Value:\n- remove blocker\n"
                "Scope Boundaries:\n- ledger/\n"
                "Requested Exclusive Window: 2026-05-18T00:00:00Z\n"
                "Status: EXPLORATION_PROPOSAL\n",
                "[验证结论 / VALIDATION_RESULT]\n\n"
                "Validator: Claude Code\n"
                "Hard Gate Result: PASS\n"
                "Score: 88\n"
                "Decision: ACCEPTED\n"
                "Reward Multiplier: 1.2\n"
                "Ledger Update: ledger/tasks/index.json\n",
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertTrue(payload["exploration_present"])
        self.assertTrue(payload["validation_present"])
        self.assertFalse(payload["ledger_entry_present"])
        self.assertEqual(payload["validation_decision"], "ACCEPTED")
        self.assertEqual(payload["validation_score"], 88)
        self.assertEqual(payload["task_id"], "")
        self.assertEqual(payload["requested_status"], "")
        self.assertEqual(payload["recommended_next_action"], "")

    def test_extracts_governance_and_state_machine_fields(self):
        raw = {
            "branch": "agent/solo/governance-v1",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[协作开工声明 / STARTED]\n\n"
                "Agent: SOLO\n"
                "Task ID: task-governance-1\n"
                "Governance Agent: SOLO-GOV\n"
                "Task Type: shared-sync\n"
                "Dependency Gate: accepted\n"
                "Current Sync State: pending\n"
                "Next Required Action: validator sync review\n"
                "状态: STARTED\n",
                "[验证结论 / VALIDATION_RESULT]\n\n"
                "Validator: Claude Code\n"
                "Score: 91\n"
                "Decision: ACCEPTED\n"
                "Governance Handoff: ledgered\n",
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertEqual(payload["task_id"], "task-governance-1")
        self.assertEqual(payload["governance_agent"], "SOLO-GOV")
        self.assertEqual(payload["task_type"], "shared-sync")
        self.assertEqual(payload["dependency_gate"], "accepted")
        self.assertEqual(payload["current_sync_state"], "pending")
        self.assertEqual(payload["next_required_action"], "validator sync review")
        self.assertEqual(payload["recommended_next_action"], "validator sync review")
        self.assertEqual(payload["governance_handoff"], "ledgered")
        self.assertEqual(payload["requested_status"], "ledgered")
        self.assertTrue(payload["validation_present"])
        self.assertFalse(payload["ledger_entry_present"])

    def test_non_numeric_validation_score_is_ignored(self):
        raw = {
            "branch": "agent/solo/governance-v1",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[协作开工声明 / STARTED]\n\n"
                "Agent: SOLO\n"
                "Task ID: task-governance-1\n"
                "Governance Agent: SOLO-GOV\n"
                "Task Type: shared-sync\n"
                "Dependency Gate: accepted\n"
                "Current Sync State: pending\n"
                "Next Required Action: validator sync review\n"
                "状态: STARTED\n",
                "[验证结论 / VALIDATION_RESULT]\n\n"
                "Validator: Claude Code\n"
                "Score: N/A\n"
                "Decision: ACCEPTED\n"
                "Governance Handoff: ledgered\n",
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertIsNone(payload["validation_score"])

    def test_extracts_controller_fields_from_ledger_entry(self):
        raw = {
            "branch": "agent/solo/governance-cycle-v1",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[协作开工声明 / STARTED]\n\n"
                "Agent: SOLO\n"
                "Task ID: task-cycle-1\n"
                "Governance Agent: SOLO-GOV\n"
                "Task Type: serial\n"
                "Dependency Gate: accepted\n"
                "Current Sync State: cleared\n"
                "Next Required Action: governance ledger write\n"
                "状态: STARTED\n",
                "[验证结论 / VALIDATION_RESULT]\n\n"
                "Validator: Claude Code\n"
                "Hard Gate Result: PASS\n"
                "Score: 90\n"
                "Decision: ACCEPTED\n"
                "Governance Handoff: ledgered\n",
                "[账本记账 / LEDGER_ENTRY]\n\n"
                "Validator: Claude Code\n"
                "Task ID: task-cycle-1\n"
                "Accepted Delivery Pointer: pointer-1\n"
                "Reward Result: 12\n",
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertEqual(payload["task_id"], "task-cycle-1")
        self.assertEqual(payload["requested_status"], "ledgered")
        self.assertTrue(payload["validation_present"])
        self.assertTrue(payload["ledger_entry_present"])
        self.assertEqual(payload["recommended_next_action"], "governance ledger write")


class GovernanceTemplateFieldTests(unittest.TestCase):
    def test_templates_and_task_entrypoints_surface_governance_fields(self):
        started = (ROOT / "templates" / "pr-comment-started.md").read_text(
            encoding="utf-8"
        )
        updated = (ROOT / "templates" / "pr-comment-updated.md").read_text(
            encoding="utf-8"
        )
        done = (ROOT / "templates" / "pr-comment-done.md").read_text(
            encoding="utf-8"
        )
        validation = (
            ROOT / "templates" / "pr-comment-validation-result.md"
        ).read_text(encoding="utf-8")
        task_card = (
            ROOT / "docs" / "superpowers" / "templates" / "agent-task-card.md"
        ).read_text(encoding="utf-8")
        pr_template = (ROOT / ".github" / "pull_request_template.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("Governance Agent:", started)
        self.assertIn("Task Type:", started)
        self.assertIn("Dependency Gate:", started)
        self.assertIn("Current Sync State:", started)
        self.assertIn("Next Required Action:", started)

        self.assertIn("Governance Agent:", updated)
        self.assertIn("Task Type:", updated)
        self.assertIn("Current Sync State:", updated)
        self.assertIn("Next Required Action:", updated)

        self.assertIn("Validation Pointer:", done)
        self.assertIn("Archive Summary:", done)
        self.assertIn("Governance Handoff:", validation)

        self.assertIn("## Governance", task_card)
        self.assertIn("Dependency Gate:", task_card)
        self.assertIn("Next Required Action:", task_card)

        self.assertIn("Governance Agent:", pr_template)
        self.assertIn("Task Type:", pr_template)
        self.assertIn("Dependency Gate:", pr_template)
        self.assertIn("Next Required Action:", pr_template)

        self.assertIn("Execution Mode:", started)
        self.assertIn("Direct Takeover:", started)
        self.assertIn("Execution Mode:", updated)
        self.assertIn("Direct Takeover:", updated)
        self.assertIn("Execution Mode:", done)
        self.assertIn("Direct Takeover:", done)
        self.assertIn("Execution Mode:", task_card)
        self.assertIn("Direct Takeover:", task_card)
        self.assertIn("Execution Mode:", pr_template)
        self.assertIn("Direct Takeover:", pr_template)

    def test_closure_templates_surface_four_status_layers(self):
        updated = (ROOT / "templates" / "pr-comment-updated.md").read_text(
            encoding="utf-8"
        )
        validation = (
            ROOT / "templates" / "pr-comment-validation-result.md"
        ).read_text(encoding="utf-8")
        handoff = (
            ROOT / "templates" / "pr-comment-governance-handoff.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Implementation Status:", updated)
        self.assertIn("Platform Status:", updated)
        self.assertIn("Governance Status:", updated)
        self.assertIn("Automation Status:", updated)

        self.assertIn("Implementation Status:", validation)
        self.assertIn("Platform Status:", validation)
        self.assertIn("Validation Decision:", validation)
        self.assertIn("Governance Recommendation:", validation)

        self.assertIn("[治理移交 / GOVERNANCE_HANDOFF]", handoff)
        self.assertIn("Implementation Status:", handoff)
        self.assertIn("Platform Status:", handoff)
        self.assertIn("Governance Status:", handoff)
        self.assertIn("Automation Status:", handoff)
        self.assertIn("Release Decision:", handoff)


if __name__ == "__main__":
    unittest.main()
