# GitHub Sync SKILL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a preview-first `GitHub-Feishu` collaboration skill that projects `issue + PR + checks` events into Feishu collaboration state, then writes back, verifies, and emits handoff/knowledge outputs after confirmation.

**Architecture:** Keep the skill package thin and move deterministic behavior into focused Python helpers under `github-actions/feishu_collab/github_sync/`. Reuse the existing field semantics from `github-actions/sync_github_to_feishu.py`, consume shared contracts from `github-actions/feishu_collab/shared/contracts.py`, and add an explicit event-coverage registry so the flow can classify supported actions, downgrade on gaps, and stay auditable.

**Tech Stack:** Markdown skill docs, Python 3, `unittest`, `json`, existing GitHub Actions workflows, shared Feishu-collaboration contracts

---

## Scope Check

This plan covers one coherent sub-project:

- Normalize GitHub `issue`, `pull_request`, and `check`-style events into a single preview-first flow
- Reuse the existing GitHub-to-Feishu field mapping as the state-projection adapter
- Add an explicit event coverage registry and tests for auditable support boundaries
- Package the flow as `.trae/skills/feishu-collab-github-sync/SKILL.md`
- Verify that `ExecutionResult`, `KnowledgeUpdate`, and handoff outputs are produced after execution

It does **not** include:

- A general GitHub operations platform
- Full remote-action execution against GitHub
- Rebuilding the existing acceptance workflow from scratch
- Approval-skill implementation beyond gate handoff fields
- Knowledge-Ops implementation beyond emitting routable `KnowledgeUpdate`

## File Map

- Create: `.trae/skills/feishu-collab-github-sync/SKILL.md`
  - Main skill instructions, trigger conditions, preview-first flow, and event-driven guardrails.
- Create: `.trae/skills/feishu-collab-github-sync/references/execution-checklist.md`
  - Operator checklist for event intake, preview review, writeback order, verification, and handoff.
- Create: `github-actions/feishu_collab/github_sync/__init__.py`
  - Package marker for GitHub sync helpers.
- Create: `github-actions/feishu_collab/github_sync/build_github_sync_preview.py`
  - Compile normalized GitHub event payloads plus context into preview data with event summary, field updates, risk flags, and coverage hits.
- Create: `github-actions/tests/test_build_github_sync_preview.py`
  - Lock preview object shapes, coverage hits, and confirmation requirements.
- Create: `github-actions/tests/fixtures/github_sync/issue_event.json`
  - Stable issue-event fixture for preview and dry-run validation.
- Create: `github-actions/tests/fixtures/github_sync/pr_event.json`
  - Stable PR-event fixture with review/check context.
- Create: `github-actions/tests/fixtures/github_sync/check_event.json`
  - Stable checks-event fixture with automation status transitions.
- Create: `github-actions/tests/fixtures/github_sync/collab_context.json`
  - Stable Feishu collaboration context fixture with task/goal/approval linkage.
- Create: `github-actions/feishu_collab/github_sync/materialize_github_sync_execution.py`
  - Turn preview output into ordered writeback stages, `ExecutionResult`-like payload data, `KnowledgeUpdate`, and handoff.
- Create: `github-actions/tests/test_materialize_github_sync_execution.py`
  - Lock writeback order, failure modes, and handoff emission.
- Create: `github-actions/feishu_collab/github_sync/verify_github_sync_projection.py`
  - Re-check record lookup, field writeback, automation summary, comment anchor, and coverage gaps after execution.
- Create: `github-actions/tests/test_verify_github_sync_projection.py`
  - Lock verification behavior for `hard_block`, `soft_block`, `degraded_success`, and `confirmed`.
- Create: `github-actions/feishu_collab/github_sync/event_coverage_registry.json`
  - Explicit registry for supported events, actions, field mapping, fallback policies, and knowledge requirements.
- Create: `github-actions/tests/test_github_sync_event_registry.py`
  - Audit the registry for required event coverage and fallback completeness.
- Modify: `github-actions/sync_github_to_feishu.py`
  - Preserve the current mapping function while exposing a thin adapter helper reused by the new materializer.

## Execution Guardrails

- Ignore the unrelated deletion `.github/workflows/feishu-approval-smoke.yml`; never restore or stage it.
- Ignore `.superpowers/` files and any temporary local state outside the files listed in this plan.
- Keep v1 focused on `Issue + PR + Checks`; do not add merge queues, release automation, or repository-wide dashboards.
- Reuse the existing mapping semantics from `github-actions/sync_github_to_feishu.py`; do not invent a second incompatible field vocabulary.
- Treat unknown actions and incomplete check states as explicit coverage gaps; never silently drop them.
- Emit `KnowledgeUpdate` and handoff payloads whenever execution reaches verification, including degraded outcomes.

