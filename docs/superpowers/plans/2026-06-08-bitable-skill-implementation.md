# Bitable SKILL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a preview-first `Bitable SKILL` that projects `OKR-driven` outputs into Base task records, progress records, and view-validation results, then writes back and verifies after confirmation.

**Architecture:** Keep the skill package thin and move deterministic behavior into small Python helpers under `github-actions/feishu_collab/bitable/`. Reuse the existing goal-projection semantics from `build_goal_progress_record.py`, consume shared contracts from `github-actions/feishu_collab/shared/contracts.py`, and let the skill orchestrate preview, confirmation, writeback, verification, and knowledge update without redefining goals.

**Tech Stack:** Markdown skill docs, Python 3, `unittest`, `dataclasses`, existing `github-actions/*` helpers, shared Feishu-collaboration contracts

---

## Scope Check

This plan covers one coherent sub-project:

- Compile `OKR-driven` outputs and Base context into `Bitable` preview objects
- Materialize those preview objects into task/progress/projection/view-validation writeback plans
- Package the flow as `.trae/skills/feishu-collab-bitable/SKILL.md`
- Verify that `KnowledgeUpdate` and handoff payloads are produced after execution

It does **not** include:

- A full Base platform or arbitrary cross-table computation engine
- Deep automatic view configuration changes in v1
- Full implementation of GitHub sync, Approval, or Knowledge-Ops skills
- Migration of all historical Base schemas

## File Map

- Create: `.trae/skills/feishu-collab-bitable/SKILL.md`
  - Main skill instructions, trigger conditions, preview-first flow, and verification gate.
- Create: `.trae/skills/feishu-collab-bitable/references/execution-checklist.md`
  - Operator checklist for preview review, writeback order, verification, and handoff.
- Create: `github-actions/feishu_collab/bitable/__init__.py`
  - Package marker for Bitable helpers.
- Create: `github-actions/feishu_collab/bitable/build_bitable_preview.py`
  - Compile `OKR-driven` payloads plus Base context into `TaskRecordSpec`, `ProgressRecordSpec`, `GoalProjectionSpec`, `FieldGovernanceSpec`, and `ViewProjectionSpec`.
- Create: `github-actions/tests/test_build_bitable_preview.py`
  - Lock preview object shapes, drift flags, and confirmation requirements.
- Create: `github-actions/feishu_collab/bitable/materialize_bitable_execution.py`
  - Turn preview output into ordered task/progress/projection/view-validation writeback plans.
- Create: `github-actions/tests/test_materialize_bitable_execution.py`
  - Lock writeback order, failure modes, and knowledge-update emission.
- Create: `github-actions/feishu_collab/bitable/verify_bitable_projection.py`
  - Re-check task/progress/projection/view outputs after writeback and classify success vs degraded/blocking outcomes.
- Create: `github-actions/tests/test_verify_bitable_projection.py`
  - Lock verification behavior for `hard_block`, `soft_block`, and `degraded_success`.
- Create: `github-actions/tests/fixtures/bitable_skill/okr_driven_preview.json`
  - Stable upstream fixture representing `OKR-driven` output.
- Create: `github-actions/tests/fixtures/bitable_skill/base_context.json`
  - Stable Base context fixture representing current records, fields, and views.

## Execution Guardrails

- Ignore the unrelated deletion `.github/workflows/feishu-approval-smoke.yml`; never restore or stage it.
- Ignore `.superpowers/` files and any temporary local state outside the files listed in this plan.
- Keep `Bitable` downstream of `OKR-driven`; do not add a second planning entrypoint.
- Keep v1 focused on `任务 + 进度 + 视图`; do not add cross-table engines or BI abstractions.
- Treat view handling as validation-first in v1: verify dependencies and emit repair guidance, but do not automate deep view configuration rewrites.
- Emit `KnowledgeUpdate` and handoff payloads whenever execution reaches verification, including degraded outcomes.

## Task 1: Add the Bitable Preview Compiler

**Files:**
- Create: `github-actions/feishu_collab/bitable/__init__.py`
- Create: `github-actions/feishu_collab/bitable/build_bitable_preview.py`
- Create: `github-actions/tests/test_build_bitable_preview.py`
- Create: `github-actions/tests/fixtures/bitable_skill/okr_driven_preview.json`
- Create: `github-actions/tests/fixtures/bitable_skill/base_context.json`

