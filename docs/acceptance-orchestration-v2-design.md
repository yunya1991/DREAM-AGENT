---
id: ACCEPTANCE-ORCHESTRATION-V2-DESIGN
type: design
owner: ledger-protocol-agent
depends:
  - ACCEPTANCE-REQUEST-PROTOCOL-DESIGN
  - LIFECYCLE-GUARD-COMPATIBILITY-V2-DESIGN
  - 01-COLLABORATION-PROTOCOL
  - 03-WORKFLOWS-AND-NORMS
version: 1
last_verified: 2026-06-07
---

# Acceptance Orchestration V2 设计

> 仓库：`DREAM-AGENT`
> 日期：2026-06-07
> 状态：v1 候选稿
> 目标：在已跑通单 agent `ACCEPTANCE_REQUEST -> VALIDATION_RESULT` 自动回写闭环的基础上，引入以 `acceptance cycle` 为中心的多 agent 验收编排机制，并明确飞书与 GitHub 的分层职责。

## 0. 背景

当前 `DREAM-AGENT` 已经完成了两件关键工作：

- `ACCEPTANCE_REQUEST` 协议已正式进入仓库主协议；
- `collab-acceptance-agent` 已在真实 `issue_comment` 触发下完成 `VALIDATION_RESULT` 自动回写闭环。

这意味着首版“单 agent 验收自动化”已经成立，但仍存在三个明显限制：

1. 当前验收仍主要依赖单一 validator，难以表达多视角结论；
2. 上下文主要来自 PR 评论与代码对象，缺少更稳定的目标导向输入；
3. 还没有一个正式的编排对象来聚合多个 PR、多个 agent 子结果与一次阶段性验收。

与此同时，新的协作要求已经变得清晰：

- 代码提交、PR、workflow、执行证据继续以 GitHub 为承载面；
- 验收目标、长期背景、工作项拆解、人工工作记录更适合由飞书 OKR / 多维表格承载；
- 多 agent 编排需要有一个比单个 PR 更稳定的聚合对象。

因此，`Acceptance Orchestration V2` 的核心不是替代现有协议，而是在现有协议之上新增：

- 飞书上游目标与上下文层；
- `acceptance cycle` 聚合对象；
- 多 agent 串行编排链路；
- 最终统一回写的主 `VALIDATION_RESULT`。

## 1. 设计目标

本次设计目标如下：

- 定义飞书与 GitHub / `DREAM-AGENT` 的正式分层职责；
- 确立飞书 `work item` 作为 AI 协作的上游主入口；
- 定义 `work item -> acceptance cycle -> PR / ACCEPTANCE_REQUEST / VALIDATION_RESULT` 的对象关系；
- 引入首版多 agent 编排链路，但保持执行拓扑简单、可审计；
- 首版采用“手动创建为主，自动创建为辅”的 cycle 创建机制；
- 为后续飞书 CLI 接入提供稳定的数据边界与同步方向。

## 2. 非目标

本次设计明确不包含以下内容：

- 不让飞书替代 GitHub 成为代码执行协议真源；
- 不在首版中引入复杂跨仓库自动编排；
- 不在首版中引入任意 fan-out / fan-in 的并行 agent 执行图；
- 不在首版中实现完全自动创建 `acceptance cycle`；
- 不在首版中做飞书与 GitHub 的双向任意状态同步；
- 不把 `human-approval-gateway` 或 `test-executor` 单独拆成首版 agent 角色。

## 3. 核心结论

### 3.1 分层真源按对象拆分，而不是全局单真源

本次设计不采用“飞书或 GitHub 二选一全局真源”的模式，而采用“按对象分配真源”的模式：

- 飞书真源：
  - `Objective`
  - `KR`
  - `Work Item`
  - 业务背景
  - 工作记录
  - 人工备注与人工状态
- GitHub / `DREAM-AGENT` 真源：
  - `PR`
  - `ACCEPTANCE_REQUEST`
  - `VALIDATION_RESULT`
  - workflow run
  - agent 编排执行证据

这样做的原因是：

- 飞书更适合承载目标和过程上下文；
- GitHub 更适合承载代码变更、触发事件与可审计执行证据；
- 多 agent 编排需要同时消费这两类对象，但不应让二者争抢同一类状态的权威性。

### 3.2 飞书首版主入口是多维表格 `work item`

飞书侧首版不以 `Objective` 或 `KR` 直接触发编排，而以多维表格中的 `work item` 作为 AI 协作主入口。

