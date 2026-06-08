# Central Hub OKR Binding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bind the live goal `goal-trading-hub-connectivity-20260519` to a real Feishu Objective with four KR entries, then write the resulting OKR anchors back into the live `目标推进表` record so the boss view changes from `待补OKR` to `已对齐`.

**Architecture:** Keep Feishu OKR as the source of truth for the new Objective/KR structure, and treat the live Base record as the projection layer. Reuse the existing goal payload builder only for fields already under code control; perform the OKR binding and Base anchor writeback as explicit, auditable user-owned online operations.

**Tech Stack:** Python 3, `unittest`, `lark-cli base +record-*`, live Feishu Base, browser-assisted Feishu OKR creation when API/CLI coverage is unavailable

---

## Scope Check

This plan only covers `子项目 A`:

- Create the real Objective and four KR entries
- Bind the existing Base goal record to that Objective
- Update the OKR anchor fields in `目标推进表`

It does **not** include:

- `OKR-driven SKILL`
- dashboard work
- ledger-to-Base bulk sync

## File Map

- Create: `github-actions/build_central_hub_okr_binding_payload.py`
  - Produce the exact Base writeback payload for the live goal after an Objective is created.
- Create: `github-actions/tests/test_build_central_hub_okr_binding_payload.py`
  - Lock the binding payload contract so Base writeback remains deterministic.
- Modify online Feishu Base record:
  - Base `SjCHbDasHarEcFsJjXwc5JZgnUr`
  - Table `tblYwbyMwnO8j8iG`
  - Record `goal-trading-hub-connectivity-20260519` / `recvlSRHGZIC6N`
- Create online Feishu OKR objects:
  - 1 Objective
  - 4 KR entries

## Execution Guardrails

- Ignore the unrelated deletion `.github/workflows/feishu-approval-smoke.yml`; never restore or stage it.
- Ignore `.superpowers/` files created during brainstorming.
- Prefer `--as user` for every live Feishu operation.
- If Feishu OKR has no stable CLI/API route in the current environment, browser-assisted creation is acceptable, but every created identifier must be written down before Base is updated.
- Do not update the Base record to `已对齐` until the real Objective exists and its identifier is captured.

## Task 1: Add a Deterministic OKR Binding Payload Builder

**Files:**
- Create: `github-actions/build_central_hub_okr_binding_payload.py`
- Create: `github-actions/tests/test_build_central_hub_okr_binding_payload.py`

- [ ] **Step 1: Write the failing tests for the OKR binding payload**

Create `github-actions/tests/test_build_central_hub_okr_binding_payload.py` with:

```python
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "github-actions" / "build_central_hub_okr_binding_payload.py"
SPEC = importlib.util.spec_from_file_location("build_central_hub_okr_binding_payload", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)


class BuildCentralHubOkrBindingPayloadTests(unittest.TestCase):
    def test_build_binding_payload_marks_goal_aligned(self):
        SPEC.loader.exec_module(MODULE)
        payload = MODULE.build_binding_payload(
            {
                "goal_id": "goal-trading-hub-connectivity-20260519",
                "goal_name": "中台与前端联动验证能力打通",
            },
            {
                "objective_id": "obj-central-hub-001",
                "objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
                "objective_owner": "governance-agent",
            },
        )
        self.assertEqual(payload["OKR对齐"], "已对齐")
        self.assertEqual(payload["okr_objective_id"], "obj-central-hub-001")
        self.assertEqual(payload["okr_objective_title"], "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制")
        self.assertEqual(payload["okr_owner"], "governance-agent")
        self.assertEqual(payload["okr_sync_status"], "bound")

    def test_build_binding_payload_emits_summary_for_four_krs(self):
        SPEC.loader.exec_module(MODULE)
        payload = MODULE.build_binding_payload(
            {
                "goal_id": "goal-trading-hub-connectivity-20260519",
                "goal_name": "中台与前端联动验证能力打通",
            },
            {
                "objective_id": "obj-central-hub-001",
                "objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
                "objective_owner": "governance-agent",
                "krs": [
                    "KR1: Hub 到 Trading 的实时桥接能力可运行",
                    "KR2: 前端关键页面完成实时联动验证",
                    "KR3: 审批、目标推进、workflow 提醒与老板视图形成运行闭环",
                    "KR4: 架构图、spec、实施计划中的核心功能项被拆解进持续推进机制并可跟踪",
                ],
            },
        )
        self.assertIn("KR1", payload["最近决策摘要"])
        self.assertIn("KR4", payload["最近决策摘要"])
```

