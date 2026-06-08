# Knowledge-Ops SKILL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a preview-first `Knowledge-Ops SKILL` that normalizes `KnowledgeUpdate` intake, validates asset targets and metadata, runs `drift / gap / stale` checks, writes knowledge assets to the right docs location, and emits handoff plus governance results after verification.

**Architecture:** Keep the skill package thin and move deterministic behavior into focused Python helpers under `github-actions/feishu_collab/knowledge_ops/`. Reuse the existing shared `KnowledgeUpdate` contract, path-routing logic, templates, and index structure, then add a stronger intake normalizer, asset validator, knowledge checker, materializer, and verifier so the skill can orchestrate `intake -> preview -> confirmation -> materialize -> verify -> handoff`.

**Tech Stack:** Markdown skill docs, Python 3, `unittest`, `json`, existing Feishu-collaboration templates/indexes, shared Feishu-collaboration contracts

---

## Scope Check

This plan covers one coherent sub-project:

- Normalize `KnowledgeUpdate` and handoff-like inputs into a canonical intake object
- Resolve governed asset targets and validate metadata before writeback
- Run `drift / gap / stale` checks as first-class governance results
- Materialize runbook / handoff / governance assets and verify index alignment
- Package the flow as `.trae/skills/feishu-collab-knowledge-ops/SKILL.md`
- Verify that `ExecutionResult`, `KnowledgeUpdate` receipts, and handoff outputs are produced after execution

It does **not** include:

- A knowledge dashboard or operations UI
- Automatic rewriting of historical assets
- A background scheduler or cron-driven audit service
- External knowledge-base synchronization
- Complex self-healing repair flows

## File Map

- Create: `.trae/skills/feishu-collab-knowledge-ops/SKILL.md`
  - Main skill instructions, trigger conditions, preview-first governance flow, and knowledge guardrails.
- Create: `.trae/skills/feishu-collab-knowledge-ops/references/execution-checklist.md`
  - Operator checklist for intake review, validation review, checker review, writeback, and verification.
- Create: `.trae/skills/feishu-collab-knowledge-ops/references/check-policy.md`
  - Explicit policy for `drift / gap / stale` severity, overwrite handling, and fallback expectations.
- Create: `github-actions/feishu_collab/knowledge_ops/intake.py`
  - Normalize `KnowledgeUpdate` plus optional handoff/source metadata into a canonical intake object.
- Create: `github-actions/tests/test_knowledge_intake.py`
  - Lock canonical intake behavior, default metadata handling, and source-skill retention.
- Create: `github-actions/tests/fixtures/knowledge_ops/knowledge_update.json`
  - Stable knowledge-update fixture for preview and dry-run validation.
- Create: `github-actions/tests/fixtures/knowledge_ops/handoff_context.json`
  - Stable handoff/source fixture with source skill, evidence, and delivery context.
- Modify: `github-actions/feishu_collab/knowledge_ops/pathing.py`
  - Keep current route mapping but add stronger target validation behavior for empty titles and unknown types.
- Create: `github-actions/feishu_collab/knowledge_ops/validate_knowledge_asset.py`
  - Validate title, asset type, template compatibility, evidence presence, and overwrite conditions.
- Create: `github-actions/tests/test_validate_knowledge_asset.py`
  - Lock validation behavior for empty title, unknown asset type, missing evidence, and template existence.
- Create: `github-actions/feishu_collab/knowledge_ops/check_knowledge_assets.py`
  - Compute `drift / gap / stale` checks from intake data, target info, and current docs/index state.
- Create: `github-actions/tests/test_check_knowledge_assets.py`
  - Lock checker behavior and severity classification.
- Create: `github-actions/feishu_collab/knowledge_ops/materialize_knowledge_asset.py`
  - Turn preview output into ordered writeback stages, target file content, index update plan, `KnowledgeUpdate` receipt, and handoff.
- Create: `github-actions/tests/test_materialize_knowledge_asset.py`
  - Lock writeback order, degraded outcomes, and governance receipts.
- Create: `github-actions/feishu_collab/knowledge_ops/verify_knowledge_asset.py`
  - Re-check file existence, required headings, index alignment, and preserved checker output after writeback.
- Create: `github-actions/tests/test_verify_knowledge_asset.py`
  - Lock verification behavior for `hard_block`, `soft_block`, `degraded_success`, and `confirmed`.
