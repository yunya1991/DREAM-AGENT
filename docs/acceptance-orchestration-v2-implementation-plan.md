# Acceptance Orchestration V2 实施方案

> **给执行型 agent：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐项执行。所有步骤都使用勾选框 `- [ ]` 跟踪。

**目标：** 实现一个首版可落地的 `Acceptance Orchestration V2`，通过 `lark-cli` 读取飞书 `work item` 上下文，在仓库 `ledger` 中保存稳定的 `acceptance_cycle` 对象，按 4 角色串行执行验收流程，并继续以 GitHub `VALIDATION_RESULT` 作为唯一正式验收锚点。

**架构：** 保持 GitHub 作为协议中枢，不重写现有 acceptance workflow，而是在其上扩展。`acceptance_cycle` 记录落在 `ledger/acceptance_cycles`，通过轻量 `lark-cli` 适配层和上下文收集器读取 Base / OKR 数据，再交给串行 orchestrator 产出 GitHub 验收评论与飞书摘要补丁；飞书只提供上下文与摘要回写，不成为正式结论真源。

**技术栈：** Python 3.11、GitHub Actions YAML、`unittest`、`gh`、`lark-cli`、JSON ledger 文件、Markdown 协议模板

---

## 文件结构

### 新增文件

- `docs/acceptance-orchestration-v2-implementation-plan.md`
  - 本实施方案文档。
- `ledger/templates/acceptance-cycle-record.json`
  - 单个 `acceptance_cycle` 的标准 JSON 模板。
- `ledger/acceptance_cycles/index.json`
  - `acceptance_cycle` 总索引，维护 `open_cycles` 和完整 cycle 列表。
- `github-actions/manage_acceptance_cycle.py`
  - 负责在仓库 ledger 中创建、更新、持久化、读取 `acceptance_cycle` 记录。
- `github-actions/lark_cli.py`
  - `lark-cli` 的安全包装器，统一处理 JSON 输出、身份参数、认证检查。
- `github-actions/collect_lark_context.py`
  - 读取 Base `work item` 与可选 OKR 实体，构建规范化上下文快照。
- `github-actions/run_acceptance_cycle.py`
  - 串行 4 角色 orchestrator：`context-reader -> protocol-checker -> acceptance-validator -> result-synthesizer`。
- `github-actions/tests/test_manage_acceptance_cycle.py`
  - `acceptance_cycle` ledger 持久化和状态推进测试。
- `github-actions/tests/test_lark_cli.py`
  - `lark-cli` 包装器的命令拼装、JSON 解析、认证测试。
- `github-actions/tests/test_collect_lark_context.py`
  - Base / OKR 上下文收集测试，使用 mock 响应。
- `github-actions/tests/test_run_acceptance_cycle.py`
  - 串行角色链路和综合输出的端到端测试。

### 修改文件

- `templates/pr-comment-acceptance-request.md`
  - 扩展验收请求协议，增加 `acceptance_cycle` 和飞书 `work item` 定位字段。
- `templates/pr-comment-validation-result.md`
  - 增加 `Acceptance Cycle ID`，让正式 GitHub 结论能反向关联到 cycle ledger。
- `github-actions/check_acceptance_request.py`
  - 校验新增结构化字段，并向下游编排暴露解析结果。
- `github-actions/resolve_acceptance_inputs.py`
  - 除 `acceptance_request_id` 外，再从 PR 评论中解析 `acceptance_cycle_id` 和 `work_item_id`。
- `github-actions/tests/test_check_acceptance_request.py`
  - 固化新的评论协议和解析行为。
- `github-actions/tests/test_resolve_acceptance_inputs.py`
  - 固化新的输入提取行为。
- `.github/workflows/collab-acceptance-agent.yml`
  - 用脚本化的 cycle 创建、飞书上下文收集、cycle 执行、评论发布、摘要同步替换内联逻辑。
- `docs/01-COLLABORATION-PROTOCOL.md`
  - 记录 `acceptance_cycle` 对象、新的请求字段，以及 GitHub / 飞书真源边界。
- `docs/03-WORKFLOWS-AND-NORMS.md`
  - 记录串行 4 角色验收链路与飞书摘要回写规则。
- `github-actions/README.md`
  - 说明新的 ledger、飞书适配层与编排脚本。

## Task 1：增加基于 Ledger 的 `acceptance_cycle` 对象

**Files:**
- Create: `ledger/templates/acceptance-cycle-record.json`
- Create: `ledger/acceptance_cycles/index.json`
- Create: `github-actions/manage_acceptance_cycle.py`
- Test: `github-actions/tests/test_manage_acceptance_cycle.py`

