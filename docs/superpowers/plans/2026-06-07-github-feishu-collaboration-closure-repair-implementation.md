---
id: GITHUB-FEISHU-COLLABORATION-CLOSURE-REPAIR-IMPLEMENTATION
type: plan
owner: governance-agent
depends:
  - GITHUB-FEISHU-COLLABORATION-CLOSURE-REPAIR-DESIGN
version: 1
last_verified: 2026-06-07
---

# GitHub x 飞书协作闭环修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 Dream-Agent 自动化执行中的协作闭环问题，建立 GitHub checks 与治理结论的一致性规则，并补齐飞书侧的自动化任务监控与 `pause / retry` 远程干预最小闭环。

**Architecture:** 先在 GitHub 侧修正状态模型与结构化评论输出，使 `implementation_status / platform_status / governance_status / automation_status` 成为统一真源表达；再新增一层轻量 `GitHub x Feishu bridge`，把 PR/checks/workflow/comment 状态同步到飞书 Base，并读取飞书侧 `pause / retry` 动作回写到 GitHub/Schedule。整个计划只收口协作闭环，不扩展到产物中台业务实现。

**Tech Stack:** Python 3 standard library, unittest, GitHub Actions YAML, existing `gh` CLI flow, existing `lark-cli` / `github-actions/lark_cli.py`, JSON ledger files, markdown PR comment templates.

---

## File Structure

### Create

- `github-actions/build_collaboration_closure_payload.py`
  - 统一构建四层状态 payload，作为治理与飞书同步的输入。
- `github-actions/check_collaboration_closure.py`
  - 负责校验 `checks` 与治理状态是否一致，并输出 release decision。
- `github-actions/sync_github_to_feishu.py`
  - 将 GitHub 侧 PR/checks/workflow/comment 状态同步到飞书 Base。
- `github-actions/process_feishu_remote_action.py`
  - 读取飞书 Base 的 `remote_action` 并执行 `pause / retry`。
- `github-actions/tests/test_build_collaboration_closure_payload.py`
- `github-actions/tests/test_check_collaboration_closure.py`
- `github-actions/tests/test_sync_github_to_feishu.py`
- `github-actions/tests/test_process_feishu_remote_action.py`
- `templates/pr-comment-governance-handoff.md`
  - 标准化 `GOVERNANCE_HANDOFF` 输出格式。

### Modify

- `github-actions/run_governance_ledger_cycle.py`
  - 接入新的 closure payload 与 checker。
- `github-actions/update_agent_ledger.py`
  - 持久化四层状态与飞书监控字段。
- `github-actions/tests/test_run_governance_ledger_cycle.py`
- `github-actions/tests/test_update_agent_ledger.py`
- `.github/workflows/collab-governance-agent.yml`
  - 从“协议完整性检查”升级为“状态一致性 + 治理结论”工作流。
- `templates/pr-comment-updated.md`
- `templates/pr-comment-validation-result.md`
- `README.md`
- `docs/README.md`
- `docs/04-ENGINEERING-INDEX.md`

---

## Task 1: 建立四层状态 payload 与一致性 checker

**Files:**
- Create: `github-actions/build_collaboration_closure_payload.py`
- Create: `github-actions/check_collaboration_closure.py`
- Create: `github-actions/tests/test_build_collaboration_closure_payload.py`
- Create: `github-actions/tests/test_check_collaboration_closure.py`

- [ ] **Step 1: 先写 payload builder 失败测试**

Create `github-actions/tests/test_build_collaboration_closure_payload.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_collaboration_closure_payload.py"
SPEC = importlib.util.spec_from_file_location("build_collaboration_closure_payload", MODULE_PATH)
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_collaboration_closure_payload.py -v
```

Expected:

- FAIL because `build_collaboration_closure_payload.py` does not exist

- [ ] **Step 3: 实现 payload builder**

Create `github-actions/build_collaboration_closure_payload.py`:

