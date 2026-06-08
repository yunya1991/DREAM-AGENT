# Real Knowledge Materialization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated real-knowledge-materialization workflow that consumes approval and polling artifacts, writes real runbook and handoff documents into the governed docs tree, updates both knowledge indexes, emits a materialization result artifact, and supports stable reruns for the same `task_id`.

**Architecture:** Keep the workflow thin and split the implementation into five focused units: one payload builder that converts approval/polling artifacts into stable document specs, one real materializer that writes the runbook and handoff files, one index updater that deduplicates and updates `RUNBOOK_INDEX.md` and `HANDOFF_INDEX.md`, one workflow-only summary helper, and one standalone `.github/workflows/knowledge-materialization.yml`. Reuse the existing Knowledge-Ops pathing/templates where they fit, but upgrade from simulated materialize results to real file writes and index alignment checks.

**Tech Stack:** Python 3, `unittest`, Markdown, GitHub Actions YAML, existing Knowledge-Ops helpers in `github-actions/feishu_collab/knowledge_ops/`, JSON artifacts, governed docs under `docs/feishu-collab/`

---

## Scope Check

This plan covers one coherent sub-project:

- Build a real payload builder for approval/polling knowledge inputs
- Materialize one runbook and one handoff document to governed paths
- Update `RUNBOOK_INDEX.md` and `HANDOFF_INDEX.md` with deduped entries
- Add a workflow-only summary helper and standalone `workflow_dispatch` workflow
- Add operator-facing docs and targeted validation for real knowledge materialization

It does **not** include:

- Approval creation
- Approval instance querying
- Base writeback
- Multi-source registry-driven knowledge ingestion
- Governance-document materialization
- Knowledge search UI or dashboards

## File Map

- Create: `github-actions/feishu_collab/knowledge_ops/build_real_knowledge_payload.py`
  - Convert `approval_status_result`, `approval_writeback_result`, and `materialization_context` into stable runbook/handoff specs and governed output paths.
- Create: `github-actions/tests/test_build_real_knowledge_payload.py`
  - Lock task-id based filenames, document titles, and payload field mapping.
- Create: `github-actions/feishu_collab/knowledge_ops/materialize_real_knowledge_assets.py`
  - Render and write the runbook/handoff Markdown files from the existing templates and return per-document results.
- Create: `github-actions/tests/test_materialize_real_knowledge_assets.py`
  - Lock real file writes, overwrite-on-rerun behavior, and partial-failure evidence.
- Create: `github-actions/feishu_collab/knowledge_ops/update_knowledge_indexes.py`
  - Insert or replace the runbook/handoff entries in the two index files without duplication.
- Create: `github-actions/tests/test_update_knowledge_indexes.py`
  - Lock index insertion, deduplication, and stable rerun behavior.
- Create: `github-actions/run_real_knowledge_materialization.py`
  - Orchestrate payload building, real file writes, and index updates; emit `knowledge_materialization_result.json`.
- Create: `github-actions/tests/test_run_real_knowledge_materialization.py`
  - Lock the top-level result shape, failure propagation, and evidence retention.
- Create: `github-actions/render_real_knowledge_materialization_summary.py`
  - Render Job Summary from the materialization result and compute workflow exit code.
- Create: `github-actions/tests/test_render_real_knowledge_materialization_summary.py`
  - Lock summary content and exit semantics.
- Create: `.github/workflows/knowledge-materialization.yml`
  - Standalone `workflow_dispatch` workflow for real knowledge materialization.
- Create: `github-actions/tests/test_knowledge_materialization_workflow.py`
  - Lock required workflow inputs, helper calls, and artifact upload behavior.
- Create: `docs/feishu-collab/runbooks/knowledge-materialization.md`
  - Operator-facing workflow runbook for the fourth phase.
- Modify: `docs/feishu-collab/RUNBOOK_INDEX.md`
  - Register the new materialization runbook in the operator index.
- Create: `github-actions/tests/test_real_knowledge_materialization_docs.py`
  - Lock workflow runbook discoverability and index registration.

## Execution Guardrails

- Do not re-query approval state in the fourth-phase workflow; consume upstream JSON inputs as the source of truth.
- Do not re-run Base writeback logic inside the knowledge workflow.
- Keep generated paths stable for the same `task_id` so reruns overwrite instead of multiplying files.
- Update indexes only after both target documents are written successfully enough to reference.
- If runbook write fails, stop immediately and do not attempt handoff.
- If handoff write fails, keep the runbook file and report partial success as a failed overall materialization.
- Preserve any successfully written document files even when index updates fail.
- Reuse the existing runbook/handoff templates instead of inventing a second documentation format.

## Task 1: Build the Real Knowledge Payload Builder

**Files:**
- Create: `github-actions/feishu_collab/knowledge_ops/build_real_knowledge_payload.py`
- Create: `github-actions/tests/test_build_real_knowledge_payload.py`

- [ ] **Step 1: Write the failing payload-builder test**

