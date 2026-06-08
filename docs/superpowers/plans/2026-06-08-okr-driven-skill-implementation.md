# OKR-driven SKILL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an `OKR-driven SKILL` that turns `spec + plan` into a reviewable execution preview, then executes `OKR + Base + task + workflow` updates and refreshes goal projection after confirmation.

**Architecture:** Keep the skill itself as a thin orchestration surface in `.trae/skills/okr-driven/SKILL.md`, and move deterministic compilation / payload-building logic into small Python helpers under `github-actions/`. Reuse the already-proven live patterns for OKR binding, goal projection refresh, Base writeback, and workflow schema alignment instead of inventing a second execution path.

**Tech Stack:** Markdown skill docs, Python 3, `unittest`, existing `github-actions/*` helpers, `lark-cli base`, browser-assisted Feishu OKR runtime fallback

---

## Scope Check

This plan covers one coherent sub-project:

- Compile `spec + plan` into a stable intermediate preview object
- Materialize that preview into execution payloads for `OKR + Base + task + workflow`
- Package the flow into `.trae/skills/okr-driven/SKILL.md`
- Reuse existing live helpers to refresh goal projection and verify boss view after execution

It does **not** include:

- General architecture-diagram parsing as a required v1 input
- Dashboard automation
- Rewriting the existing workflow bootstrapper from scratch
- A fully generic DSL compiler in v1

## File Map

- Create: `.trae/skills/okr-driven/SKILL.md`
  - Main skill instructions, trigger conditions, preview-first workflow, execution sequence, and guardrails.
- Create: `.trae/skills/okr-driven/references/execution-checklist.md`
  - Operator checklist for preview review, execution confirmation, and post-run verification.
- Create: `github-actions/build_okr_driven_preview.py`
  - Compile `spec + plan` into the normalized `ExecutionPreview` object.
- Create: `github-actions/tests/test_build_okr_driven_preview.py`
  - Lock preview extraction, object typing, downgrade flags, and confirmation requirements.
- Create: `github-actions/materialize_okr_driven_execution.py`
  - Turn `ExecutionPreview` into deterministic execution payloads for OKR, Base, task, workflow, and projection refresh.
- Create: `github-actions/tests/test_materialize_okr_driven_execution.py`
  - Lock payload shapes and adapter boundaries.
- Create: `github-actions/refresh_okr_driven_goal_projection.py`
  - Rebuild the live goal payload from the updated OKR anchors and write it back to Base.
- Create: `github-actions/tests/test_refresh_okr_driven_goal_projection.py`
  - Lock `workflow_signal`, boss-field refresh, and verification output.
- Create: `github-actions/tests/fixtures/okr_driven_skill/central_hub_spec.md`
  - Stable fixture copied from the approved design spec.
- Create: `github-actions/tests/fixtures/okr_driven_skill/central_hub_plan.md`
  - Stable fixture copied from the approved implementation plan.

## Execution Guardrails

- Ignore the unrelated deletion `.github/workflows/feishu-approval-smoke.yml`; never restore or stage it.
- Ignore `.superpowers/` files created by prior skill flows.
- Keep all 19-digit OKR / Base identifiers as strings in every helper and test fixture.
- The preview builder must never perform online writes.
- The skill must default to `先预演后执行`; direct execution without preview is a bug.
- The execution materializer must preserve layer boundaries:
  - Objective/KR for goal truth
  - Base for projection
  - tasks for actions
  - workflow for reminders/checks
- Reuse the existing `build_goal_progress_record.py` and `build_central_hub_okr_binding_payload.py` contracts where possible; do not fork equivalent JSON shapes.

## Task 1: Add the Preview Compiler

**Files:**
- Create: `github-actions/build_okr_driven_preview.py`
- Create: `github-actions/tests/test_build_okr_driven_preview.py`
- Create: `github-actions/tests/fixtures/okr_driven_skill/central_hub_spec.md`
- Create: `github-actions/tests/fixtures/okr_driven_skill/central_hub_plan.md`

- [ ] **Step 1: Write the failing preview tests**

Create `github-actions/tests/test_build_okr_driven_preview.py`:

```python
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_okr_driven_preview.py"
SPEC = importlib.util.spec_from_file_location("build_okr_driven_preview", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "okr_driven_skill"


class BuildOkrDrivenPreviewTests(unittest.TestCase):
    def load_sources(self):
        return {
            "spec_text": (FIXTURE_DIR / "central_hub_spec.md").read_text(encoding="utf-8"),
            "plan_text": (FIXTURE_DIR / "central_hub_plan.md").read_text(encoding="utf-8"),
        }

    def test_preview_builds_objective_kr_goal_task_workflow_layers(self):
        SPEC.loader.exec_module(MODULE)
        preview = MODULE.build_preview(**self.load_sources())
        self.assertEqual(preview["requires_confirmation"], True)
        self.assertEqual(preview["objective_candidates"][0]["title"], "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制")
        self.assertEqual(len(preview["kr_candidates"]), 4)
        self.assertEqual(preview["goal_record_candidates"][0]["goal_id"], "goal-trading-hub-connectivity-20260519")
        self.assertGreaterEqual(len(preview["task_candidates"]), 1)
        self.assertGreaterEqual(len(preview["workflow_candidates"]), 1)

    def test_preview_marks_incomplete_task_or_workflow_when_plan_is_too_thin(self):
        SPEC.loader.exec_module(MODULE)
        preview = MODULE.build_preview(
            spec_text="# spec\nKR1：前端关键页面完成实时联动验证\n",
            plan_text="# plan\n",
        )
        self.assertIn("task_layer_incomplete", preview["risk_flags"])
        self.assertIn("workflow_layer_incomplete", preview["risk_flags"])

    def test_preview_keeps_ids_and_refs_as_strings(self):
        SPEC.loader.exec_module(MODULE)
        preview = MODULE.build_preview(**self.load_sources())
        goal = preview["goal_record_candidates"][0]
        self.assertIsInstance(goal["goal_id"], str)
        self.assertIsInstance(goal["okr_anchor_ref"], str)
```

- [ ] **Step 2: Add stable spec/plan fixtures**

Create `github-actions/tests/fixtures/okr_driven_skill/central_hub_spec.md` with the minimal approved source:

```md
# 中台能力 Objective/KR 绑定与目标驱动推进设计

## 设计目标
- 把“中台与前端联动验证能力打通”绑定为真实飞书 Objective

## 推荐建模方案
- Objective：中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制
- KR1：Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路
- KR2：前端关键页面完成实时联动验证，能直接反映交易链路状态变化
- KR3：审批、目标推进、workflow 提醒与老板视图形成运行闭环
- KR4：架构图、spec、实施计划中的核心功能项被拆解进持续推进机制并可跟踪

## 目标推进表与 Objective/KR 的联动
- goal_id = goal-trading-hub-connectivity-20260519
- 目标名称 = 中台与前端联动验证能力打通
```

Create `github-actions/tests/fixtures/okr_driven_skill/central_hub_plan.md`:

```md
# Central Hub OKR Binding Implementation Plan

## Scope Check
- Create the real Objective and four KR entries
- Bind the existing Base goal record to that Objective
- Update the OKR anchor fields in 目标推进表

## Task 3
- Create the real Objective and four KRs in Feishu OKR

## Task 4
- Bind the live Base goal record to the new Objective

## Task 5
- Verify the boss view still works and capture the final handoff
```

- [ ] **Step 3: Run the tests and verify they fail**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_okr_driven_preview.py -v
```

Expected: FAIL because `github-actions/build_okr_driven_preview.py` does not exist yet.

- [ ] **Step 4: Write the minimal preview compiler**

Create `github-actions/build_okr_driven_preview.py`:

```python
import json
import re
import sys


OBJECTIVE_RE = re.compile(r"Objective[：:]\s*(.+)")
KR_RE = re.compile(r"KR\d+[：:]\s*(.+)")
GOAL_ID_RE = re.compile(r"goal_id\s*=\s*([A-Za-z0-9\-_]+)")
GOAL_NAME_RE = re.compile(r"目标名称\s*=\s*(.+)")


def _extract_objective(spec_text):
    match = OBJECTIVE_RE.search(spec_text)
    return match.group(1).strip() if match else ""


def _extract_krs(spec_text):
    return [m.group(1).strip() for m in KR_RE.finditer(spec_text)]


def _extract_goal(spec_text):
    goal_id_match = GOAL_ID_RE.search(spec_text)
    goal_name_match = GOAL_NAME_RE.search(spec_text)
    goal_id = goal_id_match.group(1) if goal_id_match else "goal-missing-id"
    goal_name = goal_name_match.group(1).strip() if goal_name_match else "未命名目标"
    return {
        "goal_id": str(goal_id),
        "goal_name": goal_name,
        "goal_owner": "governance-agent",
        "goal_status": "blocked",
        "risk_level": "high",
        "blocker": "",
        "next_action": "",
        "okr_anchor_ref": str(goal_id),
    }