- [ ] **Step 1: 先写失败测试**

```python
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "manage_acceptance_cycle.py"
SPEC = importlib.util.spec_from_file_location("manage_acceptance_cycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AcceptanceCycleLedgerTests(unittest.TestCase):
    def test_create_manual_cycle_writes_record_and_index(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            ledger_dir = root / "ledger" / "acceptance_cycles"
            ledger_dir.mkdir(parents=True)
            (ledger_dir / "index.json").write_text(
                json.dumps(
                    {
                        "version": 1,
                        "generated_at": "",
                        "open_cycles": [],
                        "cycles": [],
                    }
                ),
                encoding="utf-8",
            )

            record = MODULE.create_manual_cycle(
                root=root,
                acceptance_cycle_id="ac-20260607-001",
                work_item_id="WI-123",
                pr_number="6",
                acceptance_request_id="ar-20260607-006",
                lark_base_url="https://example.feishu.cn/base/app123?table=tbl456",
                lark_table_id="tbl456",
                lark_record_id="rec789",
            )

            self.assertEqual(record["cycle_status"], "requested")
            self.assertEqual(record["current_phase"], "context-reader")
            self.assertEqual(record["linked_prs"], ["6"])
            self.assertEqual(record["lark_context_locator"]["record_id"], "rec789")

            persisted = json.loads(
                (ledger_dir / "ac-20260607-001.json").read_text(encoding="utf-8")
            )
            index_payload = json.loads(
                (ledger_dir / "index.json").read_text(encoding="utf-8")
            )

            self.assertEqual(persisted["acceptance_cycle_id"], "ac-20260607-001")
            self.assertIn("ac-20260607-001", index_payload["open_cycles"])
            self.assertEqual(index_payload["cycles"][0]["acceptance_cycle_id"], "ac-20260607-001")

    def test_update_cycle_phase_keeps_latest_request_pointer(self):
        cycle = {
            "acceptance_cycle_id": "ac-20260607-001",
            "cycle_status": "requested",
            "current_phase": "context-reader",
            "latest_acceptance_request_id": "ar-20260607-006",
            "latest_validation_result_id": "",
            "agent_outputs": {},
        }

        updated = MODULE.apply_cycle_progress(
            cycle,
            phase="result-synthesizer",
            cycle_status="validated",
            validation_result_id="vr-20260607-001",
            agent_output={"decision": "ACCEPTED"},
        )

        self.assertEqual(updated["current_phase"], "result-synthesizer")
        self.assertEqual(updated["cycle_status"], "validated")
        self.assertEqual(updated["latest_acceptance_request_id"], "ar-20260607-006")
        self.assertEqual(updated["latest_validation_result_id"], "vr-20260607-001")
        self.assertEqual(updated["agent_outputs"]["result-synthesizer"]["decision"], "ACCEPTED")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行定向测试，确认先红灯**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_manage_acceptance_cycle -v
```

Expected: FAIL，因为 ledger 模板、索引文件和 manager 模块还不存在。

- [ ] **Step 3: 增加 cycle 模板、索引文件和 manager 实现**

`ledger/templates/acceptance-cycle-record.json`

```json
{
  "acceptance_cycle_id": "ac-example",
  "work_item_id": "WI-example",
  "cycle_status": "requested",
  "creation_mode": "manual",
  "linked_prs": [],
  "latest_acceptance_request_id": "",
  "latest_validation_result_id": "",
  "current_phase": "context-reader",
  "lark_context_locator": {
    "base_url": "",
    "table_id": "",
    "record_id": ""
  },
  "agent_outputs": {
    "context-reader": {},
    "protocol-checker": {},
    "acceptance-validator": {},
    "result-synthesizer": {}
  },
  "artifacts": {
    "context_snapshot_file": "",
    "validation_result_comment_file": ""
  }
}
```

`ledger/acceptance_cycles/index.json`

```json
{
  "version": 1,
  "generated_at": "",
  "open_cycles": [],
  "cycles": []
}
```

`github-actions/manage_acceptance_cycle.py`

