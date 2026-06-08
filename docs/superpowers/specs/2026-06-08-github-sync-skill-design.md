---
id: GITHUB-SYNC-SKILL-DESIGN
type: design
owner: governance-agent
depends:
  - FEISHU-COLLABORATION-SYSTEM-DESIGN
  - OKR-DRIVEN-SKILL-DESIGN
  - BITABLE-SKILL-DESIGN
version: 1
last_verified: 2026-06-08
---

# 飞书-GitHub 协作 SKILL 设计

> 仓库：`DREAM-AGENT`
> 日期：`2026-06-08`
> 状态：draft
> 目标：构建一个以 GitHub 事件为驱动、以飞书协作状态为投影目标的工程协作技能，使 issue、PR 与 checks 的真实研发状态能够稳定回传到飞书协作界面，并在确认后完成真实写回、验证和交接。

## 1. 背景

当前主线已经具备三个关键基础：

- `OKR-driven SKILL` 已经定义长期目标、任务候选与 workflow 候选
- `Bitable SKILL` 已经把目标与任务、进度、视图投影纳入执行面
- 现有 `sync_github_to_feishu.py`、测试用例与 acceptance workflow 已经证明 GitHub 到飞书字段映射是存在的

这意味着当前缺失的不是“再做一套 GitHub 自动化”，而是一个位于飞书协作体系中的专门技能，用来回答下面的问题：

- GitHub 中真实发生了什么
- 这些变化会影响飞书里的哪些协作对象
- 哪些字段需要被回写
- 哪些风险需要升级到审批或知识运维

也就是说，`GitHub-Feishu 协作 SKILL` 的真实职责不是通用 GitHub 平台集成，而是“工程协作投影层”。

## 2. 问题定义

本设计主要解决以下五类问题：

### 2.1 工程真实状态与管理视图脱节

GitHub 中 issue、PR 与 checks 会持续变化，但如果这些变化不被稳定投影到飞书协作记录，管理界面就会出现：

- PR 已阻塞但飞书仍显示推进中
- checks 已失败但自动化状态仍保留旧值
- 代码已提交或合并，但任务状态和下一步建议没有更新

### 2.2 当前能力存在脚本，但缺少统一技能闭环

现有底层资产已经包括：

- GitHub 到飞书字段映射
- acceptance / collaboration workflow
- goal record 聚合与协作上下文采集

但仍缺少：

- dedicated skill package
- preview-first flow
- single preview/result contract
- explicit event coverage registry

结果是可以零散执行，但无法成为体系化技能。

### 2.3 GitHub 事件覆盖与降级边界不清晰

若不先定义 v1 事件覆盖边界，就会出现两种风险：

- 范围过窄，只能同步少量字段，无法形成闭环
- 范围过宽，直接退化成重型 GitHub 运营平台

因此需要明确：

- v1 默认覆盖 `issue + PR + checks`
- 未覆盖的 action、字段和证据必须显式记录为 gap

### 2.4 风险门禁与知识沉淀无法联动

GitHub 事件并不总是普通状态变更，部分场景会涉及：

- 高风险状态跃迁
- 审批要求
- 自动化失败后的人工接手
- 运行证据和评论锚点沉淀

如果没有统一闭环，这些变化会散落在 PR 评论、workflow artifact 和临时记忆中。

### 2.5 现有 workflow 缺少统一对象语义

当前 workflow 能串起：

- 输入解析
- acceptance cycle 创建
- 飞书上下文收集
- 执行与评论回写

但它仍偏向流程入口，而不是统一的领域对象模型。因此需要一个技能层来稳定定义：

- 输入事件语义
- 预演结构
- 写回计划
- 验证快照
- 交接与知识输出

## 3. 设计目标

本设计的目标如下：

- 定义一个 `GitHub-Feishu 协作 SKILL`，作为飞书协作体系中的工程协作投影层
- 默认覆盖 `Issue + PR + Checks`
- 坚持 `preview -> confirmation -> writeback -> verify -> handoff`
- 将事件命中规则、字段更新和风险标记纳入 preview，而不是只输出最终 record
- 将审批门禁、知识沉淀和失败分层纳入标准流程

成功标准：

