# Approval SKILL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a preview-first `Approval SKILL` that evaluates risk, prepares and creates Feishu approval instances, polls and projects decision status back into collaboration records, then emits handoff and knowledge outputs after confirmation.

**Architecture:** Keep the skill package thin and move deterministic behavior into focused Python helpers under `github-actions/feishu_collab/approval/`. Reuse the existing gate logic from `github-actions/evaluate_risk_approval_gate.py`, harden the Feishu approval API wrapper so it matches the proven `open_id + json-string form` contract, and let the skill orchestrate preview, confirmation, create/reuse, poll, writeback, verification, escalation, and knowledge update.

**Tech Stack:** Markdown skill docs, Python 3, `unittest`, `json`, existing GitHub Actions workflows, shared Feishu-collaboration contracts

---

## Scope Check

This plan covers one coherent sub-project:

- Evaluate whether high-risk actions require approval
- Build preview objects that explain the gate decision, approval request, projected status, and timeout fallback
- Create or reuse Feishu approval instances and poll their status
- Project approval outcomes back into task/goal collaboration records
- Package the flow as `.trae/skills/feishu-collab-approval/SKILL.md`
- Verify that `ExecutionResult`, `KnowledgeUpdate`, and handoff outputs are produced after execution

It does **not** include:

- A general approval operations platform
- Webhook subscription infrastructure
- Approval dashboards or reporting UIs
- Rebuilding the existing acceptance workflow from scratch
- Knowledge-Ops implementation beyond emitting routable `KnowledgeUpdate`

## File Map

- Create: `.trae/skills/feishu-collab-approval/SKILL.md`
  - Main skill instructions, trigger conditions, preview-first approval flow, and governance guardrails.
- Create: `.trae/skills/feishu-collab-approval/references/execution-checklist.md`
  - Operator checklist for risk gate review, approval request verification, polling, writeback, and handoff.
- Create: `.trae/skills/feishu-collab-approval/references/escalation-policy.md`
  - Explicit escalation rules for parameter gaps, polling failures, timeout fallback, and evidence gaps.
- Create: `github-actions/feishu_collab/approval/__init__.py`
  - Package marker for Approval helpers.
- Create: `github-actions/feishu_collab/approval/build_approval_preview.py`
  - Compile risk context plus approval config into preview data with risk gate summary, approval request candidate, status projection candidate, and timeout policy.
- Create: `github-actions/tests/test_build_approval_preview.py`
  - Lock preview object shapes, risk flags, and confirmation requirements.
- Create: `github-actions/tests/fixtures/approval_skill/risk_context.json`
  - Stable risk-context fixture for preview and dry-run validation.
- Create: `github-actions/tests/fixtures/approval_skill/approval_context.json`
  - Stable approval-config fixture with code, applicant, timeout policy, and target references.
- Modify: `github-actions/feishu_approval_api.py`
  - Align request body semantics with the proven workflow contract: `open_id`, JSON-string `form`, and explicit projection helpers.
- Create: `github-actions/tests/test_feishu_approval_api_contract.py`
  - Lock the `open_id` and JSON-string `form` contract and preserve status projection behavior.
- Create: `github-actions/feishu_collab/approval/materialize_approval_execution.py`
  - Turn preview output into ordered approval create/reuse, status projection, escalation, `KnowledgeUpdate`, and handoff payloads.
- Create: `github-actions/tests/test_materialize_approval_execution.py`
  - Lock writeback order, failure modes, and handoff emission.
- Create: `github-actions/feishu_collab/approval/verify_approval_projection.py`
  - Re-check approval status, automation status, timeout fallback, and evidence presence after execution.
- Create: `github-actions/tests/test_verify_approval_projection.py`
  - Lock verification behavior for `hard_block`, `soft_block`, `degraded_success`, and `confirmed`.
- Modify: `github-actions/run_goal_progress_approval_cycle.py`
  - Keep existing behavior but expose a clear adapter path for `applicant_open_id` and hardened form serialization.