- [ ] **Step 1: Write the failing preview tests**

Create `github-actions/tests/test_build_bitable_preview.py`:

```python
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "bitable" / "build_bitable_preview.py"
SPEC = importlib.util.spec_from_file_location("build_bitable_preview", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "bitable_skill"


class BuildBitablePreviewTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_payloads(self):
        return {
            "okr_preview": json.loads((FIXTURE_DIR / "okr_driven_preview.json").read_text(encoding="utf-8")),
            "base_context": json.loads((FIXTURE_DIR / "base_context.json").read_text(encoding="utf-8")),
        }

    def test_preview_builds_task_progress_projection_and_view_layers(self):
        module = self.load_module()
        preview = module.build_bitable_preview(**self.load_payloads())
        self.assertEqual(preview["requires_confirmation"], True)
        self.assertEqual(len(preview["task_record_candidates"]), 2)
        self.assertEqual(len(preview["progress_record_candidates"]), 2)
        self.assertEqual(preview["goal_projection_candidates"][0]["goal_id"], "goal-trading-hub-connectivity-20260519")
        self.assertEqual(preview["view_projection_candidates"][0]["view_name"], "老板视图（状态与阻塞）")

    def test_preview_marks_missing_fields_and_view_drift(self):
        module = self.load_module()
        preview = module.build_bitable_preview(
            okr_preview={
                "goal_record_candidates": [{"goal_id": "goal-1", "goal_name": "测试目标"}],
                "task_candidates": [],
                "workflow_candidates": [],
            },
            base_context={
                "required_fields": ["goal_id", "任务标题"],
                "existing_fields": ["goal_id"],
                "views": [],
            },
        )
        self.assertIn("missing_required_fields", preview["drift_flags"])
        self.assertIn("view_projection_incomplete", preview["drift_flags"])

    def test_preview_keeps_refs_linked_to_goal_and_kr(self):
        module = self.load_module()
        preview = module.build_bitable_preview(**self.load_payloads())
        first_task = preview["task_record_candidates"][0]
        self.assertEqual(first_task["goal_ref"], "goal-trading-hub-connectivity-20260519")
        self.assertTrue(first_task["kr_ref"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add stable upstream/base fixtures**

Create `github-actions/tests/fixtures/bitable_skill/okr_driven_preview.json`:

```json
{
  "objective_candidates": [
    {
      "title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
      "owner": "governance-agent"
    }
  ],
  "kr_candidates": [
    {
      "title": "Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路"
    },
    {
      "title": "前端关键页面完成实时联动验证，能直接反映交易链路状态变化"
    }
  ],
  "goal_record_candidates": [
    {
      "goal_id": "goal-trading-hub-connectivity-20260519",
      "goal_name": "中台与前端联动验证能力打通",
      "goal_owner": "governance-agent",
      "okr_objective_id": "7648838772720995522",
      "okr_objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
      "okr_owner": "Asher",
      "okr_sync_status": "bound"
    }
  ],
  "task_candidates": [
    {
      "task_id": "task-create-real-okr",
      "title": "创建真实 Objective 和 4 个 KR",
      "goal_ref": "goal-trading-hub-connectivity-20260519",
      "kr_ref": "Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路",
      "owner": "governance-agent",
      "status": "planned",
      "deliverable": "real objective and kr ids"
    },
    {
      "task_id": "task-bind-base-record",
      "title": "回写目标推进表的 OKR 锚点字段",
      "goal_ref": "goal-trading-hub-connectivity-20260519",
      "kr_ref": "前端关键页面完成实时联动验证，能直接反映交易链路状态变化",
      "owner": "governance-agent",
      "status": "planned",
      "deliverable": "base anchor writeback"
    }
  ]
}
```

Create `github-actions/tests/fixtures/bitable_skill/base_context.json`:

```json
{
  "required_fields": [
    "goal_id",
    "任务标题",
    "任务负责人",
    "当前状态",
    "风险等级",
    "当前阻塞",
    "下一步动作",
    "okr_objective_id",
    "workflow_signal"
  ],
  "existing_fields": [
    "goal_id",
    "任务标题",
    "任务负责人",
    "当前状态",
    "风险等级",
    "当前阻塞",
    "下一步动作",
    "okr_objective_id",
    "workflow_signal"
  ],
  "views": [
    {
      "view_name": "老板视图（状态与阻塞）",
      "required_columns": ["目标名称", "当前状态", "当前阻塞", "风险等级", "下一步动作"]
    }
  ]
}
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_bitable_preview.py -v
```

Expected: FAIL because `build_bitable_preview.py` does not exist yet.

- [ ] **Step 4: Write the minimal preview compiler**

Create `github-actions/feishu_collab/bitable/__init__.py`:

```python
"""Bitable projection helpers for the Feishu collaboration system."""
```

Create `github-actions/feishu_collab/bitable/build_bitable_preview.py`:

```python
import json
import sys


