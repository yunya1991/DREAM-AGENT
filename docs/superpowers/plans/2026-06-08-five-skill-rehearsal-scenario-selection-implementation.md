# Five Skill Rehearsal Scenario Selection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add registry-driven scenario selection to the five-skill rehearsal workflow so operators can choose a pre-registered `scenario_id` instead of relying on a single hardcoded manifest path.

**Architecture:** Introduce one small scenario registry plus one registry resolver module, then extend the existing runner to resolve `scenario_id -> manifest path` before calling the current loader, orchestrator, and reporter. Keep the workflow thin by only passing `scenario_id` through `workflow_dispatch`, and keep the next-stage “real approval trigger” explicitly out of scope for this implementation.

**Tech Stack:** Python 3, `unittest`, JSON fixtures, GitHub Actions YAML, existing five-skill rehearsal runner and workflow

---

## Scope Check

This plan covers one coherent sub-project:

- Add a centralized scenario registry
- Add a small registry resolver for `scenario_id`
- Extend the runner to accept `scenario_id`
- Extend the workflow to pass `scenario_id`
- Update the runbook and validate the full scenario-selection baseline

It does **not** include:

- Arbitrary `scenario_path` input
- Directory scanning discovery
- Running multiple scenarios in one workflow
- Real approval trigger execution
- Acceptance workflow integration

## File Map

- Create: `github-actions/tests/fixtures/integration/scenario_registry.json`
  - Central registry that maps pre-registered `scenario_id` values to manifest paths and operator-facing metadata.
- Create: `github-actions/feishu_collab/integration/scenario_registry.py`
  - Loads the registry file, resolves a `scenario_id`, and raises a clear error for unknown values.
- Create: `github-actions/tests/test_integration_scenario_registry.py`
  - Locks registry parsing, default baseline presence, and unknown-scenario failure behavior.
- Modify: `github-actions/run_five_skill_integration_rehearsal.py`
  - Accepts `scenario_id`, resolves it via the registry, and preserves `core-objective-baseline` as the default.
- Create: `github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py`
  - Locks runner CLI and function-level behavior for `scenario_id`.
- Modify: `.github/workflows/five-skill-rehearsal.yml`
  - Adds `workflow_dispatch.inputs.scenario_id` and passes that input to the runner.
- Modify: `github-actions/tests/test_five_skill_rehearsal_workflow.py`
  - Extends the workflow contract to assert `scenario_id` input and forwarding behavior.
- Modify: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
  - Replaces the “single fixed scenario” operator guidance with registry-driven `scenario_id` guidance.
- Create: `github-actions/tests/test_five_skill_rehearsal_scenario_docs.py`
  - Locks that the runbook mentions `scenario_id`, the registry-driven selection model, and the default baseline.

## Execution Guardrails

- Keep `scenario_registry.json` as the only operator-facing scenario source of truth.
- Do not let the workflow parse registry files or resolve manifest paths itself; that remains runner-side logic.
- Preserve the existing `core-objective-baseline` manifest and behavior while removing its hardcoded path from the runner.
- Unknown `scenario_id` values must fail clearly and early; do not silently fall back to an arbitrary path.
- Do not mix this plan with “real approval trigger” changes; that remains the next stage after this one.
- Continue to treat the workflow as thin orchestration: checkout, run the runner, render summary, upload artifact.

## Task 1: Add the Scenario Registry and Resolver

**Files:**
- Create: `github-actions/tests/fixtures/integration/scenario_registry.json`
- Create: `github-actions/feishu_collab/integration/scenario_registry.py`
- Create: `github-actions/tests/test_integration_scenario_registry.py`

- [ ] **Step 1: Write the failing registry tests**

