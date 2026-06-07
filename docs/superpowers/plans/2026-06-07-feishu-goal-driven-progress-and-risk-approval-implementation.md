# 飞书目标驱动进度监控与风险审批 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 GitHub x 飞书协作闭环基础上，新增“目标推进表 + 风险审批闸门 + 审批超时保守策略”，让飞书同时承接目标驱动监控和关键决策拍板。

**Architecture:** 先扩展现有任务监控契约，把 `goal_id` 与审批字段纳入 GitHub -> 飞书同步真源；再新增一个纯 Python 的目标聚合器与风险判定器，用于决定何时创建审批、何时进入等待决策；最后接入飞书审批实例创建 / 查询能力，并用一个单独的 orchestrator 串起“任务状态同步 -> 风险判定 -> 审批创建/回读 -> 目标表聚合”的最小周期。

**Tech Stack:** Python 3 standard library, unittest, urllib.request, JSON payload scripts, existing `lark-cli` wrapper patterns, existing GitHub Actions repo scripts.

---

## File Structure

### Create

- `github-actions/build_goal_progress_record.py`
  - 把任务列表聚合成目标推进记录。
- `github-actions/evaluate_risk_approval_gate.py`
  - 判断任务是否需要进入风险审批。
- `github-actions/feishu_approval_api.py`
  - 通过飞书开放平台创建和查询审批实例。
- `github-actions/run_goal_progress_approval_cycle.py`
  - 编排任务同步、审批创建/回读、目标聚合的最小周期。
- `github-actions/tests/test_build_goal_progress_record.py`
- `github-actions/tests/test_evaluate_risk_approval_gate.py`
- `github-actions/tests/test_feishu_approval_api.py`
- `github-actions/tests/test_run_goal_progress_approval_cycle.py`

### Modify

- `github-actions/sync_github_to_feishu.py`
  - 扩展任务监控记录，纳入 `goal_id` 和审批字段。
- `github-actions/update_agent_ledger.py`
  - 持久化新增的目标 / 审批相关默认字段。
- `github-actions/tests/test_sync_github_to_feishu.py`
- `github-actions/tests/test_update_agent_ledger.py`
- `github-actions/README.md`
  - 登记新增脚本职责。
- `README.md`
- `docs/README.md`
- `docs/04-ENGINEERING-INDEX.md`

---

## Task 1: 扩展任务监控契约

**Files:**
- Modify: `github-actions/sync_github_to_feishu.py`
- Modify: `github-actions/update_agent_ledger.py`
- Modify: `github-actions/tests/test_sync_github_to_feishu.py`
- Modify: `github-actions/tests/test_update_agent_ledger.py`

- [ ] **Step 1: 先给任务同步脚本补失败测试**

Append to `github-actions/tests/test_sync_github_to_feishu.py`:

```python
    def test_build_feishu_record_includes_goal_and_approval_fields(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_feishu_record(
            {
                "task_id": "task-approval-001",
                "task_name": "风险审批样例任务",
                "goal_id": "goal-collab-001",
                "repo": "yunya1991/DREAM-AGENT",
                "branch": "feature/risk-approval",
                "pr_number": "9",
                "implementation_status": "implemented",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
                "risk_level": "high",
                "approval_status": "pending",
                "approval_decision_id": "decision-001",
                "approval_due_at": "2026-06-07T16:00:00Z",
                "decision_summary": "waiting_for_choice",
            }
        )
        self.assertEqual(record["目标ID"], "goal-collab-001")
        self.assertEqual(record["风险等级"], "high")
        self.assertEqual(record["审批状态"], "pending")
        self.assertEqual(record["审批决策ID"], "decision-001")
        self.assertEqual(record["审批截止时间"], "2026-06-07T16:00:00Z")
        self.assertEqual(record["决策摘要"], "waiting_for_choice")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_sync_github_to_feishu.py -v
```

Expected:

- FAIL because the new fields are not yet mapped

- [ ] **Step 3: 扩展任务监控记录映射**

Update `github-actions/sync_github_to_feishu.py`:

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