```python
import json
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_cycle_record(
    acceptance_cycle_id: str,
    work_item_id: str,
    pr_number: str,
    acceptance_request_id: str,
    lark_base_url: str,
    lark_table_id: str,
    lark_record_id: str,
) -> dict:
    return {
        "acceptance_cycle_id": acceptance_cycle_id,
        "work_item_id": work_item_id,
        "cycle_status": "requested",
        "creation_mode": "manual",
        "linked_prs": [pr_number],
        "latest_acceptance_request_id": acceptance_request_id,
        "latest_validation_result_id": "",
        "current_phase": "context-reader",
        "lark_context_locator": {
            "base_url": lark_base_url,
            "table_id": lark_table_id,
            "record_id": lark_record_id,
        },
        "agent_outputs": {
            "context-reader": {},
            "protocol-checker": {},
            "acceptance-validator": {},
            "result-synthesizer": {},
        },
        "artifacts": {
            "context_snapshot_file": "",
            "validation_result_comment_file": "",
        },
    }


def apply_cycle_progress(
    cycle: dict,
    phase: str,
    cycle_status: str,
    validation_result_id: str,
    agent_output: dict,
) -> dict:
    cycle["current_phase"] = phase
    cycle["cycle_status"] = cycle_status
    if validation_result_id:
        cycle["latest_validation_result_id"] = validation_result_id
    cycle.setdefault("agent_outputs", {})[phase] = dict(agent_output)
    return cycle


def create_manual_cycle(
    root: Path,
    acceptance_cycle_id: str,
    work_item_id: str,
    pr_number: str,
    acceptance_request_id: str,
    lark_base_url: str,
    lark_table_id: str,
    lark_record_id: str,
) -> dict:
    ledger_dir = root / "ledger" / "acceptance_cycles"
    index_path = ledger_dir / "index.json"
    record = build_cycle_record(
        acceptance_cycle_id,
        work_item_id,
        pr_number,
        acceptance_request_id,
        lark_base_url,
        lark_table_id,
        lark_record_id,
    )
    (ledger_dir / f"{acceptance_cycle_id}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    index_payload = json.loads(index_path.read_text(encoding="utf-8"))
    index_payload["generated_at"] = utc_now()
    index_payload["open_cycles"].append(acceptance_cycle_id)
    index_payload["cycles"].append(
        {
            "acceptance_cycle_id": acceptance_cycle_id,
            "work_item_id": work_item_id,
            "cycle_status": "requested",
            "linked_prs": [pr_number],
        }
    )
    index_path.write_text(json.dumps(index_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return record
```

- [ ] **Step 4: 重新运行定向测试，确认转绿**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_manage_acceptance_cycle -v
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add ledger/templates/acceptance-cycle-record.json ledger/acceptance_cycles/index.json github-actions/manage_acceptance_cycle.py github-actions/tests/test_manage_acceptance_cycle.py
git commit -m "feat: add acceptance cycle ledger model"
```

## Task 2：扩展面向飞书 Work Item 的验收评论协议

**Files:**
- Modify: `templates/pr-comment-acceptance-request.md`
- Modify: `templates/pr-comment-validation-result.md`
- Modify: `github-actions/check_acceptance_request.py`
- Modify: `github-actions/resolve_acceptance_inputs.py`
- Modify: `github-actions/tests/test_check_acceptance_request.py`
- Modify: `github-actions/tests/test_resolve_acceptance_inputs.py`

- [ ] **Step 1: 为新增字段补失败测试**

```python
VALID_COMMENT = """
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: ar-20260607-001
Acceptance Cycle ID: ac-20260607-001
Work Item ID: WI-123
Request Type: pilot
Request Mode: manual
Source of Truth: PR comment
Target PR: #6
Lark Base URL: https://example.feishu.cn/base/app123?table=tbl456
Lark Table ID: tbl456
Lark Record ID: rec789

## 验收对象
- PR comment driven acceptance pilot

## 验收范围
- comment structure

## 业务上下文映射
- 目标来源: Objective O-1 / KR KR-1
- 本轮说明: verify cycle orchestration inputs

## 重点验收项
- source of truth clarity

## 本轮不要求
- no business code changes

## 期望回写格式
- 验收对象
- 最终结论
""".strip()


class AcceptanceRequestParserTests(unittest.TestCase):
    def test_acceptance_request_extracts_cycle_and_lark_locators(self):
        result = MODULE.evaluate_acceptance_request(VALID_COMMENT)
        self.assertEqual(result["decision"], "ACCEPTED")
        self.assertEqual(result["acceptance_request_id"], "ar-20260607-001")
        self.assertEqual(result["acceptance_cycle_id"], "ac-20260607-001")
        self.assertEqual(result["work_item_id"], "WI-123")
        self.assertEqual(result["lark_table_id"], "tbl456")
        self.assertEqual(result["lark_record_id"], "rec789")
