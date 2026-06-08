# Feishu Collaboration System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the Feishu collaboration system foundation in `DREAM-AGENT` by adding governance entrypoints, shared execution contracts, audit baselines for the remaining four core skills, and knowledge-ops routing/templates.

**Architecture:** Keep this phase focused on governance infrastructure rather than implementing all remaining skills. Store the human-facing system docs under `docs/feishu-collab/`, keep executable shared logic under `github-actions/feishu_collab/`, and use small `unittest` suites to lock directory entrypoints, contract shapes, audit registry structure, and knowledge-routing behavior.

**Tech Stack:** Markdown docs, Python 3, `unittest`, `pathlib`, `dataclasses`, existing `github-actions/tests` patterns

---

## Scope Check

This plan covers one coherent sub-project:

- Create a single Feishu-collaboration documentation entrypoint and registry layout
- Add shared machine-readable execution contracts for cross-skill orchestration
- Produce audit baseline assets for the remaining four core skills
- Add knowledge-ops pathing utilities and standard templates for handoff/runbook maintenance

It does **not** include:

- Full implementation of `Bitable`, `GitHub-Feishu`, `Approval`, or `Knowledge-Ops` skills
- Migrating every historical doc into the new structure
- Building a production event bus service
- Reorganizing unrelated historical repositories or snapshots

## File Map

- Create: `docs/feishu-collab/README.md`
  - Feishu-collaboration system entrypoint, reading order, and source-of-truth guidance.
- Create: `docs/feishu-collab/SKILL_REGISTRY.md`
  - Registry of the five core skills, status, scope, and package names.
- Create: `docs/feishu-collab/RUNBOOK_INDEX.md`
  - Runbook categories and navigation entrypoint.
- Create: `docs/feishu-collab/HANDOFF_INDEX.md`
  - Handoff categories, open slots, and update policy.
- Create: `docs/feishu-collab/governance/system-map.md`
  - Human-readable system map for layers, event flow, and maintenance responsibilities.
- Modify: `docs/README.md`
  - Link the new Feishu-collaboration entrypoint from the existing docs home.
- Create: `github-actions/tests/test_feishu_collab_docs_structure.py`
  - Lock docs entrypoints and root README linkage.
- Create: `github-actions/feishu_collab/shared/__init__.py`
  - Shared package marker.
- Create: `github-actions/feishu_collab/shared/contracts.py`
  - `EventEnvelope`, `ExecutionIntent`, `ExecutionPreview`, `ExecutionResult`, `KnowledgeUpdate`.
- Create: `github-actions/tests/test_feishu_collab_contracts.py`
  - Lock shared contract shape and serialization.
- Create: `docs/feishu-collab/registry/skill-audit-matrix.json`
  - Machine-readable audit status for all five core skills.
- Create: `docs/feishu-collab/audits/bitable-skill-audit.md`
  - Current assets, gaps, and next actions for the Bitable skill.
- Create: `docs/feishu-collab/audits/github-sync-skill-audit.md`
  - Current assets, gaps, and next actions for the GitHub-Feishu skill.
- Create: `docs/feishu-collab/audits/approval-skill-audit.md`
  - Current assets, gaps, and next actions for the Approval skill.
- Create: `docs/feishu-collab/audits/knowledge-ops-skill-audit.md`
  - Current assets, gaps, and next actions for the Knowledge-Ops skill.
- Create: `github-actions/tests/test_feishu_collab_audit_registry.py`
  - Validate the audit-matrix schema and audit coverage.
- Create: `docs/feishu-collab/templates/handoff-template.md`
  - Standard stage/fault handoff template.
- Create: `docs/feishu-collab/templates/runbook-template.md`
  - Standard operational runbook template.
- Create: `github-actions/feishu_collab/knowledge_ops/pathing.py`
  - Resolve `KnowledgeUpdate` assets to canonical documentation locations.
- Create: `github-actions/tests/test_feishu_collab_knowledge_pathing.py`
  - Lock asset-type to directory routing and template presence.

## Execution Guardrails

