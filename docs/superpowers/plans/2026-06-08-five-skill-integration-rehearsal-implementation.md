# Five Skill Integration Rehearsal Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fixture-driven five-skill rehearsal runner that chains `OKR -> Bitable -> GitHub Sync -> Approval -> Knowledge-Ops`, normalizes each skill's raw status into one system status vocabulary, and emits a single system-level result with breakpoints, handoff, and knowledge output.

**Architecture:** Add a small `integration/` package under `github-actions/feishu_collab/` and keep all existing skill implementations intact. The new layer loads one core scenario manifest, runs each existing preview/materialize/verify helper in order, adapts raw status into a shared system status model, and renders a final rehearsal report from those step results.

**Tech Stack:** Python 3, `unittest`, `json`, existing five-skill helpers under `github-actions/`, shared Feishu-collaboration contracts, Markdown runbook docs

---

## Scope Check

This plan covers one coherent sub-project:

- Add a shared status adapter that maps raw skill outcomes into `pass / warn / fail / blocked`
- Add a scenario loader for the `core-objective-baseline` rehearsal
- Add a chain orchestrator that reuses the existing five-skill helpers in order
- Add a reporter and one top-level runner entrypoint
- Add one system runbook and validate the full rehearsal baseline

It does **not** include:

- Real Feishu or GitHub writeback during rehearsal
- A GitHub Actions workflow for the new runner
- A general-purpose event bus or scheduler
- Rewriting the current skill internals to a new shared status model
- Expanding the scenario matrix beyond the single core baseline

## File Map

- Create: `github-actions/feishu_collab/integration/__init__.py`
  - Package marker for the system-level integration helpers.
- Create: `github-actions/feishu_collab/shared/status_adapter.py`
  - Shared mapping from raw skill statuses into system statuses, breakpoint types, and recovery hints.
- Create: `github-actions/tests/test_status_adapter.py`
  - Lock status mapping semantics and fallback behavior for unknown raw statuses.
- Create: `github-actions/tests/fixtures/integration/core_objective_baseline.json`
  - Scenario manifest that points at the approved OKR spec/plan plus the existing Bitable, GitHub Sync, Approval, and Knowledge-Ops fixtures.
- Create: `github-actions/feishu_collab/integration/scenario_loader.py`
  - Read the scenario manifest, resolve file paths under repo root, and load all source texts and JSON payloads into a rehearsal input object.
- Create: `github-actions/tests/test_integration_scenario_loader.py`
  - Lock the scenario manifest shape, skill sequence, and loaded input payloads.
- Create: `github-actions/feishu_collab/integration/chain_orchestrator.py`
  - Reuse existing five-skill preview/materialize/verify helpers, pass the minimum shared context between them, and collect step-level raw plus normalized results.
- Create: `github-actions/tests/test_chain_orchestrator.py`
  - Lock the five-step sequence and the stop-on-`blocked` behavior.
- Create: `github-actions/feishu_collab/integration/rehearsal_reporter.py`
  - Collapse step results into one system result, one handoff summary, and one final `KnowledgeUpdate`.
- Create: `github-actions/tests/test_rehearsal_reporter.py`
  - Lock status precedence and system report shape.
- Create: `github-actions/run_five_skill_integration_rehearsal.py`
  - Top-level CLI runner that loads the default scenario, runs the chain, and prints JSON.
- Create: `github-actions/tests/test_run_five_skill_integration_rehearsal.py`
  - End-to-end contract for the new runner entrypoint.
- Create: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
  - Operator-facing runbook for how to run the new rehearsal and how to read the output.
- Modify: `docs/feishu-collab/RUNBOOK_INDEX.md`
  - Register the new runbook in the central runbook index.

## Execution Guardrails

- Keep the existing skill files as the source of domain behavior; the new integration layer may call them but must not absorb their internal logic.
- Treat `hard_block` and `blocked` as `blocked`; once a step normalizes to `blocked`, stop the chain immediately and report the breakpoint.
- Allow the chain to continue through `warn` and `fail` so the system report can expose downstream effects, unless the step is `blocked`.
- Reuse the approved OKR spec and plan as the baseline source for the first step instead of inventing a second OKR fixture.
- Make the final report deterministic and fixture-driven; do not call network APIs, browser tools, or GitHub CLI from the new runner.
- Emit both raw step status and normalized system status for every step so later debugging can distinguish domain failure from integration failure.

## Task 1: Add the Shared Status Adapter

