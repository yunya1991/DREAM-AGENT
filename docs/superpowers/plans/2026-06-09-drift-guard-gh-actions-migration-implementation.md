# Drift Guard + Controlled Dispatch (GitHub Actions) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate “推进主线的自动化执行” from local scheduled sessions to GitHub Actions, using a reusable, module-based Drift Guard that blocks drift and gates any controlled workflow triggers.

**Architecture:** Implement a deterministic Drift Guard as a reusable composite action hosted in `DREAM-AGENT`, configured per repo via `.workbuddy/drift-guard.yml`, and enforced via branch protection + required checks. Controlled triggers run only after Drift Guard passes.

**Tech Stack:** GitHub Actions (self-hosted runner), Python 3 stdlib (unittest), Git + gh CLI (already used), YAML config.

---

## Scope

**Repos**
- `yunya1991/DREAM-AGENT` (module center)
- `yunya1991/Dreambuddy-V2` (mainline repo)

**Default allowed mainline modules in Dreambuddy-V2**
- `7-产物中台/**`
- `6-TRADING/**`
- `3-FRONTEND/dream-universal-gateway/**`

**Non-goals**
- No LLM-based judging.
- No direct code modifications by scheduled sessions; all changes via PR.

---

## File Structure (What to Create / Modify)

**DREAM-AGENT**
- Create: `.github/actions/drift-guard/action.yml`
- Create: `.github/actions/drift-guard/drift_guard.py`
- Create: `.github/actions/drift-guard/format_report_md.py`
- Create: `.github/workflows/drift-guard.yml`
- Create: `.github/workflows/controlled-dispatch.yml`
- Create: `.workbuddy/drift-guard.yml`
- Create: `github-actions/tests/test_drift_guard_config.py`
- Create: `docs/feishu-collab/runbooks/drift-guard.md`

**Dreambuddy-V2**
- Create: `.github/workflows/drift-guard.yml`
- Create: `.github/workflows/controlled-dispatch.yml` (optional; can be centralized in DREAM-AGENT if desired)
- Create: `.workbuddy/drift-guard.yml`
- Modify: `docs/superpowers/plans/` index doc if you maintain one (optional)

---

### Task 1: Implement reusable Drift Guard composite action (DREAM-AGENT)

**Files:**
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/actions/drift-guard/action.yml`
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/actions/drift-guard/drift_guard.py`
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/actions/drift-guard/format_report_md.py`
- Test: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/github-actions/tests/test_drift_guard_config.py`

**Behavior contract**
- Inputs:
  - `mode`: `pull_request` | `schedule` | `manual`
  - `change_class`: `mainline` | `integration` | `infra` (string)
  - `config_path`: default `.workbuddy/drift-guard.yml`
  - `base_sha` / `head_sha`: required for PR mode
- Outputs:
  - `verdict`: `PASS` | `BLOCK`
  - `reason_codes`: JSON array string
  - `report_json_path`: path to JSON report in workspace
  - `report_md_path`: path to MD report in workspace
- Fail-closed:
  - Any parse error, missing config, missing required docs, unknown changed file path mapping → `BLOCK` (non-zero exit code).

- [ ] **Step 1: Write failing config parser test (unittest)**

```python
import unittest
from pathlib import Path
import yaml


class DriftGuardConfigTests(unittest.TestCase):
    def test_config_has_change_classes_and_modules(self):
        text = """
modules:
  product_hub:
    paths:
      - "7-产物中台/**"
change_classes:
  mainline:
    allowed_modules: ["product_hub"]
required_docs:
  - "docs/superpowers/plans/2026-05-17-agent-standard-dev-lifecycle-implementation-plan.md"
"""
        cfg = yaml.safe_load(text)
        self.assertIn("modules", cfg)
        self.assertIn("change_classes", cfg)
        self.assertIn("required_docs", cfg)
        self.assertIn("product_hub", cfg["modules"])
        self.assertIn("mainline", cfg["change_classes"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test to verify it fails (before code exists)**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_drift_guard_config -v
```

Expected: FAIL due to missing dependency (`yaml`) or missing file, which drives the next step.

- [ ] **Step 3: Decide YAML strategy (stdlib-only fallback)**

Because stdlib does not include YAML, implement a strict subset parser:
- Prefer JSON config first: allow `.workbuddy/drift-guard.json` as primary.
- Support YAML only if runner already has PyYAML installed; otherwise block with a clear reason code `CONFIG_YAML_UNSUPPORTED`.