- [ ] **Step 2: Run the test file and verify it fails**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_central_hub_okr_binding_payload.py -v
```

Expected: FAIL because the module does not exist yet.

- [ ] **Step 3: Write the minimal payload builder**

Create `github-actions/build_central_hub_okr_binding_payload.py` with:

```python
import json
import sys
from datetime import datetime, timezone


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_binding_payload(goal, objective):
    kr_summary = "；".join(objective.get("krs", []))
    decision_summary = (
        f"objective_bound:{objective['objective_id']}"
        + (f"；{kr_summary}" if kr_summary else "")
    )
    return {
        "goal_id": goal["goal_id"],
        "目标名称": goal["goal_name"],
        "OKR对齐": "已对齐",
        "okr_objective_id": objective["objective_id"],
        "okr_objective_title": objective["objective_title"],
        "okr_owner": objective["objective_owner"],
        "okr_sync_status": "bound",
        "okr_last_sync_at": now_iso(),
        "最近决策摘要": decision_summary,
    }


if __name__ == "__main__":
    payload = json.load(sys.stdin)
    json.dump(
        build_binding_payload(payload["goal"], payload["objective"]),
        sys.stdout,
        ensure_ascii=False,
        indent=2,
    )
    sys.stdout.write("\n")
```

- [ ] **Step 4: Run the tests and verify they pass**

Run:

```bash
python3 -m unittest github-actions/tests/test_build_central_hub_okr_binding_payload.py -v
```

Expected: `Ran 2 tests ... OK`

- [ ] **Step 5: Commit**

```bash
git add github-actions/build_central_hub_okr_binding_payload.py \
        github-actions/tests/test_build_central_hub_okr_binding_payload.py
git commit -m "feat: add central hub okr binding payload builder"
```

## Task 2: Prepare the Exact Objective and KR Content

**Files:**
- Create: `/tmp/central-hub-okr-draft.json`

- [ ] **Step 1: Write the Objective and KR draft to a local JSON file**

Run:

```bash
python3 - <<'PY'
import json

draft = {
    "objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
    "objective_owner": "governance-agent",
    "krs": [
        "KR1: Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路",
        "KR2: 前端关键页面完成实时联动验证，能直接反映交易链路状态变化",
        "KR3: 审批、目标推进、workflow 提醒与老板视图形成运行闭环",
        "KR4: 架构图、spec、实施计划中的核心功能项被拆解进持续推进机制并可跟踪",
    ],
}

with open("/tmp/central-hub-okr-draft.json", "w", encoding="utf-8") as fh:
    json.dump(draft, fh, ensure_ascii=False, indent=2)
PY
```

Expected: `/tmp/central-hub-okr-draft.json` exists and contains the final Objective/KR wording.

- [ ] **Step 2: Verify the draft file content**

Run:

```bash
python3 -m json.tool /tmp/central-hub-okr-draft.json
```

Expected: the printed JSON contains 1 objective title and 4 KR strings matching the spec.

## Task 3: Create the Real Objective and Four KRs in Feishu OKR

**Files:**
- Live Feishu OKR workspace
- Local note file: `/tmp/central-hub-okr-created.json`

- [ ] **Step 1: Check whether a direct OKR CLI/API route already exists**

Run:

```bash
python3 - <<'PY'
from pathlib import Path

root = Path("/Users/zhangjiangtao/.trae/skills")
matches = sorted(str(p) for p in root.glob("**/*okr*"))
for item in matches[:50]:
    print(item)
PY
```

Expected: either no dedicated OKR skill is found, or a specific route is identified.

- [ ] **Step 2: If no stable OKR CLI exists, create the Objective and KRs via the browser**

Open the Feishu OKR product with the user session, then create:

- Objective title:
  - `中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制`
- KR1:
  - `Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路`
- KR2:
  - `前端关键页面完成实时联动验证，能直接反映交易链路状态变化`
- KR3:
  - `审批、目标推进、workflow 提醒与老板视图形成运行闭环`
- KR4:
  - `架构图、spec、实施计划中的核心功能项被拆解进持续推进机制并可跟踪`

Expected: the Objective and 4 KR entries are visible in Feishu OKR under the correct owner.

- [ ] **Step 3: Capture the created Objective metadata**

Write `/tmp/central-hub-okr-created.json` with the captured data:

```json
{
  "objective_id": "<real-objective-id>",
  "objective_title": "中台与前端联动验证能力打通，并形成可持续的目标驱动建设机制",
  "objective_owner": "<real-owner-name-or-id>",
  "krs": [
    "KR1: Hub 到 Trading 的实时桥接能力可运行，摆脱前端代理和目录投递的临时链路",
    "KR2: 前端关键页面完成实时联动验证，能直接反映交易链路状态变化",
    "KR3: 审批、目标推进、workflow 提醒与老板视图形成运行闭环",
    "KR4: 架构图、spec、实施计划中的核心功能项被拆解进持续推进机制并可跟踪"
  ]
}
```

Expected: a concrete `objective_id` is recorded; if only a URL is available, capture the URL and extract the stable object identifier from it.

## Task 4: Bind the Live Base Goal Record to the New Objective

**Files:**
- Modify online Base record: `recvlSRHGZIC6N`
- Local temp file: `/tmp/central-hub-okr-binding.json`
- Use: `github-actions/build_central_hub_okr_binding_payload.py`

- [ ] **Step 1: Generate the Base binding payload from the captured Objective**

Run:

```bash
python3 - <<'PY'
import json
import subprocess