Create `github-actions/tests/test_build_real_knowledge_payload.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "build_real_knowledge_payload.py"
SPEC = importlib.util.spec_from_file_location("build_real_knowledge_payload", MODULE_PATH)


class BuildRealKnowledgePayloadTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_payload_creates_stable_runbook_and_handoff_specs(self):
        module = self.load_module()
        payload = module.build_real_knowledge_payload(
            approval_status_result={
                "approval_instance_code": "ins_123",
                "approval_status": "pending",
                "automation_status": "paused",
                "decision_summary": "pending:TASK-123",
            },
            approval_writeback_result={
                "task_id": "TASK-123",
                "goal_id": "GOAL-123",
                "task_writeback_status": "success",
                "goal_writeback_status": "success",
            },
            materialization_context={
                "workflow_name": "approval-polling-writeback",
                "operator_summary": "Approval waiting for review",
            },
        )

        self.assertEqual(
            payload["runbook"]["target_path"],
            "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
        )
        self.assertEqual(
            payload["handoff"]["target_path"],
            "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
        )
        self.assertEqual(payload["runbook"]["title"], "Approval TASK-123 Runbook")
        self.assertEqual(payload["handoff"]["title"], "Approval TASK-123 Handoff")
        self.assertEqual(payload["source_refs"]["approval_instance_code"], "ins_123")
        self.assertEqual(payload["source_refs"]["task_id"], "TASK-123")
        self.assertEqual(payload["source_refs"]["goal_id"], "GOAL-123")
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_real_knowledge_payload.py -v
```

Expected: FAIL because `build_real_knowledge_payload.py` does not exist yet.

- [ ] **Step 3: Write the minimal payload-builder implementation**

Create `github-actions/feishu_collab/knowledge_ops/build_real_knowledge_payload.py`:

```python
def _doc_slug(task_id, suffix):
    return f"approval-{task_id.lower()}-{suffix}.md"


def build_real_knowledge_payload(
    approval_status_result,
    approval_writeback_result,
    materialization_context,
):
    task_id = approval_writeback_result.get("task_id", "").strip()
    goal_id = approval_writeback_result.get("goal_id", "").strip()
    instance_code = approval_status_result.get("approval_instance_code", "").strip()

    return {
        "source_refs": {
            "approval_instance_code": instance_code,
            "task_id": task_id,
            "goal_id": goal_id,
        },
        "runbook": {
            "title": f"Approval {task_id} Runbook",
            "target_path": f"docs/feishu-collab/runbooks/{_doc_slug(task_id, 'runbook')}",
            "index_path": "docs/feishu-collab/RUNBOOK_INDEX.md",
            "content_context": {
                "approval_status_result": approval_status_result,
                "approval_writeback_result": approval_writeback_result,
                "materialization_context": materialization_context,
            },
        },
        "handoff": {
            "title": f"Approval {task_id} Handoff",
            "target_path": f"docs/feishu-collab/handoffs/{_doc_slug(task_id, 'handoff')}",
            "index_path": "docs/feishu-collab/HANDOFF_INDEX.md",
            "content_context": {
                "approval_status_result": approval_status_result,
                "approval_writeback_result": approval_writeback_result,
                "materialization_context": materialization_context,
            },
        },
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_real_knowledge_payload.py -v
```

Expected: PASS with the stable path and title assertions green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/build_real_knowledge_payload.py \
        github-actions/tests/test_build_real_knowledge_payload.py
git commit -m "feat: add real knowledge payload builder"
```

## Task 2: Materialize Real Runbook and Handoff Files

**Files:**
- Create: `github-actions/feishu_collab/knowledge_ops/materialize_real_knowledge_assets.py`
- Create: `github-actions/tests/test_materialize_real_knowledge_assets.py`

- [ ] **Step 1: Write the failing materialization tests**

Create `github-actions/tests/test_materialize_real_knowledge_assets.py`:

```python
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "materialize_real_knowledge_assets.py"
SPEC = importlib.util.spec_from_file_location("materialize_real_knowledge_assets", MODULE_PATH)


class MaterializeRealKnowledgeAssetsTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_materialize_assets_writes_both_documents(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            runbook_path = repo_root / "docs/feishu-collab/runbooks/approval-task-123-runbook.md"
            handoff_path = repo_root / "docs/feishu-collab/handoffs/approval-task-123-handoff.md"
            runbook_path.parent.mkdir(parents=True, exist_ok=True)
            handoff_path.parent.mkdir(parents=True, exist_ok=True)

            result = module.materialize_real_knowledge_assets(
                repo_root=repo_root,
                payload={
                    "source_refs": {
                        "approval_instance_code": "ins_123",
                        "task_id": "TASK-123",
                        "goal_id": "GOAL-123",
                    },
                    "runbook": {
                        "title": "Approval TASK-123 Runbook",
                        "target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                    },
                    "handoff": {
                        "title": "Approval TASK-123 Handoff",
                        "target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                    },
                },
                approval_status_result={
                    "approval_instance_code": "ins_123",
                    "approval_status": "pending",
                    "automation_status": "paused",
                    "decision_summary": "pending:TASK-123",
                },
                approval_writeback_result={
                    "task_id": "TASK-123",
                    "goal_id": "GOAL-123",
                    "task_writeback_status": "success",
                    "goal_writeback_status": "success",
                },
            )

            self.assertEqual(result["runbook"]["write_status"], "success")
            self.assertEqual(result["handoff"]["write_status"], "success")
            self.assertTrue(runbook_path.exists())
            self.assertTrue(handoff_path.exists())
            self.assertIn("Approval TASK-123 Runbook", runbook_path.read_text(encoding="utf-8"))
            self.assertIn("Approval TASK-123 Handoff", handoff_path.read_text(encoding="utf-8"))

    def test_handoff_failure_keeps_runbook_result(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / "docs/feishu-collab/runbooks").mkdir(parents=True, exist_ok=True)
            handoff_parent = repo_root / "docs/feishu-collab/handoffs"
            handoff_parent.mkdir(parents=True, exist_ok=True)
            handoff_parent.chmod(0o400)
            try:
                result = module.materialize_real_knowledge_assets(
                    repo_root=repo_root,
                    payload={
                        "source_refs": {"approval_instance_code": "ins_123", "task_id": "TASK-123", "goal_id": "GOAL-123"},
                        "runbook": {
                            "title": "Approval TASK-123 Runbook",
                            "target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                        },
                        "handoff": {
                            "title": "Approval TASK-123 Handoff",
                            "target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                        },
                    },
                    approval_status_result={"approval_instance_code": "ins_123", "approval_status": "pending"},
                    approval_writeback_result={"task_id": "TASK-123", "goal_id": "GOAL-123"},
                )
            finally:
                handoff_parent.chmod(0o700)

            self.assertEqual(result["runbook"]["write_status"], "success")
            self.assertEqual(result["handoff"]["write_status"], "failed")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_real_knowledge_assets.py -v
```

Expected: FAIL because `materialize_real_knowledge_assets.py` does not exist yet.

- [ ] **Step 3: Write the minimal real-materialization implementation**

Create `github-actions/feishu_collab/knowledge_ops/materialize_real_knowledge_assets.py`:

```python
from pathlib import Path


RUNBOOK_TEMPLATE = """# {title}

## Trigger

- Approval Instance Code: `{approval_instance_code}`

## Scope

- Task ID: `{task_id}`
- Goal ID: `{goal_id}`

## Preconditions

- Approval Status: `{approval_status}`
- Automation Status: `{automation_status}`

## Detection

- Decision Summary: `{decision_summary}`

## Investigation Steps

- Review approval artifact and writeback artifact.

## Recovery Steps

- Continue from the current approval and Base writeback state.

## Verification

- Task Writeback: `{task_writeback_status}`
- Goal Writeback: `{goal_writeback_status}`

## Escalation

- Escalate if status and Base writeback drift again.

## Evidence To Capture

- Approval Instance Code: `{approval_instance_code}`
- Task ID: `{task_id}`
- Goal ID: `{goal_id}`

## Follow-up Knowledge Update

- Sync handoff after state changes.
"""


HANDOFF_TEMPLATE = """# {title}

## Background

- Approval Instance Code: `{approval_instance_code}`

## Current State

- Approval Status: `{approval_status}`
- Automation Status: `{automation_status}`

## Completed Work

- Task Writeback: `{task_writeback_status}`
- Goal Writeback: `{goal_writeback_status}`

## Remaining Work

- Continue approval follow-up until final decision lands.

## Active Blocker

- Pending approval decision.

## Next Action

- Review the latest approval result and rerun writeback if state changes.

## Dependencies

- Task ID: `{task_id}`
- Goal ID: `{goal_id}`

## Risk Notes

- Keep knowledge documents aligned with approval state.

## Evidence Links

- Decision Summary: `{decision_summary}`

## Handover Focus

- Preserve approval state, Base state, and rerun path.
"""


def _render_context(source_refs, approval_status_result, approval_writeback_result, title):
    return {
        "title": title,
        "approval_instance_code": source_refs.get("approval_instance_code", ""),
        "task_id": approval_writeback_result.get("task_id", source_refs.get("task_id", "")),
        "goal_id": approval_writeback_result.get("goal_id", source_refs.get("goal_id", "")),
        "approval_status": approval_status_result.get("approval_status", ""),
        "automation_status": approval_status_result.get("automation_status", ""),
        "decision_summary": approval_status_result.get("decision_summary", ""),
        "task_writeback_status": approval_writeback_result.get("task_writeback_status", ""),
        "goal_writeback_status": approval_writeback_result.get("goal_writeback_status", ""),
    }


def _write_text(repo_root, target_path, text):
    path = Path(repo_root) / target_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def materialize_real_knowledge_assets(
    repo_root,
    payload,
    approval_status_result,
    approval_writeback_result,
):
    source_refs = payload.get("source_refs", {})
    runbook = payload["runbook"]
    handoff = payload["handoff"]

    runbook_ctx = _render_context(source_refs, approval_status_result, approval_writeback_result, runbook["title"])
    runbook_text = RUNBOOK_TEMPLATE.format(**runbook_ctx)
    runbook_result = {
        "target_path": runbook["target_path"],
        "title": runbook["title"],
        "write_status": "failed",
        "index_status": "pending",
    }
    handoff_result = {
        "target_path": handoff["target_path"],
        "title": handoff["title"],
        "write_status": "skipped",
        "index_status": "pending",
    }

    try:
        _write_text(repo_root, runbook["target_path"], runbook_text)
        runbook_result["write_status"] = "success"
    except Exception as exc:
        runbook_result["error"] = str(exc)
        return {"runbook": runbook_result, "handoff": handoff_result}

    try:
        handoff_ctx = _render_context(source_refs, approval_status_result, approval_writeback_result, handoff["title"])
        handoff_text = HANDOFF_TEMPLATE.format(**handoff_ctx)
        _write_text(repo_root, handoff["target_path"], handoff_text)
        handoff_result["write_status"] = "success"
    except Exception as exc:
        handoff_result["write_status"] = "failed"
        handoff_result["error"] = str(exc)

    return {"runbook": runbook_result, "handoff": handoff_result}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_real_knowledge_assets.py -v
```

Expected: PASS with real file-write and partial-failure assertions green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/materialize_real_knowledge_assets.py \
        github-actions/tests/test_materialize_real_knowledge_assets.py
git commit -m "feat: add real knowledge materializer"
```

## Task 3: Update the Runbook and Handoff Indexes

**Files:**
- Create: `github-actions/feishu_collab/knowledge_ops/update_knowledge_indexes.py`
- Create: `github-actions/tests/test_update_knowledge_indexes.py`

- [ ] **Step 1: Write the failing index-updater tests**

Create `github-actions/tests/test_update_knowledge_indexes.py`:

```python
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "update_knowledge_indexes.py"
SPEC = importlib.util.spec_from_file_location("update_knowledge_indexes", MODULE_PATH)


class UpdateKnowledgeIndexesTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_update_indexes_inserts_new_entries(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            runbook_index = repo_root / "docs/feishu-collab/RUNBOOK_INDEX.md"
            handoff_index = repo_root / "docs/feishu-collab/HANDOFF_INDEX.md"
            runbook_index.parent.mkdir(parents=True, exist_ok=True)
            runbook_index.write_text(
                "# Runbook Index\n\n## Entries\n\n| Runbook | Path | Purpose |\n| --- | --- | --- |\n",
                encoding="utf-8",
            )
            handoff_index.write_text(
                "# Handoff Index\n\n## Entries\n\n| Handoff | Path | Purpose |\n| --- | --- | --- |\n",
                encoding="utf-8",
            )

            result = module.update_knowledge_indexes(
                repo_root=repo_root,
                runbook_entry={
                    "title": "Approval TASK-123 Runbook",
                    "path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                    "purpose": "Track approval TASK-123 recovery and verification",
                },
                handoff_entry={
                    "title": "Approval TASK-123 Handoff",
                    "path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                    "purpose": "Hand off approval TASK-123 next actions",
                },
            )

            self.assertEqual(result["runbook_index_status"], "success")
            self.assertEqual(result["handoff_index_status"], "success")
            self.assertIn("Approval TASK-123 Runbook", runbook_index.read_text(encoding="utf-8"))
            self.assertIn("Approval TASK-123 Handoff", handoff_index.read_text(encoding="utf-8"))

    def test_update_indexes_deduplicates_existing_entries(self):
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            runbook_index = repo_root / "docs/feishu-collab/RUNBOOK_INDEX.md"
            handoff_index = repo_root / "docs/feishu-collab/HANDOFF_INDEX.md"
            runbook_index.parent.mkdir(parents=True, exist_ok=True)
            runbook_index.write_text(
                "# Runbook Index\n\n## Entries\n\n| Runbook | Path | Purpose |\n| --- | --- | --- |\n| Approval TASK-123 Runbook | `docs/feishu-collab/runbooks/approval-task-123-runbook.md` | Existing |\n",
                encoding="utf-8",
            )
            handoff_index.write_text(
                "# Handoff Index\n\n## Entries\n\n| Handoff | Path | Purpose |\n| --- | --- | --- |\n| Approval TASK-123 Handoff | `docs/feishu-collab/handoffs/approval-task-123-handoff.md` | Existing |\n",
                encoding="utf-8",
            )

            module.update_knowledge_indexes(
                repo_root=repo_root,
                runbook_entry={
                    "title": "Approval TASK-123 Runbook",
                    "path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md",
                    "purpose": "Updated purpose",
                },
                handoff_entry={
                    "title": "Approval TASK-123 Handoff",
                    "path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md",
                    "purpose": "Updated purpose",
                },
            )

            self.assertEqual(runbook_index.read_text(encoding="utf-8").count("Approval TASK-123 Runbook"), 1)
            self.assertEqual(handoff_index.read_text(encoding="utf-8").count("Approval TASK-123 Handoff"), 1)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest github-actions/tests/test_update_knowledge_indexes.py -v
```

Expected: FAIL because `update_knowledge_indexes.py` does not exist yet.

- [ ] **Step 3: Write the minimal index-updater implementation**

Create `github-actions/feishu_collab/knowledge_ops/update_knowledge_indexes.py`:

```python
from pathlib import Path


def _replace_or_append(text, marker, line_prefix, new_line):
    lines = text.splitlines()
    result = []
    replaced = False
    inserted = False
    for line in lines:
        if line.startswith(line_prefix):
            if not replaced:
                result.append(new_line)
                replaced = True
            continue
        result.append(line)
        if line.strip() == marker and not inserted:
            inserted = True
    if not replaced:
        try:
            idx = result.index(marker)
        except ValueError:
            result.append(marker)
            idx = len(result) - 1
        result.insert(idx + 1, new_line)
    return "\n".join(result) + "\n"


def update_knowledge_indexes(repo_root, runbook_entry, handoff_entry):
    repo_root = Path(repo_root)
    runbook_index = repo_root / "docs/feishu-collab/RUNBOOK_INDEX.md"
    handoff_index = repo_root / "docs/feishu-collab/HANDOFF_INDEX.md"

    runbook_line = f"| {runbook_entry['title']} | `{runbook_entry['path']}` | {runbook_entry['purpose']} |"
    handoff_line = f"| {handoff_entry['title']} | `{handoff_entry['path']}` | {handoff_entry['purpose']} |"

    runbook_text = runbook_index.read_text(encoding="utf-8")
    runbook_text = _replace_or_append(
        runbook_text,
        "| --- | --- | --- |",
        f"| {runbook_entry['title']} |",
        runbook_line,
    )
    runbook_index.write_text(runbook_text, encoding="utf-8")

    handoff_text = handoff_index.read_text(encoding="utf-8")
    handoff_text = _replace_or_append(
        handoff_text,
        "| --- | --- | --- |",
        f"| {handoff_entry['title']} |",
        handoff_line,
    )
    handoff_index.write_text(handoff_text, encoding="utf-8")

    return {
        "runbook_index_status": "success",
        "handoff_index_status": "success",
    }
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest github-actions/tests/test_update_knowledge_indexes.py -v
```

Expected: PASS with insertion and deduplication assertions green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/update_knowledge_indexes.py \
        github-actions/tests/test_update_knowledge_indexes.py
git commit -m "feat: add knowledge index updater"
```

## Task 4: Orchestrate Real Materialization, Summary, and Workflow

**Files:**
- Create: `github-actions/run_real_knowledge_materialization.py`
- Create: `github-actions/tests/test_run_real_knowledge_materialization.py`
- Create: `github-actions/render_real_knowledge_materialization_summary.py`
- Create: `github-actions/tests/test_render_real_knowledge_materialization_summary.py`
- Create: `.github/workflows/knowledge-materialization.yml`
- Create: `github-actions/tests/test_knowledge_materialization_workflow.py`

- [ ] **Step 1: Write the failing orchestration and workflow tests**

Create `github-actions/tests/test_run_real_knowledge_materialization.py`:

```python
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_real_knowledge_materialization.py"
SPEC = importlib.util.spec_from_file_location("run_real_knowledge_materialization", MODULE_PATH)


class RunRealKnowledgeMaterializationTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    @patch("run_real_knowledge_materialization.UPDATE.update_knowledge_indexes")
    @patch("run_real_knowledge_materialization.MATERIALIZE.materialize_real_knowledge_assets")
    @patch("run_real_knowledge_materialization.BUILDER.build_real_knowledge_payload")
    def test_run_materialization_returns_combined_result(self, mock_build, mock_materialize, mock_update):
        mock_build.return_value = {
            "source_refs": {
                "approval_instance_code": "ins_123",
                "task_id": "TASK-123",
                "goal_id": "GOAL-123",
            },
            "runbook": {"title": "Approval TASK-123 Runbook", "target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md"},
            "handoff": {"title": "Approval TASK-123 Handoff", "target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md"},
        }
        mock_materialize.return_value = {
            "runbook": {"target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md", "write_status": "success"},
            "handoff": {"target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md", "write_status": "success"},
        }
        mock_update.return_value = {
            "runbook_index_status": "success",
            "handoff_index_status": "success",
        }
        module = self.load_module()
        result = module.run_materialization(
            repo_root=ROOT,
            payload={
                "approval_status_result": {"approval_instance_code": "ins_123"},
                "approval_writeback_result": {"task_id": "TASK-123", "goal_id": "GOAL-123"},
                "materialization_context": {"workflow_name": "approval-polling-writeback"},
            },
        )
        self.assertEqual(result["materialization_status"], "success")
        self.assertEqual(result["runbook"]["target_path"], "docs/feishu-collab/runbooks/approval-task-123-runbook.md")
        self.assertEqual(result["handoff"]["target_path"], "docs/feishu-collab/handoffs/approval-task-123-handoff.md")
```

Create `github-actions/tests/test_render_real_knowledge_materialization_summary.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_real_knowledge_materialization_summary.py"
SPEC = importlib.util.spec_from_file_location("render_real_knowledge_materialization_summary", MODULE_PATH)


class RenderRealKnowledgeMaterializationSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_result(self, status="success"):
        return {
            "materialization_status": status,
            "source_refs": {
                "task_id": "TASK-123",
                "goal_id": "GOAL-123",
                "approval_instance_code": "ins_123",
            },
            "runbook": {"target_path": "docs/feishu-collab/runbooks/approval-task-123-runbook.md"},
            "handoff": {"target_path": "docs/feishu-collab/handoffs/approval-task-123-handoff.md"},
            "index_update_status": "success",
        }

    def test_summary_renders_paths_and_status(self):
        module = self.load_module()
        summary = module.build_summary_markdown(self.sample_result())
        self.assertIn("TASK-123", summary)
        self.assertIn("GOAL-123", summary)
        self.assertIn("ins_123", summary)
        self.assertIn("approval-task-123-runbook.md", summary)
        self.assertIn("success", summary)

    def test_exit_code_requires_full_success(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_result()), 0)
        self.assertEqual(module.workflow_exit_code(self.sample_result(status="failed")), 1)
```

Create `github-actions/tests/test_knowledge_materialization_workflow.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class KnowledgeMaterializationWorkflowTests(unittest.TestCase):
    def read_workflow(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "knowledge-materialization.yml"
        return workflow.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "knowledge-materialization.yml"
        self.assertTrue(workflow.exists(), str(workflow))

    def test_workflow_declares_required_inputs(self):
        text = self.read_workflow()
        self.assertIn("approval_status_result_json:", text)
        self.assertIn("approval_writeback_result_json:", text)
        self.assertIn("materialization_context_json:", text)

    def test_workflow_calls_runner_and_summary(self):
        text = self.read_workflow()
        self.assertIn("python3 github-actions/run_real_knowledge_materialization.py", text)
        self.assertIn("python3 github-actions/render_real_knowledge_materialization_summary.py", text)

    def test_workflow_uploads_artifacts_even_on_failure(self):
        text = self.read_workflow()
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("knowledge_materialization_result.json", text)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_run_real_knowledge_materialization.py \
  github-actions/tests/test_render_real_knowledge_materialization_summary.py \
  github-actions/tests/test_knowledge_materialization_workflow.py -v
```

Expected: FAIL because the runner, summary helper, and workflow do not exist yet.

- [ ] **Step 3: Write the minimal orchestration, summary helper, and workflow**

Create `github-actions/run_real_knowledge_materialization.py`:

```python
import importlib.util
import json
from pathlib import Path
import sys


HERE = Path(__file__).resolve().parent


def load_module(name, relative_path):
    path = HERE / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BUILDER = load_module("build_real_knowledge_payload", "feishu_collab/knowledge_ops/build_real_knowledge_payload.py")
MATERIALIZE = load_module("materialize_real_knowledge_assets", "feishu_collab/knowledge_ops/materialize_real_knowledge_assets.py")
UPDATE = load_module("update_knowledge_indexes", "feishu_collab/knowledge_ops/update_knowledge_indexes.py")


def run_materialization(repo_root, payload):
    approval_status_result = payload.get("approval_status_result", {})
    approval_writeback_result = payload.get("approval_writeback_result", {})
    materialization_context = payload.get("materialization_context", {})
    built = BUILDER.build_real_knowledge_payload(
        approval_status_result=approval_status_result,
        approval_writeback_result=approval_writeback_result,
        materialization_context=materialization_context,
    )
    written = MATERIALIZE.materialize_real_knowledge_assets(
        repo_root=repo_root,
        payload=built,
        approval_status_result=approval_status_result,
        approval_writeback_result=approval_writeback_result,
    )

    index_update_status = "skipped"
    if written["runbook"].get("write_status") == "success" and written["handoff"].get("write_status") == "success":
        index_result = UPDATE.update_knowledge_indexes(
            repo_root=repo_root,
            runbook_entry={
                "title": built["runbook"]["title"],
                "path": built["runbook"]["target_path"],
                "purpose": "Track approval materialization and recovery",
            },
            handoff_entry={
                "title": built["handoff"]["title"],
                "path": built["handoff"]["target_path"],
                "purpose": "Hand off approval follow-up work",
            },
        )
        written["runbook"]["index_status"] = index_result["runbook_index_status"]
        written["handoff"]["index_status"] = index_result["handoff_index_status"]
        index_update_status = "success"

    materialization_status = "success" if (
        written["runbook"].get("write_status") == "success"
        and written["handoff"].get("write_status") == "success"
        and written["runbook"].get("index_status") == "success"
        and written["handoff"].get("index_status") == "success"
    ) else "failed"

    return {
        "source_refs": built["source_refs"],
        "runbook": written["runbook"],
        "handoff": written["handoff"],
        "index_update_status": index_update_status,
        "materialization_status": materialization_status,
        "evidence_refs": [
            built["runbook"]["target_path"],
            built["handoff"]["target_path"],
        ],
        "failure_reason": "" if materialization_status == "success" else "materialization_incomplete",
    }


def main():
    payload = json.load(sys.stdin)
    result = run_materialization(repo_root=HERE.parent, payload=payload)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
```

Create `github-actions/render_real_knowledge_materialization_summary.py`:

```python
import json
import os
from pathlib import Path
import sys


def build_summary_markdown(result):
    lines = [
        "# Real Knowledge Materialization",
        "",
        f"- Task ID: `{result.get('source_refs', {}).get('task_id', '')}`",
        f"- Goal ID: `{result.get('source_refs', {}).get('goal_id', '')}`",
        f"- Approval Instance Code: `{result.get('source_refs', {}).get('approval_instance_code', '')}`",
        f"- Runbook Path: `{result.get('runbook', {}).get('target_path', '')}`",
        f"- Handoff Path: `{result.get('handoff', {}).get('target_path', '')}`",
        f"- Materialization Status: `{result.get('materialization_status', '')}`",
        f"- Index Update Status: `{result.get('index_update_status', '')}`",
        "",
    ]
    return "\n".join(lines)


def workflow_exit_code(result):
    return 0 if result.get("materialization_status") == "success" else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    result_path = Path(argv[0])
    result = json.loads(result_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(result)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary + "\n")
    else:
        sys.stdout.write(summary + "\n")
    raise SystemExit(workflow_exit_code(result))


if __name__ == "__main__":
    main()
```

Create `.github/workflows/knowledge-materialization.yml`:

```yaml
name: knowledge-materialization

on:
  workflow_dispatch:
    inputs:
      approval_status_result_json:
        description: Approval status result JSON
        required: true
        type: string
      approval_writeback_result_json:
        description: Approval writeback result JSON
        required: true
        type: string
      materialization_context_json:
        description: Knowledge materialization context JSON
        required: true
        type: string

permissions:
  contents: write

jobs:
  knowledge-materialization:
    runs-on: [self-hosted, macOS, workbuddy]
    steps:
      - name: Checkout workflow ref
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Build materialization payload
        env:
          APPROVAL_STATUS_RESULT_JSON: ${{ inputs.approval_status_result_json }}
          APPROVAL_WRITEBACK_RESULT_JSON: ${{ inputs.approval_writeback_result_json }}
          MATERIALIZATION_CONTEXT_JSON: ${{ inputs.materialization_context_json }}
        run: |
          python3 - <<'PY' > knowledge_materialization_input.json
          import json
          import os

          payload = {
              "approval_status_result": json.loads(os.environ["APPROVAL_STATUS_RESULT_JSON"]),
              "approval_writeback_result": json.loads(os.environ["APPROVAL_WRITEBACK_RESULT_JSON"]),
              "materialization_context": json.loads(os.environ["MATERIALIZATION_CONTEXT_JSON"]),
          }
          print(json.dumps(payload, ensure_ascii=False))
          PY

      - name: Run real knowledge materialization
        run: |
          python3 github-actions/run_real_knowledge_materialization.py < knowledge_materialization_input.json > knowledge_materialization_result.json

      - name: Render knowledge materialization summary
        if: always()
        run: |
          python3 github-actions/render_real_knowledge_materialization_summary.py knowledge_materialization_result.json

      - name: Upload knowledge materialization artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: knowledge-materialization-${{ github.run_id }}
          path: |
            knowledge_materialization_result.json
```

- [ ] **Step 4: Run the tests to verify they pass**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_run_real_knowledge_materialization.py \
  github-actions/tests/test_render_real_knowledge_materialization_summary.py \
  github-actions/tests/test_knowledge_materialization_workflow.py -v
```

Expected: PASS with orchestration, summary, and workflow contract assertions green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/run_real_knowledge_materialization.py \
        github-actions/tests/test_run_real_knowledge_materialization.py \
        github-actions/render_real_knowledge_materialization_summary.py \
        github-actions/tests/test_render_real_knowledge_materialization_summary.py \
        .github/workflows/knowledge-materialization.yml \
        github-actions/tests/test_knowledge_materialization_workflow.py
git commit -m "feat: add real knowledge materialization workflow"
```

## Task 5: Add Operator Docs and Validate the Full Baseline

**Files:**
- Create: `docs/feishu-collab/runbooks/knowledge-materialization.md`
- Modify: `docs/feishu-collab/RUNBOOK_INDEX.md`
- Create: `github-actions/tests/test_real_knowledge_materialization_docs.py`
- Modify: `github-actions/run_real_knowledge_materialization.py`
- Modify: `github-actions/render_real_knowledge_materialization_summary.py`
- Modify: `.github/workflows/knowledge-materialization.yml`

- [ ] **Step 1: Write the failing docs and end-to-end validation tests**

Create `github-actions/tests/test_real_knowledge_materialization_docs.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class RealKnowledgeMaterializationDocsTests(unittest.TestCase):
    def test_runbook_mentions_workflow_inputs_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "knowledge-materialization.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/knowledge-materialization.yml", text)
        self.assertIn("approval_status_result_json", text)
        self.assertIn("approval_writeback_result_json", text)
        self.assertIn("knowledge_materialization_result.json", text)

    def test_runbook_index_registers_knowledge_materialization(self):
        text = (REPO_ROOT / "docs" / "feishu-collab" / "RUNBOOK_INDEX.md").read_text(encoding="utf-8")
        self.assertIn("Knowledge Materialization", text)
        self.assertIn("knowledge-materialization.md", text)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```bash
python3 -m unittest github-actions/tests/test_real_knowledge_materialization_docs.py -v
```

Expected: FAIL because the workflow runbook and index entry do not exist yet.

- [ ] **Step 3: Write the runbook and register the workflow**

Create `docs/feishu-collab/runbooks/knowledge-materialization.md`:

```md
# Knowledge Materialization

## Purpose

Consume approval and polling artifacts, write one governed runbook and one governed handoff document, and update the knowledge indexes.

## Workflow Entry

- Workflow: `.github/workflows/knowledge-materialization.yml`
- Trigger: `workflow_dispatch`
- Required inputs:
  - `approval_status_result_json`
  - `approval_writeback_result_json`
  - `materialization_context_json`

## Artifacts

- `knowledge_materialization_result.json`

## Success Rule

The workflow succeeds only when both the runbook and handoff are written and both indexes are updated.

## Failure Guide

- If runbook write fails, inspect the materialization result before rerunning.
- If handoff write fails, keep the runbook and rerun after fixing the handoff path.
- If index update fails, keep the documents and repair the indexes before the next run.
```

Update the entries table in `docs/feishu-collab/RUNBOOK_INDEX.md` to include:

```md
| Knowledge Materialization | `docs/feishu-collab/runbooks/knowledge-materialization.md` | Materialize approval and polling artifacts into governed runbook and handoff documents |
```

- [ ] **Step 4: Run the tests and the full targeted validation suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_real_knowledge_payload.py \
  github-actions/tests/test_materialize_real_knowledge_assets.py \
  github-actions/tests/test_update_knowledge_indexes.py \
  github-actions/tests/test_run_real_knowledge_materialization.py \
  github-actions/tests/test_render_real_knowledge_materialization_summary.py \
  github-actions/tests/test_knowledge_materialization_workflow.py \
  github-actions/tests/test_real_knowledge_materialization_docs.py \
  github-actions/tests/test_knowledge_ops_end_to_end_contract.py -v
```

Expected: all fourth-phase materialization and legacy knowledge-ops contract tests PASS.

Then run the local workflow-style dry-run:

```bash
python3 -c 'import json, pathlib; payload={"approval_status_result":{"approval_instance_code":"ins_local","approval_status":"pending","automation_status":"paused","decision_summary":"pending:TASK-LOCAL"},"approval_writeback_result":{"task_id":"TASK-LOCAL","goal_id":"GOAL-LOCAL","task_writeback_status":"success","goal_writeback_status":"success"},"materialization_context":{"workflow_name":"approval-polling-writeback","operator_summary":"Local knowledge materialization"}}; pathlib.Path("knowledge_materialization_input.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")'
python3 github-actions/run_real_knowledge_materialization.py < knowledge_materialization_input.json > knowledge_materialization_result.json
GITHUB_STEP_SUMMARY=/tmp/knowledge-materialization-summary.md python3 github-actions/render_real_knowledge_materialization_summary.py knowledge_materialization_result.json
python3 -c 'import json, pathlib; result=json.loads(pathlib.Path("knowledge_materialization_result.json").read_text(encoding="utf-8")); summary=pathlib.Path("/tmp/knowledge-materialization-summary.md").read_text(encoding="utf-8"); assert result["source_refs"]["task_id"]=="TASK-LOCAL"; assert result["runbook"]["target_path"].endswith("approval-task-local-runbook.md"); assert result["handoff"]["target_path"].endswith("approval-task-local-handoff.md"); assert "Real Knowledge Materialization" in summary; assert "TASK-LOCAL" in summary; print("real knowledge materialization dry-run ok")'
```

Expected:

- `knowledge_materialization_result.json` exists
- `/tmp/knowledge-materialization-summary.md` exists
- the terminal prints `real knowledge materialization dry-run ok`

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/build_real_knowledge_payload.py \
        github-actions/tests/test_build_real_knowledge_payload.py \
        github-actions/feishu_collab/knowledge_ops/materialize_real_knowledge_assets.py \
        github-actions/tests/test_materialize_real_knowledge_assets.py \
        github-actions/feishu_collab/knowledge_ops/update_knowledge_indexes.py \
        github-actions/tests/test_update_knowledge_indexes.py \
        github-actions/run_real_knowledge_materialization.py \
        github-actions/tests/test_run_real_knowledge_materialization.py \
        github-actions/render_real_knowledge_materialization_summary.py \
        github-actions/tests/test_render_real_knowledge_materialization_summary.py \
        .github/workflows/knowledge-materialization.yml \
        github-actions/tests/test_knowledge_materialization_workflow.py \
        docs/feishu-collab/runbooks/knowledge-materialization.md \
        docs/feishu-collab/RUNBOOK_INDEX.md \
        github-actions/tests/test_real_knowledge_materialization_docs.py
git commit -m "test: validate real knowledge materialization baseline"
```

## Self-Review

- Spec coverage:
  - independent knowledge workflow: Task 4
  - approval/polling-only input boundary: Task 1 and Task 4
  - stable runbook/handoff filenames and real file writes: Task 1 and Task 2
  - index update order and deduped reruns: Task 3
  - summary, artifact, and workflow exit semantics: Task 4
  - operator discoverability and local dry-run validation: Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred markers
  - Every code-bearing step includes concrete code or YAML
  - Every verification step includes exact commands and expected outcomes
- Type consistency:
  - workflow file stays `.github/workflows/knowledge-materialization.yml`
  - result artifact stays `knowledge_materialization_result.json`
  - runner stays `github-actions/run_real_knowledge_materialization.py`
  - summary helper stays `github-actions/render_real_knowledge_materialization_summary.py`
  - workflow inputs stay `approval_status_result_json`, `approval_writeback_result_json`, `materialization_context_json`