- Create: `github-actions/tests/test_run_goal_progress_approval_cycle_contract.py`
  - Lock the runtime contract between gate evaluation, approval API wrapper, and cycle orchestration.

## Execution Guardrails

- Keep v1 focused on `风险门控 + 发起 + 轮询`; do not add approval dashboards, webhooks, or notification buses.
- Reuse the existing risk gate semantics from `github-actions/evaluate_risk_approval_gate.py`; do not invent a second incompatible risk vocabulary.
- Reuse the existing status projection semantics from `github-actions/feishu_approval_api.py` and `github-actions/poll_feishu_approval_and_sync_base.py`.
- Treat missing `approval_code` or `applicant_open_id` as explicit `hard_block`; never silently skip approval.
- Preserve the proven workflow contract: `open_id` must be used for the applicant and `form` must be sent as a JSON string.
- Emit `KnowledgeUpdate` and handoff payloads whenever execution reaches verification, including degraded outcomes.

## Task 1: Add the Approval Preview Compiler

**Files:**
- Create: `github-actions/feishu_collab/approval/__init__.py`
- Create: `github-actions/feishu_collab/approval/build_approval_preview.py`
- Create: `github-actions/tests/test_build_approval_preview.py`
- Create: `github-actions/tests/fixtures/approval_skill/risk_context.json`
- Create: `github-actions/tests/fixtures/approval_skill/approval_context.json`

- [ ] **Step 1: Write the failing preview tests**

Create `github-actions/tests/test_build_approval_preview.py`:

```python
import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "approval" / "build_approval_preview.py"
SPEC = importlib.util.spec_from_file_location("build_approval_preview", MODULE_PATH)
FIXTURE_DIR = ROOT / "github-actions" / "tests" / "fixtures" / "approval_skill"


class BuildApprovalPreviewTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def load_fixture(self, name):
        return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))

    def test_preview_builds_gate_summary_request_candidate_and_timeout_policy(self):
        module = self.load_module()
        preview = module.build_approval_preview(
            risk_context=self.load_fixture("risk_context.json"),
            approval_context=self.load_fixture("approval_context.json"),
        )
        self.assertEqual(preview["risk_gate_summary"]["requires_approval"], True)
        self.assertEqual(preview["risk_gate_summary"]["trigger_reason"], "high_risk_scope:release_handoff")
        self.assertEqual(preview["approval_request_candidate"]["approval_code"], "APPROVAL-001")
        self.assertEqual(preview["approval_request_candidate"]["applicant_open_id"], "ou_demo_applicant")
        self.assertEqual(preview["timeout_policy"]["action"], "pause")
        self.assertEqual(preview["requires_confirmation"], True)

    def test_preview_marks_missing_approval_code_as_risk(self):
        module = self.load_module()
        context = self.load_fixture("approval_context.json")
        context["approval_code"] = ""
        preview = module.build_approval_preview(
            risk_context=self.load_fixture("risk_context.json"),
            approval_context=context,
        )
        self.assertIn("missing_approval_code", preview["risk_flags"])

    def test_preview_marks_missing_applicant_open_id_as_risk(self):
        module = self.load_module()
        context = self.load_fixture("approval_context.json")
        context["applicant_open_id"] = ""
        preview = module.build_approval_preview(
            risk_context=self.load_fixture("risk_context.json"),
            approval_context=context,
        )
        self.assertIn("missing_applicant_open_id", preview["risk_flags"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add stable risk and approval fixtures**

Create `github-actions/tests/fixtures/approval_skill/risk_context.json`:

```json
{
  "task_id": "task-approval-001",
  "goal_id": "goal-collab-approval-001",
  "risk_level": "high",
  "task_scope": "release_handoff",
  "trigger_reason": "high_risk_scope:release_handoff",
  "owner": "governance-agent",
  "recommended_option": "human_review",
  "timeout_fallback": {
    "action": "pause",
    "is_safe": false,
    "decision_summary": "waiting_for_manual_decision"
  }
}
```

Create `github-actions/tests/fixtures/approval_skill/approval_context.json`:

```json
{
  "approval_code": "APPROVAL-001",
  "applicant_open_id": "ou_demo_applicant",
  "instance_external_id": "task-approval-001",
  "form_payload": [
    {
      "id": "decision_id",
      "type": "textarea",
      "value": "task-approval-001"
    },
    {
      "id": "trigger_reason",
      "type": "textarea",
      "value": "high_risk_scope:release_handoff"
    }
  ],
  "source_refs": [
    "task-approval-001",
    "goal-collab-approval-001"
  ],
  "target_object_id": "task-approval-001"
}
```

- [ ] **Step 3: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_approval_preview.py -v
```