## Task 1: Add the GitHub Event Preview Compiler

**Files:**
- Create: `github-actions/feishu_collab/github_sync/__init__.py`
- Create: `github-actions/feishu_collab/github_sync/build_github_sync_preview.py`
- Create: `github-actions/tests/test_build_github_sync_preview.py`
- Create: `github-actions/tests/fixtures/github_sync/issue_event.json`
- Create: `github-actions/tests/fixtures/github_sync/pr_event.json`
- Create: `github-actions/tests/fixtures/github_sync/check_event.json`
- Create: `github-actions/tests/fixtures/github_sync/collab_context.json`

- [ ] **Step 1: Write the failing preview tests**

Create `github-actions/tests/test_build_github_sync_preview.py`:

```python
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "build_github_sync_preview.py"
SPEC = importlib.util.spec_from_file_location("build_github_sync_preview", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "github_sync"


class BuildGithubSyncPreviewTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_preview_builds_pr_event_summary_and_field_updates(self):
        module = self.load_module()
        preview = module.build_github_sync_preview(
            event_payload=self.load_fixture("pr_event.json"),
            collab_context=self.load_fixture("collab_context.json"),
        )
        self.assertEqual(preview["event_summary"]["event_type"], "github.pr.changed")
        self.assertEqual(preview["event_summary"]["repo"], "yunya1991/DREAM-AGENT")
        self.assertEqual(preview["field_updates"]["平台状态"], "checks_pending")
        self.assertEqual(preview["field_updates"]["自动化状态"], "running")
        self.assertEqual(preview["event_coverage_hit"]["action"], "synchronize")
        self.assertEqual(preview["requires_confirmation"], True)

    def test_preview_marks_issue_event_without_goal_link_as_risk(self):
        module = self.load_module()
        context = self.load_fixture("collab_context.json")
        context["goal_id"] = ""
        preview = module.build_github_sync_preview(
            event_payload=self.load_fixture("issue_event.json"),
            collab_context=context,
        )
        self.assertIn("missing_goal_link", preview["risk_flags"])
        self.assertEqual(preview["event_summary"]["event_type"], "github.issue.changed")

    def test_preview_marks_unknown_check_state_as_coverage_gap(self):
        module = self.load_module()
        event_payload = self.load_fixture("check_event.json")
        event_payload["check_run"]["conclusion"] = "startup_failure"
        preview = module.build_github_sync_preview(
            event_payload=event_payload,
            collab_context=self.load_fixture("collab_context.json"),
        )
        self.assertIn("unknown_check_state", preview["risk_flags"])
        self.assertEqual(preview["event_coverage_hit"]["fallback_policy"], "soft_block")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add stable event and context fixtures**

Create `github-actions/tests/fixtures/github_sync/issue_event.json`:

```json
{
  "event_name": "issues",
  "action": "opened",
  "repository": {
    "full_name": "yunya1991/DREAM-AGENT"
  },
  "issue": {
    "number": 21,
    "title": "同步验收状态到飞书协作面",
    "html_url": "https://github.com/yunya1991/DREAM-AGENT/issues/21",
    "user": {
      "login": "asher"
    }
  },
  "sender": {
    "login": "asher"
  }
}
```

Create `github-actions/tests/fixtures/github_sync/pr_event.json`:

```json
{
  "event_name": "pull_request",
  "action": "synchronize",
  "repository": {
    "full_name": "yunya1991/DREAM-AGENT"
  },
  "pull_request": {
    "number": 88,
    "title": "feat: connect github sync preview to collaboration flow",
    "html_url": "https://github.com/yunya1991/DREAM-AGENT/pull/88",
    "head": {
      "ref": "feature/github-sync-preview",
      "sha": "abc123def456"
    },
    "user": {
      "login": "asher"
    }
  },
  "sender": {
    "login": "asher"
  },
  "workflow_run": {
    "id": "778899",
    "status": "in_progress"
  }
}
```

Create `github-actions/tests/fixtures/github_sync/check_event.json`:

```json
{
  "event_name": "check_run",
  "action": "completed",
  "repository": {
    "full_name": "yunya1991/DREAM-AGENT"
  },
  "check_run": {
    "name": "collab-acceptance-agent",
    "status": "completed",
    "conclusion": "success",
    "html_url": "https://github.com/yunya1991/DREAM-AGENT/actions/runs/778899",
    "head_sha": "abc123def456"
  },
  "sender": {
    "login": "github-actions[bot]"
  }
}
```

Create `github-actions/tests/fixtures/github_sync/collab_context.json`:

```json
{
  "task_id": "task-github-sync-001",
  "task_name": "打通 GitHub 事件到飞书协作状态投影",
  "goal_id": "goal-collab-sync-001",
  "repo": "yunya1991/DREAM-AGENT",
  "branch": "feature/github-sync-preview",
  "pr_number": "88",
  "workflow_run_id": "778899",
  "implementation_status": "implemented",
  "platform_status": "checks_pending",
  "governance_status": "review_required",
  "automation_status": "running",
  "risk_level": "medium",
  "approval_status": "not_required",
  "approval_decision_id": "",
  "approval_due_at": "",
  "decision_summary": "",
  "last_comment_anchor": "https://github.com/yunya1991/DREAM-AGENT/pull/88#issuecomment-1",
  "last_commit": "abc123def456",
  "blocker": "",
  "next_action": "wait for checks",
  "remote_action": "none",
  "remote_action_result": ""
}
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_github_sync_preview.py -v
```

Expected: FAIL because `build_github_sync_preview.py` does not exist yet.

- [ ] **Step 4: Write the minimal preview compiler**

Create `github-actions/feishu_collab/github_sync/__init__.py`:

```python
"""GitHub sync helpers for the Feishu collaboration system."""
```

Create `github-actions/feishu_collab/github_sync/build_github_sync_preview.py`:

```python
import json
import sys