goal = {
    "goal_id": "goal-trading-hub-connectivity-20260519",
    "goal_name": "中台与前端联动验证能力打通",
}

objective = json.load(open("/tmp/central-hub-okr-created.json", encoding="utf-8"))

payload = {"goal": goal, "objective": objective}
output = subprocess.check_output(
    [
        "python3",
        "/Users/zhangjiangtao/WorkBuddy/DREAM-AGENT/github-actions/build_central_hub_okr_binding_payload.py",
    ],
    input=json.dumps(payload, ensure_ascii=False),
    text=True,
)

with open("/tmp/central-hub-okr-binding.json", "w", encoding="utf-8") as fh:
    fh.write(output)

print(output)
PY
```

Expected: printed JSON includes `OKR对齐=已对齐`, `okr_objective_id`, `okr_objective_title`, `okr_owner`, `okr_sync_status=bound`.

- [ ] **Step 2: Upsert the live Base record**

Run:

```bash
lark-cli base +record-upsert \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --record-id recvlSRHGZIC6N \
  --json "$(cat /tmp/central-hub-okr-binding.json)" \
  --as user --format json
```

Expected: `updated=true`

- [ ] **Step 3: Read the record back and verify the binding**

Run:

```bash
lark-cli base +record-get \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --record-id recvlSRHGZIC6N \
  --as user --format json
```

Expected:

- `OKR对齐 = 已对齐`
- `okr_objective_id` is non-empty
- `okr_objective_title` matches the created Objective
- `okr_owner` is non-empty

## Task 5: Verify the Boss View Still Works and Capture the Final Handoff

**Files:**
- Live Base view: `老板视图（状态与阻塞）`
- Live record: `recvlSRHGZIC6N`
- Optional handoff note: `/tmp/central-hub-okr-handoff.md`

- [ ] **Step 1: Read the boss-view-facing record surface**

Run:

```bash
lark-cli base +record-get \
  --base-token SjCHbDasHarEcFsJjXwc5JZgnUr \
  --table-id tblYwbyMwnO8j8iG \
  --record-id recvlSRHGZIC6N \
  --as user --format json
```

Expected: the record still contains the fields needed by `老板视图（状态与阻塞）`, and `OKR对齐` now reads `已对齐`.

- [ ] **Step 2: Write a short handoff note for the next sub-project**

Run:

```bash
python3 - <<'PY'
import json

record = json.load(open("/tmp/central-hub-okr-created.json", encoding="utf-8"))
with open("/tmp/central-hub-okr-handoff.md", "w", encoding="utf-8") as fh:
    fh.write("# Central Hub OKR Binding Handoff\n\n")
    fh.write(f"- Objective ID: {record['objective_id']}\n")
    fh.write(f"- Objective Title: {record['objective_title']}\n")
    fh.write("- Next Subproject: OKR-driven SKILL\n")
PY
```

Expected: the handoff note captures the real Objective ID for later reuse.

## Self-Review

- Spec coverage:
  - Real Objective creation: Task 2-3
  - 4 KR entries: Task 2-3
  - Base binding and `已对齐`: Task 1 and Task 4
  - Separation from `OKR-driven SKILL`: scope check and Task 5 handoff only
- Placeholder scan:
  - No `TODO` / `TBD`
  - Every code step contains concrete code
  - Every live operation has an exact command or explicit browser creation step
- Type consistency:
  - `OKR对齐` only uses Chinese enum text
  - `okr_objective_*` fields remain the Base anchor layer
  - The payload builder owns the Base binding JSON shape