Expected: FAIL because `build_approval_preview.py` does not exist yet.

- [ ] **Step 4: Write the minimal preview compiler**

Create `github-actions/feishu_collab/approval/__init__.py`:

```python
"""Approval helpers for the Feishu collaboration system."""
```

Create `github-actions/feishu_collab/approval/build_approval_preview.py`:

```python
import json
import sys


def build_approval_preview(risk_context, approval_context):
    risk_flags = []
    if not approval_context.get("approval_code"):
        risk_flags.append("missing_approval_code")
    if not approval_context.get("applicant_open_id"):
        risk_flags.append("missing_applicant_open_id")

    return {
        "risk_gate_summary": {
            "risk_level": risk_context.get("risk_level", ""),
            "trigger_reason": risk_context.get("trigger_reason", ""),
            "risk_scope": risk_context.get("task_scope", ""),
            "recommended_action": risk_context.get("recommended_option", ""),
            "requires_approval": risk_context.get("risk_level") == "high",
        },
        "approval_request_candidate": {
            "approval_code": approval_context.get("approval_code", ""),
            "applicant_open_id": approval_context.get("applicant_open_id", ""),
            "instance_external_id": approval_context.get("instance_external_id", ""),
            "form_payload": approval_context.get("form_payload", []),
            "source_refs": approval_context.get("source_refs", []),
            "target_object_id": approval_context.get("target_object_id", ""),
        },
        "status_projection_candidate": {
            "approval_status": "pending",
            "approval_decision_id": risk_context.get("task_id", ""),
            "decision_summary": "approval_created",
            "automation_status": "paused",
        },
        "risk_flags": risk_flags,
        "timeout_policy": risk_context.get("timeout_fallback", {}),
        "requires_confirmation": True,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_approval_preview(payload["risk_context"], payload["approval_context"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
```

- [ ] **Step 5: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_approval_preview.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 6: Commit**

```bash
git add github-actions/feishu_collab/approval/__init__.py \
        github-actions/feishu_collab/approval/build_approval_preview.py \
        github-actions/tests/test_build_approval_preview.py \
        github-actions/tests/fixtures/approval_skill/risk_context.json \
        github-actions/tests/fixtures/approval_skill/approval_context.json
git commit -m "feat: add approval preview compiler"
```

## Task 2: Harden the Feishu Approval API Contract

**Files:**
- Modify: `github-actions/feishu_approval_api.py`
- Create: `github-actions/tests/test_feishu_approval_api_contract.py`
- Modify: `github-actions/run_goal_progress_approval_cycle.py`
- Create: `github-actions/tests/test_run_goal_progress_approval_cycle_contract.py`

- [ ] **Step 1: Write the failing API contract tests**