- Create: `github-actions/tests/test_knowledge_ops_end_to_end_contract.py`
  - Lock the dry-run payload shape between intake, validation, checker, materializer, and verifier.

## Execution Guardrails

- Keep v1 focused on `Intake + Validation + Check`; do not add dashboards, schedulers, or auto-rewriters.
- Reuse the existing `KnowledgeUpdate` shared contract from `github-actions/feishu_collab/shared/contracts.py`; do not invent a second incompatible knowledge event shape.
- Reuse the existing route mapping semantics from `github-actions/feishu_collab/knowledge_ops/pathing.py`; extend validation around them rather than replacing them wholesale.
- Treat unknown `asset_type`, empty title, missing template, or unresolved target path as explicit `hard_block`; never silently fall back to an arbitrary directory.
- Keep `drift / gap / stale` as first-class results in preview and verification; never hide them in logs only.
- Emit `KnowledgeUpdate` receipt and handoff payloads whenever execution reaches verification, including degraded outcomes.

## Task 1: Add Canonical Intake and Target Validation

**Files:**
- Create: `github-actions/feishu_collab/knowledge_ops/intake.py`
- Modify: `github-actions/feishu_collab/knowledge_ops/pathing.py`
- Create: `github-actions/feishu_collab/knowledge_ops/validate_knowledge_asset.py`
- Create: `github-actions/tests/test_knowledge_intake.py`
- Create: `github-actions/tests/test_validate_knowledge_asset.py`
- Create: `github-actions/tests/fixtures/knowledge_ops/knowledge_update.json`
- Create: `github-actions/tests/fixtures/knowledge_ops/handoff_context.json`

- [ ] **Step 1: Write the failing intake and validation tests**

Create `github-actions/tests/test_knowledge_intake.py`:

```python
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "intake.py"
SPEC = importlib.util.spec_from_file_location("knowledge_intake", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "knowledge_ops"


class KnowledgeIntakeTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_normalize_knowledge_intake_preserves_source_skill_and_handoff(self):
        module = self.load_module()
        result = module.normalize_knowledge_intake(
            knowledge_update=self.load_fixture("knowledge_update.json"),
            handoff_context=self.load_fixture("handoff_context.json"),
        )
        self.assertEqual(result["asset_type"], "operations")
        self.assertEqual(result["title"], "Approval timeout recovery")
        self.assertEqual(result["source_skill"], "feishu-collab-approval")
        self.assertEqual(result["handoff_summary"], "Approval timed out and needs manual review")

    def test_normalize_knowledge_intake_defaults_missing_handoff_summary(self):
        module = self.load_module()
        result = module.normalize_knowledge_intake(
            knowledge_update=self.load_fixture("knowledge_update.json"),
            handoff_context={},
        )
        self.assertEqual(result["handoff_summary"], "")


if __name__ == "__main__":
    unittest.main()
```

Create `github-actions/tests/test_validate_knowledge_asset.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "validate_knowledge_asset.py"
SPEC = importlib.util.spec_from_file_location("validate_knowledge_asset", MODULE_PATH)


class ValidateKnowledgeAssetTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_validation_accepts_operations_asset_with_evidence(self):
        module = self.load_module()
        result = module.validate_knowledge_asset(
            intake={
                "asset_type": "operations",
                "title": "Approval timeout recovery",
                "summary": "Manual recovery path for timed-out approvals",
                "evidence_refs": ["task-approval-001"],
            }
        )
        self.assertEqual(result["title_valid"], True)
        self.assertEqual(result["asset_type_valid"], True)
        self.assertEqual(result["evidence_valid"], True)
        self.assertEqual(result["template_type"], "runbook")

    def test_validation_marks_empty_title_as_invalid(self):
        module = self.load_module()
        result = module.validate_knowledge_asset(
            intake={
                "asset_type": "operations",
                "title": "",
                "summary": "Manual recovery path for timed-out approvals",
                "evidence_refs": ["task-approval-001"],
            }
        )
        self.assertEqual(result["title_valid"], False)
        self.assertIn("empty_title", result["risk_flags"])

    def test_validation_marks_unknown_asset_type_as_invalid(self):
        module = self.load_module()
        result = module.validate_knowledge_asset(
            intake={
                "asset_type": "mystery",
                "title": "Unknown type",
                "summary": "Should fail validation",
                "evidence_refs": ["task-approval-001"],
            }
        )
        self.assertEqual(result["asset_type_valid"], False)
        self.assertIn("unknown_asset_type", result["risk_flags"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add stable fixtures**

Create `github-actions/tests/fixtures/knowledge_ops/knowledge_update.json`:

```json
{
  "asset_type": "operations",
  "title": "Approval timeout recovery",
  "summary": "Manual recovery path for timed-out approvals",
  "evidence_refs": [
    "task-approval-001",
    "instance-approval-001"
  ]
}
```

Create `github-actions/tests/fixtures/knowledge_ops/handoff_context.json`:

```json
{
  "source_skill": "feishu-collab-approval",
  "handoff_summary": "Approval timed out and needs manual review",
  "target_object_id": "task-approval-001",
  "goal_id": "goal-collab-approval-001"
}
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_knowledge_intake.py \
  github-actions/tests/test_validate_knowledge_asset.py -v