**Files:**
- Create: `github-actions/feishu_collab/shared/status_adapter.py`
- Create: `github-actions/tests/test_status_adapter.py`

- [ ] **Step 1: Write the failing adapter tests**

Create `github-actions/tests/test_status_adapter.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "shared" / "status_adapter.py"
SPEC = importlib.util.spec_from_file_location("status_adapter", MODULE_PATH)


class StatusAdapterTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_confirmed_maps_to_pass_without_breakpoint(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="bitable",
            raw_status="confirmed",
            risk_flags=[],
            verification={"status": "confirmed"},
        )
        self.assertEqual(result["system_status"], "pass")
        self.assertEqual(result["breakpoint_type"], "")
        self.assertEqual(result["recovery_hint"], "continue to next skill")

    def test_degraded_success_maps_to_warn_with_execution_gap_hint(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="github-sync",
            raw_status="degraded_success",
            risk_flags=[],
            verification={"status": "degraded_success"},
        )
        self.assertEqual(result["system_status"], "warn")
        self.assertEqual(result["breakpoint_type"], "execution_gap")
        self.assertIn("github-sync", result["recovery_hint"])

    def test_soft_block_maps_to_fail_and_uses_contract_gap_when_risk_flag_present(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="approval",
            raw_status="soft_block",
            risk_flags=["status_projection_gap"],
            verification={"status": "soft_block"},
        )
        self.assertEqual(result["system_status"], "fail")
        self.assertEqual(result["breakpoint_type"], "contract_gap")

    def test_hard_block_maps_to_blocked_and_policy_gap_for_missing_gate_inputs(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="approval",
            raw_status="hard_block",
            risk_flags=["missing_approval_code"],
            verification={"status": "hard_block"},
        )
        self.assertEqual(result["system_status"], "blocked")
        self.assertEqual(result["breakpoint_type"], "policy_gap")

    def test_unknown_status_falls_back_to_fail(self):
        module = self.load_module()
        result = module.normalize_skill_result(
            skill_name="okr-driven",
            raw_status="mystery",
            risk_flags=[],
            verification={"status": "mystery"},
        )
        self.assertEqual(result["system_status"], "fail")
        self.assertEqual(result["breakpoint_type"], "contract_gap")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_status_adapter.py -v
```

Expected: FAIL because `status_adapter.py` does not exist yet.

- [ ] **Step 3: Write the minimal adapter**

Create `github-actions/feishu_collab/shared/status_adapter.py`:

```python
STATUS_MAP = {
    "confirmed": "pass",
    "degraded_success": "warn",
    "soft_block": "fail",
    "hard_block": "blocked",
    "blocked": "blocked",
}

POLICY_FLAGS = {"missing_approval_code", "missing_applicant_open_id", "unknown_asset_type"}
CONTRACT_FLAGS = {"status_projection_gap", "event_coverage_gap", "missing_goal_link", "missing_task_link"}
DATA_FLAGS = {"empty_title", "missing_evidence_refs", "task_goal_unlinked"}


def _breakpoint_type(raw_status, risk_flags):
    flags = set(risk_flags or [])
    if flags & POLICY_FLAGS:
        return "policy_gap"
    if flags & DATA_FLAGS:
        return "data_gap"
    if flags & CONTRACT_FLAGS:
        return "contract_gap"
    if raw_status == "degraded_success":
        return "execution_gap"
    if raw_status in {"soft_block", "hard_block", "blocked"}:
        return "execution_gap"
    return ""


def _recovery_hint(skill_name, system_status, breakpoint_type):
    if system_status == "pass":
        return "continue to next skill"
    if breakpoint_type == "policy_gap":
        return f"fix governance inputs before rerunning {skill_name}"
    if breakpoint_type == "data_gap":
        return f"repair missing scenario data before rerunning {skill_name}"
    if breakpoint_type == "contract_gap":
        return f"align upstream or downstream contracts before rerunning {skill_name}"
    return f"review {skill_name} execution evidence and rerun the rehearsal"


def normalize_skill_result(skill_name, raw_status, risk_flags=None, verification=None):
    system_status = STATUS_MAP.get(raw_status, "fail")
    breakpoint_type = _breakpoint_type(raw_status, risk_flags)
    return {
        "skill_name": skill_name,
        "raw_status": raw_status,
        "system_status": system_status,
        "breakpoint_type": breakpoint_type,
        "risk_flags": list(risk_flags or []),
        "verification": verification or {},
        "recovery_hint": _recovery_hint(skill_name, system_status, breakpoint_type),
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_status_adapter.py -v
```