`Objective` / `KR` 仍然重要，但在首版中主要承担：

- 目标归属；
- 优先级与背景来源；
- 对 `work item` 的业务解释。

之所以选择 `work item` 作为主入口，是因为它更贴近一次具体执行与验收动作，便于映射：

- 当前执行状态；
- 负责人与协作者；
- 依赖与阻塞；
- GitHub PR；
- 验收重点；
- 工作日志与人工补充说明。

### 3.3 一个 `work item` 对应一个 `acceptance cycle`

首版主映射关系定义为：

- 一个 `work item` 对应一个 `acceptance cycle`

这里的含义不是“永远只有一次验收”，而是：

- 在某个时间窗口内，围绕该 `work item` 会激活一个当前验收周期；
- 该周期负责聚合本轮执行与验收所需的协议对象。

之所以引入 `acceptance cycle` 而不是直接让 `work item` 绑定单个 PR，是因为真实开发过程经常具有以下形态：

- 一个任务拆成多个 PR；
- 一轮验收后需要返工，再追加新 PR；
- 多个 agent 围绕同一目标从不同视角给出结论。

因此，`acceptance cycle` 是首版编排与汇总的中心对象。

### 3.4 `acceptance cycle` 手动创建为主，自动创建为辅

首版 `acceptance cycle` 的创建策略如下：

- 主路径：手动创建
- 辅路径：规则驱动的自动建议 / 自动创建

手动创建为主的原因是：

- 当前协议仍在快速演化；
- 多 agent 编排的误触发成本较高；
- 需要确保每个 cycle 都有明确验收意图、明确上下文和明确目标边界。

自动创建在首版中只作为扩展位保留，用于后续满足明确规则时触发，例如：

- `work item` 进入“待验收”状态；
- 关联 PR 进入 `ready for review`；
- GitHub 评论中出现明确结构化触发语句。

### 3.5 首版采用 4 角色精简版

首版多 agent 编排采用 4 个固定角色：

- `context-reader`
- `protocol-checker`
- `acceptance-validator`
- `result-synthesizer`

其职责分工如下：

- `context-reader`
  - 读取飞书 `work item`
  - 读取关联 `Objective / KR`
  - 读取 GitHub PR / 评论 / 最近一次 `VALIDATION_RESULT`
  - 产出本轮验收上下文快照
- `protocol-checker`
  - 检查 cycle 是否可执行
  - 检查 `ACCEPTANCE_REQUEST` 是否结构化完整
  - 检查对象关联、基线字段、前置约束是否齐备
- `acceptance-validator`
  - 执行专项验收
  - 基于上下文包与协议输入做结构、功能、对齐、风险检查
- `result-synthesizer`
  - 汇总前序角色输出
  - 形成统一主 `VALIDATION_RESULT`
  - 负责最终回写协议结论

### 3.6 首版执行拓扑：先串行，保留并行扩展位

首版执行拓扑明确采用：

- 先串行
- 保留并行扩展位

默认链路为：

1. `context-reader`
2. `protocol-checker`
3. `acceptance-validator`
4. `result-synthesizer`

之所以不在首版就引入并行 fan-out / fan-in，是因为：

- 首版更需要稳定、易解释、易回溯的链路；
- 上下文和协议完整性应先于正式验收；
- 当前最重要的是把多 agent 验收从“概念”变成“可执行、可追溯、可治理”的稳定协议。

并行扩展位主要保留在后续的 `acceptance-validator` 阶段：

- 未来可以拆出多个 validator 并行执行；
- 再由 `result-synthesizer` 做结果汇总。

## 4. 对象模型

### 4.1 飞书对象

首版涉及的飞书对象为：

- `objective`
- `kr`
- `work_item`

建议最小字段集合：

#### `objective`

- `objective_id`
- `title`
- `status`

#### `kr`

- `kr_id`
- `objective_id`
- `title`
- `status`

#### `work_item`

- `work_item_id`
- `kr_id`
- `title`
- `status`
- `priority`
- `context_summary`
- `acceptance_focus`
- `dependencies`
- `work_log`
- `linked_prs`

### 4.2 编排对象

首版新增的编排中心对象为：

- `acceptance_cycle`

建议最小字段集合：

- `acceptance_cycle_id`
- `work_item_id`
- `cycle_status`
- `creation_mode` (`manual | auto`)
- `linked_prs`
- `latest_acceptance_request_id`
- `latest_validation_result_id`
- `current_phase`