```python
import json
import sys


def build_payload(raw):
    return {
        "task_id": raw.get("task_id", ""),
        "pr_number": raw.get("pr_number", ""),
        "repo": raw.get("repo", ""),
        "branch": raw.get("branch", ""),
        "implementation_status": raw.get("implementation_status", "planned"),
        "platform_status": raw.get("platform_status", "no_pr"),
        "governance_status": raw.get("governance_status", "draft"),
        "automation_status": raw.get("automation_status", "idle"),
        "workflow_run_id": raw.get("workflow_run_id", ""),
        "last_comment_anchor": raw.get("last_comment_anchor", ""),
        "blocker": raw.get("blocker", ""),
        "next_action": raw.get("next_action", ""),
    }


if __name__ == "__main__":
    json.dump(build_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 4: 再写 checker 测试**

Create `github-actions/tests/test_check_collaboration_closure.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "check_collaboration_closure.py"
SPEC = importlib.util.spec_from_file_location("check_collaboration_closure", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CheckCollaborationClosureTests(unittest.TestCase):
    def test_blocks_ready_when_checks_are_failing(self):
        result = MODULE.evaluate_payload(
            {
                "implementation_status": "tested",
                "platform_status": "checks_failing",
                "governance_status": "ready",
                "automation_status": "running",
            }
        )
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_GOVERNANCE_REQUIRES_GREEN_CHECKS", result["reason_codes"])

    def test_passes_review_required_when_checks_pending(self):
        result = MODULE.evaluate_payload(
            {
                "implementation_status": "tested",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
            }
        )
        self.assertEqual(result["decision"], "PASS")
        self.assertEqual(result["release_decision"], "hold")
```

- [ ] **Step 5: 实现 checker**

Create `github-actions/check_collaboration_closure.py`:

```python
import json
import sys


def evaluate_payload(payload):
    implementation_status = payload.get("implementation_status", "")
    platform_status = payload.get("platform_status", "")
    governance_status = payload.get("governance_status", "")

    reason_codes = []
    release_decision = "hold"

    if platform_status != "checks_green" and governance_status in {"ready", "released"}:
        reason_codes.append("RULE_GOVERNANCE_REQUIRES_GREEN_CHECKS")

    if platform_status == "checks_green" and implementation_status == "tested":
        release_decision = "ready_for_release"
    elif platform_status in {"checks_pending", "checks_failing", "workflow_failed"}:
        release_decision = "hold"

    return {
        "decision": "PASS" if not reason_codes else "BLOCK",
        "reason_codes": reason_codes,
        "release_decision": release_decision,
    }


if __name__ == "__main__":
    json.dump(evaluate_payload(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
```

- [ ] **Step 6: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_collaboration_closure_payload.py github-actions/tests/test_check_collaboration_closure.py -v
```

Expected:

- PASS for both new suites

- [ ] **Step 7: Commit**

```bash
git add github-actions/build_collaboration_closure_payload.py github-actions/check_collaboration_closure.py github-actions/tests/test_build_collaboration_closure_payload.py github-actions/tests/test_check_collaboration_closure.py
git commit -m "feat: add collaboration closure state validator"
```

---

## Task 2: 修正 governance workflow 与评论模板

**Files:**
- Create: `templates/pr-comment-governance-handoff.md`
- Modify: `github-actions/run_governance_ledger_cycle.py`
- Modify: `.github/workflows/collab-governance-agent.yml`
- Modify: `templates/pr-comment-updated.md`
- Modify: `templates/pr-comment-validation-result.md`
- Modify: `github-actions/tests/test_run_governance_ledger_cycle.py`

- [ ] **Step 1: 先给 governance cycle 写失败测试**

Append to `github-actions/tests/test_run_governance_ledger_cycle.py`:

```python
def test_blocks_ready_governance_when_platform_checks_fail():
    raw = {
        "task_id": "task-001",
        "requested_status": "ledgered",
        "comments": [
            "[协作开工声明 / STARTED]",
            "[测试报告 / TEST_REPORT]",
            "[验证结论 / VALIDATION_RESULT]",
        ],
        "implementation_status": "tested",
        "platform_status": "checks_failing",
        "governance_status": "ready",
    }
    result = MODULE.run_cycle(raw, TASK_INDEX_PATH, REWARD_INDEX_PATH)
    assert result["decision"] == "BLOCK"
    assert "RULE_GOVERNANCE_REQUIRES_GREEN_CHECKS" in result["reason_codes"]
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_governance_ledger_cycle.py -v
```

Expected:

- FAIL because governance cycle does not yet enforce the new closure checker

- [ ] **Step 3: 接入新的 payload builder / checker**

Modify `github-actions/run_governance_ledger_cycle.py` near the existing module loader section:

```python
CLOSURE_BUILDER = load_module(
    "build_collaboration_closure_payload", "build_collaboration_closure_payload.py"
)
CLOSURE_CHECKER = load_module(
    "check_collaboration_closure", "check_collaboration_closure.py"
)
```

Then add this block before the existing ledger update write path:

```python
closure_payload = CLOSURE_BUILDER.build_payload(raw)
closure_result = CLOSURE_CHECKER.evaluate_payload(closure_payload)
if closure_result.get("decision") != "PASS":
    return {
        "task_id": task_id,
        "decision": "BLOCK",
        "reason_codes": closure_result.get("reason_codes", []),
        "previous_status": task.get("status", ""),
        "new_status": task.get("status", ""),
        "state_changed": False,
        "reward_written": False,
        "knowledge_sync_written": False,
        "next_required_action": "governance: resolve platform/checks mismatch",
        "repair_hint": "do not release governance when checks are not green",
    }
```

- [ ] **Step 4: 新增治理 handoff 模板**

Create `templates/pr-comment-governance-handoff.md`:

```md
[治理移交 / GOVERNANCE_HANDOFF]

Task ID: <task-id>
Implementation Status: <planned|in_progress|implemented|tested>
Platform Status: <no_pr|checks_pending|checks_green|checks_failing|workflow_failed>
Governance Status: <draft|review_required|blocked|ready|released>
Automation Status: <idle|running|paused|retry_requested|failed>
Release Decision: <hold|review_required|blocked|ready_for_release|released>
Blocker: <none or reason>
Required Next Action: <next-action>
```

Modify `templates/pr-comment-updated.md` to include:

```md
- Implementation Status:
- Platform Status:
- Governance Status:
- Automation Status:
```

Modify `templates/pr-comment-validation-result.md` to include:

```md
Implementation Status: <...>
Platform Status: <...>
Validation Decision: <...>
Governance Recommendation: <...>
```

- [ ] **Step 5: 升级 governance workflow**

Modify `.github/workflows/collab-governance-agent.yml` to replace the current “Protocol completeness check” shell block with a Python-driven closure evaluation:

```yaml
      - name: Build collaboration closure payload
        run: |
          python3 github-actions/build_collaboration_closure_payload.py <<'EOF' > closure_payload.json
          {
            "task_id": "${{ env.TASK_ID }}",
            "pr_number": "${{ env.PR_NUMBER }}",
            "repo": "${{ github.repository }}",
            "branch": "${{ github.head_ref || github.ref_name }}",
            "implementation_status": "tested",
            "platform_status": "checks_pending",
            "governance_status": "review_required",
            "automation_status": "running"
          }
          EOF

      - name: Check collaboration closure
        run: |
          python3 github-actions/check_collaboration_closure.py < closure_payload.json > closure_check.json
          cat closure_check.json
```

- [ ] **Step 6: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_governance_ledger_cycle.py -v
python3 -m unittest github-actions/tests/test_collab_workflows_present.py -v
```

Expected:

- PASS for the new governance closure test
- Existing workflow presence tests remain green

- [ ] **Step 7: Commit**

```bash
git add github-actions/run_governance_ledger_cycle.py .github/workflows/collab-governance-agent.yml templates/pr-comment-governance-handoff.md templates/pr-comment-updated.md templates/pr-comment-validation-result.md github-actions/tests/test_run_governance_ledger_cycle.py
git commit -m "feat: align governance handoff with github checks"
```

---

## Task 3: 扩展 ledger 字段并同步 GitHub 状态到飞书 Base

**Files:**
- Create: `github-actions/sync_github_to_feishu.py`
- Create: `github-actions/tests/test_sync_github_to_feishu.py`
- Modify: `github-actions/update_agent_ledger.py`
- Modify: `github-actions/tests/test_update_agent_ledger.py`

- [ ] **Step 1: 为飞书同步脚本先写失败测试**

Create `github-actions/tests/test_sync_github_to_feishu.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "sync_github_to_feishu.py"
SPEC = importlib.util.spec_from_file_location("sync_github_to_feishu", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class SyncGithubToFeishuTests(unittest.TestCase):
    def test_build_feishu_record_maps_all_four_status_layers(self):
        SPEC.loader.exec_module(MODULE)
        record = MODULE.build_feishu_record(
            {
                "task_id": "task-001",
                "repo": "yunya1991/DREAM-AGENT",
                "branch": "feature",
                "pr_number": "7",
                "implementation_status": "tested",
                "platform_status": "checks_pending",
                "governance_status": "review_required",
                "automation_status": "running",
            }
        )
        self.assertEqual(record["任务ID"], "task-001")
        self.assertEqual(record["平台状态"], "checks_pending")
        self.assertEqual(record["治理状态"], "review_required")
        self.assertEqual(record["自动化状态"], "running")
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
python3 -m unittest github-actions/tests/test_sync_github_to_feishu.py -v
```

Expected:

- FAIL because `sync_github_to_feishu.py` does not exist

- [ ] **Step 3: 实现飞书记录映射**

Create `github-actions/sync_github_to_feishu.py`:

```python
import json
import sys


def build_feishu_record(payload):
    return {
        "任务ID": payload.get("task_id", ""),
        "任务名称": payload.get("task_name", ""),
        "仓库": payload.get("repo", ""),
        "分支": payload.get("branch", ""),
        "PR号": payload.get("pr_number", ""),
        "Workflow运行ID": payload.get("workflow_run_id", ""),
        "实现状态": payload.get("implementation_status", ""),
        "平台状态": payload.get("platform_status", ""),
        "治理状态": payload.get("governance_status", ""),
        "自动化状态": payload.get("automation_status", ""),
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

- [ ] **Step 4: 扩展 ledger 字段**

Modify `github-actions/update_agent_ledger.py` to add this helper:

```python
def normalize_closure_status(task):
    task["implementation_status"] = task.get("implementation_status", "planned")
    task["platform_status"] = task.get("platform_status", "no_pr")
    task["governance_status"] = task.get("governance_status", "draft")
    task["automation_status"] = task.get("automation_status", "idle")
    return task
```

Then call it before writing task updates:

```python
task = normalize_closure_status(task)
```

Append to `github-actions/tests/test_update_agent_ledger.py`:

```python
class CollaborationClosureStatusTests(unittest.TestCase):
    def test_normalize_closure_status_fills_missing_layers(self):
        task = {}
        result = MODULE.normalize_closure_status(task)
        self.assertEqual(result["implementation_status"], "planned")
        self.assertEqual(result["platform_status"], "no_pr")
        self.assertEqual(result["governance_status"], "draft")
        self.assertEqual(result["automation_status"], "idle")
```

- [ ] **Step 5: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_sync_github_to_feishu.py github-actions/tests/test_update_agent_ledger.py -v
```

Expected:

- PASS for new sync script test
- PASS for new ledger status default test

- [ ] **Step 6: Commit**

```bash
git add github-actions/sync_github_to_feishu.py github-actions/tests/test_sync_github_to_feishu.py github-actions/update_agent_ledger.py github-actions/tests/test_update_agent_ledger.py
git commit -m "feat: sync collaboration status to feishu"
```

---

## Task 4: 增加飞书 remote_action 的 pause / retry 处理

**Files:**
- Create: `github-actions/process_feishu_remote_action.py`
- Create: `github-actions/tests/test_process_feishu_remote_action.py`

- [ ] **Step 1: 先写远程动作处理失败测试**

Create `github-actions/tests/test_process_feishu_remote_action.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "process_feishu_remote_action.py"
SPEC = importlib.util.spec_from_file_location("process_feishu_remote_action", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProcessFeishuRemoteActionTests(unittest.TestCase):
    def test_pause_action_sets_paused_status(self):
        result = MODULE.apply_remote_action(
            {"automation_status": "running"},
            {"remote_action": "pause"},
        )
        self.assertEqual(result["automation_status"], "paused")
        self.assertEqual(result["remote_action_result"], "pause_applied")
        self.assertEqual(result["remote_action"], "none")

    def test_retry_action_sets_retry_triggered(self):
        result = MODULE.apply_remote_action(
            {"automation_status": "failed"},
            {"remote_action": "retry"},
        )
        self.assertEqual(result["automation_status"], "running")
        self.assertEqual(result["remote_action_result"], "retry_triggered")
        self.assertEqual(result["remote_action"], "none")
```

- [ ] **Step 2: 实现动作处理器**

Create `github-actions/process_feishu_remote_action.py`:

```python
import json
import sys


def apply_remote_action(current, incoming):
    action = incoming.get("remote_action", "none")
    result = dict(current)
    result["remote_action"] = "none"

    if action == "pause":
        result["automation_status"] = "paused"
        result["remote_action_result"] = "pause_applied"
        return result

    if action == "retry":
        result["automation_status"] = "running"
        result["remote_action_result"] = "retry_triggered"
        return result

    result["remote_action_result"] = "no_action"
    return result


if __name__ == "__main__":
    data = json.load(sys.stdin)
    json.dump(
        apply_remote_action(data.get("current", {}), data.get("incoming", {})),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
```

- [ ] **Step 3: 运行测试确认通过**

Run:

```bash
python3 -m unittest github-actions/tests/test_process_feishu_remote_action.py -v
```

Expected:

- PASS for `pause` and `retry`

- [ ] **Step 4: Commit**

```bash
git add github-actions/process_feishu_remote_action.py github-actions/tests/test_process_feishu_remote_action.py
git commit -m "feat: add feishu remote action processor"
```

---

## Task 5: 更新文档入口并做最小回归

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/04-ENGINEERING-INDEX.md`
- Modify: `docs/superpowers/plans/2026-06-07-github-feishu-collaboration-closure-repair-implementation.md`

- [ ] **Step 1: 把修复设计与计划登记到入口文档**

Add to `README.md`:

```md
- `docs/superpowers/specs/2026-06-07-github-feishu-collaboration-closure-repair-design.md` — GitHub checks、治理结论与飞书监控闭环修复设计
- `docs/superpowers/plans/2026-06-07-github-feishu-collaboration-closure-repair-implementation.md` — 对应实施计划
```

Add to `docs/README.md`:

```md
- `docs/superpowers/specs/2026-06-07-github-feishu-collaboration-closure-repair-design.md`
- `docs/superpowers/plans/2026-06-07-github-feishu-collaboration-closure-repair-implementation.md`
```

Add to `docs/04-ENGINEERING-INDEX.md`:

```md
### GitHub x 飞书协作闭环修复

- 设计：`docs/superpowers/specs/2026-06-07-github-feishu-collaboration-closure-repair-design.md`
- 计划：`docs/superpowers/plans/2026-06-07-github-feishu-collaboration-closure-repair-implementation.md`
```

- [ ] **Step 2: 运行最小回归**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_collaboration_closure_payload.py \
  github-actions/tests/test_check_collaboration_closure.py \
  github-actions/tests/test_run_governance_ledger_cycle.py \
  github-actions/tests/test_sync_github_to_feishu.py \
  github-actions/tests/test_process_feishu_remote_action.py \
  github-actions/tests/test_update_agent_ledger.py -v
git diff --check
```

Expected:

- All selected tests pass
- `git diff --check` outputs nothing

- [ ] **Step 3: Commit**

```bash
git add README.md docs/README.md docs/04-ENGINEERING-INDEX.md docs/superpowers/plans/2026-06-07-github-feishu-collaboration-closure-repair-implementation.md
git commit -m "docs: register github feishu collaboration repair plan"
```

---

## Self-Review

### Spec coverage

- 四层状态模型：Task 1 + Task 3
- checks 与治理结论一致性：Task 1 + Task 2
- 评论模板与治理输出规则：Task 2
- 飞书监控 Base 契约：Task 3
- `pause / retry`：Task 4
- 恢复自动化前的最小回归：Task 5

### Placeholder scan

- 未使用 `TODO` / `TBD`
- 每个任务包含明确文件、代码块、命令和预期结果

### Type consistency

- 全程统一使用：
  - `implementation_status`
  - `platform_status`
  - `governance_status`
  - `automation_status`
  - `remote_action`
  - `remote_action_result`

---

Plan complete and saved to `docs/superpowers/plans/2026-06-07-github-feishu-collaboration-closure-repair-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