- 能把 GitHub 事件归一化为可读的 `ExecutionPreview`
- 能稳定产出飞书协作字段更新计划与验证快照
- 能在执行前显式暴露 event coverage、状态映射和风险标记
- 能在执行后输出 `ExecutionResult`、`KnowledgeUpdate` 和 handoff
- 能作为下一步实施计划与真实落地的统一设计基线

## 4. 范围与非目标

### 4.1 本设计覆盖

- `github.issue.changed`
- `github.pr.changed`
- `github.check.changed`
- GitHub 到飞书协作状态投影
- 自动化结果与评论锚点的最小写回
- 写回验证
- handoff 与 `KnowledgeUpdate`

### 4.2 本设计不覆盖

- 通用 GitHub 平台治理
- 全量 remote action 编排
- 复杂跨仓库运营面板
- v1 内主动修改大量 GitHub 远程状态
- 与 GitHub 无关的审批或知识系统重构

v1 的重点是：

- 让 issue / PR / checks 的事件变化稳定投影到飞书协作状态
- 让风险、缺口和证据可见
- 让后续 `Approval` 与 `Knowledge-Ops` 能稳定接手

而不是一开始就做成全量仓库运营平台。

## 5. 核心原则

### 5.1 事件投影原则

`GitHub-Feishu` 的核心不是驱动 GitHub，而是消费 GitHub 事件并投影到飞书协作对象。

### 5.2 协作闭环原则

任何同步动作都必须回答：

- 为什么这次要写回
- 会改哪些字段
- 哪些地方存在不确定性
- 最终结果是否已被验证

### 5.3 预演优先原则

所有写回前必须先生成 preview，并显式展示：

- 事件摘要
- 命中的覆盖规则
- 字段更新
- 风险标记

### 5.4 分层失败原则

失败必须区分：

- `hard_block`
- `soft_block`
- `degraded_success`
- `confirmed`

不能整体静默失败，也不能把局部缺口伪装成完全成功。

### 5.5 体系协同原则

`GitHub-Feishu` 不独立生长，必须服从整个协作体系的主从关系：

- `OKR-driven` 提供目标上下文与长期约束
- `Bitable` 承接任务和进度投影
- `Approval` 接管高风险门禁
- `Knowledge-Ops` 接管证据、handoff 与运维沉淀

## 6. 角色定位与主从关系

### 6.1 `OKR-driven` 的职责

负责回答：

- 为什么要做
- 当前目标和 KR 是什么
- 本次工程动作属于哪个长期目标

### 6.2 `Bitable` 的职责

负责回答：

- 当前任务和进度记录如何承接工程动作
- 飞书管理视图中应显示什么状态

### 6.3 `GitHub-Feishu` 的职责

负责回答：

- GitHub 的 issue / PR / checks 刚刚发生了什么
- 这些变化应该如何投影到飞书协作字段
- 哪些地方需要审批、验证、交接或知识沉淀

### 6.4 固定主从关系

必须固定为：

- `OKR-driven` 提供上游目标上下文
- `Bitable` 提供下游任务/进度承接
- `GitHub-Feishu` 负责工程真实状态的协作投影
- `Approval` 只在命中高风险门禁时参与
- `Knowledge-Ops` 负责最终的知识回收与运维沉淀

## 7. 推荐方案

推荐采用：

- `方案 A：事件投影型`

其核心做法是：

- 以 GitHub 事件为唯一入口
- 将 issue / PR / checks 归一化为统一事件对象
- 先输出可读 preview，再决定是否写回飞书
- 通过 event coverage registry 管理命中规则、字段映射和降级策略

不推荐：

- 把 v1 设计成大而全的 workflow 平台
- 把重点放到复杂 remote actions，而忽略协作状态投影
- 在没有 preview/result contract 的前提下继续堆叠脚本

## 8. 对象模型

### 8.1 `GitHubEventSpec`

表示归一化后的 GitHub 事件对象，最少包含：

- `event_id`
- `event_type`
- `object_type`
- `repo`
- `number`
- `action`
- `sender`
- `branch`
- `sha`
- `occurred_at`

### 8.2 `CollabStateProjection`

表示投影到飞书协作状态的字段集合，最少包含：

