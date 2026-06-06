# Acceptance Request Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `DREAM-AGENT` so the existing collaboration protocol supports `ACCEPTANCE_REQUEST -> VALIDATION_RESULT -> next-work precheck` as a first-class acceptance flow.

**Architecture:** Keep `DREAM-AGENT` as the protocol hub and do not move business execution into this repository. Add one new PR comment template, extend the existing validation result template, introduce a focused acceptance-checker script with unit tests, and add one dedicated workflow for acceptance comments so the old `DONE` validator path remains stable.

**Tech Stack:** Markdown templates, GitHub Actions workflow YAML, Python 3 unittest-based protocol checks under `github-actions/tests`, existing `gh`-driven PR comment flow

---

## File Structure

### New Files

- `docs/agent-acceptance-request-protocol-implementation-plan.md`
  - This implementation plan.
- `templates/pr-comment-acceptance-request.md`
  - Canonical PR comment template for `[验收委托 / ACCEPTANCE_REQUEST]`.
- `github-actions/check_acceptance_request.py`
  - Pure parser/evaluator for acceptance-request comments and acceptance-mode validation result generation.
- `github-actions/tests/test_check_acceptance_request.py`
  - Unit tests for required fields, missing-section failure, and output recommendation behavior.
- `.github/workflows/collab-acceptance-agent.yml`
  - Dedicated workflow for `ACCEPTANCE_REQUEST` comments and manual dispatch.

### Modified Files

- `templates/pr-comment-validation-result.md`
  - Extend the current template with acceptance-mode fields while keeping the old hard-gate fields.
- `docs/01-COLLABORATION-PROTOCOL.md`
  - Add `ACCEPTANCE_REQUEST` as a canonical anchor and define its required fields.
- `docs/03-WORKFLOWS-AND-NORMS.md`
  - Add the acceptance flow and the next-work precheck rule.
- `github-actions/tests/test_collab_workflows_present.py`
  - Assert that the new acceptance workflow exists.

## Task 1: Add The ACCEPTANCE_REQUEST Template

**Files:**
- Create: `templates/pr-comment-acceptance-request.md`
- Test: `github-actions/tests/test_check_acceptance_request.py`