if __name__ == "__main__":
    json.dump(build_feishu_record(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 给 ledger 默认值补失败测试**

Append to `github-actions/tests/test_update_agent_ledger.py`:

```python
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
```

- [ ] **Step 5: 扩展 ledger 默认字段**

Update `github-actions/update_agent_ledger.py`:

```python
def normalize_closure_status(task):
    task["implementation_status"] = task.get("implementation_status", "planned")
    task["platform_status"] = task.get("platform_status", "no_pr")
    task["governance_status"] = task.get("governance_status", "draft")
    task["automation_status"] = task.get("automation_status", "idle")
    task["goal_id"] = task.get("goal_id", "")
    task["risk_level"] = task.get("risk_level", "low")
    task["approval_status"] = task.get("approval_status", "not_required")
    task["approval_decision_id"] = task.get("approval_decision_id", "")
    task["approval_due_at"] = task.get("approval_due_at", "")
    task["decision_summary"] = task.get("decision_summary", "")
    return task
```

- [ ] **Step 6: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_sync_github_to_feishu.py github-actions/tests/test_update_agent_ledger.py -v
```

Expected:

- PASS for both suites

- [ ] **Step 7: Commit**

```bash
git add github-actions/sync_github_to_feishu.py github-actions/update_agent_ledger.py github-actions/tests/test_sync_github_to_feishu.py github-actions/tests/test_update_agent_ledger.py
git commit -m "feat: extend feishu task monitor contract"
```

---

## Task 2: 构建目标推进聚合器

**Files:**
- Create: `github-actions/build_goal_progress_record.py`
- Create: `github-actions/tests/test_build_goal_progress_record.py`

- [ ] **Step 1: 先写目标聚合失败测试**

Create `github-actions/tests/test_build_goal_progress_record.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_goal_progress_record.py"
SPEC = importlib.util.spec_from_file_location("build_goal_progress_record", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class BuildGoalProgressRecordTests(unittest.TestCase):
    def test_waiting_decision_goal_wins_over_active(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {
                "goal_id": "goal-collab-001",
                "goal_name": "协作闭环修复",
                "goal_owner": "governance-agent",
                "current_phase": "risk-approval",
            },
            [
                {
                    "task_id": "task-1",
                    "approval_status": "pending",
                    "platform_status": "checks_pending",
                    "governance_status": "review_required",
                    "blocker": "waiting for decision",
                    "decision_summary": "choose rollback-safe path",
                },
                {
                    "task_id": "task-2",
                    "approval_status": "not_required",
                    "platform_status": "checks_green",
                    "governance_status": "ready",
                    "blocker": "",
                    "decision_summary": "",
                },
            ],
        )
        self.assertEqual(record["goal_status"], "waiting_decision")
        self.assertEqual(record["risk_level"], "high")
        self.assertEqual(record["key_blocker"], "waiting for decision")
        self.assertEqual(record["latest_decision_summary"], "choose rollback-safe path")

    def test_released_goal_requires_all_tasks_released(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_goal_record(
            {"goal_id": "goal-release-001", "goal_name": "release"},
            [
                {"task_id": "task-a", "governance_status": "released", "approval_status": "executed"},
                {"task_id": "task-b", "governance_status": "released", "approval_status": "executed"},
            ],
        )
        self.assertEqual(record["goal_status"], "released")
        self.assertEqual(record["goal_progress"], 100)
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_goal_progress_record.py -v
```

Expected:

- FAIL because `build_goal_progress_record.py` does not exist

- [ ] **Step 3: 实现目标聚合器**

Create `github-actions/build_goal_progress_record.py`:

```python
import json
import sys


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def choose_risk(tasks):
    max_name = "low"
    for task in tasks:
        candidate = task.get("risk_level", "low")
        if RISK_ORDER.get(candidate, 0) > RISK_ORDER.get(max_name, 0):
            max_name = candidate
    return max_name


def compute_goal_status(tasks):
    if any(task.get("approval_status") in {"pending", "timeout"} for task in tasks):
        return "waiting_decision"
    if any(task.get("platform_status") == "checks_failing" for task in tasks):
        return "blocked"
    if any(task.get("governance_status") == "blocked" for task in tasks):
        return "blocked"
    if tasks and all(task.get("governance_status") == "released" for task in tasks):
        return "released"
    return "active"


def compute_goal_progress(tasks):
    if not tasks:
        return 0
    completed = sum(1 for task in tasks if task.get("governance_status") in {"ready", "released"})
    return int(completed * 100 / len(tasks))


def first_non_empty(tasks, key):
    for task in tasks:
        value = task.get(key, "")
        if value:
            return value
    return ""


def build_goal_record(goal, tasks):
    return {
        "goal_id": goal.get("goal_id", ""),
        "goal_name": goal.get("goal_name", ""),
        "goal_owner": goal.get("goal_owner", ""),
        "goal_status": compute_goal_status(tasks),
        "goal_progress": compute_goal_progress(tasks),
        "current_phase": goal.get("current_phase", ""),
        "key_blocker": first_non_empty(tasks, "blocker"),
        "next_milestone": goal.get("next_milestone", ""),
        "risk_level": choose_risk(tasks),
        "latest_decision_summary": first_non_empty(tasks, "decision_summary"),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_goal_record(payload.get("goal", {}), payload.get("tasks", [])),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_goal_progress_record.py -v
```

Expected:

- PASS for both tests

- [ ] **Step 5: Commit**

```bash
git add github-actions/build_goal_progress_record.py github-actions/tests/test_build_goal_progress_record.py
git commit -m "feat: add goal progress projection"
```

---

## Task 3: 构建风险审批判定器

**Files:**
- Create: `github-actions/evaluate_risk_approval_gate.py`
- Create: `github-actions/tests/test_evaluate_risk_approval_gate.py`

- [ ] **Step 1: 先写风险审批判定失败测试**

Create `github-actions/tests/test_evaluate_risk_approval_gate.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "evaluate_risk_approval_gate.py"
SPEC = importlib.util.spec_from_file_location("evaluate_risk_approval_gate", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class EvaluateRiskApprovalGateTests(unittest.TestCase):
    def test_low_risk_fix_does_not_require_approval(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.evaluate_gate(
            {
                "task_id": "task-low-001",
                "risk_level": "low",
                "change_scope": "patch_fix",
                "requested_action": "continue",
            }
        )
        self.assertFalse(result["requires_approval"])
        self.assertEqual(result["approval_status"], "not_required")

    def test_release_handoff_requires_approval(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.evaluate_gate(
            {
                "task_id": "task-high-001",
                "risk_level": "high",
                "change_scope": "release_handoff",
                "requested_action": "release",
            }
        )
        self.assertTrue(result["requires_approval"])
        self.assertEqual(result["approval_status"], "pending")
        self.assertEqual(result["trigger_reason"], "release_handoff")
        self.assertEqual(result["timeout_fallback"]["action"], "pause")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_evaluate_risk_approval_gate.py -v
```

Expected:

- FAIL because `evaluate_risk_approval_gate.py` does not exist

- [ ] **Step 3: 实现风险审批判定器**

Create `github-actions/evaluate_risk_approval_gate.py`:

```python
import json
import sys


HIGH_RISK_SCOPES = {
    "multi_agent_expansion",
    "release_handoff",
    "rollback",
    "high_cost_retry",
    "goal_switch",
}


def build_default_options(task):
    return [
        {
            "key": "recommended",
            "label": "按推荐方案继续",
            "risk": task.get("risk_level", "low"),
            "rollback": "use existing version anchor",
        },
        {
            "key": "pause",
            "label": "暂停并等待人工接手",
            "risk": "low",
            "rollback": "no-op",
        },
    ]


def evaluate_gate(task):
    change_scope = task.get("change_scope", "")
    risk_level = task.get("risk_level", "low")
    requires_approval = risk_level in {"high", "critical"} or change_scope in HIGH_RISK_SCOPES
    if not requires_approval:
        return {
            "requires_approval": False,
            "approval_status": "not_required",
            "trigger_reason": "",
            "recommended_option": "auto_continue",
            "options": [],
            "timeout_fallback": {"action": "auto_continue"},
        }

    return {
        "requires_approval": True,
        "approval_status": "pending",
        "trigger_reason": change_scope or "high_risk_change",
        "recommended_option": "recommended",
        "options": build_default_options(task),
        "timeout_fallback": {"action": "pause"},
    }


if __name__ == "__main__":
    json.dump(evaluate_gate(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_evaluate_risk_approval_gate.py -v
```

Expected:

- PASS for both tests

- [ ] **Step 5: Commit**

```bash
git add github-actions/evaluate_risk_approval_gate.py github-actions/tests/test_evaluate_risk_approval_gate.py
git commit -m "feat: add risk approval gate evaluator"
```

---

## Task 4: 接入飞书审批实例创建与结果解析

**Files:**
- Create: `github-actions/feishu_approval_api.py`
- Create: `github-actions/tests/test_feishu_approval_api.py`

- [ ] **Step 1: 先写审批 API 失败测试**

Create `github-actions/tests/test_feishu_approval_api.py`:

```python
import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_approval_api.py"
SPEC = importlib.util.spec_from_file_location("feishu_approval_api", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class FeishuApprovalApiTests(unittest.TestCase):
    def test_build_create_instance_body_keeps_external_id_and_form(self):
        SPEC.loader.exec_module(MODULE)
        body = MODULE.build_create_instance_body(
            approval_code="approval-code-001",
            user_id="ou_xxx",
            instance_external_id="decision-001",
            form=[{"id": "decision_summary", "type": "textarea", "value": "pick A"}],
        )
        self.assertEqual(body["approval_code"], "approval-code-001")
        self.assertEqual(body["user_id"], "ou_xxx")
        self.assertEqual(body["instance_external_id"], "decision-001")
        self.assertEqual(body["form"][0]["value"], "pick A")

    @mock.patch("urllib.request.urlopen")
    def test_create_instance_uses_instances_endpoint(self, mock_urlopen):
        SPEC.loader.exec_module(MODULE)
        mock_urlopen.return_value.__enter__.return_value = io.BytesIO(
            json.dumps({"data": {"instance_code": "ins_001"}}).encode("utf-8")
        )
        result = MODULE.create_instance(
            tenant_access_token="tenant-token",
            body={"approval_code": "approval-code-001"},
        )
        self.assertEqual(result["data"]["instance_code"], "ins_001")
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.full_url, "https://open.feishu.cn/open-apis/approval/v4/instances")
        self.assertEqual(request.get_method(), "POST")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_approval_api.py -v
```

Expected:

- FAIL because `feishu_approval_api.py` does not exist

- [ ] **Step 3: 实现审批 API 助手**

Create `github-actions/feishu_approval_api.py`:

```python
import json
import urllib.request


APPROVAL_BASE_URL = "https://open.feishu.cn/open-apis/approval/v4"


def build_create_instance_body(approval_code, user_id, instance_external_id, form):
    return {
        "approval_code": approval_code,
        "user_id": user_id,
        "instance_external_id": instance_external_id,
        "form": form,
    }


def request_json(url, method, token, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method=method,
    )
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def create_instance(tenant_access_token, body):
    return request_json(
        f"{APPROVAL_BASE_URL}/instances",
        "POST",
        tenant_access_token,
        body=body,
    )


def get_instance(tenant_access_token, instance_code):
    return request_json(
        f"{APPROVAL_BASE_URL}/instances/{instance_code}",
        "GET",
        tenant_access_token,
    )
```

- [ ] **Step 4: 再写状态解析测试**

Append to `github-actions/tests/test_feishu_approval_api.py`:

```python
    def test_resolve_instance_status_maps_to_task_updates(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.resolve_instance_status(
            {
                "status": "APPROVED",
                "instance_code": "ins_001",
            },
            decision_id="decision-001",
        )
        self.assertEqual(result["approval_status"], "approved")
        self.assertEqual(result["automation_status"], "running")
        self.assertEqual(result["decision_summary"], "approved:decision-001")
```

- [ ] **Step 5: 实现状态解析**

Append to `github-actions/feishu_approval_api.py`:

```python
def resolve_instance_status(instance, decision_id):
    status = instance.get("status", "PENDING")
    if status == "APPROVED":
        return {
            "approval_status": "approved",
            "automation_status": "running",
            "decision_summary": f"approved:{decision_id}",
        }
    if status == "REJECTED":
        return {
            "approval_status": "rejected",
            "automation_status": "paused",
            "decision_summary": f"rejected:{decision_id}",
        }
    return {
        "approval_status": "pending",
        "automation_status": "paused",
        "decision_summary": f"pending:{decision_id}",
    }
```

- [ ] **Step 6: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_approval_api.py -v
```

Expected:

- PASS for body building, instance creation request, and status resolution

- [ ] **Step 7: Commit**

```bash
git add github-actions/feishu_approval_api.py github-actions/tests/test_feishu_approval_api.py
git commit -m "feat: add feishu approval api bridge"
```

---

## Task 5: 串起目标进度与风险审批周期

**Files:**
- Create: `github-actions/run_goal_progress_approval_cycle.py`
- Create: `github-actions/tests/test_run_goal_progress_approval_cycle.py`

- [ ] **Step 1: 先写 orchestrator 失败测试**

Create `github-actions/tests/test_run_goal_progress_approval_cycle.py`:

```python
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_goal_progress_approval_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_goal_progress_approval_cycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class RunGoalProgressApprovalCycleTests(unittest.TestCase):
    def test_creates_pending_approval_for_high_risk_task(self):
        SPEC.loader.exec_module(MODULE)
        with mock.patch.object(MODULE.GATE, "evaluate_gate", return_value={
            "requires_approval": True,
            "approval_status": "pending",
            "trigger_reason": "release_handoff",
            "recommended_option": "recommended",
            "options": [{"key": "recommended"}],
            "timeout_fallback": {"action": "pause"},
        }), mock.patch.object(MODULE.APPROVAL_API, "create_instance", return_value={
            "data": {"instance_code": "ins_001"}
        }):
            result = MODULE.run_cycle(
                task_payload={
                    "task_id": "task-risk-001",
                    "goal_id": "goal-collab-001",
                    "risk_level": "high",
                    "change_scope": "release_handoff",
                },
                goal_payload={"goal_id": "goal-collab-001", "goal_name": "协作闭环"},
                sibling_tasks=[],
                tenant_access_token="tenant-token",
                approval_code="approval-code-001",
                applicant_user_id="ou_xxx",
            )
        self.assertEqual(result["task_updates"]["approval_status"], "pending")
        self.assertEqual(result["task_updates"]["approval_decision_id"], "task-risk-001")
        self.assertEqual(result["task_updates"]["decision_summary"], "approval_created")
        self.assertEqual(result["task_updates"]["approval_instance_code"], "ins_001")

    def test_approved_instance_resumes_running(self):
        SPEC.loader.exec_module(MODULE)
        with mock.patch.object(MODULE.GATE, "evaluate_gate", return_value={
            "requires_approval": True,
            "approval_status": "pending",
            "trigger_reason": "release_handoff",
            "recommended_option": "recommended",
            "options": [{"key": "recommended"}],
            "timeout_fallback": {"action": "pause"},
        }), mock.patch.object(MODULE.APPROVAL_API, "get_instance", return_value={
            "status": "APPROVED",
            "instance_code": "ins_001",
        }):
            result = MODULE.run_cycle(
                task_payload={
                    "task_id": "task-risk-001",
                    "goal_id": "goal-collab-001",
                    "risk_level": "high",
                    "change_scope": "release_handoff",
                    "approval_instance_code": "ins_001",
                },
                goal_payload={"goal_id": "goal-collab-001", "goal_name": "协作闭环"},
                sibling_tasks=[],
                tenant_access_token="tenant-token",
                approval_code="approval-code-001",
                applicant_user_id="ou_xxx",
            )
        self.assertEqual(result["task_updates"]["approval_status"], "approved")
        self.assertEqual(result["task_updates"]["automation_status"], "running")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_goal_progress_approval_cycle.py -v
```

Expected:

- FAIL because `run_goal_progress_approval_cycle.py` does not exist

- [ ] **Step 3: 实现 orchestrator**

Create `github-actions/run_goal_progress_approval_cycle.py`:

```python
import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent


def load_module(name, file_name):
    path = HERE / file_name
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SYNC = load_module("sync_github_to_feishu", "sync_github_to_feishu.py")
GOAL = load_module("build_goal_progress_record", "build_goal_progress_record.py")
GATE = load_module("evaluate_risk_approval_gate", "evaluate_risk_approval_gate.py")
APPROVAL_API = load_module("feishu_approval_api", "feishu_approval_api.py")


def run_cycle(task_payload, goal_payload, sibling_tasks, tenant_access_token, approval_code, applicant_user_id):
    gate = GATE.evaluate_gate(task_payload)
    task_updates = dict(task_payload)

    if not gate["requires_approval"]:
        task_updates["approval_status"] = "not_required"
        task_updates["decision_summary"] = "auto_continue"
    elif task_payload.get("approval_instance_code"):
        resolved = APPROVAL_API.resolve_instance_status(
            APPROVAL_API.get_instance(tenant_access_token, task_payload["approval_instance_code"]),
            decision_id=task_payload["task_id"],
        )
        task_updates.update(resolved)
    else:
        approval_body = APPROVAL_API.build_create_instance_body(
            approval_code=approval_code,
            user_id=applicant_user_id,
            instance_external_id=task_payload["task_id"],
            form=[
                {"id": "decision_id", "type": "textarea", "value": task_payload["task_id"]},
                {"id": "trigger_reason", "type": "textarea", "value": gate["trigger_reason"]},
            ],
        )
        created = APPROVAL_API.create_instance(tenant_access_token, approval_body)
        task_updates["approval_status"] = "pending"
        task_updates["approval_decision_id"] = task_payload["task_id"]
        task_updates["approval_instance_code"] = created["data"]["instance_code"]
        task_updates["decision_summary"] = "approval_created"
        task_updates["automation_status"] = "paused"

    goal_record = GOAL.build_goal_record(
        goal_payload,
        [task_updates, *sibling_tasks],
    )

    return {
        "task_record": SYNC.build_feishu_record(task_updates),
        "task_updates": task_updates,
        "goal_record": goal_record,
    }
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_goal_progress_approval_cycle.py -v
```

Expected:

- PASS for approval creation and approval resolution paths

- [ ] **Step 5: Commit**

```bash
git add github-actions/run_goal_progress_approval_cycle.py github-actions/tests/test_run_goal_progress_approval_cycle.py
git commit -m "feat: add goal progress approval cycle"
```

---

## Task 6: 文档登记与最小回归

**Files:**
- Modify: `github-actions/README.md`
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/04-ENGINEERING-INDEX.md`
- Modify: `docs/superpowers/plans/2026-06-07-feishu-goal-driven-progress-and-risk-approval-implementation.md`

- [x] **Step 1: 更新脚本与文档入口**

Add to `github-actions/README.md`:

```md
- `build_goal_progress_record.py`：把任务状态聚合成目标推进记录
- `evaluate_risk_approval_gate.py`：判断任务是否需要风险审批
- `feishu_approval_api.py`：创建和查询飞书审批实例
- `run_goal_progress_approval_cycle.py`：串起目标推进与风险审批周期
```

Add to `README.md`:

```md
- `docs/superpowers/specs/2026-06-07-feishu-goal-driven-progress-and-risk-approval-design.md` — 飞书目标驱动进度监控与风险审批设计
- `docs/superpowers/plans/2026-06-07-feishu-goal-driven-progress-and-risk-approval-implementation.md` — 对应实施计划
```

Add to `docs/README.md`:

```md
- `docs/superpowers/specs/2026-06-07-feishu-goal-driven-progress-and-risk-approval-design.md`
- `docs/superpowers/plans/2026-06-07-feishu-goal-driven-progress-and-risk-approval-implementation.md`
```

Add to `docs/04-ENGINEERING-INDEX.md`:

```md
### 飞书目标驱动进度监控与风险审批

- 设计：`docs/superpowers/specs/2026-06-07-feishu-goal-driven-progress-and-risk-approval-design.md`
- 计划：`docs/superpowers/plans/2026-06-07-feishu-goal-driven-progress-and-risk-approval-implementation.md`
```

- [x] **Step 2: 运行最小回归**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_sync_github_to_feishu.py \
  github-actions/tests/test_update_agent_ledger.py \
  github-actions/tests/test_build_goal_progress_record.py \
  github-actions/tests/test_evaluate_risk_approval_gate.py \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_run_goal_progress_approval_cycle.py -v
git diff --check
```

Expected:

- All selected tests pass
- `git diff --check` outputs nothing

- [ ] **Step 3: Commit**

Per current execution request, do not commit in this run.

```bash
git add github-actions/README.md README.md docs/README.md docs/04-ENGINEERING-INDEX.md docs/superpowers/plans/2026-06-07-feishu-goal-driven-progress-and-risk-approval-implementation.md
git commit -m "docs: register feishu goal approval plan"
```

---

## Self-Review

### Spec coverage

- 目标层 + 任务层双层可视化：Task 1 + Task 2
- 高风险分叉识别：Task 3
- 审批实例创建与回读：Task 4
- 审批超时/等待决策状态收口：Task 3 + Task 5
- 目标推进与任务推进串联：Task 2 + Task 5
- 文档与入口登记：Task 6

### Placeholder scan

- 未使用 `TODO` / `TBD`
- 每个任务都包含明确文件、代码块、命令和预期结果
- 未引用未定义的函数名或脚本名

### Type consistency

- 统一使用：
  - `goal_id`
  - `risk_level`
  - `approval_status`
  - `approval_decision_id`
  - `approval_due_at`
  - `decision_summary`
  - `approval_instance_code`

---

Plan complete and saved to `docs/superpowers/plans/2026-06-07-feishu-goal-driven-progress-and-risk-approval-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