```

```python
class ResolveAcceptanceInputsTests(unittest.TestCase):
    def test_extract_acceptance_cycle_id_from_comment_body(self):
        body = VALID_COMMENT
        self.assertEqual(
            MODULE.extract_field(body, "Acceptance Cycle ID"),
            "ac-20260607-001",
        )
        self.assertEqual(MODULE.extract_field(body, "Work Item ID"), "WI-123")
```

- [ ] **Step 2: 运行定向测试，确认先红灯**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request github-actions.tests.test_resolve_acceptance_inputs -v
```

Expected: FAIL，因为当前评论协议还没有声明或解析 cycle 和飞书定位字段。

- [ ] **Step 3: 最小扩展模板和解析器**

`templates/pr-comment-acceptance-request.md`

```md
[验收委托 / ACCEPTANCE_REQUEST]

Acceptance Request ID: <ar-YYYYMMDD-001>
Acceptance Cycle ID: <ac-YYYYMMDD-001>
Work Item ID: <WI-123>
Request Type: <feature | phase-gate | pilot>
Request Mode: <manual | auto>
Source of Truth: PR comment
Target PR: <#123>
Lark Base URL: <https://tenant.feishu.cn/base/appToken?table=tblToken>
Lark Table ID: <tblToken>
Lark Record ID: <recToken>

## 验收对象
- <what is being accepted now>

## 验收范围
- <scope item 1>

## 业务上下文映射
- 目标来源: <Objective / KR / none>
- 本轮说明: <why this acceptance exists now>

## 重点验收项
- <focus item 1>

## 本轮不要求
- <out-of-scope item 1>

## 期望回写格式
- 验收对象
- 协议读取结论
- 当前阻塞项
- 下一步建议
- 最终结论
```

`templates/pr-comment-validation-result.md`

```md
[验证结论 / VALIDATION_RESULT]

Validator: <validator agent>
Validation Mode: <delivery | acceptance>
Acceptance Request ID: <request id | none>
Acceptance Cycle ID: <cycle id | none>
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

`github-actions/check_acceptance_request.py`

```python
REQUIRED_FIELDS = [
    "Acceptance Request ID:",
    "Acceptance Cycle ID:",
    "Work Item ID:",
    "Request Type:",
    "Request Mode:",
    "Source of Truth:",
    "Target PR:",
    "Lark Base URL:",
    "Lark Table ID:",
    "Lark Record ID:",
]


def extract_field(comment_body: str, field_name: str) -> str:
    pattern = rf"{re.escape(field_name)}:\s*(.+)"
    match = re.search(pattern, comment_body)
    return match.group(1).strip() if match else ""


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

    return {
        "decision": "ACCEPTED",
        "protocol_read_result": "PASS",
        "source_of_truth_verdict": "usable",
        "reason_codes": ["NONE"],
        "recommended_next_action": "context-reader: collect lark work item snapshot",
        "acceptance_request_id": extract_field(comment_body, "Acceptance Request ID"),
        "acceptance_cycle_id": extract_field(comment_body, "Acceptance Cycle ID"),
        "work_item_id": extract_field(comment_body, "Work Item ID"),
        "lark_base_url": extract_field(comment_body, "Lark Base URL"),
        "lark_table_id": extract_field(comment_body, "Lark Table ID"),
        "lark_record_id": extract_field(comment_body, "Lark Record ID"),
    }
```

`github-actions/resolve_acceptance_inputs.py`

```python
def extract_field(comment_body: str, field_name: str) -> str:
    match = re.search(rf"{re.escape(field_name)}:\s*(.+)", comment_body)
    return match.group(1).strip() if match else ""


def resolve_issue_comment_event(event: dict) -> dict:
    comment_body = event.get("comment", {}).get("body", "")
    return {
        "pr_number": str(event.get("issue", {}).get("number", "")),
        "acceptance_request_id": extract_field(comment_body, "Acceptance Request ID"),
        "acceptance_cycle_id": extract_field(comment_body, "Acceptance Cycle ID"),
        "work_item_id": extract_field(comment_body, "Work Item ID"),
        "comment_body": comment_body,
    }
```

- [ ] **Step 4: 重新运行定向测试，确认转绿**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_check_acceptance_request github-actions.tests.test_resolve_acceptance_inputs -v
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add templates/pr-comment-acceptance-request.md templates/pr-comment-validation-result.md github-actions/check_acceptance_request.py github-actions/resolve_acceptance_inputs.py github-actions/tests/test_check_acceptance_request.py github-actions/tests/test_resolve_acceptance_inputs.py
git commit -m "feat: extend acceptance request contract for lark work items"
```