- [ ] **Step 1: Write the failing template test**

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AcceptanceRequestTemplateTests(unittest.TestCase):
    def test_acceptance_request_template_exists_and_declares_required_sections(self):
        template = ROOT / "templates" / "pr-comment-acceptance-request.md"
        self.assertTrue(template.exists(), str(template))
        text = template.read_text(encoding="utf-8")
        self.assertIn("[验收委托 / ACCEPTANCE_REQUEST]", text)
        self.assertIn("Acceptance Request ID:", text)
        self.assertIn("## 验收对象", text)
        self.assertIn("## 验收范围", text)
        self.assertIn("## 业务上下文映射", text)
        self.assertIn("## 重点验收项", text)
        self.assertIn("## 本轮不要求", text)
        self.assertIn("## 期望回写格式", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request.AcceptanceRequestTemplateTests -v
```

Expected: FAIL because `templates/pr-comment-acceptance-request.md` does not yet exist.

- [ ] **Step 3: Write the minimal template**

```md
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: <ar-YYYYMMDD-001>
Request Type: <feature | phase-gate | pilot>
Request Mode: <manual | auto>
Source of Truth: PR comment
Target PR: <#123>

## 验收对象
- <what is being accepted now>

## 验收范围
- <scope item 1>
- <scope item 2>

## 业务上下文映射
- 架构图基线: <url or none>
- 前端承接基线: <url or none>
- 本轮说明: <why this acceptance exists now>

## 重点验收项
- <focus item 1>
- <focus item 2>

## 本轮不要求
- <out-of-scope item 1>

## 期望回写格式
- 验收对象
- 协议读取结论
- 结构化程度结论
- 是否可作为唯一真源
- 当前阻塞项
- 下一步建议
- 最终结论：<试点通过 | 试点部分通过 | 试点不通过 | ACCEPTED | REWORK | BLOCK>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request.AcceptanceRequestTemplateTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/pr-comment-acceptance-request.md github-actions/tests/test_check_acceptance_request.py
git commit -m "docs: add acceptance request comment template"
```

## Task 2: Extend VALIDATION_RESULT For Acceptance Mode

**Files:**
- Modify: `templates/pr-comment-validation-result.md`
- Test: `github-actions/tests/test_check_acceptance_request.py`

- [ ] **Step 1: Write the failing validation-template test**

```python
class ValidationResultTemplateTests(unittest.TestCase):
    def test_validation_result_template_supports_acceptance_mode_fields(self):
        template = ROOT / "templates" / "pr-comment-validation-result.md"
        text = template.read_text(encoding="utf-8")
        self.assertIn("Validation Mode:", text)
        self.assertIn("Acceptance Request ID:", text)
        self.assertIn("Protocol Read Result:", text)
        self.assertIn("Source of Truth Verdict:", text)
        self.assertIn("Must-Fix Items:", text)
        self.assertIn("Next Step Recommendation:", text)
        self.assertIn("Acceptance Conclusion:", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request.ValidationResultTemplateTests -v
```

Expected: FAIL because the current template only contains hard-gate fields.

- [ ] **Step 3: Extend the template minimally**

```md
[验证结论 / VALIDATION_RESULT]

Validator: <validator agent>
Validation Mode: <delivery | acceptance>
Acceptance Request ID: <request id | none>
Hard Gate Result: <PASS | BLOCK>
Score: <0-100>
Decision: <ACCEPTED | REWORK | BLOCK>
Protocol Read Result: <PASS | PARTIAL | FAIL>
Source of Truth Verdict: <usable | ambiguous | invalid>
Reason Codes:
- <code>
Must-Fix Items:
- <item or none>
Next Step Recommendation: <next action>
Acceptance Conclusion: <trial_pass | trial_partial | trial_fail | accepted | rework | blocked>
Reward Multiplier: <value>
Ledger Update: <task pointer or none>
Governance Handoff: <ledgered | archived | knowledge_synced | pending>
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request.ValidationResultTemplateTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add templates/pr-comment-validation-result.md github-actions/tests/test_check_acceptance_request.py
git commit -m "docs: extend validation result template for acceptance"
```

## Task 3: Add The Acceptance Comment Checker

**Files:**
- Create: `github-actions/check_acceptance_request.py`
- Create: `github-actions/tests/test_check_acceptance_request.py`

- [ ] **Step 1: Write the failing parser tests**

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = Path(__file__).resolve().parents[1] / "check_acceptance_request.py"
SPEC = importlib.util.spec_from_file_location("check_acceptance_request", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


VALID_COMMENT = """
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-001
Request Type: pilot
Request Mode: manual
Source of Truth: PR comment
Target PR: #4

## 验收对象
- PR comment driven acceptance pilot

## 验收范围
- comment structure

## 业务上下文映射
- 架构图基线: http://127.0.0.1:62932/ui-map-independent-hub-architecture.html
- 前端承接基线: http://localhost:3000/dashboard

## 重点验收项
- source of truth clarity

## 本轮不要求
- no business code changes

## 期望回写格式
- 验收对象
- 最终结论
""".strip()


class AcceptanceRequestParserTests(unittest.TestCase):
    def test_acceptance_request_passes_when_required_fields_and_sections_exist(self):
        result = MODULE.evaluate_acceptance_request(VALID_COMMENT)
        self.assertEqual(result["decision"], "ACCEPTED")
        self.assertEqual(result["protocol_read_result"], "PASS")
        self.assertEqual(result["source_of_truth_verdict"], "usable")

    def test_acceptance_request_returns_rework_when_required_section_is_missing(self):
        broken = VALID_COMMENT.replace("## 重点验收项\\n- source of truth clarity\\n\\n", "")
        result = MODULE.evaluate_acceptance_request(broken)
        self.assertEqual(result["decision"], "REWORK")
        self.assertIn("RULE_ACCEPTANCE_SECTION_MISSING", result["reason_codes"])

    def test_acceptance_request_returns_block_when_anchor_is_missing(self):
        broken = VALID_COMMENT.replace("[验收委托 / ACCEPTANCE_REQUEST]", "[别的评论]")
        result = MODULE.evaluate_acceptance_request(broken)
        self.assertEqual(result["decision"], "BLOCK")
        self.assertIn("RULE_ACCEPTANCE_ANCHOR_MISSING", result["reason_codes"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request.AcceptanceRequestParserTests -v
```

Expected: FAIL because `github-actions/check_acceptance_request.py` does not exist.

- [ ] **Step 3: Write the minimal parser/evaluator**

```python
import re


REQUIRED_FIELDS = [
    "Acceptance Request ID:",
    "Request Type:",
    "Request Mode:",
    "Source of Truth:",
    "Target PR:",
]

REQUIRED_SECTIONS = [
    "## 验收对象",
    "## 验收范围",
    "## 业务上下文映射",
    "## 重点验收项",
    "## 本轮不要求",
    "## 期望回写格式",
]


def evaluate_acceptance_request(comment_body: str) -> dict:
    if "[验收委托 / ACCEPTANCE_REQUEST]" not in comment_body:
        return {
            "decision": "BLOCK",
            "protocol_read_result": "FAIL",
            "source_of_truth_verdict": "invalid",
            "reason_codes": ["RULE_ACCEPTANCE_ANCHOR_MISSING"],
            "recommended_next_action": "author: post a valid ACCEPTANCE_REQUEST comment",
        }

    missing_fields = [field for field in REQUIRED_FIELDS if field not in comment_body]
    missing_sections = [section for section in REQUIRED_SECTIONS if section not in comment_body]

    if missing_fields or missing_sections:
        return {
            "decision": "REWORK",
            "protocol_read_result": "PARTIAL",
            "source_of_truth_verdict": "ambiguous",
            "reason_codes": [
                *["RULE_ACCEPTANCE_FIELD_MISSING" for _ in missing_fields],
                *["RULE_ACCEPTANCE_SECTION_MISSING" for _ in missing_sections],
            ],
            "recommended_next_action": "author: complete the missing ACCEPTANCE_REQUEST fields and sections",
        }

    match = re.search(r"Acceptance Request ID:\\s*(.+)", comment_body)
    request_id = match.group(1).strip() if match else "none"

    return {
        "decision": "ACCEPTED",
        "protocol_read_result": "PASS",
        "source_of_truth_verdict": "usable",
        "reason_codes": ["NONE"],
        "recommended_next_action": "validator: post VALIDATION_RESULT",
        "acceptance_request_id": request_id,
    }
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add github-actions/check_acceptance_request.py github-actions/tests/test_check_acceptance_request.py
git commit -m "feat: add acceptance request protocol checker"
```

## Task 4: Add The Acceptance Workflow

**Files:**
- Create: `.github/workflows/collab-acceptance-agent.yml`
- Modify: `github-actions/tests/test_collab_workflows_present.py`

- [ ] **Step 1: Write the failing workflow-presence test**

```python
class AcceptanceWorkflowPresenceTests(unittest.TestCase):
    def test_acceptance_workflow_exists(self):
        workflow = REPO_ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        self.assertTrue(workflow.exists(), str(workflow))
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_collab_workflows_present -v
```

Expected: FAIL because the workflow file does not yet exist.

- [ ] **Step 3: Write the minimal workflow**

```yaml
name: collab-acceptance-agent

on:
  workflow_dispatch:
    inputs:
      pr_number:
        description: "Target PR number"
        required: true
        type: string
      acceptance_request_id:
        description: "Acceptance Request ID"
        required: false
        default: ""
        type: string
  issue_comment:
    types: [created]

permissions:
  contents: read
  issues: write
  pull-requests: write

jobs:
  acceptance:
    runs-on: [self-hosted, macOS, workbuddy]
    if: >
      github.event_name == 'workflow_dispatch' ||
      (
        github.event_name == 'issue_comment' &&
        github.event.issue.pull_request != null &&
        contains(github.event.comment.body, '[验收委托 / ACCEPTANCE_REQUEST]')
      )
    steps:
      - name: Checkout main
        uses: actions/checkout@v4
        with:
          ref: main

      - name: Resolve comment body
        id: payload
        env:
          COMMENT_BODY: ${{ github.event.comment.body }}
        run: |
          python3 github-actions/check_acceptance_request.py <<'PYEOF'
          PYEOF

      - name: Evaluate acceptance request
        id: evaluate
        env:
          COMMENT_BODY: ${{ github.event.comment.body }}
        run: |
          python3 - <<'PY'
          import json
          import os
          import pathlib
          import importlib.util

          root = pathlib.Path.cwd()
          module_path = root / "github-actions" / "check_acceptance_request.py"
          spec = importlib.util.spec_from_file_location("check_acceptance_request", module_path)
          module = importlib.util.module_from_spec(spec)
          spec.loader.exec_module(module)
          result = module.evaluate_acceptance_request(os.environ.get("COMMENT_BODY", ""))
          with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
              fh.write(f"decision={result['decision']}\\n")
              fh.write(f"protocol_read_result={result['protocol_read_result']}\\n")
              fh.write(f"source_of_truth_verdict={result['source_of_truth_verdict']}\\n")
              fh.write(f"recommended_next_action={result['recommended_next_action']}\\n")
              fh.write(f"acceptance_request_id={result.get('acceptance_request_id', 'none')}\\n")
              fh.write(f"reason_codes={','.join(result['reason_codes'])}\\n")
          PY

      - name: Post VALIDATION_RESULT comment
        env:
          GH_TOKEN: ${{ github.token }}
          PR_NUMBER: ${{ github.event.issue.number || inputs.pr_number }}
        run: |
          {
            printf '%s\n' \
              '[验证结论 / VALIDATION_RESULT]' \
              '' \
              'Validator: collab-acceptance-agent' \
              'Validation Mode: acceptance' \
              "Acceptance Request ID: ${{ steps.evaluate.outputs.acceptance_request_id }}" \
              "Hard Gate Result: ${{ steps.evaluate.outputs.decision == 'BLOCK' && 'BLOCK' || 'PASS' }}" \
              'Score: 90' \
              "Decision: ${{ steps.evaluate.outputs.decision }}" \
              "Protocol Read Result: ${{ steps.evaluate.outputs.protocol_read_result }}" \
              "Source of Truth Verdict: ${{ steps.evaluate.outputs.source_of_truth_verdict }}" \
              'Reason Codes:' \
              "- ${{ steps.evaluate.outputs.reason_codes }}" \
              'Must-Fix Items:' \
              '- none' \
              "Next Step Recommendation: ${{ steps.evaluate.outputs.recommended_next_action }}" \
              "Acceptance Conclusion: ${{ steps.evaluate.outputs.decision == 'ACCEPTED' && 'trial_pass' || steps.evaluate.outputs.decision == 'REWORK' && 'trial_partial' || 'trial_fail' }}" \
              'Reward Multiplier: 1.0' \
              'Ledger Update: none' \
              'Governance Handoff: pending'
          } > pr_acceptance_result.md
          gh pr comment "${PR_NUMBER}" --body-file pr_acceptance_result.md
```

- [ ] **Step 4: Run the workflow-presence test**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_collab_workflows_present -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/collab-acceptance-agent.yml github-actions/tests/test_collab_workflows_present.py
git commit -m "feat: add acceptance request workflow"
```

## Task 5: Update Protocol Docs And Precheck Rule

**Files:**
- Modify: `docs/01-COLLABORATION-PROTOCOL.md`
- Modify: `docs/03-WORKFLOWS-AND-NORMS.md`

- [ ] **Step 1: Write the failing documentation assertions**

```python
class AcceptanceProtocolDocsTests(unittest.TestCase):
    def test_collaboration_protocol_mentions_acceptance_request_anchor(self):
        text = (ROOT / "docs" / "01-COLLABORATION-PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn("[验收委托 / ACCEPTANCE_REQUEST]", text)
        self.assertIn("DONE != ACCEPTED", text)

    def test_workflow_norms_mentions_precheck_rule(self):
        text = (ROOT / "docs" / "03-WORKFLOWS-AND-NORMS.md").read_text(encoding="utf-8")
        self.assertIn("先读取最近一次 `VALIDATION_RESULT`", text)
        self.assertIn("ACCEPTANCE_REQUEST", text)
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request.AcceptanceProtocolDocsTests -v
```

Expected: FAIL because the current docs do not yet define the new anchor and precheck rule.

- [ ] **Step 3: Update the protocol docs minimally**

```md
<!-- docs/01-COLLABORATION-PROTOCOL.md excerpt -->
- `[验收委托 / ACCEPTANCE_REQUEST]`

### 2.x ACCEPTANCE_REQUEST

- `Acceptance Request ID`
- `Request Type`
- `Request Mode`
- `Source of Truth`
- `Target PR`
- `验收对象`
- `验收范围`
- `业务上下文映射`
- `重点验收项`
- `本轮不要求`
- `期望回写格式`

Notes:
- `DONE != ACCEPTED`
- `DONE` is delivery completion, `VALIDATION_RESULT` is acceptance conclusion.
```

```md
<!-- docs/03-WORKFLOWS-AND-NORMS.md excerpt -->
12. If a task needs acceptance, post `ACCEPTANCE_REQUEST` after the delivery package is ready.
13. Before continuing the next round of work, 先读取最近一次 `VALIDATION_RESULT`.
14. If `REWORK`, `BLOCK`, or `Must-Fix Items` exist, fix them before continuing mainline work.
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request.AcceptanceProtocolDocsTests -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/01-COLLABORATION-PROTOCOL.md docs/03-WORKFLOWS-AND-NORMS.md github-actions/tests/test_check_acceptance_request.py
git commit -m "docs: define acceptance request protocol flow"
```

## Task 6: Final Verification

**Files:**
- Verify only

- [ ] **Step 1: Run the full targeted test suite**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest \
  github-actions.tests.test_check_acceptance_request \
  github-actions.tests.test_collab_workflows_present \
  github-actions.tests.test_check_agent_collaboration -v
```

Expected: PASS.

- [ ] **Step 2: Run a manual protocol smoke check**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 - <<'PY'
import importlib.util
from pathlib import Path

root = Path.cwd()
module_path = root / "github-actions" / "check_acceptance_request.py"
spec = importlib.util.spec_from_file_location("check_acceptance_request", module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

comment = """
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-001
Request Type: pilot
Request Mode: manual
Source of Truth: PR comment
Target PR: #4

## 验收对象
- protocol pilot

## 验收范围
- comment parsing

## 业务上下文映射
- 架构图基线: http://127.0.0.1:62932/ui-map-independent-hub-architecture.html
- 前端承接基线: http://localhost:3000/dashboard

## 重点验收项
- unique source-of-truth parsing

## 本轮不要求
- no business execution

## 期望回写格式
- 验收对象
- 最终结论
""".strip()

result = module.evaluate_acceptance_request(comment)
assert result["decision"] == "ACCEPTED", result
print("acceptance protocol smoke ok")
PY
```

Expected:

```text
acceptance protocol smoke ok
```

- [ ] **Step 3: Commit the verification-complete state**

```bash
git add .
git commit -m "test: verify acceptance request protocol flow"
```

## Self-Review

- Spec coverage:
  - `ACCEPTANCE_REQUEST` template: Task 1
  - `VALIDATION_RESULT` extension: Task 2
  - dedicated acceptance workflow: Task 4
  - protocol doc updates: Task 5
  - next-work precheck rule: Task 5
  - v1 remains protocol-only, not business-execution heavy: Tasks 3-4
- Placeholder scan:
  - No `TODO`/`TBD` placeholders remain.
  - Each task contains concrete file paths, commands, and example code.
- Type consistency:
  - `Acceptance Request ID`, `Validation Mode`, `Protocol Read Result`, and `Source of Truth Verdict` are used consistently across template, checker, workflow, and docs.

Plan complete and saved to `docs/agent-acceptance-request-protocol-implementation-plan.md`. Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?
