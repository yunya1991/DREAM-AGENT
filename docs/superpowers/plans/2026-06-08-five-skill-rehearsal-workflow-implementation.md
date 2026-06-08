# Five Skill Rehearsal Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated GitHub Actions workflow that runs the existing five-skill rehearsal runner, uploads the JSON report as an artifact, renders a Job Summary, and fails the workflow whenever the normalized system status is not `pass`.

**Architecture:** Keep the workflow thin and treat the existing Python integration runner as the single orchestration source of truth. Add one small workflow-only helper that reads the rehearsal JSON, renders GitHub Job Summary markdown, and converts `system_status` into the workflow exit code; then wire that helper into a new standalone `.github/workflows/five-skill-rehearsal.yml`.

**Tech Stack:** GitHub Actions YAML, Python 3, `unittest`, `json`, existing five-skill rehearsal runner, Markdown runbook docs

---

## Scope Check

This plan covers one coherent sub-project:

- Add a workflow-only summary and exit-code helper
- Add a dedicated `workflow_dispatch` rehearsal workflow
- Keep the workflow parallel to `collab-acceptance-agent` instead of modifying it
- Update the rehearsal runbook so operators know both the local and workflow entrypoints
- Validate the full workflow contract and local dry-run behavior

It does **not** include:

- PR comment triggers
- cron triggers
- Lark writeback
- acceptance-workflow integration
- multi-scenario selection

## File Map

- Create: `github-actions/render_rehearsal_workflow_summary.py`
  - Reads the rehearsal JSON report, renders Job Summary markdown, and exits with `0/1` from `system_status`.
- Create: `github-actions/tests/test_render_rehearsal_workflow_summary.py`
  - Locks summary content and `pass / warn / fail / blocked` exit-code mapping.
- Create: `.github/workflows/five-skill-rehearsal.yml`
  - Dedicated `workflow_dispatch` entrypoint for the five-skill rehearsal.
- Create: `github-actions/tests/test_five_skill_rehearsal_workflow.py`
  - Locks workflow presence, trigger mode, runner command, summary helper usage, and artifact upload behavior.
- Modify: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
  - Add the workflow entrypoint, artifact name, Job Summary reading guide, and failure semantics.
- Create: `github-actions/tests/test_five_skill_rehearsal_workflow_docs.py`
  - Locks that the runbook mentions the new workflow file, `workflow_dispatch`, artifact file, and Job Summary.

## Execution Guardrails

- Do not move five-skill orchestration logic into YAML; keep `github-actions/run_five_skill_integration_rehearsal.py` as the only chain runner.
- Keep the new workflow independent from `collab-acceptance-agent.yml`; do not add jobs or modes to the acceptance workflow in this plan.
- Treat the summary helper as a workflow adapter only; it may format output and return exit codes, but it must not recompute step results.
- Use `if: always()` on artifact upload so evidence survives `warn / fail / blocked`.
- Keep the workflow trigger to `workflow_dispatch` only in v1.
- Preserve the existing report file name and scenario defaults unless a failing test proves a change is required.

## Task 1: Add the Workflow Summary Helper

**Files:**
- Create: `github-actions/render_rehearsal_workflow_summary.py`
- Create: `github-actions/tests/test_render_rehearsal_workflow_summary.py`

- [ ] **Step 1: Write the failing helper tests**