## Task 3：增加安全的 `lark-cli` 适配层和上下文收集器

**Files:**
- Create: `github-actions/lark_cli.py`
- Create: `github-actions/collect_lark_context.py`
- Test: `github-actions/tests/test_lark_cli.py`
- Test: `github-actions/tests/test_collect_lark_context.py`

- [ ] **Step 1: 先写适配层和收集器的失败测试**

```python
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


LARK_CLI_PATH = Path(__file__).resolve().parents[1] / "lark_cli.py"
LARK_CLI_SPEC = importlib.util.spec_from_file_location("lark_cli", LARK_CLI_PATH)
LARK_CLI = importlib.util.module_from_spec(LARK_CLI_SPEC)
LARK_CLI_SPEC.loader.exec_module(LARK_CLI)


class LarkCliTests(unittest.TestCase):
    def test_build_command_appends_identity_and_json_output(self):
        argv = LARK_CLI.build_lark_command(
            ["base", "+record-get", "--base-token", "app123"],
            identity="user",
        )
        self.assertEqual(argv[:3], ["lark-cli", "base", "+record-get"])
        self.assertIn("--as", argv)
        self.assertEqual(argv[-2:], ["--format", "json"])
```

```python
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "collect_lark_context.py"
SPEC = importlib.util.spec_from_file_location("collect_lark_context", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class CollectLarkContextTests(unittest.TestCase):
    @mock.patch.object(MODULE, "run_lark_json")
    def test_collect_context_reads_base_record_and_okr_entities(self, mock_run):
        mock_run.side_effect = [
            {"data": {"records": [{"record_id": "rec789", "fields": {"Title": "Pilot item", "Objective ID": "obj1", "KR ID": "kr1"}}]}},
            {"data": {"objective": {"id": "obj1", "content": {"blocks": [{"text": "Stabilize acceptance orchestration"}]}}}},
            {"data": {"key_result": {"id": "kr1", "content": {"blocks": [{"text": "Run one cycle from work item"}]}}}},
        ]

        snapshot = MODULE.collect_context_snapshot(
            {
                "work_item_id": "WI-123",
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                }
            }
        )

        self.assertEqual(snapshot["work_item"]["record_id"], "rec789")
        self.assertEqual(snapshot["objective"]["id"], "obj1")
        self.assertEqual(snapshot["key_result"]["id"], "kr1")
        self.assertEqual(snapshot["context_summary"], "Pilot item")
```

- [ ] **Step 2: 运行定向测试，确认先红灯**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_lark_cli github-actions.tests.test_collect_lark_context -v
```

Expected: FAIL，因为适配层和收集器尚未实现。

- [ ] **Step 3: 最小实现适配层和收集器**

`github-actions/lark_cli.py`

```python
import json
import subprocess


def build_lark_command(args: list[str], identity: str = "user") -> list[str]:
    return ["lark-cli", *args, "--as", identity, "--format", "json"]