- `task_id`
- `goal_id`
- `repo`
- `branch`
- `pr_number`
- `implementation_status`
- `platform_status`
- `governance_status`
- `automation_status`
- `risk_level`
- `approval_status`
- `decision_summary`
- `last_comment_anchor`
- `last_commit`
- `blocker`
- `next_action`

### 8.3 `EventCoverageSpec`

表示事件命中规则与降级策略，最少包含：

- `event_type`
- `supported_actions`
- `required_fields`
- `field_mapping`
- `risk_rules`
- `fallback_policy`
- `knowledge_required`

### 8.4 `WritebackPlan`

表示写回飞书前的执行计划，最少包含：

- `target_record_id`
- `update_fields`
- `idempotency_key`
- `writeback_stage`
- `risk_flags`
- `approval_gate`

### 8.5 `VerificationSnapshot`

表示写回后的验证快照，最少包含：

- `record_fields_verified`
- `automation_summary`
- `comment_anchor_verified`
- `coverage_rule_hit`
- `unresolved_gaps`

## 9. Preview 产物

`GitHub-Feishu 协作 SKILL` 的 preview 建议固定输出：

- `event_summary`
- `impacted_records`
- `field_updates`
- `risk_flags`
- `event_coverage_hit`
- `writeback_plan`
- `requires_confirmation`

### 9.1 `event_summary`

必须能回答：

- 是哪类事件
- 来源仓库和对象是什么
- 触发动作是什么
- 当前变更会影响哪条飞书协作记录

### 9.2 `risk_flags`

至少包括：

- `missing_goal_link`
- `missing_task_link`
- `approval_required`
- `unknown_check_state`
- `event_coverage_gap`
- `record_lookup_failed`

### 9.3 `event_coverage_hit`

必须显式包含：

- 命中的事件规则
- 命中的 action
- 触发的字段映射
- 若未完全命中，使用的 fallback 或 gap 说明

### 9.4 `writeback_plan`

建议固定按阶段展示：

1. 事件覆盖检查
2. 协作状态写回
3. 自动化结果写回
4. 评论锚点写回
5. 验证快照生成

## 10. 执行链路

统一执行链路为：

1. `event intake`
2. `preview`
3. `confirmation / policy check`
4. `writeback`
5. `verify`
6. `handoff`

### 10.1 Event Intake

只做三件事：

- 读取 GitHub 事件和 workflow 上下文
- 归一化为 `GitHubEventSpec`
- 挂接 goal / task / approval 关联上下文

### 10.2 Preview

只做四件事：

- 识别事件命中规则
- 生成字段级更新预演
- 暴露风险标记
- 生成执行计划

### 10.3 Confirmation / Policy Check

当存在以下情况时，必须要求确认或进入门禁：

- `approval_required`
- `event_coverage_gap`
- `unknown_check_state`
- 跨越关键治理状态
- 目标或任务关联缺失

### 10.4 Writeback

确认后按固定顺序写回：

1. `event_coverage_check`
2. `collab_state_writeback`
3. `automation_result_writeback`
4. `comment_anchor_writeback`
5. `verification_snapshot`

### 10.5 Verify

验证至少分四层：

- 协作记录字段验证
- 自动化状态验证
- 评论锚点验证
- coverage 与 gap 验证

### 10.6 Handoff

每次执行后必须生成：

- 成功或失败 handoff
- `ExecutionResult`
- `KnowledgeUpdate`

## 11. 适配器边界

建议将 `GitHub-Feishu 协作 SKILL` 设计为“薄 skill + 稳定适配器”。

### 11.1 `GitHub Intake Adapter`

负责：

- 事件解析
- workflow 上下文提取
- 归一化对象构建

不负责：

- 字段策略判断
- 风险决策

### 11.2 `State Projection Adapter`

负责：

- issue / PR / checks 到飞书字段映射
- 复用现有 `sync_github_to_feishu.py` 的字段语义
- 输出 `CollabStateProjection`

### 11.3 `Feishu Writeback Adapter`

负责：

- 目标记录查找
- 字段更新
- 幂等写回
- 写回回执

### 11.4 `Knowledge Adapter`

负责：

- handoff 证据组装
- runbook / delivery 路由
- 事件处理结果沉淀

### 11.5 `Approval Adapter`

负责：

- 命中门禁时发起或连接审批流
- 获取审批结果并回传治理状态

