---
date: 2026-06-10
status: Draft
scope: Dreambuddy-V2 + DREAM-AGENT + Feishu OKR + Feishu Base (Dream多维表格)
---

# Doc → OKR → Base 协作主流程协议

## 1. 目的

把“项目协作”统一收敛为可监督、可同步、可追溯的链路：

- Spec/实施计划 → 飞书审批与评审记录（DESIGN_REVIEW） → 飞书 OKR（Objective/KR） → 多维表格（目标推进表/模块任务表） → PR 推进 → 自动化任务监控回写。
- 缺失任何前置要素时，优先补齐，不允许进入真实开工推进。

## 2. 适用范围

- 适用于所有“项目工作”（会消耗主线产能、需要对齐目标并可追踪推进的工作）。
- 不适用于纯探索、一次性临时验证；若确需走临时工作，必须显式标记为 non-okr 且不允许进入主线自动化推进与监督统计。

## 3. 名词与真源

- Spec：定义边界、约束、验收口径的文档（仓库内或飞书文档）。
- 实施计划（Plan）：把 Spec 拆成可执行步骤、可拆分任务的文档（仓库内或飞书文档）。
- 飞书审批：项目第一次开工前的审批实例（必须存在）。
- DESIGN_REVIEW：评审记录（必须存在，且需你亲自确认已完成）。
- 飞书 OKR：Objective/KR 的真源系统。
- Dream多维表格（Feishu Base）：协作与监督用的“执行索引与状态面板”，不是 OKR 真源。
  - `目标推进表`：Goal 层（绑定 Objective/KR、阶段、风险、下一步、同步状态）。
  - `模块任务表`：Module Task 层（由 Spec/Plan 拆分出的可执行任务卡，绑定 goal_id）。
  - `自动化任务监控`：Run 层（PR/Workflow/运行证据与提醒）。

## 4. 角色与职责

- 你（Owner）：确认第一次开工审批与 DESIGN_REVIEW 已完成；监督飞书侧工具同步是否完整。
- 执行者（人或 agent）：严格按本协议补齐前置、推进任务、并在收尾时完成后置更新与回写。
- 监督自动化（可选）：从 Base 读取待推进任务，创建/推进 PR，并回写运行证据到 Base（但不得绕过前置 Gate）。

## 5. 强制 Gate（立即生效）

### 5.1 Gate A：项目/模块第一次开工批准（必须人工确认）

在任一项目/模块第一次正式开工前，必须同时满足：

1. 飞书审批实例存在（提供链接或编号）。
2. DESIGN_REVIEW 评审记录存在（提供文档链接，且包含评审结论）。
3. 你已确认：审批通过 + 评审已完成。

未满足 Gate A 时，只允许做“补齐前置材料”的工作，不允许进入实现/交付推进，也不允许提交开工声明。

### 5.2 Gate B：Doc → OKR → Base 完整性（每次自动化任务/每次推进都必须检查）

对每一条将要推进的模块任务，开工前必须满足：

- Spec 与 Plan 均可定位（链接或仓库路径明确，且与 module_paths 对齐）。
- 飞书 OKR Objective 已创建（Objective 链接或 ID 明确）。
- Base `目标推进表` 中存在与该 Objective 绑定的目标记录（goal_id）。
- Base `模块任务表` 中存在任务记录（task_id），并且：
  - `goal_id` 已绑定
  - `lane_type` 已明确
  - `module_paths/spec_doc/plan_doc` 已填写

任何缺失项都视为阻塞：必须先补齐，再进入开工与推进。

## 6. 开工与推进规则

### 6.1 PR 作为推进载体（所有正式工作）

每个 PR 必须在 PR Body 中写明（用于门禁、审计与回写）：

- Task ID（模块任务表.task_id）
- Goal ID（目标推进表.goal_id）
- Lane（fast/strict）
- Module Key / Module Paths
- Spec Doc / Plan Doc

### 6.2 开工声明（STARTED）

允许提交 STARTED 的前提：已通过 Gate A（若是首次）与 Gate B。

STARTED 评论必须包含：

- 前置检查结果（见第 8 节模板）
- 本次工作范围（对应 module_paths）
- 风险/阻塞（若有）
- 计划回写点（哪些字段会在后置更新时写回 Base）

### 6.3 过程中的自动化任务（每次执行）

每次自动化任务执行（例如创建 PR、更新 PR、触发 workflow、生成产物）必须：

- 在执行前做 Gate B 前置检查并记录在评论中
- 执行后做后置更新并记录在评论中（包括 Base 回写）

### 6.4 完工回报（DONE）

完成一次可验收交付后，必须：

- 提交 DONE（或在 SUMMARY 中明确标记已完成并给出证据与链接）
- 完成 Base 后置更新（见第 7 节）

## 7. 后置更新（必须执行，作为监督抓手）

### 7.1 模块任务表（模块任务层）

至少更新：

- `status`（in_progress/blocked/done）
- `pr_url`、`pr_number`
- `comment_anchor`（本次 SUMMARY/DONE 的 comment URL）
- `blocker`（若阻塞）
- `next_action`（下一步动作）
- `owner_agent`（执行者标识）

### 7.2 目标推进表（Goal 层）

至少更新：

- `goal_status/current_phase/risk_level`
- `next_milestone/下一步动作/当前阻塞`
- `okr_sync_status/okr_last_sync_at`（若已完成 OKR 对齐或同步）

### 7.3 自动化任务监控（Run 层）

写入或更新：

- 本次自动化任务 run 的链接、状态、关键输出
- 对应 PR/任务卡的绑定信息

## 8. PR 评论模板（必须包含前置检查 + 后置更新）

### 8.1 每次自动化执行的 SUMMARY 模板（fast/strict 均可用）

```md
[单次总结 / SUMMARY]

前置检查（未通过则先补齐，禁止开工）：
- 审批：<link>
- DESIGN_REVIEW：<link>
- OKR Objective：<link or id>
- Base Goal（goal_id）：<goal_id>
- Base Task（task_id）：<task_id>
- Module Paths 与本次改动范围一致：yes/no
- Lane 与任务卡一致：yes/no

执行内容：
- <本次做了什么，范围与边界>

验证证据：
- Test: <command>
- Result: pass/fail
- Proof: <logs/screenshots/run url>

后置更新（必须完成）：
- 模块任务表回写：status=<...> pr_url=<...> comment_anchor=<...> blocker=<...> next_action=<...>
- 目标推进表回写：goal_status=<...> current_phase=<...> risk_level=<...> next_milestone=<...>
- 监控表回写：workflow/run=<...>
```

### 8.2 Strict Lane 的 DESIGN_REVIEW / TEST_REPORT / DONE

Strict Lane 保持原有结构化评论协议；但每条关键评论同样必须包含：

- 前置检查结论（可引用最近一次 SUMMARY 的结论与链接）
- 后置更新结果（确保飞书侧同步完整）

