import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "build_agent_lifecycle_payload.py"
SPEC = importlib.util.spec_from_file_location("build_agent_lifecycle_payload", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BuildLifecyclePayloadTests(unittest.TestCase):
    def test_started_comment_extracts_owner_and_shared_file_declaration(self):
        raw = {
            "branch": "agent/solo/lifecycle-docs",
            "pr_body": "## Owner Agent\nOwner Agent: <UNKNOWN>\n",
            "comments": [
                "[协作开工声明 / STARTED]\n\n"
                "Agent: SOLO\n"
                "任务: 修正文档\n"
                "分支: agent/solo/lifecycle-docs\n"
                "计划修改:\n"
                "- docs/a.md\n\n"
                "预期产出:\n"
                "- docs\n\n"
                "占用范围:\n"
                "- docs/shared.md\n\n"
                "冲突门禁结果:\n"
                "- decision: SAFE\n"
                "- reason_codes: []\n\n"
                "状态: STARTED\n"
            ]
        }

        payload = MODULE.build_payload(raw)

        self.assertEqual(payload["owner_agent"], "SOLO")
        self.assertTrue(payload["shared_files_declared"])
        self.assertIn("STARTED", payload["comments"])

    def test_free_form_comment_does_not_count_as_structured_status(self):
        raw = {
            "branch": "agent/solo/lifecycle-docs",
            "pr_body": "",
            "comments": [
                "我们后面记得补 STARTED、UPDATED、BLOCKED、DONE 这些评论。"
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertEqual(payload["comments"], [])
        self.assertEqual(payload["owner_agent"], "UNKNOWN")
        self.assertFalse(payload["scope_changed"])
        self.assertFalse(payload["execution_blocked"])

    def test_updated_and_blocked_comments_drive_scope_and_execution_flags(self):
        raw = {
            "branch": "agent/solo/lifecycle-docs",
            "pr_body": "",
            "comments": [
                "[协作状态更新 / UPDATED]\n\n"
                "Agent: SOLO\n"
                "任务: 调整规则\n"
                "变更说明:\n"
                "- 扩大到 .github/workflows\n\n"
                "当前占用范围:\n"
                "- .github/workflows/agent-lifecycle-guard.yml\n\n"
                "阶段:\n"
                "- Phase 6\n\n"
                "状态: UPDATED\n",
                "[协作阻塞通知 / BLOCKED]\n\n"
                "Agent: SOLO\n"
                "任务: 调整规则\n"
                "阻塞原因:\n"
                "- 需要补充 payload builder\n\n"
                "需要对方配合:\n"
                "- 无\n\n"
                "状态: BLOCKED\n",
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertTrue(payload["scope_changed"])
        self.assertTrue(payload["execution_blocked"])
        self.assertIn("UPDATED", payload["comments"])
        self.assertIn("BLOCKED", payload["comments"])

    def test_pr_template_fallback_extracts_owner_and_task_card(self):
        raw = {
            "branch": "agent/claude/ui-shell",
            "pr_body": (
                "## Task Card\n"
                "Task Card: docs/superpowers/templates/agent-task-card.md\n\n"
                "## Owner Agent\n"
                "Owner Agent: Claude Code\n\n"
                "## Shared Files Declaration\n"
                "Shared Files Declared: yes\n"
            ),
            "comments": [],
        }

        payload = MODULE.build_payload(raw)

        self.assertEqual(payload["owner_agent"], "Claude Code")
        self.assertTrue(payload["task_card_present"])
        self.assertTrue(payload["shared_files_declared"])

    def test_design_review_from_different_reviewer_counts_as_non_owner_review(self):
        raw = {
            "branch": "agent/solo/lifecycle-docs",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[方案评审记录 / DESIGN_REVIEW]\n\n"
                "Reviewer: Claude Code\n"
                "Scope:\n"
                "- review lifecycle docs\n\n"
                "Decision: APPROVED\n"
            ],
            "review_count": 0,
        }

        payload = MODULE.build_payload(raw)

        self.assertTrue(payload["design_review_present"])
        self.assertTrue(payload["non_owner_review_present"])

    def test_design_review_from_owner_does_not_count_as_non_owner_review(self):
        raw = {
            "branch": "agent/solo/lifecycle-docs",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[方案评审记录 / DESIGN_REVIEW]\n\n"
                "Reviewer: SOLO\n"
                "Scope:\n"
                "- self review lifecycle docs\n\n"
                "Decision: APPROVED\n"
            ],
            "review_count": 0,
        }

        payload = MODULE.build_payload(raw)

        self.assertTrue(payload["design_review_present"])
        self.assertFalse(payload["non_owner_review_present"])

    def test_started_comment_extracts_phase_broadcast_execution_mode(self):
        raw = {
            "branch": "agent/solo/lifecycle-docs",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[协作开工声明 / STARTED]\n\n"
                "Agent: SOLO\n"
                "任务: 生命周期收口\n"
                "分支: agent/solo/lifecycle-docs\n"
                "计划修改:\n"
                "- docs/agent-standard-dev-lifecycle-design.md\n\n"
                "预期产出:\n"
                "- 文档草案\n\n"
                "占用范围:\n"
                "- docs/\n\n"
                "Execution Mode: PHASE_BROADCAST\n"
                "冲突门禁结果:\n"
                "- decision: SAFE\n"
                "- reason_codes: []\n\n"
                "状态: STARTED\n"
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertEqual(payload["execution_mode"], "PHASE_BROADCAST")
        self.assertFalse(payload["direct_takeover"])

    def test_takeover_keywords_are_detected_from_structured_comment(self):
        raw = {
            "branch": "agent/solo/lifecycle-docs",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[协作开工声明 / STARTED]\n\n"
                "Agent: SOLO\n"
                "任务: 接力修复 review 问题\n"
                "分支: agent/solo/lifecycle-docs\n"
                "计划修改:\n"
                "- github-actions/check_agent_lifecycle.py\n\n"
                "预期产出:\n"
                "- checker hotfix\n\n"
                "占用范围:\n"
                "- github-actions/\n\n"
                "冲突门禁结果:\n"
                "- decision: WARNING\n"
                "- reason_codes: [\"USER_AUTHORIZED_TAKEOVER\"]\n\n"
                "说明: 本次为接力修复 / direct takeover。\n"
                "状态: STARTED\n"
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertEqual(payload["execution_mode"], "STANDARD")
        self.assertTrue(payload["direct_takeover"])

    def test_acceptance_request_comment_is_recognized_as_structured_status(self):
        raw = {
            "branch": "design/acceptance-protocol",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[验收委托 / ACCEPTANCE_REQUEST]\n\n"
                "Acceptance Request ID: ar-20260607-002\n"
                "Request Type: phase-gate\n"
                "Request Mode: manual\n"
                "Source of Truth: PR comment\n"
                "Target PR: #5\n\n"
                "## 验收对象\n"
                "- acceptance protocol v1\n"
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertIn("ACCEPTANCE_REQUEST", payload["comments"])
        self.assertTrue(payload["acceptance_request_present"])
        self.assertEqual(payload["acceptance_request_id"], "ar-20260607-002")

    def test_validation_result_comment_extracts_decision_and_mode(self):
        raw = {
            "branch": "design/acceptance-protocol",
            "pr_body": "## Owner Agent\nOwner Agent: SOLO\n",
            "comments": [
                "[验证结论 / VALIDATION_RESULT]\n\n"
                "Validator: manual-pilot\n"
                "Validation Mode: acceptance\n"
                "Acceptance Request ID: ar-20260607-002\n"
                "Decision: ACCEPTED\n"
            ],
        }

        payload = MODULE.build_payload(raw)

        self.assertIn("VALIDATION_RESULT", payload["comments"])
        self.assertTrue(payload["validation_result_present"])
        self.assertEqual(payload["validation_mode"], "acceptance")
        self.assertEqual(payload["validation_decision"], "ACCEPTED")
if __name__ == "__main__":
    unittest.main()