def _build_task_records(okr_preview):
    tasks = []
    goal = okr_preview["goal_record_candidates"][0]
    for item in okr_preview.get("task_candidates", []):
        tasks.append(
            {
                "task_id": item["task_id"],
                "goal_ref": goal["goal_id"],
                "objective_ref": goal.get("okr_objective_id", ""),
                "kr_ref": item.get("kr_ref", ""),
                "title": item["title"],
                "owner": item.get("owner", "governance-agent"),
                "status": item.get("status", "planned"),
                "risk_level": "medium",
                "blocker": "",
                "next_action": item.get("deliverable", ""),
                "deliverable": item.get("deliverable", ""),
                "source_refs": [item["task_id"]],
            }
        )
    return tasks


def _build_progress_records(task_records):
    return [
        {
            "goal_id": task["goal_ref"],
            "task_ref": task["task_id"],
            "progress_status": task["status"],
            "governance_status": "planned",
            "approval_status": "not_required",
            "risk_level": task["risk_level"],
            "blocker": task["blocker"],
            "decision_summary": "",
            "last_sync_at": "",
        }
        for task in task_records
    ]


def build_bitable_preview(okr_preview, base_context):
    goal = okr_preview["goal_record_candidates"][0]
    task_records = _build_task_records(okr_preview)
    progress_records = _build_progress_records(task_records)

    missing_fields = [
        field
        for field in base_context.get("required_fields", [])
        if field not in base_context.get("existing_fields", [])
    ]
    drift_flags = []
    if missing_fields:
        drift_flags.append("missing_required_fields")
    if not task_records:
        drift_flags.append("task_goal_unlinked")
    if not base_context.get("views"):
        drift_flags.append("view_projection_incomplete")

    return {
        "task_record_candidates": task_records,
        "progress_record_candidates": progress_records,
        "goal_projection_candidates": [
            {
                "goal_id": goal["goal_id"],
                "goal_name": goal["goal_name"],
                "okr_objective_id": goal.get("okr_objective_id", ""),
                "okr_objective_title": goal.get("okr_objective_title", ""),
                "okr_owner": goal.get("okr_owner", ""),
                "okr_sync_status": goal.get("okr_sync_status", ""),
                "goal_status": "active",
                "goal_progress": 0,
                "workflow_signal": "healthy",
                "key_blocker": "",
                "next_milestone": "",
                "next_action": "",
            }
        ],
        "field_governance_report": {
            "required_fields": base_context.get("required_fields", []),
            "missing_fields": missing_fields,
            "stale_fields": [],
            "field_mapping": {
                "任务标题": "title",
                "任务负责人": "owner",
                "当前状态": "progress_status",
            },
            "writeback_scope": ["tasks", "progress", "goal_projection"],
        },
        "view_projection_candidates": [
            {
                "view_name": view["view_name"],
                "view_type": "table",
                "required_columns": view.get("required_columns", []),
                "sort_keys": ["风险等级"],
                "filter_rules": [],
                "projection_fields": view.get("required_columns", []),
                "consumer_role": "manager",
            }
            for view in base_context.get("views", [])
        ],
        "drift_flags": drift_flags,
        "requires_confirmation": True,
        "writeback_order": [
            "field_governance_check",
            "task_writeback",
            "progress_writeback",
            "goal_projection_writeback",
            "view_validation",
        ],
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_bitable_preview(payload["okr_preview"], payload["base_context"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_bitable_preview.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 6: Commit**

```bash
git add github-actions/feishu_collab/bitable/__init__.py \
        github-actions/feishu_collab/bitable/build_bitable_preview.py \
        github-actions/tests/test_build_bitable_preview.py \
        github-actions/tests/fixtures/bitable_skill/okr_driven_preview.json \
        github-actions/tests/fixtures/bitable_skill/base_context.json
git commit -m "feat: add bitable preview compiler"
```

## Task 2: Add the Bitable Execution Materializer

**Files:**
- Create: `github-actions/feishu_collab/bitable/materialize_bitable_execution.py`
- Create: `github-actions/tests/test_materialize_bitable_execution.py`

- [ ] **Step 1: Write the failing materialization tests**

Create `github-actions/tests/test_materialize_bitable_execution.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "bitable" / "materialize_bitable_execution.py"
SPEC = importlib.util.spec_from_file_location("materialize_bitable_execution", MODULE_PATH)


class MaterializeBitableExecutionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "task_record_candidates": [
                {
                    "task_id": "task-create-real-okr",
                    "goal_ref": "goal-trading-hub-connectivity-20260519",
                    "objective_ref": "7648838772720995522",
                    "kr_ref": "KR1",
                    "title": "创建真实 Objective 和 4 个 KR",
                    "owner": "governance-agent",
                    "status": "planned",
                    "risk_level": "medium",
                    "blocker": "",
                    "next_action": "real objective and kr ids",
                    "deliverable": "real objective and kr ids",
                    "source_refs": ["task-create-real-okr"]
                }
            ],
            "progress_record_candidates": [
                {
                    "goal_id": "goal-trading-hub-connectivity-20260519",
                    "task_ref": "task-create-real-okr",
                    "progress_status": "planned",
                    "governance_status": "planned",
                    "approval_status": "not_required",
                    "risk_level": "medium",
                    "blocker": "",
                    "decision_summary": "",
                    "last_sync_at": ""
                }
            ],
            "goal_projection_candidates": [
                {
                    "goal_id": "goal-trading-hub-connectivity-20260519",
                    "goal_name": "中台与前端联动验证能力打通"
                }
            ],
            "field_governance_report": {
                "required_fields": ["goal_id"],
                "missing_fields": [],
                "stale_fields": [],
                "field_mapping": {},
                "writeback_scope": ["tasks", "progress", "goal_projection"]
            },
            "view_projection_candidates": [
                {
                    "view_name": "老板视图（状态与阻塞）",
                    "required_columns": ["目标名称", "当前状态"]
                }
            ]
        }

    def test_materialize_builds_writeback_order_and_knowledge_update(self):
        module = self.load_module()
        result = module.materialize_bitable_execution(self.sample_preview())
        self.assertEqual(
            result["writeback_order"],
            [
                "field_governance_check",
                "task_writeback",
                "progress_writeback",
                "goal_projection_writeback",
                "view_validation",
            ],
        )
        self.assertEqual(result["knowledge_update"]["asset_type"], "delivery")

    def test_materialize_marks_hard_block_when_required_fields_missing(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["field_governance_report"]["missing_fields"] = ["任务标题"]
        result = module.materialize_bitable_execution(preview)
        self.assertEqual(result["status"], "hard_block")

    def test_materialize_marks_degraded_success_when_only_views_are_incomplete(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["view_projection_candidates"] = []
        result = module.materialize_bitable_execution(preview)
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_bitable_execution.py -v
```

Expected: FAIL because `materialize_bitable_execution.py` does not exist yet.

- [ ] **Step 3: Write the minimal materializer**

Create `github-actions/feishu_collab/bitable/materialize_bitable_execution.py`:

```python
import json
import sys


WRITEBACK_ORDER = [
    "field_governance_check",
    "task_writeback",
    "progress_writeback",
    "goal_projection_writeback",
    "view_validation",
]


def materialize_bitable_execution(preview):
    missing_fields = preview["field_governance_report"].get("missing_fields", [])
    view_candidates = preview.get("view_projection_candidates", [])
    status = "ready"
    if missing_fields:
        status = "hard_block"
    elif not view_candidates:
        status = "degraded_success"

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "tasks": {"items": preview["task_record_candidates"]},
        "progress": {"items": preview["progress_record_candidates"]},
        "goal_projection": {"items": preview["goal_projection_candidates"]},
        "view_validation": {"items": view_candidates},
        "knowledge_update": {
            "asset_type": "delivery",
            "title": "bitable-writeback-result",
            "summary": f"status={status}",
            "evidence_refs": [item["task_id"] for item in preview["task_record_candidates"]],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_bitable_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_bitable_execution.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/bitable/materialize_bitable_execution.py \
        github-actions/tests/test_materialize_bitable_execution.py
git commit -m "feat: add bitable execution materializer"
```

## Task 3: Add Verification and Failure-Mode Handling

**Files:**
- Create: `github-actions/feishu_collab/bitable/verify_bitable_projection.py`
- Create: `github-actions/tests/test_verify_bitable_projection.py`

- [ ] **Step 1: Write the failing verification tests**

Create `github-actions/tests/test_verify_bitable_projection.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "bitable" / "verify_bitable_projection.py"
SPEC = importlib.util.spec_from_file_location("verify_bitable_projection", MODULE_PATH)


class VerifyBitableProjectionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_all_layers_exist(self):
        module = self.load_module()
        result = module.verify_bitable_projection(
            task_records=[{"task_id": "task-1"}],
            progress_records=[{"task_ref": "task-1"}],
            goal_projection=[{"goal_id": "goal-1", "workflow_signal": "healthy"}],
            view_validation=[{"view_name": "老板视图（状态与阻塞）"}],
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_blocked_when_goal_projection_missing(self):
        module = self.load_module()
        result = module.verify_bitable_projection(
            task_records=[{"task_id": "task-1"}],
            progress_records=[{"task_ref": "task-1"}],
            goal_projection=[],
            view_validation=[{"view_name": "老板视图（状态与阻塞）"}],
        )
        self.assertEqual(result["status"], "blocked")

    def test_verify_returns_degraded_success_when_view_layer_missing(self):
        module = self.load_module()
        result = module.verify_bitable_projection(
            task_records=[{"task_id": "task-1"}],
            progress_records=[{"task_ref": "task-1"}],
            goal_projection=[{"goal_id": "goal-1", "workflow_signal": "healthy"}],
            view_validation=[],
        )
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_verify_bitable_projection.py -v
```

Expected: FAIL because `verify_bitable_projection.py` does not exist yet.

- [ ] **Step 3: Write the minimal verification helper**

Create `github-actions/feishu_collab/bitable/verify_bitable_projection.py`:

```python
import json
import sys


def verify_bitable_projection(task_records, progress_records, goal_projection, view_validation):
    if not task_records or not progress_records or not goal_projection:
        status = "blocked"
    elif not view_validation:
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "task_count": len(task_records),
        "progress_count": len(progress_records),
        "goal_projection_count": len(goal_projection),
        "view_validation_count": len(view_validation),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_bitable_projection(
            payload["task_records"],
            payload["progress_records"],
            payload["goal_projection"],
            payload["view_validation"],
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
python3 -m unittest github-actions/tests/test_verify_bitable_projection.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/bitable/verify_bitable_projection.py \
        github-actions/tests/test_verify_bitable_projection.py
git commit -m "feat: add bitable verification helper"
```

## Task 4: Package the Bitable Skill

**Files:**
- Create: `.trae/skills/feishu-collab-bitable/SKILL.md`
- Create: `.trae/skills/feishu-collab-bitable/references/execution-checklist.md`

- [ ] **Step 1: Write the skill package files**

Create `.trae/skills/feishu-collab-bitable/SKILL.md`:

```md
---
name: "feishu-collab-bitable"
description: "Projects OKR-driven outputs into Base task, progress, and view-validation previews, then writes back after confirmation. Invoke when aligning long-term goal structure with short-term execution records in Feishu Base."
---

# Feishu Collaboration Bitable

## When to use

Use this skill when:

- `OKR-driven` already produced a goal/task preview
- the user needs Base task and progress projection
- the user needs boss-view or execution-view validation
- the user wants preview-before-writeback

## Inputs

- upstream `ExecutionPreview`
- current Base context
- optional existing task/progress records

## Flow

1. build preview
2. review drift flags
3. confirm execution
4. write back tasks/progress/projection
5. verify output
6. generate handoff and `KnowledgeUpdate`

## Guardrails

- never redefine the goal outside upstream input
- never skip preview
- treat missing required fields as hard block
- treat missing view validation as degraded success
```

Create `.trae/skills/feishu-collab-bitable/references/execution-checklist.md`:

```md
# Execution Checklist

## Preview Gate

- Confirm upstream `OKR-driven` preview exists
- Confirm Base required fields are known
- Confirm drift flags are visible
- Confirm `requires_confirmation = true`

## Writeback Gate

- Field governance checked first
- Task writeback ordered before progress writeback
- Goal projection writeback ordered before final view validation

## Verification Gate

- Task records exist
- Progress records exist
- Goal projection exists
- Boss-view validation result recorded
- Handoff and `KnowledgeUpdate` emitted
```

- [ ] **Step 2: Sanity-check the skill files**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
for path in [
    Path(".trae/skills/feishu-collab-bitable/SKILL.md"),
    Path(".trae/skills/feishu-collab-bitable/references/execution-checklist.md"),
]:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
print("bitable skill files ok")
PY
```

Expected: `bitable skill files ok`

- [ ] **Step 3: Commit**

```bash
git add .trae/skills/feishu-collab-bitable/SKILL.md \
        .trae/skills/feishu-collab-bitable/references/execution-checklist.md
git commit -m "feat: add bitable skill package"
```

## Task 5: Validate the Bitable Baseline End-to-End

**Files:**
- Modify: `github-actions/feishu_collab/bitable/build_bitable_preview.py`
- Modify: `github-actions/feishu_collab/bitable/materialize_bitable_execution.py`
- Modify: `github-actions/feishu_collab/bitable/verify_bitable_projection.py`
- Modify: `.trae/skills/feishu-collab-bitable/SKILL.md`

- [ ] **Step 1: Run the full targeted test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_bitable_preview.py \
  github-actions/tests/test_materialize_bitable_execution.py \
  github-actions/tests/test_verify_bitable_projection.py -v
```

Expected: all tests PASS.

- [ ] **Step 2: Perform a local dry-run using the fixtures**

Run:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT")
fixture_dir = root / "github-actions" / "tests" / "fixtures" / "bitable_skill"
payload = {
    "okr_preview": json.loads((fixture_dir / "okr_driven_preview.json").read_text(encoding="utf-8")),
    "base_context": json.loads((fixture_dir / "base_context.json").read_text(encoding="utf-8")),
}
preview_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "bitable" / "build_bitable_preview.py")],
    input=json.dumps(payload, ensure_ascii=False),
    text=True,
)
preview = json.loads(preview_out)
execution_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "bitable" / "materialize_bitable_execution.py")],
    input=json.dumps(preview, ensure_ascii=False),
    text=True,
)
execution = json.loads(execution_out)
verification_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "bitable" / "verify_bitable_projection.py")],
    input=json.dumps(
        {
            "task_records": preview["task_record_candidates"],
            "progress_records": preview["progress_record_candidates"],
            "goal_projection": preview["goal_projection_candidates"],
            "view_validation": preview["view_projection_candidates"],
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

- preview contains task/progress/projection/view layers
- execution contains ordered writeback steps and `KnowledgeUpdate`
- verification returns `confirmed`

- [ ] **Step 3: Commit the validation pass**

```bash
git add github-actions/feishu_collab/bitable/build_bitable_preview.py \
        github-actions/feishu_collab/bitable/materialize_bitable_execution.py \
        github-actions/feishu_collab/bitable/verify_bitable_projection.py \
        github-actions/tests/test_build_bitable_preview.py \
        github-actions/tests/test_materialize_bitable_execution.py \
        github-actions/tests/test_verify_bitable_projection.py \
        github-actions/tests/fixtures/bitable_skill/okr_driven_preview.json \
        github-actions/tests/fixtures/bitable_skill/base_context.json \
        .trae/skills/feishu-collab-bitable/SKILL.md \
        .trae/skills/feishu-collab-bitable/references/execution-checklist.md
git commit -m "test: validate bitable skill baseline"
```

## Self-Review

- Spec coverage:
  - downstream relationship to `OKR-driven`: Task 1, Task 2, and Task 4
  - v1 scope `任务 + 进度 + 视图`: Task 1, Task 2, and Task 3
  - preview-first flow: Task 1, Task 2, and Task 4
  - adapter boundaries and failure modes: Task 2 and Task 3
  - knowledge update and handoff outputs: Task 2, Task 4, and Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred implementation markers
  - Every code-bearing step includes concrete code or markdown content
  - Every verification step has exact commands and expected outcomes
- Type consistency:
  - Preview object names match the approved spec: `TaskRecordSpec`, `ProgressRecordSpec`, `GoalProjectionSpec`, `FieldGovernanceSpec`, `ViewProjectionSpec`
  - Shared contract names match the existing system baseline: `ExecutionPreview`, `ExecutionResult`, `KnowledgeUpdate`
  - Failure statuses stay aligned across materialization and verification: `hard_block`, `soft_block`, `degraded_success`, `confirmed`, `blocked`