Create `github-actions/tests/test_render_rehearsal_workflow_summary.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "render_rehearsal_workflow_summary.py"
SPEC = importlib.util.spec_from_file_location(
    "render_rehearsal_workflow_summary",
    MODULE_PATH,
)


class RenderRehearsalWorkflowSummaryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_report(self, system_status="pass", breakpoints=None):
        return {
            "scenario_manifest": {"scenario_id": "core-objective-baseline"},
            "system_status": system_status,
            "step_results": [
                {
                    "skill_name": "okr-driven",
                    "normalized": {"system_status": "pass"},
                    "verification": {"status": "confirmed"},
                },
                {
                    "skill_name": "approval",
                    "normalized": {"system_status": system_status},
                    "verification": {"status": "confirmed" if system_status == "pass" else "soft_block"},
                },
            ],
            "breakpoints": breakpoints or [],
            "verification_summary": {
                "step_count": 2,
                "breakpoint_count": len(breakpoints or []),
                "highest_status": system_status,
            },
        }

    def test_build_summary_markdown_renders_core_fields_and_step_table(self):
        module = self.load_module()
        summary = module.build_summary_markdown(
            self.sample_report(
                breakpoints=[
                    {
                        "skill_name": "approval",
                        "breakpoint_type": "contract_gap",
                        "recovery_hint": "align approval projection",
                    }
                ]
            )
        )
        self.assertIn("core-objective-baseline", summary)
        self.assertIn("System Status: `pass`", summary)
        self.assertIn("| Skill | Raw Verification | System |", summary)
        self.assertIn("| approval | confirmed | pass |", summary)
        self.assertIn("contract_gap", summary)
        self.assertIn("align approval projection", summary)

    def test_workflow_exit_code_returns_zero_only_for_pass(self):
        module = self.load_module()
        self.assertEqual(module.workflow_exit_code(self.sample_report("pass")), 0)
        self.assertEqual(module.workflow_exit_code(self.sample_report("warn")), 1)
        self.assertEqual(module.workflow_exit_code(self.sample_report("fail")), 1)
        self.assertEqual(module.workflow_exit_code(self.sample_report("blocked")), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_render_rehearsal_workflow_summary.py -v
```

Expected: FAIL because `render_rehearsal_workflow_summary.py` does not exist yet.

- [ ] **Step 3: Write the minimal helper**

Create `github-actions/render_rehearsal_workflow_summary.py`:

```python
import json
import os
from pathlib import Path
import sys


def build_summary_markdown(report):
    scenario_id = report["scenario_manifest"]["scenario_id"]
    system_status = report["system_status"]
    verification = report["verification_summary"]

    lines = [
        "# Five Skill Rehearsal",
        "",
        f"- Scenario: `{scenario_id}`",
        f"- System Status: `{system_status}`",
        f"- Step Count: `{verification['step_count']}`",
        f"- Breakpoint Count: `{verification['breakpoint_count']}`",
        "",
        "| Skill | Raw Verification | System |",
        "| --- | --- | --- |",
    ]

    for step in report.get("step_results", []):
        lines.append(
            f"| {step['skill_name']} | "
            f"{step['verification'].get('status', '')} | "
            f"{step['normalized'].get('system_status', '')} |"
        )

    breakpoints = report.get("breakpoints", [])
    if breakpoints:
        lines.extend(["", "## Breakpoints", ""])
        for item in breakpoints:
            lines.append(
                f"- `{item['skill_name']}` / `{item['breakpoint_type']}`: {item['recovery_hint']}"
            )

    return "\n".join(lines) + "\n"


def workflow_exit_code(report):
    return 0 if report.get("system_status") == "pass" else 1


def main(argv=None):
    argv = argv or sys.argv[1:]
    report_path = Path(argv[0])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = build_summary_markdown(report)
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as fh:
            fh.write(summary)
    else:
        sys.stdout.write(summary)
    raise SystemExit(workflow_exit_code(report))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_render_rehearsal_workflow_summary.py -v
```

Expected: PASS with `Ran 2 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/render_rehearsal_workflow_summary.py \
        github-actions/tests/test_render_rehearsal_workflow_summary.py
git commit -m "feat: add rehearsal workflow summary helper"
```

## Task 2: Add the Dedicated Workflow

**Files:**
- Create: `.github/workflows/five-skill-rehearsal.yml`
- Create: `github-actions/tests/test_five_skill_rehearsal_workflow.py`

- [ ] **Step 1: Write the failing workflow contract tests**

