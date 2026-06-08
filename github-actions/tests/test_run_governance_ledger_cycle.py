import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_governance_ledger_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_governance_ledger_cycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class GovernanceCycleControllerTests(unittest.TestCase):
    def test_advances_accepted_task_to_ledgered_and_writes_reward(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task_index = tmp_path / "tasks.json"
            reward_index = tmp_path / "rewards.json"
            task_index.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "1970-01-01T00:00:00Z",
                        "open_tasks": [],
                        "tasks": [
                            {
                                "task_id": "task-cycle-1",
                                "status": "accepted",
                                "score": None,
                                "reward": None,
                                "final_credit_agent": "",
                                "governance_closure": {
                                    "archive_summary": "",
                                    "index_updates": [],
                                    "faq_decision": "",
                                    "faq_entries": [],
                                    "closure_agent": "",
                                    "closure_completed_at": "",
                                },
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            reward_index.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "1970-01-01T00:00:00Z",
                        "reward_records": [],
                    }
                ),
                encoding="utf-8",
            )

            raw = {
                "branch": "agent/solo/governance-cycle",
                "pr_body": "",
                "comments": [
                    "[协作开工声明 / STARTED]\n\n"
                    "Task ID: task-cycle-1\n"
                    "Governance Agent: SOLO-GOV\n"
                    "Task Type: parallel\n"
                    "Dependency Gate: accepted\n"
                    "Current Sync State: cleared\n"
                    "Next Required Action: governance ledger write\n",
                    "[验证结论 / VALIDATION_RESULT]\n\n"
                    "Validator: Claude Code\n"
                    "Hard Gate Result: PASS\n"
                    "Score: 90\n"
                    "Decision: ACCEPTED\n"
                    "Governance Handoff: ledgered\n",
                ],
            }

            result = MODULE.run_cycle(raw, task_index, reward_index)

            self.assertEqual(result["decision"], "PASS")
            self.assertEqual(result["previous_status"], "accepted")
            self.assertEqual(result["new_status"], "ledgered")
            self.assertTrue(result["reward_written"])

            tasks_after_first = task_index.read_text(encoding="utf-8")
            rewards_after_first = reward_index.read_text(encoding="utf-8")

            result2 = MODULE.run_cycle(raw, task_index, reward_index)

            self.assertEqual(result2["decision"], "PASS")
            self.assertFalse(result2["state_changed"])
            self.assertFalse(result2["reward_written"])
            self.assertEqual(task_index.read_text(encoding="utf-8"), tasks_after_first)
            self.assertEqual(reward_index.read_text(encoding="utf-8"), rewards_after_first)

    def test_blocks_without_touching_indexes(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task_index = tmp_path / "tasks.json"
            reward_index = tmp_path / "rewards.json"
            initial_tasks = {
                "version": 1,
                "generated_at": "1970-01-01T00:00:00Z",
                "open_tasks": [],
                "tasks": [
                    {
                        "task_id": "task-cycle-2",
                        "status": "accepted",
                        "governance_closure": {
                            "archive_summary": "",
                            "index_updates": [],
                            "faq_decision": "",
                            "faq_entries": [],
                            "closure_agent": "",
                            "closure_completed_at": "",
                        },
                    }
                ],
            }
            initial_rewards = {
                "version": 1,
                "generated_at": "1970-01-01T00:00:00Z",
                "reward_records": [],
            }
            task_index.write_text(json.dumps(initial_tasks), encoding="utf-8")
            reward_index.write_text(json.dumps(initial_rewards), encoding="utf-8")

            raw = {
                "branch": "agent/solo/governance-cycle",
                "pr_body": "",
                "comments": [
                    "[协作开工声明 / STARTED]\n\n"
                    "Task ID: task-cycle-2\n"
                    "Governance Agent: SOLO-GOV\n"
                    "Task Type: shared-sync\n"
                    "Current Sync State: pending\n"
                    "Next Required Action: governance sync review\n",
                ],
            }

            result = MODULE.run_cycle(raw, task_index, reward_index)

            self.assertEqual(result["decision"], "BLOCK")
            self.assertEqual(
                json.loads(task_index.read_text(encoding="utf-8")),
                initial_tasks,
            )
            self.assertEqual(
                json.loads(reward_index.read_text(encoding="utf-8")),
                initial_rewards,
            )

    def test_blocks_ready_governance_when_platform_checks_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            task_index = tmp_path / "tasks.json"
            reward_index = tmp_path / "rewards.json"
            initial_tasks = {
                "version": 1,
                "generated_at": "1970-01-01T00:00:00Z",
                "open_tasks": [],
                "tasks": [
                    {
                        "task_id": "task-cycle-3",
                        "status": "accepted",
                        "governance_closure": {
                            "archive_summary": "",
                            "index_updates": [],
                            "faq_decision": "",
                            "faq_entries": [],
                            "closure_agent": "",
                            "closure_completed_at": "",
                        },
                    }
                ],
            }
            initial_rewards = {
                "version": 1,
                "generated_at": "1970-01-01T00:00:00Z",
                "reward_records": [],
            }
            task_index.write_text(json.dumps(initial_tasks), encoding="utf-8")
            reward_index.write_text(json.dumps(initial_rewards), encoding="utf-8")

            raw = {
                "branch": "agent/solo/governance-cycle",
                "pr_body": "",
                "comments": [
                    "[协作开工声明 / STARTED]\n\n"
                    "Task ID: task-cycle-3\n"
                    "Governance Agent: SOLO-GOV\n"
                    "Task Type: parallel\n"
                    "Dependency Gate: accepted\n"
                    "Current Sync State: cleared\n"
                    "Next Required Action: governance ledger write\n",
                    "[测试报告 / TEST_REPORT]\n\n"
                    "Test Scope: github-actions\n"
                    "Result: PASS\n",
                    "[验证结论 / VALIDATION_RESULT]\n\n"
                    "Validator: Claude Code\n"
                    "Hard Gate Result: PASS\n"
                    "Score: 92\n"
                    "Decision: ACCEPTED\n"
                    "Governance Handoff: ledgered\n",
                ],
                "implementation_status": "tested",
                "platform_status": "checks_failing",
                "governance_status": "ready",
            }

            result = MODULE.run_cycle(raw, task_index, reward_index)

            self.assertEqual(result["decision"], "BLOCK")
            self.assertIn(
                "RULE_GOVERNANCE_REQUIRES_GREEN_CHECKS",
                result["reason_codes"],
            )
            self.assertEqual(
                json.loads(task_index.read_text(encoding="utf-8")),
                initial_tasks,
            )
            self.assertEqual(
                json.loads(reward_index.read_text(encoding="utf-8")),
                initial_rewards,
            )


if __name__ == "__main__":
    unittest.main()