普通同步路径中不主动侵入业务决策。

### 11.6 Skill 本体职责

`GitHub-Feishu 协作 SKILL` 本身只负责：

- 读取输入
- 生成 preview
- 决定执行顺序
- 汇总验证结果
- 产出 handoff / knowledge update

## 12. 失败策略

建议固定四类执行状态：

### 12.1 `hard_block`

例如：

- 关键记录无法定位
- 必需字段缺失
- repo 或对象主键无法识别

结果：

- 停止执行
- 必须人工确认或补齐上下文

### 12.2 `soft_block`

例如：

- 事件可识别，但 action 或字段映射不完整
- checks 结果语义不完整
- event coverage 存在缺口

结果：

- 允许输出 preview
- 不允许伪装成完全成功

### 12.3 `degraded_success`

例如：

- 核心协作字段已写回
- 但评论锚点、次要证据或部分 checks 摘要未完成

结果：

- 执行成功但降级
- 必须生成 gap 和后续动作

### 12.4 `confirmed`

表示：

- 写回完成
- 验证通过
- handoff 与知识输出完整

## 13. 事件覆盖策略

建议 v1 至少覆盖三类事件：

### 13.1 `github.issue.changed`

优先覆盖：

- opened
- edited
- closed
- reopened
- labeled

### 13.2 `github.pr.changed`

优先覆盖：

- opened
- synchronize
- ready_for_review
- review_requested
- closed
- merged

### 13.3 `github.check.changed`

优先覆盖：

- requested
- in_progress
- completed

对于：

- 未覆盖 action
- 字段语义冲突
- comment anchor 缺失

必须统一进入 `event_coverage_gap` 记录，而不是静默忽略。

## 14. 漂移策略

建议至少识别四类漂移：

### 14.1 `目标关联漂移`

GitHub 对象已存在，但无法稳定关联目标或任务记录。

### 14.2 `状态语义漂移`

GitHub 当前状态与飞书协作字段语义不一致。

### 14.3 `覆盖规则漂移`

新的 event action 已经出现，但 registry 未更新。

### 14.4 `证据漂移`

评论锚点、workflow 结果或验证证据缺失，导致后续交接困难。

其中：

- 目标关联漂移、状态语义漂移属于高优先级
- 覆盖规则漂移、证据漂移允许局部降级，但不能静默忽略

## 15. 测试策略

建议测试固定为四层：

### 15.1 Preview Tests

验证：

- issue 事件预演
- PR 事件预演
- checks 事件预演
- 风险标记与 gap 暴露

### 15.2 Projection Tests

分别验证：

- 四层状态字段映射
- goal / approval 字段映射
- 写回计划生成

### 15.3 Registry Tests

验证：

- 事件覆盖表完整性
- action 到字段映射一致性
- fallback policy 与风险规则可审计

### 15.4 Dry-Run Tests

验证：

- `preview -> confirm -> writeback -> verify -> handoff`
- acceptance / collaboration workflow 挂接点
- `KnowledgeUpdate` 和 handoff 是否完整输出

## 16. 风险与应对

### 16.1 风险：退化成通用 GitHub 平台

应对：

- 固定 v1 只覆盖 `Issue + PR + Checks`
- 不把 remote action 作为默认路径

### 16.2 风险：只有脚本映射，没有可审计 preview

应对：

- 强制 preview-first
- 强制输出 event coverage 与 risk flags

### 16.3 风险：workflow 入口与 skill 语义脱节

应对：

- 保留现有 workflow 作为入口
- 在 skill 层补统一对象与闭环契约

### 16.4 风险：失败后无法交接与排障

应对：

- 固定输出 `ExecutionResult`
- 固定输出 `KnowledgeUpdate`
- 固定 handoff 与 gap 记录

## 17. 验收标准

本设计完成后，应满足以下验收标准：

- 能清晰说明 `GitHub-Feishu` 在整个协作体系中的定位和主从关系
- 能定义 v1 的 `Issue + PR + Checks` 边界
- 能说明对象模型、preview 产物和写回顺序
- 能说明适配器边界、失败分级、事件覆盖与漂移策略
- 能说明测试策略和知识回收机制
- 能作为下一步实施计划与真实落地的统一设计基线