Create `github-actions/tests/test_five_skill_rehearsal_workflow.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FiveSkillRehearsalWorkflowTests(unittest.TestCase):
    def read_workflow(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "five-skill-rehearsal.yml"
        return workflow.read_text(encoding="utf-8")

    def test_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "five-skill-rehearsal.yml"
        self.assertTrue(workflow.exists(), str(workflow))

    def test_workflow_uses_workflow_dispatch_only(self):
        text = self.read_workflow()
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("issue_comment:", text)
        self.assertNotIn("schedule:", text)

    def test_workflow_runs_rehearsal_runner_and_summary_helper(self):
        text = self.read_workflow()
        self.assertIn("python3 github-actions/run_five_skill_integration_rehearsal.py > five-skill-rehearsal-report.json", text)
        self.assertIn("python3 github-actions/render_rehearsal_workflow_summary.py five-skill-rehearsal-report.json", text)

    def test_workflow_uploads_artifact_even_on_failure(self):
        text = self.read_workflow()
        self.assertIn("if: always()", text)
        self.assertIn("uses: actions/upload-artifact@v4", text)
        self.assertIn("five-skill-rehearsal-${{ github.run_id }}", text)
        self.assertIn("five-skill-rehearsal-report.json", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_five_skill_rehearsal_workflow.py -v
```

Expected: FAIL because `.github/workflows/five-skill-rehearsal.yml` does not exist yet.

- [ ] **Step 3: Write the minimal workflow**

Create `.github/workflows/five-skill-rehearsal.yml`:

```yaml
name: five-skill-rehearsal

on:
  workflow_dispatch:

env:
  FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true

permissions:
  contents: read

concurrency:
  group: five-skill-rehearsal-${{ github.ref }}
  cancel-in-progress: true

jobs:
  rehearsal:
    runs-on: [self-hosted, macOS, workbuddy]
    steps:
      - name: Checkout workflow ref
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run five skill rehearsal
        run: |
          python3 github-actions/run_five_skill_integration_rehearsal.py > five-skill-rehearsal-report.json

      - name: Render rehearsal summary
        run: |
          python3 github-actions/render_rehearsal_workflow_summary.py five-skill-rehearsal-report.json

      - name: Upload rehearsal artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: five-skill-rehearsal-${{ github.run_id }}
          path: five-skill-rehearsal-report.json
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_five_skill_rehearsal_workflow.py -v
```

Expected: PASS with `Ran 4 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/five-skill-rehearsal.yml \
        github-actions/tests/test_five_skill_rehearsal_workflow.py
git commit -m "feat: add five skill rehearsal workflow"
```

## Task 3: Update the Runbook for Workflow Operators

**Files:**
- Modify: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
- Create: `github-actions/tests/test_five_skill_rehearsal_workflow_docs.py`

- [ ] **Step 1: Write the failing runbook contract test**

Create `github-actions/tests/test_five_skill_rehearsal_workflow_docs.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FiveSkillRehearsalWorkflowDocsTests(unittest.TestCase):
    def test_runbook_mentions_workflow_entry_and_artifacts(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "five-skill-integration-rehearsal.md"
        ).read_text(encoding="utf-8")
        self.assertIn(".github/workflows/five-skill-rehearsal.yml", text)
        self.assertIn("workflow_dispatch", text)
        self.assertIn("five-skill-rehearsal-report.json", text)
        self.assertIn("Job Summary", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_five_skill_rehearsal_workflow_docs.py -v
```

Expected: FAIL because the runbook does not mention the workflow entrypoint yet.

- [ ] **Step 3: Update the runbook**

Modify `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md` so it contains:

```md
# Five Skill Integration Rehearsal

## Purpose

Run the fixture-driven system rehearsal for:

1. `OKR-driven`
2. `Bitable`
3. `GitHub Sync`
4. `Approval`
5. `Knowledge-Ops`

This runbook verifies that the core objective baseline can move through the full collaboration chain with one normalized system result.

## Local Command

    python3 github-actions/run_five_skill_integration_rehearsal.py

## Workflow Entry

- Workflow: `.github/workflows/five-skill-rehearsal.yml`
- Trigger: `workflow_dispatch`
- Artifact report: `five-skill-rehearsal-report.json`
- Primary GitHub surface: `Job Summary`

## Expected Output

- `scenario_manifest`
- `step_results`
- `breakpoints`
- `system_status`
- `verification_summary`
- `handoff`
- `knowledge_update`

## Status Reading Guide

- `pass`: the step completed without a system breakpoint
- `warn`: the workflow renders evidence but exits failed for operator review
- `fail`: the workflow renders evidence and exits failed because a contract or execution issue remains
- `blocked`: the workflow renders evidence and exits failed because the chain cannot continue safely

## Recovery Guide

- If `policy_gap`, fix the governance input and rerun
- If `data_gap`, repair the fixture or missing reference and rerun
- If `contract_gap`, align the step interface and rerun
- If `execution_gap`, inspect the skill output and rerun
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_five_skill_rehearsal_workflow_docs.py -v
```