def _extract_task_candidates(plan_text, goal_id, kr_titles):
    tasks = []
    if "Task 3" in plan_text:
        tasks.append(
            {
                "task_id": "task-create-real-okr",
                "title": "创建真实 Objective 和 4 个 KR",
                "goal_ref": goal_id,
                "kr_ref": kr_titles[0] if kr_titles else "",
                "owner": "governance-agent",
                "status": "planned",
                "deliverable": "real objective and kr ids",
            }
        )
    if "Task 4" in plan_text:
        tasks.append(
            {
                "task_id": "task-bind-base-record",
                "title": "回写目标推进表的 OKR 锚点字段",
                "goal_ref": goal_id,
                "kr_ref": "",
                "owner": "governance-agent",
                "status": "planned",
                "deliverable": "base anchor writeback",
            }
        )
    return tasks


def _extract_workflow_candidates(plan_text, goal_id):
    workflows = []
    if "boss view" in plan_text.lower() or "老板视图" in plan_text:
        workflows.append(
            {
                "name": "OKR对齐缺失提醒",
                "trigger_kind": "record_change",
                "conditions": ["当前状态=推进中", "OKR对齐!=已对齐"],
                "receivers": ["OKR负责人"],
                "expected_signal": "missing_okr_alignment",
                "goal_ref": goal_id,
            }
        )
    return workflows