### 4.3 GitHub 协议对象

首版继续沿用并增强以下对象：

- `pr_number`
- `acceptance_request_id`
- `validation_result`

它们与 `acceptance_cycle` 的关系如下：

- 一个 `acceptance_cycle` 可关联一个或多个 `pr_number`
- 一个 `acceptance_cycle` 在某一时刻有一个最新有效的 `acceptance_request_id`
- 一个 `acceptance_cycle` 在某一轮验收后产出一个主 `validation_result`

## 5. 数据流

### 5.1 上下文流

飞书向 `DREAM-AGENT` 提供：

- `work_item` 基础字段
- `Objective / KR` 目标归属
- 工作记录与人工补充上下文

`context-reader` 将这些内容与 GitHub 当前状态拼装成“本轮上下文包”。

### 5.2 协议流

GitHub 评论链继续作为协议主接口：

1. 由人或 orchestrator 发起 `ACCEPTANCE_REQUEST`
2. `protocol-checker` 确认结构完整
3. `acceptance-validator` 执行验收
4. `result-synthesizer` 回写主 `VALIDATION_RESULT`

### 5.3 结果回写流

首版建议保持以下方向：

- 飞书 -> GitHub：提供目标上下文快照
- GitHub -> 飞书：回写执行摘要与验收结果摘要

首版明确不支持飞书与 GitHub 任意双向修改同一状态字段。

## 6. 状态边界

### 6.1 飞书管理的状态

飞书负责管理的状态包括：

- 目标状态
- 业务任务状态
- 工作记录
- 人工备注

### 6.2 GitHub 管理的状态

GitHub / `DREAM-AGENT` 负责管理的状态包括：

- PR 状态
- `ACCEPTANCE_REQUEST`
- `VALIDATION_RESULT`
- workflow 运行状态
- agent 编排阶段状态

### 6.3 必须避免的漂移

首版必须避免以下漂移：

- 飞书显示“已完成”，但 GitHub 仍未有正式验收结论；
- GitHub 验收已 `BLOCK`，但飞书仍显示“通过”；
- agent 同时在飞书和 GitHub 回写正式主结论。

因此，本次设计要求：

- 正式验收结论以 GitHub `VALIDATION_RESULT` 为准；
- 飞书只回写摘要与业务可读状态，不生成第二份正式验收锚点。

## 7. 首版治理规则

首版必须遵守以下规则：

1. 所有 `acceptance cycle` 必须具备稳定 ID；
2. 所有 cycle 都必须绑定 `work_item_id`；
3. 所有正式验收结论必须落为 GitHub `VALIDATION_RESULT`；
4. `protocol-checker` 不通过时，不进入正式 validator 阶段；
5. `result-synthesizer` 是唯一主结论写入者；
6. 首版默认不做并行 validator fan-out；
7. 首版默认由人显式发起 cycle。

## 8. 与现有体系的关系

本次设计不是推翻现有体系，而是在以下基础上增量扩容：

- 保留 `ACCEPTANCE_REQUEST` / `VALIDATION_RESULT` 现有协议；
- 保留 `Agent Lifecycle Guard` 的双轨兼容能力；
- 保留 GitHub 评论驱动自动回写链；
- 新增飞书上游上下文层与 `acceptance cycle` 聚合层；
- 为多 agent reviewer / validator 编排留出正式结构位。

## 9. 实施建议

建议实施顺序如下：

1. 在 `DREAM-AGENT` 中先定义 `acceptance_cycle` 对象模型与状态机；
2. 引入 `4 角色精简版` 编排链；
3. 将 `context-reader` 的输入扩展到飞书 `work item` 快照；
4. 让 `result-synthesizer` 支持 GitHub 主结论 + 飞书摘要回写；
5. 最后再评估是否需要加入并行 validator、人工审批网关或跨仓库联动。

## 10. 开放问题

本次设计已收口首版方向，但以下问题留给后续 plan / implementation 再细化：

- `acceptance_cycle` 的存储载体放在仓库文件、评论链，还是外部表；
- 飞书 CLI 在首版采用只读拉取，还是允许摘要回写；
- `context-reader` 如何缓存飞书快照以便审计；
- 何时从“手动建 cycle”为主，升级到“自动建 cycle”为主；
- 何时从串行 4 角色，升级到并行 validator 编排。