```

Expected: FAIL because `intake.py` and `validate_knowledge_asset.py` do not exist yet.

- [ ] **Step 4: Write the minimal intake normalizer and validator**

Create `github-actions/feishu_collab/knowledge_ops/intake.py`:

```python
def normalize_knowledge_intake(knowledge_update, handoff_context):
    return {
        "asset_type": knowledge_update.get("asset_type", ""),
        "title": knowledge_update.get("title", ""),
        "summary": knowledge_update.get("summary", ""),
        "evidence_refs": knowledge_update.get("evidence_refs", []),
        "source_skill": handoff_context.get("source_skill", ""),
        "handoff_summary": handoff_context.get("handoff_summary", ""),
        "target_object_id": handoff_context.get("target_object_id", ""),
        "goal_id": handoff_context.get("goal_id", ""),
    }
```

Modify `github-actions/feishu_collab/knowledge_ops/pathing.py`:

```python
import re


def _slugify(title):
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def resolve_knowledge_target(asset_type, title):
    slug = _slugify(title)
    if not slug:
        raise ValueError("empty_title")
    if asset_type == "operations":
        return f"docs/feishu-collab/runbooks/{slug}.md"
    if asset_type == "delivery":
        return f"docs/feishu-collab/handoffs/{slug}.md"
    if asset_type == "architecture":
        return f"docs/feishu-collab/governance/{slug}.md"
    if asset_type == "policy":
        return f"docs/feishu-collab/governance/{slug}.md"
    raise ValueError("unknown_asset_type")
```

Create `github-actions/feishu_collab/knowledge_ops/validate_knowledge_asset.py`:

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def validate_knowledge_asset(intake):
    asset_type = intake.get("asset_type", "")
    title = intake.get("title", "")
    evidence_refs = intake.get("evidence_refs", [])
    risk_flags = []

    title_valid = bool(title.strip())
    if not title_valid:
        risk_flags.append("empty_title")

    asset_type_valid = asset_type in {"operations", "delivery", "architecture", "policy"}
    if not asset_type_valid:
        risk_flags.append("unknown_asset_type")

    evidence_valid = bool(evidence_refs)
    if not evidence_valid:
        risk_flags.append("missing_evidence_refs")

    template_type = "runbook" if asset_type == "operations" else "handoff"
    if asset_type in {"architecture", "policy"}:
        template_type = "governance"

    return {
        "title_valid": title_valid,
        "asset_type_valid": asset_type_valid,
        "evidence_valid": evidence_valid,
        "template_type": template_type,
        "risk_flags": risk_flags,
    }
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_knowledge_intake.py \
  github-actions/tests/test_validate_knowledge_asset.py -v
```

Expected: PASS with `Ran 5 tests ... OK`.

- [ ] **Step 6: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/intake.py \
        github-actions/feishu_collab/knowledge_ops/pathing.py \
        github-actions/feishu_collab/knowledge_ops/validate_knowledge_asset.py \
        github-actions/tests/test_knowledge_intake.py \
        github-actions/tests/test_validate_knowledge_asset.py \
        github-actions/tests/fixtures/knowledge_ops/knowledge_update.json \
        github-actions/tests/fixtures/knowledge_ops/handoff_context.json