Implement this by:
- Attempt `json.loads` first when file ends with `.json`.
- If `.yml/.yaml`, try importing `yaml`; if import fails, `BLOCK`.

- [ ] **Step 4: Implement `drift_guard.py` (minimal CLI)**

```python
import argparse
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DriftVerdict:
    verdict: str
    reason_codes: List[str]
    report: Dict[str, Any]


def _run(cmd: List[str]) -> str:
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out.decode("utf-8", errors="replace").strip()


def _load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(str(path))
    if path.suffix.lower() == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    if path.suffix.lower() in (".yml", ".yaml"):
        try:
            import yaml  # type: ignore
        except Exception as exc:
            raise RuntimeError("CONFIG_YAML_UNSUPPORTED") from exc
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    raise RuntimeError("CONFIG_UNSUPPORTED_FORMAT")


def _match_module(modules: Dict[str, Any], file_path: str) -> Optional[str]:
    for name, cfg in modules.items():
        for pattern in cfg.get("paths", []):
            if _git_pathspec_match(pattern, file_path):
                return name
    return None


def _git_pathspec_match(pattern: str, file_path: str) -> bool:
    try:
        subprocess.check_output(
            ["git", "pathspec", "match", pattern, file_path],
            stderr=subprocess.DEVNULL,
        )
        return True
    except Exception:
        return False


def _diff_files(base_sha: str, head_sha: str) -> List[str]:
    out = _run(["git", "diff", "--name-only", f"{base_sha}..{head_sha}"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def _hash_file(path: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def evaluate(
    repo_root: Path,
    config_path: Path,
    change_class: str,
    base_sha: Optional[str],
    head_sha: Optional[str],
) -> DriftVerdict:
    cfg = _load_config(config_path)
    modules = cfg.get("modules", {})
    change_classes = cfg.get("change_classes", {})
    required_docs = cfg.get("required_docs", [])

    reason_codes: List[str] = []
    report: Dict[str, Any] = {
        "repo_root": str(repo_root),
        "change_class": change_class,
        "required_docs": required_docs,
        "docs_hashes": {},
        "changed_files": [],
        "changed_files_by_module": {},
        "reason_codes": [],
    }

    if change_class not in change_classes:
        reason_codes.append("UNKNOWN_CHANGE_CLASS")
    allowed_modules = set(change_classes.get(change_class, {}).get("allowed_modules", []))

    for rel in required_docs:
        p = repo_root / rel
        if not p.exists():
            reason_codes.append("REQUIRED_DOC_MISSING")
            report["docs_hashes"][rel] = None
        else:
            report["docs_hashes"][rel] = _hash_file(p)

    changed_files: List[str] = []
    if base_sha and head_sha:
        changed_files = _diff_files(base_sha, head_sha)
    report["changed_files"] = changed_files

    by_module: Dict[str, List[str]] = {}
    unknown: List[str] = []
    for f in changed_files:
        module = _match_module(modules, f)
        if module is None:
            unknown.append(f)
            continue
        by_module.setdefault(module, []).append(f)
        if allowed_modules and module not in allowed_modules:
            reason_codes.append("PATH_OUT_OF_SCOPE")

    if unknown:
        reason_codes.append("UNKNOWN_PATH")
        by_module["__unknown__"] = unknown

    report["changed_files_by_module"] = by_module
    report["reason_codes"] = sorted(set(reason_codes))

    verdict = "PASS" if not report["reason_codes"] else "BLOCK"
    return DriftVerdict(verdict=verdict, reason_codes=report["reason_codes"], report=report)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--change-class", required=True)
    parser.add_argument("--base-sha")
    parser.add_argument("--head-sha")
    parser.add_argument("--report-json", required=True)
    parser.add_argument("--report-md", required=True)
    args = parser.parse_args()

    repo_root = Path.cwd()
    verdict = evaluate(
        repo_root=repo_root,
        config_path=repo_root / args.config,
        change_class=args.change_class,
        base_sha=args.base_sha,
        head_sha=args.head_sha,
    )

    Path(args.report_json).write_text(json.dumps(verdict.report, ensure_ascii=False, indent=2), encoding="utf-8")

    from format_report_md import format_report_md

    Path(args.report_md).write_text(format_report_md(verdict.report), encoding="utf-8")

    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"verdict={verdict.verdict}\n")
            f.write(f"reason_codes={json.dumps(verdict.reason_codes, ensure_ascii=False)}\n")
            f.write(f"report_json_path={args.report_json}\n")
            f.write(f"report_md_path={args.report_md}\n")

    return 0 if verdict.verdict == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Implement deterministic markdown formatter**

```python
import json
from typing import Any, Dict