def _normalize_event(event_payload):
    event_name = event_payload.get("event_name", "")
    action = event_payload.get("action", "")
    repository = event_payload.get("repository", {})
    sender = event_payload.get("sender", {})

    if event_name == "issues":
        issue = event_payload.get("issue", {})
        return {
            "event_type": "github.issue.changed",
            "object_type": "issue",
            "number": str(issue.get("number", "")),
            "title": issue.get("title", ""),
            "repo": repository.get("full_name", ""),
            "action": action,
            "sender": sender.get("login", ""),
            "branch": "",
            "sha": "",
            "workflow_run_id": "",
        }

    if event_name == "pull_request":
        pr = event_payload.get("pull_request", {})
        workflow_run = event_payload.get("workflow_run", {})
        head = pr.get("head", {})
        return {
            "event_type": "github.pr.changed",
            "object_type": "pull_request",
            "number": str(pr.get("number", "")),
            "title": pr.get("title", ""),
            "repo": repository.get("full_name", ""),
            "action": action,
            "sender": sender.get("login", ""),
            "branch": head.get("ref", ""),
            "sha": head.get("sha", ""),
            "workflow_run_id": str(workflow_run.get("id", "")),
        }

    check_run = event_payload.get("check_run", {})
    return {
        "event_type": "github.check.changed",
        "object_type": "check_run",
        "number": "",
        "title": check_run.get("name", ""),
        "repo": repository.get("full_name", ""),
        "action": action,
        "sender": sender.get("login", ""),
        "branch": "",
        "sha": check_run.get("head_sha", ""),
        "workflow_run_id": "",
    }


def _field_updates(normalized_event, collab_context):
    field_updates = {
        "任务ID": collab_context.get("task_id", ""),
        "任务名称": collab_context.get("task_name", ""),
        "目标ID": collab_context.get("goal_id", ""),
        "仓库": normalized_event["repo"] or collab_context.get("repo", ""),
        "分支": normalized_event["branch"] or collab_context.get("branch", ""),
        "PR号": collab_context.get("pr_number", ""),
        "Workflow运行ID": normalized_event["workflow_run_id"] or collab_context.get("workflow_run_id", ""),
        "实现状态": collab_context.get("implementation_status", ""),
        "平台状态": collab_context.get("platform_status", ""),
        "治理状态": collab_context.get("governance_status", ""),
        "自动化状态": collab_context.get("automation_status", ""),
        "风险等级": collab_context.get("risk_level", "low"),
        "审批状态": collab_context.get("approval_status", "not_required"),
        "审批决策ID": collab_context.get("approval_decision_id", ""),
        "审批截止时间": collab_context.get("approval_due_at", ""),
        "决策摘要": collab_context.get("decision_summary", ""),
        "最近评论锚点": collab_context.get("last_comment_anchor", ""),
        "最近提交": normalized_event["sha"] or collab_context.get("last_commit", ""),
        "当前阻塞": collab_context.get("blocker", ""),
        "下一步建议": collab_context.get("next_action", ""),
        "远程动作": collab_context.get("remote_action", "none"),
        "远程动作结果": collab_context.get("remote_action_result", ""),
    }

    if normalized_event["event_type"] == "github.pr.changed":
        field_updates["平台状态"] = "checks_pending"
        field_updates["自动化状态"] = "running"
    elif normalized_event["event_type"] == "github.issue.changed":
        field_updates["治理状态"] = "triage_required"
    elif normalized_event["event_type"] == "github.check.changed":
        conclusion = collab_context.get("check_conclusion") or "success"
        field_updates["平台状态"] = "checks_passed" if conclusion == "success" else "checks_failed"
        field_updates["自动化状态"] = "completed"

    return field_updates