git commit -m "feat: add knowledge ops intake validation"
```

## Task 2: Add Drift/Gap/Stale Checks

**Files:**
- Create: `github-actions/feishu_collab/knowledge_ops/check_knowledge_assets.py`
- Create: `github-actions/tests/test_check_knowledge_assets.py`

- [ ] **Step 1: Write the failing checker tests**

Create `github-actions/tests/test_check_knowledge_assets.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "check_knowledge_assets.py"
SPEC = importlib.util.spec_from_file_location("check_knowledge_assets", MODULE_PATH)


class CheckKnowledgeAssetsTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_checker_returns_clean_result_for_valid_asset(self):
        module = self.load_module()
        result = module.check_knowledge_assets(
            intake={"title": "Approval timeout recovery", "evidence_refs": ["task-approval-001"]},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            existing_state={"index_contains_target": True, "stale_hint": False},
        )
        self.assertEqual(result["severity"], "none")
        self.assertEqual(result["drift_flags"], [])
        self.assertEqual(result["gap_flags"], [])
        self.assertEqual(result["stale_flags"], [])

    def test_checker_marks_gap_when_index_missing(self):
        module = self.load_module()
        result = module.check_knowledge_assets(
            intake={"title": "Approval timeout recovery", "evidence_refs": ["task-approval-001"]},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            existing_state={"index_contains_target": False, "stale_hint": False},
        )
        self.assertIn("index_alignment_gap", result["gap_flags"])
        self.assertEqual(result["severity"], "medium")

    def test_checker_marks_stale_when_source_hint_present(self):
        module = self.load_module()
        result = module.check_knowledge_assets(
            intake={"title": "Approval timeout recovery", "evidence_refs": ["task-approval-001"]},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            existing_state={"index_contains_target": True, "stale_hint": True},
        )
        self.assertIn("stale_source_hint", result["stale_flags"])
        self.assertEqual(result["severity"], "medium")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_check_knowledge_assets.py -v
```

Expected: FAIL because `check_knowledge_assets.py` does not exist yet.

- [ ] **Step 3: Write the minimal checker**

Create `github-actions/feishu_collab/knowledge_ops/check_knowledge_assets.py`:

```python
def check_knowledge_assets(intake, validation_report, existing_state):
    drift_flags = []
    gap_flags = []
    stale_flags = []
    severity = "none"
    repair_suggestions = []

    if not validation_report.get("title_valid") or not validation_report.get("asset_type_valid"):
        drift_flags.append("validation_drift")
        severity = "high"
        repair_suggestions.append("fix title or asset type")

    if not existing_state.get("index_contains_target", False):
        gap_flags.append("index_alignment_gap")
        if severity == "none":
            severity = "medium"
        repair_suggestions.append("add target to index")

    if existing_state.get("stale_hint", False):
        stale_flags.append("stale_source_hint")
        if severity == "none":
            severity = "medium"
        repair_suggestions.append("refresh stale asset metadata")

    return {
        "drift_flags": drift_flags,
        "gap_flags": gap_flags,
        "stale_flags": stale_flags,
        "severity": severity,
        "repair_suggestions": repair_suggestions,
    }
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_check_knowledge_assets.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/check_knowledge_assets.py \
        github-actions/tests/test_check_knowledge_assets.py
git commit -m "feat: add knowledge ops checker"
```

## Task 3: Add the Knowledge Asset Materializer

**Files:**
- Create: `github-actions/feishu_collab/knowledge_ops/materialize_knowledge_asset.py`
- Create: `github-actions/tests/test_materialize_knowledge_asset.py`

- [ ] **Step 1: Write the failing materialization tests**

Create `github-actions/tests/test_materialize_knowledge_asset.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "materialize_knowledge_asset.py"
SPEC = importlib.util.spec_from_file_location("materialize_knowledge_asset", MODULE_PATH)


class MaterializeKnowledgeAssetTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "intake_summary": {
                "asset_type": "operations",
                "title": "Approval timeout recovery",
                "source_skill": "feishu-collab-approval",
            },
            "asset_target_candidate": {
                "target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md",
                "template_type": "runbook",
                "index_target": "docs/feishu-collab/RUNBOOK_INDEX.md",
                "allow_overwrite": False,
            },
            "validation_report": {
                "title_valid": True,
                "asset_type_valid": True,
                "evidence_valid": True,
                "risk_flags": [],
            },
            "check_report": {
                "drift_flags": [],
                "gap_flags": [],
                "stale_flags": [],
                "severity": "none",
                "repair_suggestions": [],
            },
            "risk_flags": [],
            "requires_confirmation": True,
        }

    def test_materialize_builds_writeback_order_handoff_and_receipt(self):
        module = self.load_module()
        result = module.materialize_knowledge_asset(self.sample_preview())
        self.assertEqual(
            result["writeback_order"],
            [
                "intake_normalization",
                "asset_target_resolution",
                "validation_snapshot",
                "knowledge_asset_writeback",
                "index_alignment_check",
            ],
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["knowledge_update"]["asset_type"], "operations")
        self.assertEqual(result["handoff"]["type"], "stage_handoff")

    def test_materialize_marks_hard_block_for_unknown_asset_type(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["unknown_asset_type"]
        result = module.materialize_knowledge_asset(preview)
        self.assertEqual(result["status"], "hard_block")

    def test_materialize_marks_soft_block_for_index_alignment_gap(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["check_report"]["gap_flags"] = ["index_alignment_gap"]
        preview["check_report"]["severity"] = "medium"
        result = module.materialize_knowledge_asset(preview)
        self.assertEqual(result["status"], "soft_block")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_knowledge_asset.py -v
```

Expected: FAIL because `materialize_knowledge_asset.py` does not exist yet.

- [ ] **Step 3: Write the minimal materializer**

Create `github-actions/feishu_collab/knowledge_ops/materialize_knowledge_asset.py`:

```python
import json
import sys


WRITEBACK_ORDER = [
    "intake_normalization",
    "asset_target_resolution",
    "validation_snapshot",
    "knowledge_asset_writeback",
    "index_alignment_check",
]


def materialize_knowledge_asset(preview):
    status = "confirmed"
    risk_flags = preview.get("risk_flags", [])
    check_report = preview.get("check_report", {})
    if "unknown_asset_type" in risk_flags or "empty_title" in risk_flags:
        status = "hard_block"
    elif check_report.get("gap_flags"):
        status = "soft_block"
    elif check_report.get("stale_flags"):
        status = "degraded_success"

    target_path = preview["asset_target_candidate"].get("target_path", "")

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "asset_target": preview["asset_target_candidate"],
        "validation_report": preview["validation_report"],
        "check_report": check_report,
        "knowledge_update": {
            "asset_type": preview["intake_summary"].get("asset_type", ""),
            "title": preview["intake_summary"].get("title", ""),
            "summary": f"status={status}",
            "evidence_refs": [target_path] if target_path else [],
        },
        "handoff": {
            "type": "stage_handoff",
            "status": status,
            "summary": f"knowledge ops execution {status}",
            "next_action": "review knowledge verification result",
            "evidence_refs": [target_path] if target_path else [],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_knowledge_asset(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_knowledge_asset.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/materialize_knowledge_asset.py \
        github-actions/tests/test_materialize_knowledge_asset.py
git commit -m "feat: add knowledge ops materializer"
```

## Task 4: Add Verification and End-to-End Contract Coverage

**Files:**
- Create: `github-actions/feishu_collab/knowledge_ops/verify_knowledge_asset.py`
- Create: `github-actions/tests/test_verify_knowledge_asset.py`
- Create: `github-actions/tests/test_knowledge_ops_end_to_end_contract.py`

- [ ] **Step 1: Write the failing verification and contract tests**

Create `github-actions/tests/test_verify_knowledge_asset.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "verify_knowledge_asset.py"
SPEC = importlib.util.spec_from_file_location("verify_knowledge_asset", MODULE_PATH)


class VerifyKnowledgeAssetTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_target_and_index_are_aligned(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md"},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": [], "stale_flags": []},
            existing_state={"target_exists": True, "index_aligned": True},
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_hard_block_when_target_missing(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": ""},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": [], "stale_flags": []},
            existing_state={"target_exists": False, "index_aligned": False},
        )
        self.assertEqual(result["status"], "hard_block")

    def test_verify_returns_soft_block_when_gap_persists(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md"},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": ["index_alignment_gap"], "stale_flags": []},
            existing_state={"target_exists": True, "index_aligned": False},
        )
        self.assertEqual(result["status"], "soft_block")

    def test_verify_returns_degraded_success_when_stale_flag_persists(self):
        module = self.load_module()
        result = module.verify_knowledge_asset(
            asset_target={"target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md"},
            validation_report={"title_valid": True, "asset_type_valid": True, "evidence_valid": True},
            check_report={"drift_flags": [], "gap_flags": [], "stale_flags": ["stale_source_hint"]},
            existing_state={"target_exists": True, "index_aligned": True},
        )
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()
```

Create `github-actions/tests/test_knowledge_ops_end_to_end_contract.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INTAKE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "intake.py"
VALIDATE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "validate_knowledge_asset.py"
CHECK_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "check_knowledge_assets.py"
MATERIALIZE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "materialize_knowledge_asset.py"
VERIFY_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "verify_knowledge_asset.py"


def load_module(module_path, name):
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class KnowledgeOpsEndToEndContractTests(unittest.TestCase):
    def test_end_to_end_payload_shapes_align(self):
        intake_module = load_module(INTAKE_PATH, "knowledge_intake")
        validate_module = load_module(VALIDATE_PATH, "validate_knowledge_asset")
        check_module = load_module(CHECK_PATH, "check_knowledge_assets")
        materialize_module = load_module(MATERIALIZE_PATH, "materialize_knowledge_asset")
        verify_module = load_module(VERIFY_PATH, "verify_knowledge_asset")

        intake = intake_module.normalize_knowledge_intake(
            knowledge_update={
                "asset_type": "operations",
                "title": "Approval timeout recovery",
                "summary": "Manual recovery path for timed-out approvals",
                "evidence_refs": ["task-approval-001"],
            },
            handoff_context={"source_skill": "feishu-collab-approval", "handoff_summary": "manual review"},
        )
        validation = validate_module.validate_knowledge_asset(intake)
        checks = check_module.check_knowledge_assets(
            intake=intake,
            validation_report=validation,
            existing_state={"index_contains_target": True, "stale_hint": False},
        )
        preview = {
            "intake_summary": intake,
            "asset_target_candidate": {
                "target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md",
                "template_type": validation["template_type"],
                "index_target": "docs/feishu-collab/RUNBOOK_INDEX.md",
                "allow_overwrite": False,
            },
            "validation_report": validation,
            "check_report": checks,
            "risk_flags": validation["risk_flags"],
            "requires_confirmation": True,
        }
        execution = materialize_module.materialize_knowledge_asset(preview)
        verification = verify_module.verify_knowledge_asset(
            asset_target=execution["asset_target"],
            validation_report=execution["validation_report"],
            check_report=execution["check_report"],
            existing_state={"target_exists": True, "index_aligned": True},
        )

        self.assertEqual(execution["status"], "confirmed")
        self.assertEqual(verification["status"], "confirmed")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_verify_knowledge_asset.py \
  github-actions/tests/test_knowledge_ops_end_to_end_contract.py -v
```

Expected: FAIL because `verify_knowledge_asset.py` and end-to-end contract wiring do not exist yet.

- [ ] **Step 3: Write the minimal verifier**

Create `github-actions/feishu_collab/knowledge_ops/verify_knowledge_asset.py`:

```python
import json
import sys


def verify_knowledge_asset(asset_target, validation_report, check_report, existing_state):
    if not asset_target.get("target_path"):
        status = "hard_block"
    elif check_report.get("gap_flags") or not existing_state.get("index_aligned", False):
        status = "soft_block"
    elif check_report.get("stale_flags"):
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "target_path": asset_target.get("target_path", ""),
        "index_aligned": existing_state.get("index_aligned", False),
        "target_exists": existing_state.get("target_exists", False),
        "has_drift": bool(check_report.get("drift_flags")),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_knowledge_asset(
            payload["asset_target"],
            payload["validation_report"],
            payload["check_report"],
            payload["existing_state"],
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
python3 -m unittest \
  github-actions/tests/test_verify_knowledge_asset.py \
  github-actions/tests/test_knowledge_ops_end_to_end_contract.py -v
```

Expected: PASS with `Ran 5 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/knowledge_ops/verify_knowledge_asset.py \
        github-actions/tests/test_verify_knowledge_asset.py \
        github-actions/tests/test_knowledge_ops_end_to_end_contract.py
git commit -m "feat: add knowledge ops verification"
```

## Task 5: Package the Skill and Validate the Baseline

**Files:**
- Create: `.trae/skills/feishu-collab-knowledge-ops/SKILL.md`
- Create: `.trae/skills/feishu-collab-knowledge-ops/references/execution-checklist.md`
- Create: `.trae/skills/feishu-collab-knowledge-ops/references/check-policy.md`
- Modify: `github-actions/feishu_collab/knowledge_ops/intake.py`
- Modify: `github-actions/feishu_collab/knowledge_ops/pathing.py`
- Modify: `github-actions/feishu_collab/knowledge_ops/validate_knowledge_asset.py`
- Modify: `github-actions/feishu_collab/knowledge_ops/check_knowledge_assets.py`
- Modify: `github-actions/feishu_collab/knowledge_ops/materialize_knowledge_asset.py`
- Modify: `github-actions/feishu_collab/knowledge_ops/verify_knowledge_asset.py`

- [ ] **Step 1: Write the skill package files**

Create `.trae/skills/feishu-collab-knowledge-ops/SKILL.md`:

```md
---
name: "feishu-collab-knowledge-ops"
description: "Normalizes KnowledgeUpdate intake, validates governed asset targets, checks drift/gap/stale signals, writes governed knowledge assets, and emits handoff after verification."
---

# Feishu Collaboration Knowledge Ops

## When to use

Use this skill when:

- another Feishu collaboration skill emits a `KnowledgeUpdate`
- a handoff or runbook needs governed routing and validation
- the user needs drift/gap/stale checks before storing knowledge
- the flow must emit verification and governance handoff after writeback

## Inputs

- `KnowledgeUpdate`
- optional handoff summary and source skill metadata
- optional existing asset/index state

## Flow

1. normalize knowledge intake
2. build preview with target, validation, and checks
3. confirm writeback or overwrite
4. materialize governed asset
5. verify file and index alignment
6. generate handoff and `KnowledgeUpdate` receipt

## Guardrails

- never skip preview
- treat unknown asset type as hard block
- treat empty title as hard block
- treat missing evidence or index gaps as soft block
- treat stale assets as degraded success
- do not expand into dashboards in v1
```

Create `.trae/skills/feishu-collab-knowledge-ops/references/execution-checklist.md`:

```md
# Execution Checklist

## Intake Gate

- Confirm `asset_type` is present
- Confirm title is present
- Confirm source skill or handoff context is visible

## Validation Gate

- Confirm target path is resolved
- Confirm template type matches asset type
- Confirm evidence refs are present
- Confirm overwrite handling is explicit

## Check Gate

- Confirm drift results are visible
- Confirm gap results are visible
- Confirm stale results are visible

## Verification Gate

- Confirm target file exists
- Confirm index alignment is checked
- Confirm handoff and `KnowledgeUpdate` receipt are emitted
```

Create `.trae/skills/feishu-collab-knowledge-ops/references/check-policy.md`:

```md
# Check Policy

## Hard Block

- Unknown `asset_type`
- Empty title
- Missing template
- Unresolved target path

## Soft Block

- Missing evidence refs
- Index alignment gap
- Missing required metadata

## Degraded Success

- Asset written but stale flag persists
- Asset written but metadata still needs refresh

## Expected Checks

- `drift`
- `gap`
- `stale`
```

- [ ] **Step 2: Sanity-check the skill files**

Run:

```bash
python3 -c 'from pathlib import Path
for path in [
    Path(".trae/skills/feishu-collab-knowledge-ops/SKILL.md"),
    Path(".trae/skills/feishu-collab-knowledge-ops/references/execution-checklist.md"),
    Path(".trae/skills/feishu-collab-knowledge-ops/references/check-policy.md"),
]:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
print("knowledge ops skill files ok")'
```

Expected: `knowledge ops skill files ok`

- [ ] **Step 3: Run the full targeted test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_knowledge_intake.py \
  github-actions/tests/test_validate_knowledge_asset.py \
  github-actions/tests/test_check_knowledge_assets.py \
  github-actions/tests/test_materialize_knowledge_asset.py \
  github-actions/tests/test_verify_knowledge_asset.py \
  github-actions/tests/test_knowledge_ops_end_to_end_contract.py \
  github-actions/tests/test_feishu_collab_knowledge_pathing.py \
  github-actions/tests/test_feishu_collab_contracts.py \
  github-actions/tests/test_feishu_collab_docs_structure.py \
  github-actions/tests/test_feishu_collab_audit_registry.py -v
```

Expected: all knowledge-ops related tests PASS.

- [ ] **Step 4: Perform a local dry-run using the fixtures**

Run:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT")
fixture_dir = root / "github-actions" / "tests" / "fixtures" / "knowledge_ops"
knowledge_update = json.loads((fixture_dir / "knowledge_update.json").read_text(encoding="utf-8"))
handoff_context = json.loads((fixture_dir / "handoff_context.json").read_text(encoding="utf-8"))

preview = {
    "intake_summary": {
        "asset_type": knowledge_update["asset_type"],
        "title": knowledge_update["title"],
        "summary": knowledge_update["summary"],
        "evidence_refs": knowledge_update["evidence_refs"],
        "source_skill": handoff_context["source_skill"],
        "handoff_summary": handoff_context["handoff_summary"],
    },
    "asset_target_candidate": {
        "target_path": "docs/feishu-collab/runbooks/approval-timeout-recovery.md",
        "template_type": "runbook",
        "index_target": "docs/feishu-collab/RUNBOOK_INDEX.md",
        "allow_overwrite": False,
    },
    "validation_report": {
        "title_valid": True,
        "asset_type_valid": True,
        "evidence_valid": True,
        "risk_flags": [],
    },
    "check_report": {
        "drift_flags": [],
        "gap_flags": [],
        "stale_flags": [],
        "severity": "none",
        "repair_suggestions": [],
    },
    "risk_flags": [],
    "requires_confirmation": True,
}

execution_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "knowledge_ops" / "materialize_knowledge_asset.py")],
    input=json.dumps(preview, ensure_ascii=False),
    text=True,
)
execution = json.loads(execution_out)