Expected: PASS with `Ran 5 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/shared/status_adapter.py \
        github-actions/tests/test_status_adapter.py
git commit -m "feat: add rehearsal status adapter"
```

## Task 2: Add the Core Scenario Loader

**Files:**
- Create: `github-actions/tests/fixtures/integration/core_objective_baseline.json`
- Create: `github-actions/feishu_collab/integration/__init__.py`
- Create: `github-actions/feishu_collab/integration/scenario_loader.py`
- Create: `github-actions/tests/test_integration_scenario_loader.py`

- [ ] **Step 1: Write the failing scenario loader tests**

Create `github-actions/tests/test_integration_scenario_loader.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "scenario_loader.py"
SPEC = importlib.util.spec_from_file_location("scenario_loader", MODULE_PATH)
SCENARIO_PATH = ROOT / "github-actions" / "tests" / "fixtures" / "integration" / "core_objective_baseline.json"


class IntegrationScenarioLoaderTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_loader_reads_manifest_and_all_skill_inputs(self):
        module = self.load_module()
        payload = module.load_rehearsal_scenario(ROOT, SCENARIO_PATH)
        self.assertEqual(payload["scenario_manifest"]["scenario_id"], "core-objective-baseline")
        self.assertEqual(
            payload["scenario_manifest"]["skill_sequence"],
            ["okr-driven", "bitable", "github-sync", "approval", "knowledge-ops"],
        )
        self.assertIn("spec_text", payload["inputs"]["okr"])
        self.assertIn("plan_text", payload["inputs"]["okr"])
        self.assertIn("base_context", payload["inputs"]["bitable"])
        self.assertIn("event_payload", payload["inputs"]["github_sync"])
        self.assertIn("risk_context", payload["inputs"]["approval"])
        self.assertIn("handoff_context", payload["inputs"]["knowledge_ops"])

    def test_loader_keeps_repo_relative_paths_in_manifest(self):
        module = self.load_module()
        payload = module.load_rehearsal_scenario(ROOT, SCENARIO_PATH)
        self.assertEqual(
            payload["scenario_manifest"]["sources"]["okr_spec_path"],
            "docs/superpowers/specs/2026-06-08-okr-driven-skill-design.md",
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add the scenario manifest fixture**

Create `github-actions/tests/fixtures/integration/core_objective_baseline.json`:

```json
{
  "scenario_id": "core-objective-baseline",
  "skill_sequence": [
    "okr-driven",
    "bitable",
    "github-sync",
    "approval",
    "knowledge-ops"
  ],
  "sources": {
    "okr_spec_path": "docs/superpowers/specs/2026-06-08-okr-driven-skill-design.md",
    "okr_plan_path": "docs/superpowers/plans/2026-06-08-okr-driven-skill-implementation.md",
    "bitable_base_context_path": "github-actions/tests/fixtures/bitable_skill/base_context.json",
    "github_sync_event_path": "github-actions/tests/fixtures/github_sync/pr_event.json",
    "github_sync_collab_context_path": "github-actions/tests/fixtures/github_sync/collab_context.json",
    "approval_risk_context_path": "github-actions/tests/fixtures/approval_skill/risk_context.json",
    "approval_context_path": "github-actions/tests/fixtures/approval_skill/approval_context.json",
    "knowledge_handoff_context_path": "github-actions/tests/fixtures/knowledge_ops/handoff_context.json"
  }
}
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_integration_scenario_loader.py -v
```

Expected: FAIL because `scenario_loader.py` and `integration/__init__.py` do not exist yet.

- [ ] **Step 4: Write the minimal scenario package and loader**

Create `github-actions/feishu_collab/integration/__init__.py`:

```python
"""Five-skill integration rehearsal helpers."""
```

Create `github-actions/feishu_collab/integration/scenario_loader.py`:

```python
import json
from pathlib import Path


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_rehearsal_scenario(repo_root, scenario_path):
    repo_root = Path(repo_root)
    scenario_path = Path(scenario_path)
    manifest = _read_json(scenario_path)
    sources = manifest["sources"]

    def resolve(relative_path):
        return repo_root / relative_path

    return {
        "scenario_manifest": {
            "scenario_id": manifest["scenario_id"],
            "skill_sequence": manifest["skill_sequence"],
            "sources": sources,
        },
        "inputs": {
            "okr": {
                "spec_text": resolve(sources["okr_spec_path"]).read_text(encoding="utf-8"),
                "plan_text": resolve(sources["okr_plan_path"]).read_text(encoding="utf-8"),
            },
            "bitable": {
                "base_context": _read_json(resolve(sources["bitable_base_context_path"])),
            },
            "github_sync": {
                "event_payload": _read_json(resolve(sources["github_sync_event_path"])),
                "collab_context": _read_json(resolve(sources["github_sync_collab_context_path"])),
            },
            "approval": {
                "risk_context": _read_json(resolve(sources["approval_risk_context_path"])),
                "approval_context": _read_json(resolve(sources["approval_context_path"])),
            },
            "knowledge_ops": {
                "handoff_context": _read_json(resolve(sources["knowledge_handoff_context_path"])),
            },
        },
    }
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_integration_scenario_loader.py -v
```

Expected: PASS with `Ran 2 tests ... OK`.

- [ ] **Step 6: Commit**

```bash
git add github-actions/tests/fixtures/integration/core_objective_baseline.json \
        github-actions/feishu_collab/integration/__init__.py \
        github-actions/feishu_collab/integration/scenario_loader.py \
        github-actions/tests/test_integration_scenario_loader.py