Create `github-actions/tests/test_integration_scenario_registry.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "scenario_registry.py"
SPEC = importlib.util.spec_from_file_location("scenario_registry", MODULE_PATH)
REGISTRY_PATH = ROOT / "github-actions" / "tests" / "fixtures" / "integration" / "scenario_registry.json"


class IntegrationScenarioRegistryTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_registry_contains_core_objective_baseline(self):
        module = self.load_module()
        registry = module.load_scenario_registry(ROOT, REGISTRY_PATH)
        self.assertIn("core-objective-baseline", registry)
        self.assertEqual(
            registry["core-objective-baseline"]["manifest_path"],
            "github-actions/tests/fixtures/integration/core_objective_baseline.json",
        )

    def test_resolve_registered_scenario_returns_manifest_path(self):
        module = self.load_module()
        result = module.resolve_scenario_manifest(
            repo_root=ROOT,
            scenario_id="core-objective-baseline",
            registry_path=REGISTRY_PATH,
        )
        self.assertTrue(str(result).endswith("core_objective_baseline.json"))

    def test_unknown_scenario_id_raises_clear_error(self):
        module = self.load_module()
        with self.assertRaisesRegex(ValueError, "unknown_scenario_id:missing-scenario"):
            module.resolve_scenario_manifest(
                repo_root=ROOT,
                scenario_id="missing-scenario",
                registry_path=REGISTRY_PATH,
            )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add the registry fixture**

Create `github-actions/tests/fixtures/integration/scenario_registry.json`:

```json
{
  "scenarios": [
    {
      "scenario_id": "core-objective-baseline",
      "manifest_path": "github-actions/tests/fixtures/integration/core_objective_baseline.json",
      "description": "Primary five-skill baseline for the core objective chain",
      "status": "active"
    }
  ]
}
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_integration_scenario_registry.py -v
```

Expected: FAIL because `scenario_registry.py` does not exist yet.

- [ ] **Step 4: Write the minimal registry resolver**

Create `github-actions/feishu_collab/integration/scenario_registry.py`:

```python
import json
from pathlib import Path


def load_scenario_registry(repo_root, registry_path):
    repo_root = Path(repo_root)
    registry_path = Path(registry_path)
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    return {
        item["scenario_id"]: {
            "manifest_path": item["manifest_path"],
            "description": item.get("description", ""),
            "status": item.get("status", ""),
            "resolved_manifest_path": repo_root / item["manifest_path"],
        }
        for item in data.get("scenarios", [])
    }


def resolve_scenario_manifest(repo_root, scenario_id, registry_path):
    registry = load_scenario_registry(repo_root, registry_path)
    if scenario_id not in registry:
        raise ValueError(f"unknown_scenario_id:{scenario_id}")
    return registry[scenario_id]["resolved_manifest_path"]
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_integration_scenario_registry.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 6: Commit**

```bash
git add github-actions/tests/fixtures/integration/scenario_registry.json \
        github-actions/feishu_collab/integration/scenario_registry.py \
        github-actions/tests/test_integration_scenario_registry.py
git commit -m "feat: add rehearsal scenario registry"
```

## Task 2: Extend the Runner for `scenario_id`

**Files:**
- Modify: `github-actions/run_five_skill_integration_rehearsal.py`
- Create: `github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py`

- [ ] **Step 1: Write the failing runner scenario tests**

Create `github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_five_skill_integration_rehearsal.py"
SPEC = importlib.util.spec_from_file_location(
    "run_five_skill_integration_rehearsal",
    MODULE_PATH,
)


class RunFiveSkillIntegrationRehearsalScenarioTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_run_rehearsal_defaults_to_core_objective_baseline(self):
        module = self.load_module()
        report = module.run_rehearsal()
        self.assertEqual(report["scenario_manifest"]["scenario_id"], "core-objective-baseline")

    def test_run_rehearsal_accepts_registered_scenario_id(self):
        module = self.load_module()
        report = module.run_rehearsal(scenario_id="core-objective-baseline")
        self.assertEqual(report["scenario_manifest"]["scenario_id"], "core-objective-baseline")

    def test_run_rehearsal_rejects_unknown_scenario_id(self):
        module = self.load_module()
        with self.assertRaisesRegex(ValueError, "unknown_scenario_id:missing-scenario"):
            module.run_rehearsal(scenario_id="missing-scenario")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py -v
```

Expected: FAIL because the runner does not yet accept `scenario_id`.

- [ ] **Step 3: Update the runner**

Modify `github-actions/run_five_skill_integration_rehearsal.py` so it becomes:

```python
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from feishu_collab.integration.chain_orchestrator import run_rehearsal_chain
from feishu_collab.integration.rehearsal_reporter import build_rehearsal_report
from feishu_collab.integration.scenario_loader import load_rehearsal_scenario
from feishu_collab.integration.scenario_registry import resolve_scenario_manifest


DEFAULT_SCENARIO_ID = "core-objective-baseline"
REGISTRY_PATH = ROOT / "tests" / "fixtures" / "integration" / "scenario_registry.json"


def run_rehearsal(scenario_id=DEFAULT_SCENARIO_ID):
    scenario_path = resolve_scenario_manifest(
        repo_root=ROOT.parent,
        scenario_id=scenario_id,
        registry_path=REGISTRY_PATH,
    )
    payload = load_rehearsal_scenario(ROOT.parent, scenario_path)
    result = run_rehearsal_chain(payload)
    return build_rehearsal_report(
        scenario_manifest=payload["scenario_manifest"],
        step_results=result["step_results"],
        breakpoints=result["breakpoints"],
    )


if __name__ == "__main__":
    selected = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SCENARIO_ID
    report = run_rehearsal(scenario_id=selected)
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_run_five_skill_integration_rehearsal.py \
  github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py -v
```

Expected: PASS with `Ran 4 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/run_five_skill_integration_rehearsal.py \
        github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py
git commit -m "feat: add rehearsal scenario selection to runner"
```

## Task 3: Extend the Workflow Input and Contract

**Files:**
- Modify: `.github/workflows/five-skill-rehearsal.yml`
- Modify: `github-actions/tests/test_five_skill_rehearsal_workflow.py`

- [ ] **Step 1: Write the failing workflow input contract**

Update `github-actions/tests/test_five_skill_rehearsal_workflow.py` by adding these tests:

```python
    def test_workflow_accepts_scenario_id_input(self):
        text = self.read_workflow()
        self.assertIn("scenario_id:", text)
        self.assertIn("default: core-objective-baseline", text)
        self.assertIn("description: Registered rehearsal scenario id", text)

    def test_workflow_passes_scenario_id_to_runner(self):
        text = self.read_workflow()
        self.assertIn("${{ inputs.scenario_id }}", text)
        self.assertIn(
            "python3 github-actions/run_five_skill_integration_rehearsal.py \"${{ inputs.scenario_id }}\" > five-skill-rehearsal-report.json",
            text,
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_five_skill_rehearsal_workflow.py -v
```

Expected: FAIL because the workflow does not yet declare or forward `scenario_id`.

- [ ] **Step 3: Update the workflow**

Modify `.github/workflows/five-skill-rehearsal.yml` so it becomes:

```yaml
name: five-skill-rehearsal

on:
  workflow_dispatch:
    inputs:
      scenario_id:
        description: Registered rehearsal scenario id
        required: true
        default: core-objective-baseline
        type: string

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
          python3 github-actions/run_five_skill_integration_rehearsal.py "${{ inputs.scenario_id }}" > five-skill-rehearsal-report.json

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

Expected: PASS with `Ran 6 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/five-skill-rehearsal.yml \
        github-actions/tests/test_five_skill_rehearsal_workflow.py
git commit -m "feat: add workflow scenario input"
```

## Task 4: Update the Runbook and Validate the Scenario Baseline

**Files:**
- Modify: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
- Create: `github-actions/tests/test_five_skill_rehearsal_scenario_docs.py`
- Modify: `github-actions/render_rehearsal_workflow_summary.py`
- Modify: `github-actions/run_five_skill_integration_rehearsal.py`

- [ ] **Step 1: Write the failing runbook scenario contract**

Create `github-actions/tests/test_five_skill_rehearsal_scenario_docs.py`:

```python
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