verification_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "knowledge_ops" / "verify_knowledge_asset.py")],
    input=json.dumps(
        {
            "asset_target": execution["asset_target"],
            "validation_report": execution["validation_report"],
            "check_report": execution["check_report"],
            "existing_state": {"target_exists": True, "index_aligned": True},
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

- preview contains intake summary, target candidate, validation report, and check report
- execution contains ordered writeback steps, handoff, and `KnowledgeUpdate` receipt
- verification returns `confirmed`

- [ ] **Step 5: Commit**

```bash
git add .trae/skills/feishu-collab-knowledge-ops/SKILL.md \
        .trae/skills/feishu-collab-knowledge-ops/references/execution-checklist.md \
        .trae/skills/feishu-collab-knowledge-ops/references/check-policy.md \
        github-actions/feishu_collab/knowledge_ops/intake.py \
        github-actions/feishu_collab/knowledge_ops/pathing.py \
        github-actions/feishu_collab/knowledge_ops/validate_knowledge_asset.py \
        github-actions/feishu_collab/knowledge_ops/check_knowledge_assets.py \
        github-actions/feishu_collab/knowledge_ops/materialize_knowledge_asset.py \
        github-actions/feishu_collab/knowledge_ops/verify_knowledge_asset.py \
        github-actions/tests/test_knowledge_intake.py \
        github-actions/tests/test_validate_knowledge_asset.py \
        github-actions/tests/test_check_knowledge_assets.py \
        github-actions/tests/test_materialize_knowledge_asset.py \
        github-actions/tests/test_verify_knowledge_asset.py \
        github-actions/tests/test_knowledge_ops_end_to_end_contract.py \
        github-actions/tests/fixtures/knowledge_ops/knowledge_update.json \
        github-actions/tests/fixtures/knowledge_ops/handoff_context.json
git commit -m "test: validate knowledge ops skill baseline"
```

## Self-Review

- Spec coverage:
  - v1 scope `Intake + Validation + Check`: Task 1, Task 2, and Task 3
  - preview-first flow and governed asset targeting: Task 1 and Task 3
  - `drift / gap / stale` as first-class results: Task 2 and Task 4
  - writeback, verification, handoff, and `KnowledgeUpdate` receipt: Task 3, Task 4, and Task 5
  - skill packaging and operator guidance: Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred implementation markers
  - Every code-bearing step includes concrete code or markdown content
  - Every verification step has exact commands and expected outcomes
- Type consistency:
  - Preview/result names stay aligned with the shared system baseline: `ExecutionPreview`, `ExecutionResult`, `KnowledgeUpdate`
  - Knowledge model names stay aligned with the approved spec: `KnowledgeIntakeSpec`, `AssetTargetSpec`, `AssetValidationSpec`, `KnowledgeCheckSpec`, `KnowledgeWritebackSpec`
  - Failure statuses stay aligned across preview, materialization, and verification: `hard_block`, `soft_block`, `degraded_success`, `confirmed`