git commit -m "feat: add rehearsal scenario loader"
```

## Task 3: Add the Five-Skill Chain Orchestrator

**Files:**
- Create: `github-actions/feishu_collab/integration/chain_orchestrator.py`
- Create: `github-actions/tests/test_chain_orchestrator.py`

- [ ] **Step 1: Write the failing orchestrator tests**

Create `github-actions/tests/test_chain_orchestrator.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOADER_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "scenario_loader.py"
ORCHESTRATOR_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "chain_orchestrator.py"
SCENARIO_PATH = ROOT / "github-actions" / "tests" / "fixtures" / "integration" / "core_objective_baseline.json"


def load_module(module_path, name):
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ChainOrchestratorTests(unittest.TestCase):
    def load_payload(self):
        loader = load_module(LOADER_PATH, "scenario_loader")
        return loader.load_rehearsal_scenario(ROOT, SCENARIO_PATH)

    def test_orchestrator_runs_five_steps_for_core_baseline(self):
        module = load_module(ORCHESTRATOR_PATH, "chain_orchestrator")
        result = module.run_rehearsal_chain(self.load_payload())
        self.assertEqual(
            [item["skill_name"] for item in result["step_results"]],
            ["okr-driven", "bitable", "github-sync", "approval", "knowledge-ops"],
        )
        self.assertEqual(result["step_results"][0]["normalized"]["system_status"], "pass")
        self.assertEqual(result["step_results"][-1]["normalized"]["system_status"], "pass")

    def test_orchestrator_stops_when_approval_becomes_blocked(self):
        module = load_module(ORCHESTRATOR_PATH, "chain_orchestrator")
        payload = self.load_payload()
        payload["inputs"]["approval"]["approval_context"]["approval_code"] = ""
        result = module.run_rehearsal_chain(payload)
        self.assertEqual(result["step_results"][-1]["skill_name"], "approval")
        self.assertEqual(result["step_results"][-1]["normalized"]["system_status"], "blocked")
        self.assertGreaterEqual(len(result["breakpoints"]), 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_chain_orchestrator.py -v
```

Expected: FAIL because `chain_orchestrator.py` does not exist yet.

- [ ] **Step 3: Write the minimal orchestrator**

Create `github-actions/feishu_collab/integration/chain_orchestrator.py`:

```python
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from build_okr_driven_preview import build_preview as build_okr_preview
from materialize_okr_driven_execution import materialize_execution as materialize_okr_execution
from feishu_collab.bitable.build_bitable_preview import build_bitable_preview
from feishu_collab.bitable.materialize_bitable_execution import materialize_bitable_execution
from feishu_collab.bitable.verify_bitable_projection import verify_bitable_projection
from feishu_collab.github_sync.build_github_sync_preview import build_github_sync_preview
from feishu_collab.github_sync.materialize_github_sync_execution import materialize_github_sync_execution
from feishu_collab.github_sync.verify_github_sync_projection import verify_github_sync_projection
from feishu_collab.approval.build_approval_preview import build_approval_preview
from feishu_collab.approval.materialize_approval_execution import materialize_approval_execution
from feishu_collab.approval.verify_approval_projection import verify_approval_projection
from feishu_collab.knowledge_ops.intake import normalize_knowledge_intake
from feishu_collab.knowledge_ops.pathing import resolve_knowledge_target
from feishu_collab.knowledge_ops.validate_knowledge_asset import validate_knowledge_asset
from feishu_collab.knowledge_ops.check_knowledge_assets import check_knowledge_assets
from feishu_collab.knowledge_ops.materialize_knowledge_asset import materialize_knowledge_asset
from feishu_collab.knowledge_ops.verify_knowledge_asset import verify_knowledge_asset
from feishu_collab.shared.status_adapter import normalize_skill_result


def _append_step(step_results, breakpoints, skill_name, raw_status, risk_flags, raw_result, verification):
    normalized = normalize_skill_result(
        skill_name=skill_name,
        raw_status=raw_status,
        risk_flags=risk_flags,
        verification=verification,
    )
    step = {
        "skill_name": skill_name,
        "raw_result": raw_result,
        "verification": verification,
        "normalized": normalized,
    }
    step_results.append(step)
    if normalized["system_status"] in {"warn", "fail", "blocked"}:
        breakpoints.append(
            {
                "skill_name": skill_name,
                "system_status": normalized["system_status"],
                "breakpoint_type": normalized["breakpoint_type"],
                "recovery_hint": normalized["recovery_hint"],
            }
        )
    return normalized


def run_rehearsal_chain(payload):
    inputs = payload["inputs"]
    step_results = []
    breakpoints = []

    okr_preview = build_okr_preview(inputs["okr"]["spec_text"], inputs["okr"]["plan_text"])
    okr_execution = materialize_okr_execution(okr_preview)
    okr_verification = {"status": "confirmed", "task_count": len(okr_preview["task_candidates"])}
    normalized = _append_step(
        step_results,
        breakpoints,
        "okr-driven",
        "confirmed",
        okr_preview.get("risk_flags", []),
        {"preview": okr_preview, "execution": okr_execution},
        okr_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    bitable_preview = build_bitable_preview(okr_preview, inputs["bitable"]["base_context"])
    bitable_execution = materialize_bitable_execution(bitable_preview)
    bitable_verification = verify_bitable_projection(
        bitable_preview["task_record_candidates"],
        bitable_preview["progress_record_candidates"],
        bitable_preview["goal_projection_candidates"],
        bitable_preview["view_projection_candidates"],
    )
    normalized = _append_step(
        step_results,
        breakpoints,
        "bitable",
        bitable_execution["status"],
        bitable_preview.get("drift_flags", []),
        {"preview": bitable_preview, "execution": bitable_execution},
        bitable_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    collab_context = dict(inputs["github_sync"]["collab_context"])
    collab_context["goal_id"] = bitable_preview["goal_projection_candidates"][0]["goal_id"]
    collab_context["task_id"] = bitable_preview["task_record_candidates"][0]["task_id"]
    collab_context["task_name"] = bitable_preview["task_record_candidates"][0]["title"]
    github_preview = build_github_sync_preview(inputs["github_sync"]["event_payload"], collab_context)
    github_execution = materialize_github_sync_execution(github_preview)
    github_verification = verify_github_sync_projection(
        github_execution["collab_state"]["fields"],
        github_execution["verification_seed"]["coverage_hit"],
        github_execution["verification_seed"]["risk_flags"],
        github_execution["collab_state"]["fields"].get("最近评论锚点", ""),
        {"status": github_execution["collab_state"]["fields"].get("自动化状态", "")},
    )
    normalized = _append_step(
        step_results,
        breakpoints,
        "github-sync",
        github_execution["status"],
        github_preview.get("risk_flags", []),
        {"preview": github_preview, "execution": github_execution},
        github_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    risk_context = dict(inputs["approval"]["risk_context"])
    risk_context["task_id"] = collab_context["task_id"]
    risk_context["goal_id"] = collab_context["goal_id"]
    approval_context = dict(inputs["approval"]["approval_context"])
    approval_context["target_object_id"] = collab_context["task_id"]
    approval_context["instance_external_id"] = collab_context["task_id"]
    approval_preview = build_approval_preview(risk_context, approval_context)
    approval_execution = materialize_approval_execution(approval_preview)
    approval_verification = verify_approval_projection(
        approval_execution["status_projection"],
        approval_execution["timeout_policy"],
        {
            "instance_code": approval_execution["approval_request"].get("instance_external_id", ""),
            "decision_summary": approval_execution["status_projection"].get("decision_summary", ""),
        },
        approval_preview["risk_flags"],
    )
    normalized = _append_step(
        step_results,
        breakpoints,
        "approval",
        approval_execution["status"],
        approval_preview.get("risk_flags", []),
        {"preview": approval_preview, "execution": approval_execution},
        approval_verification,
    )
    if normalized["system_status"] == "blocked":
        return {"step_results": step_results, "breakpoints": breakpoints}

    handoff_context = dict(inputs["knowledge_ops"]["handoff_context"])
    handoff_context["source_skill"] = "feishu-collab-approval"
    handoff_context["handoff_summary"] = approval_execution["handoff"]["summary"]
    handoff_context["target_object_id"] = collab_context["task_id"]
    handoff_context["goal_id"] = collab_context["goal_id"]
    knowledge_intake = normalize_knowledge_intake(approval_execution["knowledge_update"], handoff_context)
    asset_target = {
        "target_path": resolve_knowledge_target(knowledge_intake["asset_type"], knowledge_intake["title"]),
        "template_type": "runbook",
        "index_target": "docs/feishu-collab/RUNBOOK_INDEX.md",
        "allow_overwrite": False,
    }
    validation_report = validate_knowledge_asset(knowledge_intake)
    check_report = check_knowledge_assets(
        intake=knowledge_intake,
        validation_report=validation_report,
        existing_state={"index_contains_target": True, "stale_hint": False},
    )
    knowledge_preview = {
        "intake_summary": knowledge_intake,
        "asset_target_candidate": asset_target,
        "validation_report": validation_report,
        "check_report": check_report,
        "risk_flags": validation_report["risk_flags"],
        "requires_confirmation": True,
    }
    knowledge_execution = materialize_knowledge_asset(knowledge_preview)
    knowledge_verification = verify_knowledge_asset(
        knowledge_execution["asset_target"],
        knowledge_execution["validation_report"],
        knowledge_execution["check_report"],
        {"target_exists": True, "index_aligned": True},
    )
    _append_step(
        step_results,
        breakpoints,
        "knowledge-ops",
        knowledge_execution["status"],
        knowledge_preview["risk_flags"],
        {"preview": knowledge_preview, "execution": knowledge_execution},
        knowledge_verification,
    )

    return {"step_results": step_results, "breakpoints": breakpoints}
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_chain_orchestrator.py -v
```

Expected: PASS with `Ran 2 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/integration/chain_orchestrator.py \
        github-actions/tests/test_chain_orchestrator.py
git commit -m "feat: add five skill chain orchestrator"
```

## Task 4: Add the Reporter and Top-Level Runner

**Files:**
- Create: `github-actions/feishu_collab/integration/rehearsal_reporter.py`
- Create: `github-actions/run_five_skill_integration_rehearsal.py`
- Create: `github-actions/tests/test_rehearsal_reporter.py`
- Create: `github-actions/tests/test_run_five_skill_integration_rehearsal.py`

- [ ] **Step 1: Write the failing reporter and runner tests**

Create `github-actions/tests/test_rehearsal_reporter.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "integration" / "rehearsal_reporter.py"
SPEC = importlib.util.spec_from_file_location("rehearsal_reporter", MODULE_PATH)


class RehearsalReporterTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_reporter_uses_blocked_fail_warn_pass_precedence(self):
        module = self.load_module()
        report = module.build_rehearsal_report(
            scenario_manifest={"scenario_id": "core-objective-baseline", "skill_sequence": []},
            step_results=[
                {"skill_name": "okr-driven", "normalized": {"system_status": "pass"}, "raw_result": {"execution": {"knowledge_update": {"title": "okr"}}}},
                {"skill_name": "github-sync", "normalized": {"system_status": "warn"}, "raw_result": {"execution": {"knowledge_update": {"title": "sync"}}}},
                {"skill_name": "approval", "normalized": {"system_status": "fail"}, "raw_result": {"execution": {"knowledge_update": {"title": "approval"}}}},
            ],
            breakpoints=[{"skill_name": "approval", "breakpoint_type": "contract_gap", "recovery_hint": "fix contract"}],
        )
        self.assertEqual(report["system_status"], "fail")
        self.assertEqual(report["handoff"]["status"], "fail")
        self.assertEqual(report["knowledge_update"]["title"], "approval")


if __name__ == "__main__":
    unittest.main()
```

Create `github-actions/tests/test_run_five_skill_integration_rehearsal.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_five_skill_integration_rehearsal.py"
SPEC = importlib.util.spec_from_file_location("run_five_skill_integration_rehearsal", MODULE_PATH)


class RunFiveSkillIntegrationRehearsalTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_runner_returns_system_report_for_default_scenario(self):
        module = self.load_module()
        report = module.run_rehearsal()
        self.assertEqual(report["scenario_manifest"]["scenario_id"], "core-objective-baseline")
        self.assertEqual(len(report["step_results"]), 5)
        self.assertIn(report["system_status"], {"pass", "warn", "fail", "blocked"})
        self.assertIn("handoff", report)
        self.assertIn("knowledge_update", report)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_rehearsal_reporter.py \
  github-actions/tests/test_run_five_skill_integration_rehearsal.py -v
```

Expected: FAIL because `rehearsal_reporter.py` and `run_five_skill_integration_rehearsal.py` do not exist yet.

- [ ] **Step 3: Write the minimal reporter and runner**

Create `github-actions/feishu_collab/integration/rehearsal_reporter.py`:

```python
STATUS_ORDER = {"pass": 0, "warn": 1, "fail": 2, "blocked": 3}


def _system_status(step_results):
    if not step_results:
        return "blocked"
    return max(
        (step["normalized"]["system_status"] for step in step_results),
        key=lambda value: STATUS_ORDER[value],
    )


def build_rehearsal_report(scenario_manifest, step_results, breakpoints):
    system_status = _system_status(step_results)
    final_execution = step_results[-1]["raw_result"]["execution"] if step_results else {}
    return {
        "scenario_manifest": scenario_manifest,
        "step_results": step_results,
        "breakpoints": breakpoints,
        "system_status": system_status,
        "verification_summary": {
            "step_count": len(step_results),
            "breakpoint_count": len(breakpoints),
            "highest_status": system_status,
        },
        "handoff": {
            "type": "stage_handoff",
            "status": system_status,
            "summary": f"five skill rehearsal {system_status}",
            "next_action": "review breakpoints and rerun if needed",
            "evidence_refs": [item["skill_name"] for item in step_results],
        },
        "knowledge_update": final_execution.get(
            "knowledge_update",
            {
                "asset_type": "delivery",
                "title": "five-skill-rehearsal-result",
                "summary": f"status={system_status}",
                "evidence_refs": [item["skill_name"] for item in step_results],
            },
        ),
    }
```

Create `github-actions/run_five_skill_integration_rehearsal.py`:

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


DEFAULT_SCENARIO = (
    ROOT / "tests" / "fixtures" / "integration" / "core_objective_baseline.json"
)


def run_rehearsal(scenario_path=None):
    payload = load_rehearsal_scenario(ROOT.parent, scenario_path or DEFAULT_SCENARIO)
    result = run_rehearsal_chain(payload)
    return build_rehearsal_report(
        scenario_manifest=payload["scenario_manifest"],
        step_results=result["step_results"],
        breakpoints=result["breakpoints"],
    )


if __name__ == "__main__":
    report = run_rehearsal()
    json.dump(report, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_rehearsal_reporter.py \
  github-actions/tests/test_run_five_skill_integration_rehearsal.py -v
```

Expected: PASS with `Ran 2 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/integration/rehearsal_reporter.py \
        github-actions/run_five_skill_integration_rehearsal.py \
        github-actions/tests/test_rehearsal_reporter.py \
        github-actions/tests/test_run_five_skill_integration_rehearsal.py
git commit -m "feat: add five skill rehearsal runner"
```

## Task 5: Add the Runbook and Validate the Baseline

**Files:**
- Create: `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`
- Modify: `docs/feishu-collab/RUNBOOK_INDEX.md`
- Modify: `github-actions/feishu_collab/shared/status_adapter.py`
- Modify: `github-actions/feishu_collab/integration/scenario_loader.py`
- Modify: `github-actions/feishu_collab/integration/chain_orchestrator.py`
- Modify: `github-actions/feishu_collab/integration/rehearsal_reporter.py`
- Modify: `github-actions/run_five_skill_integration_rehearsal.py`

- [ ] **Step 1: Write the runbook and index entry**

Create `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md`:

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

## Command

    python3 github-actions/run_five_skill_integration_rehearsal.py

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
- `warn`: the step completed with degraded evidence and the chain continued
- `fail`: the step completed with a non-blocking contract or execution issue
- `blocked`: the step cannot safely continue and the chain stops

## Recovery Guide

- If `policy_gap`, fix the governance input and rerun
- If `data_gap`, repair the fixture or missing reference and rerun
- If `contract_gap`, align the step interface and rerun
- If `execution_gap`, inspect the skill output and rerun
```

Modify `docs/feishu-collab/RUNBOOK_INDEX.md` by adding this row:

```md
| Five Skill Integration Rehearsal | `docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md` | Run the fixture-driven full-chain rehearsal and interpret the normalized result |
```

- [ ] **Step 2: Run the full targeted test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_status_adapter.py \
  github-actions/tests/test_integration_scenario_loader.py \
  github-actions/tests/test_chain_orchestrator.py \
  github-actions/tests/test_rehearsal_reporter.py \
  github-actions/tests/test_run_five_skill_integration_rehearsal.py \
  github-actions/tests/test_build_okr_driven_preview.py \
  github-actions/tests/test_materialize_okr_driven_execution.py \
  github-actions/tests/test_build_bitable_preview.py \
  github-actions/tests/test_materialize_bitable_execution.py \
  github-actions/tests/test_verify_bitable_projection.py \
  github-actions/tests/test_build_github_sync_preview.py \
  github-actions/tests/test_github_sync_event_registry.py \
  github-actions/tests/test_materialize_github_sync_execution.py \
  github-actions/tests/test_verify_github_sync_projection.py \
  github-actions/tests/test_build_approval_preview.py \
  github-actions/tests/test_materialize_approval_execution.py \
  github-actions/tests/test_verify_approval_projection.py \
  github-actions/tests/test_knowledge_intake.py \
  github-actions/tests/test_validate_knowledge_asset.py \
  github-actions/tests/test_check_knowledge_assets.py \
  github-actions/tests/test_materialize_knowledge_asset.py \
  github-actions/tests/test_verify_knowledge_asset.py \
  github-actions/tests/test_knowledge_ops_end_to_end_contract.py \
  github-actions/tests/test_feishu_collab_contracts.py \
  github-actions/tests/test_feishu_collab_docs_structure.py -v
```

Expected: all rehearsal and referenced skill tests PASS.

- [ ] **Step 3: Perform the local rehearsal dry-run**

Run:

```bash
python3 github-actions/run_five_skill_integration_rehearsal.py
```

Expected:

- `scenario_manifest.scenario_id` is `core-objective-baseline`
- `step_results` contains five entries in the fixed skill order
- `system_status` is one of `pass`, `warn`, `fail`, `blocked`
- `handoff.status` matches `system_status`
- `knowledge_update` is present

- [ ] **Step 4: Commit**

```bash
git add docs/feishu-collab/runbooks/five-skill-integration-rehearsal.md \
        docs/feishu-collab/RUNBOOK_INDEX.md \
        github-actions/feishu_collab/shared/status_adapter.py \
        github-actions/feishu_collab/integration/__init__.py \
        github-actions/feishu_collab/integration/scenario_loader.py \
        github-actions/feishu_collab/integration/chain_orchestrator.py \
        github-actions/feishu_collab/integration/rehearsal_reporter.py \
        github-actions/run_five_skill_integration_rehearsal.py \
        github-actions/tests/fixtures/integration/core_objective_baseline.json \
        github-actions/tests/test_status_adapter.py \
        github-actions/tests/test_integration_scenario_loader.py \
        github-actions/tests/test_chain_orchestrator.py \
        github-actions/tests/test_rehearsal_reporter.py \
        github-actions/tests/test_run_five_skill_integration_rehearsal.py
git commit -m "test: validate five skill rehearsal baseline"
```

## Self-Review

- Spec coverage:
  - shared status adapter and unified status vocabulary: Task 1
  - `core-objective-baseline` scenario loading: Task 2
  - fixed five-skill chain and breakpoint capture: Task 3
  - system report, handoff, and `KnowledgeUpdate`: Task 4
  - operator runbook and full validation pass: Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred markers
  - Every code step includes concrete file content
  - Every verification step includes exact commands and expected outcomes
- Type consistency:
  - Raw skill statuses remain `confirmed`, `degraded_success`, `soft_block`, `hard_block`, `blocked`
  - System statuses remain `pass`, `warn`, `fail`, `blocked`
  - Step result shape stays consistent across orchestrator and reporter: `skill_name`, `raw_result`, `verification`, `normalized`