Expected: PASS with `Ran 1 test ... OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md \
        github-actions/tests/test_five_skill_rehearsal_workflow_docs.py
git commit -m "docs: update rehearsal workflow runbook"
```

## Task 4: Validate the Workflow Baseline

**Files:**
- Modify: `github-actions/render_rehearsal_workflow_summary.py`
- Modify: `.github/workflows/five-skill-rehearsal.yml`
- Modify: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`

- [ ] **Step 1: Run the full targeted workflow-related test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_render_rehearsal_workflow_summary.py \
  github-actions/tests/test_five_skill_rehearsal_workflow.py \
  github-actions/tests/test_five_skill_rehearsal_workflow_docs.py \
  github-actions/tests/test_status_adapter.py \
  github-actions/tests/test_integration_scenario_loader.py \
  github-actions/tests/test_chain_orchestrator.py \
  github-actions/tests/test_rehearsal_reporter.py \
  github-actions/tests/test_run_five_skill_integration_rehearsal.py \
  github-actions/tests/test_collab_workflows_present.py -v
```

Expected: all workflow and rehearsal tests PASS.

- [ ] **Step 2: Perform the local workflow-style dry-run**

Run:

```bash
python3 github-actions/run_five_skill_integration_rehearsal.py > five-skill-rehearsal-report.json
GITHUB_STEP_SUMMARY=/tmp/five-skill-rehearsal-summary.md python3 github-actions/render_rehearsal_workflow_summary.py five-skill-rehearsal-report.json
python3 -c 'import json, pathlib
report = json.loads(pathlib.Path("five-skill-rehearsal-report.json").read_text(encoding="utf-8"))
summary = pathlib.Path("/tmp/five-skill-rehearsal-summary.md").read_text(encoding="utf-8")
assert report["scenario_manifest"]["scenario_id"] == "core-objective-baseline"
assert report["system_status"] in {"pass", "warn", "fail", "blocked"}
assert "System Status:" in summary
assert "core-objective-baseline" in summary
print("workflow rehearsal dry-run ok")'
```

Expected:

- helper exits `0` when the report is `pass`
- `five-skill-rehearsal-report.json` exists
- `/tmp/five-skill-rehearsal-summary.md` exists and contains the system summary
- terminal prints `workflow rehearsal dry-run ok`

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/five-skill-rehearsal.yml \
        github-actions/render_rehearsal_workflow_summary.py \
        github-actions/tests/test_render_rehearsal_workflow_summary.py \
        github-actions/tests/test_five_skill_rehearsal_workflow.py \
        github-actions/tests/test_five_skill_rehearsal_workflow_docs.py \
        docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md
git commit -m "test: validate rehearsal workflow baseline"
```

## Self-Review

- Spec coverage:
  - standalone `workflow_dispatch` workflow: Task 2
  - workflow helper for summary and exit semantics: Task 1
  - artifact and Job Summary expectations: Task 2 and Task 4
  - operator runbook updates: Task 3
  - workflow success/failure mapping from `system_status`: Task 1 and Task 4
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred markers
  - Every code-bearing step includes exact code or YAML
  - Every verification step includes exact commands and expected outcomes
- Type consistency:
  - workflow report file name stays `five-skill-rehearsal-report.json`
  - workflow statuses stay `pass`, `warn`, `fail`, `blocked`
  - workflow file name stays `.github/workflows/five-skill-rehearsal.yml`