def format_report_md(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("# Drift Guard Report")
    lines.append("")
    lines.append(f"- Change Class: {report.get('change_class')}")
    lines.append(f"- Verdict: {'PASS' if not report.get('reason_codes') else 'BLOCK'}")
    lines.append(f"- Reason Codes: {', '.join(report.get('reason_codes') or []) or 'NONE'}")
    lines.append("")
    lines.append("## Changed Files By Module")
    lines.append("")
    by_module = report.get("changed_files_by_module") or {}
    for module, files in by_module.items():
        lines.append(f"### {module}")
        for f in files:
            lines.append(f"- {f}")
        lines.append("")
    lines.append("## Required Docs (sha256)")
    lines.append("")
    docs = report.get("docs_hashes") or {}
    for p, h in docs.items():
        lines.append(f"- {p}: {h}")
    lines.append("")
    lines.append("## Raw JSON")
    lines.append("")
    lines.append("```json")
    lines.append(json.dumps(report, ensure_ascii=False, indent=2))
    lines.append("```")
    lines.append("")
    return "\n".join(lines)
```

- [ ] **Step 6: Create composite action definition**

```yaml
name: "workbuddy drift guard"
description: "Deterministic drift guard (path scope + required docs + report artifacts)"
inputs:
  mode:
    description: "pull_request|schedule|manual"
    required: true
  change_class:
    description: "mainline|integration|infra"
    required: true
  config_path:
    description: "Config file path"
    required: false
    default: ".workbuddy/drift-guard.yml"
  base_sha:
    description: "Base SHA for diff"
    required: false
  head_sha:
    description: "Head SHA for diff"
    required: false
  report_json:
    description: "Report JSON output path"
    required: false
    default: "drift_report.json"
  report_md:
    description: "Report MD output path"
    required: false
    default: "drift_report.md"
outputs:
  verdict:
    description: "PASS|BLOCK"
  reason_codes:
    description: "JSON array string"
  report_json_path:
    description: "Path to JSON report"
  report_md_path:
    description: "Path to markdown report"
runs:
  using: "composite"
  steps:
    - name: Run drift guard
      shell: bash
      run: |
        set -e
        python3 "${{ github.action_path }}/drift_guard.py" \
          --config "${{ inputs.config_path }}" \
          --change-class "${{ inputs.change_class }}" \
          --base-sha "${{ inputs.base_sha }}" \
          --head-sha "${{ inputs.head_sha }}" \
          --report-json "${{ inputs.report_json }}" \
          --report-md "${{ inputs.report_md }}"
```

- [ ] **Step 7: Run tests**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_collab_workflows_present -v
python3 -m unittest github-actions.tests.test_drift_guard_config -v
```

Expected: PASS. If YAML parser dependency is missing, adjust the test to use JSON config for baseline and add one negative test for YAML without PyYAML.

- [ ] **Step 8: Commit (DREAM-AGENT)**

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
git add .github/actions/drift-guard .github/workflows github-actions/tests docs/feishu-collab/runbooks/drift-guard.md .workbuddy/drift-guard.yml
git commit -m "feat(drift-guard): add deterministic drift guard composite action"
git push
```

---

### Task 2: Add per-repo drift guard configuration (both repos)

**Files:**
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.workbuddy/drift-guard.yml`
- Create: `/Users/zhangjiangtao/WorkBuddy/dreambuddy-v2/.workbuddy/drift-guard.yml`

- [ ] **Step 1: Create Dreambuddy-V2 config (YAML)**

```yaml
modules:
  product_hub:
    paths:
      - "7-产物中台/**"
  trading:
    paths:
      - "6-TRADING/**"
  frontend_gateway:
    paths:
      - "3-FRONTEND/dream-universal-gateway/**"
  ci:
    paths:
      - ".github/**"
      - "docs/**"
      - ".workbuddy/**"

change_classes:
  mainline:
    allowed_modules: ["product_hub", "ci"]
  integration:
    allowed_modules: ["product_hub", "trading", "frontend_gateway", "ci"]
  infra:
    allowed_modules: ["ci"]

required_docs:
  - "docs/superpowers/plans/2026-05-17-agent-standard-dev-lifecycle-implementation-plan.md"
  - "1-ARCHITECTURE/中台设计/PRODUCT_HUB.md"
```

- [ ] **Step 2: Create DREAM-AGENT config (YAML)**

```yaml
modules:
  workflows:
    paths:
      - ".github/workflows/**"
  scripts:
    paths:
      - "github-actions/**"
  docs:
    paths:
      - "docs/**"
  config:
    paths:
      - ".workbuddy/**"

change_classes:
  mainline:
    allowed_modules: ["workflows", "scripts", "docs", "config"]
  infra:
    allowed_modules: ["workflows", "scripts", "docs", "config"]

required_docs:
  - "docs/03-WORKFLOWS-AND-NORMS.md"
  - "docs/self-hosted-runner.md"
  - "docs/01-COLLABORATION-PROTOCOL.md"
```

- [ ] **Step 3: Commit configs**

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
git add .workbuddy/drift-guard.yml
git commit -m "chore(drift-guard): add repo drift guard config"
git push

cd /Users/zhangjiangtao/WorkBuddy/dreambuddy-v2
git add .workbuddy/drift-guard.yml
git commit -m "chore(drift-guard): add repo drift guard config"
git push
```

---

### Task 3: Wire Drift Guard into GitHub Actions checks (both repos)

**Files:**
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/workflows/drift-guard.yml`
- Create: `/Users/zhangjiangtao/WorkBuddy/dreambuddy-v2/.github/workflows/drift-guard.yml`

- [ ] **Step 1: Add Dreambuddy-V2 drift-guard workflow**

```yaml
name: drift-guard

on:
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      change_class:
        required: true
        type: choice
        options: [mainline, integration, infra]
        default: mainline
  schedule:
    - cron: "10 */4 * * *"

permissions:
  contents: read
  pull-requests: write

concurrency:
  group: drift-guard-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true

jobs:
  guard:
    runs-on: [self-hosted, macOS, workbuddy]
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Ensure clean workspace
        shell: bash
        run: |
          set -e
          git reset --hard
          git clean -fdx

      - name: Run drift guard
        id: drift
        uses: yunya1991/DREAM-AGENT/.github/actions/drift-guard@main
        with:
          mode: ${{ github.event_name }}
          change_class: ${{ inputs.change_class || 'mainline' }}
          config_path: .workbuddy/drift-guard.yml
          base_sha: ${{ github.event.pull_request.base.sha }}
          head_sha: ${{ github.event.pull_request.head.sha }}
          report_json: drift_report.json
          report_md: drift_report.md

      - name: Upload drift report
        uses: actions/upload-artifact@v4
        with:
          name: drift-guard-report
          path: |
            drift_report.json
            drift_report.md

      - name: Comment on PR (BLOCK)
        if: ${{ github.event_name == 'pull_request' && failure() }}
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh pr comment ${{ github.event.pull_request.number }} --body-file drift_report.md
```

- [ ] **Step 2: Add DREAM-AGENT drift-guard workflow (self-check)**

Use the same structure but `uses: ./.github/actions/drift-guard` (local path), and keep schedule enabled.

- [ ] **Step 3: Verify in a test PR that the check appears**

Expected: PR checks show `drift-guard` with PASS/BLOCK based on file scope + required docs.

---

### Task 4: Add Controlled Dispatch (trigger existing workflows only when Drift Guard passes)

**Files:**
- Create: `/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/.github/workflows/controlled-dispatch.yml`
- Create (optional): `/Users/zhangjiangtao/WorkBuddy/dreambuddy-v2/.github/workflows/controlled-dispatch.yml`

- [ ] **Step 1: Implement controlled dispatch in DREAM-AGENT**

```yaml
name: controlled-dispatch

on:
  workflow_dispatch:
    inputs:
      change_class:
        required: true
        type: choice
        options: [mainline, integration, infra]
        default: mainline
      trigger_target:
        required: true
        type: choice
        options:
          - real-approval-trigger
          - knowledge-materialization
          - approval-polling-writeback
        default: knowledge-materialization

permissions:
  contents: read
  actions: write

jobs:
  gate:
    runs-on: [self-hosted, macOS, workbuddy]
    outputs:
      verdict: ${{ steps.drift.outputs.verdict }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Ensure clean workspace
        shell: bash
        run: |
          set -e
          git reset --hard
          git clean -fdx
      - name: Run drift guard (manual gate)
        id: drift
        uses: ./.github/actions/drift-guard
        with:
          mode: manual
          change_class: ${{ inputs.change_class }}
          config_path: .workbuddy/drift-guard.yml
          report_json: drift_report.json
          report_md: drift_report.md
      - uses: actions/upload-artifact@v4
        with:
          name: drift-guard-report
          path: |
            drift_report.json
            drift_report.md

  dispatch:
    needs: gate
    if: ${{ needs.gate.outputs.verdict == 'PASS' }}
    runs-on: ubuntu-latest
    steps:
      - name: Trigger workflow
        uses: actions/github-script@v7
        with:
          script: |
            const mapping = {
              "real-approval-trigger": "real-approval-trigger.yml",
              "knowledge-materialization": "knowledge-materialization.yml",
              "approval-polling-writeback": "approval-polling-writeback.yml",
            }
            const workflow_id = mapping["${{ inputs.trigger_target }}"]
            await github.rest.actions.createWorkflowDispatch({
              owner: context.repo.owner,
              repo: context.repo.repo,
              workflow_id,
              ref: "main",
              inputs: {}
            })
```

- [ ] **Step 2: (Optional) Add a Dreambuddy-V2 controlled-dispatch that triggers DREAM-AGENT workflows via repository_dispatch**

Only do this if you want Dreambuddy-V2 to be the single entry button. Otherwise keep dispatch centralized in DREAM-AGENT.

---

### Task 5: Enforce “No direct push to main” via branch protection (both repos)

**Goal:** Require PR + required checks (at least `drift-guard`) before merging to `main`.

- [ ] **Step 1: Confirm drift-guard check name**

Create a trivial PR and confirm the check name shown in GitHub UI is `drift-guard`.

- [ ] **Step 2: Apply branch protection via GitHub UI (fastest, least error-prone)**

For each repo:
- Protect `main`
- Require a pull request before merging
- Require status checks to pass before merging:
  - `drift-guard`
- (Optional) Require code review approval
- Restrict who can push to matching branches (disable direct pushes)

- [ ] **Step 3: (Optional) Apply branch protection via gh api**

Run (replace `<OWNER>` / `<REPO>`):

```bash
gh api -X PUT repos/<OWNER>/<REPO>/branches/main/protection \
  -f required_status_checks.strict=true \
  -F required_status_checks.contexts[]="drift-guard" \
  -f enforce_admins=true \
  -f required_pull_request_reviews.dismiss_stale_reviews=true \
  -f required_pull_request_reviews.required_approving_review_count=1 \
  -f restrictions=null
```

Expected: 200 response JSON describing protection settings.

---

### Task 6: Migrate away from local scheduled sessions (TRAE schedules)

**Goal:** Stop local scheduled sessions from pushing code or creating untracked work-in-progress; GitHub Actions becomes the single source of automation truth.

- [ ] **Step 1: Pause local scheduled tasks that can mutate repos**

Pause at least:
- `Dream-Agent Hybrid Dispatch Executor` (currently active)
- Any local developer/governance/validator scheduled sessions that push commits

- [ ] **Step 2: Keep only read-only local schedules if needed**

If you still want local read-only monitoring, keep it but enforce:
- no git write
- no file write
- only report output

---

### Task 7: Verification checklist (end-to-end)

- [ ] **Step 1: Dreambuddy-V2 PR out-of-scope file should BLOCK**

Create a PR that changes `2-GOVERNANCE/README.md` and confirm:
- `drift-guard` fails
- report lists `UNKNOWN_PATH` or `PATH_OUT_OF_SCOPE`

- [ ] **Step 2: Dreambuddy-V2 integration PR touching 7-产物中台 + 6-TRADING + 3-FRONTEND gateway should PASS with change_class=integration**

Confirm:
- changed files are categorized into 3 modules
- `drift-guard` passes

- [ ] **Step 3: Controlled dispatch should not trigger when drift guard blocks**

Run `controlled-dispatch` with a deliberately broken required doc and confirm:
- `dispatch` job is skipped

- [ ] **Step 4: Branch protection blocks direct push**

Attempt direct push to `main` and confirm GitHub rejects it (or requires bypass permission).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-09-drift-guard-gh-actions-migration-implementation.md`.

Two execution options:
1) **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks
2) **Inline Execution** — execute tasks in this session with checkpoints

Which approach?