def run_lark_json(args: list[str], identity: str = "user") -> dict:
    result = subprocess.run(
        build_lark_command(args, identity=identity),
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def ensure_lark_auth(identity: str = "user") -> None:
    subprocess.run(
        build_lark_command(["auth", "status"], identity=identity),
        check=True,
        capture_output=True,
        text=True,
    )
```

`github-actions/collect_lark_context.py`

```python
from lark_cli import ensure_lark_auth, run_lark_json


def extract_base_token(base_url: str) -> str:
    return base_url.split("/base/", 1)[1].split("?", 1)[0]


def get_base_record(base_token: str, table_id: str, record_id: str) -> dict:
    payload = run_lark_json(
        [
            "base",
            "+record-get",
            "--base-token",
            base_token,
            "--table-id",
            table_id,
            "--record-id",
            record_id,
        ]
    )
    return payload["data"]["records"][0]


def get_objective(objective_id: str) -> dict:
    payload = run_lark_json(
        ["okr", "objectives", "get", "--params", f'{{"objective_id":"{objective_id}"}}']
    )
    return payload["data"]["objective"]


def get_key_result(key_result_id: str) -> dict:
    payload = run_lark_json(
        ["okr", "key_results", "get", "--params", f'{{"key_result_id":"{key_result_id}"}}']
    )
    return payload["data"]["key_result"]


def collect_context_snapshot(cycle: dict) -> dict:
    locator = cycle["lark_context_locator"]
    ensure_lark_auth(identity="user")
    base_token = extract_base_token(locator["base_url"])
    record = get_base_record(base_token, locator["table_id"], locator["record_id"])
    fields = record.get("fields", {})
    objective_id = fields.get("Objective ID", "")
    key_result_id = fields.get("KR ID", "")
    objective = get_objective(objective_id) if objective_id else {}
    key_result = get_key_result(key_result_id) if key_result_id else {}
    return {
        "work_item": {
            "record_id": record["record_id"],
            "fields": fields,
        },
        "objective": objective,
        "key_result": key_result,
        "context_summary": fields.get("Title", ""),
    }
```

- [ ] **Step 4: 重新运行定向测试，确认转绿**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_lark_cli github-actions.tests.test_collect_lark_context -v
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add github-actions/lark_cli.py github-actions/collect_lark_context.py github-actions/tests/test_lark_cli.py github-actions/tests/test_collect_lark_context.py
git commit -m "feat: add lark cli adapter and context collector"
```

## Task 4：实现串行 4 角色 Acceptance Orchestrator

**Files:**
- Create: `github-actions/run_acceptance_cycle.py`
- Modify: `github-actions/manage_acceptance_cycle.py`
- Test: `github-actions/tests/test_run_acceptance_cycle.py`

- [ ] **Step 1: 先写 orchestrator 的失败测试**

```python
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "run_acceptance_cycle.py"
SPEC = importlib.util.spec_from_file_location("run_acceptance_cycle", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RunAcceptanceCycleTests(unittest.TestCase):
    @mock.patch.object(MODULE, "collect_context_snapshot")
    @mock.patch.object(MODULE, "evaluate_acceptance_request")
    def test_run_cycle_executes_serial_roles_and_builds_outputs(
        self,
        mock_evaluate,
        mock_collect,
    ):
        mock_collect.return_value = {
            "work_item": {"record_id": "rec789", "fields": {"Title": "Pilot item"}},
            "objective": {"id": "obj1"},
            "key_result": {"id": "kr1"},
            "context_summary": "Pilot item",
        }
        mock_evaluate.return_value = {
            "decision": "ACCEPTED",
            "protocol_read_result": "PASS",
            "source_of_truth_verdict": "usable",
            "reason_codes": ["NONE"],
            "recommended_next_action": "validator: post VALIDATION_RESULT",
            "acceptance_request_id": "ar-20260607-006",
            "acceptance_cycle_id": "ac-20260607-001",
            "work_item_id": "WI-123",
        }

        result = MODULE.run_cycle(
            cycle={
                "acceptance_cycle_id": "ac-20260607-001",
                "work_item_id": "WI-123",
                "current_phase": "context-reader",
                "cycle_status": "requested",
                "lark_context_locator": {
                    "base_url": "https://example.feishu.cn/base/app123?table=tbl456",
                    "table_id": "tbl456",
                    "record_id": "rec789",
                },
            },
            comment_body="[验收委托 / ACCEPTANCE_REQUEST]",
            pr_number="6",
        )

        self.assertEqual(result["cycle"]["cycle_status"], "validated")
        self.assertEqual(result["cycle"]["current_phase"], "result-synthesizer")
        self.assertEqual(result["validation_result"]["decision"], "ACCEPTED")
        self.assertIn("Acceptance Cycle ID: ac-20260607-001", result["comment_body"])
        self.assertEqual(result["lark_summary_patch"]["fields"]["Acceptance Status"], "accepted")
```

- [ ] **Step 2: 运行定向测试，确认先红灯**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_run_acceptance_cycle -v
```

Expected: FAIL，因为 orchestrator 还不存在。

- [ ] **Step 3: 实现 orchestrator 和 cycle 推进逻辑**

`github-actions/run_acceptance_cycle.py`

```python
from collect_lark_context import collect_context_snapshot
from check_acceptance_request import evaluate_acceptance_request
from manage_acceptance_cycle import apply_cycle_progress


def build_validation_result_comment(
    cycle: dict,
    validation_result: dict,
    context_snapshot: dict,
) -> str:
    hard_gate = "BLOCK" if validation_result["decision"] == "BLOCK" else "PASS"
    conclusion_map = {
        "ACCEPTED": "accepted",
        "REWORK": "rework",
        "BLOCK": "blocked",
    }
    lines = [
        "[验证结论 / VALIDATION_RESULT]",
        "",
        "Validator: result-synthesizer",
        "Validation Mode: acceptance",
        f"Acceptance Request ID: {validation_result['acceptance_request_id']}",
        f"Acceptance Cycle ID: {cycle['acceptance_cycle_id']}",
        f"Hard Gate Result: {hard_gate}",
        "Score: 90",
        f"Decision: {validation_result['decision']}",
        f"Protocol Read Result: {validation_result['protocol_read_result']}",
        f"Source of Truth Verdict: {validation_result['source_of_truth_verdict']}",
        "Reason Codes:",
        f"- {','.join(validation_result['reason_codes'])}",
        "Must-Fix Items:",
        "- none" if validation_result["decision"] == "ACCEPTED" else "- complete the protocol gaps before rerun",
        f"Next Step Recommendation: {validation_result['recommended_next_action']}",
        f"Acceptance Conclusion: {conclusion_map[validation_result['decision']]}",
        "Reward Multiplier: 1.0",
        "Ledger Update: none",
        "Governance Handoff: pending",
        "",
        "Context Snapshot:",
        f"- work_item_title={context_snapshot['context_summary']}",
        f"- pr_number={cycle['linked_prs'][0] if cycle.get('linked_prs') else ''}",
    ]
    return "\n".join(lines) + "\n"


def build_lark_summary_patch(cycle: dict, validation_result: dict) -> dict:
    status_map = {
        "ACCEPTED": "accepted",
        "REWORK": "rework",
        "BLOCK": "blocked",
    }
    return {
        "fields": {
            "Acceptance Cycle ID": cycle["acceptance_cycle_id"],
            "Acceptance Status": status_map[validation_result["decision"]],
            "Latest Acceptance Request ID": validation_result["acceptance_request_id"],
            "Latest Validation Decision": validation_result["decision"],
        }
    }


def run_cycle(cycle: dict, comment_body: str, pr_number: str) -> dict:
    cycle.setdefault("linked_prs", []).append(pr_number)
    context_snapshot = collect_context_snapshot(cycle)
    cycle = apply_cycle_progress(
        cycle,
        phase="context-reader",
        cycle_status="context_collected",
        validation_result_id="",
        agent_output=context_snapshot,
    )

    protocol_result = evaluate_acceptance_request(comment_body)
    cycle = apply_cycle_progress(
        cycle,
        phase="protocol-checker",
        cycle_status="protocol_checked",
        validation_result_id="",
        agent_output=protocol_result,
    )

    validation_result = dict(protocol_result)
    cycle = apply_cycle_progress(
        cycle,
        phase="acceptance-validator",
        cycle_status="validation_running",
        validation_result_id="",
        agent_output=validation_result,
    )

    comment = build_validation_result_comment(cycle, validation_result, context_snapshot)
    cycle = apply_cycle_progress(
        cycle,
        phase="result-synthesizer",
        cycle_status="validated",
        validation_result_id=f"vr-{cycle['acceptance_cycle_id']}",
        agent_output={"decision": validation_result["decision"], "comment_body": comment},
    )
    return {
        "cycle": cycle,
        "context_snapshot": context_snapshot,
        "validation_result": validation_result,
        "comment_body": comment,
        "lark_summary_patch": build_lark_summary_patch(cycle, validation_result),
    }
```

- [ ] **Step 4: 重新运行定向测试，确认转绿**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_run_acceptance_cycle -v
```

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add github-actions/run_acceptance_cycle.py github-actions/manage_acceptance_cycle.py github-actions/tests/test_run_acceptance_cycle.py
git commit -m "feat: add serial acceptance cycle orchestrator"
```

## Task 5：接线 Workflow、摘要同步和文档

**Files:**
- Modify: `.github/workflows/collab-acceptance-agent.yml`
- Modify: `docs/01-COLLABORATION-PROTOCOL.md`
- Modify: `docs/03-WORKFLOWS-AND-NORMS.md`
- Modify: `github-actions/README.md`
- Modify: `github-actions/tests/test_collab_workflows_present.py`

- [ ] **Step 1: 为新的编排步骤增加失败测试**

```python
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class AcceptanceWorkflowContractTests(unittest.TestCase):
    def test_acceptance_workflow_uses_cycle_and_lark_scripts(self):
        text = (
            ROOT / ".github" / "workflows" / "collab-acceptance-agent.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("python3 github-actions/manage_acceptance_cycle.py", text)
        self.assertIn("python3 github-actions/collect_lark_context.py", text)
        self.assertIn("python3 github-actions/run_acceptance_cycle.py", text)
```

- [ ] **Step 2: 运行 workflow 合同测试，确认先红灯**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest github-actions.tests.test_collab_workflows_present.AcceptanceWorkflowContractTests -v
```

Expected: FAIL，因为当前 workflow 仍然只执行内联 acceptance 逻辑。

- [ ] **Step 3: 用脚本驱动的编排替换内联 workflow 逻辑**

`.github/workflows/collab-acceptance-agent.yml`

```yaml
      - name: Create or load acceptance cycle
        id: cycle
        env:
          ACCEPTANCE_CYCLE_ID: ${{ steps.inputs.outputs.acceptance_cycle_id }}
          WORK_ITEM_ID: ${{ steps.inputs.outputs.work_item_id }}
          ACCEPTANCE_REQUEST_ID: ${{ steps.inputs.outputs.acceptance_request_id }}
          PR_NUMBER: ${{ steps.inputs.outputs.pr_number }}
          COMMENT_BODY: ${{ steps.request.outputs.comment_body }}
        run: |
          python3 github-actions/manage_acceptance_cycle.py > acceptance_cycle.json

      - name: Collect lark context
        run: |
          python3 github-actions/collect_lark_context.py acceptance_cycle.json > acceptance_context.json

      - name: Run acceptance cycle
        run: |
          python3 github-actions/run_acceptance_cycle.py acceptance_cycle.json > acceptance_run.json

      - name: Render validation result
        run: |
          python3 - <<'PY'
          import json
          from pathlib import Path

          payload = json.loads(Path("acceptance_run.json").read_text(encoding="utf-8"))
          Path("pr_acceptance_result.md").write_text(
              payload["comment_body"],
              encoding="utf-8",
          )
          Path("lark_summary_patch.json").write_text(
              json.dumps(payload["lark_summary_patch"], ensure_ascii=False, indent=2),
              encoding="utf-8",
          )
          PY
```

`docs/01-COLLABORATION-PROTOCOL.md`

```md
### `acceptance_cycle`

- `acceptance_cycle` 是 `Acceptance Orchestration V2` 的编排中心对象
- 真源载体位于 `ledger/acceptance_cycles/*.json`
- 正式验收结论仍只允许落在 GitHub `VALIDATION_RESULT`
- 飞书只提供上下文与摘要回写，不写入第二份正式主结论
```

`docs/03-WORKFLOWS-AND-NORMS.md`

```md
### V2 串行验收链

1. `context-reader` 读取飞书 `work item` 和可选 `Objective / KR`
2. `protocol-checker` 校验 `ACCEPTANCE_REQUEST` 结构化完整性
3. `acceptance-validator` 形成当前轮次的验收判断
4. `result-synthesizer` 回写唯一正式 `VALIDATION_RESULT`

规则：

- GitHub `VALIDATION_RESULT` 是正式验收真源
- 飞书只允许回写摘要字段，不允许回写正式主结论字段
```

`github-actions/README.md`

```md
- `manage_acceptance_cycle.py`：创建和推进 `acceptance_cycle` ledger 记录
- `lark_cli.py`：`lark-cli` 安全包装器
- `collect_lark_context.py`：拉取 Base / OKR 上下文快照
- `run_acceptance_cycle.py`：执行串行 4 角色验收编排
```

- [ ] **Step 4: 重新运行测试，并做一次聚焦 workflow 干跑验证**

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
python3 -m unittest \
  github-actions.tests.test_manage_acceptance_cycle \
  github-actions.tests.test_check_acceptance_request \
  github-actions.tests.test_resolve_acceptance_inputs \
  github-actions.tests.test_lark_cli \
  github-actions.tests.test_collect_lark_context \
  github-actions.tests.test_run_acceptance_cycle \
  github-actions.tests.test_collab_workflows_present -v
```

Expected: PASS。

Run:

```bash
cd /Users/zhangjiangtao/WorkBuddy/DREAM-AGENT
lark-cli auth status --as user
gh workflow run collab-acceptance-agent.yml -f pr_number=6 -f acceptance_request_id=ar-20260607-006
```

Expected: `lark-cli auth status` 成功，然后 workflow 启动并产出 `acceptance_cycle.json`、`acceptance_context.json`、`acceptance_run.json`，同时在 PR 下回写一个包含 `Acceptance Cycle ID` 的 `VALIDATION_RESULT` 评论。

- [ ] **Step 5: 提交**

```bash
git add .github/workflows/collab-acceptance-agent.yml docs/01-COLLABORATION-PROTOCOL.md docs/03-WORKFLOWS-AND-NORMS.md github-actions/README.md github-actions/tests/test_collab_workflows_present.py
git commit -m "feat: wire acceptance orchestration v2 workflow"
```