def build_github_sync_preview(event_payload, collab_context):
    normalized_event = _normalize_event(event_payload)
    risk_flags = []
    fallback_policy = "confirmed"

    if not collab_context.get("goal_id"):
        risk_flags.append("missing_goal_link")
    if not collab_context.get("task_id"):
        risk_flags.append("missing_task_link")

    if normalized_event["event_type"] == "github.check.changed":
        conclusion = event_payload.get("check_run", {}).get("conclusion", "")
        if conclusion not in {"success", "failure", "cancelled", ""}:
            risk_flags.append("unknown_check_state")
            fallback_policy = "soft_block"

    return {
        "event_summary": {
            "event_type": normalized_event["event_type"],
            "object_type": normalized_event["object_type"],
            "repo": normalized_event["repo"],
            "number": normalized_event["number"],
            "action": normalized_event["action"],
            "title": normalized_event["title"],
        },
        "impacted_records": [
            {
                "task_id": collab_context.get("task_id", ""),
                "goal_id": collab_context.get("goal_id", ""),
                "repo": normalized_event["repo"],
            }
        ],
        "field_updates": _field_updates(normalized_event, collab_context),
        "risk_flags": risk_flags,
        "event_coverage_hit": {
            "event_type": normalized_event["event_type"],
            "action": normalized_event["action"],
            "fallback_policy": fallback_policy,
        },
        "writeback_plan": [
            "event_coverage_check",
            "collab_state_writeback",
            "automation_result_writeback",
            "comment_anchor_writeback",
            "verification_snapshot",
        ],
        "requires_confirmation": True,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_github_sync_preview(payload["event_payload"], payload["collab_context"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_github_sync_preview.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 6: Commit**

```bash
git add github-actions/feishu_collab/github_sync/__init__.py \
        github-actions/feishu_collab/github_sync/build_github_sync_preview.py \
        github-actions/tests/test_build_github_sync_preview.py \
        github-actions/tests/fixtures/github_sync/issue_event.json \
        github-actions/tests/fixtures/github_sync/pr_event.json \
        github-actions/tests/fixtures/github_sync/check_event.json \
        github-actions/tests/fixtures/github_sync/collab_context.json
git commit -m "feat: add github sync preview compiler"
```

## Task 2: Add the Event Coverage Registry and State Projection Adapter

**Files:**
- Create: `github-actions/feishu_collab/github_sync/event_coverage_registry.json`
- Create: `github-actions/tests/test_github_sync_event_registry.py`
- Modify: `github-actions/sync_github_to_feishu.py`

- [ ] **Step 1: Write the failing registry and adapter tests**

Create `github-actions/tests/test_github_sync_event_registry.py`:

```python
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "event_coverage_registry.json"
MODULE_PATH = ROOT / "github-actions" / "sync_github_to_feishu.py"
SPEC = importlib.util.spec_from_file_location("sync_github_to_feishu", MODULE_PATH)


class GithubSyncRegistryTests(unittest.TestCase):
    def load_registry(self):
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_registry_covers_issue_pr_and_check_events(self):
        registry = self.load_registry()
        covered = {item["event_type"] for item in registry["events"]}
        self.assertEqual(
            covered,
            {"github.issue.changed", "github.pr.changed", "github.check.changed"},
        )

    def test_registry_declares_fallback_policy_for_every_event(self):
        registry = self.load_registry()
        for item in registry["events"]:
            self.assertTrue(item["fallback_policy"])
            self.assertTrue(item["supported_actions"])
            self.assertTrue(item["field_mapping"])

    def test_sync_module_exposes_projection_adapter(self):
        module = self.load_module()
        record = module.project_github_collab_state(
            {
                "task_id": "task-001",
                "task_name": "Sync preview",
                "goal_id": "goal-001",
                "repo": "yunya1991/DREAM-AGENT",
                "branch": "feature/test",
                "pr_number": "8",
                "workflow_run_id": "99",
                "implementation_status": "implemented",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running"
            }
        )
        self.assertEqual(record["任务ID"], "task-001")
        self.assertEqual(record["平台状态"], "checks_pending")
        self.assertEqual(record["自动化状态"], "running")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_github_sync_event_registry.py -v
```

Expected: FAIL because the registry file and projection adapter do not exist yet.

- [ ] **Step 3: Add the registry and adapter**

Create `github-actions/feishu_collab/github_sync/event_coverage_registry.json`:

```json
{
  "events": [
    {
      "event_type": "github.issue.changed",
      "supported_actions": ["opened", "edited", "closed", "reopened", "labeled"],
      "field_mapping": {
        "治理状态": "triage_required",
        "实现状态": "backlog"
      },
      "fallback_policy": "soft_block",
      "knowledge_required": true
    },
    {
      "event_type": "github.pr.changed",
      "supported_actions": ["opened", "synchronize", "ready_for_review", "review_requested", "closed", "merged"],
      "field_mapping": {
        "平台状态": "checks_pending",
        "自动化状态": "running"
      },
      "fallback_policy": "soft_block",
      "knowledge_required": true
    },
    {
      "event_type": "github.check.changed",
      "supported_actions": ["requested", "in_progress", "completed"],
      "field_mapping": {
        "平台状态": "checks_passed_or_failed",
        "自动化状态": "completed"
      },
      "fallback_policy": "soft_block",
      "knowledge_required": true
    }
  ]
}
```

Modify `github-actions/sync_github_to_feishu.py`:

```python
import json
import sys


def build_feishu_record(payload):
    return {
        "任务ID": payload.get("task_id", ""),
        "任务名称": payload.get("task_name", ""),
        "目标ID": payload.get("goal_id", ""),
        "仓库": payload.get("repo", ""),
        "分支": payload.get("branch", ""),
        "PR号": payload.get("pr_number", ""),
        "Workflow运行ID": payload.get("workflow_run_id", ""),
        "实现状态": payload.get("implementation_status", ""),
        "平台状态": payload.get("platform_status", ""),
        "治理状态": payload.get("governance_status", ""),
        "自动化状态": payload.get("automation_status", ""),
        "风险等级": payload.get("risk_level", "low"),
        "审批状态": payload.get("approval_status", "not_required"),
        "审批决策ID": payload.get("approval_decision_id", ""),
        "审批截止时间": payload.get("approval_due_at", ""),
        "决策摘要": payload.get("decision_summary", ""),
        "最近评论锚点": payload.get("last_comment_anchor", ""),
        "最近提交": payload.get("last_commit", ""),
        "当前阻塞": payload.get("blocker", ""),
        "下一步建议": payload.get("next_action", ""),
        "远程动作": payload.get("remote_action", "none"),
        "远程动作结果": payload.get("remote_action_result", ""),
    }


def project_github_collab_state(payload):
    return build_feishu_record(payload)


if __name__ == "__main__":
    json.dump(build_feishu_record(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_github_sync_event_registry.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/github_sync/event_coverage_registry.json \
        github-actions/tests/test_github_sync_event_registry.py \
        github-actions/sync_github_to_feishu.py
git commit -m "feat: add github sync event registry"
```

## Task 3: Add the Execution Materializer

**Files:**
- Create: `github-actions/feishu_collab/github_sync/materialize_github_sync_execution.py`
- Create: `github-actions/tests/test_materialize_github_sync_execution.py`

- [ ] **Step 1: Write the failing materialization tests**

Create `github-actions/tests/test_materialize_github_sync_execution.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "materialize_github_sync_execution.py"
SPEC = importlib.util.spec_from_file_location("materialize_github_sync_execution", MODULE_PATH)


class MaterializeGithubSyncExecutionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "event_summary": {
                "event_type": "github.pr.changed",
                "repo": "yunya1991/DREAM-AGENT",
                "action": "synchronize",
                "number": "88"
            },
            "impacted_records": [
                {
                    "task_id": "task-github-sync-001",
                    "goal_id": "goal-collab-sync-001",
                    "repo": "yunya1991/DREAM-AGENT"
                }
            ],
            "field_updates": {
                "任务ID": "task-github-sync-001",
                "平台状态": "checks_pending",
                "自动化状态": "running",
                "治理状态": "review_required",
                "最近评论锚点": "https://github.com/yunya1991/DREAM-AGENT/pull/88#issuecomment-1"
            },
            "risk_flags": [],
            "event_coverage_hit": {
                "event_type": "github.pr.changed",
                "action": "synchronize",
                "fallback_policy": "confirmed"
            },
            "writeback_plan": [
                "event_coverage_check",
                "collab_state_writeback",
                "automation_result_writeback",
                "comment_anchor_writeback",
                "verification_snapshot"
            ],
            "requires_confirmation": True
        }

    def test_materialize_builds_writeback_order_handoff_and_knowledge(self):
        module = self.load_module()
        result = module.materialize_github_sync_execution(self.sample_preview())
        self.assertEqual(
            result["writeback_order"],
            [
                "event_coverage_check",
                "collab_state_writeback",
                "automation_result_writeback",
                "comment_anchor_writeback",
                "verification_snapshot"
            ],
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["knowledge_update"]["asset_type"], "delivery")
        self.assertEqual(result["handoff"]["type"], "stage_handoff")

    def test_materialize_marks_soft_block_when_coverage_gap_exists(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["event_coverage_gap"]
        result = module.materialize_github_sync_execution(preview)
        self.assertEqual(result["status"], "soft_block")

    def test_materialize_marks_degraded_success_when_comment_anchor_is_missing(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["field_updates"]["最近评论锚点"] = ""
        result = module.materialize_github_sync_execution(preview)
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_github_sync_execution.py -v
```

Expected: FAIL because `materialize_github_sync_execution.py` does not exist yet.

- [ ] **Step 3: Write the minimal materializer**

Create `github-actions/feishu_collab/github_sync/materialize_github_sync_execution.py`:

```python
import json
import sys


WRITEBACK_ORDER = [
    "event_coverage_check",
    "collab_state_writeback",
    "automation_result_writeback",
    "comment_anchor_writeback",
    "verification_snapshot",
]


def materialize_github_sync_execution(preview):
    status = "confirmed"
    if "event_coverage_gap" in preview.get("risk_flags", []):
        status = "soft_block"
    elif not preview.get("field_updates", {}).get("最近评论锚点"):
        status = "degraded_success"

    evidence_refs = [
        preview["event_summary"].get("repo", ""),
        preview["event_summary"].get("number", ""),
    ]

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "collab_state": {"fields": preview["field_updates"]},
        "event_summary": preview["event_summary"],
        "verification_seed": {
            "coverage_hit": preview["event_coverage_hit"],
            "risk_flags": preview["risk_flags"],
        },
        "knowledge_update": {
            "asset_type": "delivery",
            "title": "github-sync-writeback-result",
            "summary": f"status={status}",
            "evidence_refs": [item for item in evidence_refs if item],
        },
        "handoff": {
            "type": "stage_handoff",
            "status": status,
            "summary": f"github sync execution {status}",
            "next_action": "review verification result",
            "evidence_refs": [item for item in evidence_refs if item],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_github_sync_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_github_sync_execution.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/github_sync/materialize_github_sync_execution.py \
        github-actions/tests/test_materialize_github_sync_execution.py
git commit -m "feat: add github sync execution materializer"
```

## Task 4: Add Verification and Failure-Mode Handling

**Files:**
- Create: `github-actions/feishu_collab/github_sync/verify_github_sync_projection.py`
- Create: `github-actions/tests/test_verify_github_sync_projection.py`

- [ ] **Step 1: Write the failing verification tests**

Create `github-actions/tests/test_verify_github_sync_projection.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "github_sync" / "verify_github_sync_projection.py"
SPEC = importlib.util.spec_from_file_location("verify_github_sync_projection", MODULE_PATH)


class VerifyGithubSyncProjectionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_fields_and_coverage_are_complete(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "task-1", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.pr.changed", "action": "synchronize"},
            risk_flags=[],
            comment_anchor="https://github.com/example/pull/1#issuecomment-1",
            automation_summary={"status": "running"},
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_hard_block_when_task_record_is_missing(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.pr.changed", "action": "synchronize"},
            risk_flags=[],
            comment_anchor="https://github.com/example/pull/1#issuecomment-1",
            automation_summary={"status": "running"},
        )
        self.assertEqual(result["status"], "hard_block")

    def test_verify_returns_soft_block_when_coverage_gap_is_present(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "task-1", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.check.changed", "action": "completed"},
            risk_flags=["event_coverage_gap"],
            comment_anchor="https://github.com/example/pull/1#issuecomment-1",
            automation_summary={"status": "completed"},
        )
        self.assertEqual(result["status"], "soft_block")

    def test_verify_returns_degraded_success_when_comment_anchor_is_missing(self):
        module = self.load_module()
        result = module.verify_github_sync_projection(
            record_fields={"任务ID": "task-1", "平台状态": "checks_pending"},
            coverage_hit={"event_type": "github.pr.changed", "action": "synchronize"},
            risk_flags=[],
            comment_anchor="",
            automation_summary={"status": "running"},
        )
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_verify_github_sync_projection.py -v
```

Expected: FAIL because `verify_github_sync_projection.py` does not exist yet.

- [ ] **Step 3: Write the minimal verification helper**

Create `github-actions/feishu_collab/github_sync/verify_github_sync_projection.py`:

```python
import json
import sys


def verify_github_sync_projection(record_fields, coverage_hit, risk_flags, comment_anchor, automation_summary):
    if not record_fields.get("任务ID"):
        status = "hard_block"
    elif "event_coverage_gap" in risk_flags:
        status = "soft_block"
    elif not comment_anchor:
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "event_type": coverage_hit.get("event_type", ""),
        "action": coverage_hit.get("action", ""),
        "task_id": record_fields.get("任务ID", ""),
        "automation_status": automation_summary.get("status", ""),
        "comment_anchor_present": bool(comment_anchor),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_github_sync_projection(
            payload["record_fields"],
            payload["coverage_hit"],
            payload["risk_flags"],
            payload["comment_anchor"],
            payload["automation_summary"],
        ),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_verify_github_sync_projection.py -v
```

Expected: PASS with `Ran 4 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/github_sync/verify_github_sync_projection.py \
        github-actions/tests/test_verify_github_sync_projection.py
git commit -m "feat: add github sync verification helper"
```

## Task 5: Package the Skill and Validate the Baseline

**Files:**
- Create: `.trae/skills/feishu-collab-github-sync/SKILL.md`
- Create: `.trae/skills/feishu-collab-github-sync/references/execution-checklist.md`
- Modify: `github-actions/feishu_collab/github_sync/build_github_sync_preview.py`
- Modify: `github-actions/feishu_collab/github_sync/materialize_github_sync_execution.py`
- Modify: `github-actions/feishu_collab/github_sync/verify_github_sync_projection.py`

- [ ] **Step 1: Write the skill package files**

Create `.trae/skills/feishu-collab-github-sync/SKILL.md`:

```md
---
name: "feishu-collab-github-sync"
description: "Projects GitHub issue, PR, and checks events into Feishu collaboration state, then writes back after confirmation with verification and handoff."
---

# Feishu Collaboration GitHub Sync

## When to use

Use this skill when:

- the user needs GitHub issue, PR, or checks status reflected in Feishu collaboration records
- a workflow or event hook has already produced GitHub event payloads
- the user needs preview-before-writeback for engineering collaboration updates
- the flow must emit verification notes, handoff, and `KnowledgeUpdate`

## Inputs

- normalized or raw GitHub event payload
- current Feishu collaboration context
- optional approval context

## Flow

1. build preview
2. review coverage hit and risk flags
3. confirm execution or trigger policy check
4. write back collaboration state
5. verify fields, automation summary, and comment anchor
6. generate handoff and `KnowledgeUpdate`

## Guardrails

- never skip preview
- treat missing task lookup as hard block
- treat event coverage gaps as soft block
- treat missing comment anchor as degraded success
- do not default to remote GitHub mutations in v1
```

Create `.trae/skills/feishu-collab-github-sync/references/execution-checklist.md`:

```md
# Execution Checklist

## Intake Gate

- Confirm the event is issue, PR, or checks related
- Confirm repository and object number are visible
- Confirm Feishu task and goal context are available

## Preview Gate

- Confirm event summary is readable
- Confirm field updates are visible before writeback
- Confirm `event_coverage_hit` is recorded
- Confirm `risk_flags` are recorded

## Writeback Gate

- Event coverage checked first
- Collaboration state writeback recorded
- Automation result writeback recorded
- Comment anchor writeback recorded when present

## Verification Gate

- Task record lookup confirmed
- Coverage gap outcome recorded
- Automation summary recorded
- Handoff and `KnowledgeUpdate` emitted
```

- [ ] **Step 2: Sanity-check the skill files**

Run:

```bash
python3 -c 'from pathlib import Path
for path in [
    Path(".trae/skills/feishu-collab-github-sync/SKILL.md"),
    Path(".trae/skills/feishu-collab-github-sync/references/execution-checklist.md"),
]:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
print("github sync skill files ok")'
```

Expected: `github sync skill files ok`

- [ ] **Step 3: Run the full targeted test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_github_sync_preview.py \
  github-actions/tests/test_github_sync_event_registry.py \
  github-actions/tests/test_materialize_github_sync_execution.py \
  github-actions/tests/test_verify_github_sync_projection.py \
  github-actions/tests/test_sync_github_to_feishu.py -v
```

Expected: all tests PASS.

- [ ] **Step 4: Perform a local dry-run using the fixtures**

Run:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT")
fixture_dir = root / "github-actions" / "tests" / "fixtures" / "github_sync"
payload = {
    "event_payload": json.loads((fixture_dir / "pr_event.json").read_text(encoding="utf-8")),
    "collab_context": json.loads((fixture_dir / "collab_context.json").read_text(encoding="utf-8")),
}

preview_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "github_sync" / "build_github_sync_preview.py")],
    input=json.dumps(payload, ensure_ascii=False),
    text=True,
)
preview = json.loads(preview_out)

execution_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "github_sync" / "materialize_github_sync_execution.py")],
    input=json.dumps(preview, ensure_ascii=False),
    text=True,
)
execution = json.loads(execution_out)

verification_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "github_sync" / "verify_github_sync_projection.py")],
    input=json.dumps(
        {
            "record_fields": execution["collab_state"]["fields"],
            "coverage_hit": preview["event_coverage_hit"],
            "risk_flags": preview["risk_flags"],
            "comment_anchor": execution["collab_state"]["fields"].get("最近评论锚点", ""),
            "automation_summary": {
                "status": execution["collab_state"]["fields"].get("自动化状态", "")
            },
        },
        ensure_ascii=False,
    ),
    text=True,
)
verification = json.loads(verification_out)
print(json.dumps({"preview": preview, "execution": execution, "verification": verification}, ensure_ascii=False, indent=2))
PY
```

Expected:

- preview contains event summary, field updates, risk flags, and coverage hit
- execution contains ordered writeback steps, handoff, and `KnowledgeUpdate`
- verification returns `confirmed`

- [ ] **Step 5: Commit**

```bash
git add .trae/skills/feishu-collab-github-sync/SKILL.md \
        .trae/skills/feishu-collab-github-sync/references/execution-checklist.md \
        github-actions/feishu_collab/github_sync/build_github_sync_preview.py \
        github-actions/feishu_collab/github_sync/materialize_github_sync_execution.py \
        github-actions/feishu_collab/github_sync/verify_github_sync_projection.py \
        github-actions/tests/test_build_github_sync_preview.py \
        github-actions/tests/test_github_sync_event_registry.py \
        github-actions/tests/test_materialize_github_sync_execution.py \
        github-actions/tests/test_verify_github_sync_projection.py \
        github-actions/tests/test_sync_github_to_feishu.py \
        github-actions/tests/fixtures/github_sync/issue_event.json \
        github-actions/tests/fixtures/github_sync/pr_event.json \
        github-actions/tests/fixtures/github_sync/check_event.json \
        github-actions/tests/fixtures/github_sync/collab_context.json \
        github-actions/feishu_collab/github_sync/event_coverage_registry.json \
        github-actions/sync_github_to_feishu.py
git commit -m "test: validate github sync skill baseline"
```

## Self-Review

- Spec coverage:
  - v1 scope `Issue + PR + Checks`: Task 1 and Task 2
  - preview-first flow and field-level explainability: Task 1 and Task 3
  - event coverage registry and downgrade policy: Task 2 and Task 4
  - writeback, verification, handoff, and knowledge output: Task 3, Task 4, and Task 5
  - skill packaging and operator guidance: Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred implementation markers
  - Every code-bearing step includes concrete code or markdown content
  - Every verification step has exact commands and expected outcomes
- Type consistency:
  - Preview/result names stay aligned with the shared system baseline: `ExecutionPreview`, `ExecutionResult`, `KnowledgeUpdate`
  - Event names stay aligned with the approved spec: `github.issue.changed`, `github.pr.changed`, `github.check.changed`
  - Failure statuses stay aligned across preview, materialization, and verification: `hard_block`, `soft_block`, `degraded_success`, `confirmed`