Create `github-actions/tests/test_feishu_approval_api_contract.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_approval_api.py"
SPEC = importlib.util.spec_from_file_location("feishu_approval_api", MODULE_PATH)


class FeishuApprovalApiContractTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_create_instance_body_uses_open_id_and_json_string_form(self):
        module = self.load_module()
        body = module.build_create_instance_body(
            approval_code="APPROVAL-001",
            applicant_open_id="ou_demo_applicant",
            instance_external_id="task-approval-001",
            form=[{"id": "decision_id", "type": "textarea", "value": "task-approval-001"}],
        )
        self.assertEqual(body["approval_code"], "APPROVAL-001")
        self.assertEqual(body["open_id"], "ou_demo_applicant")
        self.assertIsInstance(body["form"], str)
        self.assertNotIn("user_id", body)

    def test_build_status_projection_keeps_instance_code(self):
        module = self.load_module()
        projection = module.build_status_projection(
            instance={"status": "APPROVED"},
            decision_id="task-approval-001",
            instance_code="instance-001",
        )
        self.assertEqual(projection["approval_status"], "approved")
        self.assertEqual(projection["approval_instance_code"], "instance-001")


if __name__ == "__main__":
    unittest.main()
```

Create `github-actions/tests/test_run_goal_progress_approval_cycle_contract.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "run_goal_progress_approval_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_goal_progress_approval_cycle", MODULE_PATH)


class RunGoalProgressApprovalCycleContractTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_build_approval_form_returns_serializable_field_list(self):
        module = self.load_module()
        result = module.build_approval_form(
            task_payload={"task_id": "task-approval-001"},
            gate_result={"trigger_reason": "high_risk_scope:release_handoff"},
        )
        self.assertEqual(result[0]["value"], "task-approval-001")
        self.assertEqual(result[1]["value"], "high_risk_scope:release_handoff")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_feishu_approval_api_contract.py \
  github-actions/tests/test_run_goal_progress_approval_cycle_contract.py -v
```

Expected: FAIL because the API wrapper still uses `user_id` and passes raw `form`.

- [ ] **Step 3: Write the minimal contract fix**

Modify `github-actions/feishu_approval_api.py`:

```python
import json
import urllib.request


APPROVAL_BASE_URL = "https://open.feishu.cn/open-apis/approval/v4"


def build_create_instance_body(approval_code, applicant_open_id, instance_external_id, form):
    return {
        "approval_code": approval_code,
        "open_id": applicant_open_id,
        "instance_external_id": instance_external_id,
        "form": json.dumps(form, ensure_ascii=False),
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


def build_status_projection(instance, decision_id, instance_code):
    resolved = resolve_instance_status(instance, decision_id)
    resolved["approval_instance_code"] = instance_code
    return resolved
```

Modify `github-actions/run_goal_progress_approval_cycle.py`:

```python
approval_body = APPROVAL_API.build_create_instance_body(
    approval_code=approval_code,
    applicant_open_id=applicant_user_id,
    instance_external_id=task_payload.get("task_id", ""),
    form=build_approval_form(task_payload, gate_result),
)
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_feishu_approval_api_contract.py \
  github-actions/tests/test_run_goal_progress_approval_cycle_contract.py \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_run_goal_progress_approval_cycle.py -v
```

Expected: PASS with all approval API and cycle contract tests green.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_approval_api.py \
        github-actions/run_goal_progress_approval_cycle.py \
        github-actions/tests/test_feishu_approval_api_contract.py \
        github-actions/tests/test_run_goal_progress_approval_cycle_contract.py
git commit -m "feat: harden approval api contract"
```

## Task 3: Add the Approval Execution Materializer

**Files:**
- Create: `github-actions/feishu_collab/approval/materialize_approval_execution.py`
- Create: `github-actions/tests/test_materialize_approval_execution.py`

- [ ] **Step 1: Write the failing materialization tests**

Create `github-actions/tests/test_materialize_approval_execution.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "approval" / "materialize_approval_execution.py"
SPEC = importlib.util.spec_from_file_location("materialize_approval_execution", MODULE_PATH)


class MaterializeApprovalExecutionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def sample_preview(self):
        return {
            "risk_gate_summary": {
                "risk_level": "high",
                "trigger_reason": "high_risk_scope:release_handoff",
                "risk_scope": "release_handoff",
                "recommended_action": "human_review",
                "requires_approval": True
            },
            "approval_request_candidate": {
                "approval_code": "APPROVAL-001",
                "applicant_open_id": "ou_demo_applicant",
                "instance_external_id": "task-approval-001",
                "form_payload": [{"id": "decision_id", "type": "textarea", "value": "task-approval-001"}],
                "source_refs": ["task-approval-001"],
                "target_object_id": "task-approval-001"
            },
            "status_projection_candidate": {
                "approval_status": "pending",
                "approval_decision_id": "task-approval-001",
                "decision_summary": "approval_created",
                "automation_status": "paused"
            },
            "risk_flags": [],
            "timeout_policy": {
                "action": "pause",
                "is_safe": false,
                "decision_summary": "waiting_for_manual_decision"
            },
            "requires_confirmation": True
        }

    def test_materialize_builds_writeback_order_handoff_and_knowledge(self):
        module = self.load_module()
        result = module.materialize_approval_execution(self.sample_preview())
        self.assertEqual(
            result["writeback_order"],
            [
                "risk_gate_check",
                "approval_request_writeback",
                "approval_status_projection",
                "automation_status_projection",
                "approval_evidence_snapshot",
            ],
        )
        self.assertEqual(result["status"], "confirmed")
        self.assertEqual(result["knowledge_update"]["asset_type"], "operations")
        self.assertEqual(result["handoff"]["type"], "stage_handoff")

    def test_materialize_marks_hard_block_when_approval_code_missing(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["missing_approval_code"]
        result = module.materialize_approval_execution(preview)
        self.assertEqual(result["status"], "hard_block")

    def test_materialize_marks_soft_block_when_instance_lookup_failed(self):
        module = self.load_module()
        preview = self.sample_preview()
        preview["risk_flags"] = ["instance_lookup_failed"]
        result = module.materialize_approval_execution(preview)
        self.assertEqual(result["status"], "soft_block")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_approval_execution.py -v
```

Expected: FAIL because `materialize_approval_execution.py` does not exist yet.

- [ ] **Step 3: Write the minimal materializer**

Create `github-actions/feishu_collab/approval/materialize_approval_execution.py`:

```python
import json
import sys


WRITEBACK_ORDER = [
    "risk_gate_check",
    "approval_request_writeback",
    "approval_status_projection",
    "automation_status_projection",
    "approval_evidence_snapshot",
]


def materialize_approval_execution(preview):
    status = "confirmed"
    risk_flags = preview.get("risk_flags", [])
    if "missing_approval_code" in risk_flags or "missing_applicant_open_id" in risk_flags:
        status = "hard_block"
    elif "instance_lookup_failed" in risk_flags or "approval_scope_conflict" in risk_flags:
        status = "soft_block"

    evidence_refs = [
        preview["approval_request_candidate"].get("instance_external_id", ""),
        preview["approval_request_candidate"].get("approval_code", ""),
    ]

    return {
        "status": status,
        "writeback_order": WRITEBACK_ORDER,
        "approval_request": preview["approval_request_candidate"],
        "status_projection": preview["status_projection_candidate"],
        "timeout_policy": preview["timeout_policy"],
        "knowledge_update": {
            "asset_type": "operations",
            "title": "approval-execution-result",
            "summary": f"status={status}",
            "evidence_refs": [item for item in evidence_refs if item],
        },
        "handoff": {
            "type": "stage_handoff",
            "status": status,
            "summary": f"approval execution {status}",
            "next_action": "review approval verification result",
            "evidence_refs": [item for item in evidence_refs if item],
        },
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(materialize_approval_execution(payload), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
python3 -m unittest github-actions/tests/test_materialize_approval_execution.py -v
```

Expected: PASS with `Ran 3 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/approval/materialize_approval_execution.py \
        github-actions/tests/test_materialize_approval_execution.py
git commit -m "feat: add approval execution materializer"
```

## Task 4: Add Verification and Failure-Mode Handling

**Files:**
- Create: `github-actions/feishu_collab/approval/verify_approval_projection.py`
- Create: `github-actions/tests/test_verify_approval_projection.py`

- [ ] **Step 1: Write the failing verification tests**

Create `github-actions/tests/test_verify_approval_projection.py`:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "feishu_collab" / "approval" / "verify_approval_projection.py"
SPEC = importlib.util.spec_from_file_location("verify_approval_projection", MODULE_PATH)


class VerifyApprovalProjectionTests(unittest.TestCase):
    def load_module(self):
        module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(module)
        return module

    def test_verify_returns_confirmed_when_projection_and_evidence_are_complete(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={"approval_status": "approved", "automation_status": "running", "decision_summary": "approved:task-1"},
            timeout_policy={"action": "pause"},
            evidence_snapshot={"instance_code": "instance-001", "decision_summary": "approved:task-1"},
            risk_flags=[],
        )
        self.assertEqual(result["status"], "confirmed")

    def test_verify_returns_hard_block_when_status_projection_is_missing(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={},
            timeout_policy={"action": "pause"},
            evidence_snapshot={"instance_code": "instance-001", "decision_summary": "approved:task-1"},
            risk_flags=[],
        )
        self.assertEqual(result["status"], "hard_block")

    def test_verify_returns_soft_block_when_projection_gap_is_present(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={"approval_status": "pending", "automation_status": "paused", "decision_summary": "pending:task-1"},
            timeout_policy={"action": "pause"},
            evidence_snapshot={"instance_code": "instance-001", "decision_summary": "pending:task-1"},
            risk_flags=["status_projection_gap"],
        )
        self.assertEqual(result["status"], "soft_block")

    def test_verify_returns_degraded_success_when_evidence_is_missing(self):
        module = self.load_module()
        result = module.verify_approval_projection(
            status_projection={"approval_status": "approved", "automation_status": "running", "decision_summary": "approved:task-1"},
            timeout_policy={"action": "pause"},
            evidence_snapshot={},
            risk_flags=[],
        )
        self.assertEqual(result["status"], "degraded_success")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_verify_approval_projection.py -v
```

Expected: FAIL because `verify_approval_projection.py` does not exist yet.

- [ ] **Step 3: Write the minimal verification helper**

Create `github-actions/feishu_collab/approval/verify_approval_projection.py`:

```python
import json
import sys


def verify_approval_projection(status_projection, timeout_policy, evidence_snapshot, risk_flags):
    if not status_projection.get("approval_status"):
        status = "hard_block"
    elif "status_projection_gap" in risk_flags:
        status = "soft_block"
    elif not evidence_snapshot.get("instance_code"):
        status = "degraded_success"
    else:
        status = "confirmed"

    return {
        "status": status,
        "approval_status": status_projection.get("approval_status", ""),
        "automation_status": status_projection.get("automation_status", ""),
        "timeout_action": timeout_policy.get("action", ""),
        "instance_code_present": bool(evidence_snapshot.get("instance_code")),
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        verify_approval_projection(
            payload["status_projection"],
            payload["timeout_policy"],
            payload["evidence_snapshot"],
            payload["risk_flags"],
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
python3 -m unittest github-actions/tests/test_verify_approval_projection.py -v
```

Expected: PASS with `Ran 4 tests ... OK`.

- [ ] **Step 5: Commit**

```bash
git add github-actions/feishu_collab/approval/verify_approval_projection.py \
        github-actions/tests/test_verify_approval_projection.py
git commit -m "feat: add approval verification helper"
```

## Task 5: Package the Skill and Validate the Baseline

**Files:**
- Create: `.trae/skills/feishu-collab-approval/SKILL.md`
- Create: `.trae/skills/feishu-collab-approval/references/execution-checklist.md`
- Create: `.trae/skills/feishu-collab-approval/references/escalation-policy.md`
- Modify: `github-actions/feishu_approval_api.py`
- Modify: `github-actions/run_goal_progress_approval_cycle.py`
- Modify: `github-actions/feishu_collab/approval/build_approval_preview.py`
- Modify: `github-actions/feishu_collab/approval/materialize_approval_execution.py`
- Modify: `github-actions/feishu_collab/approval/verify_approval_projection.py`

- [ ] **Step 1: Write the skill package files**

Create `.trae/skills/feishu-collab-approval/SKILL.md`:

```md
---
name: "feishu-collab-approval"
description: "Evaluates high-risk actions, creates or reuses Feishu approval instances, polls decision status, and writes the result back into collaboration state after confirmation."
---

# Feishu Collaboration Approval

## When to use

Use this skill when:

- a high-risk action needs governance review before execution continues
- the user needs approval preview-before-create
- the workflow must create or reuse a Feishu approval instance
- the flow must poll decision status and project it back into collaboration records

## Inputs

- risk context
- approval config
- optional existing approval instance code
- optional sibling task / goal context

## Flow

1. evaluate risk gate
2. build preview
3. confirm approval creation or reuse
4. create or poll approval instance
5. project status and automation outcome
6. generate handoff and `KnowledgeUpdate`

## Guardrails

- never skip preview
- treat missing approval code as hard block
- treat missing applicant open_id as hard block
- treat polling failures as soft block
- treat missing evidence snapshot as degraded success
- do not expand into approval dashboards in v1
```

Create `.trae/skills/feishu-collab-approval/references/execution-checklist.md`:

```md
# Execution Checklist

## Gate Review

- Confirm the action is high risk
- Confirm the trigger reason is explicit
- Confirm the timeout policy is visible

## Approval Request Gate

- Confirm `approval_code` is present
- Confirm `applicant_open_id` is present
- Confirm `form` is serialized as JSON string before submit
- Confirm instance external ID maps to the target task

## Polling Gate

- Confirm existing instance is reused when available
- Confirm approval status is mapped to collaboration state
- Confirm automation status is updated consistently

## Verification Gate

- Confirm approval status projection exists
- Confirm evidence snapshot exists
- Confirm handoff and `KnowledgeUpdate` are emitted
```

Create `.trae/skills/feishu-collab-approval/references/escalation-policy.md`:

```md
# Escalation Policy

## Hard Block

- Missing `approval_code`
- Missing `applicant_open_id`
- Missing target task or goal record

## Soft Block

- Approval instance lookup failed
- Status projection gap detected
- Timeout policy conflict detected

## Degraded Success

- Approval result written back but evidence snapshot missing
- Approval result written back but handoff evidence incomplete

## Fallback

- `pause` when unsafe to continue
- `conservative_continue` only when explicitly marked safe
```

- [ ] **Step 2: Sanity-check the skill files**

Run:

```bash
python3 -c 'from pathlib import Path
for path in [
    Path(".trae/skills/feishu-collab-approval/SKILL.md"),
    Path(".trae/skills/feishu-collab-approval/references/execution-checklist.md"),
    Path(".trae/skills/feishu-collab-approval/references/escalation-policy.md"),
]:
    text = path.read_text(encoding="utf-8")
    assert text.strip(), f"{path} is empty"
print("approval skill files ok")'
```

Expected: `approval skill files ok`

- [ ] **Step 3: Run the full targeted test suite**

Run:

```bash
python3 -m unittest \
  github-actions/tests/test_build_approval_preview.py \
  github-actions/tests/test_feishu_approval_api_contract.py \
  github-actions/tests/test_run_goal_progress_approval_cycle_contract.py \
  github-actions/tests/test_materialize_approval_execution.py \
  github-actions/tests/test_verify_approval_projection.py \
  github-actions/tests/test_feishu_approval_api.py \
  github-actions/tests/test_run_goal_progress_approval_cycle.py \
  github-actions/tests/test_poll_feishu_approval_and_sync_base.py \
  github-actions/tests/test_collab_workflows_present.py -v
```

Expected: all approval-related tests PASS.

- [ ] **Step 4: Perform a local dry-run using the fixtures**

Run:

```bash
python3 - <<'PY'
import json
import subprocess
from pathlib import Path

root = Path("/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT")
fixture_dir = root / "github-actions" / "tests" / "fixtures" / "approval_skill"
payload = {
    "risk_context": json.loads((fixture_dir / "risk_context.json").read_text(encoding="utf-8")),
    "approval_context": json.loads((fixture_dir / "approval_context.json").read_text(encoding="utf-8")),
}

preview_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "approval" / "build_approval_preview.py")],
    input=json.dumps(payload, ensure_ascii=False),
    text=True,
)
preview = json.loads(preview_out)

execution_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "approval" / "materialize_approval_execution.py")],
    input=json.dumps(preview, ensure_ascii=False),
    text=True,
)
execution = json.loads(execution_out)

verification_out = subprocess.check_output(
    ["python3", str(root / "github-actions" / "feishu_collab" / "approval" / "verify_approval_projection.py")],
    input=json.dumps(
        {
            "status_projection": execution["status_projection"],
            "timeout_policy": execution["timeout_policy"],
            "evidence_snapshot": {
                "instance_code": execution["approval_request"].get("instance_external_id", ""),
                "decision_summary": execution["status_projection"].get("decision_summary", "")
            },
            "risk_flags": preview["risk_flags"],
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

- preview contains risk gate summary, approval request candidate, risk flags, and timeout policy
- execution contains ordered writeback steps, handoff, and `KnowledgeUpdate`
- verification returns `confirmed`

- [ ] **Step 5: Commit**

```bash
git add .trae/skills/feishu-collab-approval/SKILL.md \
        .trae/skills/feishu-collab-approval/references/execution-checklist.md \
        .trae/skills/feishu-collab-approval/references/escalation-policy.md \
        github-actions/feishu_approval_api.py \
        github-actions/run_goal_progress_approval_cycle.py \
        github-actions/feishu_collab/approval/__init__.py \
        github-actions/feishu_collab/approval/build_approval_preview.py \
        github-actions/feishu_collab/approval/materialize_approval_execution.py \
        github-actions/feishu_collab/approval/verify_approval_projection.py \
        github-actions/tests/test_build_approval_preview.py \
        github-actions/tests/test_feishu_approval_api_contract.py \
        github-actions/tests/test_run_goal_progress_approval_cycle_contract.py \
        github-actions/tests/test_materialize_approval_execution.py \
        github-actions/tests/test_verify_approval_projection.py \
        github-actions/tests/fixtures/approval_skill/risk_context.json \
        github-actions/tests/fixtures/approval_skill/approval_context.json
git commit -m "test: validate approval skill baseline"
```

## Self-Review

- Spec coverage:
  - v1 scope `风险门控 + 发起 + 轮询`: Task 1, Task 2, and Task 3
  - preview-first flow and timeout-policy explainability: Task 1 and Task 3
  - `open_id` / `form` contract hardening: Task 2
  - writeback, verification, escalation, handoff, and knowledge output: Task 3, Task 4, and Task 5
  - skill packaging and operator guidance: Task 5
- Placeholder scan:
  - No `TODO`, `TBD`, or deferred implementation markers
  - Every code-bearing step includes concrete code or markdown content
  - Every verification step has exact commands and expected outcomes
- Type consistency:
  - Preview/result names stay aligned with the shared system baseline: `ExecutionPreview`, `ExecutionResult`, `KnowledgeUpdate`
  - Approval model names stay aligned with the approved spec: `RiskGateSpec`, `ApprovalRequestSpec`, `ApprovalStatusProjection`, `EscalationSpec`, `ApprovalEvidenceSpec`
  - Failure statuses stay aligned across preview, materialization, and verification: `hard_block`, `soft_block`, `degraded_success`, `confirmed`
