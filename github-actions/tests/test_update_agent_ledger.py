import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "update_agent_ledger.py"
SPEC = importlib.util.spec_from_file_location("update_agent_ledger", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LedgerSeedShapeTests(unittest.TestCase):
    def test_task_index_has_required_top_level_keys(self):
        data = json.loads(
            (ROOT / "ledger" / "tasks" / "index.json").read_text(encoding="utf-8")
        )
        for k in ["version", "generated_at", "open_tasks", "tasks"]:
            self.assertIn(k, data)


class RewardCalculationTests(unittest.TestCase):
    def test_calculates_quality_weighted_reward(self):
        reward = MODULE.calculate_reward(base_reward=10, score=88)
        self.assertEqual(reward["quality_multiplier"], 1.0)
        self.assertEqual(reward["final_reward"], 10)


class GovernanceTaskTemplateTests(unittest.TestCase):
    def test_task_template_exposes_governance_fields(self):
        data = json.loads(
            (ROOT / "ledger" / "templates" / "task-record.json").read_text(
                encoding="utf-8"
            )
        )
        required = [
            "goal_id",
            "parent_task_id",
            "depends_on",
            "dependency_gate",
            "shared_boundary",
            "sync_checkpoint",
            "current_sync_state",
            "validation_pointer",
            "archived_at",
            "knowledge_synced_at",
            "next_required_action",
            "governance_closure",
        ]
        for key in required:
            self.assertIn(key, data)


class HybridUnitTemplateTests(unittest.TestCase):
    def test_hybrid_unit_template_exposes_dispatch_and_rollback_fields(self):
        data = json.loads(
            (ROOT / "ledger" / "templates" / "hybrid-unit-record.json").read_text(
                encoding="utf-8"
            )
        )
        required = [
            "unit_id",
            "track",
            "frontend_surface",
            "platform_capability",
            "acceptance_target",
            "collaboration_asset_surface",
            "feishu_asset_mode",
            "version_anchor",
            "rollback_strategy",
        ]
        for key in required:
            self.assertIn(key, data)

    def test_task_template_includes_hybrid_dispatch_fields(self):
        data = json.loads(
            (ROOT / "ledger" / "templates" / "task-record.json").read_text(
                encoding="utf-8"
            )
        )
        for key in [
            "unit_id",
            "feishu_asset_mode",
            "version_anchor",
            "rollback_strategy",
        ]:
            self.assertIn(key, data)


class GovernanceClosureTests(unittest.TestCase):
    def test_builds_governance_closure_record(self):
        closure = MODULE.build_governance_closure(
            archive_summary="closed with sync notes",
            index_updates=["docs/README.md"],
            faq_decision="written",
            faq_entries=["shared-sync closeout"],
            closure_agent="SOLO-GOV",
        )
        self.assertEqual(closure["closure_agent"], "SOLO-GOV")
        self.assertEqual(closure["faq_decision"], "written")
        self.assertTrue(closure["closure_completed_at"].endswith("Z"))

    def test_rejects_knowledge_sync_without_closure_data(self):
        task = {
            "status": "archived",
            "governance_closure": {
                "archive_summary": "",
                "index_updates": [],
                "faq_decision": "",
                "faq_entries": [],
                "closure_agent": "",
                "closure_completed_at": "",
            },
        }
        with self.assertRaises(ValueError):
            MODULE.apply_status_transition(task, "knowledge_synced")


class DocsEntrypointTests(unittest.TestCase):
    def test_root_readme_surfaces_v1_docs_directly(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/agent-collaboration-system-v1-design.md", text)
        self.assertIn("docs/agent-collaboration-system-v1-implementation-plan.md", text)

    def test_docs_readmes_link_governance_increment_plan(self):
        rel = "agent-collaboration-system-v1-governance-agent-implementation-plan.md"
        root_text = (ROOT / "README.md").read_text(encoding="utf-8")
        docs_text = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        self.assertIn(rel, root_text)
        self.assertIn(rel, docs_text)

    def test_docs_readme_keeps_migration_guidance(self):
        text = (ROOT / "docs" / "README.md").read_text(encoding="utf-8")
        self.assertIn("docs/superpowers/specs/", text)
        self.assertIn("docs/superpowers/plans/", text)
        self.assertIn("兼容壳", text)


class GovernanceUpdaterIOTests(unittest.TestCase):
    def test_transition_result_reports_state_change(self):
        task = {
            "task_id": "task-cycle-1",
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
        updated, result = MODULE.apply_status_transition(task, "ledgered")
        self.assertEqual(updated["status"], "ledgered")
        self.assertEqual(result["previous_status"], "accepted")
        self.assertEqual(result["new_status"], "ledgered")
        self.assertTrue(result["state_changed"])


class CollaborationClosureStatusTests(unittest.TestCase):
    def test_normalize_closure_status_fills_missing_layers(self):
        task = {}
        result = MODULE.normalize_closure_status(task)
        self.assertEqual(result["implementation_status"], "planned")
        self.assertEqual(result["platform_status"], "no_pr")
        self.assertEqual(result["governance_status"], "draft")
        self.assertEqual(result["automation_status"], "idle")


class GoalApprovalStatusDefaultsTests(unittest.TestCase):
    def test_normalize_closure_status_fills_goal_and_approval_defaults(self):
        task = {}
        result = MODULE.normalize_closure_status(task)
        self.assertEqual(result["goal_id"], "")
        self.assertEqual(result["risk_level"], "low")
        self.assertEqual(result["approval_status"], "not_required")
        self.assertEqual(result["approval_decision_id"], "")
        self.assertEqual(result["approval_due_at"], "")
        self.assertEqual(result["decision_summary"], "")


class HybridRollbackRecordTests(unittest.TestCase):
    def test_task_template_exposes_rollback_fields(self):
        data = json.loads(
            (ROOT / "ledger" / "templates" / "task-record.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("rollback_strategy", data)
        self.assertIn("version_anchor", data)

    def test_normalize_version_anchor_fills_missing_fields(self):
        anchor = MODULE.normalize_version_anchor({"git_commit_before": "abc123"})
        self.assertEqual(anchor["git_commit_before"], "abc123")
        self.assertEqual(anchor["git_branch_or_pr_ref"], "")
        self.assertEqual(anchor["workflow_run_id"], "")
        self.assertEqual(anchor["acceptance_request_id"], "")
        self.assertEqual(anchor["feishu_asset_before_snapshot"], "")

    def test_noop_transition_keeps_state_change_false(self):
        task = {
            "status": "ledgered",
            "governance_closure": {
                "archive_summary": "x",
                "index_updates": ["docs/README.md"],
                "faq_decision": "x",
                "faq_entries": ["y"],
                "closure_agent": "SOLO",
                "closure_completed_at": "2026-06-07T00:00:00Z",
            },
        }
        _, result = MODULE.apply_status_transition(task, "ledgered")
        self.assertFalse(result["state_changed"])


class WorkflowEntrypointTests(unittest.TestCase):
    def test_ledger_maintenance_workflow_surfaces_governance_suite(self):
        text = (
            ROOT / ".github" / "workflows" / "agent-ledger-maintenance.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("Validate collaboration and governance assets", text)
        self.assertIn(
            'python3 -m unittest discover -s "github-actions/tests" -p "test_*.py"',
            text,
        )


if __name__ == "__main__":
    unittest.main()