- Ignore the unrelated deletion `.github/workflows/feishu-approval-smoke.yml`; never restore or stage it.
- Ignore `.superpowers/` files and any temporary local state outside the files listed in this plan.
- Keep `DREAM-AGENT` as the only source-of-truth repository for the new system docs.
- Do not implement the remaining four core skills in this plan; only create the governance and audit baseline that defines how they will be checked next.
- Treat knowledge operations as first-class outputs; any task that creates system structure must also define how handoff/runbook assets are routed.

## Task 1: Add Feishu-Collaboration Docs Entrypoints

**Files:**
- Create: `docs/feishu-collab/README.md`
- Create: `docs/feishu-collab/SKILL_REGISTRY.md`
- Create: `docs/feishu-collab/RUNBOOK_INDEX.md`
- Create: `docs/feishu-collab/HANDOFF_INDEX.md`
- Create: `docs/feishu-collab/governance/system-map.md`
- Modify: `docs/README.md`
- Create: `github-actions/tests/test_feishu_collab_docs_structure.py`

- [ ] **Step 1: Write the failing docs-structure test**

Create `github-actions/tests/test_feishu_collab_docs_structure.py`:

```python
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS_ROOT = ROOT / "docs" / "feishu-collab"
DOCS_README = ROOT / "docs" / "README.md"


class FeishuCollabDocsStructureTests(unittest.TestCase):
    def test_docs_entrypoints_exist_with_required_headings(self):
        expected = {
            DOCS_ROOT / "README.md": "# Feishu Collaboration",
            DOCS_ROOT / "SKILL_REGISTRY.md": "# Skill Registry",
            DOCS_ROOT / "RUNBOOK_INDEX.md": "# Runbook Index",
            DOCS_ROOT / "HANDOFF_INDEX.md": "# Handoff Index",
            DOCS_ROOT / "governance" / "system-map.md": "# System Map",
        }
        for path, heading in expected.items():
            self.assertTrue(path.exists(), str(path))
            self.assertIn(heading, path.read_text(encoding="utf-8"))

    def test_docs_readme_links_the_feishu_collaboration_entrypoint(self):
        text = DOCS_README.read_text(encoding="utf-8")
        pattern = re.compile(
            r"\[[^\]]*feishu-collab/README\.md[^\]]*\]\([^)]+feishu-collab/README\.md\)",
            re.IGNORECASE,
        )
        self.assertRegex(text, pattern)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_docs_structure.py -v
```

Expected: FAIL because `docs/feishu-collab/` files do not exist yet and `docs/README.md` does not link the new entrypoint.

- [ ] **Step 3: Write the docs entrypoints and link them from `docs/README.md`**

Create `docs/feishu-collab/README.md`:

```md
# Feishu Collaboration

## Purpose

This directory is the single documentation entrypoint for the Feishu collaboration system in `DREAM-AGENT`.

## Reading Order

1. `governance/system-map.md`
2. `SKILL_REGISTRY.md`
3. `RUNBOOK_INDEX.md`
4. `HANDOFF_INDEX.md`
5. `audits/*.md`

## Source Of Truth

- System governance lives in `docs/feishu-collab/`
- Executable shared logic lives in `github-actions/feishu_collab/`
- Skill packages live in `.trae/skills/feishu-collab-*`
- Historical repositories are reference-only, not design truth
```

Create `docs/feishu-collab/SKILL_REGISTRY.md`:

```md
# Skill Registry

| Skill | Package | Scope | Status |
| --- | --- | --- | --- |
| OKR-driven | `feishu-collab-okr-driven` | Objective/KR orchestration and execution | implemented-v1 |
| Bitable | `feishu-collab-bitable` | Task breakdown, progress alignment, field governance | audit-required |
| GitHub-Feishu | `feishu-collab-github-sync` | GitHub status sync into Feishu collaboration state | audit-required |
| Approval | `feishu-collab-approval` | Risk gating, approval lifecycle, escalation | audit-required |
| Knowledge-Ops | `feishu-collab-knowledge-ops` | Knowledge capture, runbooks, handoff, maintenance | audit-required |
```

Create `docs/feishu-collab/RUNBOOK_INDEX.md`:

```md
# Runbook Index

## Categories

- Change runbooks
- Cross-system reconciliation runbooks
- Fault-isolation runbooks
- Recovery runbooks

## Default Rule

Every production-facing skill execution that changes online state must end with a runbook-valid verification path or a documented gap.
```

Create `docs/feishu-collab/HANDOFF_INDEX.md`:

```md
# Handoff Index

## Categories

- Stage handoff
- Fault handoff

## Required Fields

- Background
- Current state
- Completed work
- Remaining work
- Active blocker
- Next action
- Dependencies
- Risk notes
- Evidence links
```

Create `docs/feishu-collab/governance/system-map.md`:

```md
# System Map

## Layers

- L0 Governance
- L1 Orchestration
- L2 Domain skills
- L3 Execution adapters
- L4 Knowledge and operations

## Event Flow

`event -> impact analysis -> policy check -> dispatch -> writeback -> verification -> handoff`

## Maintenance Rule

The system defaults to event-driven response and may add reconciliation sweeps later as a safety net, not as the primary trigger.
```

Modify `docs/README.md` by adding this bullet under the collaboration/system section:

```md
- [feishu-collab/README.md](feishu-collab/README.md) - 飞书协作体系总入口（治理、技能注册表、runbook、handoff、审计）
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_docs_structure.py -v
```

Expected: PASS with `Ran 2 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/README.md \
        docs/feishu-collab/README.md \
        docs/feishu-collab/SKILL_REGISTRY.md \
        docs/feishu-collab/RUNBOOK_INDEX.md \
        docs/feishu-collab/HANDOFF_INDEX.md \
        docs/feishu-collab/governance/system-map.md \
        github-actions/tests/test_feishu_collab_docs_structure.py
git commit -m "docs: add feishu collaboration entrypoints"
```

## Task 2: Add Shared Execution Contracts

**Files:**
- Create: `github-actions/feishu_collab/shared/__init__.py`
- Create: `github-actions/feishu_collab/shared/contracts.py`
- Create: `github-actions/tests/test_feishu_collab_contracts.py`

- [ ] **Step 1: Write the failing contract tests**

Create `github-actions/tests/test_feishu_collab_contracts.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "shared" / "contracts.py"
SPEC = importlib.util.spec_from_file_location("feishu_collab_contracts", MODULE_PATH)


class FeishuCollabContractsTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_event_envelope_serializes_required_fields(self):
        module = self.load_module()
        event = module.EventEnvelope(
            event_id="evt-001",
            event_type="okr.changed",
            source_system="feishu",
            source_object_id="objective-123",
            changed_fields=["title"],
            risk_hint="medium",
            related_goal_id="goal-001",
            occurred_at="2026-06-08T12:00:00+00:00",
        )
        payload = event.to_dict()
        self.assertEqual(payload["event_type"], "okr.changed")
        self.assertEqual(payload["related_goal_id"], "goal-001")

    def test_execution_preview_requires_confirmation_by_default(self):
        module = self.load_module()
        preview = module.ExecutionPreview(
            intent_id="intent-001",
            impacted_modules=["OKR", "Base"],
            actions=["refresh_projection"],
        )
        self.assertEqual(preview.requires_confirmation, True)
        self.assertEqual(preview.to_dict()["impacted_modules"], ["OKR", "Base"])

    def test_knowledge_update_keeps_evidence_refs_as_list(self):
        module = self.load_module()
        update = module.KnowledgeUpdate(
            asset_type="operations",
            title="approval timeout runbook",
            summary="Capture timeout mitigation",
            evidence_refs=["approval-instance-1", "log://worker"],
        )
        self.assertEqual(update.to_dict()["evidence_refs"][1], "log://worker")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_contracts.py -v
```

Expected: FAIL because `contracts.py` does not exist yet.

- [ ] **Step 3: Write the minimal shared contracts**

Create `github-actions/feishu_collab/shared/__init__.py`:

```python
"""Shared contracts for the Feishu collaboration system."""
```

Create `github-actions/feishu_collab/shared/contracts.py`:

```python
from dataclasses import asdict, dataclass, field
from typing import List


@dataclass
class EventEnvelope:
    event_id: str
    event_type: str
    source_system: str
    source_object_id: str
    changed_fields: List[str]
    risk_hint: str
    related_goal_id: str
    occurred_at: str

    def to_dict(self):
        return asdict(self)


@dataclass
class ExecutionIntent:
    intent_id: str
    goal_id: str
    initiator: str
    requested_action: str
    source_refs: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class ExecutionPreview:
    intent_id: str
    impacted_modules: List[str]
    actions: List[str]
    requires_confirmation: bool = True

    def to_dict(self):
        return asdict(self)


@dataclass
class ExecutionResult:
    intent_id: str
    status: str
    writebacks: List[str] = field(default_factory=list)
    verification_notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class KnowledgeUpdate:
    asset_type: str
    title: str
    summary: str
    evidence_refs: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_contracts.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/shared/__init__.py \
        github-actions/feishu_collab/shared/contracts.py \
        github-actions/tests/test_feishu_collab_contracts.py
git commit -m "feat: add feishu collaboration shared contracts"
```

## Task 3: Add the Four-Skill Audit Baseline

**Files:**
- Create: `docs/feishu-collab/registry/skill-audit-matrix.json`
- Create: `docs/feishu-collab/audits/bitable-skill-audit.md`
- Create: `docs/feishu-collab/audits/github-sync-skill-audit.md`
- Create: `docs/feishu-collab/audits/approval-skill-audit.md`
- Create: `docs/feishu-collab/audits/knowledge-ops-skill-audit.md`
- Create: `github-actions/tests/test_feishu_collab_audit_registry.py`

- [ ] **Step 1: Write the failing audit-registry test**

Create `github-actions/tests/test_feishu_collab_audit_registry.py`:

```python
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX_PATH = ROOT / "docs" / "feishu-collab" / "registry" / "skill-audit-matrix.json"
AUDIT_DIR = ROOT / "docs" / "feishu-collab" / "audits"


class FeishuCollabAuditRegistryTests(unittest.TestCase):
    def test_matrix_covers_all_five_core_skills(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        names = {item["skill"] for item in matrix["skills"]}
        self.assertEqual(
            names,
            {
                "OKR-driven",
                "Bitable",
                "GitHub-Feishu",
                "Approval",
                "Knowledge-Ops",
            },
        )

    def test_remaining_four_skills_have_audit_docs(self):
        expected = {
            "bitable-skill-audit.md",
            "github-sync-skill-audit.md",
            "approval-skill-audit.md",
            "knowledge-ops-skill-audit.md",
        }
        existing = {path.name for path in AUDIT_DIR.glob("*.md")}
        self.assertTrue(expected.issubset(existing))

    def test_each_matrix_entry_has_status_and_next_plan(self):
        matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
        for item in matrix["skills"]:
            self.assertIn("status", item)
            self.assertIn("next_plan", item)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_audit_registry.py -v
```

Expected: FAIL because the registry and audit docs do not exist yet.

- [ ] **Step 3: Write the audit matrix and four audit docs**

Create `docs/feishu-collab/registry/skill-audit-matrix.json`:

```json
{
  "skills": [
    {
      "skill": "OKR-driven",
      "status": "implemented-v1",
      "next_plan": "use as template for the remaining four skills"
    },
    {
      "skill": "Bitable",
      "status": "audit-required",
      "next_plan": "design task decomposition, progress alignment, and field governance adapters"
    },
    {
      "skill": "GitHub-Feishu",
      "status": "audit-required",
      "next_plan": "align GitHub event sync with Base and approval projections"
    },
    {
      "skill": "Approval",
      "status": "audit-required",
      "next_plan": "extract approval gate behavior into a preview-first skill package"
    },
    {
      "skill": "Knowledge-Ops",
      "status": "audit-required",
      "next_plan": "define knowledge intake, runbook routing, and drift checks"
    }
  ]
}
```

Create `docs/feishu-collab/audits/bitable-skill-audit.md`:

```md
# Bitable Skill Audit

## Current Assets

- Base goal record patterns exist
- Boss-view projection logic exists
- OKR anchor writeback contract exists

## Gaps

- No dedicated skill package
- No preview-first task-breakdown compiler
- No unified Base governance references

## Next Plan

- Define input contract from `OKR-driven`
- Add Base field-governance preview
- Add task/progress writeback adapters
```

Create `docs/feishu-collab/audits/github-sync-skill-audit.md`:

```md
# GitHub Sync Skill Audit

## Current Assets

- GitHub-to-Feishu field mapping exists
- Acceptance and collaboration workflows exist
- Goal-record aggregation exists

## Gaps

- No dedicated skill package
- No single preview/result contract for sync actions
- No explicit registry for GitHub event coverage

## Next Plan

- Wrap sync logic in preview-first skill flow
- Define issue/PR/check event coverage
- Align evidence output with Knowledge-Ops
```

Create `docs/feishu-collab/audits/approval-skill-audit.md`:

```md
# Approval Skill Audit

## Current Assets

- Approval REST wrapper exists
- Approval cycle orchestration exists
- Status polling and Base writeback exist

## Gaps

- No standalone skill package
- No approval-specific execution checklist
- No explicit escalation policy reference in skill form

## Next Plan

- Package approval orchestration as a skill
- Add preview/confirm behavior for high-risk changes
- Link escalation paths into runbooks and handoffs
```

Create `docs/feishu-collab/audits/knowledge-ops-skill-audit.md`:

```md
# Knowledge Ops Skill Audit

## Current Assets

- Runbooks and troubleshooting docs exist
- Handoff patterns exist
- Historical knowledge scripts and indexes exist

## Gaps

- No canonical knowledge intake contract
- No unified runbook/handoff index inside `DREAM-AGENT`
- No automated drift-check routing for new evidence

## Next Plan

- Define `KnowledgeUpdate` routing
- Standardize handoff and runbook templates
- Add drift, gap, and stale-asset checks
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_audit_registry.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/feishu-collab/registry/skill-audit-matrix.json \
        docs/feishu-collab/audits/bitable-skill-audit.md \
        docs/feishu-collab/audits/github-sync-skill-audit.md \
        docs/feishu-collab/audits/approval-skill-audit.md \
        docs/feishu-collab/audits/knowledge-ops-skill-audit.md \
        github-actions/tests/test_feishu_collab_audit_registry.py
git commit -m "docs: add feishu collaboration skill audits"
```

## Task 4: Add Knowledge-Ops Pathing and Standard Templates

**Files:**
- Create: `docs/feishu-collab/templates/handoff-template.md`
- Create: `docs/feishu-collab/templates/runbook-template.md`
- Create: `github-actions/feishu_collab/knowledge_ops/pathing.py`
- Create: `github-actions/tests/test_feishu_collab_knowledge_pathing.py`

- [ ] **Step 1: Write the failing pathing test**

Create `github-actions/tests/test_feishu_collab_knowledge_pathing.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "knowledge_ops" / "pathing.py"
SPEC = importlib.util.spec_from_file_location("feishu_collab_knowledge_pathing", MODULE_PATH)
DOC_ROOT = ROOT / "docs" / "feishu-collab"


class FeishuCollabKnowledgePathingTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_operations_updates_route_to_runbooks_directory(self):
        module = self.load_module()
        target = module.resolve_knowledge_target("operations", "approval timeout")
        self.assertEqual(
            target,
            "docs/feishu-collab/runbooks/approval-timeout.md",
        )

    def test_delivery_updates_route_to_handoffs_directory(self):
        module = self.load_module()
        target = module.resolve_knowledge_target("delivery", "okr-driven checkpoint")
        self.assertEqual(
            target,
            "docs/feishu-collab/handoffs/okr-driven-checkpoint.md",
        )

    def test_templates_exist(self):
        self.assertTrue((DOC_ROOT / "templates" / "handoff-template.md").exists())
        self.assertTrue((DOC_ROOT / "templates" / "runbook-template.md").exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_knowledge_pathing.py -v
```

Expected: FAIL because the module and templates do not exist yet.

- [ ] **Step 3: Write the templates and minimal pathing helper**

Create `docs/feishu-collab/templates/handoff-template.md`:

```md
# Handoff Template

## Background
## Current State
## Completed Work
## Remaining Work
## Active Blocker
## Next Action
## Dependencies
## Risk Notes
## Evidence Links
## Handover Focus
```

Create `docs/feishu-collab/templates/runbook-template.md`:

```md
# Runbook Template

## Trigger
## Scope
## Preconditions
## Detection
## Investigation Steps
## Recovery Steps
## Verification
## Escalation
## Evidence To Capture
## Follow-up Knowledge Update
```

Create `github-actions/feishu_collab/knowledge_ops/pathing.py`:

```python
import re


def _slugify(title):
    slug = title.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def resolve_knowledge_target(asset_type, title):
    slug = _slugify(title)
    if asset_type == "operations":
        return f"docs/feishu-collab/runbooks/{slug}.md"
    if asset_type == "delivery":
        return f"docs/feishu-collab/handoffs/{slug}.md"
    if asset_type == "architecture":
        return f"docs/feishu-collab/governance/{slug}.md"
    if asset_type == "policy":
        return f"docs/feishu-collab/governance/{slug}.md"
    return f"docs/feishu-collab/registry/{slug}.md"
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_feishu_collab_knowledge_pathing.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add docs/feishu-collab/templates/handoff-template.md \
        docs/feishu-collab/templates/runbook-template.md \
        github-actions/feishu_collab/knowledge_ops/pathing.py \
        github-actions/tests/test_feishu_collab_knowledge_pathing.py
git commit -m "feat: add feishu collaboration knowledge ops routing"
```

## Task 5: Validate the Governance Baseline End-to-End

**Files:**
- Modify: `docs/feishu-collab/README.md`
- Modify: `docs/feishu-collab/SKILL_REGISTRY.md`
- Modify: `docs/feishu-collab/RUNBOOK_INDEX.md`
- Modify: `docs/feishu-collab/HANDOFF_INDEX.md`
- Modify: `docs/feishu-collab/governance/system-map.md`
- Modify: `docs/feishu-collab/registry/skill-audit-matrix.json`
- Modify: `github-actions/feishu_collab/shared/contracts.py`
- Modify: `github-actions/feishu_collab/knowledge_ops/pathing.py`

- [ ] **Step 1: Run the full targeted test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_feishu_collab_docs_structure.py \
  github-actions/tests/test_feishu_collab_contracts.py \
  github-actions/tests/test_feishu_collab_audit_registry.py \
  github-actions/tests/test_feishu_collab_knowledge_pathing.py -v
```

Expected: all tests PASS.

- [ ] **Step 2: Manually verify the governance surface**

Check:

- `docs/feishu-collab/README.md` clearly points to governance, registry, runbooks, handoffs, and audits
- `SKILL_REGISTRY.md` marks OKR-driven as implemented and the other four as audit-required
- `skill-audit-matrix.json` matches the markdown audits
- `system-map.md` states event-driven response as the default maintenance model
- `resolve_knowledge_target()` routes `operations` to `runbooks/` and `delivery` to `handoffs/`

Expected: no mismatch between docs, registry, and routing logic.

- [ ] **Step 3: Commit the validation pass**

```bash
git add docs/feishu-collab/README.md \
        docs/feishu-collab/SKILL_REGISTRY.md \
        docs/feishu-collab/RUNBOOK_INDEX.md \
        docs/feishu-collab/HANDOFF_INDEX.md \
        docs/feishu-collab/governance/system-map.md \
        docs/feishu-collab/registry/skill-audit-matrix.json \
        github-actions/feishu_collab/shared/contracts.py \
        github-actions/feishu_collab/knowledge_ops/pathing.py \
        github-actions/tests/test_feishu_collab_docs_structure.py \
        github-actions/tests/test_feishu_collab_contracts.py \
        github-actions/tests/test_feishu_collab_audit_registry.py \
        github-actions/tests/test_feishu_collab_knowledge_pathing.py
git commit -m "test: validate feishu collaboration governance baseline"
```

## Self-Review

- Spec coverage:
  - five core skill boundaries: Task 1 and Task 3
  - event-driven collaboration response: Task 1 and Task 2
  - unified file organization and call management: Task 1, Task 2, and Task 4
  - knowledge-ops model and maintenance routing: Task 3 and Task 4
  - system-maintenance collaboration response: Task 1, Task 4, and Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred implementation markers
  - Every code-bearing step includes concrete code or markdown content
  - Every verification step has exact commands and expected outcomes
- Type consistency:
  - Contract names match the approved spec: `ExecutionIntent`, `ExecutionPreview`, `ExecutionResult`, `KnowledgeUpdate`
  - Audit statuses use stable strings: `implemented-v1`, `audit-required`
  - Knowledge routing keeps `operations -> runbooks` and `delivery -> handoffs` consistent across docs and code