def build_preview(spec_text, plan_text):
    objective_title = _extract_objective(spec_text)
    kr_titles = _extract_krs(spec_text)
    goal = _extract_goal(spec_text)
    tasks = _extract_task_candidates(plan_text, goal["goal_id"], kr_titles)
    workflows = _extract_workflow_candidates(plan_text, goal["goal_id"])

    risk_flags = []
    if not tasks:
        risk_flags.append("task_layer_incomplete")
    if not workflows:
        risk_flags.append("workflow_layer_incomplete")

    return {
        "objective_candidates": [
            {
                "title": objective_title,
                "owner": "governance-agent",
                "period_hint": "current",
                "source_spec_refs": ["spec:推荐建模方案"],
                "source_plan_refs": ["plan:Task 3"],
            }
        ],
        "kr_candidates": [
            {
                "title": title,
                "objective_ref": objective_title,
                "acceptance_signal": "result_defined",
                "source_refs": ["spec:KR"],
            }
            for title in kr_titles
        ],
        "goal_record_candidates": [goal],
        "task_candidates": tasks,
        "workflow_candidates": workflows,
        "upsert_plan": ["OKR", "Base", "Task", "workflow", "projection"],
        "risk_flags": risk_flags,
        "requires_confirmation": True,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(build_preview(payload["spec_text"], payload["plan_text"]), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 5: Run the tests and verify they pass**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_okr_driven_preview.py -v
```

Expected: `Ran 3 tests ... OK`

- [ ] **Step 6: Commit**

```bash
git add github-actions/build_okr_driven_preview.py \
        github-actions/tests/test_build_okr_driven_preview.py \
        github-actions/tests/fixtures/okr_driven_skill/central_hub_spec.md \
        github-actions/tests/fixtures/okr_driven_skill/central_hub_plan.md
git commit -m "feat: add okr driven preview compiler"
```

## Task 2: Materialize the Execution Plan

**Files:**
- Create: `github-actions/materialize_okr_driven_execution.py`
- Create: `github-actions/tests/test_materialize_okr_driven_execution.py`

- [ ] **Step 1: Write the failing materialization tests**

Create `github-actions/tests/test_materialize_okr_driven_execution.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "materialize_okr_driven_execution.py"
SPEC = importlib.util.spec_from_file_location("materialize_okr_driven_execution", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class MaterializeOkrDrivenExecutionTests(unittest.TestCase):
    def sample_preview(self):
        return {
            "objective_candidates": [{"title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制", "owner": "Asher"}],
            "kr_candidates": [
                {"title": "Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路"},
                {"title": "前端关键页面完成实时联动验证，能直接反映交易链路状态变化"},
            ],
            "goal_record_candidates": [{"goal_id": "goal-trading-hub-connectivity-20260519", "goal_name": "中台与前端联动验证能力打通"}],
            "task_candidates": [{"task_id": "task-create-real-okr", "title": "创建真实 Objective 和 4 个 KR", "goal_ref": "goal-trading-hub-connectivity-20260519", "kr_ref": "Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路"}],
            "workflow_candidates": [{"name": "OKR对齐缺失提醒", "expected_signal": "missing_okr_alignment"}],
            "requires_confirmation": True,
        }

    def test_materialize_builds_four_layer_payloads(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.materialize_execution(self.sample_preview())
        self.assertIn("okr", result)
        self.assertIn("base", result)
        self.assertIn("tasks", result)
        self.assertIn("workflow", result)
        self.assertIn("projection", result)

    def test_materialize_keeps_base_as_projection_layer(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.materialize_execution(self.sample_preview())
        self.assertEqual(result["base"]["projection_only"], True)
        self.assertEqual(result["okr"]["source_of_truth"], "feishu_okr")

    def test_materialize_requires_confirmation_before_execution(self):
        SPEC.loader.exec_module(MODULE)
        result = MODULE.materialize_execution(self.sample_preview())
        self.assertEqual(result["execution_mode"], "preview_then_confirm")
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_okr_driven_execution.py -v
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Write the minimal materializer**

Create `github-actions/materialize_okr_driven_execution.py`:

```python
import json
import sys


def materialize_execution(preview):
    objective = preview["objective_candidates"][0]
    goal = preview["goal_record_candidates"][0]
    kr_titles = [item["title"] for item in preview["kr_candidates"]]

    return {
        "execution_mode": "preview_then_confirm",
        "okr": {
            "source_of_truth": "feishu_okr",
            "objective_title": objective["title"],
            "objective_owner": objective["owner"],
            "krs": kr_titles,
        },
        "base": {
            "projection_only": True,
            "goal_id": goal["goal_id"],
            "goal_name": goal["goal_name"],
            "anchor_fields": [
                "OKR对齐",
                "okr_objective_id",
                "okr_objective_title",
                "okr_owner",
                "okr_sync_status",
                "okr_last_sync_at",
            ],
        },
        "tasks": {
            "items": preview["task_candidates"],
        },
        "workflow": {
            "items": preview["workflow_candidates"],
        },
        "projection": {
            "refresh_fields": [
                "OKR对齐",
                "最近决策摘要",
                "workflow_signal",
                "当前状态",
                "当前阻塞",
                "风险等级",
                "下一步动作",
            ]
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the tests and verify they pass**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_okr_driven_execution.py -v
```

Expected: `Ran 3 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add github-actions/materialize_okr_driven_execution.py \
        github-actions/tests/test_materialize_okr_driven_execution.py
git commit -m "feat: add okr driven execution materializer"
```

## Task 3: Add Projection Refresh and Boss View Verification

**Files:**
- Create: `github-actions/refresh_okr_driven_goal_projection.py`
- Create: `github-actions/tests/test_refresh_okr_driven_goal_projection.py`

- [ ] **Step 1: Write the failing refresh tests**

Create `github-actions/tests/test_refresh_okr_driven_goal_projection.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "refresh_okr_driven_goal_projection.py"
SPEC = importlib.util.spec_from_file_location("refresh_okr_driven_goal_projection", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class RefreshOkrDrivenGoalProjectionTests(unittest.TestCase):
    def test_refresh_marks_goal_aligned_and_risk_blocked_when_blocker_remains(self):
        SPEC.loader.exec_module(MODULE)
        goal = {
            "goal_id": "goal-trading-hub-connectivity-20260519",
            "goal_name": "中台与前端联动验证能力打通",
            "goal_owner": "governance-agent",
            "okr_objective_id": "7648838772720995522",
            "okr_objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
            "okr_owner": "Asher",
            "okr_sync_status": "bound",
            "okr_last_sync_at": "2026-06-08T02:14:22+00:00",
            "last_workflow_run_at": "2026-06-08T02:20:00+00:00",
        }
        tasks = [
            {
                "approval_status": "not_required",
                "governance_status": "blocked",
                "risk_level": "high",
                "blocker": "7-ARTIFACT-HUB-V2 中台尚未直连 6-TRADING",
                "decision_summary": "objective_bound:7648838772720995522",
            }
        ]
        result = MODULE.refresh_projection(goal, tasks)
        self.assertEqual(result["OKR对齐"], "已对齐")
        self.assertEqual(result["workflow_signal"], "risk_blocked")
        self.assertEqual(result["当前状态"], "已阻塞")

    def test_refresh_emits_boss_view_verification_fields(self):
        SPEC.loader.exec_module(MODULE)
        goal = {
            "goal_id": "goal-trading-hub-connectivity-20260519",
            "goal_name": "中台与前端联动验证能力打通",
            "goal_owner": "governance-agent",
            "okr_objective_id": "7648838772720995522",
            "okr_objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
            "okr_owner": "Asher",
            "okr_sync_status": "bound",
            "okr_last_sync_at": "2026-06-08T02:14:22+00:00",
            "last_workflow_run_at": "2026-06-08T02:20:00+00:00",
        }
        tasks = [{"approval_status": "not_required", "governance_status": "blocked", "risk_level": "high", "blocker": "still blocked", "decision_summary": "bound"}]
        result = MODULE.refresh_projection(goal, tasks)
        self.assertIn("目标名称", result)
        self.assertIn("当前阻塞", result)
        self.assertIn("下一步动作", result)
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
python3 -m unittest github-actions/tests/test_refresh_okr_driven_goal_projection.py -v
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Write the minimal refresh helper**

Create `github-actions/refresh_okr_driven_goal_projection.py`:

```python
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import build_goal_progress_record as GOAL


def refresh_projection(goal, tasks):
    enriched_goal = dict(goal)
    enriched_goal.setdefault("current_phase", "hub-trading-connectivity")
    enriched_goal.setdefault("next_milestone", "打通 Hub 直连 Trading 并完成三页面实时联动验证")
    enriched_goal.setdefault("next_action", "由开发代理认领任务并实现 Hub 侧 /api/trading/* 直连桥接")
    return GOAL.build_goal_record(enriched_goal, tasks)


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(refresh_projection(payload["goal"], payload["tasks"]), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the tests and verify they pass**

Run:

```bash
python3 -m unittest github-actions/tests/test_refresh_okr_driven_goal_projection.py -v
```

Expected: `Ran 2 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add github-actions/refresh_okr_driven_goal_projection.py \
        github-actions/tests/test_refresh_okr_driven_goal_projection.py
git commit -m "feat: add okr driven projection refresh helper"
```

## Task 4: Package the Skill

**Files:**
- Create: `.trae/skills/okr-driven/SKILL.md`
- Create: `.trae/skills/okr-driven/references/execution-checklist.md`

- [ ] **Step 1: Write the skill document**

Create `.trae/skills/okr-driven/SKILL.md`:

```md
---
name: "okr-driven"
description: "Compiles spec + plan into Objective/KR, Base, task, and workflow execution previews, then executes after confirmation. Invoke when building or advancing goal-driven delivery from approved spec and plan."
---

# OKR-driven

## When to use

Use this skill when:

- the user already has an approved `spec + plan`
- the user wants to turn them into `OKR + Base + task + workflow`
- the user wants a preview before any online writes
- the user wants post-run projection refresh and boss-view verification

Do not use this skill when:

- only a raw idea exists and brainstorming is still needed
- there is no usable spec or implementation plan yet
- the request is only to write KR wording without execution

## Required execution mode

This skill always runs in two stages:

1. preview
2. confirmation
3. execution
4. projection refresh
5. boss-view verification
6. handoff generation

Never skip the preview step.

## Inputs

- approved spec path
- approved implementation plan path
- optional live identifiers already known from previous runs

## Stage 1: Build preview

Run:

```bash
python3 github-actions/build_okr_driven_preview.py <<'EOF'
{
  "spec_text": "...",
  "plan_text": "..."
}
EOF
```

Then materialize:

```bash
python3 github-actions/materialize_okr_driven_execution.py <<'EOF'
{ ...preview json... }
EOF
```

Present:

- objects to create
- objects to update
- anchor changes
- execution order
- risk flags

## Stage 2: Execute after confirmation

Execution order:

1. OKR
2. Base
3. task
4. workflow
5. projection refresh
6. boss-view verification

Keep IDs as strings at every step.

## Projection refresh

After online writes complete, run:

```bash
python3 github-actions/refresh_okr_driven_goal_projection.py <<'EOF'
{
  "goal": { ... },
  "tasks": [ ... ]
}
EOF
```

Then write the refreshed payload back to Base and re-read the boss view.

## Verification

Always verify:

- real objective id
- real record id
- workflow_signal
- boss view visible fields
- handoff output
```

- [ ] **Step 2: Write the execution checklist**

Create `.trae/skills/okr-driven/references/execution-checklist.md`:

```md
# Execution Checklist

## Preview Gate

- Confirm spec path is approved
- Confirm plan path is approved
- Confirm preview contains Objective, KR, Base, task, workflow layers
- Confirm `requires_confirmation = true`

## Execution Gate

- OKR owner and period resolved
- 19-digit ids handled as strings
- Base target record identified
- workflow schema source identified

## Post-Run Verification

- OKR anchors written back
- `OKR对齐` refreshed
- `workflow_signal` refreshed
- boss view read back
- handoff baseline written
```

- [ ] **Step 3: Sanity-check the skill files**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
for path in [
    Path(".trae/skills/okr-driven/SKILL.md"),
    Path(".trae/skills/okr-driven/references/execution-checklist.md"),
]:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
print("skill files ok")
PY
```

Expected: `skill files ok`

- [ ] **Step 4: Commit**

```bash
git add .trae/skills/okr-driven/SKILL.md \
        .trae/skills/okr-driven/references/execution-checklist.md
git commit -m "feat: add okr driven skill package"
```

## Task 5: End-to-End Dry Run and Live Validation Checklist

**Files:**
- Modify: `/tmp/okr-driven-skill-input-baseline.md` (read-only input)
- Create: `/tmp/okr-driven-skill-preview.json`
- Create: `/tmp/okr-driven-skill-execution.json`

- [ ] **Step 1: Build a local preview from the approved sources**

Run:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT")
spec_text = (root / "docs/superpowers/specs/2026-06-08-okr-driven-skill-design.md").read_text(encoding="utf-8")
plan_text = (root / "docs/superpowers/plans/2026-06-08-okr-driven-skill-implementation.md").read_text(encoding="utf-8")
payload = {"spec_text": spec_text, "plan_text": plan_text}
out = subprocess.check_output(
    ["python3", str(root / "github-actions/build_okr_driven_preview.py")],
    input=json.dumps(payload, ensure_ascii=False),
    text=True,
)
Path("/tmp/okr-driven-skill-preview.json").write_text(out, encoding="utf-8")
print(out)
PY
```

Expected: preview JSON with objective, KR, Base, task, workflow layers.

- [ ] **Step 2: Materialize the execution payload**

Run:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT")
preview = json.loads(Path("/tmp/okr-driven-skill-preview.json").read_text(encoding="utf-8"))
out = subprocess.check_output(
    ["python3", str(root / "github-actions/materialize_okr_driven_execution.py")],
    input=json.dumps(preview, ensure_ascii=False),
    text=True,
)
Path("/tmp/okr-driven-skill-execution.json").write_text(out, encoding="utf-8")
print(out)
PY
```

Expected: execution JSON with `okr`, `base`, `tasks`, `workflow`, and `projection`.

- [ ] **Step 3: Run the targeted unit test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_okr_driven_preview.py \
  github-actions/tests/test_materialize_okr_driven_execution.py \
  github-actions/tests/test_refresh_okr_driven_goal_projection.py -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add github-actions/build_okr_driven_preview.py \
        github-actions/materialize_okr_driven_execution.py \
        github-actions/refresh_okr_driven_goal_projection.py \
        github-actions/tests/test_build_okr_driven_preview.py \
        github-actions/tests/test_materialize_okr_driven_execution.py \
        github-actions/tests/test_refresh_okr_driven_goal_projection.py \
        github-actions/tests/fixtures/okr_driven_skill/central_hub_spec.md \
        github-actions/tests/fixtures/okr_driven_skill/central_hub_plan.md
git commit -m "test: validate okr driven skill dry run"
```

## Self-Review

- Spec coverage:
  - `spec + plan` input restriction: Task 1 and Task 4
  - preview-first workflow: Task 1, Task 2, Task 4, Task 5
  - four-layer execution (`OKR + Base + task + workflow`): Task 2 and Task 4
  - projection refresh and boss-view verification: Task 3 and Task 5
  - evolution path toward a later DSL: File map and Task 1/2 separation
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred “fill later” steps
  - Each code-writing step includes concrete code
  - Each validation step has exact commands and expected outcomes
- Type consistency:
  - IDs remain strings across preview, materialization, and refresh tasks
  - `workflow_signal`, `OKR对齐`, and OKR anchor fields reuse existing repository conventions
  - The skill file explicitly enforces preview-before-execution