class FiveSkillRehearsalScenarioDocsTests(unittest.TestCase):
    def test_runbook_mentions_registry_driven_scenario_selection(self):
        text = (
            REPO_ROOT
            / "docs"
            / "feishu-collab"
            / "runbooks"
            / "five-skill-integration-rehearsal.md"
        ).read_text(encoding="utf-8")
        self.assertIn("scenario_id", text)
        self.assertIn("core-objective-baseline", text)
        self.assertIn("scenario registry", text)
        self.assertIn("workflow_dispatch", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_five_skill_rehearsal_scenario_docs.py -v
```

Expected: FAIL because the runbook does not yet mention registry-driven `scenario_id` selection.

- [ ] **Step 3: Update the runbook**

Modify `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md` so the workflow section contains:

```md
## Workflow Entry

- Workflow: `.github/workflows/five-skill-rehearsal.yml`
- Trigger: `workflow_dispatch`
- Scenario input: `scenario_id`
- Default scenario: `core-objective-baseline`
- Scenario source: `scenario registry`
- Artifact report: `five-skill-rehearsal-report.json`
- Primary GitHub surface: `Job Summary`
```

Also add this operator note near the workflow section:

```md
Use only pre-registered `scenario_id` values. The workflow and runner resolve the manifest through the central scenario registry and will fail fast for unknown scenario ids.
```

- [ ] **Step 4: Run the full scenario-selection validation suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_integration_scenario_registry.py \
  github-actions/tests/test_run_five_skill_integration_rehearsal.py \
  github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py \
  github-actions/tests/test_five_skill_rehearsal_workflow.py \
  github-actions/tests/test_five_skill_rehearsal_scenario_docs.py \
  github-actions/tests/test_render_rehearsal_workflow_summary.py \
  github-actions/tests/test_chain_orchestrator.py \
  github-actions/tests/test_rehearsal_reporter.py \
  github-actions/tests/test_integration_scenario_loader.py -v
```

Expected: all scenario-selection and dependent rehearsal tests PASS.

- [ ] **Step 5: Perform the local scenario dry-run**

Run:

```bash
python3 github-actions/run_five_skill_integration_rehearsal.py core-objective-baseline > five-skill-rehearsal-report.json
GITHUB_STEP_SUMMARY=/tmp/five-skill-rehearsal-summary.md python3 github-actions/render_rehearsal_workflow_summary.py five-skill-rehearsal-report.json
python3 -c 'import json, pathlib
report = json.loads(pathlib.Path("five-skill-rehearsal-report.json").read_text(encoding="utf-8"))
summary = pathlib.Path("/tmp/five-skill-rehearsal-summary.md").read_text(encoding="utf-8")
assert report["scenario_manifest"]["scenario_id"] == "core-objective-baseline"
assert report["system_status"] in {"pass", "warn", "fail", "blocked"}
assert "System Status:" in summary
assert "core-objective-baseline" in summary
print("scenario selection dry-run ok")'
rm -f five-skill-rehearsal-report.json
```

Expected:

- runner exits successfully for the registered baseline
- report uses `scenario_manifest.scenario_id = core-objective-baseline`
- summary contains the selected scenario id
- terminal prints `scenario selection dry-run ok`

- [ ] **Step 6: Commit**

```bash
git add github-actions/tests/fixtures/integration/scenario_registry.json \
        github-actions/feishu_collab/integration/scenario_registry.py \
        github-actions/tests/test_integration_scenario_registry.py \
        github-actions/run_five_skill_integration_rehearsal.py \
        github-actions/tests/test_run_five_skill_integration_rehearsal_scenarios.py \
        .github/workflows/five-skill-rehearsal.yml \
        github-actions/tests/test_five_skill_rehearsal_workflow.py \
        docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md \
        github-actions/tests/test_five_skill_rehearsal_scenario_docs.py
git commit -m "test: validate rehearsal scenario selection baseline"
```

## Self-Review

- Spec coverage:
  - centralized scenario registry: Task 1
  - registry-driven runner selection: Task 2
  - `workflow_dispatch.inputs.scenario_id`: Task 3
  - runbook and operator guidance: Task 4
  - next-stage “real approval trigger” explicitly excluded from implementation: Scope Check and Execution Guardrails
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred markers
  - Every code-bearing step includes exact code or JSON/YAML
  - Every verification step includes exact commands and expected outcomes
- Type consistency:
  - scenario input stays `scenario_id`
  - default registered scenario stays `core-objective-baseline`
  - registry file stays `github-actions/tests/fixtures/integration/scenario_registry.json`
  - workflow file stays `.github/workflows/five-skill-rehearsal.yml`
